# SLIM CLI Testing

## Introduction
This document provides an overview of the testing architecture for SLIM CLI. It encompasses continuous testing concepts such as testing across the software development lifecycle and automated test execution. 

---
## Testing Categories
The below list of test categories is included in our testing setup. Further details are provided below.

- [x] **Static Code Analysis:** checks code for syntax, style, vulnerabilities, and bugs
- [x] **Unit Tests:** tests functions or components to verify that they perform as intended
- [x] **Integration Tests:** tests interactions between different components of the system
- [x] **Security Tests:** identifies potential security vulnerabilities
- [x] **Build Tests:** checks if the code builds into binaries or packages successfully

### Static Code Analysis Tests
- Location: `/.github/workflows/linting.yml`
- Purpose: Ensure code quality, consistency, and detect potential issues early.
- Running Tests:
  - Manually:
    1. Install required linters: `pip install flake8 pylint`
    2. Run linters: `flake8 slim_cli.py` and `pylint slim_cli.py`
    3. View results in the terminal output
  - Automatically:
    - Frequency:
      - On every pull request to the main branch
      - On every push to the main branch
    - Results Location: GitHub Actions tab in the repository
- Contributing:
  - Framework Used: flake8 and pylint
  - Tips:
    - Follow PEP 8 style guide
    - Use consistent naming conventions
    - Keep functions and methods short and focused

### Unit Tests
- Location: `/tests/unit/`
- Purpose: Verify individual functions and methods work correctly in isolation.
- Running Tests:
  - Manually:
    1. Navigate to the project root directory
    2. Run: `python -m unittest discover tests/unit`
    3. View results in the terminal output
  - Automatically:
    - Frequency:
      - On every pull request to the main branch
      - On every push to the main branch
    - Results Location: GitHub Actions tab in the repository
- Contributing:
  - Framework Used: unittest
  - Tips:
    - Test each function in `slim_cli.py` separately
    - Use mock objects to isolate units from external dependencies
    - Test edge cases and error conditions

### Integration Tests
- Location: `/tests/integration/`
- Purpose: Ensure different components of SLIM CLI work together correctly.
- Running Tests:
  - Manually:
    1. Navigate to the project root directory
    2. Run: `python -m unittest discover tests/integration`
    3. View results in the terminal output
  - Automatically:
    - Frequency:
      - On every pull request to the main branch
      - Nightly builds
    - Results Location: GitHub Actions tab in the repository
- Contributing:
  - Framework Used: unittest
  - Tips:
    - Test interactions between different functions and modules
    - Create test repositories to simulate real-world scenarios
    - Verify correct behavior of apply, deploy, and apply-deploy commands

### Security Tests
- Location: `/.github/workflows/security.yml`
- Purpose: Identify potential security vulnerabilities in the codebase and dependencies.
- Running Tests:
  - Manually:
    1. Install security scanning tools: `pip install bandit safety`
    2. Run scans: `bandit -r slim_cli.py` and `safety check`
    3. View results in the terminal output
  - Automatically:
    - Frequency:
      - On every pull request to the main branch
      - Weekly scans
    - Results Location: GitHub Actions tab in the repository
- Contributing:
  - Framework Used: Bandit and Safety
  - Tips:
    - Regularly update dependencies to their latest secure versions
    - Avoid using hard-coded credentials or sensitive information
    - Be cautious when using external libraries and evaluate their security

### Build Tests
- Location: `/.github/workflows/build.yml`
- Purpose: Ensure the SLIM CLI can be built and packaged correctly.
- Running Tests:
  - Manually:
    1. Navigate to the project root directory
    2. Run: `python setup.py sdist bdist_wheel`
    3. Check if the distribution files are created in the `dist/` directory
  - Automatically:
    - Frequency:
      - On every pull request to the main branch
      - On every push to the main branch
    - Results Location: GitHub Actions tab in the repository
- Contributing:
  - Framework Used: setuptools
  - Tips:
    - Keep `setup.py` up to date with new dependencies
    - Test the built package by installing it in a fresh virtual environment
    - Verify that the CLI works correctly when installed as a package
