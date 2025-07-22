
<hr>

<div align="center">

<h1 align="center">SLIM CLI Tool</h1>

</div>

<pre align="center">Automate the application of best practices to your git repositories</pre>

<!-- Header block for project -->
[![SLIM](https://img.shields.io/badge/Best%20Practices%20from-SLIM-blue)](https://nasa-ammos.github.io/slim/)
<!-- ☝️ Add badges via: https://shields.io e.g. ![](https://img.shields.io/github/your_chosen_action/NASA-AMMOS/your_repo) ☝️ -->

<img width="1242" alt="slim-cli-screen" src="https://github.com/user-attachments/assets/8c1ae6be-f149-4b6e-a51a-b8b0cd6c79ff">

SLIM CLI is a command-line tool designed to infuse SLIM best practices seamlessly with your development workflow. It fetches and applies structured SLIM best practices directly into your Git repositories. The tool leverages artificial intelligence capabilities to customize and tailor the application of SLIM best practices based on your repository's specifics.

[Website](https://nasa-ammos.github.io/slim/) | [Docs/Wiki](https://nasa-ammos.github.io/slim/docs) | [Discussion Board](https://nasa-ammos.github.io/slim/forum) | [Issue Tracker](https://github.com/NASA-AMMOS/slim-cli/issues)

## Features

- **Modern CLI Interface**: List, patch, and infuse SLIM best practices into your Git repository workflow using a seamless terminal interface
- **Fetches the latest SLIM best practices** dynamically from SLIM's registry the moment they change
- **Patches and pushes**, SLIM best practices to your repository and pushes up to your Git remote (i.e. GitHub) - all automatically
- **AI Enabled**: 100+ AI models to automatically infuse best practices using AI customization for your repository
- **Extensible Architecture**: Easy-to-extend best practice system with centralized mapping and YAML configuration

## Contents

- [Features](#features)
- [Contents](#contents)
- [Quick Start](#quick-start)
  - [Requirements](#requirements)
  - [Setup Instructions for Local Development (For Contributors)](#setup-instructions-for-local-development-for-contributors)
  - [Setup Instructions via pip (Recommended for most users)](#setup-instructions-via-pip-recommended-for-most-users)
  - [Run Instructions](#run-instructions)
- [Changelog](#changelog)
- [Frequently Asked Questions (FAQ)](#frequently-asked-questions-faq)
- [Contributing](#contributing)
  - [Running Tests](#running-tests)
  - [Publishing a New Version](#publishing-a-new-version)
- [License](#license)
- [Support](#support)

## Quick Start

This guide provides a quick way to get started with our project. Please see our [docs](https://nasa-ammos.github.io/slim/docs) for a more comprehensive overview.

### Rich Terminal Experience

SLIM CLI features a modern terminal interface with:

- **🎨 Colored Output**: Rich markup with emojis, colors, and styled text
- **📊 Progress Indicators**: Real-time progress bars and spinners during operations
- **🔍 Interactive Commands**: Clean input handling with automatic progress pause/resume
- **💾 Dry-run Mode**: Preview operations without making changes using `--dry-run`

Example terminal output:
```
🛠️ SLIM CLI v2.0.0
✅ LiteLLM integration enabled - 100+ AI models available

⠸ Applying readme...
✅ Successfully applied best practice 'readme' to repository
   📁 Repository: /path/to/repo
   🌿 Branch: readme
   💬 Commit: Add README documentation

✅ Apply operation completed in 2.34 seconds
```

### Requirements

* Python 3.9+
* Git
* **Optional**: LiteLLM for enhanced AI model support (`pip install litellm`)
* **Optional**: `.env` file to properly configure the environment for AI model APIs
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
* **Steps to use `ollama/gemma3` as the local AI model:**
  1. **Download and Install `ollama`:**  
     Visit the [official Ollama website](https://ollama.com/) to download and install `ollama` for your operating system. Follow the installation instructions provided.

  2. **Start the `ollama` Service:**  
     Launch the `ollama` service to enable local model hosting. Run the following command in your terminal:
     ```bash
     ollama serve
     ```
  3. **Run and Test the Model:**  
     Verify the `ollama/gemma3` model is working correctly by running the following command. Note that the first run may take some time to download the model:
     ```bash
     ollama run gemma3
     ```

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
   - `--best-practice-ids`: List of best practice aliases to apply (e.g., `readme`, `governance-small`, `secrets-github`).
   - `--repo-urls`: List of repository URLs to apply the best practices to; not used if `--repo-dir` is specified.
   - `--repo-dir`: Local directory path of the repository where the best practices will be applied.
   - `--clone-to-dir`: Path where the repository should be cloned if not present locally. Compatible with `--repo-urls`.
   - `--use-ai`: Enables AI features to customize the application of best practices based on the project’s specific needs. Specify the model provider and model name as an argument (e.g., `azure/gpt-4o`).
   ```bash
   slim apply --best-practice-ids readme --best-practice-ids governance-small --repo-urls https://github.com/your-username/your-repo1 https://github.com/your-username/your-repo2 
   ```
   - To apply a best practice using AI customization:
   ```bash
   # Apply a specific best practice using AI customization
   slim apply --best-practice-ids readme --repo-urls https://github.com/your_org/your_repo.git --use-ai <model provider>/<model name>
   ```
   Example usage: 
   ```bash
   # Apply and deploy a best practice using Azure's GPT-4o model
   slim apply --best-practice-ids governance-small --repo-urls https://github.com/riverma/terraformly/ --use-ai azure/gpt-4o
   ```
   ```bash
   # Apply and deploy a best practice using Ollama's LLaMA 3.1 model
   slim apply --best-practice-ids governance-small --repo-urls https://github.com/riverma/terraformly/ --use-ai ollama/gemma3
   ```
   
3. **Deploy a best practice**
   - After applying best practices, you may want to deploy (commit and push) them to a remote repository.
   - `--best-practice-ids`: List of best practice aliases that have been applied and are ready for deployment.
   - `--repo-dir`: The local directory of the repository where changes will be committed and pushed.
   - `--remote-name`: Specifies the remote name in the git configuration to which the changes will be pushed.
   - `--commit-message`: A message describing the changes for the commit.
   ```bash
   slim deploy --best-practice-ids readme --best-practice-ids governance-small --repo-dir /path/to/repo --remote origin --commit-message "Apply SLIM best practices"
   ```

4. **Apply and deploy a best practice**
   - Combines the application and deployment of a best practice into one step.
   - `--best-practice-ids`: List of best practice aliases to apply and then deploy.
   - `--repo-urls`: List of repository URLs for cloning if not already cloned; not used if `--repo-dir` is specified.
   - `--repo-dir`: Specifies the directory of the repository where the best practice will be applied and changes committed.
   - `--remote-name`: Specifies the remote to which the changes will be pushed. Format should be a GitHub-like URL base. For example `https://github.com/my_github_user`
   - `--commit-message`: A message describing the changes for the commit.
   - `--use-ai`: If specified, enables AI customization of the best practice before applying. False by default.
   ```bash
   slim apply-deploy --best-practice-ids readme --repo-urls https://github.com/your-username/your-repo1 https://github.com/your-username/your-repo2 --remote origin --commit-message "Integrated SLIM best practice with AI customization"
   ```
   Example output:
   ```
   AI features disabled
   Applied best practice readme and committed to branch readme
   Pushed changes to remote origin on branch readme
   ```

5. **Generate documentation**
   - Generates Docusaurus documentation for a repository.
   - `--repo-dir`: Path to the repository directory.
   - `--output-dir`: Directory where the generated documentation will be saved.
   - `--use-ai`: Optional. Enables AI enhancement of documentation. Specify the model provider and model name (e.g., `azure/gpt-4o`).
   
   **AI Model Recommendations:**
   - **Recommended**: Use cloud-based models like `openai/gpt-4o-mini`, `azure/gpt-4o`, or `openai/gpt-4o` for best documentation quality
   - **Local models**: While supported (e.g., `ollama/gemma3`), local models typically produce lower quality documentation and may not follow formatting requirements consistently
   
   **Template-Only Mode** - Generate just the template structure without analyzing a repository:
   ```bash
   slim apply --best-practice-ids docs-website --template-only --output-dir ../docs-site
   ```
   
   **AI-Enhanced Documentation** (Recommended approach):
   ```bash
   # Using OpenAI (recommended for quality)
   slim apply --best-practice-ids docs-website --repo-dir /path/to/your/repo --output-dir /path/to/output --use-ai openai/gpt-4o
   
   # Using Azure OpenAI (recommended for enterprise)
   slim apply --best-practice-ids docs-website --repo-dir /path/to/your/repo --output-dir /path/to/output --use-ai azure/gpt-4o
   
   # Using local models (basic quality, not recommended for production)
   slim apply --best-practice-ids docs-website --repo-dir /path/to/your/repo --output-dir /path/to/output --use-ai ollama/gemma3

   # Explore available AI models
   slim models list
   slim models recommend --task documentation --tier balanced
   slim models setup anthropic
   ```
   
   Example usage:
   ```bash
   slim apply --best-practice-ids docs-website --repo-dir ./hysds --output-dir ./hysds-docs-site --use-ai openai/gpt-4o
   ```
   
   **Revising an Existing Site**:
   ```bash
   # With cloud models (recommended)
   slim apply --best-practice-ids docs-website --revise-site --repo-dir /path/to/your/repo --output-dir ./docs-site --use-ai openai/gpt-4o
   
   # With local models (basic quality)
   slim apply --best-practice-ids docs-website --revise-site --repo-dir /path/to/your/repo --output-dir ./docs-site --use-ai ollama/gemma3
   ```
   
   **Generated Content**
   The documentation generator creates the following sections:

     - **Overview**: Project description, features, and key concepts (from README)
     - **Installation**: Setup instructions and prerequisites
     - **API Reference**: Auto-generated API documentation from source code
     - **Development**: Development workflow, project structure, and coding standards
     - **Contributing**: Contributing guidelines
     - **And more**: The documentation is structured to be comprehensive and user-friendly
   
   **Integration with Docusaurus**
   After generating the documentation, you can view it by:

      1. Installing dependencies in the output directory:
      ```bash
      cd /path/to/output
      npm install
      # or
      yarn
      ```

      2. Starting the development server:
      ```bash
      npm start
      # or
      yarn start
      ```

      3. Building for production:
      ```bash
      npm run build
      # or
      yarn build
      ```

   **Quality Notes:**
   - Cloud-based AI models (OpenAI, Azure) produce significantly better documentation with proper formatting, comprehensive content, and better adherence to documentation standards
   - Local models may produce inconsistent formatting, incomplete sections, or lower-quality content
   - For production documentation sites, we strongly recommend using cloud-based AI models

6. **Generate Tests**
   - Generates unit tests for a repository using AI.
   - `--repo-dir`: Path to the repository directory.
   - `--output-dir`: Optional. Directory where the generated tests will be saved.
   - `--model`: Optional. AI model to use (default: "azure/gpt-4o").
   - `--verbose`, `-v`: Optional. Enable detailed logging.
   ```bash
   slim generate-tests --repo-dir /path/to/repo --output-dir /path/to/tests --model ollama/llama3.3
   ```

7. **Discover and Manage AI Models**
   
   SLIM CLI supports 100+ AI models through LiteLLM integration with automatic model discovery:
   
   ```bash
   # List all available models (100+ models from various providers)
   slim models list
   
   # Filter by provider
   slim models list --provider anthropic
   slim models list --provider openai
   
   # Get AI model recommendations by task and quality tier
   slim models recommend                              # Default: documentation, balanced
   slim models recommend --task documentation --tier premium
   slim models recommend --task code_generation --tier fast
   
   # Get setup instructions for specific providers
   slim models setup anthropic
   slim models setup groq
   slim models setup ollama
   
   # Validate model configuration and test connectivity
   slim models validate anthropic/claude-3-5-sonnet-20241022
   slim models validate openai/gpt-4o
   slim models validate ollama/llama3.1
   ```
   
   **Example Model Commands Output:**
   ```bash
   $ slim models recommend --task documentation --tier premium
   
   🏆 Premium Cloud Models:
     • anthropic/claude-3-5-sonnet-20241022
     • openai/gpt-4o
     • openai/gpt-4-turbo
     • groq/llama-3.1-70b-versatile
   
   🦙 Local Models:
     • ollama/llama3.1:8b
     • ollama/codellama:13b
   
   💡 Usage Examples:
     # Premium documentation generation
     slim apply --best-practice-ids docs-website --use-ai anthropic/claude-3-5-sonnet-20241022
     
     # Fast local development  
     slim apply --best-practice-ids docs-website --use-ai ollama/llama3.1:8b
   ```

   **Supported AI Providers:**
   - **Cloud Premium**: OpenAI, Anthropic Claude, Google Gemini
   - **Cloud Fast**: Groq, Together AI, Cohere, Perplexity
   - **Local/Private**: Ollama, VLLM, LM Studio, GPT4All
   - **Enterprise**: Azure OpenAI, AWS Bedrock, Google Vertex AI
   
   **Environment Variables:**
   ```bash
   # OpenAI
   export OPENAI_API_KEY="sk-..."

   # Anthropic Claude
   export ANTHROPIC_API_KEY="sk-ant-..."

   # Google AI Studio & Gemini
   export GOOGLE_API_KEY="AIza..."
   
   # Groq (fast inference)
   export GROQ_API_KEY="gsk_..."
   
   # Together AI
   export TOGETHER_API_KEY="..."

   # Azure OpenAI
   export AZURE_API_KEY="..."
   export AZURE_API_BASE="https://your-resource.openai.azure.com/"
   export AZURE_API_VERSION="2024-02-01"
   
   # Ollama (local models) - no API key needed
   # Just ensure Ollama is running: ollama serve
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
