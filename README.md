
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
  - [Setup Instructions](#setup-instructions)
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
  - [Running the CLI Locally](#running-the-cli-locally)
    - [Basic Usage](#basic-usage-1)
    - [Examples](#examples)
- [Changelog](#changelog)
- [Frequently Asked Questions (FAQ)](#frequently-asked-questions-faq)
- [Contributing](#contributing)
  - [Local Development](#local-development)
  - [Running Tests](#running-tests)
  - [Publishing a New Version](#publishing-a-new-version)
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
  
### Setup Instructions

As the SLIM CLI is written in Python, you'll need Python 3.7 or later. Usually, you'll want to create a virtual environment in order to isolate the dependencies of SLIM from other Python-using applications. Install into that environment using `pip`:

    pip install slim-cli

This installs the latest SLIM CLI and its dependencies from the [Python Package Index](https://pypi.org/). The new console script `slim` is now ready for use. Confirm by running either:

    slim --version
    slim --help

To upgrade:

    pip install --upgrade slim-cli

Or select a specific version, such as `X.Y.Z`:

    pip install slim-cli==X.Y.Z



### Run Instructions

This section provides detailed commands to interact with the SLIM CLI. Each command includes various options that you can specify to tailor the tool's behavior to your needs.

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


### Generate Docusaurus documentation

The SLIM CLI includes a website generator that can automatically create [Docusaurus](https://docusaurus.io/) documentation from your repository content. This feature can analyze your codebase and generate comprehensive documentation including API references and installation guides.

#### Basic Usage

Generate documentation for your repository using:

```bash
python -m jpl.slim.cli generate-docs \
  --repo-dir /path/to/your/repo \
  --output-dir /path/to/output
```

#### AI-Enhanced Documentation

You can enable AI enhancement of the documentation using supported language models:

```bash
python -m jpl.slim.cli generate-docs \
  --repo-dir /path/to/your/repo \
  --output-dir /path/to/output \
  --use-ai ollama/llama3.3
```

Example usage:
```bash
python -m jpl.slim.cli generate-docs --repo-dir ./hysds --output-dir ./hysds/outputs --use-ai ollama/llama3.3
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
cp -r /path/to/output/* my-docs/docs/
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






### Running the CLI Locally

The CLI can be run using Python's module syntax.

#### Basic Usage
```bash
python -m jpl.slim.cli  [options]
```

#### Examples

1. Apply deployment best practices:
```bash
python -m jpl.slim.cli apply-deploy \
    --best-practice-ids SLIM-3.1 \
    --repo-urls https://github.com/yunks128/maap-py \
    --use-ai azure/gpt-4o
```


## Changelog

See our [CHANGELOG.md](CHANGELOG.md) for a history of our changes.

See our [releases page](https://github.com/NASA-AMMOS/slim-cli/releases) for our key versioned releases.

## Frequently Asked Questions (FAQ)

Questions about our project? Please see our: [FAQ](https://nasa-ammos.github.io/slim/faq)

## Contributing

Interested in contributing to our project? Please see our: [CONTRIBUTING.md](CONTRIBUTING.md)

For guidance on how to interact with our team, please see our code of conduct located at: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

For guidance on our governance approach, including decision-making process and our various roles, please see our governance model at: [GOVERNANCE.md](GOVERNANCE.md)

### Local Development

For local development of SLIM CLI, clone the GitHub repository, create a virtual environment, and then install the package in editable mode into it:
```bash
git clone --quiet https://github.com/NASA-AMMOS/slim-cli.git
cd slim-cli
python3 -m venv .venv
source .venv/bin/activate
pip install --editable .
```

The `slim` console-script is now ready in editable mode; changes you make to the source files under `src` are immediately reflected when run.

### Running Tests

We use `pytest` for testing. The test files are located within the `tests` subdirectory. To run the tests, ensure you are in the root directory of the project (where the `pyproject.toml` or `setup.py` is located) and have `pytest` installed. You can install `pytest` via pip:

```bash
pip install pytest
```

To execute all tests, simply run:

```bash
pytest
```

If you want to run a specific test file, you can specify the path to the test file:

```bash
pytest tests/jpl/slim/test_cli.py
```

This will run all the tests in the specified file. You can also use `pytest` options like `-v` for verbose output or `-s` to see print statements in the output:

```bash
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
