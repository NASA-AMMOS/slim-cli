import argparse
import logging
import os
import sys
import tempfile
import urllib.parse
import uuid
import yaml
import git
import requests
from typing import Optional, Dict, Any
from . import VERSION

# Import command modules
from jpl.slim.commands.list_command import setup_parser as setup_list_parser
from jpl.slim.commands.apply_command import setup_parser as setup_apply_parser
from jpl.slim.commands.deploy_command import setup_parser as setup_deploy_parser
from jpl.slim.commands.apply_deploy_command import setup_parser as setup_apply_deploy_parser
from jpl.slim.commands.generate_docs_command import setup_parser as setup_generate_docs_parser
from jpl.slim.commands.generate_tests_command import setup_parser as setup_generate_tests_parser
from jpl.slim.commands.common import setup_logging

# Import utility modules for backward compatibility
from jpl.slim.utils.io_utils import (
    fetch_best_practices,
    fetch_best_practices_from_file,
    create_slim_registry_dictionary,
    repo_file_to_list,
    fetch_relative_file_paths,
    download_and_place_file,
    read_file_content,
    fetch_readme,
    fetch_code_base
)
from jpl.slim.utils.git_utils import (
    generate_git_branch_name,
    deploy_best_practice,
    is_open_source
)
from jpl.slim.utils.ai_utils import (
    generate_with_ai,
    construct_prompt,
    generate_content,
    generate_with_openai,
    generate_with_azure,
    generate_with_ollama
)

# Import command functions for backward compatibility
from jpl.slim.commands.list_command import handle_command as list_practices
from jpl.slim.commands.apply_command import apply_best_practices, apply_best_practice
from jpl.slim.commands.deploy_command import deploy_best_practices, deploy_best_practice
from jpl.slim.commands.apply_deploy_command import apply_and_deploy_best_practices, apply_and_deploy_best_practice
from jpl.slim.commands.generate_docs_command import handle_generate_docs
from jpl.slim.commands.generate_tests_command import handle_generate_tests

# Constants
SLIM_REGISTRY_URI = "https://raw.githubusercontent.com/nasa-jpl/slim/main/registry/slim_registry.yaml"
GIT_DEFAULT_COMMIT_MESSAGE = "Applied SLIM best practice"
GIT_BRANCH_NAME_FOR_MULTIPLE_COMMITS = "slim-best-practices"
GIT_DEFAULT_REMOTE_NAME = "origin"
GIT_CUSTOM_REMOTE_NAME = "slim-remote"

# The following functions have been moved to their respective command modules
# and are imported above for backward compatibility

# This function is now in jpl.slim.utils.io_utils
# def create_slim_registry_dictionary(practices):
#     asset_mapping = {}
#     for i, practice in enumerate(practices, start=1):
#         title = practice.get('title', 'N/A')
#         description = practice.get('description', 'N/A')
#         
#         if 'assets' in practice and practice['assets']:
#             for j, asset in enumerate(practice['assets'], start=1):
#                 asset_id = f"SLIM-{i}.{j}"
#                 asset_name = asset.get('name', 'N/A')
#                 asset_uri = asset.get('uri', '')
#                 asset_mapping[asset_id] = {
#                     'title': title, 
#                     'description': description, 
#                     'asset_name': asset_name,
#                     'asset_uri': asset_uri
#                 }
#         else:
#             asset_mapping[f"SLIM-{i}"] = {'title': title, 'description': description, 'asset_name': 'None'}
#     return asset_mapping

def get_ai_model_pairs(supported_models):
    # return a list of "key/value" pairs
    return [f"{key}/{model}" for key, models in supported_models.items() for model in models]

# This function is now in jpl.slim.utils.git_utils
# def is_open_source(repo_url):
#     """
#     Check if the repository is open-source by inspecting its license type.
#     Returns True if the repository is open-source, False otherwise.
#     """
#     try:
#         # Extract owner and repo name from the URL
#         owner_repo = repo_url.rstrip('/').split('/')[-2:]
#         owner, repo = owner_repo[0], owner_repo[1]
# 
#         # Use the GitHub API to fetch the repository license
#         api_url = f"https://api.github.com/repos/{owner}/{repo}/license"
#         headers = {
#             "Accept": "application/vnd.github.v3+json",
#             "Authorization": f"token {os.getenv('GITHUB_API_TOKEN')}"  # Optional: Use GitHub token for higher rate limits
#         }
#         response = requests.get(api_url, headers=headers)
#         if response.status_code == 200:
#             license_data = response.json()
#             license_name = license_data.get('license', {}).get('spdx_id', '')
#             open_source_licenses = [
#                 "MIT", "Apache-2.0", "GPL-3.0", "GPL-2.0", "BSD-3-Clause", 
#                 "BSD-2-Clause", "LGPL-3.0", "MPL-2.0", "CDDL-1.0", "EPL-2.0"
#             ]
#             return license_name in open_source_licenses
#         else:
#             print(f"Failed to fetch license information. Status code: {response.status_code}")
#             return False
#     except Exception as e:
#         print(f"An error occurred while checking the license: {e}")
#         return False
        
# These functions are now in jpl.slim.utils.ai_utils
# def use_ai(best_practice_id: str, repo_path: str, template_path: str, model: str = "openai/gpt-4o") -> Optional[str]:
#     """
#     Uses AI to generate or modify content based on the provided best practice and repository.
#     
#     :param best_practice_id: ID of the best practice to apply.
#     :param repo_path: Path to the cloned repository.
#     :param template_path: Path to the template file for the best practice.
#     :param model: Name of the AI model to use (example: "openai/gpt-4o", "ollama/llama3.1:70b").
#     :return: Generated or modified content as a string, or None if an error occurs.
#     """
#     
#     logging.debug(f"Using AI to apply best practice ID: {best_practice_id} in repository {repo_path}")
#     
#     # Fetch best practice information
#     practices = fetch_best_practices(SLIM_REGISTRY_URI)
#     asset_mapping = create_slim_registry_dictionary(practices)
#     best_practice = asset_mapping.get(best_practice_id)
#     
#     if not best_practice:
#         logging.error(f"Best practice ID {best_practice_id} not found.")
#         return None
#     
#     # Read the template content
#     template_content = read_file_content(template_path)
#     if not template_content:
#         return None
#     
#     # Fetch appropriate reference content based on best practice ID
#     if best_practice_id == 'SLIM-1.1': #governance 
#         reference = fetch_readme(repo_path)
#         additional_instruction = ""
#     elif best_practice_id == 'SLIM-3.1': #readme
#         reference = fetch_code_base(repo_path)
#         additional_instruction = ""
#     elif best_practice_id == 'SLIM-13.1': #readme
#         reference1 = fetch_readme(repo_path)
#         reference2 = "\n".join(fetch_relative_file_paths(repo_path))
#         reference = "EXISTING README:\n" + reference1 + "\n\n" + "EXISTING DIRECTORY LISTING: " + reference2
#         additional_instruction = "Within the provided testing template, only fill out the sections that plausibly have existing tests to fill out based on the directory listing provided (do not make up tests that do not exist)."
#     else:
#         reference = fetch_readme(repo_path)
#         additional_instruction = ""
#     
#     if not reference:
#         return None
#         
#     # Construct the prompt for the AI
#     prompt = construct_prompt(template_content, best_practice, reference, additional_instruction if best_practice_id == 'SLIM-13.1' else "")
#     
#     # Generate and return the content using the specified model
#     return generate_content(prompt, model)
# 
# 
# def fetch_readme(repo_path: str) -> Optional[str]:
#     readme_files = ['README.md', 'README.txt', 'README.rst']  # Add more variations as needed
#     
#     for root, _, files in os.walk(repo_path):
#         for file in files:
#             if file in readme_files:
#                 file_path = os.path.join(root, file)
#                 return read_file_content(file_path)
#     
#     return None
# 
# 
# def fetch_code_base(repo_path: str) -> Optional[str]:
#     code_base = ""
#     for root, _, files in os.walk(repo_path):
#         for file in files:
#             if file.endswith(('.py', '.js', '.java', '.cpp', '.cs')):  # Add more extensions as needed
#                 file_path = os.path.join(root, file)
#                 code_base += read_file_content(file_path) or ""
#     return code_base if code_base else None
# 
# def fetch_relative_file_paths(directory):
#     relative_paths = []
#     for root, _, files in os.walk(directory):
#         for file in files:
#             # Get the relative file path and add it to the list
#             relative_path = os.path.relpath(os.path.join(root, file), directory)
#             relative_paths.append(relative_path)
#     return relative_paths
# 
# def construct_prompt(template_content: str, best_practice: Dict[str, Any], reference: str, comment: str = "") -> str:
#     return (
#         f"Fill out all blanks in the template below that start with INSERT. Use the provided context information to fill the blanks. Return the template with filled out values. {comment}\n\n"
#         f"TEMPLATE:\n{template_content}\n\n"
#         f"CONTEXT INFORMATION:\n{reference}\n\n"
#     )
# 
# def generate_content(prompt: str, model: str) -> Optional[str]:
#     model_provider, model_name = model.split('/')
#     
#     if model_provider == "openai":
#         collected_response = []
#         for token in generate_with_openai(prompt, model_name):
#             if token is not None:
#                 #print(token, end='', flush=True)
#                 collected_response.append(token)
#             else:
#                 print("\nError occurred during generation.")
#         print()  # Print a newline at the end
#         return ''.join(collected_response)
#     elif model_provider == "azure":
#         #collected_response = []
#         #for token in generate_with_azure(prompt, model_name):
#         #    if token is not None:
#         #        print(token, end='', flush=True)
#         #        collected_response.append(token)
#         #    else:
#         #        print("\nError occurred during generation.")
#         #print()  # Print a newline at the end
#         return generate_with_azure(prompt, model_name)
#     elif model_provider == "ollama":
#         return generate_with_ollama(prompt, model_name)
#     else:
#         logging.error(f"Unsupported model provider: {model_provider}")
#         return None
#     
# 
# def read_file_content(file_path: str) -> Optional[str]:
#     try:
#         with open(file_path, 'r') as file:
#             return file.read()
#     except IOError as e:
#         logging.error(f"Error reading file {file_path}: {e}")
#         return None
# 
# def generate_with_azure(prompt: str, model_name: str) -> Optional[str]:
#     from azure.identity import ClientSecretCredential, get_bearer_token_provider
#     from openai import AzureOpenAI
#     from dotenv import load_dotenv
#     import numpy as np
#     
#     try:
#         load_dotenv()
# 
#         APIM_SUBSCRIPTION_KEY = os.getenv("APIM_SUBSCRIPTION_KEY")
#         default_headers = {}
#         if APIM_SUBSCRIPTION_KEY != None:
#             # only set this if the APIM API requires a subscription...
#             default_headers["Ocp-Apim-Subscription-Key"] = APIM_SUBSCRIPTION_KEY 
# 
#         # Set up authority and credentials for Azure authentication
#         credential = ClientSecretCredential(
#             tenant_id=os.getenv("AZURE_TENANT_ID"),
#             client_id=os.getenv("AZURE_CLIENT_ID"),
#             client_secret=os.getenv("AZURE_CLIENT_SECRET"),
#             authority="https://login.microsoftonline.com",
#         )
# 
#         token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
# 
#         client = AzureOpenAI(
#             # azure_ad_token=access_token.token,
#             azure_ad_token_provider=token_provider,
#             api_version=os.getenv("API_VERSION"),
#             azure_endpoint=os.getenv("API_ENDPOINT"),
#             default_headers=default_headers,
#         )
# 
#         completion = client.chat.completions.create(
#             messages = [
#                 {
#                     "role": "system",
#                     "content": "As a SLIM Best Practice User, your role is to understand, apply, and implement the best practices for Software Lifecycle Improvement and Modernization (SLIM) within your software projects. You should aim to optimize your software development processes, enhance the quality of your software products, and ensure continuous improvement across all stages of the software lifecycle.",
#                 },
#                 {
#                     "role": "user",
#                     "content": prompt,
#                 }
#             ],
#             model=model_name
#         )
#         return completion.choices[0].message.content
#     except Exception as e:
#         print(f"An error occurred running on Azure model: {str(e)}")
#         return None
# 
# 
# def generate_with_openai(prompt: str, model_name: str) -> Optional[str]:
#     from openai import OpenAI
#     from dotenv import load_dotenv
#     load_dotenv()
#     try:    
#         client = OpenAI(api_key = os.getenv('OPENAI_API_KEY'))
#         response = client.chat.completions.create(
#             model=model_name,
#             messages=[{"role": "user", "content": prompt}],
#             stream=True
#         )
#         for chunk in response:
#             if chunk.choices[0].delta.content is not None:
#                 yield chunk.choices[0].delta.content
#     except Exception as e:
#         print(f"An error occurred running OpenAI model: {e}")
#         yield None
# 
# def generate_with_ollama(prompt: str, model_name: str) -> Optional[str]:
#     import ollama
# 
#     try:
#         response = ollama.chat(model=model_name, messages=[
#         {
#             'role': 'user',
#             'content': prompt,
#         },
#         ])
#         #print(response['message']['content'])
#         return (response['message']['content'])
#     except Exception as e:
#         logging.error(f"Error running Ollama model: {e}")
#         return None
# 
#     #try:
#     #    response = subprocess.run(['ollama', 'run', model_name, prompt], capture_output=True, text=True, check=True)
#     #    return response.stdout.strip()
#     #except subprocess.CalledProcessError as e:
#     #    logging.error(f"Error running Ollama model: {e}")
#     #    return None
# 
# def download_and_place_file(repo, url, filename, target_relative_path_in_repo=''):
#     # Create the full path where the file will be saved. By default write to root.
#     target_directory = os.path.join(repo.working_tree_dir, target_relative_path_in_repo)
#     file_path = os.path.join(target_directory, filename)
# 
#     # Ensure that the target directory exists, create if not
#     os.makedirs(target_directory, exist_ok=True)
# 
#     # Fetch the file from the URL
#     response = requests.get(url)
#     if response.status_code == 200:
#         # Ensure the parent directories exist
#         os.make
        
# These functions are now imported from their respective modules

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

    # Set up parsers for each command
    setup_list_parser(subparsers)
    setup_apply_parser(subparsers)
    setup_deploy_parser(subparsers)
    setup_apply_deploy_parser(subparsers)
    setup_generate_docs_parser(subparsers)
    setup_generate_tests_parser(subparsers)

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
            print(f"   cp -r {args.output_dir}/*.md my-docs/docs/")
            print(f"   cp -r {args.output_dir}/docusaurus.config.js my-docs/")
            print(f"   cp -r {args.output_dir}/sidebars.js my-docs/")
            print(f"   cp -r {args.output_dir}/static/* my-docs/static/")
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
