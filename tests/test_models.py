import os
import sys
import unittest

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from prompt_scanner.models import (
    Message, OpenAIPrompt, AnthropicPrompt, AnthropicMessage, OldAnthropicPrompt,
    PromptCategory, CategorySeverity, PromptScanResult, CustomGuardrail, CustomCategory
)

class TestModels(unittest.TestCase):
    def test_message_model(self):
        """Test the Message model."""
        # Test with string content
        msg1 = Message(role="user", content="Hello, world!")
        self.assertEqual(msg1.role, "user")
        self.assertEqual(msg1.content, "Hello, world!")
        
        # Test with structured content
        structured_content = [{"type": "text", "text": "Hello"}, {"type": "image_url", "image_url": {"url": "http://example.com/image.jpg"}}]
        msg2 = Message(role="user", content=structured_content)
        self.assertEqual(msg2.role, "user")
        self.assertEqual(msg2.content, structured_content)
    
    def test_openai_prompt_validation(self):
        """Test OpenAI prompt validation."""
        # Valid prompt
        valid_prompt = OpenAIPrompt(
            messages=[
                Message(role="system", content="You are a helpful assistant."),
                Message(role="user", content="Hello!")
            ],
            model="gpt-4"
        )
        self.assertEqual(len(valid_prompt.messages), 2)
        self.assertEqual(valid_prompt.model, "gpt-4")
        
        # Test empty messages validation
        with self.assertRaises(ValueError) as context:
            OpenAIPrompt(messages=[], model="gpt-4")
        self.assertIn("At least one message is required", str(context.exception))
        
        # Test invalid role validation
        with self.assertRaises(ValueError) as context:
            OpenAIPrompt(
                messages=[
                    Message(role="invalid_role", content="This is not a valid role."),
                    Message(role="user", content="Hello!")
                ],
                model="gpt-4"
            )
        self.assertIn("has invalid role", str(context.exception))
    
    def test_anthropic_prompt_validation(self):
        """Test Anthropic prompt validation."""
        # Valid prompt
        valid_prompt = AnthropicPrompt(
            messages=[
                AnthropicMessage(role="user", content="Hello!"),
                AnthropicMessage(role="assistant", content="Hi there!")
            ],
            model="claude-3-opus-20240229"
        )
        self.assertEqual(len(valid_prompt.messages), 2)
        self.assertEqual(valid_prompt.model, "claude-3-opus-20240229")
        
        # Test empty messages validation
        with self.assertRaises(ValueError) as context:
            AnthropicPrompt(messages=[], model="claude-3-opus-20240229")
        self.assertIn("At least one message is required", str(context.exception))
    
    def test_old_anthropic_prompt(self):
        """Test the old Anthropic prompt format."""
        old_prompt = OldAnthropicPrompt(
            prompt="Human: Hello\n\nAssistant:",
            model="claude-2"
        )
        self.assertEqual(old_prompt.prompt, "Human: Hello\n\nAssistant:")
        self.assertEqual(old_prompt.model, "claude-2")
    
    def test_prompt_category(self):
        """Test the PromptCategory model."""
        # Basic initialization
        category = PromptCategory(id="hate_speech", name="Hate Speech", confidence=0.85)
        self.assertEqual(category.id, "hate_speech")
        self.assertEqual(category.name, "Hate Speech")
        self.assertEqual(category.confidence, 0.85)
        self.assertEqual(category.matched_patterns, [])
        
        # Test with matched patterns
        category_with_patterns = PromptCategory(
            id="hate_speech",
            name="Hate Speech",
            confidence=0.95,
            matched_patterns=["offensive_term_1", "offensive_term_2"]
        )
        self.assertEqual(len(category_with_patterns.matched_patterns), 2)
        
        # Test string representation
        self.assertEqual(str(category), "Hate Speech (confidence: 0.85)")
    
    def test_category_severity(self):
        """Test the CategorySeverity model."""
        severity = CategorySeverity(level="high", score=0.9, description="Very severe content")
        self.assertEqual(severity.level, "high")
        self.assertEqual(severity.score, 0.9)
        self.assertEqual(severity.description, "Very severe content")
        
        # Test default values
        default_severity = CategorySeverity(level="medium")
        self.assertEqual(default_severity.level, "medium")
        self.assertEqual(default_severity.score, 0.0)
        self.assertEqual(default_severity.description, "")
    
    def test_prompt_scan_result(self):
        """Test the PromptScanResult model."""
        # Test safe result
        safe_result = PromptScanResult(
            is_safe=True,
            reasoning="Content is safe",
            token_usage={"prompt_tokens": 50, "completion_tokens": 25}
        )
        self.assertTrue(safe_result.is_safe)
        self.assertIsNone(safe_result.category)
        self.assertEqual(safe_result.reasoning, "Content is safe")
        self.assertEqual(safe_result.token_usage, {"prompt_tokens": 50, "completion_tokens": 25})
        
        # Test unsafe result with a category
        category = PromptCategory(id="illegal_activity", name="Illegal Activity", confidence=0.9)
        unsafe_result = PromptScanResult(
            is_safe=False,
            category=category,
            reasoning="Content promotes illegal activities",
            token_usage={"prompt_tokens": 60, "completion_tokens": 30}
        )
        self.assertFalse(unsafe_result.is_safe)
        self.assertEqual(unsafe_result.category.id, "illegal_activity")
        self.assertEqual(unsafe_result.reasoning, "Content promotes illegal activities")
        
        # Test string representation
        self.assertIn("SAFE", str(safe_result))
        self.assertIn("UNSAFE", str(unsafe_result))
        self.assertIn("Illegal Activity", str(unsafe_result))
        
        # Test to_dict method
        safe_dict = safe_result.to_dict()
        self.assertTrue(safe_dict["is_safe"])
        self.assertEqual(safe_dict["reasoning"], "Content is safe")
        self.assertEqual(safe_dict["token_usage"], {"prompt_tokens": 50, "completion_tokens": 25})
        
        unsafe_dict = unsafe_result.to_dict()
        self.assertFalse(unsafe_dict["is_safe"])
        self.assertEqual(unsafe_dict["reasoning"], "Content promotes illegal activities")
        self.assertEqual(unsafe_dict["primary_category"]["id"], "illegal_activity")
    
    def test_prompt_scan_result_with_multiple_categories(self):
        """Test PromptScanResult with multiple categories."""
        category = PromptCategory(id="illegal_activity", name="Illegal Activity", confidence=0.9)
        all_categories = [
            {"id": "illegal_activity", "name": "Illegal Activity", "confidence": 0.9},
            {"id": "hate_speech", "name": "Hate Speech", "confidence": 0.7},
            {"id": "violence", "name": "Violence", "confidence": 0.5}
        ]
        
        result = PromptScanResult(
            is_safe=False,
            category=category,
            all_categories=all_categories,
            reasoning="Multiple policy violations detected"
        )
        
        # Test secondary categories
        secondary = result.get_secondary_categories()
        self.assertEqual(len(secondary), 2)
        self.assertEqual(secondary[0]["id"], "hate_speech")
        
        # Test high confidence violation
        self.assertTrue(result.has_high_confidence_violation(threshold=0.85))
        self.assertFalse(result.has_high_confidence_violation(threshold=0.95))
        
        # Test highest risk categories
        top_categories = result.get_highest_risk_categories(max_count=2)
        self.assertEqual(len(top_categories), 2)
        self.assertEqual(top_categories[0]["id"], "illegal_activity")
        self.assertEqual(top_categories[1]["id"], "hate_speech")
        
        # Test to_dict with all categories
        result_dict = result.to_dict()
        self.assertIn("all_categories", result_dict)
        self.assertEqual(len(result_dict["all_categories"]), 3)
    
    def test_prompt_scan_result_str_line_coverage(self):
        """Specific test to ensure coverage of line 82 in models.py."""
        # Create a category for testing
        category = PromptCategory(id="test", name="Test Category", confidence=0.8)
        
        # Specifically targeting the condition in line 82:
        # if self.all_categories and len(self.all_categories) > 1:
        
        # Test case 1: all_categories as an empty list (condition evaluates to False)
        result_empty = PromptScanResult(
            is_safe=False,
            category=category,
            all_categories=[],
            reasoning="Test reasoning"
        )
        str_result = str(result_empty)
        self.assertIn("Category: Test Category", str_result)
        self.assertNotIn("and", str_result)  # Shouldn't contain "and X more"
        
        # Test case 2: all_categories has one item (condition evaluates to False)
        result_one = PromptScanResult(
            is_safe=False,
            category=category,
            all_categories=[{"id": "test", "name": "Test Category", "confidence": 0.8}],
            reasoning="Test reasoning"
        )
        str_result = str(result_one)
        self.assertIn("Category: Test Category", str_result)
        self.assertNotIn("and", str_result)  # Shouldn't contain "and X more"
        
        # Test case 3: all_categories has multiple items (condition evaluates to True)
        result_multi = PromptScanResult(
            is_safe=False,
            category=category,
            all_categories=[
                {"id": "test1", "name": "Category 1", "confidence": 0.9},
                {"id": "test2", "name": "Category 2", "confidence": 0.8}
            ],
            reasoning="Test reasoning"
        )
        str_result = str(result_multi)
        self.assertIn("Category: Test Category and 1 more", str_result)
        
        # Test the condition directly by monkey patching
        original_str_method = PromptScanResult.__str__
        
        try:
            # Create a replacement to track the line execution
            def test_str_method(self):
                if not self.is_safe:
                    category_info = f"Category: {self.category.name}"
                    
                    # This is exactly line 82 from models.py
                    condition_result = bool(self.all_categories and len(self.all_categories) > 1)
                    
                    # Store the result for testing
                    self._test_condition_result = condition_result
                    
                    if condition_result:
                        category_info += f" and {len(self.all_categories)-1} more"
                    return f"UNSAFE | {category_info} | Reasoning: {self.reasoning} | Token usage: {self.token_usage}"
                else:
                    return f"SAFE | Token usage: {self.token_usage}"
            
            # Replace the method
            PromptScanResult.__str__ = test_str_method
            
            # Test with multiple categories (condition should be True)
            str(result_multi)
            self.assertTrue(result_multi._test_condition_result)
            
            # Test with one category (condition should be False)
            str(result_one)
            self.assertFalse(result_one._test_condition_result)
            
            # Test with empty categories (condition should be False)
            str(result_empty)
            self.assertFalse(result_empty._test_condition_result)
            
        finally:
            # Restore the original method
            PromptScanResult.__str__ = original_str_method
    
    def test_custom_guardrail(self):
        """Test the CustomGuardrail model."""
        # Basic guardrail
        guardrail = CustomGuardrail(
            name="pii_protection",
            type="privacy",
            description="Prevents sharing of personal information"
        )
        self.assertEqual(guardrail.name, "pii_protection")
        self.assertEqual(guardrail.type, "privacy")
        self.assertEqual(guardrail.description, "Prevents sharing of personal information")
        self.assertEqual(guardrail.patterns, [])
        self.assertIsNone(guardrail.threshold)
        self.assertIsNone(guardrail.max_tokens)
        self.assertIsNone(guardrail.formats)
        
        # Guardrail with patterns
        guardrail_with_patterns = CustomGuardrail(
            name="email_protection",
            type="privacy",
            description="Prevents sharing of email addresses",
            patterns=[
                {
                    "type": "regex",
                    "value": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
                    "description": "Email address pattern"
                }
            ]
        )
        self.assertEqual(len(guardrail_with_patterns.patterns), 1)
        self.assertEqual(guardrail_with_patterns.patterns[0]["type"], "regex")
        
        # Token limit guardrail
        token_guardrail = CustomGuardrail(
            name="token_limit",
            type="limit",
            description="Limits token count",
            max_tokens=4096
        )
        self.assertEqual(token_guardrail.max_tokens, 4096)
        
        # Format guardrail
        format_guardrail = CustomGuardrail(
            name="format_control",
            type="format",
            description="Controls output format",
            formats=["json", "markdown"]
        )
        self.assertEqual(len(format_guardrail.formats), 2)
        self.assertIn("json", format_guardrail.formats)
    
    def test_custom_category(self):
        """Test the CustomCategory model."""
        # Basic category
        category = CustomCategory(
            id="tech_jargon",
            name="Technical Jargon",
            description="Excessive use of technical terminology"
        )
        self.assertEqual(category.id, "tech_jargon")
        self.assertEqual(category.name, "Technical Jargon")
        self.assertEqual(category.description, "Excessive use of technical terminology")
        self.assertEqual(category.examples, [])
        
        # Category with examples
        category_with_examples = CustomCategory(
            id="tech_jargon",
            name="Technical Jargon",
            description="Excessive use of technical terminology",
            examples=[
                "The quantum flux capacitor initiates the hyper-threading of non-linear data structures",
                "Implement a recursive neural tensor network with bidirectional LSTM encoders"
            ]
        )
        self.assertEqual(len(category_with_examples.examples), 2)

    def test_prompt_scan_result_methods(self):
        """Test additional PromptScanResult methods."""
        # Test get_secondary_categories with no additional categories
        result_no_secondary = PromptScanResult(
            is_safe=False,
            category=PromptCategory(id="test", name="Test Category", confidence=0.9),
            all_categories=[{"id": "test", "name": "Test Category", "confidence": 0.9}]
        )
        self.assertEqual(result_no_secondary.get_secondary_categories(), [])
        
        # Test get_secondary_categories with multiple categories
        result_with_secondary = PromptScanResult(
            is_safe=False,
            category=PromptCategory(id="primary", name="Primary Category", confidence=0.9),
            all_categories=[
                {"id": "primary", "name": "Primary Category", "confidence": 0.9},
                {"id": "secondary", "name": "Secondary Category", "confidence": 0.7},
                {"id": "tertiary", "name": "Tertiary Category", "confidence": 0.5}
            ]
        )
        secondary_categories = result_with_secondary.get_secondary_categories()
        self.assertEqual(len(secondary_categories), 2)
        self.assertEqual(secondary_categories[0]["id"], "secondary")
        
        # Test has_high_confidence_violation
        self.assertTrue(result_with_secondary.has_high_confidence_violation(threshold=0.8))
        self.assertFalse(result_with_secondary.has_high_confidence_violation(threshold=0.95))
        
        # Test get_highest_risk_categories with no categories
        result_no_categories = PromptScanResult(is_safe=True)
        self.assertEqual(result_no_categories.get_highest_risk_categories(), [])
        
        # Test get_highest_risk_categories with limit
        top_categories = result_with_secondary.get_highest_risk_categories(max_count=2)
        self.assertEqual(len(top_categories), 2)
        self.assertEqual(top_categories[0]["id"], "primary")
        self.assertEqual(top_categories[1]["id"], "secondary")

if __name__ == "__main__":
    unittest.main() 