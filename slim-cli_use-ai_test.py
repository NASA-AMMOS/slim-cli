# python slim-cli_use-ai_test.py --template https://github.com/NASA-AMMOS/slim/blob/main/docs/guides/governance/governance-model/GOVERNANCE-TEMPLATE.md --repo https://github.com/NASA-AMMOS/slim-cli/ --best-practice https://github.com/NASA-AMMOS/slim/tree/main/docs/guides/governance/governance-model
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
from typing import Optional, Dict, Any, List, Tuple

# Constants
SUPPORTED_MODELS = {
    "openai": ["gpt-4o-mini", "gpt-4o"],
    "ollama": ["llama3", "mistral", "codellama"],
}

def setup_logging() -> logging.Logger:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    return logging.getLogger(__name__)

def load_environment():
    load_dotenv()
    if not os.getenv('OPENAI_API_KEY'):
        logging.warning("OpenAI API key is not set in the environment.")

def use_ai(template: str, repo: str, best_practice: str, model: str = "ollama/llama2") -> Optional[str]:
    """
    Uses AI to generate a new document based on the provided template and best practices from a code repository.
    
    :param template: URL to the template document.
    :param repo: URL of the target repository.
    :param best_practice: URL to the best practice guide.
    :param model: Name of the AI model to use (default: "ollama/llama2").
    :return: Generated document as a string, or None if an error occurs.
    """
    logger = setup_logging()
    load_environment()
    
    logger.info(f"Generating document for best practice: {best_practice} in repository {repo}")
    
    best_practice_content = read_url_content(best_practice)
    template_content = read_url_content(template)
    code_base = clone_repo_and_fetch_code(repo)
    
    if not all([best_practice_content, template_content, code_base]):
        logger.error("Failed to fetch all required content.")
        return None
    
    prompt = construct_prompt(template_content, best_practice_content, code_base)
    return generate_document(prompt, model)

def read_url_content(url: str) -> Optional[str]:
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching content from {url}: {e}")
        return None

def clone_repo_and_fetch_code(repo: str) -> Optional[str]:
    with tempfile.TemporaryDirectory(prefix='repo_clone_') as tmp_dir:
        repo_list_file = os.path.join(tmp_dir, 'repo_list.txt')
        with open(repo_list_file, 'w') as f:
            f.write(f"{repo}\n")
        
        repo_code_path = os.path.join(tmp_dir, 'cloned_repos')
        try:
            subprocess.run(['git', 'clone', repo, repo_code_path], 
                           check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            logging.error(f"Error cloning repository: {e.stderr}")
            return None
        
        cloned_repo_path = os.path.join(repo_code_path, os.path.basename(repo))
        return aggregate_code_files(cloned_repo_path)

def aggregate_code_files(repo_path: str, file_extensions: Tuple[str] = ('.py', '.js', '.java', '.cpp', '.cs')) -> str:
    code_base = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith(file_extensions):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    code_base.append(f"File: {os.path.relpath(file_path, repo_path)}\n{f.read()}\n")
    return "\n".join(code_base)

def construct_prompt(template_content: str, best_practice_content: str, code_base: str) -> str:
    return textwrap.dedent(f"""
    You are an AI assistant tasked with generating a new document based on the provided template and best practices.

    Template:
    {template_content}

    Best Practice:
    {best_practice_content}

    Code Base:
    {code_base}

    update the template above using the information from best practice and code base.
    """).strip()

def generate_document(prompt: str, model: str) -> Optional[str]:
    provider, model_name = model.split('/')
    
    generators = {
        "openai": generate_with_openai,
        "ollama": generate_with_ollama
    }
    
    generator = generators.get(provider)
    if not generator:
        logging.error(f"Unsupported model provider: {provider}")
        return None
    
    return generator(prompt, model_name)

def generate_with_openai(prompt: str, model_name: str) -> Optional[str]:
    openai.api_key = os.getenv('OPENAI_API_KEY')
    if not openai.api_key:
        logging.error("OpenAI API key is missing.")
        return None
    
    try:
        response = openai.ChatCompletion.create(
            model=model_name,
            messages=[{"role": "system", "content": "You are a helpful AI assistant."},
                      {"role": "user", "content": prompt}],
            max_tokens=2000
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
        logging.error(f"Error running Ollama model: {e.stderr}")
        return None

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate AI-assisted documents based on templates and best practices.")
    parser.add_argument("--template", required=True, help="URL to the template document")
    parser.add_argument("--repo", required=True, help="URL of the target repository")
    parser.add_argument("--best-practice", required=True, help="URL to the best practice guide")
    parser.add_argument("--model", default="ollama/llama3", help="AI model to use (e.g., 'ollama/llama2' or 'openai/gpt-3.5-turbo')")
    return parser.parse_args()

def main():
    args = parse_arguments()
    new_document = use_ai(args.template, args.repo, args.best_practice, args.model)
    if new_document:
        print(new_document)
    else:
        print("Failed to generate document.")

if __name__ == "__main__":
    main()