import functools
import logging
from typing import Callable, Any, Dict, Optional, Union, List, Tuple
from .scanner import PromptScanner
from .models import PromptScanResult

logger = logging.getLogger(__name__)

def scan_prompt(
    provider: str = "openai",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    log_results: bool = True,
    raise_on_unsafe: bool = False,
    confidence_threshold: float = 0.7,
    allowed_categories: Optional[List[str]] = None
):
    """
    Decorator that scans prompts before passing them to the decorated function.
    
    Args:
        provider: LLM provider ("openai" or "anthropic")
        api_key: API key for the provider (defaults to environment variable)
        model: Model to use for scanning
        log_results: Whether to log scan results
        raise_on_unsafe: Whether to raise an exception for unsafe content
        confidence_threshold: Confidence threshold for safety warnings
        allowed_categories: List of category IDs that are allowed even if flagged
        
    Returns:
        Decorator function
        
    Example:
        @scan_prompt(provider="openai", raise_on_unsafe=True)
        def generate_response(prompt):
            # Function implementation...
            return response
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Initialize scanner
            scanner = PromptScanner(provider=provider, api_key=api_key, model=model)
            
            # Extract prompt from args or kwargs
            prompt = None
            if args and isinstance(args[0], (dict, str)):
                prompt = args[0]
            elif 'prompt' in kwargs:
                prompt = kwargs['prompt']
            elif 'messages' in kwargs:
                prompt = {'messages': kwargs['messages']}
            
            if not prompt:
                logger.warning("No prompt found in function arguments")
                return func(*args, **kwargs)
            
            # Scan prompt
            try:
                if isinstance(prompt, str):
                    scan_result = scanner.scan_text(prompt)
                else:
                    scan_result = scanner.scan(prompt)
                
                # Add scan result to function metadata
                if 'metadata' not in kwargs:
                    kwargs['metadata'] = {}
                kwargs['metadata']['scan_result'] = scan_result
                
                # Log the result if enabled
                if log_results:
                    if scan_result.is_safe:
                        logger.info("Prompt scan passed: Content is safe")
                    else:
                        logger.warning(
                            f"Prompt scan flagged content: {scan_result.category.name} "
                            f"(confidence: {scan_result.category.confidence:.2f})"
                        )
                
                # Check if we should block the request
                if not scan_result.is_safe:
                    if allowed_categories and scan_result.category and scan_result.category.id in allowed_categories:
                        logger.info(f"Content flagged as {scan_result.category.name} but is in allowed categories")
                    elif scan_result.category and scan_result.category.confidence >= confidence_threshold:
                        if raise_on_unsafe:
                            raise ValueError(
                                f"Unsafe content detected: {scan_result.category.name} "
                                f"(confidence: {scan_result.category.confidence:.2f}). "
                                f"Reasoning: {scan_result.reasoning}"
                            )
            except Exception as e:
                logger.error(f"Error scanning prompt: {str(e)}")
                # Continue with the function if scan fails
            
            # Call the original function
            return func(*args, **kwargs)
        return wrapper
    return decorator

def safe_completion(
    provider: str = "openai",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    fallback_response: Optional[str] = None
):
    """
    Decorator that ensures completions are safe by scanning both input and output.
    If unsafe content is detected, the function will return a fallback response.
    
    Args:
        provider: LLM provider ("openai" or "anthropic")
        api_key: API key for the provider (defaults to environment variable)
        model: Model to use for scanning
        fallback_response: Response to return if unsafe content is detected
        
    Returns:
        Decorator function
        
    Example:
        @safe_completion(provider="openai", fallback_response="I cannot provide unsafe content.")
        def generate_text(prompt: str) -> str:
            # Function implementation...
            return completion_text
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Initialize scanner
            scanner = PromptScanner(provider=provider, api_key=api_key, model=model)
            
            # Extract prompt from args or kwargs
            prompt = None
            if args and isinstance(args[0], (dict, str)):
                prompt = args[0]
            elif 'prompt' in kwargs:
                prompt = kwargs['prompt']
            
            # Check input prompt if available
            if prompt and isinstance(prompt, str):
                input_result = scanner.scan_text(prompt)
                if not input_result.is_safe:
                    logger.warning(
                        f"Input prompt flagged as unsafe: {input_result.category.name} "
                        f"(confidence: {input_result.category.confidence:.2f})"
                    )
                    if fallback_response:
                        return fallback_response
            
            # Call the original function
            response = func(*args, **kwargs)
            
            # Check output if it's a string
            if isinstance(response, str):
                output_result = scanner.scan_text(response)
                if not output_result.is_safe:
                    logger.warning(
                        f"Output flagged as unsafe: {output_result.category.name} "
                        f"(confidence: {output_result.category.confidence:.2f})"
                    )
                    if fallback_response:
                        return fallback_response
            
            return response
        return wrapper
    return decorator 