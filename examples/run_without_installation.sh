#!/bin/bash
# Example script for running the prompt-scanner CLI locally without installation

# Step 1: Ensure dependencies are installed
echo "Installing dependencies..."
pip install -r requirements.txt

# Step 2: Set API keys (you should replace these with your actual keys)
# Option 1: Set environment variables
export OPENAI_API_KEY="your-openai-api-key-here"
export ANTHROPIC_API_KEY="your-anthropic-api-key-here"

# Option 2: Create a temporary .env file (if you prefer)
# cat > .env << EOF
# OPENAI_API_KEY=your-openai-api-key-here
# ANTHROPIC_API_KEY=your-anthropic-api-key-here
# EOF

# Step 3: Run CLI examples

echo -e "\n======================="
echo "Basic usage (no verbosity)"
echo "======================="
python -m prompt_scanner.cli --text "What's the weather like today?"

echo -e "\n======================="
echo "Basic verbosity (-v)"
echo "======================="
python -m prompt_scanner.cli -v --text "What's the weather like today?"

echo -e "\n======================="
echo "Full verbosity (-vv)"
echo "======================="
python -m prompt_scanner.cli -vv --text "What's the weather like today?"

echo -e "\n======================="
echo "JSON output format"
echo "======================="
python -m prompt_scanner.cli --text "What's the weather like today?" --format json

echo -e "\n======================="
echo "Reading from a file"
echo "======================="
# Create a temporary file
cat > test_prompt.txt << EOF
I need to understand quantum computing. Can you explain it to me?
EOF
python -m prompt_scanner.cli --file test_prompt.txt

echo -e "\n======================="
echo "Reading from stdin"
echo "======================="
echo "How do I make a good pasta sauce?" | python -m prompt_scanner.cli --stdin

echo -e "\n======================="
echo "Using Anthropic as provider"
echo "======================="
python -m prompt_scanner.cli --provider anthropic --text "What is the capital of France?"

echo -e "\n======================="
echo "Creating and using custom guardrails"
echo "======================="
# Create a temporary guardrails file
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
python -m prompt_scanner.cli -v --text "My AWS access key is AKIA12345678EXAMPLE" --guardrail-file custom_guardrails.json

# Clean up temporary files
rm -f test_prompt.txt custom_guardrails.json 