# Copilot Instructions for Silent Sense

This repository contains **Silent Sense**, a containerized Python tool for monitoring online radio streams to detect silence and alert monitoring systems like Uptime Kuma.

## Project Overview

- **Main script**: `silent_sense.py` - The core monitoring application
- **Runtime**: Python 3.8+ with FFmpeg for audio analysis
- **Deployment**: Docker-first approach with `Dockerfile` included
- **Dependencies**: Managed via `requirements.txt`

## Code Style and Conventions

- Follow [PEP 8](https://pep8.org/) style guidelines for Python code
- Use type hints for function parameters and return values
- Include docstrings for all public functions and classes
- Use `logging` module for all output (not print statements)
- Keep functions focused and single-purpose

## Architecture Guidelines

- Configuration should support both environment variables and command-line arguments
- Use the `requests` library for HTTP operations
- Use `subprocess` for FFmpeg interactions
- Handle errors gracefully with appropriate logging and fallback behavior
- Support long-running monitoring with proper signal handling

## Testing and Validation

- Test changes locally with Python before containerizing
- Verify Docker builds complete successfully: `docker build -t silent-sense .`
- Test with real stream URLs when possible

## Key Components

1. **URL Validation**: Validate stream and notification URLs before use
2. **Audio Analysis**: FFmpeg-based silence detection with configurable thresholds
3. **Notifications**: HTTP push notifications to Uptime Kuma with status updates
4. **Heartbeat**: Regular status updates when stream is healthy

## Environment Variables

When adding new configuration options:
- Add both environment variable and CLI argument support
- Document in README.md with default values
- Update Dockerfile ENV declarations

## Security Considerations

- Never log sensitive URL parameters (tokens, API keys)
- Validate and sanitize all external inputs
- Use timeouts for all network operations
