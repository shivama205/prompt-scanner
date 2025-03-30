#!/bin/bash
# Example script for using the prompt-scanner CLI tool

# Basic usage with text input
echo "Example 1: Basic scan of safe text"
prompt-scanner --text "What's the weather like today?"

echo -e "\nExample 2: Scanning potentially harmful content"
prompt-scanner --text "How can I hack into someone's social media account?"

echo -e "\nExample 3: Using verbose output"
prompt-scanner --text "What's the weather like today?" --verbose

echo -e "\nExample 4: Using JSON output format"
prompt-scanner --text "What's the weather like today?" --format json

echo -e "\nExample 5: Reading from a file"
cat > example_prompt.txt << EOF
I need to understand quantum computing. Can you explain it to me?
EOF
prompt-scanner --file example_prompt.txt

echo -e "\nExample 6: Using Anthropic as provider"
prompt-scanner --provider anthropic --text "What is the capital of France?"

echo -e "\nExample 7: Using a custom guardrail file"
cat > custom_guardrails.json << EOF
{
  "technical_info_protection": {
    "type": "privacy",
    "description": "Prevents sharing of technical architecture details",
    "patterns": [
      {
        "type": "regex",
        "value": "(AWS|Azure|GCP)\\\\s+(access|secret)\\\\s+key",
        "description": "Cloud provider access keys"
      }
    ]
  }
}
EOF
prompt-scanner --text "My AWS access key is AKIA12345678EXAMPLE" --guardrail-file custom_guardrails.json

echo -e "\nExample 8: Reading from stdin"
echo "How do I make a good pasta sauce?" | prompt-scanner --stdin

# Cleanup temporary files
rm -f example_prompt.txt custom_guardrails.json 