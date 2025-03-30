import unittest
from unittest.mock import patch, MagicMock
from prompt_scanner import OpenAIPromptScanner, AnthropicPromptScanner

class TestScannerInitialization(unittest.TestCase):
    def test_scanner_init(self):
        """Test basic scanner initialization."""
        # Mock dependencies
        with patch('yaml.safe_load', return_value={}):
            with patch('re.compile', return_value=MagicMock()):
                with patch('openai.OpenAI') as mock_openai:
                    # Create scanner with default values
                    scanner = OpenAIPromptScanner(api_key="test-key")
                    
                    # Check model default
                    self.assertEqual(scanner.model, "gpt-4o")
                    
                    # Check api key is set
                    self.assertEqual(scanner.api_key, "test-key")

if __name__ == "__main__":
    unittest.main() 