import functools
from typing import Callable

def scan(
    scanner=None,
    prompt_param: str = "prompt"
):
    """
    Decorator that scans prompts before passing them to the decorated function.
    If content is unsafe, returns the scan result instead of calling the function.
    
    Args:
        scanner: The PromptScanner instance to use
        prompt_param: The parameter name that contains the prompt text/object
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Use the scanner provided to the decorator or from class
            nonlocal scanner
            if scanner is None:
                raise ValueError("No scanner instance provided to the decorator")
            
            # Extract prompt from args or kwargs based on prompt_param
            prompt = None
            
            # Check kwargs first
            if prompt_param in kwargs:
                prompt = kwargs[prompt_param]
            # Then check args based on function signature
            elif args:
                import inspect
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                if prompt_param in param_names:
                    idx = param_names.index(prompt_param)
                    if idx < len(args):
                        prompt = args[idx]
            
            if not prompt:
                return func(*args, **kwargs)
            
            # Scan prompt - use scan_text for strings, scan for dictionaries/objects
            if isinstance(prompt, str):
                scan_result = scanner.scan_text(prompt)
            else:
                scan_result = scanner.scan(prompt)
            
            # Return the scan result if unsafe, otherwise call the function
            if not scan_result.is_safe:
                return scan_result
            
            # Call the original function
            return func(*args, **kwargs)
        return wrapper
    return decorator

def safe_completion(
    scanner=None, 
    prompt_param: str = "prompt"
):
    """
    Decorator that ensures completions are safe by scanning both input and output.
    If input is unsafe, returns the scan result. If output is unsafe, returns the scan result.
    
    Args:
        scanner: The PromptScanner instance to use
        prompt_param: The parameter name that contains the prompt text
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Use the scanner provided to the decorator or from class
            nonlocal scanner
            if scanner is None:
                raise ValueError("No scanner instance provided to the decorator") 
            
            # Extract prompt from args or kwargs based on prompt_param
            prompt = None
            
            # Check kwargs first
            if prompt_param in kwargs:
                prompt = kwargs[prompt_param]
            # Then check args based on function signature
            elif args:
                import inspect
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                if prompt_param in param_names:
                    idx = param_names.index(prompt_param)
                    if idx < len(args):
                        prompt = args[idx]
            
            # Check input prompt if available
            if prompt:
                # Use scan_text for strings, scan for dictionaries/objects
                if isinstance(prompt, str):
                    input_result = scanner.scan_text(prompt)
                else:
                    input_result = scanner.scan(prompt)
                    
                if not input_result.is_safe:
                    return input_result
            
            # Call the original function
            response = func(*args, **kwargs)
            
            # Check output content safety
            if response:
                # Use scan_text for strings, scan for dictionaries/objects
                if isinstance(response, str):
                    output_result = scanner.scan_text(response)
                else:
                    output_result = scanner.scan(response)
                    
                if not output_result.is_safe:
                    return output_result
            
            return response
        return wrapper
    return decorator 