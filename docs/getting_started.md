# Getting Started with Prompt Scanner

## Installation

You can install Prompt Scanner directly from PyPI:

```bash
pip install prompt-scanner
```

Or install from source:

```bash
git clone https://github.com/shivama205/prompt-scanner.git
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

## Basic Usage

### Content Safety Evaluation

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

### Scanning Prompts

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

## Provider Selection

You can choose between OpenAI and Anthropic for content evaluation:

```python
# Use OpenAI (default)
openai_scanner = PromptScanner(provider="openai", model="gpt-4o")

# Use Anthropic
anthropic_scanner = PromptScanner(provider="anthropic", model="claude-3-haiku-20240307")
``` 