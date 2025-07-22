# CLAUDE.md - AI Assistant Advisory Notes

## Purpose
This document provides AI-specific guidance for working with the SLIM CLI codebase. For project details, refer to the documentation files listed below.

## Essential Documentation Order
1. **README.md** - Project overview, installation, basic usage
2. **ARCHITECTURE.md** - System design, components, extension points
3. **CONTRIBUTING.md** - Development setup, how to add features, coding standards
4. **TESTING.md** - Test architecture, running tests, writing new tests

## AI Assistant Guidelines

### When Reviewing Code
- Python 3.9+ is required due to numpy 2.0.2 dependency
- UV is the recommended package manager for development
- pip is included as a dependency for subprocess operations

### When Suggesting Changes
- Follow existing Typer patterns with Rich integration for CLI output
- Use `console.print()` for user output, `logging.debug()` for debugging
- Maintain the established command structure in `src/jpl/slim/commands/`
- New best practices require registration in `practice_mapping.py`
- Consider semantic versioning when making changes (update `src/jpl/slim/VERSION.txt`)
- Use semantic commit message format: `<type>(<scope>): <description>`

### When Running Commands
- Always use `uv run` prefix for development commands
- Test with `--dry-run` flag first when making destructive changes
- Use `--logging DEBUG` to see detailed execution information

### Common Pitfalls to Avoid
- Don't assume pip/venv setup - check if user is using UV
- Don't create new files unless absolutely necessary
- Don't modify git config or push without explicit user request

### Testing Reminders
- Run `uv run pytest tests/` before suggesting PR submission
- Check both unit tests and YAML integration tests
- AI-related tests may fail without proper model configuration

### Key Context
- This is a NASA-AMMOS project for applying software best practices
- Supports AI models via LiteLLM integration
- Uses YAML-based configuration for prompts and tests
- Best practices are fetched from a centralized SLIM registry

## Quick Command Reference
```bash
# Development setup
uv sync

# Run CLI
uv run slim --help

# Run all tests
uv run pytest tests/

# Debug mode
uv run slim --logging DEBUG [command]
```