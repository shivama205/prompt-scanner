import os
import sys
import unittest
from unittest.mock import patch, mock_open, MagicMock

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from prompt_scanner import PromptScanner, ScanResult
from prompt_scanner.models import CustomGuardrail, CustomCategory

class TestCustomGuardrails(unittest.TestCase):
    def setUp(self):
        # Set up mocks similar to test_scanner.py
        self.open_mock = mock_open()
        self.open_patcher = patch('builtins.open', self.open_mock)
        self.open_patcher.start()

        # Mock yaml.safe_load to return empty data (we'll add custom guardrails)
        self.yaml_patcher = patch('yaml.safe_load', return_value={})
        self.mock_yaml_load = self.yaml_patcher.start()
        
        # Mock re.compile to prevent actual regex compilation
        self.re_patcher = patch('re.compile', return_value=MagicMock())
        self.mock_re_compile = self.re_patcher.start()
        
        # Mock re.search to control regex search results
        self.re_search_patcher = patch('re.search')
        self.mock_re_search = self.re_search_patcher.start()
        
        # Mock the OpenAI client
        self.openai_patcher = patch('openai.OpenAI')
        self.mock_openai = self.openai_patcher.start()
        self.mock_openai.return_value = MagicMock()
        
        # Create scanner instance with mocked dependencies
        self.scanner = PromptScanner(provider="openai", api_key="fake-api-key")
        
        # Add a custom guardrail for testing
        self.test_guardrail = {
            "type": "privacy",
            "description": "Test guardrail for PII detection",
            "patterns": [
                {
                    "type": "regex",
                    "value": "test_pattern",
                    "description": "Test pattern"
                }
            ]
        }
        
        # Add a custom category for testing
        self.test_category = {
            "name": "Test Category",
            "description": "Test category for unsafe content",
            "examples": ["This is a test example"]
        }
    
    def tearDown(self):
        self.open_patcher.stop()
        self.yaml_patcher.stop()
        self.re_patcher.stop()
        self.re_search_patcher.stop()
        self.openai_patcher.stop()
    
    def test_add_custom_guardrail(self):
        # Add a custom guardrail
        self.scanner.add_custom_guardrail("test_guardrail", self.test_guardrail)
        
        # Verify it was added to the scanner's custom_guardrails dictionary
        self.assertIn("test_guardrail", self.scanner.scanner.custom_guardrails)
        self.assertEqual(
            self.scanner.scanner.custom_guardrails["test_guardrail"]["description"],
            "Test guardrail for PII detection"
        )
    
    def test_remove_custom_guardrail(self):
        # Add and then remove a custom guardrail
        self.scanner.add_custom_guardrail("test_guardrail", self.test_guardrail)
        result = self.scanner.remove_custom_guardrail("test_guardrail")
        
        # Verify it was removed
        self.assertTrue(result)
        self.assertNotIn("test_guardrail", self.scanner.scanner.custom_guardrails)
        
        # Try removing a non-existent guardrail
        result = self.scanner.remove_custom_guardrail("nonexistent")
        self.assertFalse(result)
    
    def test_add_custom_category(self):
        # Add a custom category
        self.scanner.add_custom_category("test_category", self.test_category)
        
        # Verify it was added
        self.assertIn("policies", self.scanner.scanner.custom_categories)
        self.assertIn("test_category", self.scanner.scanner.custom_categories["policies"])
        self.assertEqual(
            self.scanner.scanner.custom_categories["policies"]["test_category"]["name"],
            "Test Category"
        )
    
    def test_remove_custom_category(self):
        # Add and then remove a custom category
        self.scanner.add_custom_category("test_category", self.test_category)
        result = self.scanner.remove_custom_category("test_category")
        
        # Verify it was removed
        self.assertTrue(result)
        self.assertNotIn(
            "test_category", 
            self.scanner.scanner.custom_categories.get("policies", {})
        )
        
        # Try removing a non-existent category
        result = self.scanner.remove_custom_category("nonexistent")
        self.assertFalse(result)
    
    def test_custom_guardrail_violation(self):
        # Add a custom guardrail
        self.scanner.add_custom_guardrail("test_guardrail", self.test_guardrail)
        
        # Set up the re.search mock to return a match for our test pattern
        self.mock_re_search.return_value = True
        
        # Create a test prompt that should match our custom guardrail pattern
        test_prompt = {
            "messages": [
                {"role": "user", "content": "This contains the test_pattern that should be flagged"}
            ]
        }
        
        # Scan the prompt
        result = self.scanner.scan(test_prompt)
        
        # Verify the scan result shows it's not safe due to our custom guardrail
        self.assertFalse(result.is_safe)
        
        # Find the issue related to our custom guardrail
        custom_guardrail_issue = None
        for issue in result.issues:
            if issue.get("type") == "guardrail_violation" and issue.get("guardrail") == "test_guardrail":
                custom_guardrail_issue = issue
                break
        
        self.assertIsNotNone(custom_guardrail_issue)
        self.assertEqual(custom_guardrail_issue["description"], "Test guardrail for PII detection")
        self.assertTrue(custom_guardrail_issue.get("custom", False))
    
    def test_custom_guardrail_using_pydantic_model(self):
        # Create a guardrail using the Pydantic model
        guardrail = CustomGuardrail(
            name="pydantic_guardrail",
            type="privacy",
            description="Guardrail created with Pydantic model",
            patterns=[
                {
                    "type": "regex",
                    "value": "test_pydantic_pattern",
                    "description": "Test pattern from Pydantic model"
                }
            ]
        )
        
        # Add it to the scanner
        self.scanner.add_custom_guardrail(guardrail.name, guardrail.model_dump())
        
        # Verify it was added correctly
        self.assertIn(guardrail.name, self.scanner.scanner.custom_guardrails)
        self.assertEqual(
            self.scanner.scanner.custom_guardrails[guardrail.name]["description"],
            "Guardrail created with Pydantic model"
        )

if __name__ == "__main__":
    unittest.main() 