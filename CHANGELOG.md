# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2024-03-30

### Added
- Achieved 100% test coverage for all modules
- Added comprehensive tests for edge cases in models and scanner
- Added detailed test cases for validation and error handling
- Added monkey patching approach for thorough testing

### Fixed
- Fixed issues with string representation in PromptScanResult
- Improved error handling in scanner classes
- Fixed validation logic for different message formats

### Changed
- Improved documentation examples
- Enhanced test suite with better mocking techniques
- Restructured test cases for better organization

## [0.1.0] - 2024-03-15

### Added
- Initial release of the prompt-scanner package
- Support for OpenAI and Anthropic API providers
- Basic prompt validation and scanning functionality
- Content safety evaluation using LLMs
- Custom guardrails and category support
- Decorator utilities for automatic scanning
- Basic documentation and examples 