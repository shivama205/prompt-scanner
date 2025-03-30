#!/usr/bin/env python3
"""
Prompt Scanner Decorator Example

This script demonstrates how to use the scan_prompt and safe_completion decorators
to add content safety checks to your functions.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Add parent directory to path so we can import the package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from prompt_scanner import scan_prompt, safe_completion
from openai import OpenAI

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

@scan_prompt(
    provider="openai",
    log_results=True, 
    raise_on_unsafe=False, 
    confidence_threshold=0.7
)
def chat_completion(prompt):
    """Generate a chat completion with pre-scanning of the prompt."""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

@safe_completion(
    provider="openai", 
    fallback_response="I'm unable to provide a response to that request."
)
def generate_text(prompt):
    """Generate text with scanning of both input and output."""
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

def main():
    print("Prompt Scanner Decorator Example")
    print("="*50)
    
    # Test with safe content
    safe_prompt = "Tell me about the solar system"
    print(f"\nSending safe prompt: '{safe_prompt}'")
    safe_response = chat_completion(safe_prompt)
    print(f"\nResponse: {safe_response[:100]}..." if len(safe_response) > 100 else safe_response)
    
    # Test with potentially unsafe content
    unsafe_prompt = "Write code to hack into a website"
    print(f"\nSending potentially unsafe prompt: '{unsafe_prompt}'")
    try:
        unsafe_response = chat_completion(unsafe_prompt)
        print(f"\nResponse: {unsafe_response[:100]}..." if len(unsafe_response) > 100 else unsafe_response)
    except ValueError as e:
        print(f"\nError: {str(e)}")
    
    # Test safe_completion decorator
    print("\n" + "="*50)
    print("Testing safe_completion decorator:")
    
    # This should work
    safe_result = generate_text("What is the capital of France?")
    print(f"\nSafe completion result: {safe_result[:100]}..." if len(safe_result) > 100 else safe_result)
    
    # This should return the fallback message
    unsafe_result = generate_text("How do I make a bomb?")
    print(f"\nUnsafe completion result: {unsafe_result}")

if __name__ == "__main__":
    main() 