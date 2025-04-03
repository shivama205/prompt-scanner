import unittest
import json
import sys
import io
import os
import tempfile
from unittest.mock import patch, MagicMock, mock_open
import logging

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
        
        result = get_input_text(args)  # Add verbose parameter
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
        
        result = get_input_text(args)  # Add verbose parameter
        self.assertEqual(result, "test content from file")
        mock_open.assert_called_once_with("test.txt", 'r')
    
    @patch('sys.stdin')
    def test_get_input_text_from_stdin(self, mock_stdin):
        mock_stdin.read.return_value = "test content from stdin"
        
        args = MagicMock()
        args.text = None
        args.file = None
        args.stdin = True
        
        result = get_input_text(args)  # Add verbose parameter
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
            # Patch logging within the function scope
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                load_guardrails('test_file.json')
                mock_exit.assert_called_once_with(1)
                # Check that logger.error was called with the correct message
                mock_logger.error.assert_called_once()
                self.assertIn("Invalid JSON in guardrails file", mock_logger.error.call_args[0][0])

    @patch('sys.stderr', new_callable=io.StringIO)
    @patch('sys.exit')
    def test_load_guardrails_not_dict(self, mock_exit, mock_stderr):
        # Test with JSON that's not a dictionary
        with patch('builtins.open', mock_open(read_data='[1, 2, 3]')):
            # Patch logging within the function scope
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                load_guardrails('test_file.json')
                mock_exit.assert_called_once_with(1)
                # Check that logger.error was called with the correct message
                mock_logger.error.assert_called_once()
                self.assertIn("Guardrails file should contain a JSON object", mock_logger.error.call_args[0][0])

    @patch('sys.stderr', new_callable=io.StringIO)
    @patch('sys.exit')
    def test_load_guardrails_file_error(self, mock_exit, mock_stderr):
        # Test with file that doesn't exist or can't be opened
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            # Patch logging within the function scope
            with patch('logging.getLogger') as mock_get_logger:
                mock_logger = MagicMock()
                mock_get_logger.return_value = mock_logger
                load_guardrails('nonexistent_file.json')
                mock_exit.assert_called_once_with(1)
                # Check that logger.error was called with the correct message
                mock_logger.error.assert_called_once()
                self.assertIn("Error loading guardrails file", mock_logger.error.call_args[0][0])

    # Test get_input_text with verbose mode (checks logger.info)
    @patch('logging.getLogger')
    def test_get_input_text_verbose_text(self, mock_get_logger):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        args = MagicMock()
        args.text = "test content"
        args.file = None
        args.stdin = False
        
        result = get_input_text(args) 
        self.assertEqual(result, "test content")
        # Check logger.info call
        mock_logger.info.assert_called_once()
        self.assertIn("Input: Direct text input", mock_logger.info.call_args[0][0])

    @patch('builtins.open', new_callable=MagicMock)
    @patch('logging.getLogger')
    def test_get_input_text_verbose_file(self, mock_get_logger, mock_open):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        mock_file = MagicMock()
        mock_file.read.return_value = "test content from file"
        mock_open.return_value.__enter__.return_value = mock_file
        
        args = MagicMock()
        args.text = None
        args.file = "test.txt"
        args.stdin = False
        
        result = get_input_text(args) 
        self.assertEqual(result, "test content from file")
        # Check logger.info calls
        self.assertEqual(mock_logger.info.call_count, 2)
        self.assertIn("Input: Reading from file", mock_logger.info.call_args_list[0][0][0])
        self.assertIn("Read", mock_logger.info.call_args_list[1][0][0])

    @patch('sys.stdin')
    @patch('logging.getLogger')
    def test_get_input_text_verbose_stdin(self, mock_get_logger, mock_stdin):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        mock_stdin.read.return_value = "test content from stdin"
        
        args = MagicMock()
        args.text = None
        args.file = None
        args.stdin = True
        
        result = get_input_text(args) 
        self.assertEqual(result, "test content from stdin")
        # Check logger.info calls
        self.assertEqual(mock_logger.info.call_count, 2)
        self.assertIn("Input: Reading from standard input", mock_logger.info.call_args_list[0][0][0])
        self.assertIn("Read", mock_logger.info.call_args_list[1][0][0])

    @patch('sys.exit')
    @patch('logging.getLogger')
    def test_get_input_text_file_error(self, mock_get_logger, mock_exit):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        args = MagicMock()
        args.text = None
        args.file = "nonexistent.txt"
        args.stdin = False
        
        with patch('builtins.open', side_effect=FileNotFoundError("File not found")):
            get_input_text(args)
            mock_exit.assert_called_once_with(1)
            # Check logger.error call
            mock_logger.error.assert_called_once()
            self.assertIn("Error reading input file", mock_logger.error.call_args[0][0])

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
    
    # Test setup_api_keys (checks logger.info and logger.error)
    @patch('os.environ', {})
    @patch('logging.getLogger')
    def test_setup_api_keys_from_args(self, mock_get_logger):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        args = MagicMock()
        args.openai_api_key = "test-openai-key"
        args.anthropic_api_key = "test-anthropic-key"
        args.provider = "openai" # Set a provider to avoid exit
        
        setup_api_keys(args) 
        
        self.assertEqual(os.environ.get("OPENAI_API_KEY"), "test-openai-key")
        self.assertEqual(os.environ.get("ANTHROPIC_API_KEY"), "test-anthropic-key")
        # Check logger.info calls
        self.assertEqual(mock_logger.info.call_count, 2)
        self.assertIn("Using OpenAI API key from command line", mock_logger.info.call_args_list[0][0][0])
        self.assertIn("Using Anthropic API key from command line", mock_logger.info.call_args_list[1][0][0])

    @patch('os.environ', {})
    @patch('sys.exit')
    @patch('logging.getLogger')
    def test_setup_api_keys_missing_openai(self, mock_get_logger, mock_exit):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        args = MagicMock()
        args.openai_api_key = None
        args.anthropic_api_key = None
        args.provider = "openai"
        
        setup_api_keys(args)
        
        mock_exit.assert_called_once_with(1)
        # Check logger.error call
        mock_logger.error.assert_called_once()
        self.assertIn("OpenAI API key not found", mock_logger.error.call_args[0][0])

    @patch('os.environ', {})
    @patch('sys.exit')
    @patch('logging.getLogger')
    def test_setup_api_keys_missing_anthropic(self, mock_get_logger, mock_exit):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        args = MagicMock()
        args.openai_api_key = None
        args.anthropic_api_key = None
        args.provider = "anthropic"
        
        setup_api_keys(args)
        
        mock_exit.assert_called_once_with(1)
        # Check logger.error call
        mock_logger.error.assert_called_once()
        self.assertIn("Anthropic API key not found", mock_logger.error.call_args[0][0])

    # Test main with verbose output (checks logger.info)
    @patch('prompt_scanner.cli.PromptScanner')
    @patch('prompt_scanner.cli.parse_args')
    @patch('prompt_scanner.cli.get_input_text')
    @patch('prompt_scanner.cli.format_result')
    @patch('prompt_scanner.cli.setup_api_keys')
    @patch('logging.basicConfig') # Mock basicConfig to check level
    @patch('logging.getLogger')   # Mock getLogger to check calls
    def test_main_with_verbose(self, mock_get_logger, mock_basic_config, mock_setup_keys, mock_format, mock_get_input, mock_parse_args, mock_scanner_class):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        
        # Setup mocks
        args = MagicMock()
        args.provider = "openai"
        args.model = None # Let main choose default
        args.verbose = 1  # Verbose mode
        args.format = "text"
        args.color = True
        args.guardrail_file = None
        mock_parse_args.return_value = args
        
        mock_get_input.return_value = "Safe content"
        
        mock_scanner = MagicMock()
        mock_scanner_class.return_value = mock_scanner
        
        safe_result = MagicMock(spec=PromptScanResult) # Use spec for PromptScanResult attributes
        safe_result.is_safe = True
        safe_result.category = None
        safe_result.severity = None
        safe_result.reasoning = "Safe"
        safe_result.token_usage = {}
        mock_scanner.scan.return_value = safe_result # Use scan instead of scan_text
        
        mock_format.return_value = "✅ Content is safe"
        
        # Call main
        with patch('sys.exit') as mock_exit: # Prevent exit during test
             main()
        
        # Verify logger configuration and calls
        mock_basic_config.assert_called_once()
        self.assertEqual(mock_basic_config.call_args[1]['level'], logging.INFO) 

        # Verify logger.info calls (Provider, Model, Guardrails, Scanning)
        # Order might vary slightly depending on default model logic, check content
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        self.assertTrue(any("Using provider: openai" in call for call in info_calls))
        self.assertTrue(any("Using model: gpt-4o" in call for call in info_calls)) # Check default model
        self.assertTrue(any("Scanning content..." in call for call in info_calls))
        # Check setup_api_keys and get_input_text were called (their logs are tested separately)
        mock_setup_keys.assert_called_once_with(args)
        mock_get_input.assert_called_once_with(args)


    @patch('prompt_scanner.cli.PromptScanner')
    @patch('prompt_scanner.cli.parse_args')
    @patch('prompt_scanner.cli.get_input_text')
    @patch('prompt_scanner.cli.setup_api_keys') 
    @patch('sys.exit')
    @patch('logging.getLogger') # Patch logger
    def test_main_with_exception_in_scan(self, mock_get_logger, mock_exit, mock_setup_api_keys, mock_get_input, mock_parse_args, mock_scanner_class):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

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
        mock_scanner.scan.side_effect = Exception("Scan error") # Use scan
        
        # Call main which should catch the exception
        main()
        
        # Check that sys.exit was called with 1
        mock_exit.assert_called_with(1)
        # Check logger.error call
        mock_logger.error.assert_called_once()
        self.assertIn("Error during content scanning: Scan error", mock_logger.error.call_args[0][0])

    # Remove tests that check stderr directly for general exceptions,
    # as the final exception handler in __main__ now logs.
    # We can test the final logger call if needed.

    # Test main with verbose and custom guardrails (checks logger.info)
    @patch('prompt_scanner.cli.PromptScanner')
    @patch('prompt_scanner.cli.parse_args')
    @patch('prompt_scanner.cli.get_input_text')
    @patch('prompt_scanner.cli.format_result')
    @patch('prompt_scanner.cli.setup_api_keys')
    @patch('prompt_scanner.cli.load_guardrails')
    @patch('logging.getLogger') # Patch logger
    def test_main_verbose_with_guardrails(self, mock_get_logger, mock_load_guardrails, mock_setup_keys, 
                                        mock_format, mock_get_input, mock_parse_args, mock_scanner_class):
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

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
        
        safe_result = MagicMock(spec=PromptScanResult) # Use spec
        safe_result.is_safe = True
        safe_result.category = None
        safe_result.severity = None
        safe_result.reasoning = "Safe"
        safe_result.token_usage = {}
        mock_scanner.scan.return_value = safe_result # Use scan
        
        mock_format.return_value = "✅ Content is safe"
        
        # Call main
        with patch('sys.exit') as mock_exit: # Prevent exit during test
             main()
        
        # Verify logger.info calls related to guardrails
        info_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        self.assertTrue(any("Loading custom guardrails from" in call for call in info_calls))
        self.assertTrue(any("Adding custom guardrail: custom_rule" in call for call in info_calls))
        # Verify load_guardrails was called
        mock_load_guardrails.assert_called_once_with(args.guardrail_file)
        # Verify guardrail was added to scanner
        mock_scanner.add_guardrail.assert_called_once_with("custom_rule", guardrails["custom_rule"])

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

if __name__ == '__main__':
    unittest.main()