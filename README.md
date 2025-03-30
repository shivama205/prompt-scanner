# Prompt Scanner

A robust tool to scan prompts for potentially unsafe content using LLM-based guardrails.

[![PyPI version](https://badge.fury.io/py/prompt-scanner.svg)](https://badge.fury.io/py/prompt-scanner)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Test Coverage: 100%](https://img.shields.io/badge/Test%20Coverage-100%25-brightgreen.svg)](https://github.com/shivama205/prompt-scanner)

**Current Version: 0.3.1** - Now with enhanced severity levels for better risk assessment!

## Overview

Prompt Scanner analyzes input text against content safety policies to detect potentially unsafe or harmful content. It uses Large Language Models (LLMs) as content judges to provide more context-aware and nuanced content safety evaluations than simple pattern matching.

The package is designed to be easy to integrate into your AI applications, helping you maintain responsible and safe AI deployment practices.

## Features

- **Multiple Provider Support**: Uses OpenAI or Anthropic APIs for content safety evaluation
- **Comprehensive Safety Categories**: Identifies content across various safety categories
- **Multi-category Detection**: Supports detecting multiple policy violations in a single piece of content
- **Standardized Severity Levels**: Categorizes risk with LOW, MEDIUM, HIGH, and CRITICAL severity levels
- **Prompt Injection Protection**: Checks for prompt injection attacks and other security risks
- **Detailed Analysis**: Returns structured responses with detailed reasoning
- **Performance Metrics**: Includes token usage metrics
- **Customizable**: Supports customizing the LLM model used for evaluation
- **Custom Guardrails**: Add your own custom guardrails and content policy categories
- **Rich Command Line Interface**: Scan prompts directly from the terminal with detailed output

## What's New in 0.3.1

- **Enhanced Severity Levels**: Added standardized severity assessment with LOW, MEDIUM, HIGH, and CRITICAL levels
- **Severity Feedback**: Included detailed severity information in scan results, CLI output, and JSON responses
- **Improved LLM Prompts**: Updated LLM evaluation prompts to include severity assessment
- **Category-Based Severity**: Automatically assigns CRITICAL severity to particularly dangerous categories
- **See the [CHANGELOG.md](CHANGELOG.md) for full details**

## Quick Start

### Installation

```bash
# Install the latest version
pip install prompt-scanner

# Or specify the version explicitly
pip install prompt-scanner==0.3.1
```

### Basic Usage

```python
from prompt_scanner import PromptScanner

# Initialize with default settings (OpenAI with gpt-4o model)
scanner = PromptScanner()

# Scan a text input for unsafe content
result = scanner.scan_text("What's the weather like today?")

# Check the safety status
if result.is_safe:
    print("Content is safe!")
else:
    print(f"Primary violation: {result.category.name}")
    print(f"Severity: {result.severity.level.value}")  # Now provides severity information
    print(f"Reasoning: {result.reasoning}")
```

### Command Line Interface

After installation, you can use the `prompt-scanner` command:

```bash
# Basic usage
prompt-scanner --text "What's the weather like today?"

# With API key
prompt-scanner --openai-api-key "your-key" --text "Tell me about Mars"

# Read from a file
prompt-scanner --file input.txt

# Read from stdin
cat input.txt | prompt-scanner --stdin

# Use Anthropic instead of OpenAI
prompt-scanner --provider anthropic --text "Tell me about Mars"

# Get basic process information
prompt-scanner -v --text "What's the weather like today?"

# Get full detailed output including token usage
prompt-scanner -vv --text "What's the weather like today?"

# Output in JSON format
prompt-scanner --text "What's the weather like today?" --format json

# Use custom guardrails
prompt-scanner --text "Tell me a secret" --guardrail-file custom_guardrails.json

# Disable colored output
prompt-scanner --text "What's the weather like today?" --no-color
```

### Adding Custom Guardrails

```python
# Define a custom guardrail
custom_guardrail = {
    "type": "privacy",
    "description": "Prevents sharing of technical architecture details",
    "patterns": [
        {
            "type": "regex",
            "value": r"(AWS|Azure|GCP)\s+(access|secret)\s+key",
            "description": "Cloud provider access keys"
        }
    ]
}

# Add the custom guardrail to the scanner
scanner.add_custom_guardrail("technical_info_protection", custom_guardrail)
```

### Using Decorators

```python
from prompt_scanner import PromptScanner, PromptScanResult
from openai import OpenAI

scanner = PromptScanner()
client = OpenAI()

# Decorator that scans prompts before processing
@scanner.decorators.scan(prompt_param="user_input")
def generate_content(user_input):
    # This function will only run if the content is safe
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message.content

# Usage
result = generate_content(user_input="Tell me about space")
```

## Documentation

For detailed documentation, please see the [docs](docs/index.md) directory:

- [Getting Started](docs/getting_started.md)
- [Custom Guardrails and Categories](docs/custom_guardrails.md)
- [Using Decorators](docs/decorators.md)
- [CLI Usage](docs/cli_usage.md)
- [API Reference](docs/api_reference.md)

## Examples

The package includes example scripts to demonstrate functionality:

```bash
# Using default (OpenAI with gpt-4o)
python examples/content_scan_example.py

# Basic usage example
python examples/basic_usage.py

# Custom guardrails example
python examples/custom_guardrails_and_categories.py

# CLI usage examples
bash examples/installed_cli_examples.sh

# Run CLI without installation
bash examples/run_without_installation.sh
```

## Quality

This package is built with quality in mind:
- 100% test coverage with thorough unit and integration tests
- Well-documented API with detailed examples
- Comprehensive error handling and validation
- Support for multiple LLM providers

## Configuration

See the [Getting Started](docs/getting_started.md) documentation for various ways to configure API keys.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the [MIT License](LICENSE) - see the [LICENSE](LICENSE) file for details.