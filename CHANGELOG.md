# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-03-31

### Added
- Added full-featured command-line interface (CLI) tool
- Added support for passing API keys via command line arguments
- Added detailed verbosity levels in CLI (-v, -vv)
- Added colored output for better readability
- Added multiple input methods (text, file, stdin)
- Added JSON output format option
- Added comprehensive CLI documentation
- Added severity display for all unsafe content
- Added reasoning display for all scan results

### Fixed
- Fixed handling of missing severity attributes in scan results
- Fixed proper error handling in the CLI
- Fixed handling of custom guardrails loading
- Fixed null checks for consistency in output formatting

### Changed
- Enhanced CLI help text with better organization and examples
- Improved CLI error messages with helpful context
- Updated documentation with detailed CLI usage examples
- Added color-coded severity levels in CLI output

## [0.2.0] - 2025-03-30

### Added
- Achieved 100% test coverage for all modules
- Added comprehensive tests for edge cases in models and scanner
- Added detailed test cases for validation and error handling
- Added monkey patching approach for thorough testing
- Added command-line interface (CLI) for scanning prompts directly from the terminal
- Added support for multiple input methods (text, file, stdin) in CLI
- Added JSON and text output formats for CLI results

### Fixed
- Fixed issues with string representation in PromptScanResult
- Improved error handling in scanner classes
- Fixed validation logic for different message formats

### Changed
- Improved documentation examples
- Enhanced test suite with better mocking techniques
- Restructured test cases for better organization
- Added CLI usage documentation

## [0.1.0] - 2025-03-30

### Added
- Initial release of the prompt-scanner package
- Support for OpenAI and Anthropic API providers
- Basic prompt validation and scanning functionality
- Content safety evaluation using LLMs
- Custom guardrails and category support
- Decorator utilities for automatic scanning
- Basic documentation and examples 