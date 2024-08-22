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
- [Changelog](#changelog)
- [Frequently Asked Questions (FAQ)](#frequently-asked-questions-faq)
- [Contributing](#contributing)
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
   slim apply --best-practice-ids SLIM-3.1 --repo-urls https://github.com/riverma/terraformly/ --use-ai ollama/llama3.1:405b
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
   - `--remote-name`: Specifies the remote to which the changes will be pushed.
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
