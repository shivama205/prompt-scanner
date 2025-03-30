#!/usr/bin/env python3
import argparse
import json
import sys
import os
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
                print(f"Error: Guardrails file should contain a JSON object", file=sys.stderr)
                sys.exit(1)
            return guardrails
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in guardrails file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error loading guardrails file: {e}", file=sys.stderr)
        sys.exit(1)


def get_input_text(args: argparse.Namespace, verbose: int) -> str:
    """Get the input text from the specified source."""
    if args.text:
        if verbose >= 1:
            print(f"Input: Direct text input ({len(args.text)} characters)", file=sys.stderr)
        return args.text
    elif args.file:
        try:
            if verbose >= 1:
                print(f"Input: Reading from file '{args.file}'", file=sys.stderr)
            with open(args.file, 'r') as f:
                content = f.read()
                if verbose >= 1:
                    print(f"Read {len(content)} characters from file", file=sys.stderr)
                return content
        except Exception as e:
            print(f"Error reading input file: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.stdin:
        if verbose >= 1:
            print(f"Input: Reading from standard input", file=sys.stderr)
        content = sys.stdin.read()
        if verbose >= 1:
            print(f"Read {len(content)} characters from stdin", file=sys.stderr)
        return content
    
    return ""  # This should never happen due to the mutually exclusive group


def format_result(result: PromptScanResult, format_type: str, verbose: int, use_color: bool) -> str:
    """Format the scan result based on the specified format type."""
    # For unsafe content, set a default severity if not present
    severity_name = None
    if not result.is_safe and result.category:
        if hasattr(result.category, 'severity') and result.category.severity:
            severity_name = result.category.severity.name
        else:
            # Default to HIGH severity for unsafe content if not specified
            severity_name = "HIGH"
    
    if format_type == "json":
        result_dict = {
            "is_safe": result.is_safe,
            "category": result.category.name if result.category else None,
            "severity": severity_name,
            "reasoning": result.reasoning  # Always include reasoning
        }
        
        if verbose >= 2:
            result_dict["token_usage"] = result.token_usage
        
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
            # Add severity with default if not present
            severity_color = RED if severity_name == "HIGH" else YELLOW
            output.append(f"Severity: {severity_color}{severity_name}{RESET}")
        
        # Always include reasoning
        output.append(f"\n{BOLD}Reasoning:{RESET}")
        output.append(result.reasoning)
        
        if verbose >= 2:
            output.append(f"\n{BOLD}Token usage:{RESET}")
            output.append(json.dumps(result.token_usage, indent=2))
        
        return "\n".join(output)


def setup_api_keys(args: argparse.Namespace, verbose: int) -> None:
    """Set up API keys from args or check if they're in environment."""
    # Set API keys from command line if provided
    if args.openai_api_key:
        os.environ["OPENAI_API_KEY"] = args.openai_api_key
        if verbose >= 1:
            print("Using OpenAI API key from command line", file=sys.stderr)
    
    if args.anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = args.anthropic_api_key
        if verbose >= 1:
            print("Using Anthropic API key from command line", file=sys.stderr)
    
    # Check if required API key is in environment
    provider = args.provider.lower()
    if provider == "openai" and "OPENAI_API_KEY" not in os.environ:
        print("Error: OpenAI API key not found. Set OPENAI_API_KEY environment variable or use --openai-api-key", 
              file=sys.stderr)
        sys.exit(1)
    elif provider == "anthropic" and "ANTHROPIC_API_KEY" not in os.environ:
        print("Error: Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable or use --anthropic-api-key", 
              file=sys.stderr)
        sys.exit(1)


def main():
    args = parse_args()
    verbose = args.verbose
    
    # Set up API keys
    setup_api_keys(args, verbose)
    
    # Initialize scanner with specified provider and model
    scanner_kwargs = {"provider": args.provider.lower()}
    
    if args.model:
        scanner_kwargs["model"] = args.model
        if verbose >= 1:
            print(f"Using model: {args.model}", file=sys.stderr)
    
    if verbose >= 1:
        print(f"Using provider: {args.provider}", file=sys.stderr)
    
    try:
        scanner = PromptScanner(**scanner_kwargs)
        
        # Load custom guardrails if specified
        if args.guardrail_file:
            if verbose >= 1:
                print(f"Loading custom guardrails from {args.guardrail_file}", file=sys.stderr)
            guardrails = load_guardrails(args.guardrail_file)
            for name, guardrail in guardrails.items():
                if verbose >= 1:
                    print(f"Adding custom guardrail: {name}", file=sys.stderr)
                scanner.add_custom_guardrail(name, guardrail)
        
        # Get input text
        input_text = get_input_text(args, verbose)
        
        if verbose >= 1:
            print("Scanning content...", file=sys.stderr)
        
        # Scan the input
        try:
            result = scanner.scan_text(input_text)
        except Exception as e:
            print(f"Error during content scanning: {e}", file=sys.stderr)
            sys.exit(1)
        
        # Format and display the result
        output = format_result(result, args.format, verbose, args.color)
        print(output)
        
        # Exit with status code 1 if unsafe content was detected
        if not result.is_safe:
            sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if verbose >= 2:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 