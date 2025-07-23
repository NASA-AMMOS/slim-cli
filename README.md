<hr>

<div align="center">

<h1 align="center">SLIM CLI Tool</h1>

</div>

<pre align="center">Automate the application of best practices to your git repositories</pre>

<!-- Header block for project -->
[![SLIM](https://img.shields.io/badge/Best%20Practices%20from-SLIM-blue)](https://nasa-ammos.github.io/slim/)
<!-- ☝️ Add badges via: https://shields.io e.g. ![](https://img.shields.io/github/your_chosen_action/NASA-AMMOS/your_repo) ☝️ -->

<img width="1242" alt="slim-cli-demo" src="https://nasa-ammos.github.io/slim/img/tools/slim-cli-demo-apply.gif">

SLIM CLI is a command-line tool designed to infuse SLIM best practices seamlessly with your development workflow. It fetches and applies structured SLIM best practices directly into your Git repositories. The tool leverages artificial intelligence capabilities to customize and tailor the application of SLIM best practices based on your repository's specifics.

[Website](https://nasa-ammos.github.io/slim/) | [Docs/Wiki](https://nasa-ammos.github.io/slim/docs) | [Discussion Board](https://nasa-ammos.github.io/slim/forum) | [Issue Tracker](https://github.com/NASA-AMMOS/slim-cli/issues)

📺 **[View demonstration videos and detailed tutorials](https://nasa-ammos.github.io/slim/docs/tools#slim-cli)**

## Features

- **Modern CLI Interface**: List, patch, and infuse SLIM best practices into your Git repository workflow using a seamless terminal interface
- **Rich Terminal Experience**: Colored output with emojis, progress indicators, and interactive commands with dry-run mode support
- **Fetches the latest SLIM best practices** dynamically from SLIM's registry the moment they change
- **Patches and pushes**, SLIM best practices to your repository and pushes up to your Git remote (i.e. GitHub) - all automatically
- **AI Enabled**: 100+ AI models to automatically infuse best practices using AI customization for your repository
- **Extensible Architecture**: Easy-to-extend best practice system with centralized mapping and YAML configuration

## Contents

- [Features](#features)
- [Contents](#contents)
- [Quick Start](#quick-start)
  - [Requirements](#requirements)
  - [Setup Instructions via pip (Recommended for most users)](#setup-instructions-via-pip-recommended-for-most-users)
  - [Run Instructions](#run-instructions)
- [Generate Documentation](#generate-documentation)
- [Discover and Manage AI Models](#discover-and-manage-ai-models)
- [Changelog](#changelog)
- [Frequently Asked Questions (FAQ)](#frequently-asked-questions-faq)
- [Contributing](#contributing)
  - [Setup for Local Development (For Contributors)](#setup-for-local-development-for-contributors)
  - [Running Tests](#running-tests)
  - [Publishing a New Version](#publishing-a-new-version)
- [License](#license)
- [Support](#support)

## Quick Start

This guide provides a quick way to get started with our project. Please see our [docs](https://nasa-ammos.github.io/slim/docs) for a more comprehensive overview.

### Requirements

* Python 3.9+
* Git
* **Optional**: LiteLLM for enhanced AI model support (automatically installed with slim-cli)
* **Optional**: API keys for cloud AI models - if using cloud models, set the appropriate environment variable:
  ```bash
  # Use the slim models setup command to see provider-specific instructions
  slim models setup <provider>
  
  # Example: slim models setup openai
  # Example: slim models setup anthropic
  ```
* **Optional**: For local AI models (e.g., Ollama), follow the setup instructions:
  ```bash
  slim models setup ollama
  ```

### Setup Instructions via pip (Recommended for most users)

As the SLIM CLI is written in Python, you'll need Python 3.9 or later. Usually, you'll want to create a virtual environment in order to isolate the dependencies of SLIM from other Python-using applications. Install into that environment using `pip`:

    pip install slim-cli

This installs the latest SLIM CLI and its dependencies from the [Python Package Index](https://pypi.org/). The new console script `slim` is now ready for use. Confirm by running either:

    slim --version
    slim --help

To upgrade:

    pip install --upgrade slim-cli

Or select a specific version, such as `X.Y.Z`:

    pip install slim-cli==X.Y.Z

### Run Instructions

The following commands demonstrate the core SLIM CLI functionality. Use `slim --help` for a complete list of options.

**Global Options:**
- `--version`, `-v`: Show version and exit
- `--dry-run`, `-d`: Preview operations without making changes
- `--logging`, `-l`: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  
  ```bash
  # Using long form
  slim --logging DEBUG apply --best-practice-ids readme
  
  # Using shorthand
  slim -l DEBUG apply -b readme
  
  # Preview changes without executing (dry run)
  slim -d apply -b readme -r <YOUR_GITHUB_REPO_URL>
  ```

#### Command Shorthands

SLIM CLI provides convenient shorthand options for commonly used arguments:

- `-b` for `--best-practice-ids` - Specify best practice aliases
- `-r` for `--repo-urls` - Specify repository URLs  
- `-d` for `--dry-run` - Preview changes without applying them
- `-l` for `--logging` - Set logging level
- `-m` for `--commit-message` - Custom commit message (apply-deploy and deploy commands)

**Examples:**
```bash
# Using full argument names
slim apply --best-practice-ids readme --repo-urls https://github.com/user/repo

# Using shorthands (equivalent)
slim apply -b readme -r https://github.com/user/repo

# Multiple values with shorthands
slim apply -b readme -b governance-small -r https://github.com/org/repo1 -r https://github.com/org/repo2
```

**Available Commands:**

1. **list** - List all available best practices from the SLIM registry
   ```bash
   slim list
   ```

2. **apply** - Apply best practices to git repositories
   
   **Key Options:**
   - `--best-practice-ids`, `-b`: Best practice aliases (required)
   - `--repo-urls`, `-r`: Repository URLs (cannot be used with --repo-dir)
   - `--repo-dir`: Local repository directory *[no shorthand]*
   - `--use-ai`: AI model for customization *[no shorthand]*
   - `--output-dir`: Output directory (required for docs-website) *[no shorthand]*
   
   ```bash
   # Basic usage - clone to temp folder and apply README template
   slim apply --best-practice-ids readme --repo-urls <YOUR_GITHUB_REPO_URL>
   
   # Using shorthand for best-practice-ids and repo-urls
   slim apply -b readme -r <YOUR_GITHUB_REPO_URL>
   
   # Apply multiple best practices (repeat -b for each)
   slim apply -b secrets-github -b secrets-precommit -r <YOUR_GITHUB_REPO_URL>
   
   # Apply with AI customization using cloud model
   slim apply -b readme -r <YOUR_GITHUB_REPO_URL> --use-ai anthropic/claude-3-5-sonnet-20241022
   
   # Apply with local AI model
   slim apply -b readme -r <YOUR_GITHUB_REPO_URL> --use-ai ollama/llama3.1
   
   # Apply to multiple repositories
   slim apply -b readme -r https://github.com/org/repo1 -r https://github.com/org/repo2
   
   # Apply using a list of repositories from a file
   slim apply -b governance-small --repo-urls-file repos.txt
   
   # Generate documentation website
   slim apply -b docs-website -r <YOUR_GITHUB_REPO_URL> --output-dir /path/to/docs-site --use-ai openai/gpt-4o
   ```

3. **apply-deploy** - Apply and deploy best practices in one step (creates branch and pushes to remote)
   
   **Key Options:**
   - `--best-practice-ids`, `-b`: Best practice aliases (required)
   - `--commit-message`, `-m`: Custom commit message
   - `--remote`: Remote name or URL (defaults to 'origin') *[no shorthand]*
   - `--repo-urls`, `-r`: Repository URLs
   
   ```bash
   # Basic usage
   slim apply-deploy --best-practice-ids readme --repo-urls <YOUR_GITHUB_REPO_URL>
   
   # Using shorthand options
   slim apply-deploy -b readme -r <YOUR_GITHUB_REPO_URL>
   
   # With custom commit message using shorthand
   slim apply-deploy -b readme -r <YOUR_GITHUB_REPO_URL> -m "Add comprehensive README documentation"
   
   # Multiple best practices with shorthand
   slim apply-deploy -b readme -b governance-small -r <YOUR_GITHUB_REPO_URL>
   ```

4. **deploy** - Deploy previously applied best practices (commit and push)
   
   **Key Options:**
   - `--best-practice-ids`, `-b`: Best practice aliases (required)
   - `--commit-message`, `-m`: Custom commit message
   - `--repo-dir`: Repository directory *[no shorthand]*
   - `--remote`: Remote name (defaults to 'origin') *[no shorthand]*
   
   ```bash
   # Basic usage
   slim deploy --best-practice-ids readme --repo-dir /path/to/repo --remote origin --commit-message "Apply SLIM best practices"
   
   # Using shorthand options
   slim deploy -b readme --repo-dir /path/to/repo -m "Apply SLIM best practices"
   
   # Deploy multiple best practices with shorthand
   slim deploy -b readme -b governance-small --repo-dir /path/to/repo
   ```

5. **models** - Discover and configure AI models
   ```bash
   # List all available models
   slim models list
   
   # Get model recommendations for specific tasks
   slim models recommend
   slim models recommend --task documentation --tier premium
   
   # Get setup instructions for a provider
   slim models setup anthropic
   slim models setup openai
   
   # Validate model configuration
   slim models validate openai/gpt-4o
   ```

## Generate Documentation

SLIM CLI can generate comprehensive Docusaurus documentation sites for your repositories using AI.

### Basic Usage

```bash
# Generate documentation with cloud AI (recommended)
slim apply -b docs-website -r <YOUR_GITHUB_REPO_URL> --output-dir /path/to/docs-site --use-ai openai/gpt-4o

# Generate documentation with local AI
slim apply -b docs-website -r <YOUR_GITHUB_REPO_URL> --output-dir /path/to/docs-site --use-ai ollama/llama3.1
```

### AI Model Recommendations

- **Cloud Models (Recommended)**: `openai/gpt-4o`, `anthropic/claude-3-5-sonnet-20241022`, `openai/gpt-4o-mini`
- **Local Models**: `ollama/llama3.1`, `ollama/gemma3` (lower quality, not recommended for production)

Use `slim models recommend --task documentation` to get personalized recommendations.

### Generated Content

The documentation generator creates:
- **Overview**: Project description and features
- **Installation**: Setup instructions
- **API Reference**: Auto-generated from source code
- **Development**: Workflow and coding standards
- **Contributing**: Guidelines for contributors

### Viewing Your Documentation

```bash
cd /path/to/output
npm install
npm start  # View at http://localhost:3000
```

📖 **For detailed documentation generation guidance, see the [SLIM CLI documentation guide](https://nasa-ammos.github.io/slim/docs/tools#slim-cli)**

## Discover and Manage AI Models

SLIM CLI supports 100+ AI models through LiteLLM integration. Use the `models` command to discover, configure, and validate AI models.

```bash
# List all available models
slim models list
slim models list --provider anthropic

# Get model recommendations
slim models recommend                              # Default: documentation, balanced
slim models recommend --task documentation --tier premium
slim models recommend --task code_generation --tier fast

# Get setup instructions for providers
slim models setup anthropic
slim models setup openai
slim models setup ollama

# Validate model configuration
slim models validate openai/gpt-4o
```

### Supported Providers

- **Cloud Premium**: OpenAI, Anthropic Claude, Google Gemini
- **Cloud Fast**: Groq, Together AI, Cohere, Perplexity
- **Local/Private**: Ollama, VLLM, LM Studio, GPT4All
- **Enterprise**: Azure OpenAI, AWS Bedrock, Google Vertex AI

### Environment Setup

Use `slim models setup <provider>` to see provider-specific instructions. Common examples:

```bash
# OpenAI
export OPENAI_API_KEY="sk-..."

# Anthropic Claude
export ANTHROPIC_API_KEY="sk-ant-..."

# Ollama (local models) - no API key needed
ollama serve
```

## Changelog

See our [CHANGELOG.md](CHANGELOG.md) for a history of our changes.

See our [releases page](https://github.com/NASA-AMMOS/slim-cli/releases) for our key versioned releases.

## Frequently Asked Questions (FAQ)

Questions about our project? Please see our: [FAQ](https://nasa-ammos.github.io/slim/faq)

## Contributing

Interested in contributing to our project? Please see our: [CONTRIBUTING.md](CONTRIBUTING.md). 

For a detailed understanding of the codebase architecture, including component design, data flow, and extension points, see our [ARCHITECTURE.md](ARCHITECTURE.md).

Specifically, see our section on [architecture and extensions](CONTRIBUTING.md#slim-architecture-and-extension-points) if you'd like to add support for a new best practice from SLIM or a new command. 

For guidance on how to interact with our team, please see our code of conduct located at: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

For guidance on our governance approach, including decision-making process and our various roles, please see our governance model at: [GOVERNANCE.md](GOVERNANCE.md)

### Setup for Local Development (For Contributors)

If you're working on `slim-cli` itself, you'll want to run it in editable mode so your changes are immediately reflected.

#### Using UV (Recommended for Development)

[UV](https://github.com/astral-sh/uv) is a fast Python package manager that simplifies dependency management and virtual environment handling. It's our recommended tool for local development.

```bash
# Install UV (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repo
git clone https://github.com/NASA-AMMOS/slim-cli.git
cd slim-cli

# UV automatically creates and manages the virtual environment
# Install all dependencies and the package in editable mode
uv sync

# Run the CLI locally with UV
uv run slim --help
uv run slim --version

# Run tests
uv run pytest tests/
```

#### Using Traditional pip/venv

If you prefer the traditional approach:

```bash
# Clone the repo
git clone https://github.com/NASA-AMMOS/slim-cli.git
cd slim-cli

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode
pip install --editable .

# Run the CLI locally
slim --help
slim --version
```

Use this method if:
- You're adding new features or fixing bugs in the CLI
- You're contributing to the SLIM project
- You want to test changes before publishing

### Running Tests

We use `pytest` for testing. For detailed information about our testing framework, test structure, and how to run tests, please refer to our [TESTING.md](TESTING.md) document.

#### With UV (Recommended)

```bash
# Run all tests
uv run pytest tests/

# Run a specific test file
uv run pytest tests/jpl/slim/test_cli.py

# Run tests with verbose output
uv run pytest -v -s
```

#### With Traditional Setup

```bash
# Install pytest (if not already installed)
pip install pytest

# Run all tests
pytest

# Run tests with verbose output
pytest -v -s
```

### Publishing a New Version

To publish a new version of SLIM CLI to the Python Package Index, typically you'll update the `VERSION.txt` file; then do:
```bash
pip install build wheel twine
python3 -m build .
twine upload dist/*
```

(Note: this can and should eventually be automated with GitHub Actions.)

## License

See our: [LICENSE](LICENSE)

## Support

Key points of contact are: [@riverma](https://github.com/riverma) and [@yunks128](https://github.com/yunks128)