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

    # Get best practices information
    practices = fetch_best_practices(SLIM_REGISTRY_URI)

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
