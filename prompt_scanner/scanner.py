import os
import yaml
import re
import json
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Literal, Union, cast, Protocol, Type, TypeVar
from abc import ABC, abstractmethod
from pydantic import ValidationError
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic

from prompt_scanner.models import OpenAIPrompt, AnthropicPrompt, OldAnthropicPrompt, PromptType, PromptScanResult, PromptCategory

# Load environment variables from .env file
load_dotenv()

@dataclass
class ScanResult:
    is_safe: bool
    issues: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []

class BasePromptScanner(ABC):
    """
    Base class for prompt scanners that scan for potential safety issues.
    """
    
    def __init__(self, api_key: str, model: str):
        """
        Initialize the BasePromptScanner.
        
        Args:
            api_key: API key for the LLM provider
            model: Model name to use for content scanning
        """
        if not api_key:
            raise ValueError("API key cannot be empty")
            
        self.api_key = api_key
        self.model = model
        
        # Load guardrails and patterns
        self.guardrails = self._load_yaml_data("guardrails.yaml")
        self.injection_patterns = self._load_yaml_data("injection_patterns.yaml")
        self.content_policies = self._load_yaml_data("content_policies.yaml")
        
        # Compile regex patterns for better performance
        self._compile_patterns()
        
        # Should be set by subclasses
        self.client = None
    
    def _load_yaml_data(self, filename: str) -> Dict:
        """Load data from a YAML file in the data directory."""
        data_dir = os.path.join(os.path.dirname(__file__), "data")
        filepath = os.path.join(data_dir, filename)
        
        try:
            with open(filepath, "r") as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            # Return empty dict if file doesn't exist yet
            return {}
    
    def _compile_patterns(self):
        """Compile regex patterns from injection_patterns for better performance."""
        for pattern_name, pattern_data in self.injection_patterns.items():
            if pattern_data.get("regex"):
                try:
                    pattern_data["compiled_regex"] = re.compile(pattern_data["regex"], re.IGNORECASE)
                except re.error:
                    # If regex is invalid, create a fallback pattern that matches the literal string
                    pattern_data["compiled_regex"] = re.compile(re.escape(pattern_data["regex"]), re.IGNORECASE)
    
    def _count_tokens(self, text: str) -> int:
        """
        Simple token counting approximation.
        Uses a basic heuristic of ~4 characters per token.
        """
        return len(text) // 4
    
    @abstractmethod
    def _setup_client(self):
        """Setup the API client for the selected provider."""
        pass
    
    @abstractmethod
    def _validate_prompt_structure(self, prompt: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate prompt structure for the provider."""
        pass
    
    @abstractmethod
    def _scan_prompt(self, prompt: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan a provider-specific prompt."""
        pass
    
    @abstractmethod
    def _call_content_evaluation(self, prompt, text) -> tuple:
        """Call the LLM to evaluate content."""
        pass
    
    def scan(self, prompt: Dict[str, Any]) -> ScanResult:
        """
        Scan a prompt for potential injection attacks and apply guardrails.
        
        Args:
            prompt: Prompt in the format used by the provider's chat completions API
            
        Returns:
            ScanResult: Object containing scan results and issues
        """
        issues = []
        
        # Validate prompt structure
        validation_issues = self._validate_prompt_structure(prompt)
        if validation_issues:
            return ScanResult(is_safe=False, issues=validation_issues)
        
        # Scan the prompt
        issues.extend(self._scan_prompt(prompt))
        
        return ScanResult(
            is_safe=len(issues) == 0,
            issues=issues
        )
    
    def scan_text(self, text: str) -> PromptScanResult:
        """
        Scan text content for unsafe content using LLM-based evaluation.
        
        Args:
            text: The input text to scan
            
        Returns:
            PromptScanResult: Object containing content safety scan results
        """
        prompt = self._create_evaluation_prompt(text)
        
        try:
            response_text, token_usage = self._call_content_evaluation(prompt, text)
        except Exception as e:
            return PromptScanResult(
                is_safe=True,  # Default to safe on error
                reasoning=f"Error during content evaluation: {str(e)}",
                token_usage={"prompt_tokens": self._count_tokens(text)}
            )
        
        # Parse the response
        try:
            result = json.loads(response_text)
            is_safe = result.get("is_safe", True)
            reasoning = result.get("reasoning", "No reasoning provided")
            
            if not is_safe and "categories" in result:
                # Get the primary category (highest confidence)
                categories = result["categories"]
                if not categories:
                    return PromptScanResult(
                        is_safe=True,
                        reasoning="No specific unsafe categories identified",
                        token_usage=token_usage
                    )
                    
                # Sort categories by confidence (descending)
                sorted_categories = sorted(categories, key=lambda x: x.get("confidence", 0), reverse=True)
                primary_category = sorted_categories[0]
                
                # Create category object
                category = PromptCategory(
                    id=primary_category.get("id", "unknown"),
                    name=primary_category.get("name", "Unspecified"),
                    confidence=primary_category.get("confidence", 0.5),
                    matched_patterns=primary_category.get("matched_patterns", [])
                )
                
                # Include information about secondary categories in the reasoning
                if len(sorted_categories) > 1:
                    secondary_info = "Additional categories: "
                    for cat in sorted_categories[1:]:
                        secondary_info += f"{cat.get('name', 'Unknown')} (confidence: {cat.get('confidence', 0):.2f}), "
                    reasoning += "\n\n" + secondary_info.rstrip(", ")
                
                return PromptScanResult(
                    is_safe=False,
                    category=category,
                    reasoning=reasoning,
                    token_usage=token_usage,
                    all_categories=sorted_categories
                )
            else:
                return PromptScanResult(
                    is_safe=True,
                    reasoning=reasoning,
                    token_usage=token_usage
                )
        except json.JSONDecodeError:
            return PromptScanResult(
                is_safe=True,  # Default to safe on parsing error
                reasoning="Error parsing content evaluation response",
                token_usage=token_usage
            )
    
    # For backward compatibility
    def scan_content(self, text: str) -> PromptScanResult:
        """Alias for scan_text for backward compatibility."""
        return self.scan_text(text)
    
    def _format_categories_for_prompt(self) -> str:
        """Format content policy categories for inclusion in the prompt."""
        formatted = "Content Policy Categories:\n"
        if "policies" in self.content_policies:
            for id, policy in self.content_policies["policies"].items():
                formatted += f"{id}. {policy['name']}: {policy['description']}\n"
                
                # If examples are available, include one as a reasoning example
                examples = policy.get("examples", [])
                if examples:
                    formatted += f"   Reasoning: Content that asks for or provides information about {policy['name'].lower()} violates safety guidelines. "
                    formatted += f"For example, \"{examples[0]}\" would be unsafe because it explicitly seeks instructions for harmful activities.\n"
        
        return formatted
    
    def _format_examples_for_prompt(self) -> str:
        """Format examples from content policies for inclusion in the prompt."""
        formatted = "Examples of unsafe content by category:\n"
        
        if "policies" in self.content_policies:
            for id, policy in self.content_policies["policies"].items():
                name = policy.get("name", "Unknown")
                formatted += f"\n{id}. {name}:\n"
                
                # Add examples if available
                examples = policy.get("examples", [])
                # Limit examples to 5 to keep prompt length reasonable
                example_subset = examples[:5] if len(examples) > 5 else examples
                for example in example_subset:
                    formatted += f"  - {example}\n"
        
        return formatted
    
    @abstractmethod
    def _create_evaluation_prompt(self, text: str):
        """Create the prompt to send to the LLM for content evaluation."""
        pass
    
    def _check_content_for_issues(self, content: str, index: int, issues: List[Dict[str, Any]], is_system_message: bool = False):
        """Check content string for injection patterns and guardrail violations."""
        if not isinstance(content, str):
            issues.append({
                "type": "invalid_content",
                "message_index": index,
                "description": "Content must be a string",
                "severity": "medium"
            })
            return
            
        # Check content for injection patterns
        for pattern_name, pattern in self.injection_patterns.items():
            # Skip patterns with exempt_system_role=True when checking system messages
            if is_system_message and pattern.get("exempt_system_role", False):
                continue
                
            if self._check_pattern(content, pattern):
                issues.append({
                    "type": "potential_injection",
                    "pattern": pattern_name,
                    "message_index": index,
                    "description": pattern.get("description", "Potential prompt injection detected"),
                    "severity": pattern.get("severity", "medium")
                })
        
        # Apply guardrails
        for guardrail_name, guardrail in self.guardrails.items():
            if not self._check_guardrail(content, guardrail):
                issues.append({
                    "type": "guardrail_violation",
                    "guardrail": guardrail_name,
                    "message_index": index,
                    "description": guardrail.get("description", "Guardrail violation detected"),
                    "severity": "high"
                })
        
        # Run LLM-based content safety check
        content_result = self.scan_text(content)
        if not content_result.is_safe:
            issues.append({
                "type": "unsafe_content",
                "message_index": index,
                "category": content_result.category.model_dump() if content_result.category else None,
                "description": content_result.reasoning,
                "severity": "high"
            })
    
    def _check_pattern(self, content: str, pattern: Dict[str, Any]) -> bool:
        """Check if content matches a pattern using compiled regex."""
        if "compiled_regex" in pattern:
            return bool(pattern["compiled_regex"].search(content))
        elif "regex" in pattern:
            # Fallback to string matching if pattern wasn't compiled
            return pattern["regex"].lower() in content.lower()
        return False
    
    def _check_guardrail(self, content: str, guardrail: Dict[str, Any]) -> bool:
        """Check if content passes a guardrail check."""
        guardrail_type = guardrail.get("type")
        
        if guardrail_type == "privacy":
            # Check for PII patterns
            for pattern in guardrail.get("patterns", []):
                if pattern.get("type") == "regex" and pattern.get("value"):
                    if re.search(pattern["value"], content, re.IGNORECASE):
                        return False
        
        # For now, other guardrail types pass by default
        # This would be expanded in a full implementation
        return True


class OpenAIPromptScanner(BasePromptScanner):
    """Implementation of PromptScanner for OpenAI."""
    
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        Initialize OpenAI-specific prompt scanner.
        
        Args:
            api_key: OpenAI API key
            model: OpenAI model name to use (default: gpt-4o)
        """
        super().__init__(api_key, model)
        self._setup_client()
    
    def _setup_client(self):
        """Setup OpenAI client."""
        self.client = OpenAI(api_key=self.api_key)
    
    def _validate_prompt_structure(self, prompt: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate OpenAI prompt structure."""
        issues = []
        
        try:
            OpenAIPrompt(**prompt)
        except ValidationError as e:
            for error in e.errors():
                issues.append({
                    "type": "validation_error",
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "description": error["msg"],
                    "severity": "medium"
                })
        except Exception as e:
            issues.append({
                "type": "validation_error",
                "description": f"Unexpected error validating prompt structure: {str(e)}",
                "severity": "medium"
            })
            
        return issues
    
    def _scan_prompt(self, prompt: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan an OpenAI-formatted prompt."""
        issues = []
        
        try:
            # Convert to Pydantic model for easier access
            validated_prompt = OpenAIPrompt(**prompt)
            
            # Scan each message
            for i, message in enumerate(validated_prompt.messages):
                # Check if this is a system message
                is_system_message = message.role == "system"
                
                # Check content for injection patterns
                if isinstance(message.content, str):
                    self._check_content_for_issues(message.content, i, issues, is_system_message)
                elif isinstance(message.content, list):
                    # Handle content parts array (for functions with multiple content parts)
                    for part in message.content:
                        if isinstance(part, dict) and part.get("type") == "text":
                            self._check_content_for_issues(part.get("text", ""), i, issues, is_system_message)
        except Exception as e:
            # This shouldn't happen as we've already validated the structure
            issues.append({
                "type": "processing_error",
                "description": f"Error processing OpenAI prompt: {str(e)}",
                "severity": "medium"
            })
        
        return issues
    
    def _create_evaluation_prompt(self, text: str) -> List[Dict[str, str]]:
        """Create the prompt for OpenAI content evaluation."""
        categories_info = self._format_categories_for_prompt()
        examples_info = self._format_examples_for_prompt()
        
        instructions = """
You are a content safety classifier. Your task is to determine if the user's input
contains unsafe content according to our content policies.

Analyze the input and determine if it violates any of the content policy categories.
Content can violate multiple categories simultaneously, so check each category thoroughly.

For each category you consider, provide clear reasoning about why the content does or does not 
violate that category's policy. Focus on being precise and specific in your assessment.

Respond in the following JSON format:
{
  "is_safe": true/false,
  "categories": [
    {
      "id": "category_id",
      "name": "category_name",
      "confidence": 0.0-1.0 (your confidence level)
    },
    {
      "id": "another_category_id",
      "name": "another_category_name",
      "confidence": 0.0-1.0 (your confidence level)
    }
  ],
  "reasoning": "Detailed explanation of why the content is safe or unsafe, including which specific policies it violates and how"
}

If the content is safe, return is_safe as true and an empty categories array, but still provide reasoning about why it's safe.
If the content violates multiple categories, list them all in the categories array with their respective confidence levels.
"""
        
        return [
            {"role": "system", "content": instructions + "\n\n" + categories_info + "\n\n" + examples_info},
            {"role": "user", "content": f"Input to evaluate: {text}"}
        ]
    
    def _call_content_evaluation(self, prompt, text) -> tuple:
        """Call OpenAI to evaluate content."""
        response = self.client.chat.completions.create(
            model=self.model,  # Use the specified model
            messages=prompt,
            response_format={"type": "json_object"}
        )
        
        response_text = response.choices[0].message.content
        token_usage = {
            "prompt_tokens": response.usage.prompt_tokens,
            "completion_tokens": response.usage.completion_tokens,
            "total_tokens": response.usage.total_tokens
        }
        
        return response_text, token_usage


class AnthropicPromptScanner(BasePromptScanner):
    """Implementation of PromptScanner for Anthropic."""
    
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        """
        Initialize Anthropic-specific prompt scanner.
        
        Args:
            api_key: Anthropic API key
            model: Anthropic model name to use (default: claude-3-haiku-20240307)
        """
        super().__init__(api_key, model)
        self._setup_client()
    
    def _setup_client(self):
        """Setup Anthropic client."""
        self.client = Anthropic(api_key=self.api_key)
    
    def _validate_prompt_structure(self, prompt: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Validate Anthropic prompt structure."""
        issues = []
        
        try:
            if "messages" in prompt:
                AnthropicPrompt(**prompt)
            elif "prompt" in prompt:
                OldAnthropicPrompt(**prompt)
            else:
                issues.append({
                    "type": "missing_field",
                    "description": "Missing required field: either 'messages' or 'prompt' must be present",
                    "severity": "medium"
                })
        except ValidationError as e:
            for error in e.errors():
                issues.append({
                    "type": "validation_error",
                    "field": ".".join(str(loc) for loc in error["loc"]),
                    "description": error["msg"],
                    "severity": "medium"
                })
        except Exception as e:
            issues.append({
                "type": "validation_error",
                "description": f"Unexpected error validating prompt structure: {str(e)}",
                "severity": "medium"
            })
            
        return issues
    
    def _scan_prompt(self, prompt: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Scan an Anthropic-formatted prompt."""
        issues = []
        
        try:
            if "messages" in prompt:
                # Convert to Pydantic model for messages format
                validated_prompt = AnthropicPrompt(**prompt)
                
                # Scan each message
                for i, message in enumerate(validated_prompt.messages):
                    # Check if this is a system-like message (Anthropic doesn't have system role)
                    is_system_message = message.role == "assistant" and i == 0
                    
                    # Check content for injection patterns
                    if isinstance(message.content, str):
                        self._check_content_for_issues(message.content, i, issues, is_system_message)
                    elif isinstance(message.content, list):
                        # Handle content parts array
                        for part in message.content:
                            if isinstance(part, dict) and part.get("type") == "text":
                                self._check_content_for_issues(part.get("text", ""), i, issues, is_system_message)
            elif "prompt" in prompt:
                # Old Anthropic API format (single string)
                # Here we can't distinguish roles, so we check the entire prompt
                self._check_content_for_issues(prompt["prompt"], 0, issues)
                
        except Exception as e:
            # This shouldn't happen as we've already validated the structure
            issues.append({
                "type": "processing_error",
                "description": f"Error processing Anthropic prompt: {str(e)}",
                "severity": "medium"
            })
        
        return issues
    
    def _create_evaluation_prompt(self, text: str) -> str:
        """Create the prompt for Anthropic content evaluation."""
        categories_info = self._format_categories_for_prompt()
        examples_info = self._format_examples_for_prompt()
        
        instructions = """
You are a content safety classifier. Your task is to determine if the user's input
contains unsafe content according to our content policies.

Analyze the input and determine if it violates any of the content policy categories.
Content can violate multiple categories simultaneously, so check each category thoroughly.

For each category you consider, provide clear reasoning about why the content does or does not 
violate that category's policy. Focus on being precise and specific in your assessment.

Respond in the following JSON format:
{
  "is_safe": true/false,
  "categories": [
    {
      "id": "category_id",
      "name": "category_name",
      "confidence": 0.0-1.0 (your confidence level)
    },
    {
      "id": "another_category_id",
      "name": "another_category_name",
      "confidence": 0.0-1.0 (your confidence level)
    }
  ],
  "reasoning": "Detailed explanation of why the content is safe or unsafe, including which specific policies it violates and how"
}

If the content is safe, return is_safe as true and an empty categories array, but still provide reasoning about why it's safe.
If the content violates multiple categories, list them all in the categories array with their respective confidence levels.
"""
        
        return f"""
{instructions}

{categories_info}

{examples_info}

Input to evaluate: {text}

JSON response:
"""
    
    def _call_content_evaluation(self, prompt, text) -> tuple:
        """Call Anthropic to evaluate content."""
        response = self.client.messages.create(
            model=self.model,  # Use the specified model
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024
        )
        
        response_text = response.content[0].text
        # Anthropic doesn't provide token usage in the same way
        input_length = self._count_tokens(text)
        output_length = self._count_tokens(response_text)
        token_usage = {
            "prompt_tokens": input_length,
            "completion_tokens": output_length,
            "total_tokens": input_length + output_length
        }
        
        return response_text, token_usage


class PromptScanner:
    """
    A class to scan prompts for potential safety issues, injection attacks, and apply guardrails before
    sending to language models like OpenAI and Anthropic. Uses LLM-based content safety checking.
    
    Factory class that creates appropriate provider-specific scanners.
    """
    
    def __init__(self, provider: Literal["openai", "anthropic"] = "openai", api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize the PromptScanner with an LLM provider, API key, and model.
        
        Args:
            provider: The LLM provider (default: "openai")
            api_key: API key for the specified provider (if None, will use environment variable)
            model: Model name to use (if None, will use provider-specific default)
        """
        self.provider = provider
        
        # Get API key from environment if not provided
        if api_key is None:
            if provider == "openai":
                api_key = os.environ.get("OPENAI_API_KEY")
                if not api_key:
                    raise ValueError("No OpenAI API key provided and none found in environment variables")
            else:  # anthropic
                api_key = os.environ.get("ANTHROPIC_API_KEY")
                if not api_key:
                    raise ValueError("No Anthropic API key provided and none found in environment variables")
        
        # Create provider-specific scanner
        if provider == "openai":
            model = model or "gpt-4o"
            self._scanner = OpenAIPromptScanner(api_key=api_key, model=model)
        elif provider == "anthropic":
            model = model or "claude-3-haiku-20240307"
            self._scanner = AnthropicPromptScanner(api_key=api_key, model=model)
        else:
            raise ValueError(f"Unsupported provider: {provider}. Use 'openai' or 'anthropic'")
    
    def scan(self, prompt: Dict[str, Any]) -> ScanResult:
        """
        Scan a prompt for potential injection attacks and apply guardrails.
        
        Args:
            prompt: Prompt in the format used by the provider's chat completions API
            
        Returns:
            ScanResult: Object containing scan results and issues
        """
        return self._scanner.scan(prompt)
    
    def scan_text(self, text: str) -> PromptScanResult:
        """
        Scan text content for unsafe content using LLM-based evaluation.
        
        Args:
            text: The input text to scan
            
        Returns:
            PromptScanResult: Object containing content safety scan results
        """
        return self._scanner.scan_text(text)
    
    def scan_content(self, text: str) -> PromptScanResult:
        """Alias for scan_text for backward compatibility."""
        return self.scan_text(text) 