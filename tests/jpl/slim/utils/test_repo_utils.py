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
    extract_from_pom_xml,
    extract_from_build_gradle,
    extract_from_cargo_toml,
    extract_from_go_mod,
    extract_from_composer_json,
    extract_from_gemfile,
    extract_from_csproj,
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


@pytest.fixture
def temp_java_maven_repo():
    """Create a temporary Java Maven repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        
        # Create Maven directory structure
        (repo_path / "src" / "main" / "java" / "com" / "example").mkdir(parents=True)
        (repo_path / "src" / "test" / "java" / "com" / "example").mkdir(parents=True)
        (repo_path / "src" / "main" / "resources").mkdir(parents=True)
        (repo_path / "target").mkdir()
        
        # Create pom.xml
        pom_content = """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
    <modelVersion>4.0.0</modelVersion>
    <groupId>com.example</groupId>
    <artifactId>test-project</artifactId>
    <version>1.0.0</version>
    <description>A test Java project</description>
    <url>https://github.com/example/test-project</url>
    <licenses>
        <license>
            <name>Apache License 2.0</name>
        </license>
    </licenses>
    <dependencies>
        <dependency>
            <groupId>junit</groupId>
            <artifactId>junit</artifactId>
            <version>4.13.2</version>
        </dependency>
    </dependencies>
</project>"""
        (repo_path / "pom.xml").write_text(pom_content)
        
        # Create Java files
        (repo_path / "src" / "main" / "java" / "com" / "example" / "Main.java").write_text(
            "package com.example;\npublic class Main {}"
        )
        (repo_path / "src" / "test" / "java" / "com" / "example" / "MainTest.java").write_text(
            "package com.example;\npublic class MainTest {}"
        )
        
        yield repo_path


@pytest.fixture
def temp_java_gradle_repo():
    """Create a temporary Java Gradle repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        
        # Create Gradle directory structure
        (repo_path / "src" / "main" / "java").mkdir(parents=True)
        (repo_path / "src" / "test" / "java").mkdir(parents=True)
        (repo_path / "build").mkdir()
        
        # Create build.gradle
        gradle_content = """
group = 'com.example'
version = '1.0.0'

dependencies {
    implementation 'org.springframework:spring-core:5.3.0'
    testImplementation 'junit:junit:4.13.2'
}
"""
        (repo_path / "build.gradle").write_text(gradle_content)
        
        # Create settings.gradle
        (repo_path / "settings.gradle").write_text("rootProject.name = 'gradle-test-project'")
        
        yield repo_path


@pytest.fixture
def temp_rust_repo():
    """Create a temporary Rust repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        
        # Create Rust directory structure
        (repo_path / "src").mkdir()
        (repo_path / "target").mkdir()
        
        # Create Cargo.toml
        cargo_content = """[package]
name = "test-rust-project"
version = "0.1.0"
description = "A test Rust project"
authors = ["Test Author <test@example.com>"]
license = "MIT"
repository = "https://github.com/example/test-rust-project"

[dependencies]
serde = "1.0"
tokio = { version = "1.0", features = ["full"] }

[dev-dependencies]
mockall = "0.11"
"""
        (repo_path / "Cargo.toml").write_text(cargo_content)
        
        # Create Rust files
        (repo_path / "src" / "main.rs").write_text("fn main() { println!(\"Hello\"); }")
        (repo_path / "src" / "lib.rs").write_text("pub fn add(a: i32, b: i32) -> i32 { a + b }")
        
        yield repo_path


@pytest.fixture
def temp_go_repo():
    """Create a temporary Go repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        
        # Create Go directory structure
        (repo_path / "cmd" / "app").mkdir(parents=True)
        (repo_path / "pkg" / "utils").mkdir(parents=True)
        (repo_path / "internal" / "config").mkdir(parents=True)
        
        # Create go.mod
        go_mod_content = """module github.com/example/test-go-project

go 1.20

require (
    github.com/gin-gonic/gin v1.9.0
    github.com/stretchr/testify v1.8.0
)
"""
        (repo_path / "go.mod").write_text(go_mod_content)
        
        # Create Go files
        (repo_path / "cmd" / "app" / "main.go").write_text("package main\nfunc main() {}")
        (repo_path / "pkg" / "utils" / "helpers.go").write_text("package utils")
        
        yield repo_path


@pytest.fixture
def temp_php_repo():
    """Create a temporary PHP repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        
        # Create PHP directory structure
        (repo_path / "src").mkdir()
        (repo_path / "tests").mkdir()
        (repo_path / "vendor").mkdir()
        
        # Create composer.json
        composer_content = """{
    "name": "example/test-php-project",
    "description": "A test PHP project",
    "version": "1.0.0",
    "license": "MIT",
    "authors": [
        {
            "name": "Test Author",
            "email": "test@example.com"
        }
    ],
    "homepage": "https://github.com/example/test-php-project",
    "require": {
        "php": ">=7.4",
        "symfony/console": "^5.0",
        "guzzlehttp/guzzle": "^7.0"
    },
    "require-dev": {
        "phpunit/phpunit": "^9.0"
    }
}"""
        (repo_path / "composer.json").write_text(composer_content)
        
        # Create PHP files
        (repo_path / "src" / "App.php").write_text("<?php\nnamespace Example;\nclass App {}")
        (repo_path / "tests" / "AppTest.php").write_text("<?php\nclass AppTest {}")
        
        yield repo_path


@pytest.fixture
def temp_ruby_repo():
    """Create a temporary Ruby repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        
        # Create Ruby directory structure
        (repo_path / "lib").mkdir()
        (repo_path / "spec").mkdir()
        
        # Create Gemfile
        gemfile_content = """source 'https://rubygems.org'

gemspec

gem 'rails', '~> 7.0'
gem 'puma', '~> 5.0'
gem 'sqlite3', '~> 1.4'

group :development, :test do
  gem 'rspec-rails'
  gem 'pry'
end
"""
        (repo_path / "Gemfile").write_text(gemfile_content)
        
        # Create .gemspec file
        gemspec_content = """Gem::Specification.new do |spec|
  spec.name          = "test-ruby-gem"
  spec.version       = "0.1.0"
  spec.summary       = "A test Ruby gem"
  spec.description   = "This is a test Ruby gem for testing purposes"
  spec.authors       = ["Test Author"]
  spec.email         = ["test@example.com"]
  spec.homepage      = "https://github.com/example/test-ruby-gem"
  spec.license       = "MIT"
end
"""
        (repo_path / "test-ruby-gem.gemspec").write_text(gemspec_content)
        
        # Create Ruby files
        (repo_path / "lib" / "main.rb").write_text("class Main\nend")
        (repo_path / "spec" / "main_spec.rb").write_text("require 'spec_helper'")
        
        yield repo_path


@pytest.fixture
def temp_dotnet_repo():
    """Create a temporary .NET repository for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        
        # Create .NET directory structure
        (repo_path / "Controllers").mkdir()
        (repo_path / "Models").mkdir()
        (repo_path / "Views").mkdir()
        (repo_path / "bin").mkdir()
        (repo_path / "obj").mkdir()
        
        # Create .csproj file
        csproj_content = """<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net6.0</TargetFramework>
    <AssemblyName>TestDotNetProject</AssemblyName>
    <Version>1.0.0</Version>
    <Description>A test .NET project</Description>
    <Authors>Test Author</Authors>
    <PackageLicenseExpression>MIT</PackageLicenseExpression>
    <RepositoryUrl>https://github.com/example/test-dotnet-project</RepositoryUrl>
  </PropertyGroup>
  <ItemGroup>
    <PackageReference Include="Microsoft.AspNetCore.Mvc" Version="2.2.0" />
    <PackageReference Include="Newtonsoft.Json" Version="13.0.1" />
  </ItemGroup>
</Project>"""
        (repo_path / "TestDotNetProject.csproj").write_text(csproj_content)
        
        # Create C# files
        (repo_path / "Program.cs").write_text("namespace TestApp { class Program { } }")
        (repo_path / "Controllers" / "HomeController.cs").write_text("namespace TestApp.Controllers { }")
        
        yield repo_path


@pytest.fixture
def temp_polyglot_repo():
    """Create a repository with multiple languages."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        
        # Create mixed structure
        (repo_path / "backend" / "src").mkdir(parents=True)
        (repo_path / "frontend" / "src").mkdir(parents=True)
        (repo_path / "scripts").mkdir()
        
        # Backend: Python
        (repo_path / "backend" / "requirements.txt").write_text("flask==2.0.0\npytest==7.0.0")
        (repo_path / "backend" / "src" / "app.py").write_text("from flask import Flask")
        
        # Frontend: JavaScript
        (repo_path / "frontend" / "package.json").write_text('{"name": "frontend", "version": "1.0.0"}')
        (repo_path / "frontend" / "src" / "index.js").write_text("console.log('Hello');")
        
        # Scripts: Shell
        (repo_path / "scripts" / "deploy.sh").write_text("#!/bin/bash\necho 'Deploying...'")
        
        # Documentation
        (repo_path / "README.md").write_text("# Polyglot Project\nMulti-language project")
        
        yield repo_path


@pytest.fixture
def temp_docs_only_repo():
    """Create a repository with only documentation files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir)
        
        # Create docs structure
        (repo_path / "docs").mkdir()
        (repo_path / "guides").mkdir()
        
        # Create various doc files
        (repo_path / "README.md").write_text("# Documentation Project\nThis is a docs-only repo")
        (repo_path / "LICENSE").write_text("MIT License")
        (repo_path / "CONTRIBUTING.md").write_text("# Contributing Guidelines")
        (repo_path / "docs" / "getting-started.md").write_text("# Getting Started")
        (repo_path / "docs" / "api-reference.md").write_text("# API Reference")
        (repo_path / "guides" / "user-guide.txt").write_text("User Guide\n==========")
        (repo_path / "CHANGELOG.txt").write_text("Version 1.0.0\n- Initial release")
        (repo_path / "notes.txt").write_text("Some plain text notes")
        
        yield repo_path


class TestScanRepository:
    """Test the scan_repository function."""
    
    def test_scan_repository_basic(self, temp_repo):
        """Test basic repository scanning."""
        result = scan_repository(temp_repo)
        
        assert result["project_name"] == "test-project"  # From package.json
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
    
    def test_extract_project_metadata_java_maven(self, temp_java_maven_repo):
        """Test extracting metadata from Java Maven project."""
        result = extract_project_metadata(temp_java_maven_repo)
        
        assert result["project_name"] == "test-project"
        assert result["version"] == "1.0.0"
        assert result["description"] == "A test Java project"
        assert result["org_name"] == "com.example"
        assert result["repo_url"] == "https://github.com/example/test-project"
        assert result["license"] == "Apache License 2.0"
        assert "junit" in result["dependencies"]
    
    def test_extract_project_metadata_java_gradle(self, temp_java_gradle_repo):
        """Test extracting metadata from Java Gradle project."""
        result = extract_project_metadata(temp_java_gradle_repo)
        
        assert result["project_name"] == "gradle-test-project"
        assert result["version"] == "1.0.0"
        assert result["org_name"] == "com.example"
        assert "org.springframework:spring-core" in result["dependencies"]
    
    def test_extract_project_metadata_rust(self, temp_rust_repo):
        """Test extracting metadata from Rust project."""
        result = extract_project_metadata(temp_rust_repo)
        
        assert result["project_name"] == "test-rust-project"
        assert result["version"] == "0.1.0"
        assert result["description"] == "A test Rust project"
        assert result["author"] == "Test Author <test@example.com>"
        assert result["license"] == "MIT"
        assert result["repo_url"] == "https://github.com/example/test-rust-project"
        assert "serde" in result["dependencies"]
        assert "mockall" in result["dev_dependencies"]
    
    def test_extract_project_metadata_go(self, temp_go_repo):
        """Test extracting metadata from Go project."""
        result = extract_project_metadata(temp_go_repo)
        
        assert result["project_name"] == "test-go-project"
        assert result["repo_url"] == "https://github.com/example/test-go-project"
        assert "github.com/gin-gonic/gin" in result["dependencies"]
        assert "github.com/stretchr/testify" in result["dependencies"]
    
    def test_extract_project_metadata_php(self, temp_php_repo):
        """Test extracting metadata from PHP project."""
        result = extract_project_metadata(temp_php_repo)
        
        assert result["project_name"] == "test-php-project"
        assert result["version"] == "1.0.0"
        assert result["description"] == "A test PHP project"
        assert result["author"] == "Test Author"
        assert result["license"] == "MIT"
        assert result["repo_url"] == "https://github.com/example/test-php-project"
        assert "symfony/console" in result["dependencies"]
        assert "phpunit/phpunit" in result["dev_dependencies"]
    
    def test_extract_project_metadata_ruby(self, temp_ruby_repo):
        """Test extracting metadata from Ruby project."""
        result = extract_project_metadata(temp_ruby_repo)
        
        assert result["project_name"] == "test-ruby-gem"
        assert result["version"] == "0.1.0"
        assert result["description"] == "This is a test Ruby gem for testing purposes"
        assert "rails" in result["dependencies"]
        assert "puma" in result["dependencies"]
    
    def test_extract_project_metadata_dotnet(self, temp_dotnet_repo):
        """Test extracting metadata from .NET project."""
        result = extract_project_metadata(temp_dotnet_repo)
        
        assert result["project_name"] == "TestDotNetProject"
        assert result["version"] == "1.0.0"
        assert result["description"] == "A test .NET project"
        assert result["author"] == "Test Author"
        assert result["license"] == "MIT"
        assert result["repo_url"] == "https://github.com/example/test-dotnet-project"
        assert "Microsoft.AspNetCore.Mvc" in result["dependencies"]
        assert "Newtonsoft.Json" in result["dependencies"]
    
    def test_extract_project_metadata_polyglot(self, temp_polyglot_repo):
        """Test extracting metadata from multi-language project."""
        result = extract_project_metadata(temp_polyglot_repo)
        
        # Should find the README
        assert result["project_name"] == "Polyglot Project"
        assert "Multi-language project" in result["description"]


class TestCategorizeDirectories:
    """Test the categorize_directories function."""
    
    def test_categorize_directories(self, temp_repo):
        """Test directory categorization."""
        result = categorize_directories(temp_repo)
        
        assert "src" in result["source"]
        assert "tests" in result["test"]
        assert "docs" in result["documentation"]
        assert "build" in result["build"]
    
    def test_categorize_directories_java_maven(self, temp_java_maven_repo):
        """Test categorization of Java Maven directories."""
        result = categorize_directories(temp_java_maven_repo)
        
        # Should find nested source directories
        assert any("src/main/java" in path for path in result["source"])
        assert any("src/test/java" in path for path in result["test"])
        assert "target" in result["build"]
    
    def test_categorize_directories_go(self, temp_go_repo):
        """Test categorization of Go directories."""
        result = categorize_directories(temp_go_repo)
        
        assert "cmd" in result["source"]
        assert "pkg" in result["source"]
        assert "internal" in result["source"]
    
    def test_categorize_directories_dotnet(self, temp_dotnet_repo):
        """Test categorization of .NET directories."""
        result = categorize_directories(temp_dotnet_repo)
        
        assert "Controllers" in result["source"]
        assert "Models" in result["source"]
        assert "Views" in result["source"]
        assert "bin" in result["build"]
        assert "obj" in result["build"]


class TestDetectLanguages:
    """Test the detect_languages function."""
    
    def test_detect_languages(self, temp_repo):
        """Test language detection."""
        result = detect_languages(temp_repo)
        
        assert "Python" in result
        assert "Markdown" in result
        assert result["Python"] >= 1  # At least one Python file
    
    def test_detect_languages_comprehensive(self):
        """Test detection of all supported languages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Create files for each supported language
            test_files = {
                "script.py": "Python",
                "app.js": "JavaScript",
                "Component.jsx": "React",
                "app.ts": "TypeScript",
                "Component.tsx": "React",
                "Main.java": "Java",
                "program.c": "C",
                "program.cpp": "C++",
                "header.h": "C/C++",
                "main.go": "Go",
                "lib.rs": "Rust",
                "script.rb": "Ruby",
                "index.php": "PHP",
                "app.swift": "Swift",
                "Main.kt": "Kotlin",
                "App.scala": "Scala",
                "Program.cs": "C#",
                "analysis.r": "R",
                "deploy.sh": "Shell",
                "index.html": "HTML",
                "styles.css": "CSS",
                "styles.scss": "SCSS",
                "doc.md": "Markdown",
                "config.json": "JSON",
                "data.xml": "XML",
                "config.yaml": "YAML",
                "settings.toml": "TOML",
                "query.sql": "SQL",
                "Dockerfile": "Docker",
                "notes.txt": "Text",
                "doc.rst": "reStructuredText",
                "manual.tex": "LaTeX",
                "app.properties": "Properties",
                "config.ini": "INI",
                ".env": "Environment"
            }
            
            for filename, expected_lang in test_files.items():
                (repo_path / filename).write_text("test content")
            
            result = detect_languages(repo_path)
            
            # Check that all languages are detected
            for filename, expected_lang in test_files.items():
                assert expected_lang in result, f"Failed to detect {expected_lang} from {filename}"
                assert result[expected_lang] >= 1
    
    def test_detect_languages_java_project(self, temp_java_maven_repo):
        """Test language detection in Java project."""
        result = detect_languages(temp_java_maven_repo)
        
        assert "Java" in result
        assert "XML" in result  # pom.xml
        assert result["Java"] == 2  # Main.java and MainTest.java
    
    def test_detect_languages_polyglot(self, temp_polyglot_repo):
        """Test language detection in multi-language project."""
        result = detect_languages(temp_polyglot_repo)
        
        assert "Python" in result
        assert "JavaScript" in result
        assert "Shell" in result
        assert "Markdown" in result
    
    def test_detect_languages_docs_only(self, temp_docs_only_repo):
        """Test language detection in documentation-only repository."""
        result = detect_languages(temp_docs_only_repo)
        
        assert "Markdown" in result
        assert "Text" in result
        # Should not detect any programming languages
        assert "Python" not in result
        assert "Java" not in result
        assert "JavaScript" not in result


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
    
    def test_find_key_files_variations(self):
        """Test finding key files with various naming conventions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Create various file variations
            (repo_path / "readme.txt").write_text("readme")
            (repo_path / "LICENSE.md").write_text("license")
            (repo_path / "CONTRIBUTING.md").write_text("contributing")
            (repo_path / "CHANGELOG.txt").write_text("changelog")
            
            result = find_key_files(repo_path)
            
            assert result["readme"] == "readme.txt"
            assert result["license"] == "LICENSE.md"
            assert result["contributing"] == "CONTRIBUTING.md"
            assert result["changelog"] == "CHANGELOG.txt"
    
    def test_find_key_files_case_insensitive(self):
        """Test case-insensitive detection of key files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Create files with different cases
            (repo_path / "ReAdMe.md").write_text("readme")
            (repo_path / "LiCeNsE.txt").write_text("license")
            (repo_path / "COPYING").write_text("copying")
            (repo_path / "COPYRIGHT.md").write_text("copyright")
            
            result = find_key_files(repo_path)
            
            assert result["readme"] == "ReAdMe.md"
            assert result["license"] in ["LiCeNsE.txt", "COPYING", "COPYRIGHT.md"]
    
    def test_find_key_files_priority(self):
        """Test that root directory files are preferred over nested ones."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Create nested structure
            (repo_path / "docs").mkdir()
            (repo_path / "docs" / "README.md").write_text("nested readme")
            (repo_path / "README.md").write_text("root readme")
            
            result = find_key_files(repo_path)
            
            # Should prefer the root README
            assert result["readme"] == "README.md"
    
    def test_find_key_files_special_names(self):
        """Test finding files with special names."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Create special files
            (repo_path / "README").write_text("no extension")
            (repo_path / "LICENSE").write_text("no extension")
            (repo_path / "AUTHORS.md").write_text("authors")
            (repo_path / "SECURITY.md").write_text("security")
            (repo_path / "CODE_OF_CONDUCT.md").write_text("code of conduct")
            
            result = find_key_files(repo_path)
            
            assert result["readme"] == "README"
            assert result["license"] == "LICENSE"
            assert result["authors"] == "AUTHORS.md"
            assert result["security"] == "SECURITY.md"
            assert result["code_of_conduct"] == "CODE_OF_CONDUCT.md"


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
        assert get_file_language("Dockerfile.dev") == "Docker"
        assert get_file_language("Dockerfile.prod") == "Docker"
    
    def test_get_file_language_unknown(self):
        """Test handling unknown file types."""
        assert get_file_language("unknown.xyz") is None
        assert get_file_language("no_extension") is None
    
    def test_get_file_language_all_extensions(self):
        """Test all supported file extensions."""
        test_cases = {
            # Programming languages
            "script.py": "Python",
            "app.js": "JavaScript",
            "Component.jsx": "React",
            "app.ts": "TypeScript",
            "Component.tsx": "React",
            "Main.java": "Java",
            "program.c": "C",
            "program.cpp": "C++",
            "program.cxx": "C++",
            "program.cc": "C++",
            "header.h": "C/C++",
            "header.hpp": "C++",
            "main.go": "Go",
            "lib.rs": "Rust",
            "script.rb": "Ruby",
            "index.php": "PHP",
            "app.swift": "Swift",
            "Main.kt": "Kotlin",
            "App.scala": "Scala",
            "Program.cs": "C#",
            "analysis.r": "R",
            "script.sh": "Shell",
            "script.bash": "Shell",
            "script.zsh": "Shell",
            "script.fish": "Shell",
            
            # Web technologies
            "index.html": "HTML",
            "index.htm": "HTML",
            "styles.css": "CSS",
            "styles.scss": "SCSS",
            "styles.sass": "Sass",
            "styles.less": "Less",
            
            # Data/Config formats
            "doc.md": "Markdown",
            "doc.markdown": "Markdown",
            "config.json": "JSON",
            "data.xml": "XML",
            "config.yaml": "YAML",
            "config.yml": "YAML",
            "settings.toml": "TOML",
            "query.sql": "SQL",
            
            # Documentation formats
            "notes.txt": "Text",
            "notes.text": "Text",
            "doc.rst": "reStructuredText",
            "doc.adoc": "AsciiDoc",
            "doc.asciidoc": "AsciiDoc",
            "doc.pod": "Pod",
            "manual.tex": "LaTeX",
            "manual.latex": "LaTeX",
            
            # Config files
            "app.properties": "Properties",
            "config.ini": "INI",
            "app.cfg": "Config",
            "app.conf": "Config",
            ".env": "Environment"
        }
        
        for filename, expected_lang in test_cases.items():
            assert get_file_language(filename) == expected_lang, f"Failed for {filename}"
    
    def test_get_file_language_case_insensitive(self):
        """Test case-insensitive extension detection."""
        assert get_file_language("Script.PY") == "Python"
        assert get_file_language("App.JS") == "JavaScript"
        assert get_file_language("Main.JAVA") == "Java"
    
    def test_get_file_language_special_files(self):
        """Test special file name detection."""
        special_files = {
            "Makefile": "Makefile",
            "makefile": "Makefile",
            "GNUmakefile": "Makefile",
            "Rakefile": "Ruby",
            "Gemfile": "Ruby",
            "Jenkinsfile": "Groovy",
            "gulpfile.js": "JavaScript",
            "webpack.config.js": "JavaScript",
            "CMakeLists.txt": "CMake",
            "build.gradle": "Gradle",
            "build.gradle.kts": "Kotlin"
        }
        
        for filename, expected_lang in special_files.items():
            assert get_file_language(filename) == expected_lang, f"Failed for {filename}"
    
    def test_get_file_language_shebang_detection(self):
        """Test shebang detection for files without extensions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Python shebang
            python_script = Path(tmpdir) / "script"
            python_script.write_text("#!/usr/bin/env python\nprint('hello')")
            assert get_file_language(python_script) == "Python"
            
            # Ruby shebang
            ruby_script = Path(tmpdir) / "rubyapp"
            ruby_script.write_text("#!/usr/bin/ruby\nputs 'hello'")
            assert get_file_language(ruby_script) == "Ruby"
            
            # Shell shebang
            shell_script = Path(tmpdir) / "deploy"
            shell_script.write_text("#!/bin/bash\necho 'hello'")
            assert get_file_language(shell_script) == "Shell"
            
            # Node.js shebang
            node_script = Path(tmpdir) / "server"
            node_script.write_text("#!/usr/bin/env node\nconsole.log('hello')")
            assert get_file_language(node_script) == "JavaScript"


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


class TestNonCodeRepositories:
    """Test handling of repositories with no code, only documentation or text files."""
    
    def test_scan_docs_only_repo(self, temp_docs_only_repo):
        """Test scanning a documentation-only repository."""
        result = scan_repository(temp_docs_only_repo)
        
        assert result["project_name"] == "Documentation Project"
        assert "This is a docs-only repo" in result["description"]
        assert "Markdown" in result["languages"]
        assert "Text" in result["languages"]
        assert len(result["files"]) >= 7  # All the doc files we created
        assert "readme" in result["key_files"]
        assert "license" in result["key_files"]
        assert "contributing" in result["key_files"]
        assert "changelog" in result["key_files"]
    
    def test_categorize_docs_only_repo(self, temp_docs_only_repo):
        """Test directory categorization for docs-only repository."""
        result = categorize_directories(temp_docs_only_repo)
        
        assert "docs" in result["documentation"]
        assert "guides" in result["other"]  # Not recognized as standard doc dir
        assert len(result["source"]) == 0  # No source directories
        assert len(result["test"]) == 0  # No test directories
    
    def test_empty_repository(self):
        """Test handling of completely empty repository."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = scan_repository(tmpdir)
            
            assert result["project_name"] == Path(tmpdir).name
            assert result["description"] == ""
            assert len(result["files"]) == 0
            assert len(result["directories"]) == 0
            assert len(result["languages"]) == 0
            assert result["file_count"] == 0
    
    def test_plain_text_only_repo(self):
        """Test repository with only plain text files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Create various text files
            (repo_path / "notes.txt").write_text("Some notes")
            (repo_path / "README").write_text("Plain text readme")
            (repo_path / "TODO").write_text("Todo list")
            (repo_path / "data.csv").write_text("col1,col2\n1,2\n3,4")
            
            result = scan_repository(repo_path)
            
            assert "Text" in result["languages"]
            assert result["file_count"] == 4
            assert "readme" in result["key_files"]
    
    def test_config_only_repo(self):
        """Test repository with only configuration files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Create various config files
            (repo_path / "config.json").write_text('{"key": "value"}')
            (repo_path / "settings.yaml").write_text("key: value")
            (repo_path / "app.toml").write_text("[section]\nkey = 'value'")
            (repo_path / ".env").write_text("KEY=value")
            (repo_path / "app.properties").write_text("key=value")
            
            result = detect_languages(repo_path)
            
            assert "JSON" in result
            assert "YAML" in result
            assert "TOML" in result
            assert "Environment" in result
            assert "Properties" in result
    
    def test_mixed_non_code_repo(self):
        """Test repository with mix of docs, configs, and text."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Create mixed content
            (repo_path / "README.md").write_text("# Project\nDocs and configs only")
            (repo_path / "config.json").write_text('{"name": "project"}')
            (repo_path / "notes.txt").write_text("Some notes")
            (repo_path / "LICENSE").write_text("MIT License")
            (repo_path / "data.xml").write_text("<root><item>data</item></root>")
            
            result = extract_project_metadata(repo_path)
            
            assert result["project_name"] == "Project"
            assert "Docs and configs only" in result["description"]
    
    def test_assets_only_repo(self):
        """Test repository with only assets (images, fonts, etc)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir)
            
            # Create directories
            (repo_path / "images").mkdir()
            (repo_path / "fonts").mkdir()
            (repo_path / "data").mkdir()
            
            # Create non-code files
            (repo_path / "images" / "logo.png").write_bytes(b"fake image data")
            (repo_path / "fonts" / "font.ttf").write_bytes(b"fake font data")
            (repo_path / "data" / "dataset.csv").write_text("col1,col2\n1,2")
            (repo_path / "README.md").write_text("# Assets Repository\nContains project assets")
            
            result = scan_repository(repo_path)
            
            assert result["project_name"] == "Assets Repository"
            assert "Contains project assets" in result["description"]
            assert result["file_count"] == 4
            # Should only detect Markdown from README
            assert "Markdown" in result["languages"]
            assert len(result["languages"]) == 1