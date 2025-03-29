"""
AI utility functions for SLIM.

This module contains utility functions for AI operations, including generating content
with various AI models.
"""

import os
import logging

# Import functions from io_utils
from jpl.slim.utils.io_utils import (
    fetch_best_practices,
    create_slim_registry_dictionary,
    read_file_content,
    fetch_readme,
    fetch_code_base,
    fetch_relative_file_paths
)

__all__ = [
    "generate_with_ai",
    "construct_prompt",
    "generate_content",
    "generate_with_openai",
    "generate_with_azure",
    "generate_with_ollama"
]


def generate_with_ai(best_practice_id, repo_path, template_path, model="openai/gpt-4o"):
    """
    Uses AI to generate or modify content based on the provided best practice and repository.
    
    Args:
        best_practice_id: ID of the best practice to apply
        repo_path: Path to the cloned repository
        template_path: Path to the template file for the best practice
        model: Name of the AI model to use (example: "openai/gpt-4o", "ollama/llama3.1:70b")
        
    Returns:
        str: Generated or modified content, or None if an error occurs
    """
    logging.debug(f"Using AI to apply best practice ID: {best_practice_id} in repository {repo_path}")
    
    # Fetch best practice information
    from jpl.slim.cli import SLIM_REGISTRY_URI  # Temporary import until constants are moved
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
    
    # Fetch appropriate reference content based on best practice ID
    if best_practice_id == 'SLIM-1.1': #governance 
        reference = fetch_readme(repo_path)
        additional_instruction = ""
    elif best_practice_id == 'SLIM-3.1': #readme
        reference = fetch_code_base(repo_path)
        additional_instruction = ""
    elif best_practice_id == 'SLIM-13.1': #readme
        reference1 = fetch_readme(repo_path)
        reference2 = "\n".join(fetch_relative_file_paths(repo_path))
        reference = "EXISTING README:\n" + reference1 + "\n\n" + "EXISTING DIRECTORY LISTING: " + reference2
        additional_instruction = "Within the provided testing template, only fill out the sections that plausibly have existing tests to fill out based on the directory listing provided (do not make up tests that do not exist)."
    else:
        reference = fetch_readme(repo_path)
        additional_instruction = ""
    
    if not reference:
        return None
        
    # Construct the prompt for the AI
    prompt = construct_prompt(template_content, best_practice, reference, additional_instruction if best_practice_id == 'SLIM-13.1' else "")
    
    # Generate and return the content using the specified model
    return generate_content(prompt, model)


def construct_prompt(template_content, best_practice, reference, comment=""):
    """
    Construct a prompt for AI.
    
    Args:
        template_content: Content of the template
        best_practice: Best practice information
        reference: Reference content
        comment: Additional comment
        
    Returns:
        str: Constructed prompt
    """
    return (
        f"Fill out all blanks in the template below that start with INSERT. Use the provided context information to fill the blanks. Return the template with filled out values. {comment}\n\n"
        f"TEMPLATE:\n{template_content}\n\n"
        f"CONTEXT INFORMATION:\n{reference}\n\n"
    )


def generate_content(prompt, model):
    """
    Generate content using an AI model.
    
    Args:
        prompt: Prompt for the AI model
        model: Name of the AI model to use
        
    Returns:
        str: Generated content, or None if an error occurs
    """
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


def generate_with_openai(prompt, model_name):
    """
    Generate content using OpenAI.
    
    Args:
        prompt: Prompt for the AI model
        model_name: Name of the OpenAI model to use
        
    Yields:
        str: Generated content tokens
    """
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


def generate_with_azure(prompt, model_name):
    """
    Generate content using Azure OpenAI.
    
    Args:
        prompt: Prompt for the AI model
        model_name: Name of the Azure OpenAI model to use
        
    Returns:
        str: Generated content, or None if an error occurs
    """
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


def generate_with_ollama(prompt, model_name):
    """
    Generate content using Ollama.
    
    Args:
        prompt: Prompt for the AI model
        model_name: Name of the Ollama model to use
        
    Returns:
        str: Generated content, or None if an error occurs
    """
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
