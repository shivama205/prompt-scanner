import os
import sys
from typing import Dict, Any, List

# Add parent directory to path so we can import prompt_scanner
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompt_scanner import PromptScanner
from prompt_scanner.models import CustomGuardrail, CustomCategory

# Initialize the prompt scanner with OpenAI (default)
scanner = PromptScanner(api_key=os.environ.get("OPENAI_API_KEY"))

# Example 1: Adding a custom guardrail for preventing specific technical information
custom_guardrail = {
    "type": "privacy",
    "description": "Prevents sharing of technical architecture details",
    "patterns": [
        {
            "type": "regex",
            "value": r"(AWS|Azure|GCP)\s+(access|secret)\s+key",
            "description": "Cloud provider access keys"
        },
        {
            "type": "regex",
            "value": r"internal\s+API\s+endpoint",
            "description": "Internal API information"
        }
    ]
}

# Add the custom guardrail to the scanner
scanner.add_custom_guardrail("technical_info_protection", custom_guardrail)

# Example 2: Adding a custom content policy category
custom_category = {
    "name": "Technical Jargon Overuse",
    "description": "Content that uses excessive technical jargon making it inaccessible",
    "examples": [
        "The quantum flux capacitor initiates the hyper-threading of non-linear data structures",
        "Implement a recursive neural tensor network with bidirectional LSTM encoders for sentiment analysis"
    ]
}

# Add the custom category to the scanner
scanner.add_custom_category("tech_jargon", custom_category)

# Test the scanner with various prompts
test_prompts = [
    # Safe prompt
    {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Tell me about machine learning."}
        ]
    },
    # Prompt that violates the custom guardrail
    {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Can you help me organize my AWS secret keys?"}
        ]
    },
    # Prompt with technical jargon
    {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "The quantum flux capacitor initiates the hyper-threading of non-linear data structures. Can you explain this?"}
        ]
    }
]

# Scan each prompt and print results
for i, prompt in enumerate(test_prompts):
    print(f"\n=== Testing Prompt {i+1} ===")
    result = scanner.scan(prompt)
    print(f"Is safe: {result.is_safe}")
    
    if not result.is_safe:
        print("Issues detected:")
        for issue in result.issues:
            print(f"  - Type: {issue['type']}")
            print(f"    Description: {issue['description']}")
            print(f"    Severity: {issue.get('severity', 'unknown')}")
            if issue.get('custom', False):
                print(f"    Custom rule: Yes")
            print()

# Example 3: Demo programmatically creating and using CustomGuardrail model
print("\n=== Using CustomGuardrail and CustomCategory models ===")

# Create a guardrail using the Pydantic model
product_info_guardrail = CustomGuardrail(
    name="product_info_protection",
    type="privacy",
    description="Prevents sharing of product information before release",
    patterns=[
        {
            "type": "regex",
            "value": r"upcoming\s+product\s+release",
            "description": "Upcoming product release info" 
        },
        {
            "type": "regex",
            "value": r"unannounced\s+feature",
            "description": "Unannounced feature info"
        }
    ]
)

# Convert to dictionary for scanner usage
scanner.add_custom_guardrail(product_info_guardrail.name, product_info_guardrail.model_dump())

# Create a category using the Pydantic model
speculative_content = CustomCategory(
    id="speculation",
    name="Speculative Content",
    description="Content that makes unfounded speculations about upcoming products",
    examples=[
        "I heard they're going to release an AI-powered toaster next month",
        "The next version will definitely include teleportation features"
    ]
)

# Add to scanner
scanner.add_custom_category(speculative_content.id, speculative_content.model_dump())

# Test a prompt that violates the new guardrail
test_prompt = {
    "messages": [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me about the upcoming product release that's scheduled for next month."}
    ]
}

print("\n=== Testing New Custom Guardrail ===")
result = scanner.scan(test_prompt)
print(f"Is safe: {result.is_safe}")
if not result.is_safe:
    print("Issues detected:")
    for issue in result.issues:
        print(f"  - Type: {issue['type']}")
        print(f"    Description: {issue['description']}")
        print(f"    Severity: {issue.get('severity', 'unknown')}")
        print(f"    Custom rule: {issue.get('custom', False)}")
        print()

# Remove a custom guardrail
print("\n=== Removing a Custom Guardrail ===")
removed = scanner.remove_custom_guardrail("product_info_protection")
print(f"Guardrail removed: {removed}")

# Test the same prompt after removal
result = scanner.scan(test_prompt)
print(f"Is safe after removal: {result.is_safe}") 