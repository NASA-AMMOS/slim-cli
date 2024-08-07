import argparse
import logging
import sys
import requests
import re
import json
import os
import textwrap
import subprocess
from tabulate import tabulate
import tempfile
import uuid
import openai
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from rich.console import Console
from rich.table import Table
import git
import urllib

# Constants
SLIM_REGISTRY_URI = "https://raw.githubusercontent.com/NASA-AMMOS/slim/issue-154/static/data/slim-registry.json"
SUPPORTED_MODELS = {
    "openai": ["gpt-3.5-turbo", "gpt-4o"],
    "ollama": ["llama2", "mistral", "codellama"],
    # Add more models as needed
}
GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS = 'slim-best-practices'
GIT_DEFAULT_REMOTE_NAME = 'origin'
GIT_DEFAULT_COMMIT_MESSAGE = 'SLIM-CLI Best Practices Bot Commit',

def setup_logging():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

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
    # practices = fetch_best_practices_from_file("slim-registry.json")

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


def use_ai(best_practice_id: str, repo_path: str, template_path: str, model: str = "openai/gpt-4o") -> Optional[str]:
    """
    Uses AI to generate or modify content based on the provided best practice and repository.
    
    :param best_practice_id: ID of the best practice to apply.
    :param repo_path: Path to the cloned repository.
    :param template_path: Path to the template file for the best practice.
    :param model: Name of the AI model to use (example: "openai/gpt-4o", "ollama/llama3.1:70b").
    :return: Generated or modified content as a string, or None if an error occurs.
    """
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
    elif best_practice_id == 'SLIM-3.1': #readme
        reference = fetch_code_base(repo_path)
    else:
        reference = fetch_readme(repo_path)
    if not reference:
        return None
    
    # Construct the prompt for the AI
    prompt = construct_prompt(template_content, best_practice, reference)
    print("prompt: ")
    print(prompt)
    # Generate the content using the specified model
    new_content = generate_content(prompt, model)
    print("output: ")
    print(new_content)

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

def construct_prompt(template_content: str, best_practice: Dict[str, Any], readme: str) -> str:
    return (
        f"Fill out all blanks in the template below that start with INSERT. Return the result as Markdown code.\n\n"
        f"Best Practice: {best_practice['title']}\n"
        f"Description: {best_practice['description']}\n\n"
        f"Template and output format:\n{template_content}\n\n"
        f"Use the info:\n{readme}...\n\n"
        f"Show only the updated template output as markdown code."
    )

def generate_content(prompt: str, model: str) -> Optional[str]:
    model_provider, model_name = model.split('/')
    
    if model_provider == "openai":
        return generate_with_openai(prompt, model_name)
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


def generate_with_openai(prompt: str, model_name: str) -> Optional[str]:
    from openai import OpenAI
    client = OpenAI(api_key = os.getenv('OPENAI_API_KEY'))
    #if not openai.api_key:
    #    logging.error("OpenAI API key is missing.")
    #    return None
    
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}]
    )
    return str(response.choices[0].message.content)

def generate_with_ollama(prompt: str, model_name: str) -> Optional[str]:
    try:
        response = subprocess.run(['ollama', 'run', model_name, prompt], capture_output=True, text=True, check=True)
        return response.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running Ollama model: {e}")
        return None

def download_and_place_file(repo, url, filename, target_relative_path_in_repo=''):
    # Create the full path where the file will be saved. By default write to root.
    target_directory = os.path.join(repo.working_tree_dir, target_relative_path_in_repo)
    file_path = os.path.join(target_directory, filename)

    # Ensure that the target directory exists, create if not
    os.makedirs(target_directory, exist_ok=True)

    # Fetch the file from the URL
    response = requests.get(url)
    if response.status_code == 200:
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

def apply_best_practices(best_practice_ids, use_ai_flag, repo_urls = None, existing_repo_dir = None, target_dir_to_clone_to = None):
    
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
                            repo_url=repo_url, 
                            target_dir_to_clone_to=repo_dir, 
                            branch=GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS)
            else:
                for best_practice_id in best_practice_ids:
                    apply_best_practice(best_practice_id=best_practice_id, use_ai_flag=use_ai_flag, existing_repo_dir=existing_repo_dir)
        elif len(best_practice_ids) == 1:
            apply_best_practice(
                best_practice_id=best_practice_ids[0], 
                use_ai_flag=use_ai_flag, 
                repo_url=repo_url, 
                existing_repo_dir=existing_repo_dir, 
                target_dir_to_clone_to=target_dir_to_clone_to)
        else:
            logging.error(f"No best practice IDs specified.")

def apply_best_practice(best_practice_id, use_ai_flag, repo_url = None, existing_repo_dir = None, target_dir_to_clone_to = None, branch = None):
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

            # Check if the branch exists
            print(f"*** GIT REPO: {git_repo}")
            print(f"*** git_repo.head.is_valid(): {git_repo.head.is_valid()}")
            print(f"*** git_repo.heads: {git_repo.heads}")

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
            applied_file_path = download_and_place_file(git_repo, uri, 'GOVERNANCE.md')
            if use_ai_flag:
                #logging.warning(f"AI apply features unsupported for best practice {best_practice_id} currently")

                # Custom AI processing code to go here using and modifying applied_file_path content

                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path) #template file path 
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")
        elif best_practice_id == 'SLIM-1.2':
            applied_file_path = download_and_place_file(git_repo, uri, 'GOVERNANCE.md')
            if use_ai_flag:
                #logging.warning(f"AI apply features unsupported for best practice {best_practice_id} currently")

                # Custom AI processing code to go here using and modifying applied_file_path content
                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path)
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")
        elif best_practice_id == 'SLIM-3.1':
            applied_file_path = download_and_place_file(git_repo, uri, 'README.md')
            if use_ai_flag:
                #logging.warning(f"AI apply features unsupported for best practice {best_practice_id} currently")

                # Custom AI processing code to go here using and modifying applied_file_path content
                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path)
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")
        elif best_practice_id == 'SLIM-4.1':
            applied_file_path = download_and_place_file(git_repo, uri, '.github/ISSUE_TEMPLATE/bug_report.md')
            if use_ai_flag:
                #logging.warning(f"AI apply features unsupported for best practice {best_practice_id} currently")

                # Custom AI processing code to go here using and modifying applied_file_path content
                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path)
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")    
        elif best_practice_id == 'SLIM-4.2':
            applied_file_path = download_and_place_file(git_repo, uri, '.github/ISSUE_TEMPLATE/bug_report.yml')
            if use_ai_flag:
                #logging.warning(f"AI apply features unsupported for best practice {best_practice_id} currently")

                # Custom AI processing code to go here using and modifying applied_file_path content
                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path)
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")   
        elif best_practice_id == 'SLIM-4.3':
            applied_file_path = download_and_place_file(git_repo, uri, '.github/ISSUE_TEMPLATE/new_feature.md')
            if use_ai_flag:
                #logging.warning(f"AI apply features unsupported for best practice {best_practice_id} currently")

                # Custom AI processing code to go here using and modifying applied_file_path content
                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path)
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")   
        elif best_practice_id == 'SLIM-4.4':
            applied_file_path = download_and_place_file(git_repo, uri, '.github/ISSUE_TEMPLATE/new_feature.yml')
            if use_ai_flag:
                #logging.warning(f"AI apply features unsupported for best practice {best_practice_id} currently")

                # Custom AI processing code to go here using and modifying applied_file_path content
                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path)
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")  
        elif best_practice_id == 'SLIM-5.1':
            applied_file_path = download_and_place_file(git_repo, uri, 'CHANGELOG.md')
            if use_ai_flag:
                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path)
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")  
        elif best_practice_id == 'SLIM-7.1':
            applied_file_path = download_and_place_file(git_repo, uri, '.github/PULL_REQUEST_TEMPLATE.md')
            if use_ai_flag:
                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path)
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")  
        elif best_practice_id == 'SLIM-8.1':
            applied_file_path = download_and_place_file(git_repo, uri, 'CODE_OF_CONDUCT.md')
            if use_ai_flag:
                #logging.warning(f"AI apply features unsupported for best practice {best_practice_id} currently")

                # Custom AI processing code to go here using and modifying applied_file_path content
                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path)
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")
        elif best_practice_id == 'SLIM-9.1':
            applied_file_path = download_and_place_file(git_repo, uri, 'CONTRIBUTING.md')
            if use_ai_flag:
                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path)
                if ai_content:
                    with open(applied_file_path, 'w') as f:
                        f.write(ai_content)
                    logging.info(f"Applied AI-generated content to {applied_file_path}")
                else:
                    logging.warning(f"AI generation failed for best practice {best_practice_id}")  
        elif best_practice_id == 'SLIM-13.1':
            applied_file_path = download_and_place_file(git_repo, uri, 'TESTING.md')
            if use_ai_flag:
                ai_content = use_ai(best_practice_id, git_repo.working_tree_dir, applied_file_path)
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

def deploy_best_practices(best_practice_ids, repo_dir, remote_name = GIT_DEFAULT_REMOTE_NAME, commit_message = GIT_DEFAULT_COMMIT_MESSAGE):
    # Use shared branch if multiple best_practice_ids else use default branch name
    branch_name = generate_git_branch_name(best_practice_ids)

    for best_practice_id in best_practice_ids:
        deploy_best_practice(
            best_practice_id=best_practice_id, 
            repo_dir=repo_dir, 
            remote_name=remote_name, 
            commit_message=commit_message,
            branch=branch_name)

def deploy_best_practice(best_practice_id, repo_dir, remote_name='origin', commit_message='Default commit message', branch=None):
    branch_name = branch if branch else best_practice_id
    
    logging.debug(f"Deploying branch: {branch_name}")
    
    try:
        # Assuming repo_dir points to a local git repository directory
        repo = git.Repo(repo_dir)

        # Checkout the branch
        repo.git.checkout(branch_name)
        logging.debug(f"Checked out to branch {branch_name}")

        # Fetch latest info from remote
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


def apply_and_deploy_best_practices(best_practice_ids, use_ai_flag, remote_name = GIT_DEFAULT_REMOTE_NAME, commit_message = GIT_DEFAULT_COMMIT_MESSAGE, repo_urls=None, existing_repo_dir=None, target_dir_to_clone_to=None):
    branch_name = generate_git_branch_name(best_practice_ids)

    for repo_url in repo_urls:
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
                            repo_url=repo_url, 
                            target_dir_to_clone_to=target_dir_to_clone_to, 
                            branch=branch_name)
                    
                    # deploy just the last best practice, which deploys others as well
                    if git_repo:
                        deploy_best_practice(
                            best_practice_id=best_practice_id,
                            repo_dir=git_repo.working_tree_dir,
                            remote_name=remote_name,
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
                            repo_url=repo_url, 
                            target_dir_to_clone_to=repo_dir, 
                            branch=branch_name)
                        
                    # deploy just the last best practice, which deploys others as well    
                    if git_repo:
                        deploy_best_practice(
                            best_practice_id=best_practice_id,
                            repo_dir=git_repo.working_tree_dir,
                            remote_name=remote_name,
                            commit_message=commit_message,
                            branch=branch_name)
                    else:
                        logging.error(f"Unable to deploy best practice '{best_practice_id}' because apply failed.")
            else:
                for best_practice_id in best_practice_ids:
                    git_repo = apply_best_practice(best_practice_id=best_practice_id, use_ai_flag=use_ai_flag, existing_repo_dir=existing_repo_dir)
                
                # deploy just the last best practice, which deploys others as well
                if git_repo:
                    deploy_best_practice(
                        best_practice_id=best_practice_id,
                        repo_dir=git_repo.working_tree_dir,
                        remote_name=remote_name,
                        commit_message=commit_message,
                        branch=branch_name)
                else:
                    logging.error(f"Unable to deploy best practice '{best_practice_id}' because apply failed.")
        elif len(best_practice_ids) == 1:
            git_repo = apply_best_practice(
                best_practice_id=best_practice_ids[0], 
                use_ai_flag=use_ai_flag, 
                repo_url=repo_url, 
                existing_repo_dir=existing_repo_dir, 
                target_dir_to_clone_to=branch_name)
            
            # deploy just the last best practice, which deploys others as well
            if git_repo:
                deploy_best_practice(
                    best_practice_id=best_practice_id,
                    repo_dir=git_repo.working_tree_dir,
                    remote_name=remote_name,
                    commit_message=commit_message,
                    branch=branch_name)
            else:
                logging.error(f"Unable to deploy best practice '{best_practice_id}' because apply failed.")
        else:
            logging.error(f"No best practice IDs specified.")

    # for best_practice_id in best_practice_ids:
    #     result = apply_and_deploy_best_practice(
    #         best_practice_id, 
    #         use_ai_flag, 
    #         remote_name, 
    #         commit_message, 
    #         repo_url, 
    #         existing_repo_dir, 
    #         target_dir_to_clone_to,
    #         branch=branch_name)
    #     if not result:
    #         logging.error(f"Failed to apply and deploy best practice ID: {best_practice_id}")

def apply_and_deploy_best_practice(best_practice_id, use_ai_flag, remote_name=GIT_DEFAULT_REMOTE_NAME, commit_message=GIT_DEFAULT_COMMIT_MESSAGE, repo_url = None, existing_repo_dir = None, target_dir_to_clone_to = None, branch = None):
    logging.debug("AI customization enabled for applying and deploying best practices" if use_ai_flag else "AI customization disabled")
    logging.debug(f"Applying and deploying best practice ID: {best_practice_id}")

    # Apply the best practice
    git_repo = apply_best_practice(best_practice_id=best_practice_id, use_ai_flag=use_ai_flag, repo_url=repo_url, existing_repo_dir=existing_repo_dir, target_dir_to_clone_to=target_dir_to_clone_to, branch=branch)
    
    # Deploy the best practice if applied successfully 
    if git_repo:
        result = deploy_best_practice(best_practice_id=best_practice_id, repo_dir=git_repo.working_tree_dir, remote_name=remote_name, commit_message=commit_message, branch=branch)
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
    parser.add_argument('-d', '--dry-run', action='store_true', help='Generate a dry-run plan of activities to be performed')
    
    subparsers = parser.add_subparsers(dest='command', required=True)

    parser_list = subparsers.add_parser('list', help='Lists all available best practice from the SLIM')
    parser_list.set_defaults(func=list_practices)

    # Parser for applying a best practice
    parser_apply = subparsers.add_parser('apply', help='Applies a best practice, i.e. places a best practice in a git repo in the right spot with appropriate content')
    parser_apply.add_argument('--best-practice-ids', nargs='+', required=True, help='Best practice IDs to apply')
    parser_apply.add_argument('--repo-urls', nargs='+', required=False, help='Repository URLs to apply to. Do not use if --repo-dir specified')
    parser_apply.add_argument('--repo-dir', required=False, help='Repository directory location on local machine. Only one repository supported')
    parser_apply.add_argument('--clone-to_dir', required=False, help='Local path to clone repository to. Compatible with --repo-urls')
    parser_apply.add_argument('--use-ai', action='store_true', help='Automatically customize the application of the best practice')
    parser_apply.set_defaults(func=lambda args: apply_best_practices(
        best_practice_ids=args.best_practice_ids,
        use_ai_flag=args.use_ai,
        repo_urls=args.repo_urls,
        existing_repo_dir=args.repo_dir,
        target_dir_to_clone_to=args.clone_to_dir
    ))

    # Parser for deploying a best practice
    parser_deploy = subparsers.add_parser('deploy', help='Deploys a best practice, i.e. places the best practice in a git repo, adds, commits, and pushes to the git remote.')
    parser_deploy.add_argument('--best-practice-ids', nargs='+', required=True, help='Best practice IDs to deploy')
    parser_deploy.add_argument('--repo-dir', required=False, help='Repository directory location on local machine')
    parser_deploy.add_argument('--remote-name', required=False, default=GIT_DEFAULT_REMOTE_NAME, help=f"Name of the remote to push changes to. Default: '{GIT_DEFAULT_REMOTE_NAME}")
    parser_deploy.add_argument('--commit-message', required=False, default=GIT_DEFAULT_COMMIT_MESSAGE, help=f"Commit message to use for the deployment. Default '{GIT_DEFAULT_COMMIT_MESSAGE}")
    parser_deploy.set_defaults(func=lambda args: deploy_best_practices(
        best_practice_ids=args.best_practice_ids,
        repo_dir=args.repo_dir,
        remote_name=args.remote_name,
        commit_message=args.commit_message
    ))

    # Parser for applying and deploying a best practice together
    parser_apply_deploy = subparsers.add_parser('apply-deploy', help='Applies and deploys a best practice')
    parser_apply_deploy.add_argument('--best-practice-ids', nargs='+', required=True, help='Best practice IDs to apply')
    parser_apply_deploy.add_argument('--repo-urls', nargs='+', required=False, help='Repository URLs to apply to. Do not use if --repo-dir specified')
    parser_apply_deploy.add_argument('--repo-dir', required=False, help='Repository directory location on local machine. Only one repository supported')
    parser_apply_deploy.add_argument('--clone-to-dir', required=False, help='Local path to clone repository to. Compatible with --repo-urls')
    parser_apply_deploy.add_argument('--use-ai', action='store_true', help='Automatically customize the application of the best practice')
    parser_apply_deploy.add_argument('--remote-name', required=False, default=GIT_DEFAULT_REMOTE_NAME, help=f"Name of the remote to push changes to. Default: '{GIT_DEFAULT_REMOTE_NAME}")
    parser_apply_deploy.add_argument('--commit-message', required=False, default=GIT_DEFAULT_COMMIT_MESSAGE, help=f"Commit message to use for the deployment. Default '{GIT_DEFAULT_COMMIT_MESSAGE}")
    parser_apply_deploy.set_defaults(func=lambda args: apply_and_deploy_best_practices(
        best_practice_ids=args.best_practice_ids,
        use_ai_flag=args.use_ai,
        remote_name=args.remote_name,
        commit_message=args.commit_message,
        repo_urls=args.repo_urls,
        existing_repo_dir=args.repo_dir,
        target_dir_to_clone_to=args.clone_to_dir
    ))
    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()

    setup_logging()

    if args.dry_run:
        logging.debug("Dry run activated")

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
