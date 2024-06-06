import argparse
import logging
import sys
import requests
import re

def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_best_practices(url):
    response = requests.get(url)
    response.raise_for_status()
    content = response.text

    # Extract table content from the markdown
    table_match = re.search(r'\|.*?\n\|[\s-]+\n((\|.*?\n)+)', content)
    if not table_match:
        logging.error("Could not find the table in the provided URL")
        return []

    table_content = table_match.group(1).strip().split('\n')

    practices = []
    for row in table_content:
        columns = [col.strip() for col in row.split('|') if col]
        if len(columns) == 3:
            practices.append({
                "ID": columns[0],
                "NAME": columns[1],
                "DESCRIPTION": columns[2],
            })

    return practices
    
def list_practices(args):
    logging.debug("Listing all best practices...")
    url = "https://raw.githubusercontent.com/NASA-AMMOS/slim/main/docs/guides/checklist.md"
    practices = fetch_best_practices(url)
    
    if not practices:
        print("No practices found or failed to fetch practices.")
        return

    print(f"{'ID'.ljust(10)}{'NAME'.ljust(20)}{'DESCRIPTION'}")
    print("-" * 60)
    for practice in practices:
        print(f"{practice['ID'].ljust(10)}{practice['NAME'].ljust(20)}{practice['DESCRIPTION']}")

def add_repository(args):
    repo = args.repo
    logging.debug(f"Adding repository: {repo}")
    print(f"This feature needs to be implemented - Adding repository from {repo}")

def remove_repository(args):
    repo = args.repo
    logging.debug(f"Removing repository: {repo}")
    print(f"This feature needs to be implemented - Removing repository {repo}")

def list_repositories(args):
    logging.debug("Listing all repositories...")
    print("This feature needs to be implemented - Listing repositories")

def apply_best_practice(args):
    best_practice_id = args.best_practice_id
    use_ai = args.use_ai
    if use_ai:
        logging.debug("AI features enabled for applying best practices")
    logging.debug(f"Applying best practice ID: {best_practice_id}")
    print(f"This feature needs to be implemented - Applying best practice {best_practice_id}")

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

    parser_repos = subparsers.add_parser('repos', help='Initialize / list git repositories')
    repos_subparsers = parser_repos.add_subparsers(required=True)
    
    parser_add = repos_subparsers.add_parser('add', help='Add repositories from file or URL')
    parser_add.add_argument('repo', help='File path or repository URL')
    parser_add.set_defaults(func=add_repository)
    
    parser_remove = repos_subparsers.add_parser('remove', help='Remove a repository')
    parser_remove.add_argument('repo', help='Repository URL')
    parser_remove.set_defaults(func=remove_repository)
    
    parser_list_repos = repos_subparsers.add_parser('list', help='List repositories')
    parser_list_repos.set_defaults(func=list_repositories)

    parser_apply = subparsers.add_parser('apply', help='Applies a best practice')
    parser_apply.add_argument('best_practice_id', help='Best practice ID')
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
