# API Reference

## Classes

### PromptScanner

The main entry point class for scanning prompts and text content.

```python
PromptScanner(provider="openai", api_key=None, model=None)
```

**Parameters:**
- `provider` (str): The LLM provider to use ("openai" or "anthropic"). Default: "openai"
- `api_key` (str, optional): API key for the provider. If None, will look for environment variables
- `model` (str, optional): Model name to use for content evaluation. Provider-specific defaults are used if None

**Attributes:**
- `scanner`: The underlying provider-specific scanner instance
- `decorators`: Accessor for decorator functions

**Methods:**
- `scan(prompt)`: Validate prompt structure and scan for potential issues
- `scan_text(text)`: Scan text for unsafe content
- `scan_content(text)`: Alias for scan_text for backward compatibility
- `add_custom_guardrail(name, guardrail_data)`: Add a custom guardrail
- `remove_custom_guardrail(name)`: Remove a custom guardrail
- `add_custom_category(category_id, category_data)`: Add a custom content category
- `remove_custom_category(category_id)`: Remove a custom content category

### PromptScanResult

Results of content safety evaluation.

**Attributes:**
- `is_safe` (bool): Whether the content is safe
- `category` (PromptCategory, optional): Primary category of detected unsafe content (highest confidence)
- `all_categories` (List[Dict]): List of all detected unsafe categories
- `reasoning` (str): Detailed explanation of why content is unsafe
- `token_usage` (Dict): Token usage metrics for the scan
- `metadata` (Dict): Additional metadata about the scan

**Methods:**
- `to_dict()`: Convert result to a dictionary
- `get_secondary_categories()`: Get all categories except the primary one
- `has_high_confidence_violation(threshold=0.8)`: Check for high confidence violations
- `get_highest_risk_categories(max_count=3)`: Get top risk categories by confidence

### PromptCategory

Represents a category of unsafe content.

**Attributes:**
- `id` (str): Category identifier
- `name` (str): Display name of the category
- `confidence` (float): Confidence score (0.0-1.0)
- `matched_patterns` (List[str]): List of patterns that matched this category

### CustomGuardrail

Pydantic model for defining custom guardrails.

**Attributes:**
- `name` (str): Name of the guardrail
- `type` (str): Type of guardrail (e.g., "moderation", "privacy", "format", "limit")
- `description` (str): Description of what the guardrail prevents
- `patterns` (List[Dict]): List of patterns to match (for regex-based guardrails)
- `threshold` (float, optional): Threshold value for the guardrail
- `max_tokens` (int, optional): Maximum token count (for "limit" type guardrails)
- `formats` (List[str], optional): Allowed formats (for "format" type guardrails)

### CustomCategory

Pydantic model for defining custom content policy categories.

**Attributes:**
- `id` (str): Category identifier
- `name` (str): Display name of the category
- `description` (str): Description of what makes content fall into this category
- `examples` (List[str]): Example content that would fall into this category

### ScanResult

Results of prompt structure validation.

**Attributes:**
- `is_safe` (bool): Whether the prompt structure is valid and safe
- `issues` (List[Dict]): List of issues detected in the prompt

## Provider-Specific Classes

### OpenAIPromptScanner

Scanner implementation for OpenAI.

```python
OpenAIPromptScanner(api_key, model="gpt-4o")
```

### AnthropicPromptScanner

Scanner implementation for Anthropic.

```python
AnthropicPromptScanner(api_key, model="claude-3-haiku-20240307")
```

### BasePromptScanner

Abstract base class for custom scanners.

**Methods that must be implemented by subclasses:**
- `_setup_client()`: Setup the API client for the selected provider
- `_validate_prompt_structure(prompt)`: Validate prompt structure for the provider
- `_scan_prompt(prompt)`: Scan a provider-specific prompt
- `_call_content_evaluation(prompt, text)`: Call the LLM to evaluate content
- `_create_evaluation_prompt(text)`: Create the prompt to send to the LLM for content evaluation

## Decorators

### scan

```python
@scanner.decorators.scan(prompt_param="prompt")
def function_name(prompt, ...):
    # Function body
```

**Parameters:**
- `prompt_param` (str): The parameter name that contains the prompt. Default: "prompt"

**Return value:**
- If content is safe: the return value of the decorated function
- If content is unsafe: returns the `PromptScanResult` object with details about the issue

### safe_completion

```python
@scanner.decorators.safe_completion(prompt_param="prompt")
def function_name(prompt, ...):
    # Function body
```

**Parameters:**
- `prompt_param` (str): The parameter name that contains the prompt. Default: "prompt"

**Return value:**
- If input is safe and output is safe: the return value of the decorated function
- If input is unsafe: returns the `PromptScanResult` object for the input scan
- If output is unsafe: returns the `PromptScanResult` object for the output scan 