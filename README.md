
🚧 This repo is under construction. Do not use. 🚧

<hr>

<div align="center">

[INSERT YOUR LOGO IMAGE HERE (IF APPLICABLE)]
<!-- ☝️ Replace with your logo (if applicable) via ![](https://uri-to-your-logo-image) ☝️ -->
<!-- ☝️ If you see logo rendering errors, make sure you're not using indentation, or try an HTML IMG tag -->

<h1 align="center">SLIM CLI Tool</h1>
<!-- ☝️ Replace with your repo name ☝️ -->

</div>

<pre align="center">Automate the application of best practices to your git repositories</pre>
<!-- ☝️ Replace with a single sentence describing the purpose of your repo / proj ☝️ -->

<!-- Header block for project -->

[INSERT YOUR BADGES HERE (SEE: https://shields.io)] [![SLIM](https://img.shields.io/badge/Best%20Practices%20from-SLIM-blue)](https://nasa-ammos.github.io/slim/)
<!-- ☝️ Add badges via: https://shields.io e.g. ![](https://img.shields.io/github/your_chosen_action/NASA-AMMOS/your_repo) ☝️ -->

[INSERT SCREENSHOT OF YOUR SOFTWARE, IF APPLICABLE]
<!-- ☝️ Screenshot of your software (if applicable) via ![](https://uri-to-your-screenshot) ☝️ -->

SLIM CLI is a command-line tool designed to infuse SLIM best practices seamlessly with your development workflow. It fetches and applies structured SLIM best practices directly into your Git repositories. The tool leverages artificial intelligence capabilities to customize and tailor the application of SLIM best practices based on your repository's specifics.

[Website](https://nasa-ammos.github.io/slim/) | [Docs/Wiki](https://nasa-ammos.github.io/slim/docs) | [Discussion Board](https://nasa-ammos.github.io/slim/forum) | [Issue Tracker](https://github.com/NASA-AMMOS/slim-cli/issues)

## Features

- Command-line interface for applying SLIM best practices into Git development workflows
- Fetches the latest SLIM best practices dynamically from SLIM's registry
- Allows customization of best practices using advanced AI models before applying them to repositories
- Deploys, or git adds, commits, and pushes changes to your repository's remote
  
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
* OpenAI API key (for AI features)
  
### Setup Instructions

1. Clone the repository
   ```bash
   git clone https://github.com/NASA-AMMOS/slim-cli.git
   cd slim-cli
   ```
2. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

### Run Instructions

This section provides detailed commands to interact with the SLIM CLI. Each command includes various options that you can specify to tailor the tool's behavior to your needs.

1. **List all available best practices**
   - This command lists all best practices fetched from the SLIM registry.
   ```bash
   $ python slim-cli.py list
   ```

2. **Apply a best practice to a repository**
   - This command applies a specified best practice to your repository. You can also enable AI features to further customize the integration of the best practice.
   - `--best_practice_id`: Specifies the ID of the best practice to apply (required).
   - `--repo_url`: Optional URL of the repository where the best practice will be applied. This is necessary if you want the CLI to handle cloning and branch management remotely.
   - `--repo_dir`: Optional local directory path of the repository where the best practice will be applied. Use this if the repository is already cloned locally. Use this if not specifying `--repo_url`
   - `--clone_to_dir`: Optional local path where the repository should be cloned if it is not already present locally.
   - `--use-ai`: Enables AI features to customize the application of best practices based on the project’s specific needs. False by default.
   ```bash
   $ python slim-cli.py apply --best_practice_id SLIM-123 --use-ai --repo_url https://github.com/your-username/your-repo


3. **Deploy a best practice**
   - After applying best practices, you may want to deploy (commit and push) them to a remote repository.
   - `--best_practice_id`: The ID of the best practice that has been applied and is ready for deployment.
   - `--repo_dir`: The local directory of the repository where changes will be committed and pushed.
   - `--remote_name`: Specifies the remote name in the git configuration to which the changes will be pushed.
   - `--commit_message`: A message describing the changes for the commit.
   - `--use-ai`: Enables AI features to customize the application of best practices based on the project’s specific needs. False by default.
   ```bash
   $ python slim-cli.py deploy --best_practice_id SLIM-123 --repo_dir /path/to/repo --remote_name origin --commit_message "Apply SLIM best practice"
   ```
   Example output:
   ```
   Checked out to branch SLIM-123
   Added all changes to git index.
   Committed changes.
   Pushed changes to remote origin on branch SLIM-123
   ```

4. **Apply and deploy a best practice**
   - Combines the application and deployment of a best practice into one step.
   - `--best_practice_id`: Specifies the ID of the best practice to apply and then deploy.
   - `--repo_url`: Optional, specifies the repository URL for cloning if not already cloned.
   - `--repo_dir`: Specifies the directory of the repository where the best practice will be applied and changes committed.
   - `--remote_name`: Specifies the remote to which the changes will be pushed.
   - `--commit_message`: A message describing the changes for the commit.
   - `--use-ai`: If specified, enables AI customization of the best practice before applying. False by default.
   ```bash
   $ python slim-cli.py apply-deploy --best_practice_id SLIM-123 --repo_url https://github.com/your-username/your-repo --remote_name origin --commit_message "Integrated SLIM best practice with AI customization"
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

## License

See our: [LICENSE](LICENSE)

## Support

Key points of contact are: [@riverma](https://github.com/riverma) and [@yunks128](https://github.com/yunks128)
