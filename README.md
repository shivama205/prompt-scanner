# Prompt Scanner

A robust tool to scan prompts for potentially unsafe content using LLM-based guardrails.

[![PyPI version](https://badge.fury.io/py/prompt-scanner.svg)](https://badge.fury.io/py/prompt-scanner)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Test Coverage: 100%](https://img.shields.io/badge/Test%20Coverage-100%25-brightgreen.svg)](https://github.com/shivama205/prompt-scanner)

## Overview

Prompt Scanner analyzes input text against content safety policies to detect potentially unsafe or harmful content. It uses Large Language Models (LLMs) as content judges to provide more context-aware and nuanced content safety evaluations than simple pattern matching.

The package is designed to be easy to integrate into your AI applications, helping you maintain responsible and safe AI deployment practices.

## Features

- **Multiple Provider Support**: Uses OpenAI or Anthropic APIs for content safety evaluation
- **Comprehensive Safety Categories**: Identifies content across various safety categories
- **Multi-category Detection**: Supports detecting multiple policy violations in a single piece of content
- **Prompt Injection Protection**: Checks for prompt injection attacks and other security risks
- **Detailed Analysis**: Returns structured responses with detailed reasoning
- **Performance Metrics**: Includes token usage metrics
- **Customizable**: Supports customizing the LLM model used for evaluation
- **Custom Guardrails**: Add your own custom guardrails and content policy categories

## Quick Start

### Installation

```bash
pip install prompt-scanner
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
    print(f"Reasoning: {result.reasoning}")
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

This project is licensed under the MIT License - see the LICENSE file for details.