# SLIM CLI Testing

## Introduction
This document describes the test architecture and strategy for SLIM CLI. SLIM CLI employs a comprehensive testing approach that combines traditional **pytest** unit testing with an innovative **YAML-based integration test framework**. Our testing philosophy emphasizes selective test execution, parameterized testing, and comprehensive coverage of all best practice scenarios through both isolated unit tests and end-to-end integration tests.

## Tests

We use the following tests to ensure SLIM CLI's quality, performance, and reliability:

- [x] Unit Tests
- [x] Integration Tests
- [x] Security Tests
<!-- - [ ] Add any additional test categories that are relevant to your project -->

### Unit Tests

**Location:** `tests/jpl/slim/`  
**Purpose:** Test individual modules, functions, and classes in isolation to ensure each component works correctly on its own.

#### Running Manually

##### Using UV (Recommended)

```bash
# UV automatically handles dependencies and virtual environment
# No need to install pytest separately

# Run ALL tests (unit + integration)
uv run pytest tests/

# Run all unit tests only
uv run pytest tests -m "unit"

# Run specific test modules
uv run pytest tests/jpl/slim/utils/test_git_utils.py
uv run pytest tests/jpl/slim/cli/test_models_command.py

# Run with verbose output
uv run pytest tests/jpl/slim/ -v -s
```

##### Using Traditional pip/venv

```bash
# Install test dependencies
pip install pytest

# Run ALL tests (unit + integration)
pytest tests/

# Run all unit tests only
pytest tests -m "unit"

# Run specific test modules
pytest tests/jpl/slim/utils/test_git_utils.py
pytest tests/jpl/slim/cli/test_models_command.py

# Run with verbose output
pytest tests/jpl/slim/ -v -s

```

#### Running Automatically
- **Trigger:** Not yet
- **Frequency:** Not yet
- **Where to see results:** Not yet

**Testing Framework:** pytest 7.x with fixtures and mocking

**Tips for Contributing:**
- Follow the naming convention `test_*.py` for test files
- Use pytest fixtures for setup and teardown
- Mock external dependencies (API calls, file systems, git operations)
- Test both success and failure paths
- Include docstrings explaining what each test verifies

### Integration Tests

**Location:** `tests/integration/best_practices_test_commands.yaml`  
**Purpose:** Test complete command workflows and interactions between components using a YAML-based configuration system.

#### Running Manually

##### Using UV (Recommended)

```bash
# Run ALL tests (unit + integration)
uv run pytest tests/

# Run all YAML-configured integration tests
uv run pytest tests/integration/test_best_practice_commands.py

# Run with verbose output to see individual YAML commands
uv run pytest -v tests/integration/test_best_practice_commands.py

# Enable/disable specific tests via YAML configuration
# Edit tests/integration/best_practices_test_commands.yaml
```

##### Using Traditional pip/venv

```bash
# Run ALL tests (unit + integration)
pytest tests/

# Run all YAML-configured integration tests
pytest tests/integration/test_best_practice_commands.py

# Run with verbose output to see individual YAML commands
pytest -v tests/integration/test_best_practice_commands.py

# Enable/disable specific tests via YAML configuration
# Edit tests/integration/best_practices_test_commands.yaml
```

**YAML Configuration Example:**
```yaml
readme:
  enabled: true  # Enable/disable entire practice
  commands:
    - command: "slim apply --best-practice-ids readme --repo-dir {temp_git_repo}"
      enabled: true   # Enable/disable individual commands
    - command: "slim deploy --best-practice-ids readme --repo-dir {temp_git_repo_with_remote}"
      enabled: false
```

**Template Variables:**
- `{temp_git_repo}` - Temporary git repository path
- `{temp_git_repo_with_remote}` - Git repo with configured remote
- `{temp_dir}` - Generic temporary directory
- `{temp_urls_file}` - File containing repository URLs
- `{test_ai_model}` - AI model for testing
- `{custom_remote}` - Custom git remote URL

#### Running Automatically
- **Trigger:** Not yet
- **Frequency:** Not yet
- **Where to see results:** Not yet

**Testing Framework:** YAML-based test configuration with pytest runner

**Tips for Contributing:**
- Add new practices to `tests/integration/best_practices_test_commands.yaml`
- Include both success and error scenarios
- Use template variables for dynamic values
- Test with different AI models when applicable
- Enable/disable toggles for development flexibility

**Adding a New Practice:**
```yaml
new-practice:
  enabled: true
  commands:
    - command: "slim apply --best-practice-ids new-practice --repo-dir {temp_git_repo}"
      enabled: true
    - command: "slim deploy --best-practice-ids new-practice --repo-dir {temp_git_repo_with_remote}"
      enabled: true
    # Error scenarios
    - command: "slim apply --best-practice-ids new-practice --repo-dir /nonexistent/path"
      enabled: true
```

### Security Tests

**Location:** SonarQube Cloud integration  
**Purpose:** Automated security vulnerability scanning and code quality analysis.

#### Running Manually

SonarQube Cloud analysis is automatically integrated and cannot be run manually.

#### Running Automatically
- **Trigger:** Every pull request automatically
- **Frequency:** On every PR submission and update
- **Where to see results:** SonarQube Cloud dashboard and PR status checks

**Testing Framework:** SonarQube Cloud automated scanning

**Tips for Contributing:**
- SonarQube Cloud automatically scans all code changes
- Address any security vulnerabilities flagged in PR checks
- Maintain security rating above B grade
- Review SonarQube Cloud report before merging PRs
- No manual setup required - fully automated

## Contributing to Tests

When adding new test functionality to SLIM CLI:

1. **Write unit tests** for new modules and functions
2. **Add integration tests** to `best_practices_test_commands.yaml` 
3. **Add AI integration tests** to `/tests/integration` under a new best practice class or existing. See examples for refernece. NOTE: you'll want to ensure your tests read output from `caplog.text` and properly filter the string to review AI generated logs from your debugging logs (i.e. `--logging DEBUG`)
4. **Include error scenarios** and edge cases
5. **Document test purpose** with clear docstrings
6. **Run full test suite** before submitting PR by running `uv run pytest` (or `pytest` if using traditional setup)

For detailed contribution guidelines, see [CONTRIBUTING.md](CONTRIBUTING.md).
