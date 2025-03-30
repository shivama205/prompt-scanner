# Using Decorators

Prompt Scanner provides powerful decorator functions that allow you to automatically scan inputs and outputs in your AI-powered applications.

## Scan Decorator

The `scan` decorator checks the content of a specific parameter before executing the decorated function:

```python
from prompt_scanner import PromptScanner, PromptScanResult
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
```

### How It Works

1. The `scan` decorator examines the parameter specified by `prompt_param` (defaults to "prompt")
2. If the content is safe, it executes the decorated function normally
3. If the content is unsafe, it returns a `PromptScanResult` object with details about the violation

### Handling Return Values

When using the `scan` decorator, your code should always check the return type:

```python
# Call the decorated function
result = generate_content(user_input="Tell me about space")

# Handle the result
if isinstance(result, PromptScanResult):
    print(f"Content was unsafe: {result.category.name}")
    print(f"Reasoning: {result.reasoning}")
else:
    print(f"Response: {result}")
```

## Safe Completion Decorator

The `safe_completion` decorator checks both the input and output of a function:

```python
# Scan both input and output for safety
@scanner.decorators.safe_completion(prompt_param="question")
def answer_question(question):
    # Returns PromptScanResult if input or output is unsafe
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": question}
        ]
    )
    return response.choices[0].message.content
```

### How It Works

1. The decorator first checks if the input parameter is safe (like the `scan` decorator)
2. If the input is safe, it executes the function
3. If the function's output is also safe, it returns the normal function result
4. If either the input or output is unsafe, it returns a `PromptScanResult` object

### Working with Complex Objects

Both decorators can handle complex structures automatically:

```python
# For structured data
@scanner.decorators.scan(prompt_param="query")
def search_database(query):
    # Works with dictionaries or other complex objects
    # String fields will be checked for unsafe content
    results = {
        "results": ["Result 1", "Result 2"],
        "count": 2
    }
    return results
```

## Custom Behavior

You can create custom behaviors by using the decorators with your own logic:

```python
def handle_unsafe_content(result, fallback_response="I'm sorry, I can't process that request."):
    """Handle unsafe content by logging and returning a fallback response"""
    if isinstance(result, PromptScanResult) and not result.is_safe:
        # Log the violation
        logging.warning(f"Safety violation: {result.category.name} - {result.reasoning}")
        # Return fallback response instead
        return fallback_response
    return result

@scanner.decorators.scan(prompt_param="user_input")
def my_chat_function(user_input):
    # Process the input...
    response = get_llm_response(user_input)
    return response

# Usage with custom handling
response = handle_unsafe_content(my_chat_function("Tell me about space"))
print(response)
``` 