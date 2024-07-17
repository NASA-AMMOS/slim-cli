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

# Constants
SLIM_REGISTRY_URI = "https://raw.githubusercontent.com/NASA-AMMOS/slim/issue-154/static/data/slim-registry.json"

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
    #practices = fetch_best_practices(SLIM_REGISTRY_URI)
    practices = fetch_best_practices_from_file("slim-registry.json")
    
    if not practices:
        print("No practices found or failed to fetch practices.")
        return

    headers = ["ID", "Title", "Description", "Asset"]
    table = []

    for practice in practices:
        title = textwrap.fill(practice.get('title', 'N/A'), width=30)
        description = textwrap.fill(practice.get('description', 'N/A'), width=50)
        
        # Check for assets and handle accordingly
        if 'assets' in practice and practice['assets']:
            for asset in practice['assets']:
                asset_id = asset['id']
                asset_name = textwrap.fill(asset['name'], width=20)
                table.append([asset_id, title, description, asset_name])
        else: # skip best practices that don't have infusable assets
            logging.debug(f"Skipping best practice {title} due to no infusable assets being available.")

    print(tabulate(table, headers=headers, tablefmt="grid"))


def use_ai(template, repo, best_practice_id):
    """
    Uses AI to generate a new document based on the provided template and best practices from a code repository.
    
    :param template: Path to the template document (e.g., testing.md or governance.md).
    :param repo: URL of the target repository.
    :param best_practice_id: ID of the best practice to apply.
    :return: Generated document as a string.

    # Example usage
    template = "path/to/template.md"
    repo = "https://github.com/your-username/your-repo"
    best_practice_id = "SLIM-001.1"
    new_document = use_ai(template, repo, best_practice_id)
    print(new_document)
    """
        
    # Load environment variables from .env file (OPENAI_API_KEY=your_openai_api_key) 
    load_dotenv()
    openai.api_key = os.getenv('OPENAI_API_KEY')

    # Logging
    logging.debug(f"Using AI to generate document for best practice ID: {best_practice_id} in repository {repo}")

    # Fetch best practices information
    response = requests.get(SLIM_REGISTRY_URI) 
    response.raise_for_status()
    practices = response.json()

    best_practice = next((p for p in practices if p['id'] == best_practice_id), None)

    if not best_practice:
        logging.error(f"Best practice ID {best_practice_id} not found.")
        return None

    # Read the template content
    with open(template, 'r') as file:
        template_content = file.read()

    # Create a temporary directory and clone the repository
    tmp_dir = tempfile.mkdtemp(prefix='repo_clone_' + str(uuid.uuid4()) + '_')
    repo_code_path = os.path.join(tmp_dir, repo)
    subprocess.run(['gh', 'repo', 'clone', repo, repo_code_path], check=True)

    # Fetch the code base from the repository
    code_base = ""
    for root, _, files in os.walk(repo_code_path):
        for file in files:
            if file.endswith('.py'):  # Adjust the file type as needed
                with open(os.path.join(root, file), 'r') as f:
                    code_base += f.read() + "\n\n"

    # Construct the prompt for the AI
    prompt = (
        f"You are an AI assistant. Your task is to generate a new document based on the provided template and best practices.\n\n"
        f"Template:\n{template_content}\n\n"
        f"Best Practice ({best_practice_id}):\n{best_practice}\n\n"
        f"Code Base:\n{code_base}\n\n"
        f"Please generate the new document."
    )

    if openai.api_key:
        # Call the OpenAI API
        response = openai.Completion.create(
            engine="gpt-4o",
            prompt=prompt,
            max_tokens=1500  # Adjust the token count as needed
        )
    else:
        # Fallback to using the Ollama LLaMA3 model
        logging.debug("OpenAI API key is missing. Falling back to using the Ollama Llama3 model.")
        response = subprocess.run(['ollama', 'run', 'llama3', prompt], capture_output=True, text=True)
        response_text = response.stdout

    new_document = response_text if not openai.api_key else response.choices[0].text.strip()
        
    return new_document

    
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
    if best_practice_id == 'SLIM-001.1':
        # Handle the specific case for SLIM-001.1

        pass
    elif best_practice_id == 'SLIM-002':
        # Handle the specific case for SLIM-002
        pass
    else:
        # Default handling for other IDs
        pass

    # Commit and push the changes using GitHub CLI
    subprocess.run(['git', 'add', '.'], check=True)
    subprocess.run(['git', 'commit', '-m', f'Apply best practice {best_practice_id}'], check=True)
    subprocess.run(['gh', 'repo', 'create', '--source', '.', '--public', '--push'], check=True)
    
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
