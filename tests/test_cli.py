import pytest
import json
import sys
import io
from unittest.mock import patch, MagicMock

from prompt_scanner import PromptScanResult, PromptCategory, CategorySeverity
from prompt_scanner.cli import main, parse_args, get_input_text, format_result


class TestCLI:
    def test_parse_args(self):
        with patch('sys.argv', ['prompt-scanner', '--text', 'test content']):
            args = parse_args()
            assert args.text == 'test content'
            assert args.provider == 'openai'
            assert args.format == 'text'
            assert not args.verbose
    
    def test_get_input_text_from_text_arg(self):
        args = MagicMock()
        args.text = "test content"
        args.file = None
        args.stdin = False
        
        result = get_input_text(args)
        assert result == "test content"
    
    @patch('builtins.open', new_callable=MagicMock)
    def test_get_input_text_from_file(self, mock_open):
        mock_file = MagicMock()
        mock_file.read.return_value = "test content from file"
        mock_open.return_value.__enter__.return_value = mock_file
        
        args = MagicMock()
        args.text = None
        args.file = "test.txt"
        args.stdin = False
        
        result = get_input_text(args)
        assert result == "test content from file"
        mock_open.assert_called_once_with("test.txt", 'r')
    
    @patch('sys.stdin')
    def test_get_input_text_from_stdin(self, mock_stdin):
        mock_stdin.read.return_value = "test content from stdin"
        
        args = MagicMock()
        args.text = None
        args.file = None
        args.stdin = True
        
        result = get_input_text(args)
        assert result == "test content from stdin"
    
    def test_format_result_text_safe(self):
        category = None
        result = PromptScanResult(
            is_safe=True,
            category=category,
            reasoning="This is safe content",
            token_usage={"total_tokens": 100}
        )
        
        formatted = format_result(result, "text", False)
        assert "✅ Content is safe" in formatted
        assert "reasoning" not in formatted.lower()
        
        formatted_verbose = format_result(result, "text", True)
        assert "✅ Content is safe" in formatted_verbose
        assert "This is safe content" in formatted_verbose
        assert "token usage" in formatted_verbose.lower()
    
    def test_format_result_text_unsafe(self):
        category = PromptCategory(
            name="harmful_content",
            severity=CategorySeverity.HIGH
        )
        result = PromptScanResult(
            is_safe=False,
            category=category,
            reasoning="This is unsafe content",
            token_usage={"total_tokens": 100}
        )
        
        formatted = format_result(result, "text", False)
        assert "❌ Content violates" in formatted
        assert "harmful_content" in formatted
        assert "HIGH" in formatted
        assert "reasoning" not in formatted.lower()
        
        formatted_verbose = format_result(result, "text", True)
        assert "❌ Content violates" in formatted_verbose
        assert "This is unsafe content" in formatted_verbose
        assert "token usage" in formatted_verbose.lower()
    
    def test_format_result_json_safe(self):
        category = None
        result = PromptScanResult(
            is_safe=True,
            category=category,
            reasoning="This is safe content",
            token_usage={"total_tokens": 100}
        )
        
        formatted = format_result(result, "json", False)
        result_dict = json.loads(formatted)
        assert result_dict["is_safe"] is True
        assert result_dict["category"] is None
        assert result_dict["severity"] is None
        assert "reasoning" not in result_dict
        assert "token_usage" not in result_dict
        
        formatted_verbose = format_result(result, "json", True)
        result_dict = json.loads(formatted_verbose)
        assert result_dict["is_safe"] is True
        assert result_dict["reasoning"] == "This is safe content"
        assert "token_usage" in result_dict
    
    def test_format_result_json_unsafe(self):
        category = PromptCategory(
            name="harmful_content",
            severity=CategorySeverity.HIGH
        )
        result = PromptScanResult(
            is_safe=False,
            category=category,
            reasoning="This is unsafe content",
            token_usage={"total_tokens": 100}
        )
        
        formatted = format_result(result, "json", False)
        result_dict = json.loads(formatted)
        assert result_dict["is_safe"] is False
        assert result_dict["category"] == "harmful_content"
        assert result_dict["severity"] == "HIGH"
        assert "reasoning" not in result_dict
        
        formatted_verbose = format_result(result, "json", True)
        result_dict = json.loads(formatted_verbose)
        assert result_dict["is_safe"] is False
        assert result_dict["category"] == "harmful_content"
        assert result_dict["reasoning"] == "This is unsafe content"
    
    @patch('prompt_scanner.cli.PromptScanner')
    @patch('prompt_scanner.cli.parse_args')
    @patch('prompt_scanner.cli.get_input_text')
    @patch('prompt_scanner.cli.format_result')
    def test_main_safe_content(self, mock_format, mock_get_input, mock_parse_args, mock_scanner_class):
        # Setup mocks
        args = MagicMock()
        args.provider = "openai"
        args.model = "gpt-4o"
        args.verbose = False
        args.format = "text"
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
    def test_main_unsafe_content(self, mock_format, mock_get_input, mock_parse_args, mock_scanner_class):
        # Setup mocks
        args = MagicMock()
        args.provider = "openai"
        args.model = "gpt-4o"
        args.verbose = False
        args.format = "text"
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
    def test_main_with_custom_guardrails(self, mock_format, mock_get_input, mock_parse_args, 
                                         mock_scanner_class, mock_load_guardrails):
        # Setup mocks
        args = MagicMock()
        args.provider = "openai"
        args.model = "gpt-4o"
        args.verbose = False
        args.format = "text"
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