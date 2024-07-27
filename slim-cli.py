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

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    # practices = fetch_best_practices(SLIM_REGISTRY_URI)
    practices = fetch_best_practices_from_file("slim-registry.json")

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


def use_ai(template: str, repo: str, best_practice_id: str, model: str = "gpt-3.5-turbo") -> Optional[str]:
    """
    Uses AI to generate a new document based on the provided template and best practices from a code repository.
    
    :param template: Path to the template document (e.g., testing.md or governance.md).
    :param repo: URL of the target repository.
    :param best_practice_id: ID of the best practice to apply.
    :param model: Name of the AI model to use (default: "gpt-3.5-turbo").
    :return: Generated document as a string, or None if an error occurs.
    """
    
    # Load environment variables and set up logging
    load_dotenv()
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    
    logger.debug(f"Using AI to generate document for best practice ID: {best_practice_id} in repository {repo}")
    
    # Fetch best practices information
    best_practice = fetch_best_practice(best_practice_id)
    if not best_practice:
        return None
    
    # Read the template content
    template_content = read_file_content(template)
    if not template_content:
        return None
    
    # Clone the repository and fetch the code base
    code_base = clone_repo_and_fetch_code(repo)
    if not code_base:
        return None
    
    # Construct the prompt for the AI
    prompt = construct_prompt(template_content, best_practice, code_base)
    
    # Generate the document using the specified model
    new_document = generate_document(prompt, model)
    
    return new_document

def fetch_best_practice(best_practice_id: str) -> Optional[Dict[str, Any]]:
    try:
        response = requests.get(SLIM_REGISTRY_URI)
        response.raise_for_status()
        practices = response.json()
        best_practice = next((p for p in practices if p['id'] == best_practice_id), None)
        if not best_practice:
            logging.error(f"Best practice ID {best_practice_id} not found.")
            return None
        return best_practice
    except requests.RequestException as e:
        logging.error(f"Error fetching best practices: {e}")
        return None

def read_file_content(file_path: str) -> Optional[str]:
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except IOError as e:
        logging.error(f"Error reading file {file_path}: {e}")
        return None

def clone_repo_and_fetch_code(repo: str) -> Optional[str]:
    tmp_dir = tempfile.mkdtemp(prefix='repo_clone_' + str(uuid.uuid4()) + '_')
    repo_list_file = os.path.join(tmp_dir, 'repo_list.txt')
    
    with open(repo_list_file, 'w') as f:
        f.write(f"{repo}\n")
    
    repo_code_path = os.path.join(tmp_dir, 'cloned_repos')
    try:
        subprocess.run(['multi-gitter', 'clone', '--input-file', repo_list_file, '--output-directory', repo_code_path], check=True)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error cloning repository: {e}")
        return None
    
    cloned_repo_path = os.path.join(repo_code_path, os.path.basename(repo))
    
    code_base = ""
    for root, _, files in os.walk(cloned_repo_path):
        for file in files:
            if file.endswith(('.py', '.js', '.java', '.cpp', '.cs')):  # Add more extensions as needed
                file_path = os.path.join(root, file)
                code_base += read_file_content(file_path) or ""
    
    return code_base

def construct_prompt(template_content: str, best_practice: Dict[str, Any], code_base: str) -> str:
    return (
        f"You are an AI assistant. Your task is to generate a new document based on the provided template and best practices.\n\n"
        f"Template:\n{template_content}\n\n"
        f"Best Practice ({best_practice['id']}):\n{best_practice}\n\n"
        f"Code Base:\n{code_base}\n\n"
        f"Refer to the code base, based on best practice and template, generate a document."
    )

def generate_document(prompt: str, model: str) -> Optional[str]:
    model_provider, model_name = model.split('/')
    
    if model_provider == "openai":
        return generate_with_openai(prompt, model_name)
    elif model_provider == "ollama":
        return generate_with_ollama(prompt, model_name)
    else:
        logging.error(f"Unsupported model provider: {model_provider}")
        return None

def generate_with_openai(prompt: str, model_name: str) -> Optional[str]:
    openai.api_key = os.getenv('OPENAI_API_KEY')
    if not openai.api_key:
        logging.error("OpenAI API key is missing.")
        return None
    
    try:
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500
        )
        return response.choices[0].message.content.strip()
    except openai.error.OpenAIError as e:
        logging.error(f"Error calling OpenAI API: {e}")
        return None

def generate_with_ollama(prompt: str, model_name: str) -> Optional[str]:
    try:
        response = subprocess.run(['ollama', 'run', model_name, prompt], capture_output=True, text=True, check=True)
        return response.stdout.strip()
    except subprocess.CalledProcessError as e:
        logging.error(f"Error running Ollama model: {e}")
        return None

# Example usage
'''
if __name__ == "__main__":
    template = "path/to/template.md"
    repo = "https://github.com/your-username/your-repo"
    best_practice_id = "SLIM-001.1"
    model = "openai/gpt-3.5-turbo"  # or "ollama/llama2"
    new_document = use_ai(template, repo, best_practice_id, model)
    if new_document:
        print(new_document)
    else:
        print("Failed to generate document.")
'''

def download_and_place_file(repo, url, filename, relative_path=''):
    # Create the full path where the file will be saved
    target_directory = os.path.join(repo.working_tree_dir, relative_path)
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



def apply_best_practice(args):
    best_practice_id = args.best_practice_id
    use_ai = args.use_ai
    repo_url = args.repo_url if hasattr(args, 'repo_url') else None
    repo_dir = args.repo_dir if hasattr(args, 'repo_dir') else None
    clone_to_dir = args.clone_to_dir if hasattr(args, 'clone_to_dir') else None
    applied_file_path = None # default return value is invalid applied best practice

    logging.debug(f"AI features {'enabled' if use_ai else 'disabled'} for applying best practices")
    logging.debug(f"Applying best practice ID: {best_practice_id} to repository {repo_url}")

    # Fetch best practices information
    practices = fetch_best_practices_from_file("slim-registry.json")
    if not practices:
        print("No practices found or failed to fetch practices.")
        return

    asset_mapping = create_slim_registry_dictionary(practices)

    if best_practice_id in asset_mapping:
        uri = asset_mapping[best_practice_id].get('asset_uri')
        logging.debug(f"Applying best practice {best_practice_id} to repository {repo_url}. URI: {uri}")

        try:
            parsed_url = urllib.parse.urlparse(repo_url)
            repo_name = os.path.basename(parsed_url.path)
            repo_name = repo_name[:-4] if repo_name.endswith('.git') else repo_name  # Remove '.git' from repo name if present
            if clone_to_dir: # If clone_to_dir is specified, append repo name to clone_to_dir
                clone_to_dir = os.path.join(clone_to_dir, repo_name)
                logging.debug(f"Set clone directory to {clone_to_dir}")
            else: # else make a temporary directory
                clone_to_dir = tempfile.mkdtemp(prefix=f"{repo_name}_" + str(uuid.uuid4()) + '_')

            # Load the existing repository
            if repo_url:
                logging.debug(f"Cloning repository {repo_url} into {clone_to_dir}")

                # If clone_to_dir is a valid existing repo folder, use it, otherwise clone the repo into the folder
                try:
                    git_repo = git.Repo(clone_to_dir)
                    logging.warning(f"Repository folder ({clone_to_dir}) exists already. Using existing directory.")
                except git.exc.InvalidGitRepositoryError:
                    logging.debug(f"Repository folder ({clone_to_dir}) not a git repository yet already. Cloning repo {repo_url} contents into folder.")
                    git_repo = git.Repo.clone_from(repo_url, clone_to_dir)
                    
            elif repo_dir:
                clone_to_dir = repo_dir
                logging.debug(f"Using existing repository directory {repo_dir}")
            else:
                logging.error("No repository information provided.")
                return None

            # Change directory to the cloned repository
            os.chdir(clone_to_dir)

            # Check if the branch exists
            if best_practice_id in git_repo.heads:
                # Check out the existing branch
                branch = git_repo.heads[best_practice_id]
                branch.checkout()
                logging.warning(f"Git branch '{best_practice_id}' already exists in clone_to_dir '{clone_to_dir}'. Checking out existing branch.")
            else:
                # Create and check out the new branch
                new_branch = git_repo.create_head(best_practice_id)
                new_branch.checkout()
                logging.debug(f"Branch '{best_practice_id}' created and checked out successfully.")

        except git.exc.InvalidGitRepositoryError:
            logging.error(f"Error: {clone_to_dir} is not a valid Git repository.")
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
            if use_ai:
                logging.warning(f"AI apply features unsupported for best practice {best_practice_id} currently")

                # Custom AI processing code to go here using and modifying applied_file_path content
        elif best_practice_id == 'SLIM-1.2':
            applied_file_path = download_and_place_file(git_repo, uri, 'GOVERNANCE.md')
            if use_ai:
                logging.warning(f"AI apply features unsupported for best practice {best_practice_id} currently")

                # Custom AI processing code to go here using and modifying applied_file_path content
        elif best_practice_id == 'SLIM-8.1':
            applied_file_path = download_and_place_file(git_repo, uri, 'CODE_OF_CONDUCT.md')
            if use_ai:
                logging.warning(f"AI apply features unsupported for best practice {best_practice_id} currently")

                # Custom AI processing code to go here using and modifying applied_file_path content
        else:
            applied_file_path = None # nothing was modified 
            logging.warning(f"SLIM best practice {best_practice_id} not supported.")
    else:
        logging.warning(f"SLIM best practice {best_practice_id} not supported.")
    
    if applied_file_path:
        logging.info(f"Applied best practice {best_practice_id} to repo {repo_url}, cloned folder {git_repo.working_tree_dir} and branch '{best_practice_id}'")
        return applied_file_path
    else:
        logging.error(f"Failed to apply best practice {best_practice_id} to repo {repo_url}")
        return None


def deploy_best_practice(args):
    branch_name = best_practice_id = args.best_practice_id
    remote_name = args.remote_name  # This should be the name of the remote to push to
    commit_message = args.commit_message  # Commit message for the changes
    
    logging.debug(f"Deploying branch: {branch_name}")
    
    try:
        # Assuming repo_dir points to a local git repository directory
        repo = git.Repo(args.repo_dir)

        # Checkout the branch
        repo.git.checkout(branch_name)
        logging.debug(f"Checked out to branch {branch_name}")

        # Staging files
        repo.git.add(A=True)  # Adds all untracked files
        logging.debug("Added all changes to git index.")

        # Commit changes
        repo.git.commit('-m', commit_message)
        logging.debug("Committed changes.")

        # Push changes to the remote
        repo.git.push(remote_name, branch_name)
        logging.debug(f"Pushed changes to remote {remote_name} on branch {branch_name}")
        logging.info(f"Deployed best practice id '{best_practice_id} to remote '{remote_name}' on branch '{branch_name}'")

        return True
    except git.exc.GitCommandError as e:
        logging.error(f"Git command failed: {str(e)}")
        logging.error(f"An error occurred: {str(e)}")
        return False

def apply_and_deploy_best_practice(args):
    logging.debug("AI customization enabled for applying and deploying best practices" if args.use_ai else "AI customization disabled")
    logging.debug(f"Applying and deploying best practice ID: {args.best_practice_id}")

    # Apply the best practice
    path = apply_best_practice(args)
    
    # Deploy the best practice if applied successfully 
    if path:
        result = deploy_best_practice(args)
        if result:
            logging.info(f"Successfully applied and deployed best practice ID: {args.best_practice_id}")
        else:
            logging.error(f"Unable to deploy best practice ID: {args.best_practice_id}")
    else:
        logging.error(f"Unable to apply and deploy best practice ID: {args.best_practice_id}")
    



def create_parser():
    parser = argparse.ArgumentParser(description='This tool automates the application of best practices to git repositories.')
    parser.add_argument('-d', '--dry-run', action='store_true', help='Generate a dry-run plan of activities to be performed')
    
    subparsers = parser.add_subparsers(dest='command', required=True)

    parser_list = subparsers.add_parser('list', help='Lists all available best practice from the SLIM')
    parser_list.set_defaults(func=list_practices)

    # Parser for applying a best practice
    parser_apply = subparsers.add_parser('apply', help='Applies a best practice, i.e. places a best practice in a git repo in the right spot with appropriate content')
    parser_apply.add_argument('--best_practice_id', required=True, help='Best practice ID')
    parser_apply.add_argument('--repo_url', required=False, help='Repository URL')
    parser_apply.add_argument('--repo_dir', required=False, help='Repository directory location on local machine')
    parser_apply.add_argument('--clone_to_dir', required=False, help='Local path to clone repository to')
    parser_apply.add_argument('--use-ai', action='store_true', help='Automatically customize the application of the best practice')
    parser_apply.set_defaults(func=apply_best_practice)

    # Parser for deploying a best practice
    parser_deploy = subparsers.add_parser('deploy', help='Deploys a best practice, i.e. places the best practice in a git repo, adds, commits, and pushes to the git remote.')
    parser_deploy.add_argument('--best_practice_id', required=True, help='The name of the best_practice_id to deploy')
    parser_deploy.add_argument('--repo_dir', required=False, help='Local repository directory')
    parser_deploy.add_argument('--remote_name', required=True, help='Name of the remote to push changes to')
    parser_deploy.add_argument('--commit_message', required=True, help='Commit message to use for the deployment')
    parser_deploy.set_defaults(func=deploy_best_practice)

    # Parser for applying and deploying a best practice together
    parser_apply_deploy = subparsers.add_parser('apply_deploy', help='Applies and deploys a best practice')
    parser_apply_deploy.add_argument('--best_practice_id', required=True, help='Best practice ID')
    parser_apply_deploy.add_argument('--repo_url', required=False, help='Repository URL')
    parser_apply_deploy.add_argument('--repo_dir', required=False, help='Local repository directory')
    parser_apply_deploy.add_argument('--clone_to_dir', required=False, help='Local path to clone repository to')
    parser_apply_deploy.add_argument('--use-ai', action='store_true', help='Automatically customize the application of the best practice')
    parser_apply_deploy.add_argument('--remote_name', required=True, help='Name of the remote to push changes to')
    parser_apply_deploy.add_argument('--commit_message', required=True, help='Commit message to use for the deployment')
    parser_apply_deploy.set_defaults(func=apply_and_deploy_best_practice)


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
