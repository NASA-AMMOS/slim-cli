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

# Constants
SLIM_REGISTRY_URI = "https://raw.githubusercontent.com/NASA-AMMOS/slim/issue-154/static/data/slim-registry.json"
SUPPORTED_MODELS = {
    "openai": ["gpt-3.5-turbo", "gpt-4o"],
    "ollama": ["llama2", "mistral", "codellama"],
    # Add more models as needed
}

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
    # practices = fetch_best_practices(SLIM_REGISTRY_URI)
    practices = fetch_best_practices_from_file("slim-registry.json")

    if not practices:
        print("No practices found or failed to fetch practices.")
        return

    console = Console()
    table = Table(show_header=True, header_style="bold magenta", show_lines=True)
    headers = ["ID", "Title", "Description", "Asset"]
    for header in headers:
        table.add_column(header)

    i = 0  # Start the manual index for practices with assets
    for practice in practices:
        title = textwrap.fill(practice.get('title', 'N/A'), width=30)
        description = textwrap.fill(practice.get('description', 'N/A'), width=50)
        
        if 'assets' in practice and practice['assets']:
            i += 1  # Increment the practice index only if there are assets
            for j, asset in enumerate(practice['assets'], start=1):
                asset_id = f"SLIM-{i}.{j}"
                asset_name = textwrap.fill(asset['name'], width=20)
                table.add_row(asset_id, title, description, asset_name)
        else:
            logging.debug(f"Skipping best practice {title} due to no infusable assets being available.")

    console.print(table)


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

def apply_best_practice(args):
    best_practice_id = args.best_practice_id
    use_ai = args.use_ai
    repo = args.repo
    tmp_dir = tempfile.mkdtemp(prefix='repo_clone_' + str(uuid.uuid4()) + '_')

    if use_ai:
        logging.debug("AI features enabled for applying best practices")
    logging.debug(f"Applying best practice ID: {best_practice_id} to repository {repo}")

    # FOR TESTING: Clone the repository to the temporary directory
    # if not os.path.exists(tmp_dir):
    #     os.makedirs(tmp_dir)
    # subprocess.run(['git', 'clone', repo, tmp_dir], check=True)

    # Clone the repository using GitHub CLI
    subprocess.run(['gh', 'repo', 'clone', repo, tmp_dir], check=True)
    
    # Get best practices information
    practices = fetch_best_practices(SLIM_REGISTRY_URI)

    # Change directory to the cloned repository
    os.chdir(tmp_dir)
    
    # Switch statement skeleton
    # NOTE: we'll want to use multi-gitter to do the actual patch application. See: https://github.com/lindell/multi-gitter
    # if best_practice_id == 'SLIM-001.1':
    #     # Handle the specific case for SLIM-001.1

    #     if use_ai:
    #         # take GOVERNANCE.md template, and use LLMs to fill the specific template tags in using information from the repository
    #         # REPOSITORY CONTEXT INFORMATION:
    #         # - Git repo information, e.g. name
    #         # - GitHub project metadata
    #         # - List of committers?

    #         # use_ai(artifact_id, "GPT-4", repository_uir)
    #     #pass
    # elif best_practice_id == 'SLIM-002':
    #     # Handle the specific case for SLIM-002
    #     pass
    # else:
    #     # Default handling for other IDs
    #     pass

    # Commit and push the changes using GitHub CLI
    subprocess.run(['git', 'add', '.'], check=True)
    subprocess.run(['git', 'commit', '-m', f'Apply best practice {best_practice_id}'], check=True)
    subprocess.run(['gh', 'repo', 'create', '--source', '.', '--public', '--push'], check=True)

    # multi-gitter run best-practice-script.sh myorg/myrepo1 myorg/myrepo2
    
    print(f"Applying best practice {best_practice_id} to repository.")

def deploy_branch(args):
    branch_name = args.branch_name
    logging.debug(f"Deploying branch: {branch_name}")
    print(f"This feature needs to be implemented - Deploying branch {branch_name}")

def apply_and_deploy(args):
    best_practice_id = args.best_practice_id
    use_ai = args.use_ai
    if use_ai:
        logging.debug("AI customization enabled for applying and deploying best practices")
    logging.debug(f"Applying and deploying best practice ID: {best_practice_id}")
    print(f"This feature needs to be implemented - Applying and deploying {best_practice_id}")

def create_parser():
    parser = argparse.ArgumentParser(description='This tool automates the application of best practices to git repositories.')
    parser.add_argument('-d', '--dry-run', action='store_true', help='Generate a dry-run plan of activities to be performed')
    
    subparsers = parser.add_subparsers(dest='command', required=True)

    parser_list = subparsers.add_parser('list', help='Lists all available best practice from the SLIM')
    parser_list.set_defaults(func=list_practices)

    parser_apply = subparsers.add_parser('apply', help='Applies a best practice')
    parser_apply.add_argument('best_practice_id', help='Best practice ID')
    parser_apply.add_argument('repo', help='Repository URL')
    parser_apply.add_argument('--use-ai', action='store_true', help='Automatically customize the application of the best practice')
    parser_apply.set_defaults(func=apply_best_practice)

    parser_deploy = subparsers.add_parser('deploy', help='Deploys a branch and creates a pull request')
    parser_deploy.add_argument('branch_name', help='Branch name to deploy')
    parser_deploy.set_defaults(func=deploy_branch)

    parser_apply_deploy = subparsers.add_parser('apply-deploy', help='Apply and deploy a best practice')
    parser_apply_deploy.add_argument('best_practice_id', help='Best practice ID')
    parser_apply_deploy.add_argument('--use-ai', action='store_true', help='Automatically customize the application of the best practice')
    parser_apply_deploy.set_defaults(func=apply_and_deploy)

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
