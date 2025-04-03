#!/usr/bin/env python3
import argparse
import json
import sys
import os
import logging
from typing import Optional, Dict, Any

from prompt_scanner import PromptScanner, PromptScanResult, __version__


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="""
Prompt Scanner CLI - Scan prompts for potentially unsafe content.

This tool analyzes text against content safety policies to detect potentially unsafe or harmful content
using Large Language Models (LLMs) as content judges.

API KEY SETUP:
  - OpenAI:   Set OPENAI_API_KEY environment variable
  - Anthropic: Set ANTHROPIC_API_KEY environment variable

  You can set them directly in your terminal:
    export OPENAI_API_KEY="your-key-here"
    export ANTHROPIC_API_KEY="your-key-here"
    
  Or create a .env file in the current directory with these values.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"prompt-scanner {__version__}"
    )
    
    # API key options
    api_group = parser.add_argument_group('API Configuration')
    api_group.add_argument(
        "--openai-api-key",
        help="OpenAI API key (overrides environment variable)"
    )
    api_group.add_argument(
        "--anthropic-api-key",
        help="Anthropic API key (overrides environment variable)"
    )
    
    # Provider options
    provider_group = parser.add_argument_group('Provider Configuration')
    provider_group.add_argument(
        "-p", "--provider",
        choices=["openai", "anthropic"],
        default="openai",
        help="LLM provider to use for scanning (default: openai)"
    )
    provider_group.add_argument(
        "-m", "--model",
        help="Specific model to use (e.g., gpt-4o for OpenAI, claude-3-opus-20240229 for Anthropic)"
    )
    
    # Output options
    output_group = parser.add_argument_group('Output Configuration')
    output_group.add_argument(
        "-v", "--verbose",
        action="count",
        default=0,
        help="Enable verbose output. Use -v for basic info, -vv for detailed output with reasoning"
    )
    output_group.add_argument(
        "-f", "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    output_group.add_argument(
        "--color",
        action="store_true",
        default=True,
        help="Use color in output (default: True)"
    )
    output_group.add_argument(
        "--no-color",
        action="store_false",
        dest="color",
        help="Disable color in output"
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--text",
        help="Text content to scan"
    )
    input_group.add_argument(
        "--file",
        help="File containing text to scan"
    )
    input_group.add_argument(
        "--stdin",
        action="store_true",
        help="Read content from standard input"
    )
    
    # Custom guardrails
    guardrail_group = parser.add_argument_group('Custom Guardrails')
    guardrail_group.add_argument(
        "--guardrail-file",
        help="Path to a JSON file containing custom guardrails"
    )
    
    return parser.parse_args()


def load_guardrails(guardrail_file: str) -> Dict[str, Any]:
    """Load custom guardrails from a JSON file."""
    try:
        with open(guardrail_file, 'r') as f:
            guardrails = json.load(f)
            if not isinstance(guardrails, dict):
                logging.getLogger(__name__).error(f"Guardrails file should contain a JSON object")
                sys.exit(1)
            return guardrails
    except json.JSONDecodeError as e:
        logging.getLogger(__name__).error(f"Invalid JSON in guardrails file: {e}")
        sys.exit(1)
    except Exception as e:
        logging.getLogger(__name__).error(f"Error loading guardrails file: {e}")
        sys.exit(1)


def get_input_text(args: argparse.Namespace) -> str:
    """Get the input text from the specified source."""
    logger = logging.getLogger(__name__)
    
    if args.text:
        logger.info(f"Input: Direct text input ({len(args.text)} characters)")
        return args.text
    elif args.file:
        try:
            logger.info(f"Input: Reading from file '{args.file}'")
            with open(args.file, 'r') as f:
                content = f.read()
                logger.info(f"Read {len(content)} characters from file")
                return content
        except Exception as e:
            logger.error(f"Error reading input file: {e}")
            sys.exit(1)
    elif args.stdin:
        logger.info(f"Input: Reading from standard input")
        content = sys.stdin.read()
        logger.info(f"Read {len(content)} characters from stdin")
        return content
    
    return ""  # This should never happen due to the mutually exclusive group


def format_result(result: PromptScanResult, format_type: str, verbose: int, use_color: bool) -> str:
    """Format the scan result based on the specified format type."""
    # For JSON format
    if format_type == "json":
        result_dict = {
            "is_safe": result.is_safe,
            "category": result.category.name if result.category else None,
            "severity": result.severity.level.value if result.severity else None,
            "reasoning": result.reasoning  # Always include reasoning
        }
        
        if verbose >= 2:
            result_dict["token_usage"] = result.token_usage
            if result.severity:
                result_dict["severity_details"] = {
                    "level": result.severity.level.value,
                    "score": result.severity.score,
                    "description": result.severity.description
                }
        
        return json.dumps(result_dict, indent=2)
    else:  # text format
        output = []
        
        # Use colors if enabled
        if use_color:
            GREEN = "\033[92m"
            RED = "\033[91m"
            YELLOW = "\033[93m"
            BOLD = "\033[1m"
            RESET = "\033[0m"
        else:
            GREEN = RED = YELLOW = BOLD = RESET = ""
        
        if result.is_safe:
            output.append(f"{GREEN}✅ Content is safe{RESET}")
        else:
            output.append(f"{RED}❌ Content violates: {BOLD}{result.category.name}{RESET}")
            
            # Add severity information
            if result.severity:
                severity_level = result.severity.level.value
                # Choose color based on severity level
                severity_color = GREEN
                if severity_level == "MEDIUM":
                    severity_color = YELLOW
                elif severity_level in ("HIGH", "CRITICAL"):
                    severity_color = RED
                
                output.append(f"Severity: {severity_color}{severity_level}{RESET}")
                
                # Add severity description for verbose output
                if verbose >= 1 and result.severity.description:
                    output.append(f"Description: {result.severity.description}")
        
        # Always include reasoning
        output.append(f"\n{BOLD}Reasoning:{RESET}")
        output.append(result.reasoning)
        
        if verbose >= 2:
            output.append(f"\n{BOLD}Token usage:{RESET}")
            output.append(json.dumps(result.token_usage, indent=2))
        
        return "\n".join(output)


def setup_api_keys(args: argparse.Namespace) -> None:
    """Set up API keys from args or check if they're in environment."""
    logger = logging.getLogger(__name__)

    # Set API keys from command line if provided
    if args.openai_api_key:
        os.environ["OPENAI_API_KEY"] = args.openai_api_key
        logger.info("Using OpenAI API key from command line")
    
    if args.anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = args.anthropic_api_key
        logger.info("Using Anthropic API key from command line")
    
    # Check if required API key is in environment
    provider = args.provider.lower()
    if provider == "openai" and "OPENAI_API_KEY" not in os.environ:
        logger.error("OpenAI API key not found. Set OPENAI_API_KEY environment variable or use --openai-api-key")
        sys.exit(1)
    elif provider == "anthropic" and "ANTHROPIC_API_KEY" not in os.environ:
        logger.error("Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable or use --anthropic-api-key")
        sys.exit(1)


def main():
    # Load environment variables from .env file if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        # dotenv is optional, proceed without it if not installed
        pass 
        
    args = parse_args()

    # Configure logging
    log_level = logging.ERROR
    if args.verbose >= 1:
        log_level = logging.INFO
    # Simple format: LEVEL: message
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s', stream=sys.stderr)
    logger = logging.getLogger(__name__) # Get logger instance

    # Pass args directly instead of verbose level
    setup_api_keys(args) 
    content = get_input_text(args) 

    # Determine model based on provider if not specified
    model = args.model
    if not model:
        if args.provider == "openai":
            model = "gpt-4o" # Default OpenAI model
        elif args.provider == "anthropic":
            model = "claude-3-opus-20240229" # Default Anthropic model
    # Replace conditional print with logger.info
    logger.info(f"Using model: {model}")
    # Replace conditional print with logger.info
    logger.info(f"Using provider: {args.provider}")

    custom_guardrails = {}
    if args.guardrail_file:
        # Replace conditional print with logger.info
        logger.info(f"Loading custom guardrails from {args.guardrail_file}")
        custom_guardrails = load_guardrails(args.guardrail_file)
        for name in custom_guardrails.keys():
             # Replace conditional print with logger.info
            logger.info(f"Adding custom guardrail: {name}")

    try:
        scanner = PromptScanner(provider=args.provider, model=model)
        for name, definition in custom_guardrails.items():
            scanner.add_guardrail(name, definition)
        
        # Replace conditional print with logger.info
        logger.info("Scanning content...")
        result = scanner.scan(content)
        
    except Exception as e:
        # Replace print with logger.error
        logger.error(f"Error during content scanning: {e}")
        sys.exit(1)

    output = format_result(result, args.format, args.verbose, args.color)
    print(output) # Keep this print for stdout result


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # General error catcher, replace print with logger.critical or logger.error
        logging.getLogger(__name__).critical(f"An unexpected error occurred: {e}") # Use logger here too
        sys.exit(1) 