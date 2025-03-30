# Custom Guardrails and Categories

Prompt Scanner allows you to define and add your own custom guardrails and content policy categories to enhance the safety monitoring of your prompts and responses.

## Adding Custom Guardrails

Custom guardrails help you enforce specific constraints on prompts and responses based on your application's requirements.

### Using Dictionaries

```python
from prompt_scanner import PromptScanner

# Initialize the scanner
scanner = PromptScanner()

# Define a custom guardrail for detecting technical information
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
```

### Using Pydantic Models

For better type safety and validation, you can use the `CustomGuardrail` Pydantic model:

```python
from prompt_scanner import PromptScanner
from prompt_scanner.models import CustomGuardrail

# Initialize the scanner
scanner = PromptScanner()

# Create a guardrail using the Pydantic model
product_guardrail = CustomGuardrail(
    name="product_info_protection",
    type="privacy",
    description="Prevents sharing of product information before release",
    patterns=[
        {
            "type": "regex",
            "value": r"upcoming\s+product\s+release",
            "description": "Upcoming product release info" 
        }
    ]
)

# Convert the model to a dictionary for the scanner
scanner.add_custom_guardrail(product_guardrail.name, product_guardrail.model_dump())
```

## Adding Custom Content Categories

Custom content categories allow you to define new types of potentially unsafe or harmful content specific to your domain.

### Using Dictionaries

```python
from prompt_scanner import PromptScanner

# Initialize the scanner
scanner = PromptScanner()

# Define a custom content policy category
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
```

### Using Pydantic Models

```python
from prompt_scanner import PromptScanner
from prompt_scanner.models import CustomCategory

# Initialize the scanner
scanner = PromptScanner()

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
```

## Removing Custom Guardrails and Categories

You can remove custom guardrails and categories when they are no longer needed:

```python
# Remove a custom guardrail
scanner.remove_custom_guardrail("technical_info_protection")

# Remove a custom category
scanner.remove_custom_category("tech_jargon")
```

## Complete Example

For a complete working example, see the [custom_guardrails_and_categories.py](../examples/custom_guardrails_and_categories.py) example in the examples directory. 