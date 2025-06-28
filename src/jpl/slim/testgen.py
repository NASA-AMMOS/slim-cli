# testgen.py

import os
import re
import git
import json
import logging
import argparse
from typing import Dict, List, Optional, Tuple, Any
from .cli import generate_content, setup_logging

class TestGenerator:
    """
    Generates unit test files for a repository using AI assistance.
    """
    
    def __init__(self, repo_path: str, model: str = "azure/gpt-4o", output_dir: Optional[str] = None):
        self.repo_path = repo_path
        self.model = model
        self.output_dir = output_dir
        self.logger = logging.getLogger(__name__)
        
        # Configure test file naming conventions per language
        self.test_conventions = {
            'py': {'prefix': 'test_', 'suffix': '.py', 'framework': 'pytest'},
            'js': {'prefix': '', 'suffix': '.test.js', 'framework': 'jest'},
            'ts': {'prefix': '', 'suffix': '.spec.ts', 'framework': 'jest'},
            'java': {'prefix': 'Test', 'suffix': 'Test.java', 'framework': 'junit'},
            'cpp': {'prefix': '', 'suffix': '_test.cpp', 'framework': 'gtest'},
            'cs': {'prefix': '', 'suffix': 'Tests.cs', 'framework': 'nunit'}
        }
        
        # Map of language-specific import statements and basic test structures
        self.language_templates = {
            'py': {
                'imports': 'import pytest\nfrom unittest.mock import Mock, patch\n',
                'test_class': 'class Test{class_name}:\n    """Tests for {class_name} class."""\n'
            },
            'js': {
                'imports': "const {class_name} = require('./{source_file}');\n",
                'test_class': "describe('{class_name}', () => {\n});\n"
            },
            'ts': {
                'imports': "import { {class_name} } from './{source_file}';\n",
                'test_class': "describe('{class_name}', () => {\n});\n"
            },
            'java': {
                'imports': 'import org.junit.jupiter.api.Test;\nimport static org.junit.jupiter.api.Assertions.*;\n',
                'test_class': 'public class {class_name}Test {\n}\n'
            },
            'cpp': {
                'imports': '#include <gtest/gtest.h>\n#include "{source_file}"\n',
                'test_class': 'TEST({class_name}, Basic) {\n}\n'
            },
            'cs': {
                'imports': 'using NUnit.Framework;\nusing System;\n',
                'test_class': '[TestFixture]\npublic class {class_name}Tests {\n}\n'
            }
        }

    def analyze_source_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analyzes a source file to extract classes, methods, and other testable elements.
        """
        with open(file_path, 'r') as f:
            content = f.read()
            
        file_ext = file_path.split('.')[-1]
        
        # Extract classes and methods based on language
        if file_ext == 'py':
            classes = re.findall(r'class\s+(\w+)[:\(]', content)
            methods = re.findall(r'def\s+(\w+)\s*\(', content)
        elif file_ext in ['js', 'ts']:
            classes = re.findall(r'class\s+(\w+)', content)
            methods = re.findall(r'(async\s+)?function\s+(\w+)\s*\(|(\w+)\s*:\s*function\s*\(|(\w+)\s*=\s*\([^)]*\)\s*=>', content)
        elif file_ext == 'java':
            classes = re.findall(r'class\s+(\w+)', content)
            methods = re.findall(r'(public|private|protected)?\s+\w+\s+(\w+)\s*\([^)]*\)\s*{', content)
        else:
            classes = re.findall(r'class\s+(\w+)', content)
            methods = re.findall(r'\w+\s+(\w+)\s*\([^)]*\)\s*{', content)
            
        return {
            'content': content,
            'classes': classes,
            'methods': methods,
            'file_ext': file_ext,
            'file_name': os.path.basename(file_path)
        }

    def generate_test_file_path(self, source_path: str, analysis: Dict[str, Any]) -> str:
        """
        Generates the appropriate test file path based on source file and conventions.
        """
        dir_path = os.path.dirname(source_path)
        file_name = os.path.basename(source_path)
        file_ext = analysis['file_ext']
        
        if file_ext not in self.test_conventions:
            raise ValueError(f"Unsupported file extension: {file_ext}")
            
        convention = self.test_conventions[file_ext]
        base_name = os.path.splitext(file_name)[0]
        test_file_name = f"{convention['prefix']}{base_name}{convention['suffix']}"
        
        if self.output_dir:
            return os.path.join(self.output_dir, test_file_name)
            
        # Look for existing test directory
        test_dirs = ['tests', 'test', f'{base_name}_tests']
        for test_dir in test_dirs:
            test_path = os.path.join(dir_path, test_dir)
            if os.path.exists(test_path):
                return os.path.join(test_path, test_file_name)
                
        # Default to same directory as source
        return os.path.join(dir_path, test_file_name)

    def generate_test_content(self, analysis: Dict[str, Any]) -> str:
        """
        Generates test content using AI based on source file analysis.
        """
        prompt = self._create_test_generation_prompt(analysis)
        test_content = generate_content(prompt, self.model)
        
        if not test_content:
            raise ValueError("Failed to generate test content")
            
        return test_content

    def _create_test_generation_prompt(self, analysis: Dict[str, Any]) -> str:
        """
        Creates a detailed prompt for AI test generation.
        """
        file_ext = analysis['file_ext']
        convention = self.test_conventions[file_ext]
        framework = convention['framework']
        
        prompt = f"""Generate comprehensive unit tests for the following {file_ext.upper()} code using {framework}.
The tests should include:
1. Test cases for normal operation
2. Edge cases and boundary conditions
3. Error cases and exception handling
4. Mocking of external dependencies where appropriate

Source code to test:

```{file_ext}
{analysis['content']}
```

Requirements:
- Use {framework} testing conventions and best practices
- Include appropriate assertions
- Add clear test descriptions/documentation
- Group related tests logically
- Follow standard naming conventions
- Include setup/teardown where needed

Please generate complete, runnable test code including imports and proper test structure.
"""
        return prompt

    def find_testable_files(self) -> List[str]:
        """
        Finds all testable source files in the repository.
        """
        testable_files = []
        exclude_dirs = {'.git', 'node_modules', 'venv', '__pycache__', 'build', 'dist'}
        supported_extensions = set(self.test_conventions.keys())
        
        for root, dirs, files in os.walk(self.repo_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs]
            
            for file in files:
                ext = file.split('.')[-1]
                if ext in supported_extensions:
                    # Skip existing test files
                    if any(file.startswith(conv['prefix']) and file.endswith(conv['suffix']) 
                          for conv in self.test_conventions.values()):
                        continue
                    testable_files.append(os.path.join(root, file))
                    
        return testable_files

    def generate_tests(self) -> Dict[str, str]:
        """
        Generates tests for all testable files in the repository.
        
        Returns:
            Dictionary mapping test file paths to generated content
        """
        generated_tests = {}
        
        testable_files = self.find_testable_files()
        self.logger.info(f"Found {len(testable_files)} testable files")
        
        for source_file in testable_files:
            try:
                self.logger.debug(f"Analyzing {source_file}")
                analysis = self.analyze_source_file(source_file)
                
                test_file_path = self.generate_test_file_path(source_file, analysis)
                test_content = self.generate_test_content(analysis)
                
                # Ensure the output directory exists
                os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
                
                # Write the test file immediately after generation
                with open(test_file_path, 'w', encoding='utf-8') as f:
                    f.write(test_content)
                    
                generated_tests[test_file_path] = test_content
                self.logger.info(f"Generated and saved tests for {source_file} to {test_file_path}")
                
            except Exception as e:
                self.logger.error(f"Failed to generate tests for {source_file}: {str(e)}")
                continue
        
        return generated_tests

    def write_tests(self, generated_tests: Dict[str, str]) -> bool:
        """
        Verifies that all tests were written successfully.
        """
        success = True
        for test_path in generated_tests:
            if not os.path.exists(test_path):
                self.logger.error(f"Test file was not created: {test_path}")
                success = False
        return success
        
def main():
    parser = argparse.ArgumentParser(description='Generate unit tests for a repository using AI')
    parser.add_argument('--repo-dir', required=True, help='Repository directory')
    parser.add_argument('--output-dir', help='Output directory for generated tests')
    parser.add_argument('--model', default='azure/gpt-4o', help='AI model to use')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(logging.INFO)  # logging.DEBUG
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        generator = TestGenerator(args.repo_dir, args.model, args.output_dir)
        generated_tests = generator.generate_tests()
        
        if not generated_tests:
            logging.error("No tests were generated")
            return 1
            
        if generator.write_tests(generated_tests):
            logging.debug(f"Successfully generated {len(generated_tests)} test files")
            return 0
        else:
            logging.error("Failed to write some test files")
            return 1
            
    except Exception as e:
        logging.error(f"Test generation failed: {str(e)}")
        return 1

if __name__ == '__main__':
    exit(main())