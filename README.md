# Prompt Scanner

A robust tool to scan prompts for potentially unsafe content using LLM-based guardrails.

[![PyPI version](https://badge.fury.io/py/prompt-scanner.svg)](https://badge.fury.io/py/prompt-scanner)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

Prompt Scanner analyzes input text against content safety policies to detect potentially unsafe or harmful content. It uses Large Language Models (LLMs) as content judges to provide more context-aware and nuanced content safety evaluations than simple pattern matching.

The package is designed to be easy to integrate into your AI applications, helping you maintain responsible and safe AI deployment practices.

## Features

- **Multiple Provider Support**: Uses OpenAI or Anthropic APIs for content safety evaluation
- **Comprehensive Safety Categories**: Identifies content across various safety categories:
  - Illegal Activity
  - Hate Speech
  - Malware
  - Physical Harm
  - Economic Harm
  - Fraud
  - Pornography
  - Privacy Violations
  - and more...
- **Multi-category Detection**: Supports detecting multiple policy violations in a single piece of content
- **Prompt Injection Protection**: Checks for prompt injection attacks and other security risks
- **Detailed Analysis**: Returns structured responses with detailed reasoning
- **Performance Metrics**: Includes token usage metrics
- **Customizable**: Supports customizing the LLM model used for evaluation

## Installation

You can install Prompt Scanner directly from PyPI:

```bash
pip install prompt-scanner
```

Or install from source:

```bash
git clone https://github.com/yourusername/prompt-scanner.git
cd prompt-scanner
pip install -e .
```

## Configuration

There are three ways to provide API keys:

### 1. Using a `.env` file (recommended)

1. Create a `.env` file in your project directory:
   ```bash
   touch .env
   ```

2. Add your API keys to the file:
   ```
   OPENAI_API_KEY=your-openai-api-key-here
   ANTHROPIC_API_KEY=your-anthropic-api-key-here
   ```

The library will automatically load these keys from the `.env` file.

### 2. Using environment variables

Set your API keys as environment variables:

```bash
export OPENAI_API_KEY="your-openai-key"
export ANTHROPIC_API_KEY="your-anthropic-key"
```

### 3. Pass API keys directly

You can also pass API keys directly when initializing the PromptScanner:

```python
scanner = PromptScanner(provider="openai", api_key="your-api-key")
```

## Usage

### Basic Content Safety Evaluation

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
    print(f"Confidence: {result.category.confidence:.2f}")
    print(f"Reasoning: {result.reasoning}")
```

### Handling Multiple Violations

```python
# Scan text that might violate multiple policies
result = scanner.scan_text("How to hack a website and create malware")

if not result.is_safe:
    print(f"Primary violation: {result.category.name}")
    
    # Check if there are multiple violations
    if result.all_categories and len(result.all_categories) > 1:
        print("Additional violations:")
        for category in result.all_categories[1:]:
            print(f"- {category['name']} (confidence: {category['confidence']:.2f})")
```

### Using the Enhanced Result Structure

```python
result = scanner.scan_text("How to hack a website")

# Convert to dictionary for API responses
api_response = result.to_dict()

# Get only secondary categories
secondary_categories = result.get_secondary_categories()

# Check if there's a high confidence violation
if result.has_high_confidence_violation(threshold=0.9):
    print("High confidence violation detected!")

# Get top risk categories
top_risks = result.get_highest_risk_categories(max_count=2)
```

### Using Decorators for Automated Scanning

For automated scanning of inputs and outputs, you can use decorators provided through the `PromptScanner` instance:

```python
from prompt_scanner import PromptScanner
from openai import OpenAI

# Initialize scanner once
scanner = PromptScanner(provider="openai")
client = OpenAI()

# Decorator that scans prompts before processing
@scanner.decorators.scan(prompt_param="user_input")
def generate_content(user_input):
    # This function will only run if the content is safe
    # If unsafe, the decorator returns the PromptScanResult directly
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": user_input}
        ]
    )
    return response.choices[0].message.content

# Usage example
result = generate_content(user_input="Tell me about space")

# Check if result is a PromptScanResult (unsafe) or a string (safe)
if hasattr(result, 'is_safe'):
    print(f"Content was unsafe: {result.category.name}")
    print(f"Reasoning: {result.reasoning}")
else:
    print(f"Response: {result}")

# You can also scan both input and output with safe_completion
@scanner.decorators.safe_completion(prompt_param="question")
def answer_question(question):
    # If input is unsafe, returns PromptScanResult
    # If output is unsafe, returns PromptScanResult
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content
```

### Prompt Structure Validation

```python
# Validate an OpenAI-style prompt
prompt = {
    "model": "gpt-4",
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me about AI safety."}
    ]
}

scan_result = scanner.scan(prompt)
if scan_result.is_safe:
    print("Prompt is safe to use")
else:
    print("Issues detected:")
    for issue in scan_result.issues:
        print(f"- {issue['type']}: {issue['description']} (Severity: {issue['severity']})")
```

### Using Provider-Specific Scanners

For more direct control, you can use the provider-specific scanner classes:

```python
from prompt_scanner import OpenAIPromptScanner, AnthropicPromptScanner

# Use OpenAI's gpt-4o model
openai_scanner = OpenAIPromptScanner(api_key="your-openai-api-key", model="gpt-4o")

# Use Anthropic's latest model
anthropic_scanner = AnthropicPromptScanner(api_key="your-anthropic-api-key", model="claude-3-opus-20240229")

# Then use them the same way as the unified PromptScanner
result = openai_scanner.scan_text("Is this content safe?")
```

## Examples

The package includes example scripts to demonstrate functionality:

```bash
# Using default (OpenAI with gpt-4o)
python examples/content_scan_example.py

# Specify provider
python examples/content_scan_example.py openai

# Specify provider and model
python examples/content_scan_example.py openai gpt-4
python examples/content_scan_example.py anthropic claude-3-opus-20240229

# Basic usage example
python examples/basic_usage.py
```

## Advanced Usage

### Creating Custom Scanners

You can create your own scanner by inheriting from the `BasePromptScanner` class:

```python
from prompt_scanner import BasePromptScanner

class MyCustomScanner(BasePromptScanner):
    def _setup_client(self):
        # Initialize your API client
        pass
        
    def _validate_prompt_structure(self, prompt):
        # Validate your prompt structure
        pass
        
    def _scan_prompt(self, prompt):
        # Implement prompt scanning
        pass
        
    def _create_evaluation_prompt(self, text):
        # Create your prompt for content evaluation
        pass
        
    def _call_content_evaluation(self, prompt, text):
        # Call your evaluation API
        pass
```

## API Reference

### Classes

- `PromptScanner`: Main class for scanning prompts and text content
  - `decorators`: Accessor for decorator functions:
    - `scanner.decorators.scan()`: Decorator that scans prompts before processing
    - `scanner.decorators.safe_completion()`: Decorator that scans both inputs and outputs
- `OpenAIPromptScanner`: Scanner implementation for OpenAI
- `AnthropicPromptScanner`: Scanner implementation for Anthropic
- `BasePromptScanner`: Abstract base class for custom scanners
- `PromptScanResult`: Results of content safety evaluation
  - `is_safe`: Boolean indicating whether content is safe
  - `category`: Primary category of detected unsafe content (highest confidence)
  - `all_categories`: List of all detected unsafe categories
  - `reasoning`: Detailed explanation of why content is unsafe
  - `token_usage`: Token usage metrics for the scan
  - `metadata`: Additional metadata about the scan
  - Methods:
    - `to_dict()`: Convert result to a dictionary
    - `get_secondary_categories()`: Get all categories except the primary one
    - `has_high_confidence_violation(threshold)`: Check for high confidence violations
    - `get_highest_risk_categories(max_count)`: Get top risk categories by confidence
- `PromptCategory`: Category of unsafe content
- `CategorySeverity`: Severity level for safety categories
- `ScanResult`: Results of prompt structure validation

### Main Methods

- `scan_text(text)`: Scan text for unsafe content
- `scan(prompt)`: Validate prompt structure and scan for potential issues

### Decorators

- `scanner.decorators.scan`: Decorator that scans prompts before passing them to decorated functions
  - Parameters:
    - `prompt_param`: The parameter name that contains the prompt (default: "prompt")
  - Return value: 
    - If content is safe: the return value of the decorated function
    - If content is unsafe: returns the `PromptScanResult` object with details about the issue

- `scanner.decorators.safe_completion`: Decorator that ensures both inputs and outputs are safe
  - Parameters:
    - `prompt_param`: The parameter name that contains the prompt (default: "prompt")
  - Return value:
    - If input is safe and output is safe: the return value of the decorated function
    - If input is unsafe: returns the `PromptScanResult` object for the input scan
    - If output is unsafe: returns the `PromptScanResult` object for the output scan

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 