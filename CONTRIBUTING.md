# Contributing Guide

Thanks for taking the time to consider contributing! We very much appreciate your time and effort. This document outlines the many ways you can contribute to our project, and provides detailed guidance on best practices. We look forward to your help!

## Prerequisites

Before you begin contributing to our project, it'll be a good idea to ensure you've satisfied the below pre-requisites. 

### License

Our project has our licensing terms, including rules governing redistribution, documented in our [LICENSE](LICENSE) file. Please take a look at that file and ensure you understand the terms. This will impact how we, or others, use your contributions.

### Code of Conduct

Our Code of Conduct helps facilitate a positive interaction environment for everyone involved with the team, and provides guidance on what to do if you experience problematic behavior. Read more in our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and make sure you agree to its terms. 

### Developer Environment

For patch contributions, see our [README.md](README.md) for more details on how to set up your local environment, to best contribute to our project. 

At a minimum however to submit patches (if using Git), you'll want to ensure you have:
1. An account on the Version Control System our project uses (i.e. GitHub).
2. The Version Control System client (i.e. Git) installed on your local machine.
3. The ability to edit, build, and test our project on your local machine. Again, see our [README.md](README.md) for more details.

### Communication Channels

Before contributing changes to our project, it's a great idea to be familiar with our communication channels and to socialize your potential contributions to get feedback early. This will help give you context for your contributions, no matter their form.

Our communication channels are:
- [Issue tracking system](https://github.com/nasa-jpl/slim/issues) - a regularly monitored area to report issues with our software or propose changes
- [Discussion board](https://github.com/nasa-jpl/slim/discussions) - an permanently archived place to hold conversations related to our project, and to propose as well as show+tell topics to the contributor team. This resource can be searched for old discussions.

## Our Development Process

Our project integrates contributions from many people, and so we'd like to outline a process you can use to visualize how your contributions may be integrated if you provide something. 

```mermaid
flowchart TD
    repo_proj[(Our Repository)]-->|Fork|repo_fork[(Your Forked Repository)]
    repo_fork-->|Make|patch(Your Changes)
    patch-->|Submit|pr(Pull Request)
    pr==>|Approved|repo_proj
    pr-->|Changes Requested|repo_fork
```

### Fork our Repository

Forking our repository, as opposed to directly committing to a branch is the preferred way to propose changes. 

See [this GitHub guide](https://docs.github.com/en/get-started/quickstart/fork-a-repo) on forking for information specific to GitHub.com

#### Find or File an Issue

Make sure people are aware you're working on a patch! Check out our [issue tracking system](https://github.com/nasa-jpl/slim/issues) and find an open issue you'd like to work against, or alternatively file a new issue and mention you're working on a patch.

#### Choose the Right Branch to Fork

Our project typically has the following branches available, make sure to fork either the default branch or a branch someone else already tagged with a particular issue ticket you're working with.
- `main` - default branch

### Make your Modifications

Within your local development environment, this is the stage at which you'll propose your changes, and commit those changes back to version control. See the [README.md](README.md) for more specifics on what you'll need as prerequisites to setup your local development environment.

#### Commit Messages

Commit messages to version control should reference a ticket in their title / summary line:

```
Issue #248 - Show an example commit message title
```

This makes sure that tickets are updated on GitHub with references to commits that are related to them.

Commit should always be atomic. Keep solutions isolated whenever possible. Filler commits such as "clean up white space" or "fix typo" should be merged together before making a pull request, and significant sub-feature branches should be [rebased](https://www.youtube.com/results?search_query=git+rebase) to preserve commit history. Please ensure your commit history is clean and meaningful!

### Submit a Pull Request

Pull requests are the core way our project will receive your patch contributions. Navigate to your branch on your own fork within the version control system, and submit a pull request or submit the patch text to our project. 

Please make sure to provide a meaningful text description to your pull requests, whenever submitted.

**Working on your first Pull Request?** See guide: [How to Contribute to an Open Source Project on GitHub](https://kcd.im/pull-request)

### Reviewing your Pull Request

Reviewing pull-requests, or any kinds of proposed patch changes, is an art. That being said, we follow the following best practices:
- **Intent** - is the purpose of your pull-request clearly stated?
- **Solution** - is your pull-request doing what you want it to?
- **Correctness** - is your pull-request doing what you want it to *correctly*?
- **Small Patches** - is your patch of a level of complexity and brevity that it can actually be reviewed by a human being? Or is does it involve too much content for one pull request?
- **Coding best practices** - are you following best practices in the coding / contribution language being used?
- **Readability** - is your patch readable, and ultimately maintainable, by others?
- **Reproducibility** - is your patch reproducible by others?
- **Tests** - do you have or have conducted meaningful tests?

## SLIM Architecture and Extension Points

This section provides an overview of the SLIM codebase architecture and explains how to extend it by adding new best practices and commands.

### Architectural Overview

SLIM is designed with a modular architecture that makes it easy to extend with new functionality. The main components are:

```mermaid
flowchart TD
    CLI[CLI Module] --> Commands[Commands Package]
    CLI --> Manager[Manager Package]
    Commands --> Manager
    Manager --> BestPractices[Best Practices Package]
    Commands --> BestPractices
    Commands --> Utils[Utils Package]
    BestPractices --> Utils
    Manager --> Utils
```

#### Key Components

1. **CLI Module** (`src/jpl/slim/cli.py`):
   - Entry point for the command-line interface
   - Parses arguments and dispatches to appropriate command handlers
   - Registers all available commands

2. **Commands Package** (`src/jpl/slim/commands/`):
   - Contains modules for each subcommand of the SLIM CLI
   - Each command module has:
     - `setup_parser()` function to configure command arguments
     - `handle_command()` function to execute the command

3. **Best Practices Package** (`src/jpl/slim/best_practices/`):
   - Contains the base class and implementations of best practices
   - `BestPractice` abstract base class defines the interface
   - Concrete implementations extend the base class

4. **Manager Package** (`src/jpl/slim/manager/`):
   - Contains the `BestPracticeManager` class
   - Manages best practices and their lifecycle
   - Retrieves best practices by ID

5. **Utils Package** (`src/jpl/slim/utils/`):
   - Contains utility functions for:
     - Git operations (`git_utils.py`)
     - I/O operations (`io_utils.py`)
     - AI operations (`ai_utils.py`)

### Extension Points

SLIM is designed to be easily extended with new best practices and commands. Here's how to add new functionality:

#### Adding a New Best Practice

⚠️ NOTE: You'll want to ensure your best practice is referenced in the SLIM registry with assets, as this is a pre-requisite step to automating the application of a best practice:
  1. See this guide on adding to the SLIM registry: https://nasa-ammos.github.io/slim/docs/contribute/submit-best-practice#add-entry-to-the-registry
  2. Once added, run `slim list` to see and get the ID for the best practice you want to support. The ID numbers are automatically generated. 
  3. Proceed with the below steps once you have an ID and best practice assets to work with.

To add a new best practice to SLIM:

1. **Create a new class** that inherits from `BestPractice` in the `src/jpl/slim/best_practices/` directory:

```python
from jpl.slim.best_practices.base import BestPractice

class YourNewPractice(BestPractice):
    """
    Your new best practice implementation.
    
    This class implements a specific best practice for [describe purpose].
    """
    
    def __init__(self):
        """Initialize the best practice."""
        super().__init__(
            best_practice_id="your-practice-id",
            uri="https://github.com/nasa-jpl/slim/your-practice",
            title="Your Best Practice Title",
            description="Description of your best practice"
        )
    
    def apply(self, repo_path, use_ai=False, model=None, **kwargs):
        """
        Apply your best practice to a repository.
        
        Args:
            repo_path (str): Path to the repository
            use_ai (bool, optional): Whether to use AI assistance. Defaults to False.
            model (str, optional): AI model to use if use_ai is True. Defaults to None.
            
        Returns:
            str or None: Path to the applied file if successful, None otherwise
        """
        # Implementation of your best practice application
        pass
    
    def deploy(self, repo_path, remote=None, commit_message=None):
        """
        Deploy changes made by applying your best practice.
        
        Args:
            repo_path (str): Path to the repository
            remote (str, optional): Remote repository to push changes to. Defaults to None.
            commit_message (str, optional): Commit message for the changes. Defaults to None.
            
        Returns:
            bool: True if deployment was successful, False otherwise
        """
        # Implementation of your best practice deployment
        pass
```

2. **Register your best practice** in the `BestPracticeManager` class in `src/jpl/slim/manager/best_practices_manager.py`:

   - Add your best practice to the appropriate section in the `get_best_practice` method
   - Import your new best practice class at the top of the file

#### Adding a New Command

To add a new command to SLIM:

1. **Create a new command module** in the `src/jpl/slim/commands/` directory:

```python
"""
Your new command module for the SLIM CLI.

This module contains the implementation of the 'your-command' subcommand.
"""

import logging
from jpl.slim.manager.best_practices_manager import BestPracticeManager
from jpl.slim.utils.io_utils import fetch_best_practices
from jpl.slim.commands.common import SLIM_REGISTRY_URI

def setup_parser(subparsers):
    """
    Set up the parser for the 'your-command' command.
    
    Args:
        subparsers: Subparsers object from argparse
        
    Returns:
        The parser for the 'your-command' command
    """
    parser = subparsers.add_parser('your-command', help='Description of your command')
    parser.add_argument('--your-arg', required=True, help='Description of your argument')
    # Add more arguments as needed
    parser.set_defaults(func=handle_command)
    return parser

def handle_command(args):
    """
    Handle the 'your-command' command.
    
    Args:
        args: Arguments from argparse
    """
    logging.info(f"Executing your-command with args: {args.your_arg}")
    
    # Implement your command logic here
    # For example:
    practices = fetch_best_practices(SLIM_REGISTRY_URI)
    manager = BestPracticeManager(practices)
    
    # Your command-specific logic
    # ...
    
    logging.info("Your command completed successfully")
```

2. **Register your command** in the CLI module (`src/jpl/slim/cli.py`):

   - Import your command module at the top of the file:
   ```python
   from jpl.slim.commands.your_command import setup_parser as setup_your_command_parser
   ```

   - Add your command to the `create_parser` function:
   ```python
   setup_your_command_parser(subparsers)
   ```

3. **Update the `__init__.py`** in the commands package to expose your new command:

   - Add your command module to the imports
   - Add your command class to the `__all__` list

### Testing Your Extensions

After adding new best practices or commands, make sure to:

1. Write unit tests for your new functionality in the `tests/` directory
2. Run the existing test suite to ensure you haven't broken anything
3. Test your new functionality manually with various inputs and edge cases

## Ways to Contribute

### ⚠️ Issue Tickets

> *Do you like to talk about new features, changes, requests?*

Issue tickets are a very simple way to get involved in our project. It also helps new contributors get an understanding of the project more comprehensively. This is a great place to get started with the project if you're not sure where to start. 

See our list of issues at: [https://github.com/nasa-jpl/slim/issues](https://github.com/nasa-jpl/slim/issues)

#### Cleaning up Duplicate Issues

Often we receive duplicate issues that can confuse project members on *which* issue ticket to hold conversations upon.

Here's how you can help:
1. Scan the list of *open* issue tickets for duplicate titles, or internal wording 
2. If you find duplicates, copy / paste the below message on the conversation thread of the issue ticket *that has less participants* involved

```
This is a duplicate issue. Please migrate conversations over to [issue-XYZ](hyperlink to issue)
```

#### Good First Issues

Issue tickets can vary in complexity, and issues labeled with `good first issue` labels are often a great way to get started with the project as a newcomer. 

Take a look at our [issue tracking system](https://github.com/nasa-jpl/slim/issues), and filter by `good first issue` for issues that are low-complexity, and that will help you get familiar with our issue tracking and patch submission process.

#### Suggesting New Issue Labels

Labels within our [issue tracking system](https://github.com/nasa-jpl/slim/issues) are a great way to quickly sort through tickets. The project may not yet have labels to cover the full variety of issue tickets. Take a look through our list of issues, and if you notice a set of issue tickets that seem similar but are not categorized with an existing label, go ahead submit a request within one of the issues you've looked at with the following text:

```
I've noticed several other issues that are of the same category as this issue. Shall we make a new label for these types of issues?
```

#### Submitting Bug Issues

Resolving bugs is a priority for our project. We welcome bug reports. However, please make sure to do the following prior to submitting a bug report:
- **Check for duplicates** - there may be a bug report already describing your issue, so check the [issue tracking system](https://github.com/nasa-jpl/slim/issues) first.

Here's some guidance on submitting a bug issue:
1. Navigate to our [issue tracking system](https://github.com/nasa-jpl/slim/issues) and file a new issue
2. Select a bug template (if available) for your issue
   1. Fill out the template fields to the best of your ability, including output snippets or screenshots where applicable
3. Follow the general guidelines below for extra information about your bug
   1. Include a code snippet if you have it showcasing the bug
   2. Provide reproducible steps of how to recreate the bug
   3. If the bug triggers an exception or error message, include the *full message* or *stacktrace*
   4. Provide information about your operating system and the version of our project you're using

#### Submitting New Feature Issues

We welcome new feature requests to help grow our project. However, please make sure to do the following prior to submitting a new feature request:
- **Check for duplicates** - there may be a new feature issue already describing your issue, so check the [issue tracking system](https://github.com/nasa-jpl/slim/issues) first
- **Consider alternatives** - is your feature really needed? Or is there a feature within our project or with a third-party that may help you achieve what you want?

Here's some guidance on submitting a new feature issue:
1. Navigate to our [issue tracking system](https://github.com/nasa-jpl/slim/issues) and file a new issue
2. Select a new feature template (if available) for your issue
   1. Fill out the template fields to the best of your ability

#### Submitting Security Vulnerability Issues

Security vulnerabilities should **not** be filed to the regular issue tracking system.

Report your security vulnerabilities to the project maintainers directly.

Please be sure to:
* Indicate the severity of the vulnerability
* Provide any workarounds, if you know them
* Provide return-contact information to follow-up with you if needed

#### Reviewing Pull Requests

Reviewing others' contributions is a great way to learn about best practices in both contributions as well as software. 

Take a look at our [pull requests tracking system](https://github.com/nasa-jpl/slim/pulls), and try the following options for providing a review:
1. Read the code / patch associated with the pull-request, and take note of any coding, bug, or documentation issues if found
2. Try to recreate the pull-request patch on your local machine, and report if it has issues with your system in particular
3. Scan over suggested feedback from other contributors, and provide feedback if necessary

### 💻 Code

⚠️ It's **highly** advised that you take a look at our [issue tracking system](https://github.com/nasa-jpl/slim/issues) before considering any code contributions. Here's some guidelines:
1. Check if any duplicate issues exist that cover your code contribution idea / task, and add comments to those tickets with your thoughts.
2. If no duplicates exist, create a new issue ticket and get a conversation started before making code changes using our [communication channels](#communication-channels).

Once you have a solid issue ticket in hand and are ready to work on code, you'll want to:
1. Ensure you have development [prerequisites](#prerequisites) cleared.
2. Have your [development environment](#developer-environment) set up properly.
3. Go through our [development process](#our-development-process), including proposing changes to our project.

Some guidelines for code-specific contributions:
- **Do your homework** - read-up on necessary documentation, like `README.md`s, developer documentation, and pre-existing code to see the intention and context necessary to make your contribution a success. It's important to _communicate_ what you're working on through our project [communication channels](#communication-channels) and get buy-in from frequent contributors - this will help the project be more receptive to your contributions! 
- **Ask questions** - its important to ask questions while you work on your contributions, to check-in with frequent contributors on the style and the set of expectations to make your code contribution work well with pre-existing project code. Use our [communication channels](#communication-channels)
- **Keep positive** - code contributions, by their nature, have direct impacts on the output and functionality of the project. Keep a positive spirit as your code is reviewed, and take it in stride if core contributors take time to review, give you suggestions for your code or respectfully decline your contribution. This is all part of the process for quality open source development. 
- **Comments** - include *useful* comments throughout your code that explain the intention of a code block, not a step-by-step analysis. See our [inline code documentation](#inline-code-documentation) section for specifics. 

### 📖 Documentation 

Documentation is the core way our users and contributors learn about the project. We place a high value on the quality, thoroughness, and readability of our documentation. Writing or editing documentation is an excellent way to contribute to our project without performing active coding. 

⚠️ It's **highly** advised that you take a look at our [issue-tracking system](https://github.com/nasa-jpl/slim/issues) before considering any documentation contributions. Here's some guidelines:
1. Check if any duplicate issues exist that cover your documentation contribution idea / task, and add comments to those tickets with your thoughts.
2. If no duplicates exist, create a new issue ticket and get a conversation started before making documentation changes.

Some guidelines for documentation best practices (summarized from Google's [excellent documentation guide](https://google.github.io/styleguide/docguide/best_practices.html)):
- **Minimum viable docs** - don't do less documentation than your users / developers need, but also don't do more
- **Changed code = changed docs** - if your code has changed, remember to update your documentation
- **Delete old docs** - continually clean your documentation tree, and remove outdated docs regularly

#### Documentation Organization

The overall structure of our project documentation is as follows:
- Source-controlled documentation
  - [README.md](README.md) - top-level information about how to run, build, and contribute to the project
  - [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) - best practices and guidance on how to work well with other people in the project, and suggestions on dealing with interpersonal issues
  - [CONTRIBUTING.md](CONTRIBUTING.md) - guidance on contributing to the project
  - `*.py` - inline documentation available inside code files

For directions on contributing to our source-controlled documentation:
1. Ensure you have development [prerequisites](#prerequisites) cleared.
2. Have your [development environment](#developer-environment) set up properly.
3. Go through our [development process](#our-development-process), including proposing changes to our project.

#### Writing Style

To ensure documentation is readable and consistent by newcomers and experts alike, here are some suggestions on writing style for English:
- Use gender neutral pronouns (they/their/them) instead of he/she/his/her 
- Avoid qualifiers that minimize the difficulty of a task at hand, e.g. avoid words like "easily", "simply", "just", "merely", "straightforward", etc. Readers' expertise may not match your own, and qualifying complexity may deter some readers if the task does not match their level of experience. That being said, if a particular task is difficult or complex, do mention that. 

#### Inline Code Documentation

For language-specific guidance on code documentation, including style guides, see [Google's list of language style guides](https://google.github.io/styleguide/) for a variety of languages. 

Additionally, take a look at Google's recommendations on [inline code documentation](https://google.github.io/styleguide/docguide/best_practices.html#documentation-is-the-story-of-your-code) for best practices. 

#### Media

Media, such as such as images, videos, sound files, etc., are an excellent way to explain documentation to a wider audience more easily. Include media in your contributions as often as possible.

When including media into our version-control system, it is recommended to use formats such as:
- Diagrams: [Mermaid](https://mermaid-js.github.io/mermaid/#/) format
- Images: JPEG format
- Videos: H264 MPEG format
- Sounds: MP3 format

### ❓ Questions

Answering questions is an excellent way to learn more about our project, as well as get better known in our project community. 

Here are just a few ways you can help answer questions for our project:
- Answer open questions in our [discussion forum](https://github.com/nasa-jpl/slim/discussions)
- Answer open questions mentioned in our [issue tracking system](https://github.com/nasa-jpl/slim/issues)

When answering questions, keep the following in mind:
- Be polite and friendly. See our [Code of Conduct](CODE_OF_CONDUCT.md) recommendations as you interact with others in the team.
- Repeat the specific question you are answering, followed by your suggestion.
- If suggesting code, repeat the line of code that needs to be altered, followed by your alteration
- Include any post-steps or checks to verify your answer can be reproduced 

### 🎨 Design

Design files can help to guide new features and new areas of expansion for our project. We welcome these kinds of contributions.

Here are just a few ways you can help provide design recommendations for our project:
- Create visual mockups or diagrams to increase usability of our project applications. This can apply to user interfaces, documentation structuring, or even code architecture diagrams.
- Conduct user research to understand user needs better. Save your findings within spreadsheets that the project team / contributors can review.
- Create art, such as logos or icons, to support the user experience for the project

Each of the above can be contributed directly to repository code, and you should use our [development process](#our-development-process) to contribute your additions.

### 🎟️ Meetups

A great way to contribute towards our project goals is to socialize and encourage people to meet and learn more about each other. Consider ideas like:
- Propose workshops or meetups regarding some topic within our project
- Help point project contributors and community members to conferences and publications where they may socialize their unique innovations
- Schedule in-person or virtual happy-hours to help create a more social atmosphere within the project community

For the above ideas, use our [communication channels](#communication-channels) to propose get-togethers.