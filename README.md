
<hr>

<div align="center">

<h1 align="center">SLIM CLI Tool</h1>

</div>

<pre align="center">Automate the application of best practices to your git repositories</pre>

<!-- Header block for project -->
[![SLIM](https://img.shields.io/badge/Best%20Practices%20from-SLIM-blue)](https://nasa-ammos.github.io/slim/)
<!-- ☝️ Add badges via: https://shields.io e.g. ![](https://img.shields.io/github/your_chosen_action/NASA-AMMOS/your_repo) ☝️ -->

<img width="1242" alt="slim-cli-screen" src="https://github.com/user-attachments/assets/5a38e016-04ea-4e4d-b2b8-5e443367c899">

SLIM CLI is a command-line tool designed to infuse SLIM best practices seamlessly with your development workflow. It fetches and applies structured SLIM best practices directly into your Git repositories. The tool leverages artificial intelligence capabilities to customize and tailor the application of SLIM best practices based on your repository's specifics.

[Website](https://nasa-ammos.github.io/slim/) | [Docs/Wiki](https://nasa-ammos.github.io/slim/docs) | [Discussion Board](https://nasa-ammos.github.io/slim/forum) | [Issue Tracker](https://github.com/NASA-AMMOS/slim-cli/issues)

## Features

- Command-line interface for applying SLIM best practices into Git development workflows.
- Fetches the latest SLIM best practices dynamically from SLIM's registry.
- Allows customization of best practices using advanced AI models before applying them to repositories.
- Deploys, or git adds, commits, and pushes changes to your repository's remote.
  
## Contents

- [Features](#features)
- [Contents](#contents)
- [Quick Start](#quick-start)
  - [Requirements](#requirements)
  - [Setup Instructions via pip (Recommended for most users)](#setup-instructions-via-pip-recommended-for-most-users)
  - [Setup Instructions for Local Development (For Contributors)](#setup-instructions-for-local-development-for-contributors)
  - [Run Instructions](#run-instructions)
  - [Generate Docusaurus documentation](#generate-docusaurus-documentation)
    - [Basic Usage](#basic-usage)
    - [AI-Enhanced Documentation](#ai-enhanced-documentation)
    - [Generated Content](#generated-content)
    - [Integration with Docusaurus](#integration-with-docusaurus)
  - [Unit Test Generation](#unit-test-generation)
    - [Features](#features-1)
    - [Usage](#usage)
    - [Options](#options)
    - [Naming Conventions](#naming-conventions)
    - [Generated Test Structure](#generated-test-structure)
- [Changelog](#changelog)
- [Frequently Asked Questions (FAQ)](#frequently-asked-questions-faq)
- [Contributing](#contributing)
  - [Running Tests](#running-tests)
  - [Publishing a New Version](#publishing-a-new-version)
    - [How It Works](#how-it-works)
    - [Commit Message Format](#commit-message-format)
    - [Examples](#examples-1)
- [License](#license)
- [Support](#support)

## Quick Start

This guide provides a quick way to get started with our project. Please see our [docs](https://nasa-ammos.github.io/slim/docs) for a more comprehensive overview.

### Requirements

* Python 3.7+
* Git
* `.env` file to properly configure the environment for Azure and OpenAI APIs
  ```bash
  # .env for Azure
  AZURE_TENANT_ID=<Your-Azure-Tenant-ID>
  AZURE_CLIENT_ID=<Your-Azure-Client-ID>
  AZURE_CLIENT_SECRET=<Your-Azure-Client-Secret>
  API_ENDPOINT=<Your-Azure-OpenAI-API-Endpoint>
  API_VERSION=<Azure-OpenAI-API-Version>
  APIM_SUBSCRIPTION_KEY=<Your-Azure-Subscription-Key>
  ```
  ```bash
  # .env for OpenAI
  OPENAI_API_KEY=<Your-OpenAI-API-Key>
  ```
* **Steps to use `ollama/llama3.3` as the local AI model:**
  1. **Download and Install `ollama`:**  
     Visit the [official Ollama website](https://ollama.com/) to download and install `ollama` for your operating system. Follow the installation instructions provided.

  2. **Start the `ollama` Service:**  
     Launch the `ollama` service to enable local model hosting. Run the following command in your terminal:
     ```bash
     ollama serve
     ```
  3. **Run and Test the Model:**  
     Verify the `ollama/llama3.3` model is working correctly by running the following command. Note that the first run may take some time to download the model:
     ```bash
     ollama run llama3.3
     ```
  
### Setup Instructions via pip (Recommended for most users)

As the SLIM CLI is written in Python, you'll need Python 3.7 or later. Usually, you'll want to create a virtual environment in order to isolate the dependencies of SLIM from other Python-using applications. Install into that environment using `pip`:

    pip install slim-cli

This installs the latest SLIM CLI and its dependencies from the [Python Package Index](https://pypi.org/). The new console script `slim` is now ready for use. Confirm by running either:

    slim --version
    slim --help

To upgrade:

    pip install --upgrade slim-cli

Or select a specific version, such as `X.Y.Z`:

    pip install slim-cli==X.Y.Z

### Setup Instructions for Local Development (For Contributors) 

If you're working on `slim-cli` itself, you’ll want to run it in editable mode so your changes are immediately reflected.

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

### Run Instructions

This section provides detailed commands to interact with the SLIM CLI. Each command includes various options that you can specify to tailor the tool's behavior to your needs.

**NOTE:**
To specify a logging level for the app, choose between `DEBUG`, `INFO` (default), `WARNING`, `ERROR`, `CRITICAL`: 
```slim --logging DEBUG```

1. **List all available best practices**
   - This command lists all best practices fetched from the SLIM registry.
   ```bash
   slim list
   ```

2. **Apply best practices to repositories**
   - This command applies specified best practices to one or more repositories. It supports applying multiple practices simultaneously across multiple repositories, with AI customization options available.
   - `--best-practice-ids`: List of best practice IDs to apply.
   - `--repo-urls`: List of repository URLs to apply the best practices to; not used if `--repo-dir` is specified.
   - `--repo-dir`: Local directory path of the repository where the best practices will be applied.
   - `--clone-to-dir`: Path where the repository should be cloned if not present locally. Compatible with `--repo-urls`.
   - `--use-ai`: Enables AI features to customize the application of best practices based on the project’s specific needs. Specify the model provider and model name as an argument (e.g., `azure/gpt-4o`).
   ```bash
   slim apply --best-practice-ids SLIM-123 SLIM-456 --repo-urls https://github.com/your-username/your-repo1 https://github.com/your-username/your-repo2 
   ```
   - To apply a best practice using AI customization:
   ```bash
   # Apply a specific best practice using AI customization
   slim apply --best-practice-ids SLIM-123 --repo-urls https://github.com/your_org/your_repo.git --use-ai <model provider>/<model name>
   ```
   Example usage: 
   ```bash
   # Apply and deploy a best practice using Azure's GPT-4o model
   slim apply --best-practice-ids SLIM-3.1 --repo-urls https://github.com/riverma/terraformly/ --use-ai azure/gpt-4o
   ```
   ```bash
   # Apply and deploy a best practice using Ollama's LLaMA 3.1 model
   slim apply --best-practice-ids SLIM-3.1 --repo-urls https://github.com/riverma/terraformly/ --use-ai ollama/llama3.3
   ```
   
3. **Deploy a best practice**
   - After applying best practices, you may want to deploy (commit and push) them to a remote repository.
   - `--best-practice-ids`: List of best practice IDs that have been applied and are ready for deployment.
   - `--repo-dir`: The local directory of the repository where changes will be committed and pushed.
   - `--remote-name`: Specifies the remote name in the git configuration to which the changes will be pushed.
   - `--commit-message`: A message describing the changes for the commit.
   ```bash
   slim deploy --best-practice-ids SLIM-123 SLIM-456 --repo-dir /path/to/repo --remote-name origin --commit-message "Apply SLIM best practices"
   ```

4. **Apply and deploy a best practice**
   - Combines the application and deployment of a best practice into one step.
   - `--best-practice-ids`: List of best practice IDs to apply and then deploy.
   - `--repo-urls`: List of repository URLs for cloning if not already cloned; not used if `--repo-dir` is specified.
   - `--repo-dir`: Specifies the directory of the repository where the best practice will be applied and changes committed.
   - `--remote-name`: Specifies the remote to which the changes will be pushed. Format should be a GitHub-like URL base. For example `https://github.com/my_github_user`
   - `--commit-message`: A message describing the changes for the commit.
   - `--use-ai`: If specified, enables AI customization of the best practice before applying. False by default.
   ```bash
   slim apply-deploy --best-practice-ids SLIM-123 --repo-urls https://github.com/your-username/your-repo1 https://github.com/your-username/your-repo2 --remote-name origin --commit-message "Integrated SLIM best practice with AI customization"
   ```
   Example output:
   ```
   AI features disabled
   Applied best practice SLIM-123 and committed to branch slim-123
   Pushed changes to remote origin on branch slim-123
   ```

Each command can be modified with additional flags as needed for more specific tasks or environments.

5. **Generate documentation**
   - Generates Docusaurus documentation for a repository.
   - `--repo-dir`: Path to the repository directory.
   - `--output-dir`: Directory where the generated documentation will be saved.
   - `--use-ai`: Optional. Enables AI enhancement of documentation. Specify the model provider and model name (e.g., `ollama/llama3.3`).
   ```bash
   slim generate-docs --repo-dir /path/to/repo --output-dir /path/to/output --use-ai ollama/llama3.3
   ```

6. **Generate tests**
   - Generates unit tests for a repository using AI.
   - `--repo-dir`: Path to the repository directory.
   - `--output-dir`: Optional. Directory where the generated tests will be saved.
   - `--model`: Optional. AI model to use (default: "azure/gpt-4o").
   - `--verbose`, `-v`: Optional. Enable detailed logging.
   ```bash
   slim generate-tests --repo-dir /path/to/repo --output-dir /path/to/tests --model ollama/llama3.3
   ```



### Generate Docusaurus documentation

The SLIM CLI includes a website generator that can automatically create [Docusaurus](https://docusaurus.io/) documentation from your repository content. This feature can analyze your codebase and generate comprehensive documentation including API references and installation guides.

#### Basic Usage

Generate documentation for your repository using:

```bash
python -m slim generate-docs \
  --repo-dir /path/to/your/repo \
  --output-dir /path/to/output
```

#### AI-Enhanced Documentation

You can enable AI enhancement of the documentation using supported language models:

```bash
python -m slim generate-docs \
  --repo-dir /path/to/your/repo \
  --output-dir /path/to/output \
  --use-ai ollama/llama3.3
```

Example usage:
```bash
python -m slim generate-docs --repo-dir ./hysds --output-dir ./hysds/outputs --use-ai ollama/llama3.3
```

#### Generated Content

The documentation generator creates the following sections:

- **Overview**: Project description, features, and key concepts (from README)
- **Installation**: Setup instructions and prerequisites
- **API Reference**: Auto-generated API documentation from source code
- **Guides**: User guides and tutorials
- **Contributing**: Contributing guidelines
- **Changelog**: Version history and recent changes
- **Deployment**: Deployment instructions and configurations
- **Architecture**: System architecture and design documentation
- **Testing**: Testing documentation and examples
- **Security**: Security considerations and guidelines

#### Integration with Docusaurus

After generating the documentation, follow these steps to view it:

1. Install Docusaurus if you haven't already:
```bash
npx create-docusaurus@latest my-docs classic
```

2. Copy the generated files to your Docusaurus docs directory:
```bash
cp /path/to/output/*.md my-docs/docs/
cp /path/to/output/docusaurus.config.js my-docs/
cp /path/to/output/sidebars.js my-docs/
cp -r /path/to/output/static/* my-docs/static/
```

3. Start the Docusaurus development server:
```bash
cd my-docs
npm start
```


### Unit Test Generation

The slim CLI includes an AI-powered test generation feature that can automatically create unit tests for your codebase. This tool analyzes your source code and generates appropriate test files using testing frameworks for each supported language.

#### Features

- **Multi-Language Support**: Generates tests for Python, JavaScript, TypeScript, Java, C++, and C#
- **Framework-Specific**: Uses appropriate testing frameworks for each language:
  - Python: pytest
  - JavaScript/TypeScript: Jest
  - Java: JUnit
  - C++: Google Test
  - C#: NUnit
- **Comprehensive Testing**: Generates tests for normal operations, edge cases, and error scenarios
- **Dependency Mocking**: Includes appropriate mocking setup for external dependencies

#### Usage
Generate tests for an entire repository:

```bash
python -m jpl.slim.cli generate-tests --repo-dir ./my-project --output-dir ./my-project/tests
```

#### Options

- `--repo-dir` (Required): Path to your repository directory
- `--output-dir` (Optional): Custom output directory for generated tests
- `--model` (Optional): AI model to use (default: "azure/gpt-4o")
- `--verbose`, `-v` (Optional): Enable detailed logging



#### Naming Conventions

Generated test files follow language-specific conventions:

| Language | Test File Format | Example |
|----------|-----------------|----------|
| Python | `test_*.py` | `test_utils.py` |
| JavaScript | `*.test.js` | `utils.test.js` |
| TypeScript | `*.spec.ts` | `utils.spec.ts` |
| Java | `Test*.java` | `TestUtils.java` |
| C++ | `*_test.cpp` | `utils_test.cpp` |
| C# | `*Tests.cs` | `UtilsTests.cs` |

#### Generated Test Structure

Tests are generated with:
- Appropriate imports and framework setup
- Test class/suite organization
- Setup and teardown methods when needed
- Comprehensive test cases covering:
  - Normal operation
  - Edge cases
  - Error handling
  - External dependency mocking





## Changelog

See our [CHANGELOG.md](CHANGELOG.md) for a history of our changes.

See our [releases page](https://github.com/NASA-AMMOS/slim-cli/releases) for our key versioned releases.

## Frequently Asked Questions (FAQ)

Questions about our project? Please see our: [FAQ](https://nasa-ammos.github.io/slim/faq)

## Contributing

Interested in contributing to our project? Please see our: [CONTRIBUTING.md](CONTRIBUTING.md). Specifically, see our section on [architecture and extensions](CONTRIBUTING.md#slim-architecture-and-extension-points) if you'd like to add support for a new best practice from SLIM or a new command. 

For guidance on how to interact with our team, please see our code of conduct located at: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

For guidance on our governance approach, including decision-making process and our various roles, please see our governance model at: [GOVERNANCE.md](GOVERNANCE.md)


### Running Tests

We use `pytest` for testing. For detailed information about our testing framework, test structure, and how to run tests, please refer to our [TESTING.md](TESTING.md) document.

Here's a quick summary:

```bash
# Install pytest
pip install pytest

# Run all tests
pytest

# Run a specific test file
pytest tests/jpl/slim/test_cli.py

# Run tests with verbose output
pytest -v -s
```

### Publishing a New Version

This project uses semantic versioning with automated release management. New versions are automatically published based on conventional commit messages.

#### How It Works

1. The project uses `python-semantic-release` to analyze commit messages and determine the appropriate version bump
2. When changes are pushed to the `main` branch, a GitHub Actions workflow automatically:
   - Determines the next version number based on commit messages
   - Updates the version in `src/jpl/slim/VERSION.txt`
   - Creates a GitHub release
   - Builds and publishes the package to PyPI using trusted publishing

#### Commit Message Format

To properly trigger version updates, follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Where `type` is one of:

- `feat`: A new feature (triggers a minor version bump)
- `fix`: A bug fix (triggers a patch version bump)
- `docs`: Documentation changes (no version bump)
- `style`: Code style changes (no version bump)
- `refactor`: Code refactoring (no version bump)
- `perf`: Performance improvements (no version bump)
- `test`: Adding or fixing tests (no version bump)
- `build`: Changes to build system (no version bump)
- `ci`: Changes to CI configuration (no version bump)
- `chore`: Other changes (no version bump)

Include `BREAKING CHANGE:` in the commit footer to trigger a major version bump.

#### Examples

Patch release (bumps 1.2.3 to 1.2.4):
```
fix: resolve issue with command line argument parsing
```

Minor release (bumps 1.2.3 to 1.3.0):
```
feat: add support for custom configuration files
```

Major release (bumps 1.2.3 to 2.0.0):
```
feat: migrate to new API architecture

```

## License

See our: [LICENSE](LICENSE)

## Support

Key points of contact are: [@riverma](https://github.com/riverma) and [@yunks128](https://github.com/yunks128)
