"""
Unit tests for repo_utils module.
"""

import pytest
import tempfile
import os
import json
from pathlib import Path
from unittest.mock import patch, mock_open

from jpl.slim.utils.repo_utils import (
    scan_repository,
    extract_project_metadata,
    categorize_directories,
    detect_languages,
    extract_from_package_json,
    extract_from_setup_py,
    extract_from_pyproject_toml,
    extract_from_readme,
    find_key_files,
    get_file_language,
    is_source_directory,
    is_test_directory,
    is_documentation_directory
)


@pytest.fixture
def temp_repo():
    """Create a temporary repository structure for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        
        # Create directory structure
        (repo_path / "src").mkdir()
        (repo_path / "tests").mkdir()
        (repo_path / "docs").mkdir()
        (repo_path / "build").mkdir()
        (repo_path / ".git").mkdir()
        
        # Create files
        (repo_path / "README.md").write_text("# Test Project\nThis is a test project.")
        (repo_path / "LICENSE").write_text("MIT License")
        (repo_path / "src" / "main.py").write_text("print('hello')")
        (repo_path / "tests" / "test_main.py").write_text("def test_main(): pass")
        (repo_path / "docs" / "guide.md").write_text("# User Guide")
        (repo_path / "package.json").write_text('{"name": "test-project", "version": "1.0.0"}')
        
        yield repo_path


class TestScanRepository:
    """Test the scan_repository function."""
    
    def test_scan_repository_basic(self, temp_repo):
        """Test basic repository scanning."""
        result = scan_repository(temp_repo)
        
        assert result["project_name"] == temp_repo.name
        assert "src" in result["directories"]
        assert "tests" in result["directories"]
        assert "docs" in result["directories"]
        assert "README.md" in result["files"]
        assert "src/main.py" in result["files"]
        assert "Python" in result["languages"]
        assert result["file_count"] > 0
    
    def test_scan_repository_nonexistent(self):
        """Test scanning a non-existent repository."""
        with pytest.raises(FileNotFoundError):
            scan_repository("/nonexistent/path")
    
    def test_scan_repository_exclude_dirs(self, temp_repo):
        """Test repository scanning with excluded directories."""
        result = scan_repository(temp_repo, exclude_dirs={"docs"})
        
        assert "docs" not in result["directories"]
        assert "docs/guide.md" not in result["files"]
    
    def test_scan_repository_metadata_extraction(self, temp_repo):
        """Test that metadata is extracted during scanning."""
        result = scan_repository(temp_repo)
        
        # Should extract from package.json
        assert result["project_name"] == "test-project"


class TestExtractProjectMetadata:
    """Test the extract_project_metadata function."""
    
    def test_extract_project_metadata(self, temp_repo):
        """Test extracting project metadata from various sources."""
        result = extract_project_metadata(temp_repo)
        
        assert result["project_name"] == "test-project"
        assert result["description"] == "This is a test project."  # From README
    
    def test_extract_project_metadata_empty_repo(self):
        """Test extracting metadata from empty repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = extract_project_metadata(tmpdir)
            assert result["project_name"] == Path(tmpdir).name


class TestCategorizeDirectories:
    """Test the categorize_directories function."""
    
    def test_categorize_directories(self, temp_repo):
        """Test directory categorization."""
        result = categorize_directories(temp_repo)
        
        assert "src" in result["source"]
        assert "tests" in result["test"]
        assert "docs" in result["documentation"]
        assert "build" in result["build"]


class TestDetectLanguages:
    """Test the detect_languages function."""
    
    def test_detect_languages(self, temp_repo):
        """Test language detection."""
        result = detect_languages(temp_repo)
        
        assert "Python" in result
        assert "Markdown" in result
        assert result["Python"] >= 1  # At least one Python file


class TestExtractFromPackageJson:
    """Test the extract_from_package_json function."""
    
    def test_extract_from_package_json_basic(self):
        """Test extracting basic information from package.json."""
        package_data = {
            "name": "test-package",
            "version": "1.2.3",
            "description": "A test package",
            "author": "Test Author",
            "license": "MIT",
            "repository": "https://github.com/test/repo",
            "dependencies": {"lodash": "^4.0.0"},
            "devDependencies": {"jest": "^27.0.0"}
        }
        
        metadata = {}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(package_data, f)
            f.flush()
            
            extract_from_package_json(f.name, metadata)
            
        os.unlink(f.name)
        
        assert metadata["project_name"] == "test-package"
        assert metadata["version"] == "1.2.3"
        assert metadata["description"] == "A test package"
        assert metadata["author"] == "Test Author"
        assert metadata["license"] == "MIT"
        assert metadata["repo_url"] == "https://github.com/test/repo"
        assert metadata["dependencies"] == ["lodash"]
        assert metadata["dev_dependencies"] == ["jest"]
    
    def test_extract_from_package_json_author_object(self):
        """Test extracting author when it's an object."""
        package_data = {
            "name": "test-package",
            "author": {"name": "Test Author", "email": "test@example.com"}
        }
        
        metadata = {}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(package_data, f)
            f.flush()
            
            extract_from_package_json(f.name, metadata)
            
        os.unlink(f.name)
        
        assert metadata["author"] == "Test Author"
    
    def test_extract_from_package_json_repository_object(self):
        """Test extracting repository when it's an object."""
        package_data = {
            "name": "test-package",
            "repository": {"type": "git", "url": "https://github.com/test/repo"}
        }
        
        metadata = {}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(package_data, f)
            f.flush()
            
            extract_from_package_json(f.name, metadata)
            
        os.unlink(f.name)
        
        assert metadata["repo_url"] == "https://github.com/test/repo"


class TestExtractFromSetupPy:
    """Test the extract_from_setup_py function."""
    
    def test_extract_from_setup_py(self):
        """Test extracting information from setup.py."""
        setup_content = '''
setup(
    name="test-package",
    version="1.0.0",
    description="A test package",
    author="Test Author",
    license="MIT",
    url="https://github.com/test/repo",
    install_requires=["requests", "click"]
)
'''
        
        metadata = {}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(setup_content)
            f.flush()
            
            extract_from_setup_py(f.name, metadata)
            
        os.unlink(f.name)
        
        assert metadata["project_name"] == "test-package"
        assert metadata["version"] == "1.0.0"
        assert metadata["description"] == "A test package"
        assert metadata["author"] == "Test Author"
        assert metadata["license"] == "MIT"
        assert metadata["repo_url"] == "https://github.com/test/repo"
        assert metadata["dependencies"] == ["requests", "click"]


class TestExtractFromReadme:
    """Test the extract_from_readme function."""
    
    def test_extract_from_readme_basic(self):
        """Test extracting information from README."""
        readme_content = """# My Awesome Project

This is a really great project that does amazing things.

## Installation

Run `pip install awesome-project`
"""
        
        metadata = {}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(readme_content)
            f.flush()
            
            extract_from_readme(f.name, metadata)
            
        os.unlink(f.name)
        
        assert metadata["project_name"] == "My Awesome Project"
        assert "really great project" in metadata["description"]
    
    def test_extract_from_readme_no_overwrite(self):
        """Test that README extraction doesn't overwrite existing metadata."""
        readme_content = "# New Project Name\nSome description"
        
        metadata = {"project_name": "Existing Name"}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write(readme_content)
            f.flush()
            
            extract_from_readme(f.name, metadata)
            
        os.unlink(f.name)
        
        # Should not overwrite existing project name
        assert metadata["project_name"] == "Existing Name"


class TestFindKeyFiles:
    """Test the find_key_files function."""
    
    def test_find_key_files(self, temp_repo):
        """Test finding key files in repository."""
        result = find_key_files(temp_repo)
        
        assert "readme" in result
        assert result["readme"] == "README.md"
        assert "license" in result
        assert result["license"] == "LICENSE"


class TestGetFileLanguage:
    """Test the get_file_language function."""
    
    def test_get_file_language_python(self):
        """Test detecting Python language."""
        assert get_file_language("script.py") == "Python"
        assert get_file_language("/path/to/script.py") == "Python"
    
    def test_get_file_language_javascript(self):
        """Test detecting JavaScript language."""
        assert get_file_language("app.js") == "JavaScript"
        assert get_file_language("component.jsx") == "React"
    
    def test_get_file_language_docker(self):
        """Test detecting Docker files."""
        assert get_file_language("Dockerfile") == "Docker"
        assert get_file_language("dockerfile") == "Docker"
    
    def test_get_file_language_unknown(self):
        """Test handling unknown file types."""
        assert get_file_language("unknown.xyz") is None
        assert get_file_language("no_extension") is None


class TestDirectoryClassification:
    """Test directory classification functions."""
    
    def test_is_source_directory(self):
        """Test source directory detection."""
        assert is_source_directory("src")
        assert is_source_directory("lib")
        assert is_source_directory("app")
        assert not is_source_directory("tests")
        assert not is_source_directory("docs")
    
    def test_is_test_directory(self):
        """Test test directory detection."""
        assert is_test_directory("test")
        assert is_test_directory("tests")
        assert is_test_directory("__tests__")
        assert not is_test_directory("src")
        assert not is_test_directory("docs")
    
    def test_is_documentation_directory(self):
        """Test documentation directory detection."""
        assert is_documentation_directory("docs")
        assert is_documentation_directory("doc")
        assert is_documentation_directory("documentation")
        assert not is_documentation_directory("src")
        assert not is_documentation_directory("tests")


class TestPyprojectTomlExtraction:
    """Test pyproject.toml extraction functionality."""
    
    def test_extract_from_pyproject_toml_poetry(self):
        """Test extracting from pyproject.toml with Poetry configuration."""
        toml_content = """
[tool.poetry]
name = "test-package"
version = "0.1.0"
description = "A test package"
authors = ["Test Author <test@example.com>"]
license = "MIT"
repository = "https://github.com/test/repo"

[tool.poetry.dependencies]
python = "^3.8"
requests = "^2.25.0"
"""
        
        metadata = {}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()
            
            extract_from_pyproject_toml(f.name, metadata)
            
        os.unlink(f.name)
        
        assert metadata["project_name"] == "test-package"
        assert metadata["version"] == "0.1.0"
        assert metadata["description"] == "A test package"
        assert metadata["license"] == "MIT"
        assert metadata["repo_url"] == "https://github.com/test/repo"
    
    def test_extract_from_pyproject_toml_setuptools(self):
        """Test extracting from pyproject.toml with setuptools configuration."""
        toml_content = """
[project]
name = "test-package"
version = "0.1.0"
description = "A test package"
authors = [{name = "Test Author", email = "test@example.com"}]
license = {text = "MIT"}

[project.urls]
repository = "https://github.com/test/repo"
"""
        
        metadata = {}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
            f.write(toml_content)
            f.flush()
            
            extract_from_pyproject_toml(f.name, metadata)
            
        os.unlink(f.name)
        
        assert metadata["project_name"] == "test-package"
        assert metadata["version"] == "0.1.0"
        assert metadata["description"] == "A test package"