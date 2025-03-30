from setuptools import setup, find_packages
import os

# Read version from __init__.py
with open(os.path.join("prompt_scanner", "__init__.py"), "r") as f:
    for line in f:
        if line.startswith("__version__"):
            version = line.split("=")[1].strip().strip('"').strip("'")
            break

# Read long description from README.md
with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="prompt-scanner",
    version=version,
    description="A tool to scan prompts for potentially unsafe content using LLM-based guardrails",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Shivam Aggarwal",
    author_email="shivama205@gmail.com",
    url="https://github.com/shivama205/prompt-scanner",
    packages=find_packages(),
    package_data={
        "prompt_scanner": ["data/*.yaml"],
    },
    install_requires=[
        "openai>=1.12.0",
        "anthropic>=0.15.0",
        "pyyaml>=6.0",
        "pydantic>=2.0.0",
        "requests>=2.31.0",
        "python-dotenv>=1.0.0"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Security",
    ],
    python_requires=">=3.8",
) 