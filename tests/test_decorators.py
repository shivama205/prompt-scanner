import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import inspect

# Add the parent directory to the path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock external dependencies
sys.modules['openai'] = MagicMock()
sys.modules['anthropic'] = MagicMock()
sys.modules['yaml'] = MagicMock()

# Now import the package
from prompt_scanner.decorators import scan, safe_completion

# Create a mocked ScanResult class for testing
class ScanResult:
    def __init__(self, is_safe, issues=None):
        self.is_safe = is_safe
        self.issues = issues or []


class TestDecorators(unittest.TestCase):
    def setUp(self):
        # Create a mock scanner
        self.mock_scanner = MagicMock()
        
        # Mock scan results
        self.safe_result = ScanResult(is_safe=True, issues=[])
        self.unsafe_result = ScanResult(is_safe=False, issues=[{"type": "test_issue", "description": "Test issue"}])
        
        # Set up mock scan methods
        self.mock_scanner.scan_text.return_value = self.safe_result
        self.mock_scanner.scan.return_value = self.safe_result

    def test_scan_decorator_with_safe_prompt_text(self):
        """Test that scan decorator calls function when text prompt is safe."""
        # Create mock function
        mock_func = MagicMock(return_value="function_result")
        
        # Apply decorator
        decorated_func = scan(scanner=self.mock_scanner)(mock_func)
        
        # Call with safe prompt
        result = decorated_func(prompt="safe prompt text")
        
        # Verify scanner was called
        self.mock_scanner.scan_text.assert_called_once_with("safe prompt text")
        
        # Verify original function was called
        mock_func.assert_called_once_with(prompt="safe prompt text")
        
        # Verify result is from the function
        self.assertEqual(result, "function_result")

    def test_scan_decorator_with_unsafe_prompt_text(self):
        """Test that scan decorator returns scan result when text prompt is unsafe."""
        # Set up mock to return unsafe result
        self.mock_scanner.scan_text.return_value = self.unsafe_result
        
        # Create mock function
        mock_func = MagicMock(return_value="function_result")
        
        # Apply decorator
        decorated_func = scan(scanner=self.mock_scanner)(mock_func)
        
        # Call with unsafe prompt
        result = decorated_func(prompt="unsafe prompt text")
        
        # Verify scanner was called
        self.mock_scanner.scan_text.assert_called_once_with("unsafe prompt text")
        
        # Verify original function was NOT called
        mock_func.assert_not_called()
        
        # Verify result is the scan result
        self.assertEqual(result, self.unsafe_result)

    def test_scan_decorator_with_safe_prompt_object(self):
        """Test that scan decorator calls function when object prompt is safe."""
        # Create prompt object
        prompt_obj = {"messages": [{"role": "user", "content": "Hello"}]}
        
        # Create mock function
        mock_func = MagicMock(return_value="function_result")
        
        # Apply decorator
        decorated_func = scan(scanner=self.mock_scanner)(mock_func)
        
        # Call with safe prompt object
        result = decorated_func(prompt=prompt_obj)
        
        # Verify scanner was called with object
        self.mock_scanner.scan.assert_called_once_with(prompt_obj)
        
        # Verify original function was called
        mock_func.assert_called_once_with(prompt=prompt_obj)
        
        # Verify result is from the function
        self.assertEqual(result, "function_result")

    def test_scan_decorator_with_unsafe_prompt_object(self):
        """Test that scan decorator returns scan result when object prompt is unsafe."""
        # Set up mock to return unsafe result
        self.mock_scanner.scan.return_value = self.unsafe_result
        
        # Create prompt object
        prompt_obj = {"messages": [{"role": "user", "content": "unsafe content"}]}
        
        # Create mock function
        mock_func = MagicMock(return_value="function_result")
        
        # Apply decorator
        decorated_func = scan(scanner=self.mock_scanner)(mock_func)
        
        # Call with unsafe prompt object
        result = decorated_func(prompt=prompt_obj)
        
        # Verify scanner was called
        self.mock_scanner.scan.assert_called_once_with(prompt_obj)
        
        # Verify original function was NOT called
        mock_func.assert_not_called()
        
        # Verify result is the scan result
        self.assertEqual(result, self.unsafe_result)

    def test_scan_decorator_with_positional_args(self):
        """Test that scan decorator extracts prompt from positional args."""
        # Create mock function with signature that includes the prompt parameter
        def test_function(arg1, prompt, arg3):
            return "function_result"
        
        # We need to properly mock the function and its signature inspection
        mock_func = MagicMock(wraps=test_function)
        
        # Apply decorator
        decorated_func = scan(scanner=self.mock_scanner, prompt_param="prompt")(mock_func)
        
        # Call with positional args
        with patch('inspect.signature') as mock_signature:
            # Mock the signature to return parameters with the expected names
            mock_params = {
                'arg1': MagicMock(),
                'prompt': MagicMock(), 
                'arg3': MagicMock()
            }
            mock_signature_result = MagicMock()
            mock_signature_result.parameters = mock_params
            mock_signature.return_value = mock_signature_result
            
            result = decorated_func("arg1_value", "safe prompt text", "arg3_value")
        
        # Verify scanner was called with correct prompt
        self.mock_scanner.scan_text.assert_called_once_with("safe prompt text")
        
        # Verify original function was called with all args
        mock_func.assert_called_once_with("arg1_value", "safe prompt text", "arg3_value")
        
        # Verify result is from the function
        self.assertEqual(result, "function_result")

    def test_scan_decorator_with_no_prompt(self):
        """Test that scan decorator calls function when no prompt is provided."""
        # Create mock function
        mock_func = MagicMock(return_value="function_result")
        
        # Apply decorator
        decorated_func = scan(scanner=self.mock_scanner)(mock_func)
        
        # Call with no prompt
        result = decorated_func(other_param="value")
        
        # Verify scanner was NOT called
        self.mock_scanner.scan_text.assert_not_called()
        self.mock_scanner.scan.assert_not_called()
        
        # Verify original function was called
        mock_func.assert_called_once_with(other_param="value")
        
        # Verify result is from the function
        self.assertEqual(result, "function_result")

    def test_scan_decorator_no_scanner_provided(self):
        """Test that scan decorator raises error when no scanner is provided."""
        # Create mock function
        mock_func = MagicMock(return_value="function_result")
        
        # Apply decorator with no scanner
        decorated_func = scan()(mock_func)
        
        # Call the function and expect an error
        with self.assertRaises(ValueError):
            decorated_func(prompt="test prompt")
    
    # Tests for safe_completion decorator
    
    def test_safe_completion_decorator_with_safe_input_and_output(self):
        """Test that safe_completion decorator calls function when input and output are safe."""
        # Create mock function that returns safe content
        mock_func = MagicMock(return_value="safe output text")
        
        # Apply decorator
        decorated_func = safe_completion(scanner=self.mock_scanner)(mock_func)
        
        # Call with safe prompt
        result = decorated_func(prompt="safe prompt text")
        
        # Verify input scanner was called
        self.mock_scanner.scan_text.assert_any_call("safe prompt text")
        
        # Verify output scanner was called
        self.mock_scanner.scan_text.assert_any_call("safe output text")
        
        # Verify original function was called
        mock_func.assert_called_once_with(prompt="safe prompt text")
        
        # Verify result is from the function
        self.assertEqual(result, "safe output text")

    def test_safe_completion_decorator_with_unsafe_input(self):
        """Test that safe_completion decorator returns scan result when input is unsafe."""
        # Set up scan_text to return unsafe result for the first call (input check)
        self.mock_scanner.scan_text.side_effect = [self.unsafe_result, self.safe_result]
        
        # Create mock function
        mock_func = MagicMock(return_value="function_result")
        
        # Apply decorator
        decorated_func = safe_completion(scanner=self.mock_scanner)(mock_func)
        
        # Call with unsafe prompt
        result = decorated_func(prompt="unsafe prompt text")
        
        # Verify input scanner was called
        self.mock_scanner.scan_text.assert_called_once_with("unsafe prompt text")
        
        # Verify original function was NOT called
        mock_func.assert_not_called()
        
        # Verify result is the scan result
        self.assertEqual(result, self.unsafe_result)

    def test_safe_completion_decorator_with_unsafe_output(self):
        """Test that safe_completion decorator returns scan result when output is unsafe."""
        # Set up scan_text to return safe result for input but unsafe for output
        self.mock_scanner.scan_text.side_effect = [self.safe_result, self.unsafe_result]
        
        # Create mock function that returns unsafe content
        mock_func = MagicMock(return_value="unsafe output text")
        
        # Apply decorator
        decorated_func = safe_completion(scanner=self.mock_scanner)(mock_func)
        
        # Call with safe prompt
        result = decorated_func(prompt="safe prompt text")
        
        # Verify input scanner was called
        self.mock_scanner.scan_text.assert_any_call("safe prompt text")
        
        # Verify output scanner was called
        self.mock_scanner.scan_text.assert_any_call("unsafe output text")
        
        # Verify original function was called
        mock_func.assert_called_once_with(prompt="safe prompt text")
        
        # Verify result is the scan result from output check
        self.assertEqual(result, self.unsafe_result)
    
    def test_safe_completion_decorator_with_object_prompt_and_response(self):
        """Test safe_completion with object prompts and responses."""
        # Create prompt and response objects
        prompt_obj = {"messages": [{"role": "user", "content": "Hello"}]}
        response_obj = {"content": "Test response"}
        
        # Reset side effects
        self.mock_scanner.scan.side_effect = None
        self.mock_scanner.scan.return_value = self.safe_result
        
        # Create mock function that returns object
        mock_func = MagicMock(return_value=response_obj)
        
        # Apply decorator
        decorated_func = safe_completion(scanner=self.mock_scanner)(mock_func)
        
        # Call with object prompt
        result = decorated_func(prompt=prompt_obj)
        
        # Verify input scanner was called with object
        self.mock_scanner.scan.assert_any_call(prompt_obj)
        
        # Verify output scanner was called with object
        self.mock_scanner.scan.assert_any_call(response_obj)
        
        # Verify original function was called
        mock_func.assert_called_once_with(prompt=prompt_obj)
        
        # Verify result is from the function
        self.assertEqual(result, response_obj)
    
    def test_safe_completion_no_prompt_parameter(self):
        """Test safe_completion when no prompt parameter is provided."""
        # Create mock function with no prompt parameter
        mock_func = MagicMock(return_value="safe output")
        
        # Apply decorator
        decorated_func = safe_completion(scanner=self.mock_scanner)(mock_func)
        
        # Call with no prompt
        result = decorated_func(other_param="value")
        
        # Verify input scanner was NOT called
        self.assertNotIn('safe prompt text', [call[0][0] for call in self.mock_scanner.scan_text.call_args_list if call[0]])
        
        # Verify output scanner was called
        self.mock_scanner.scan_text.assert_called_with("safe output")
        
        # Verify original function was called
        mock_func.assert_called_once_with(other_param="value")
        
        # Verify result is from the function
        self.assertEqual(result, "safe output")
    
    def test_safe_completion_with_none_response(self):
        """Test safe_completion when function returns None."""
        # Create mock function that returns None
        mock_func = MagicMock(return_value=None)
        
        # Apply decorator
        decorated_func = safe_completion(scanner=self.mock_scanner)(mock_func)
        
        # Call with safe prompt
        result = decorated_func(prompt="safe prompt text")
        
        # Verify input scanner was called
        self.mock_scanner.scan_text.assert_called_once_with("safe prompt text")
        
        # Verify original function was called
        mock_func.assert_called_once_with(prompt="safe prompt text")
        
        # Verify result is None
        self.assertIsNone(result)

    def test_safe_completion_unsafe_object_output(self):
        """Test safe_completion when function returns an unsafe object response."""
        # Create response object
        response_obj = {"content": "unsafe content"}
        
        # Reset side effects and set unsafe result for second call (output check)
        self.mock_scanner.scan.side_effect = [self.safe_result, self.unsafe_result]
        
        # Create mock function that returns object
        mock_func = MagicMock(return_value=response_obj)
        
        # Apply decorator
        decorated_func = safe_completion(scanner=self.mock_scanner)(mock_func)
        
        # Call with prompt object
        prompt_obj = {"messages": [{"role": "user", "content": "Hello"}]}
        result = decorated_func(prompt=prompt_obj)
        
        # Verify input scanner was called
        self.mock_scanner.scan.assert_any_call(prompt_obj)
        
        # Verify output scanner was called
        self.mock_scanner.scan.assert_any_call(response_obj)
        
        # Verify original function was called
        mock_func.assert_called_once_with(prompt=prompt_obj)
        
        # Verify result is the scan result from output check
        self.assertEqual(result, self.unsafe_result)
    
    def test_safe_completion_with_no_scanner(self):
        """Test safe_completion decorator raises error when no scanner is provided."""
        # Create mock function
        mock_func = MagicMock(return_value="function_result")
        
        # Apply decorator with no scanner
        decorated_func = safe_completion()(mock_func)
        
        # Call the function and expect an error
        with self.assertRaises(ValueError):
            decorated_func(prompt="test prompt")

    def test_safe_completion_without_input_but_with_object_output(self):
        """Test safe_completion when no input is provided but response is an object."""
        # Create response object (non-string)
        response_obj = {"content": "Hello world"}
        
        # Create mock function that returns an object without taking a prompt
        def func_without_prompt(other_param):
            return response_obj
        
        mock_func = MagicMock(wraps=func_without_prompt)
        
        # Apply decorator
        decorated_func = safe_completion(scanner=self.mock_scanner)(mock_func)
        
        # Call without prompt parameter
        with patch('inspect.signature') as mock_signature:
            # Mock the signature to not include prompt
            mock_params = {
                'other_param': MagicMock()
            }
            mock_signature_result = MagicMock()
            mock_signature_result.parameters = mock_params
            mock_signature.return_value = mock_signature_result
            
            result = decorated_func(other_param="test")
        
        # Verify input scanner was NOT called for prompt
        self.assertEqual(self.mock_scanner.scan_text.call_count, 0)  
        
        # Verify output scanner was called with the object
        self.mock_scanner.scan.assert_called_once_with(response_obj)
        
        # Verify original function was called
        mock_func.assert_called_once_with(other_param="test")
        
        # Verify result is from the function
        self.assertEqual(result, response_obj)

    def test_safe_completion_with_positional_args(self):
        """Test that safe_completion decorator correctly extracts prompt from positional args."""
        # Create mock function with a signature that includes prompt as second parameter
        def mock_function(arg1, prompt, arg3):
            return "mock function response"
        
        # We need to use the actual inspect.signature to exercise the real code path
        real_signature = inspect.signature(mock_function)
        
        # Apply decorator
        decorated_func = safe_completion(scanner=self.mock_scanner)(mock_function)
        
        # We'll skip patching inspect.signature to test the actual code path
        # This will exercise the args extraction logic in lines 92-98
        result = decorated_func("arg1_value", "test prompt", "arg3_value")
        
        # Verify scanner was called with the prompt from positional args
        self.mock_scanner.scan_text.assert_any_call("test prompt")
        
        # Verify result is the expected response from the function
        self.assertEqual(result, "mock function response")


if __name__ == "__main__":
    unittest.main() 