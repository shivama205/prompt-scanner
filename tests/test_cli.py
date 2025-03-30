import unittest
import json
import sys
import io
import os
import tempfile
from unittest.mock import patch, MagicMock, mock_open

from prompt_scanner import PromptScanResult
from prompt_scanner.models import CategorySeverity, SeverityLevel, PromptCategory
from prompt_scanner.cli import main, parse_args, get_input_text, format_result, load_guardrails, setup_api_keys
import prompt_scanner.cli  # Import the module directly for __main__ test


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

    # NEW TESTS TO INCREASE COVERAGE

    # Test load_guardrails function
    def test_load_guardrails_valid_json(self):
        test_json = '{"test_guardrail": {"type": "security", "description": "Test description", "patterns": []}}'
        
        # Use mock_open to mock the file read operation
        with patch('builtins.open', mock_open(read_data=test_json)):
            result = load_guardrails('test_file.json')
            self.assertEqual(result, {"test_guardrail": {"type": "security", "description": "Test description", "patterns": []}})
    
    @patch('sys.stderr', new_callable=io.StringIO)
    @patch('sys.exit')
    def test_load_guardrails_invalid_json(self, mock_exit, mock_stderr):
        # Test with invalid JSON
        with patch('builtins.open', mock_open(read_data='invalid json')):
            load_guardrails('test_file.json')
            mock_exit.assert_called_once_with(1)
            self.assertIn("Error: Invalid JSON in guardrails file", mock_stderr.getvalue())
    
    @patch('sys.stderr', new_callable=io.StringIO)
    @patch('sys.exit')
    def test_load_guardrails_not_dict(self, mock_exit, mock_stderr):
        # Test with JSON that's not a dictionary
        with patch('builtins.open', mock_open(read_data='[1, 2, 3]')):
            load_guardrails('test_file.json')
            mock_exit.assert_called_once_with(1)
            self.assertIn("Error: Guardrails file should contain a JSON object", mock_stderr.getvalue())
    
    @patch('sys.stderr', new_callable=io.StringIO)
    @patch('sys.exit')
    def test_load_guardrails_file_error(self, mock_exit, mock_stderr):
        # Test with file that doesn't exist or can't be opened
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            load_guardrails('nonexistent_file.json')
            mock_exit.assert_called_once_with(1)
            self.assertIn("Error loading guardrails file", mock_stderr.getvalue())
    
    # Test get_input_text with verbose mode
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_get_input_text_verbose_text(self, mock_stderr):
        args = MagicMock()
        args.text = "test content"
        args.file = None
        args.stdin = False
        
        result = get_input_text(args, 1)  # Verbose mode
        self.assertEqual(result, "test content")
        self.assertIn("Input: Direct text input", mock_stderr.getvalue())
    
    @patch('builtins.open', new_callable=MagicMock)
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_get_input_text_verbose_file(self, mock_stderr, mock_open):
        mock_file = MagicMock()
        mock_file.read.return_value = "test content from file"
        mock_open.return_value.__enter__.return_value = mock_file
        
        args = MagicMock()
        args.text = None
        args.file = "test.txt"
        args.stdin = False
        
        result = get_input_text(args, 2)  # High verbose mode
        self.assertEqual(result, "test content from file")
        self.assertIn("Input: Reading from file", mock_stderr.getvalue())
        self.assertIn("Read", mock_stderr.getvalue())
    
    @patch('sys.stdin')
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_get_input_text_verbose_stdin(self, mock_stderr, mock_stdin):
        mock_stdin.read.return_value = "test content from stdin"
        
        args = MagicMock()
        args.text = None
        args.file = None
        args.stdin = True
        
        result = get_input_text(args, 1)  # Verbose mode
        self.assertEqual(result, "test content from stdin")
        self.assertIn("Input: Reading from standard input", mock_stderr.getvalue())
    
    @patch('sys.stderr', new_callable=io.StringIO)
    @patch('sys.exit')
    def test_get_input_text_file_error(self, mock_exit, mock_stderr):
        args = MagicMock()
        args.text = None
        args.file = "nonexistent.txt"
        args.stdin = False
        
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            get_input_text(args, 0)
            mock_exit.assert_called_once_with(1)
            self.assertIn("Error reading input file", mock_stderr.getvalue())
    
    # Test format_result with verbose options
    def test_format_result_with_verbose_level_1(self):
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
        
        result = PromptScanResult(
            is_safe=False,
            category=category,
            severity=severity,
            reasoning="This is unsafe content",
            token_usage={"total_tokens": 100}
        )
        
        # Test with verbose level 1
        output = format_result(result, "text", 1, True)
        self.assertIn("Description: Content with high risk", output)
    
    def test_format_result_with_verbose_level_2(self):
        result = PromptScanResult(
            is_safe=True,
            category=None,
            reasoning="This is safe content",
            token_usage={"prompt_tokens": 50, "completion_tokens": 50}
        )
        
        # Test with verbose level 2
        output = format_result(result, "text", 2, True)
        self.assertIn("Token usage:", output)
        self.assertIn("prompt_tokens", output)
    
    # Test setup_api_keys
    @patch('os.environ', {})
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_setup_api_keys_from_args(self, mock_stderr):
        args = MagicMock()
        args.openai_api_key = "test-openai-key"
        args.anthropic_api_key = "test-anthropic-key"
        args.provider = "openai"
        
        setup_api_keys(args, 1)  # Verbose mode
        
        self.assertEqual(os.environ.get("OPENAI_API_KEY"), "test-openai-key")
        self.assertEqual(os.environ.get("ANTHROPIC_API_KEY"), "test-anthropic-key")
        self.assertIn("Using OpenAI API key from command line", mock_stderr.getvalue())
        self.assertIn("Using Anthropic API key from command line", mock_stderr.getvalue())
    
    @patch('os.environ', {})
    @patch('sys.stderr', new_callable=io.StringIO)
    @patch('sys.exit')
    def test_setup_api_keys_missing_openai(self, mock_exit, mock_stderr):
        args = MagicMock()
        args.openai_api_key = None
        args.anthropic_api_key = None
        args.provider = "openai"
        
        setup_api_keys(args, 0)
        
        mock_exit.assert_called_once_with(1)
        self.assertIn("Error: OpenAI API key not found", mock_stderr.getvalue())
    
    @patch('os.environ', {})
    @patch('sys.stderr', new_callable=io.StringIO)
    @patch('sys.exit')
    def test_setup_api_keys_missing_anthropic(self, mock_exit, mock_stderr):
        args = MagicMock()
        args.openai_api_key = None
        args.anthropic_api_key = None
        args.provider = "anthropic"
        
        setup_api_keys(args, 0)
        
        mock_exit.assert_called_once_with(1)
        self.assertIn("Error: Anthropic API key not found", mock_stderr.getvalue())
    
    # Test main with verbose output and exception handling
    @patch('prompt_scanner.cli.PromptScanner')
    @patch('prompt_scanner.cli.parse_args')
    @patch('prompt_scanner.cli.get_input_text')
    @patch('prompt_scanner.cli.format_result')
    @patch('prompt_scanner.cli.setup_api_keys')
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_main_with_verbose(self, mock_stderr, mock_setup_keys, mock_format, mock_get_input, mock_parse_args, mock_scanner_class):
        # Setup mocks
        args = MagicMock()
        args.provider = "openai"
        args.model = "gpt-4o"
        args.verbose = 1  # Verbose mode
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
        
        # Call main
        main()
        
        # Verify verbose output was produced
        self.assertIn("Using provider: openai", mock_stderr.getvalue())
        self.assertIn("Using model: gpt-4o", mock_stderr.getvalue())
        self.assertIn("Scanning content...", mock_stderr.getvalue())
    
    @patch('prompt_scanner.cli.PromptScanner')
    @patch('prompt_scanner.cli.parse_args')
    @patch('prompt_scanner.cli.get_input_text')
    @patch('prompt_scanner.cli.setup_api_keys')  # Patch setup_api_keys to avoid environment issues
    @patch('sys.stderr', new_callable=io.StringIO)
    @patch('sys.exit')
    def test_main_with_exception_in_scan(self, mock_exit, mock_stderr, mock_setup_api_keys, mock_get_input, mock_parse_args, mock_scanner_class):
        # Setup mocks
        args = MagicMock()
        args.provider = "openai"
        args.model = "gpt-4o"
        args.verbose = 0
        args.guardrail_file = None
        args.format = "text"
        args.color = True
        mock_parse_args.return_value = args
        
        mock_get_input.return_value = "Test content"
        
        mock_scanner = MagicMock()
        mock_scanner_class.return_value = mock_scanner
        mock_scanner.scan_text.side_effect = Exception("Scan error")
        
        # Reset the mock before the actual test
        mock_exit.reset_mock()
        
        # Call main which should catch the exception
        main()
        
        # Check that sys.exit was called with 1
        mock_exit.assert_called_with(1)
        self.assertIn("Error during content scanning: Scan error", mock_stderr.getvalue())
    
    # Test exception handling in main with traceback printing
    @patch('sys.stderr', new_callable=io.StringIO)
    @patch('sys.exit')
    @patch('traceback.print_exc')
    def test_main_with_general_exception_verbose(self, mock_traceback, mock_exit, mock_stderr):
        # Patch parse_args to return args with verbose=2
        with patch('prompt_scanner.cli.parse_args') as mock_parse_args:
            # Set up args
            args = MagicMock()
            args.verbose = 2
            mock_parse_args.return_value = args
            
            # Patch setup_api_keys to avoid environment issues
            with patch('prompt_scanner.cli.setup_api_keys'):
                # Patch PromptScanner to raise exception
                with patch('prompt_scanner.cli.PromptScanner') as mock_scanner_class:
                    mock_scanner_class.side_effect = Exception("General error")
                    
                    # Reset mocks
                    mock_exit.reset_mock()
                    mock_traceback.reset_mock()
                    mock_stderr.truncate(0)
                    mock_stderr.seek(0)
                    
                    # Call main
                    main()
                    
                    # Check that exception was caught
                    mock_exit.assert_called_with(1)
                    self.assertIn("Error: General error", mock_stderr.getvalue())
                    # With verbose=2, traceback should be printed
                    mock_traceback.assert_called_once()

    # Test format_result with no-color option
    def test_format_result_with_no_color(self):
        category = PromptCategory(
            id="harmful_content", 
            name="harmful_content",
            confidence=0.9
        )
        
        severity = CategorySeverity(
            level=SeverityLevel.MEDIUM,  # Test MEDIUM level specifically
            score=0.6,
            description="Content with medium risk"
        )
        
        result = PromptScanResult(
            is_safe=False,
            category=category,
            severity=severity,
            reasoning="This is unsafe content",
            token_usage={"total_tokens": 100}
        )
        
        # Test with no colors
        output = format_result(result, "text", 0, False)
        self.assertIn("Content violates", output)
        self.assertIn("MEDIUM", output)
        # Verify no color codes in output
        self.assertNotIn("\033[", output)
    
    # Test format_result with CRITICAL severity
    def test_format_result_with_critical_severity(self):
        category = PromptCategory(
            id="harmful_content", 
            name="harmful_content",
            confidence=0.9
        )
        
        severity = CategorySeverity(
            level=SeverityLevel.CRITICAL,  # Test CRITICAL level specifically
            score=0.9,
            description="Content with critical risk"
        )
        
        result = PromptScanResult(
            is_safe=False,
            category=category,
            severity=severity,
            reasoning="This is critically unsafe content",
            token_usage={"total_tokens": 100}
        )
        
        # Test with colors
        output = format_result(result, "text", 0, True)
        self.assertIn("Content violates", output)
        self.assertIn("CRITICAL", output)
        
        # We should have red color for critical
        self.assertIn("\033[91m", output)
    
    # Skip the __main__ test for now
    @unittest.skip("Testing __main__ is complex and not critical for coverage")
    def test_main_function_call(self):
        pass

    # Test main with verbose and custom guardrails
    @patch('prompt_scanner.cli.PromptScanner')
    @patch('prompt_scanner.cli.parse_args')
    @patch('prompt_scanner.cli.get_input_text')
    @patch('prompt_scanner.cli.format_result')
    @patch('prompt_scanner.cli.setup_api_keys')
    @patch('prompt_scanner.cli.load_guardrails')
    @patch('sys.stderr', new_callable=io.StringIO)
    def test_main_verbose_with_guardrails(self, mock_stderr, mock_load_guardrails, mock_setup_keys, 
                                        mock_format, mock_get_input, mock_parse_args, mock_scanner_class):
        # Setup mocks
        args = MagicMock()
        args.provider = "openai"
        args.model = "gpt-4o"
        args.verbose = 1  # Verbose mode
        args.format = "text"
        args.color = True
        args.guardrail_file = "custom_guardrails.json"  # Add guardrail file
        mock_parse_args.return_value = args
        
        mock_get_input.return_value = "Safe content"
        
        # Setup guardrails mock
        guardrails = {
            "custom_rule": {
                "type": "security",
                "description": "Test description",
                "patterns": []
            }
        }
        mock_load_guardrails.return_value = guardrails
        
        mock_scanner = MagicMock()
        mock_scanner_class.return_value = mock_scanner
        
        safe_result = MagicMock()
        safe_result.is_safe = True
        mock_scanner.scan_text.return_value = safe_result
        
        mock_format.return_value = "✅ Content is safe"
        
        # Call main
        main()
        
        # Verify verbose output was produced for guardrails
        self.assertIn("Loading custom guardrails from", mock_stderr.getvalue())
        self.assertIn("Adding custom guardrail: custom_rule", mock_stderr.getvalue())

if __name__ == '__main__':
    unittest.main() 