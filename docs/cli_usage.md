# Command Line Interface (CLI) Usage

The prompt-scanner package includes a command-line interface for scanning prompts directly from the terminal. After installation, the `prompt-scanner` command becomes available in your environment.

## API Key Setup

Before using the CLI, you need to set up API keys for the LLM provider you want to use:

### Option 1: Environment Variables

Set the appropriate environment variable for your chosen provider:

```bash
# For OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# For Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### Option 2: .env File

Create a `.env` file in your working directory:

```
OPENAI_API_KEY=your-openai-api-key
ANTHROPIC_API_KEY=your-anthropic-api-key
```

### Option 3: Command Line Arguments

Pass the API key directly via command line arguments:

```bash
# For OpenAI
prompt-scanner --openai-api-key "your-openai-api-key" --text "Your text to scan"

# For Anthropic
prompt-scanner --anthropic-api-key "your-anthropic-api-key" --provider anthropic --text "Your text to scan"
```

## Basic Usage

```bash
prompt-scanner --text "What's the weather like today?"
```

## Command Line Options

### API Configuration

| Option | Description |
|--------|-------------|
| `--openai-api-key KEY` | OpenAI API key (overrides environment variable) |
| `--anthropic-api-key KEY` | Anthropic API key (overrides environment variable) |

### Provider Configuration

| Option | Description |
|--------|-------------|
| `-p`, `--provider {openai,anthropic}` | LLM provider to use for scanning (default: openai) |
| `-m`, `--model MODEL` | Specific model to use (e.g., gpt-4o for OpenAI, claude-3-opus-20240229 for Anthropic) |

### Output Configuration

| Option | Description |
|--------|-------------|
| `-v`, `-vv` | Verbosity level. `-v` for basic info, `-vv` for detailed output with token usage |
| `-f`, `--format {text,json}` | Output format (default: text) |
| `--color` | Use color in output (default: True) |
| `--no-color` | Disable color in output |

### Input Options (Required, choose one)

| Option | Description |
|--------|-------------|
| `--text TEXT` | Text content to scan |
| `--file FILE` | File containing text to scan |
| `--stdin` | Read content from standard input |

### Custom Guardrails

| Option | Description |
|--------|-------------|
| `--guardrail-file FILE` | Path to a JSON file containing custom guardrails |

### General Options

| Option | Description |
|--------|-------------|
| `-h`, `--help` | Show the help message and exit |
| `--version` | Show program's version number and exit |

## Verbosity Levels

The CLI supports different verbosity levels:

### No Verbosity (Default)
Shows the scan result with reasoning:

```bash
prompt-scanner --text "What's the weather like today?"
```

Output:
```
✅ Content is safe

Reasoning:
The text "What's the weather like today?" is a simple and innocent question about the weather. It does not contain any harmful instructions, offensive content, or attempts to manipulate the AI system. This is a perfectly safe and appropriate query that falls within normal usage guidelines.
```

### Basic Verbosity (`-v`)
Shows the scan process and basic status information:

```bash
prompt-scanner -v --text "What's the weather like today?"
```

Output:
```
Input: Direct text input (27 characters)
Using provider: openai
Scanning content...
✅ Content is safe

Reasoning:
The text "What's the weather like today?" is a simple and innocent question about the weather. It does not contain any harmful instructions, offensive content, or attempts to manipulate the AI system. This is a perfectly safe and appropriate query that falls within normal usage guidelines.
```

### Full Verbosity (`-vv`)
Shows detailed information including token usage:

```bash
prompt-scanner -vv --text "What's the weather like today?"
```

Output:
```
Input: Direct text input (27 characters)
Using provider: openai
Using model: gpt-4o
Scanning content...
✅ Content is safe

Reasoning:
The text "What's the weather like today?" is a simple and innocent question about the weather. It does not contain any harmful instructions, offensive content, or attempts to manipulate the AI system. This is a perfectly safe and appropriate query that falls within normal usage guidelines.

Token usage:
{
  "completion_tokens": 92,
  "prompt_tokens": 212,
  "total_tokens": 304
}
```

## Input Methods

The CLI provides three mutually exclusive options for providing input:

### 1. Direct Text Input

```bash
prompt-scanner --text "What's the weather like today?"
```

### 2. File Input

```bash
prompt-scanner --file input.txt
```

### 3. Standard Input (stdin)

```bash
cat input.txt | prompt-scanner --stdin
```

or

```bash
echo "What's the weather like today?" | prompt-scanner --stdin
```

## Output Formats

### Text Format (Default)

```bash
prompt-scanner --text "What's the weather like today?"
```

Output:
```
✅ Content is safe

Reasoning:
The text "What's the weather like today?" is a simple and innocent question about the weather. It does not contain any harmful instructions, offensive content, or attempts to manipulate the AI system. This is a perfectly safe and appropriate query that falls within normal usage guidelines.
```

For unsafe content:
```
❌ Content violates: harmful_instructions
Severity: HIGH

Reasoning:
This content appears to be requesting information on how to engage in illegal hacking activities. Providing instructions on how to hack into systems without authorization would be illegal in most jurisdictions and could potentially cause harm. This clearly violates content policy regarding illegal activities and harmful instructions.
```

### JSON Format

```bash
prompt-scanner --text "What's the weather like today?" --format json
```

Output:
```json
{
  "is_safe": true,
  "category": null,
  "severity": null,
  "reasoning": "The text 'What's the weather like today?' is a simple and innocent question about the weather. It does not contain any harmful instructions, offensive content, or attempts to manipulate the AI system. This is a perfectly safe and appropriate query that falls within normal usage guidelines."
}
```

For unsafe content:
```json
{
  "is_safe": false,
  "category": "harmful_instructions",
  "severity": "HIGH",
  "reasoning": "This content appears to be requesting information on how to engage in illegal hacking activities. Providing instructions on how to hack into systems without authorization would be illegal in most jurisdictions and could potentially cause harm. This clearly violates content policy regarding illegal activities and harmful instructions."
}
```

## Color Formatting

By default, the CLI uses colors to make output more readable:
- Green for safe content
- Red for unsafe content and HIGH severity
- Yellow for MEDIUM severity
- Bold for important labels

You can disable colors using the `--no-color` flag:

```bash
prompt-scanner --text "What's the weather like today?" --no-color
```

## Custom Guardrails

You can use a JSON file to define custom guardrails:

```bash
prompt-scanner --text "My AWS secret key is 1234567890" --guardrail-file custom_guardrails.json
```

Where `custom_guardrails.json` might look like:

```json
{
  "technical_info_protection": {
    "type": "privacy",
    "description": "Prevents sharing of technical architecture details",
    "patterns": [
      {
        "type": "regex",
        "value": "(AWS|Azure|GCP)\\s+(access|secret)\\s+key",
        "description": "Cloud provider access keys"
      }
    ]
  }
}
```

## Example Command Combinations

### Basic Scan with OpenAI
```bash
prompt-scanner --text "Is this content safe?"
```

### Scan File with Anthropic and Custom Model
```bash
prompt-scanner --provider anthropic --model claude-3-opus-20240229 --file input.txt
```

### Process Piped Input with Verbose Output and JSON Format
```bash
cat sensitive_content.txt | prompt-scanner --stdin -vv --format json
```

### Use Custom Guardrails with Color Disabled
```bash
prompt-scanner --text "Here's my password: 123456" --guardrail-file custom_guardrails.json --no-color
```

## Using Locally Without Installation

If you haven't installed the package yet, you can run the CLI module directly:

```bash
# Clone the repository
git clone https://github.com/your-username/prompt-scanner.git
cd prompt-scanner

# Install dependencies
pip install -r requirements.txt

# Run the CLI directly
python -m prompt_scanner.cli --text "Test prompt"
```

## Exit Codes

The CLI will exit with the following status codes:

- `0`: The content was scanned successfully and is safe
- `1`: The content was scanned successfully but is unsafe, or an error occurred

This allows for easy integration with scripts and automated workflows. 