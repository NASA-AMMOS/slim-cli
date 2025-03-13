import argparse
import subprocess
import git
import json
import logging
import os
import requests
import tempfile
import textwrap
import urllib
import uuid
import sys
from typing import Optional, Dict, Any
from rich.console import Console
from rich.table import Table
from . import VERSION

# Constants
SLIM_REGISTRY_URI = "https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/data/slim-registry.json"
SUPPORTED_MODELS = {
    "openai": ["gpt-3.5-turbo", "gpt-4o"],
    "ollama": ["llama3.3", "mistral", "codellama"],
    "azure" : ["gpt-3.5-turbo", "gpt-4o"],
    # Add more models as needed
}
GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS = 'slim-best-practices'
GIT_DEFAULT_REMOTE_NAME = 'origin'
GIT_CUSTOM_REMOTE_NAME = 'slim-custom'
GIT_DEFAULT_COMMIT_MESSAGE = 'SLIM-CLI Best Practices Bot Commit',

def setup_logging(logging_level):
    logging.basicConfig(level=logging_level, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_best_practices(url):
    response = requests.get(url)
    response.raise_for_status()
    practices = response.json()

    return practices

# THIS FUNCTION IS TEMPORARY FOR TESTING ONLY
def fetch_best_practices_from_file(file_path):
    with open(file_path, 'r') as file:
        practices = json.load(file)
    return practices

def list_practices(args):
    logging.debug("Listing all best practices...")
    practices = fetch_best_practices(SLIM_REGISTRY_URI)
    #practices = fetch_best_practices_from_file("slim-registry.json")

    if not practices:
        print("No practices found or failed to fetch practices.")
        return

    asset_mapping = create_slim_registry_dictionary(practices)

    console = Console()
    table = Table(show_header=True, header_style="bold magenta", show_lines=True)
    headers = ["ID", "Title", "Description", "Asset"]
    for header in headers:
        table.add_column(header)

    for asset_id, info in asset_mapping.items():
        table.add_row(asset_id, textwrap.fill(info['title'], width=30), textwrap.fill(info['description'], width=50), textwrap.fill(info['asset_name'], width=20))

    console.print(table)

def create_slim_registry_dictionary(practices):
    asset_mapping = {}
    i = 1  # Start the manual index for practices with assets
    for practice in practices:
        title = practice.get('title', 'N/A')
        description = practice.get('description', 'N/A')
        
        if 'assets' in practice and practice['assets']:
            for j, asset in enumerate(practice['assets'], start=1):
                asset_id = f"SLIM-{i}.{j}"
                asset_name = asset.get('name', 'N/A')
                asset_uri = asset.get('uri', '')
                asset_mapping[asset_id] = {
                    'title': title, 
                    'description': description, 
                    'asset_name': asset_name,
                    'asset_uri': asset_uri
                }
        else:
            asset_mapping[f"SLIM-{i}"] = {'title': title, 'description': description, 'asset_name': 'None'}
        i += 1
    return asset_mapping

def get_ai_model_pairs(supported_models):
    # return a list of "key/value" pairs
    return [f"{key}/{model}" for key, models in supported_models.items() for model in models]

def is_open_source(repo_url):
    """
    Check if the repository is open-source by inspecting its license type.
    Returns True if the repository is open-source, False otherwise.
    """
    try:
        # Extract owner and repo name from the URL
        owner_repo = repo_url.rstrip('/').split('/')[-2:]
        owner, repo = owner_repo[0], owner_repo[1]

        # Use the GitHub API to fetch the repository license
        api_url = f"https://api.github.com/repos/{owner}/{repo}/license"
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"token {os.getenv('GITHUB_API_TOKEN')}"  # Optional: Use GitHub token for higher rate limits
        }
        response = requests.get(api_url, headers=headers)
        if response.status_code == 200:
            license_data = response.json()
            license_name = license_data.get('license', {}).get('spdx_id', '')
            open_source_licenses = [
                "MIT", "Apache-2.0", "GPL-3.0", "GPL-2.0", "BSD-3-Clause", 
                "BSD-2-Clause", "LGPL-3.0", "MPL-2.0", "CDDL-1.0", "EPL-2.0"
            ]
            return license_name in open_source_licenses
        else:
            print(f"Failed to fetch license information. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"An error occurred while checking the license: {e}")
        return False
        
def use_ai(best_practice_id: str, repo_path: str, template_path: str, model: str = "openai/gpt-4o") -> Optional[str]:
    """
    Uses AI to generate or modify content based on the provided best practice and repository.
    
    :param best_practice_id: ID of the best practice to apply.
    :param repo_path: Path to the cloned repository.
    :param template_path: Path to the template file for the best practice.
    :param model: Name of the AI model to use (example: "openai/gpt-4o", "ollama/llama3.1:70b").
    :return: Generated or modified content as a string, or None if an error occurs.
    """
    # Check if the model provider is Azure or OpenAI
    model_provider, model_name = model.split('/')

    # checking open source is in progress... 
    #if model_provider in ["openai", "azure"] and not is_open_source(repo_path):
    #    logging.error(f"Azure and OpenAI features are disabled for non-open-source repositories.")
    #    return None

    
    logging.debug(f"Using AI to apply best practice ID: {best_practice_id} in repository {repo_path}")
    
    # Fetch best practice information
    practices = fetch_best_practices(SLIM_REGISTRY_URI)
    asset_mapping = create_slim_registry_dictionary(practices)
    best_practice = asset_mapping.get(best_practice_id)
    
    if not best_practice:
        logging.error(f"Best practice ID {best_practice_id} not found.")
        return None
    
    # Read the template content
    template_content = read_file_content(template_path)
    if not template_content:
        return None
    
    # Fetch the code base for SLIM-3.1 readme (limited to specific file types)
    if best_practice_id == 'SLIM-1.1': #governance 
        reference = fetch_readme(repo_path)
        # Construct the prompt for the AI
        prompt = construct_prompt(template_content, best_practice, reference)   
    elif best_practice_id == 'SLIM-3.1': #readme
        reference = fetch_code_base(repo_path)
        # Construct the prompt for the AI
        prompt = construct_prompt(template_content, best_practice, reference)
    elif best_practice_id == 'SLIM-13.1': #readme
        reference1 = fetch_readme(repo_path)
        reference2 = "\n".join(fetch_relative_file_paths(repo_path))
        reference = "EXISTING README:\n" + reference1 + "\n\n" + "EXISTING DIRECTORY LISTING: " + reference2
        # Construct the prompt for the AI
        prompt = construct_prompt(template_content, best_practice, reference, "Within the provided testing template, only fill out the sections that plausibly have existing tests to fill out based on the directory listing provided (do not make up tests that do not exist).")
    else:
        reference = fetch_readme(repo_path)
        # Construct the prompt for the AI
        prompt = construct_prompt(template_content, best_practice, reference)
    if not reference:
        return None
    
        
    # Generate the content using the specified model
    new_content = generate_content(prompt, model)

    return new_content

def fetch_readme(repo_path: str) -> Optional[str]:
    readme_files = ['README.md', 'README.txt', 'README.rst']  # Add more variations as needed
    
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file in readme_files:
                file_path = os.path.join(root, file)
                return read_file_content(file_path)
    
    return None


def fetch_code_base(repo_path: str) -> Optional[str]:
    code_base = ""
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(('.py', '.js', '.java', '.cpp', '.cs')):  # Add more extensions as needed
                file_path = os.path.join(root, file)
                code_base += read_file_content(file_path) or ""
    return code_base if code_base else None

def fetch_relative_file_paths(directory):
    relative_paths = []
    for root, _, files in os.walk(directory):
        for file in files:
            # Get the relative file path and add it to the list
            relative_path = os.path.relpath(os.path.join(root, file), directory)
            relative_paths.append(relative_path)
    return relative_paths

def construct_prompt(template_content: str, best_practice: Dict[str, Any], reference: str, comment: str = "") -> str:
    return (
        f"Fill out all blanks in the template below that start with INSERT. Use the provided context information to fill the blanks. Return the template with filled out values. {comment}\n\n"
        f"TEMPLATE:\n{template_content}\n\n"
        f"CONTEXT INFORMATION:\n{reference}\n\n"
    )

def generate_content(prompt: str, model: str) -> Optional[str]:
    model_provider, model_name = model.split('/')
    
    if model_provider == "openai":
        collected_response = []
        for token in generate_with_openai(prompt, model_name):
            if token is not None:
                #print(token, end='', flush=True)
                collected_response.append(token)
            else:
                print("\nError occurred during generation.")
        print()  # Print a newline at the end
        return ''.join(collected_response)
    elif model_provider == "azure":
        #collected_response = []
        #for token in generate_with_azure(prompt, model_name):
        #    if token is not None:
        #        print(token, end='', flush=True)
        #        collected_response.append(token)
        #    else:
        #        print("\nError occurred during generation.")
        #print()  # Print a newline at the end
        return generate_with_azure(prompt, model_name)
    elif model_provider == "ollama":
        return generate_with_ollama(prompt, model_name)
    else:
        logging.error(f"Unsupported model provider: {model_provider}")
        return None
    

def read_file_content(file_path: str) -> Optional[str]:
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except IOError as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return None

def generate_with_azure(prompt: str, model_name: str) -> Optional[str]:
    from azure.identity import ClientSecretCredential, get_bearer_token_provider
    from openai import AzureOpenAI
    from dotenv import load_dotenv
    import numpy as np
    
    try:
        load_dotenv()

        APIM_SUBSCRIPTION_KEY = os.getenv("APIM_SUBSCRIPTION_KEY")
        default_headers = {}
        if APIM_SUBSCRIPTION_KEY != None:
            # only set this if the APIM API requires a subscription...
            default_headers["Ocp-Apim-Subscription-Key"] = APIM_SUBSCRIPTION_KEY 

        # Set up authority and credentials for Azure authentication
        credential = ClientSecretCredential(
            tenant_id=os.getenv("AZURE_TENANT_ID"),
            client_id=os.getenv("AZURE_CLIENT_ID"),
            client_secret=os.getenv("AZURE_CLIENT_SECRET"),
            authority="https://login.microsoftonline.com",
        )

        token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")

        client = AzureOpenAI(
            # azure_ad_token=access_token.token,
            azure_ad_token_provider=token_provider,
            api_version=os.getenv("API_VERSION"),
            azure_endpoint=os.getenv("API_ENDPOINT"),
            default_headers=default_headers,
        )

        completion = client.chat.completions.create(
            messages = [
                {
                    "role": "system",
                    "content": "As a SLIM Best Practice User, your role is to understand, apply, and implement the best practices for Software Lifecycle Improvement and Modernization (SLIM) within your software projects. You should aim to optimize your software development processes, enhance the quality of your software products, and ensure continuous improvement across all stages of the software lifecycle.",
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model=model_name
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"An error occurred running on Azure model: {str(e)}")
        return None


def generate_with_openai(prompt: str, model_name: str) -> Optional[str]:
    from openai import OpenAI
    from dotenv import load_dotenv
    load_dotenv()
    try:    
        client = OpenAI(api_key = os.getenv('OPENAI_API_KEY'))
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            stream=True
        )
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    except Exception as e:
        print(f"An error occurred running OpenAI model: {e}")
        yield None

def generate_with_ollama(prompt: str, model_name: str) -> Optional[str]:
    import ollama

    try:
        response = ollama.chat(model=model_name, messages=[
        {
            'role': 'user',
            'content': prompt,
        },
        ])
        #print(response['message']['content'])
        return (response['message']['content'])
    except Exception as e:
        logging.error(f"Error running Ollama model: {e}")
        return None

    #try:
    #    response = subprocess.run(['ollama', 'run', model_name, prompt], capture_output=True, text=True, check=True)
    #    return response.stdout.strip()
    #except subprocess.CalledProcessError as e:
    #    logging.error(f"Error running Ollama model: {e}")
    #    return None

def download_and_place_file(repo, url, filename, target_relative_path_in_repo=''):
    # Create the full path where the file will be saved. By default write to root.
    target_directory = os.path.join(repo.working_tree_dir, target_relative_path_in_repo)
    file_path = os.path.join(target_directory, filename)

    # Ensure that the target directory exists, create if not
    os.makedirs(target_directory, exist_ok=True)

    # Fetch the file from the URL
    response = requests.get(url)
    if response.status_code == 200:
        # Ensure the parent directories exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Write the content to the file in the repository
        with open(file_path, 'wb') as file:
            file.write(response.content)
        logging.debug(f"File {filename} downloaded and placed at {file_path}.")
    else:
        logging.error(f"Failed to download the file. HTTP status code: {response.status_code}")
        file_path = None
    
    return file_path

def generate_git_branch_name(best_practice_ids):
    # Use shared branch name if multiple best_practice_ids else use default branch name

    if len(best_practice_ids) > 1:
        return GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS
    elif len(best_practice_ids) == 1:
        return best_practice_ids[0]
    else:
        return None
    
def repo_file_to_list(file_path):
    # open the file at the given path
    with open(file_path, 'r') as file:
        # read all lines and strip any leading/trailing whitespace
        repos = [line.strip() for line in file.readlines()]
    # return the list of lines
    return repos


def apply_best_practices(best_practice_ids, use_ai_flag, model, repo_urls = None, existing_repo_dir = None, target_dir_to_clone_to = None):
    
    if existing_repo_dir:
        branch = GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS if len(best_practice_ids) > 0 else best_practice_ids[0]
        for best_practice_id in best_practice_ids:
            apply_best_practice(
                best_practice_id=best_practice_id, 
                use_ai_flag=use_ai_flag, 
                model=model,
                existing_repo_dir=existing_repo_dir,
                branch=branch)
    else:
        for repo_url in repo_urls:
            if len(best_practice_ids) > 1:
                if repo_url:
                    logging.debug(f"Using repository URL {repo_url} for group of best_practice_ids {best_practice_ids}")

                    parsed_url = urllib.parse.urlparse(repo_url)
                    repo_name = os.path.basename(parsed_url.path)
                    repo_name = repo_name[:-4] if repo_name.endswith('.git') else repo_name  # Remove '.git' from repo name if present
                    if target_dir_to_clone_to: # If target_dir_to_clone_to is specified, append repo name to target_dir_to_clone_to
                        #repo_dir = os.path.join(target_dir_to_clone_to, repo_name)
                        #os.makedirs(repo_dir, exist_ok=True) # Make the dir only if it doesn't exist
                        #logging.debug(f"Set clone directory for group of best_practice_ids to {repo_dir}")

                        for best_practice_id in best_practice_ids:
                            apply_best_practice(
                                best_practice_id=best_practice_id, 
                                use_ai_flag=use_ai_flag, 
                                model=model,
                                repo_url=repo_url, 
                                target_dir_to_clone_to=target_dir_to_clone_to, 
                                branch=GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS)
                    else: # else make a temporary directory
                        repo_dir = tempfile.mkdtemp(prefix=f"{repo_name}_" + str(uuid.uuid4()) + '_')
                        logging.debug(f"Generating temporary clone directory for group of best_practice_ids at {repo_dir}")
                        for best_practice_id in best_practice_ids:
                            apply_best_practice(
                                best_practice_id=best_practice_id, 
                                use_ai_flag=use_ai_flag, 
                                model=model,
                                repo_url=repo_url, 
                                target_dir_to_clone_to=repo_dir, 
                                branch=GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS)
                else:
                    for best_practice_id in best_practice_ids:
                        apply_best_practice(best_practice_id=best_practice_id, use_ai_flag=use_ai_flag, model=model, existing_repo_dir=existing_repo_dir)
            elif len(best_practice_ids) == 1:
                apply_best_practice(
                    best_practice_id=best_practice_ids[0], 
                    use_ai_flag=use_ai_flag, 
                    model=model,
                    repo_url=repo_url, 
                    existing_repo_dir=existing_repo_dir, 
                    target_dir_to_clone_to=target_dir_to_clone_to)
            else:
                logging.error(f"No best practice IDs specified.")

def apply_best_practice(best_practice_id, use_ai_flag, model, repo_url = None, existing_repo_dir = None, target_dir_to_clone_to = None, branch = None):
    applied_file_path = None # default return value is invalid applied best practice

    logging.debug(f"AI features {'enabled' if use_ai_flag else 'disabled'} for applying best practices")
    logging.debug(f"Applying best practice ID: {best_practice_id} to repository: {repo_url}")

    # Fetch best practices information
    practices = fetch_best_practices(SLIM_REGISTRY_URI)
    if not practices:
        print("No practices found or failed to fetch practices.")
        return

    asset_mapping = create_slim_registry_dictionary(practices)

    if best_practice_id in asset_mapping:
        uri = asset_mapping[best_practice_id].get('asset_uri')

        try:
            # Load the existing repository
            if repo_url:
                logging.debug(f"Using repository URL {repo_url}. URI: {uri}")

                parsed_url = urllib.parse.urlparse(repo_url)
                repo_name = os.path.basename(parsed_url.path)
                repo_name = repo_name[:-4] if repo_name.endswith('.git') else repo_name  # Remove '.git' from repo name if present
                if target_dir_to_clone_to: # If target_dir_to_clone_to is specified, append repo name to target_dir_to_clone_to
                    target_dir_to_clone_to = os.path.join(target_dir_to_clone_to, repo_name)
                    logging.debug(f"Set clone directory to {target_dir_to_clone_to}")
                else: # else make a temporary directory
                    target_dir_to_clone_to = tempfile.mkdtemp(prefix=f"{repo_name}_" + str(uuid.uuid4()) + '_')
                    logging.debug(f"Generating temporary clone directory at {target_dir_to_clone_to}")
            elif existing_repo_dir:
                target_dir_to_clone_to = existing_repo_dir
                logging.debug(f"Using existing repository directory {existing_repo_dir}")
            else:
                logging.error("No repository information provided.")
                return None

            try:
                git_repo = git.Repo(target_dir_to_clone_to)
                logging.debug(f"Repository folder ({target_dir_to_clone_to}) exists already. Using existing directory.")
            except Exception as e:
                logging.debug(f"Repository folder ({target_dir_to_clone_to}) not a git repository yet already. Cloning repo {repo_url} contents into folder.")
                git_repo = git.Repo.clone_from(repo_url, target_dir_to_clone_to)

            # Change directory to the cloned repository
            os.chdir(target_dir_to_clone_to)

            if git_repo.head.is_valid():
                if best_practice_id in git_repo.heads:
                    # Check out the existing branch
                    git_branch = git_repo.heads[best_practice_id] if not branch else git_repo.create_head(branch)
                    git_branch.checkout()
                    logging.warning(f"Git branch '{git_branch.name}' already exists in clone_to_dir '{target_dir_to_clone_to}'. Checking out existing branch.")
                else:
                    # Create and check out the new branch
                    git_branch = git_repo.create_head(best_practice_id) if not branch else git_repo.create_head(branch)
                    git_branch.checkout()
                    logging.debug(f"Branch '{git_branch.name}' created and checked out successfully.")
            else:
                # Create an initial commit
                with open(os.path.join(git_repo.working_dir, 'README.md'), 'w') as file:
                    file.write("Initial commit")
                git_repo.index.add(['README.md'])  # Add files to the index
                git_repo.index.commit('Initial commit')  # Commit the changes
                logging.debug("Initial commit created in the empty repository.")

                # Empty repo, so only now create and check out the fresh branch
                git_branch = git_repo.create_head(best_practice_id) if not branch else git_repo.create_head(branch)
                git_branch.checkout()
                logging.debug(f"Empty repository. Creating new branch '{git_branch.name}' and checked it out successfully.")

        except git.exc.InvalidGitRepositoryError:
            logging.error(f"Error: {target_dir_to_clone_to} is not a valid Git repository.")
            return None
        except git.exc.GitCommandError as e:
            logging.error(f"Git command error: {e}")
            return None
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return None

        # Process best practice by ID
        if best_practice_id == 'SLIM-1.1':
            applied_file_path = download_and_place_file(git_repo, uri, 'GOVERNANCE-TEMPLATE-SMALL-TEAMS.md')
            if use_ai_flag and model:
                #logging.warning(f"AI apply features unsupported for best practice {best_practice_id} currently")

                # Custom AI processing code to go here using and modifying applied_file_path content

                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path, model) #template file path 
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")
        elif best_practice_id == 'SLIM-1.2':
            applied_file_path = download_and_place_file(git_repo, uri, 'GOVERNANCE.md')
            if use_ai_flag and model:
                #logging.warning(f"AI apply features unsupported for best practice {best_practice_id} currently")

                # Custom AI processing code to go here using and modifying applied_file_path content
                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path, model)
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")
        elif best_practice_id == 'SLIM-3.1':
            applied_file_path = download_and_place_file(git_repo, uri, 'README.md')
            if use_ai_flag and model:
                #logging.warning(f"AI apply features unsupported for best practice {best_practice_id} currently")

                # Custom AI processing code to go here using and modifying applied_file_path content
                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path, model)
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")
        elif best_practice_id == 'SLIM-4.1':
            applied_file_path = download_and_place_file(git_repo, uri, '.github/ISSUE_TEMPLATE/bug_report.md')
            if use_ai_flag and model:
                #logging.warning(f"AI apply features unsupported for best practice {best_practice_id} currently")

                # Custom AI processing code to go here using and modifying applied_file_path content
                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path, model)
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")    
        elif best_practice_id == 'SLIM-4.2':
            applied_file_path = download_and_place_file(git_repo, uri, '.github/ISSUE_TEMPLATE/bug_report.yml')
            if use_ai_flag and model:
                #logging.warning(f"AI apply features unsupported for best practice {best_practice_id} currently")

                # Custom AI processing code to go here using and modifying applied_file_path content
                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path, model)
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")   
        elif best_practice_id == 'SLIM-4.3':
            applied_file_path = download_and_place_file(git_repo, uri, '.github/ISSUE_TEMPLATE/new_feature.md')
            if use_ai_flag and model:
                #logging.warning(f"AI apply features unsupported for best practice {best_practice_id} currently")

                # Custom AI processing code to go here using and modifying applied_file_path content
                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path, model)
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")   
        elif best_practice_id == 'SLIM-4.4':
            applied_file_path = download_and_place_file(git_repo, uri, '.github/ISSUE_TEMPLATE/new_feature.yml')
            if use_ai_flag and model:
                #logging.warning(f"AI apply features unsupported for best practice {best_practice_id} currently")

                # Custom AI processing code to go here using and modifying applied_file_path content
                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path, model)
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")  
        elif best_practice_id == 'SLIM-5.1':
            applied_file_path = download_and_place_file(git_repo, uri, 'CHANGELOG.md')
            if use_ai_flag and model:
                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path, model)
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")  
        elif best_practice_id == 'SLIM-7.1':
            applied_file_path = download_and_place_file(git_repo, uri, '.github/PULL_REQUEST_TEMPLATE.md')
            if use_ai_flag and model:
                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path, model)
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")  
        elif best_practice_id == 'SLIM-8.1':
            applied_file_path = download_and_place_file(git_repo, uri, 'CODE_OF_CONDUCT.md')
            if use_ai_flag and model:
                #logging.warning(f"AI apply features unsupported for best practice {best_practice_id} currently")

                # Custom AI processing code to go here using and modifying applied_file_path content
                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path, model)
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")
        elif best_practice_id == 'SLIM-9.1':
            applied_file_path = download_and_place_file(git_repo, uri, 'CONTRIBUTING.md')
            if use_ai_flag and model:
                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path, model)
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")  
        elif best_practice_id == 'SLIM-13.1':
            applied_file_path = download_and_place_file(git_repo, uri, 'TESTING.md')
            if use_ai_flag and model:
                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path, model)
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")
        else:
            applied_file_path = None # nothing was modified 
            logging.warning(f"SLIM best practice {best_practice_id} not supported.")
    else:
        logging.warning(f"SLIM best practice {best_practice_id} not supported.")
    
    if applied_file_path:
        logging.info(f"Applied best practice {best_practice_id} to local repo {git_repo.working_tree_dir} and branch '{git_branch.name}'")
        return git_repo # return the modified git repo object
    else:
        logging.error(f"Failed to apply best practice {best_practice_id}")
        return None

def deploy_best_practices(best_practice_ids, repo_dir, remote = None, commit_message = GIT_DEFAULT_COMMIT_MESSAGE):
    # Use shared branch if multiple best_practice_ids else use default branch name
    branch_name = generate_git_branch_name(best_practice_ids)

    for best_practice_id in best_practice_ids:
        deploy_best_practice(
            best_practice_id=best_practice_id, 
            repo_dir=repo_dir, 
            remote=remote, 
            commit_message=commit_message,
            branch=branch_name)

def deploy_best_practice(best_practice_id, repo_dir, remote=None, commit_message='Default commit message', branch=None):
    branch_name = branch if branch else best_practice_id
    
    logging.debug(f"Deploying branch: {branch_name}")
    
    try:
        # Assuming repo_dir points to a local git repository directory
        repo = git.Repo(repo_dir)

        # Checkout the branch
        repo.git.checkout(branch_name)
        logging.debug(f"Checked out to branch {branch_name}")

        if remote:
            # Use the current GitHub user's default organization as the prefix for the remote
            remote_url = f"{remote}/{repo.working_tree_dir.split('/')[-1]}"
            remote_name = GIT_CUSTOM_REMOTE_NAME
            remote_exists = any(repo_remote.url == remote_url for repo_remote in repo.remotes)
            if not remote_exists:
                repo.create_remote(remote_name, remote_url)
            else:
                repo.git.fetch(remote_name)
        else:
            # Default to using the 'origin' remote
            remote_name = GIT_DEFAULT_REMOTE_NAME
            repo.git.fetch(remote_name)

        # Check if the branch exists on the remote
        remote_refs = repo.git.ls_remote('--heads', remote_name, branch_name)
        if remote_refs:
            # Get the last commit on the remote branch
            remote_commit = remote_refs.split()[0]
            # Get the last commit on the local branch
            local_commit = repo.heads[branch_name].commit.hexsha
            
            if remote_commit != local_commit:
                # Pull changes from the remote to make sure the local branch is up-to-date
                repo.git.pull(remote_name, branch_name, '--rebase=false')
                logging.debug(f"Pulled latest changes for branch {branch_name} from remote {remote_name}")
            else:
                logging.debug(f"Local branch {branch_name} is up-to-date with remote {remote_name}. No pull needed.")
        else:
            logging.info(f"Branch {branch_name} does not exist on remote {remote_name}. No pull performed.")

        # Add / Commit changes
        repo.git.add(A=True)  # Adds all untracked files
        logging.debug("Added all changes to git index.")

        repo.git.commit('-m', commit_message)
        logging.debug("Committed changes.")

        # Push changes to the remote
        repo.git.push(remote_name, branch_name)
        logging.debug(f"Pushed changes to remote {remote_name} on branch {branch_name}")
        logging.info(f"Deployed best practice id '{best_practice_id}' to remote '{remote_name}' on branch '{branch_name}'")

        return True
    except git.exc.GitCommandError as e:
        logging.error(f"Unable to deploy best practice id '{best_practice_id}' to remote '{remote_name}' on branch '{branch_name}'")
        logging.error(f"Git command failed: {str(e)}")
        logging.error(f"An error occurred: {str(e)}")
        return False


def apply_and_deploy_best_practices(best_practice_ids, use_ai_flag, model, remote = None, commit_message = GIT_DEFAULT_COMMIT_MESSAGE, repo_urls=None, existing_repo_dir=None, target_dir_to_clone_to=None):
    branch_name = generate_git_branch_name(best_practice_ids)

    for repo_url in repo_urls:
        git_repo = None  # Ensure git_repo is reset for each iteration
        if len(best_practice_ids) > 1:
            if repo_url:
                parsed_url = urllib.parse.urlparse(repo_url)
                repo_name = os.path.basename(parsed_url.path)
                repo_name = repo_name[:-4] if repo_name.endswith('.git') else repo_name  # Remove '.git' from repo name if present
                if target_dir_to_clone_to:
                    for best_practice_id in best_practice_ids:
                        git_repo = apply_best_practice(
                            best_practice_id=best_practice_id, 
                            use_ai_flag=use_ai_flag, 
                            model=model,
                            repo_url=repo_url, 
                            target_dir_to_clone_to=target_dir_to_clone_to, 
                            branch=branch_name)
                    
                    # deploy just the last best practice, which deploys others as well
                    if git_repo:
                        deploy_best_practice(
                            best_practice_id=best_practice_id,
                            repo_dir=git_repo.working_tree_dir,
                            remote=remote,
                            commit_message=commit_message,
                            branch=branch_name)
                    else:
                        logging.error(f"Unable to deploy best practice '{best_practice_id}' because apply failed.")
                else: # else make a temporary directory
                    repo_dir = tempfile.mkdtemp(prefix=f"{repo_name}_" + str(uuid.uuid4()) + '_')
                    logging.debug(f"Generating temporary clone directory for group of best_practice_ids at {repo_dir}")
                    for best_practice_id in best_practice_ids:
                        git_repo = apply_best_practice(
                            best_practice_id=best_practice_id, 
                            use_ai_flag=use_ai_flag, 
                            model=model,
                            repo_url=repo_url, 
                            target_dir_to_clone_to=repo_dir, 
                            branch=branch_name)
                        
                    # deploy just the last best practice, which deploys others as well    
                    if git_repo:
                        deploy_best_practice(
                            best_practice_id=best_practice_id,
                            repo_dir=git_repo.working_tree_dir,
                            remote=remote,
                            commit_message=commit_message,
                            branch=branch_name)
                    else:
                        logging.error(f"Unable to deploy best practice '{best_practice_id}' because apply failed.")
            else:
                for best_practice_id in best_practice_ids:
                    git_repo = apply_best_practice(best_practice_id=best_practice_id, use_ai_flag=use_ai_flag, model=model, existing_repo_dir=existing_repo_dir)
                
                # deploy just the last best practice, which deploys others as well
                if git_repo:
                    deploy_best_practice(
                        best_practice_id=best_practice_id,
                        repo_dir=git_repo.working_tree_dir,
                        remote=remote,
                        commit_message=commit_message,
                        branch=branch_name)
                else:
                    logging.error(f"Unable to deploy best practice '{best_practice_id}' because apply failed.")
        elif len(best_practice_ids) == 1:
            git_repo = apply_best_practice(
                best_practice_id=best_practice_ids[0], 
                use_ai_flag=use_ai_flag, 
                model=model,
                repo_url=repo_url, 
                existing_repo_dir=existing_repo_dir, 
                target_dir_to_clone_to=target_dir_to_clone_to)
            
            # deploy just the last best practice, which deploys others as well
            if git_repo:
                deploy_best_practice(
                    best_practice_id=best_practice_ids[0],
                    repo_dir=git_repo.working_tree_dir,
                    remote=remote,
                    commit_message=commit_message,
                    branch=branch_name)
            else:
                logging.error(f"Unable to deploy best practice '{best_practice_id}' because apply failed.")
        else:
            logging.error(f"No best practice IDs specified.")

def apply_and_deploy_best_practice(best_practice_id, use_ai_flag, model, remote=None, commit_message=GIT_DEFAULT_COMMIT_MESSAGE, repo_url = None, existing_repo_dir = None, target_dir_to_clone_to = None, branch = None):
    logging.debug("AI customization enabled for applying and deploying best practices" if use_ai_flag else "AI customization disabled")
    logging.debug(f"Applying and deploying best practice ID: {best_practice_id}")

    # Apply the best practice
    git_repo = apply_best_practice(best_practice_id=best_practice_id, use_ai_flag=use_ai_flag, model=model, repo_url=repo_url, existing_repo_dir=existing_repo_dir, target_dir_to_clone_to=target_dir_to_clone_to, branch=branch)
    
    # Deploy the best practice if applied successfully 
    if git_repo:
        result = deploy_best_practice(best_practice_id=best_practice_id, repo_dir=git_repo.working_tree_dir, remote=remote, commit_message=commit_message, branch=branch)
        if result:
            logging.info(f"Successfully applied and deployed best practice ID: {best_practice_id}")
            return True
        else:
            logging.error(f"Unable to deploy best practice ID: {best_practice_id}")
            return False
    else:
        logging.error(f"Unable to apply and deploy best practice ID: {best_practice_id}")
        return False

def create_parser():
    parser = argparse.ArgumentParser(description='This tool automates the application of best practices to git repositories.')
    parser.add_argument('--version', action='version', version=VERSION)
    parser.add_argument('-d', '--dry-run', action='store_true', help='Generate a dry-run plan of activities to be performed')
    parser.add_argument(
        '-l', '--logging',
        required=False,
        default='INFO',  # default is a string; we'll convert it to logging.INFO below
        type=lambda s: getattr(logging, s.upper(), None),
        help='Set the logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL'
    )

    subparsers = parser.add_subparsers(dest='command', required=True)

    parser_list = subparsers.add_parser('list', help='Lists all available best practice from the SLIM')
    parser_list.set_defaults(func=list_practices)

    # Parser for applying a best practice
    parser_apply = subparsers.add_parser('apply', help='Applies a best practice, i.e. places a best practice in a git repo in the right spot with appropriate content')
    parser_apply.add_argument('--best-practice-ids', nargs='+', required=True, help='Best practice IDs to apply')
    parser_apply.add_argument('--repo-urls', nargs='+', required=False, help='Repository URLs to apply to. Do not use if --repo-dir specified')
    parser_apply.add_argument('--repo-urls-file', required=False, help='Path to a file containing repository URLs')
    parser_apply.add_argument('--repo-dir', required=False, help='Repository directory location on local machine. Only one repository supported')
    parser_apply.add_argument('--clone-to-dir', required=False, help='Local path to clone repository to. Compatible with --repo-urls')
    parser_apply.add_argument('--use-ai', metavar='MODEL', help=f"Automatically customize the application of the best practice with an AI model. Support for: {get_ai_model_pairs(SUPPORTED_MODELS)}")
    parser_apply.set_defaults(func=lambda args: apply_best_practices(
        best_practice_ids=args.best_practice_ids,
        use_ai_flag=bool(args.use_ai),
        model=args.use_ai if args.use_ai else None, 
        repo_urls=repo_file_to_list(args.repo_urls_file) if args.repo_urls_file else args.repo_urls,
        existing_repo_dir=args.repo_dir,
        target_dir_to_clone_to=args.clone_to_dir
    ))

    # Parser for deploying a best practice
    parser_deploy = subparsers.add_parser('deploy', help='Deploys a best practice, i.e. places the best practice in a git repo, adds, commits, and pushes to the git remote.')
    parser_deploy.add_argument('--best-practice-ids', nargs='+', required=True, help='Best practice IDs to deploy')
    parser_deploy.add_argument('--repo-dir', required=False, help='Repository directory location on local machine')
    parser_deploy.add_argument('--remote', required=False, default=None, help=f"Push to a specified remote. If not specified, pushes to '{GIT_DEFAULT_REMOTE_NAME}. Format should be a GitHub-like URL base. For example `https://github.com/my_github_user`")
    parser_deploy.add_argument('--commit-message', required=False, default=GIT_DEFAULT_COMMIT_MESSAGE, help=f"Commit message to use for the deployment. Default '{GIT_DEFAULT_COMMIT_MESSAGE}")
    parser_deploy.set_defaults(func=lambda args: deploy_best_practices(
        best_practice_ids=args.best_practice_ids,
        repo_dir=args.repo_dir,
        remote=args.remote,
        commit_message=args.commit_message
    ))

    # Parser for applying and deploying a best practice together
    parser_apply_deploy = subparsers.add_parser('apply-deploy', help='Applies and deploys a best practice')
    parser_apply_deploy.add_argument('--best-practice-ids', nargs='+', required=True, help='Best practice IDs to apply')
    parser_apply_deploy.add_argument('--repo-urls', nargs='+', required=False, help='Repository URLs to apply to. Do not use if --repo-dir specified')
    parser_apply_deploy.add_argument('--repo-urls-file', required=False, help='Path to a file containing repository URLs')
    parser_apply_deploy.add_argument('--repo-dir', required=False, help='Repository directory location on local machine. Only one repository supported')
    parser_apply_deploy.add_argument('--clone-to-dir', required=False, help='Local path to clone repository to. Compatible with --repo-urls')
    parser_apply_deploy.add_argument('--use-ai', metavar='MODEL', help='Automatically customize the application of the best practice with the specified AI model. Support for: {get_ai_model_pairs(SUPPORTED_MODELS)}')
    parser_apply_deploy.add_argument('--remote', required=False, default=None, help=f"Push to a specified remote. If not specified, pushes to '{GIT_DEFAULT_REMOTE_NAME}. Format should be a GitHub-like URL base. For example `https://github.com/my_github_user`")
    parser_apply_deploy.add_argument('--commit-message', required=False, default=GIT_DEFAULT_COMMIT_MESSAGE, help=f"Commit message to use for the deployment. Default '{GIT_DEFAULT_COMMIT_MESSAGE}")
    parser_apply_deploy.set_defaults(func=lambda args: apply_and_deploy_best_practices(
        best_practice_ids=args.best_practice_ids,
        use_ai_flag=bool(args.use_ai),
        model=args.use_ai if args.use_ai else None,
        remote=args.remote,
        commit_message=args.commit_message,
        repo_urls=repo_file_to_list(args.repo_urls_file) if args.repo_urls_file else args.repo_urls,
        existing_repo_dir=args.repo_dir,
        target_dir_to_clone_to=args.clone_to_dir
    ))

    # Update Docusaurus documentation generator command with AI support
    parser_docs = subparsers.add_parser('generate-docs', 
        help='Generates Docusaurus documentation from repository content')
    parser_docs.add_argument('--repo-dir', required=True, 
        help='Repository directory location on local machine')
    parser_docs.add_argument('--output-dir', required=True,
        help='Directory where documentation should be generated')
    parser_docs.add_argument('--config', required=False,
        help='Optional YAML configuration file for documentation generation')
    parser_docs.add_argument('--use-ai', metavar='MODEL',
        help=f"Enhance documentation using AI model. Supported models: {get_ai_model_pairs(SUPPORTED_MODELS)}")
    parser_docs.set_defaults(func=handle_generate_docs)

    # Test generation command
    parser_tests = subparsers.add_parser('generate-tests',
        help='Generates unit test files for Python code in the repository')
    parser_tests.add_argument('--repo-dir', required=True,
        help='Repository directory location on local machine')
    parser_tests.add_argument('--output-dir', required=True,
        help='Directory where test files should be generated')
    parser_tests.add_argument('--use-ai', metavar='MODEL',
        help=f"Generate tests using AI model. Supported models: {get_ai_model_pairs(SUPPORTED_MODELS)}")
    parser_tests.set_defaults(func=handle_generate_tests)

    return parser

def handle_generate_docs(args):
    """Handle the generate-docs command."""
    logging.debug(f"Generating documentation from repository: {args.repo_dir}")
    
    # Validate repository directory
    if not os.path.isdir(args.repo_dir):
        logging.error(f"Repository directory does not exist: {args.repo_dir}")
        return False
        
    # Load configuration if provided
    config = None
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            logging.warning(f"Failed to load configuration file: {str(e)}")
    
    # Log AI usage
    if args.use_ai:
        logging.info(f"AI enhancement enabled using model: {args.use_ai}")
    
    # Initialize and run documentation generator
    try:
        from .docgen import DocusaurusGenerator
        generator = DocusaurusGenerator(
            repo_path=args.repo_dir,
            output_dir=args.output_dir,
            config=config,
            use_ai=args.use_ai
        )
        
        if generator.generate():
            logging.info(f"Successfully generated documentation in {args.output_dir}")
            
            # Print next steps
            print("\nDocumentation generated successfully!")
            print("\nNext steps:")
            print("1. Install Docusaurus if you haven't already:")
            print("   npx create-docusaurus@latest my-docs classic")
            print("\n2. Copy the generated files to your Docusaurus docs directory:")
            print(f"   cp -r {args.output_dir}/* my-docs/docs/")
            print("\n3. Start the Docusaurus development server:")
            print("   cd my-docs")
            print("   npm start")
            
            return True
    except Exception as e:
        logging.error(f"Documentation generation failed: {str(e)}")
        return False

def handle_generate_tests(args):
    """Handle the generate-tests command."""
    logging.debug(f"Generating tests for repository: {args.repo_dir}")
    
    # Validate repository directory
    if not os.path.isdir(args.repo_dir):
        logging.error(f"Repository directory does not exist: {args.repo_dir}")
        return False
        
    # Initialize and run test generator
    try:
        from .testgen import TestGenerator

        generator = TestGenerator(
            repo_path=args.repo_dir,
            output_dir=args.output_dir,
            model=args.use_ai
        )
        
        if generator.generate_tests():
            logging.info(f"Successfully generated tests in {args.output_dir}")
            
            # Print next steps
            print("\nTest files generated successfully!")
            print("\nNext steps:")
            print("1. Install pytest if you haven't already:")
            print("   pip install pytest")
            print("\n2. Review the generated tests and modify as needed")
            print("\n3. Run the tests:")
            print("   python -m pytest")
            
            return True
        else:
            logging.error("Test generation failed")
            return False
            
    except Exception as e:
        logging.error(f"Test generation failed: {str(e)}")
        return False

def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.logging is None:
        print("Invalid logging level provided. Choose from DEBUG, INFO, WARNING, ERROR, CRITICAL.")
        sys.exit(1)
    else:
        setup_logging(args.logging)

    if args.dry_run:
        logging.debug("Dry run activated")

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
