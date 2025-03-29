# SLIM CLI Testing

## Introduction
This document provides an overview of the testing architecture for SLIM CLI. It focuses on the pytest-based testing framework used in the project and how to run the tests.

---
## Testing with pytest

SLIM CLI uses pytest for its testing framework. The tests are organized in the `tests/` directory, mirroring the structure of the source code in `src/`.

### Test Structure

- **Location**: `/tests/jpl/slim/`
- **Naming Convention**: Test files follow the pattern `test_*.py`
- **Test Organization**:
  - `test_cli.py`: Tests for the main CLI functionality
  - `test_best_practices.py`: Tests for best practices implementation
  - `test_best_practices_manager.py`: Tests for the best practices manager
  - `/utils/`: Tests for utility functions
    - `test_git_utils.py`: Tests for Git utilities
    - `test_io_utils.py`: Tests for I/O utilities
    - `test_ai_utils.py`: Tests for AI utilities

### Running Tests

To run the tests, you'll need pytest installed:

```bash
pip install pytest
```

#### Running All Tests

From the project root directory:

```bash
pytest
```

#### Running Specific Test Files

To run tests from a specific file:

```bash
pytest tests/jpl/slim/test_cli.py
```

#### Running Tests with Verbosity

For more detailed output:

```bash
pytest -v
```

To see print statements in the output:

```bash
pytest -s
```

You can combine options:

```bash
pytest -v -s
```

#### Running Tests with Coverage

To run tests with coverage reporting:

```bash
pip install pytest-cov
pytest --cov=jpl.slim
```

For a detailed HTML coverage report:

```bash
pytest --cov=jpl.slim --cov-report=html
```

### Test Environment

The tests use various mocking techniques to avoid making real API calls or performing actual Git operations:

- `unittest.mock` is used extensively to mock external dependencies
- The environment variable `SLIM_TEST_MODE` is set to `'True'` during tests to prevent real API calls
- Temporary directories are used for file system operations

### Writing New Tests

When adding new functionality to SLIM CLI, please follow these guidelines for writing tests:

1. Create a new test file in the appropriate location following the naming convention
2. Use pytest fixtures for setup and teardown
3. Mock external dependencies to ensure tests are isolated
4. Test both success and failure cases
5. Include docstrings explaining what each test is verifying

### Continuous Integration

Tests are automatically run in the CI/CD pipeline on GitHub Actions for:
- Pull requests to the main branch
- Pushes to the main branch

This ensures that all changes are tested before being merged.
