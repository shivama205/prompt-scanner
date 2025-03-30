import unittest
import json
import sys
import io
from unittest.mock import patch, MagicMock

from prompt_scanner import PromptScanResult
from prompt_scanner.models import CategorySeverity, SeverityLevel, PromptCategory
from prompt_scanner.cli import main, parse_args, get_input_text, format_result


class TestCLI(unittest.TestCase):
    def test_parse_args(self):
        with patch('sys.argv', ['prompt-scanner', '--text', 'test content']):
            args = parse_args()
            self.assertEqual(args.text, 'test content')
            self.assertEqual(args.provider, 'openai')
            self.assertEqual(args.format, 'text')
            self.assertEqual(args.verbose, 0)  # verbose is now a count
    
    def test_get_input_text_from_text_arg(self):
        args = MagicMock()
        args.text = "test content"
        args.file = None
        args.stdin = False
        
        result = get_input_text(args, 0)  # Add verbose parameter
        self.assertEqual(result, "test content")
    
    @patch('builtins.open', new_callable=MagicMock)
    def test_get_input_text_from_file(self, mock_open):
        mock_file = MagicMock()
        mock_file.read.return_value = "test content from file"
        mock_open.return_value.__enter__.return_value = mock_file
        
        args = MagicMock()
        args.text = None
        args.file = "test.txt"
        args.stdin = False
        
        result = get_input_text(args, 0)  # Add verbose parameter
        self.assertEqual(result, "test content from file")
        mock_open.assert_called_once_with("test.txt", 'r')
    
    @patch('sys.stdin')
    def test_get_input_text_from_stdin(self, mock_stdin):
        mock_stdin.read.return_value = "test content from stdin"
        
        args = MagicMock()
        args.text = None
        args.file = None
        args.stdin = True
        
        result = get_input_text(args, 0)  # Add verbose parameter
        self.assertEqual(result, "test content from stdin")
    
    # Test format_result function directly
    def test_cli_format_result_safe(self):
        # Create a safe result
        result = PromptScanResult(
            is_safe=True,
            category=None,
            reasoning="This is safe content",
            token_usage={"total_tokens": 100}
        )
        
        # Call the format_result function directly
        output = format_result(result, "text", 0, True)
        
        # Verify output contains expected text
        self.assertIn("✅ Content is safe", output)
        self.assertIn("This is safe content", output)
    
    def test_cli_format_result_unsafe(self):
        # Create a proper category and severity using actual models
        category = PromptCategory(
            id="harmful_content",
            name="harmful_content",
            confidence=0.9
        )
        
        severity = CategorySeverity(
            level=SeverityLevel.HIGH,
            score=0.8,
            description="Content with high risk"
        )
        
        # Create a result with the proper models
        result = PromptScanResult(
            is_safe=False,
            category=category,
            severity=severity,
            reasoning="This is unsafe content",
            token_usage={"total_tokens": 100}
        )
        
        # Call the format_result function with text format
        output = format_result(result, "text", 0, True)
        
        # Verify output contains expected text
        self.assertIn("❌ Content violates", output)
        self.assertIn("harmful_content", output)
        self.assertIn("HIGH", output)
        self.assertIn("This is unsafe content", output)
        
        # Test with different severity levels
        for level in [SeverityLevel.LOW, SeverityLevel.MEDIUM, SeverityLevel.CRITICAL]:
            result.severity.level = level
            output = format_result(result, "text", 0, True)
            self.assertIn(level.value, output)
    
    def test_cli_format_result_json(self):
        # Test safe content with JSON format
        safe_result = PromptScanResult(
            is_safe=True,
            category=None,
            reasoning="This is safe content",
            token_usage={"total_tokens": 100}
        )
        
        json_output = format_result(safe_result, "json", 0, True)
        json_data = json.loads(json_output)
        
        self.assertTrue(json_data["is_safe"])
        self.assertIsNone(json_data["category"])
        self.assertIsNone(json_data["severity"])
        self.assertEqual(json_data["reasoning"], "This is safe content")
        
        # Test unsafe content with JSON format
        category = PromptCategory(
            id="harmful_content",
            name="harmful_content",
            confidence=0.9
        )
        
        severity = CategorySeverity(
            level=SeverityLevel.HIGH,
            score=0.8,
            description="Content with high risk"
        )
        
        unsafe_result = PromptScanResult(
            is_safe=False,
            category=category,
            severity=severity,
            reasoning="This is unsafe content",
            token_usage={"total_tokens": 100}
        )
        
        json_output = format_result(unsafe_result, "json", 0, True)
        json_data = json.loads(json_output)
        
        self.assertFalse(json_data["is_safe"])
        self.assertEqual(json_data["category"], "harmful_content")
        self.assertEqual(json_data["severity"], "HIGH")
        self.assertEqual(json_data["reasoning"], "This is unsafe content")
        
        # Test with verbose output (should include severity details)
        json_output = format_result(unsafe_result, "json", 2, True)
        json_data = json.loads(json_output)
        
        self.assertIn("severity_details", json_data)
        self.assertEqual(json_data["severity_details"]["level"], "HIGH")
        self.assertEqual(json_data["severity_details"]["score"], 0.8)
        self.assertEqual(json_data["severity_details"]["description"], "Content with high risk")
    
    @patch('prompt_scanner.cli.PromptScanner')
    @patch('prompt_scanner.cli.parse_args')
    @patch('prompt_scanner.cli.get_input_text')
    @patch('prompt_scanner.cli.format_result')
    @patch('prompt_scanner.cli.setup_api_keys')  # Add this patch
    def test_main_safe_content(self, mock_setup_keys, mock_format, mock_get_input, mock_parse_args, mock_scanner_class):
        # Setup mocks
        args = MagicMock()
        args.provider = "openai"
        args.model = "gpt-4o"
        args.verbose = 0
        args.format = "text"
        args.color = True
        args.guardrail_file = None
        mock_parse_args.return_value = args
        
        mock_get_input.return_value = "Safe content"
        
        mock_scanner = MagicMock()
        mock_scanner_class.return_value = mock_scanner
        
        safe_result = MagicMock()
        safe_result.is_safe = True
        mock_scanner.scan_text.return_value = safe_result
        
        mock_format.return_value = "✅ Content is safe"
        
        # Call main and verify exit code is 0 for safe content
        with patch('sys.exit') as mock_exit:
            main()
            mock_exit.assert_not_called()
    
    @patch('prompt_scanner.cli.PromptScanner')
    @patch('prompt_scanner.cli.parse_args')
    @patch('prompt_scanner.cli.get_input_text')
    @patch('prompt_scanner.cli.format_result')
    @patch('prompt_scanner.cli.setup_api_keys')  # Add this patch
    def test_main_unsafe_content(self, mock_setup_keys, mock_format, mock_get_input, mock_parse_args, mock_scanner_class):
        # Setup mocks
        args = MagicMock()
        args.provider = "openai"
        args.model = "gpt-4o"
        args.verbose = 0
        args.format = "text"
        args.color = True
        args.guardrail_file = None
        mock_parse_args.return_value = args
        
        mock_get_input.return_value = "Unsafe content"
        
        mock_scanner = MagicMock()
        mock_scanner_class.return_value = mock_scanner
        
        unsafe_result = MagicMock()
        unsafe_result.is_safe = False
        mock_scanner.scan_text.return_value = unsafe_result
        
        mock_format.return_value = "❌ Content violates: harmful_content"
        
        # Call main and verify exit code is 1 for unsafe content
        with patch('sys.exit') as mock_exit:
            main()
            mock_exit.assert_called_once_with(1)
    
    @patch('prompt_scanner.cli.load_guardrails')
    @patch('prompt_scanner.cli.PromptScanner')
    @patch('prompt_scanner.cli.parse_args')
    @patch('prompt_scanner.cli.get_input_text')
    @patch('prompt_scanner.cli.format_result') 
    @patch('prompt_scanner.cli.setup_api_keys')  # Add this patch
    def test_main_with_custom_guardrails(self, mock_setup_keys, mock_format, mock_get_input, mock_parse_args, 
                                        mock_scanner_class, mock_load_guardrails):
        # Setup mocks
        args = MagicMock()
        args.provider = "openai"
        args.model = "gpt-4o"
        args.verbose = 0
        args.format = "text"
        args.color = True
        args.guardrail_file = "guardrails.json"
        mock_parse_args.return_value = args
        
        mock_get_input.return_value = "Content with API keys"
        
        mock_scanner = MagicMock()
        mock_scanner_class.return_value = mock_scanner
        
        guardrails = {
            "api_key_protection": {
                "type": "privacy",
                "description": "Prevents sharing of API keys",
                "patterns": []
            }
        }
        mock_load_guardrails.return_value = guardrails
        
        unsafe_result = MagicMock()
        unsafe_result.is_safe = False
        mock_scanner.scan_text.return_value = unsafe_result
        
        mock_format.return_value = "❌ Content violates: api_key_protection"
        
        # Call main
        with patch('sys.exit') as mock_exit:
            main()
            mock_scanner.add_custom_guardrail.assert_called_once_with("api_key_protection", 
                                                                    guardrails["api_key_protection"])
            mock_exit.assert_called_once_with(1)

if __name__ == '__main__':
    unittest.main() 