"""
Simplified documentation generator using SLIM utils.

This module provides a lightweight orchestrator that leverages the utils layer
for repository analysis, AI enhancement, and template management.
"""

import logging
import os
import shutil
from typing import Dict, List, Optional, Tuple
from pathlib import Path

from jpl.slim.utils.repo_utils import scan_repository, extract_project_metadata
from jpl.slim.utils.ai_utils import enhance_content
from jpl.slim.utils.git_utils import extract_git_info, is_git_repository
from jpl.slim.best_practices.docs_website_impl.template_manager import TemplateManager
from jpl.slim.best_practices.docs_website_impl.config_updater import ConfigUpdater
from jpl.slim.best_practices.docs_website_impl.helpers import load_config, escape_mdx_special_characters, clean_api_doc, escape_yaml_value

__all__ = ["SlimDocGenerator"]


class SlimDocGenerator:
    """
    Simplified documentation generator that uses the utils layer.
    """
    
    def __init__(
        self, 
        target_repo_path: Optional[str],
        output_dir: str,
        template_repo: str = "https://github.com/NASA-AMMOS/slim-docsite-template.git",
        use_ai: Optional[str] = None,
        config_file: Optional[str] = None,
        verbose: bool = False,
        template_only: bool = False,
        revise_site: bool = False
    ):
        """
        Initialize the SLIM documentation generator.
        
        Args:
            target_repo_path: Path to the target repository to document
            output_dir: Directory where the documentation site will be generated
            template_repo: URL or path to the template repository
            use_ai: Optional AI model to use for content enhancement
            config_file: Optional path to configuration file
            verbose: Whether to enable verbose logging
            template_only: Whether to generate only the template structure
            revise_site: Whether to revise the site landing page
        """
        self.logger = logging.getLogger("slim-doc-generator")
        
        self.output_dir = Path(output_dir).resolve()
        self.template_repo = template_repo
        self.use_ai = use_ai
        self.config = load_config(config_file) if config_file else {}
        self.verbose = verbose
        self.template_only = template_only
        self.revise_site = revise_site
        
        # Initialize template manager and config updater
        self.template_manager = TemplateManager(template_repo, str(self.output_dir), self.logger)
        self.config_updater = ConfigUpdater(str(self.output_dir), self.logger)
        
        # Initialize target repo analysis if provided
        if target_repo_path:
            self.target_repo_path = Path(target_repo_path).resolve()
            
            if not self.target_repo_path.exists():
                raise ValueError(f"Target repository path does not exist: {target_repo_path}")
            
            self.logger.debug(f"Initialized SLIM Doc Generator for {self.target_repo_path.name}")
        else:
            self.target_repo_path = None
            self.logger.debug("Initialized SLIM Doc Generator in template-only mode")
    
    def generate(self) -> bool:
        """
        Generate the documentation site using simplified AI-driven flow.
        
        Returns:
            True if generation was successful, False otherwise
        """
        try:
            self.logger.debug("Starting documentation generation")
            
            # Step 1: Clone template to output directory
            if not self._setup_template():
                return False
            
            # Step 2: Analyze repository to extract basic information
            repo_info = self._analyze_repository() if self.target_repo_path else {}
            
            # Step 3: Replace universal placeholders (PROJECT_NAME, etc.)
            if not self._replace_basic_placeholders(repo_info):
                return False
            
            # Step 4: Use AI to fill [INSERT_CONTENT] markers in all markdown files
            if self.use_ai:
                if not self._ai_enhance_content(repo_info):
                    return False
            
            self.logger.debug("Documentation generation completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error during documentation generation: {str(e)}")
            return False
    
    def _setup_template(self) -> bool:
        """Setup the documentation template."""
        try:
            self.logger.debug("Setting up documentation template")
            return self.template_manager.clone_template()
        except Exception as e:
            self.logger.error(f"Error setting up template: {str(e)}")
            return False
    
    def _analyze_repository(self) -> Dict:
        """Analyze the target repository using utils."""
        try:
            self.logger.debug(f"Analyzing repository: {self.target_repo_path}")
            
            # Use repo_utils for comprehensive analysis
            repo_info = scan_repository(self.target_repo_path)
            
            # Add git-specific information if it's a git repo
            if is_git_repository(str(self.target_repo_path)):
                extract_git_info(str(self.target_repo_path), repo_info)
            
            self.logger.debug(f"Repository analysis complete: {len(repo_info.get('files', []))} files, "
                           f"{len(repo_info.get('languages', []))} languages detected")
            
            return repo_info
            
        except Exception as e:
            self.logger.error(f"Error analyzing repository: {str(e)}")
            return {}
    
    def _generate_content(self, repo_info: Dict) -> bool:
        """Generate documentation content."""
        try:
            self.logger.debug("Generating documentation content")
            
            # Define content sections to generate
            sections = [
                ("overview", "Overview"),
                ("installation", "Installation"),
                ("api", "API Reference"),
                ("development", "Development"),
                ("contributing", "Contributing"),
                ("changelog", "Changelog"),
                ("deployment", "Deployment"),
                ("architecture", "Architecture"),
                ("testing", "Testing"),
                ("security", "Security"),
                ("guides", "Guides")
            ]
            
            for section_key, section_name in sections:
                self.logger.debug(f"Generating {section_name} content")
                
                # Generate base content using repository information
                base_content = self._generate_section_content(section_key, repo_info)
                
                # Enhance with AI if enabled
                if self.use_ai and base_content:
                    enhanced_content = enhance_content(
                        content=base_content,
                        practice_type="docgen",
                        section_name=section_key,
                        model=self.use_ai
                    )
                    base_content = enhanced_content
                
                # Save content to appropriate file
                if base_content:
                    self._save_section_content(section_key, base_content)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error generating content: {str(e)}")
            return False
    
    def _generate_section_content(self, section_key: str, repo_info: Dict) -> str:
        """Generate base content for a specific section."""
        # This is a simplified implementation
        # In the full version, this would use the content generators
        
        if section_key == "overview":
            return self._generate_overview_content(repo_info)
        elif section_key == "installation":
            return self._generate_installation_content(repo_info)
        elif section_key == "api":
            return self._generate_api_content(repo_info)
        elif section_key == "development":
            return self._generate_development_content(repo_info)
        elif section_key == "contributing":
            return self._generate_contributing_content(repo_info)
        elif section_key == "changelog":
            return self._generate_changelog_content(repo_info)
        elif section_key == "deployment":
            return self._generate_deployment_content(repo_info)
        elif section_key == "architecture":
            return self._generate_architecture_content(repo_info)
        elif section_key == "testing":
            return self._generate_testing_content(repo_info)
        elif section_key == "security":
            return self._generate_security_content(repo_info)
        elif section_key == "guides":
            return self._generate_guides_content(repo_info)
        
        return ""
    
    def _generate_overview_content(self, repo_info: Dict) -> str:
        """Generate overview content."""
        project_name = repo_info.get('project_name', 'Project')
        description = repo_info.get('description', 'A software project')
        languages = repo_info.get('languages', [])
        
        content = f"""---
title: {escape_yaml_value(f"{project_name} Overview")}
---

# {project_name}

{description}

## Key Features

- Built with {', '.join(languages[:3]) if languages else 'modern technologies'}
- Comprehensive documentation
- Easy to use and extend

## Getting Started

To get started with {project_name}, see the [Installation Guide](./installation.md).

## Project Structure

This project is organized as follows:

"""
        
        # Add directory structure if available
        src_dirs = repo_info.get('src_dirs', [])
        test_dirs = repo_info.get('test_dirs', [])
        doc_dirs = repo_info.get('doc_dirs', [])
        
        if src_dirs:
            content += f"- **Source Code**: {', '.join(src_dirs[:3])}\n"
        if test_dirs:
            content += f"- **Tests**: {', '.join(test_dirs[:3])}\n"
        if doc_dirs:
            content += f"- **Documentation**: {', '.join(doc_dirs[:3])}\n"
        
        return content
    
    def _generate_installation_content(self, repo_info: Dict) -> str:
        """Generate installation content."""
        project_name = repo_info.get('project_name', 'Project')
        languages = repo_info.get('languages', [])
        
        content = f"""---
title: {escape_yaml_value("Installation Guide")}
---

# Installation

This guide will help you install and set up {project_name}.

## Prerequisites

"""
        
        if 'Python' in languages:
            content += "- Python 3.7 or higher\n"
        if 'JavaScript' in languages or 'TypeScript' in languages:
            content += "- Node.js 14 or higher\n- npm or yarn\n"
        if 'Java' in languages:
            content += "- Java 8 or higher\n- Maven or Gradle\n"
        
        content += """
## Installation Steps

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd """ + project_name.lower().replace(' ', '-') + """
   ```

2. Install dependencies:
"""
        
        if 'Python' in languages:
            content += """   ```bash
   pip install -r requirements.txt
   ```
"""
        if 'JavaScript' in languages or 'TypeScript' in languages:
            content += """   ```bash
   npm install
   # or
   yarn install
   ```
"""
        
        content += """
3. Run the application:
   ```bash
   # Add specific run commands here
   ```

## Verification

To verify the installation was successful:

```bash
# Add verification commands here
```
"""
        
        return content
    
    def _generate_api_content(self, repo_info: Dict) -> str:
        """Generate API documentation content."""
        project_name = repo_info.get('project_name', 'Project')
        
        content = f"""---
title: {escape_yaml_value("API Reference")}
---

# API Reference

This document provides a comprehensive reference for the {project_name} API.

## Overview

The {project_name} API provides programmatic access to core functionality.

## Authentication

<!-- Add authentication details here -->

## Endpoints

<!-- Add API endpoints documentation here -->

## Examples

<!-- Add usage examples here -->

## Error Handling

<!-- Add error handling information here -->
"""
        
        return content
    
    def _generate_development_content(self, repo_info: Dict) -> str:
        """Generate development guide content."""
        project_name = repo_info.get('project_name', 'Project')
        languages = repo_info.get('languages', [])
        
        content = f"""---
title: {escape_yaml_value("Development Guide")}
---

# Development Guide

This guide covers the development workflow for {project_name}.

## Development Environment

### Requirements

"""
        
        if 'Python' in languages:
            content += "- Python development environment\n"
        if 'JavaScript' in languages or 'TypeScript' in languages:
            content += "- Node.js development environment\n"
        
        content += """
### Setup

1. Clone the repository
2. Install development dependencies
3. Set up pre-commit hooks (if available)

## Code Structure

<!-- Add information about code organization -->

## Development Workflow

1. Create a feature branch
2. Make your changes
3. Run tests
4. Submit a pull request

## Testing

<!-- Add testing guidelines -->

## Code Style

<!-- Add code style guidelines -->
"""
        
        return content
    
    def _generate_contributing_content(self, repo_info: Dict) -> str:
        """Generate contributing guidelines content."""
        project_name = repo_info.get('project_name', 'Project')
        
        content = f"""---
title: {escape_yaml_value("Contributing Guide")}
---

# Contributing to {project_name}

We welcome contributions to {project_name}! This guide will help you get started.

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make your changes
5. Submit a pull request

## Development Setup

See the [Development Guide](./development.md) for detailed setup instructions.

## Guidelines

### Code Quality

- Write clean, readable code
- Add tests for new functionality
- Follow existing code style
- Update documentation as needed

### Pull Request Process

1. Ensure all tests pass
2. Update documentation if needed
3. Add a clear description of changes
4. Request review from maintainers

## Code of Conduct

<!-- Add code of conduct information -->

## Getting Help

<!-- Add information about getting help -->
"""
        
        return content
    
    def _generate_changelog_content(self, repo_info: Dict) -> str:
        """Generate changelog content."""
        project_name = repo_info.get('project_name', 'Project')
        
        content = f"""---
title: {escape_yaml_value("Changelog")}
---

# Changelog

All notable changes to {project_name} will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup
- Basic functionality implementation

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [1.0.0] - YYYY-MM-DD

### Added
- Initial release of {project_name}

<!-- Add new releases above this line -->
"""
        return content
    
    def _generate_deployment_content(self, repo_info: Dict) -> str:
        """Generate deployment content."""
        project_name = repo_info.get('project_name', 'Project')
        languages = repo_info.get('languages', [])
        
        content = f"""---
title: {escape_yaml_value("Deployment Guide")}
---

# Deployment Guide

This guide covers deploying {project_name} to various environments.

## Prerequisites

### System Requirements
- Operating System: Linux, macOS, or Windows
- Memory: 512MB minimum, 2GB recommended
- Disk Space: 1GB available space

### Dependencies
"""
        
        if 'Python' in languages:
            content += "- Python 3.7 or higher\n"
        if 'JavaScript' in languages or 'TypeScript' in languages:
            content += "- Node.js 14 or higher\n"
        if 'Java' in languages:
            content += "- Java 8 or higher\n"
        
        content += """
## Deployment Options

### Local Deployment

1. **Download and Setup**
   ```bash
   git clone <repository-url>
   cd """ + project_name.lower().replace(' ', '-') + """
   ```

2. **Install Dependencies**
   ```bash
   # Follow installation guide instructions
   ```

3. **Configuration**
   ```bash
   # Copy configuration template
   cp config.template.yml config.yml
   # Edit configuration as needed
   ```

4. **Start Application**
   ```bash
   # Add startup commands here
   ```

### Production Deployment

#### Docker Deployment

```dockerfile
# Example Dockerfile
FROM python:3.9-slim  # Adjust based on your stack
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt  # Adjust for your dependencies
EXPOSE 8000
CMD ["python", "app.py"]  # Adjust for your application
```

#### Environment Variables

```bash
# Required environment variables
export ENV=production
export LOG_LEVEL=info
# Add other environment variables as needed
```

## Monitoring and Maintenance

### Health Checks
- Application health endpoint: `/health`
- Database connection status
- External service connectivity

### Logging
- Application logs location: `/var/log/app/`
- Log rotation configuration
- Log level settings

### Backup and Recovery
- Database backup procedures
- Configuration backup
- Recovery procedures

## Troubleshooting

### Common Issues
1. **Port already in use**
   - Solution: Change port in configuration or stop conflicting service

2. **Permission denied**
   - Solution: Check file permissions and user privileges

3. **Database connection failed**
   - Solution: Verify database configuration and connectivity

### Getting Help
- Check application logs
- Review configuration settings
- Contact support team
"""
        return content
    
    def _generate_architecture_content(self, repo_info: Dict) -> str:
        """Generate architecture content."""
        project_name = repo_info.get('project_name', 'Project')
        languages = repo_info.get('languages', [])
        
        content = f"""---
title: {escape_yaml_value("Architecture Overview")}
---

# Architecture Overview

This document describes the high-level architecture of {project_name}.

## System Overview

{project_name} is designed with a modular architecture that promotes maintainability, scalability, and testability.

## Core Components

### Application Layer
- **Purpose**: Handles business logic and application workflows
- **Technologies**: {', '.join(languages[:3]) if languages else 'Modern technologies'}
- **Responsibilities**:
  - Business logic implementation
  - Data validation and processing
  - Workflow orchestration

### Data Layer
- **Purpose**: Manages data persistence and retrieval
- **Components**:
  - Data models and schemas
  - Database interactions
  - Data validation

### Interface Layer
- **Purpose**: Handles external interactions and APIs
- **Components**:
  - REST API endpoints
  - User interfaces
  - External service integrations

## Design Patterns

### Architectural Patterns
- **Modular Design**: Components are organized into distinct modules
- **Separation of Concerns**: Clear separation between different layers
- **Dependency Injection**: Loose coupling between components

### Code Patterns
- **Repository Pattern**: Data access abstraction
- **Factory Pattern**: Object creation management
- **Observer Pattern**: Event-driven communication

## Data Flow

1. **Request Processing**
   - User/API request received
   - Input validation and sanitization
   - Business logic execution
   - Data persistence (if required)
   - Response generation

2. **Error Handling**
   - Exception catching and logging
   - Error response formatting
   - Recovery mechanisms

## Security Architecture

### Authentication and Authorization
- User authentication mechanisms
- Role-based access control
- Session management

### Data Protection
- Input validation and sanitization
- SQL injection prevention
- Cross-site scripting (XSS) protection

## Performance Considerations

### Optimization Strategies
- Caching mechanisms
- Database query optimization
- Asynchronous processing
- Resource pooling

### Scalability
- Horizontal scaling capabilities
- Load balancing strategies
- Database scaling approaches

## Technology Stack

### Core Technologies
"""
        
        for lang in languages:
            content += f"- **{lang}**: [Description of usage]\n"
        
        content += """
### External Dependencies
- List of major external libraries and frameworks
- Database systems
- Third-party services

## Deployment Architecture

### Environment Structure
- Development environment
- Staging environment
- Production environment

### Infrastructure Components
- Application servers
- Database servers
- Load balancers
- Monitoring systems

## Future Considerations

### Planned Improvements
- Performance optimizations
- Feature enhancements
- Technology upgrades

### Scalability Roadmap
- Expected growth patterns
- Scaling strategies
- Technology evolution path
"""
        return content
    
    def _generate_testing_content(self, repo_info: Dict) -> str:
        """Generate testing content."""
        project_name = repo_info.get('project_name', 'Project')
        languages = repo_info.get('languages', [])
        test_dirs = repo_info.get('test_dirs', [])
        
        content = f"""---
title: {escape_yaml_value("Testing Guide")}
---

# Testing Guide

This document describes the testing strategy and practices for {project_name}.

## Testing Philosophy

We believe in comprehensive testing to ensure code quality, reliability, and maintainability. Our testing approach includes:

- **Test-Driven Development (TDD)**: Writing tests before implementation
- **Continuous Testing**: Automated testing in CI/CD pipeline
- **Coverage Goals**: Maintaining high test coverage
- **Quality Gates**: Tests must pass before deployment

## Test Structure

### Test Organization
"""
        
        if test_dirs:
            content += f"- **Test Directories**: {', '.join(test_dirs)}\n"
        else:
            content += "- **Test Directories**: `tests/`, `test/`\n"
        
        content += """- **Test Naming**: Descriptive test names that explain the scenario
- **Test Grouping**: Tests organized by feature or module

### Test Types

#### Unit Tests
- **Purpose**: Test individual functions and methods in isolation
- **Coverage**: All public functions and critical private functions
- **Mock Usage**: External dependencies are mocked
- **Execution**: Fast execution (< 1 second per test)

#### Integration Tests
- **Purpose**: Test interaction between components
- **Coverage**: API endpoints, database interactions, service integrations
- **Environment**: Test database and external service mocks
- **Execution**: Moderate execution time (1-10 seconds per test)

#### End-to-End Tests
- **Purpose**: Test complete user workflows
- **Coverage**: Critical user journeys and business processes
- **Environment**: Production-like test environment
- **Execution**: Slower execution (10+ seconds per test)

## Testing Frameworks and Tools

### Primary Testing Frameworks
"""
        
        if 'Python' in languages:
            content += """- **pytest**: Main testing framework for Python code
- **unittest**: Built-in Python testing framework
- **pytest-cov**: Coverage reporting
"""
        
        if 'JavaScript' in languages or 'TypeScript' in languages:
            content += """- **Jest**: JavaScript testing framework
- **Mocha**: Alternative JavaScript testing framework
- **Cypress**: End-to-end testing framework
"""
        
        if 'Java' in languages:
            content += """- **JUnit**: Main testing framework for Java
- **Mockito**: Mocking framework
- **TestNG**: Alternative testing framework
"""
        
        content += """
### Supporting Tools
- **Coverage Tools**: Track test coverage metrics
- **Mocking Libraries**: Create test doubles for dependencies
- **Test Data Factories**: Generate test data consistently
- **Performance Testing**: Load and stress testing tools

## Running Tests

### Local Development

```bash
# Run all tests
make test  # or npm test, pytest, etc.

# Run specific test suite
make test-unit
make test-integration

# Run with coverage
make test-coverage

# Run specific test file
pytest tests/test_specific_module.py
```

### Continuous Integration

Tests are automatically executed on:
- Every pull request
- Every push to main branch
- Nightly builds for comprehensive testing

### Test Configuration

```yaml
# Example test configuration
test:
  unit:
    timeout: 30s
    parallel: true
  integration:
    timeout: 300s
    database: test_db
  coverage:
    minimum: 80%
    exclude:
      - tests/
      - migrations/
```

## Writing Good Tests

### Test Structure (AAA Pattern)
```python
def test_user_creation():
    # Arrange: Set up test data
    user_data = {"name": "John", "email": "john@example.com"}
    
    # Act: Execute the functionality
    user = create_user(user_data)
    
    # Assert: Verify the results
    assert user.name == "John"
    assert user.email == "john@example.com"
```

### Best Practices
- **One Assertion Per Test**: Focus on testing one thing
- **Descriptive Names**: Test names should describe the scenario
- **Independent Tests**: Tests should not depend on each other
- **Fast Execution**: Optimize for quick feedback
- **Readable Code**: Tests serve as documentation

### Test Data Management
- Use factories for consistent test data
- Avoid hardcoded values
- Clean up test data after tests
- Use realistic but safe test data

## Coverage Requirements

### Coverage Targets
- **Overall Coverage**: Minimum 80%
- **New Code Coverage**: Minimum 90%
- **Critical Paths**: 100% coverage required

### Coverage Reports
- Generated automatically in CI/CD
- Available in HTML format for detailed analysis
- Integrated with code review process

## Testing in Different Environments

### Development
- Fast feedback loop
- Subset of tests for quick validation
- Local database and services

### Staging
- Full test suite execution
- Production-like environment
- Performance testing

### Production
- Smoke tests after deployment
- Health checks and monitoring
- Rollback procedures if tests fail

## Performance Testing

### Load Testing
- Simulate expected user load
- Identify performance bottlenecks
- Validate scalability assumptions

### Stress Testing
- Test system limits
- Evaluate graceful degradation
- Identify breaking points

## Troubleshooting Tests

### Common Issues
1. **Flaky Tests**: Tests that pass/fail inconsistently
   - Solution: Identify and eliminate race conditions
   
2. **Slow Tests**: Tests taking too long to execute
   - Solution: Optimize database queries, use mocks

3. **Test Dependencies**: Tests that depend on external services
   - Solution: Mock external dependencies

### Debugging Tests
- Use debugging tools in your IDE
- Add logging to understand test execution
- Isolate failing tests
- Check test environment configuration

## Contributing to Tests

### Adding New Tests
1. Follow naming conventions
2. Use appropriate test type (unit/integration/e2e)
3. Ensure tests are independent
4. Add documentation for complex test scenarios

### Updating Existing Tests
1. Maintain backward compatibility when possible
2. Update related tests when changing functionality
3. Ensure coverage is maintained or improved
4. Review test performance impact
"""
        return content
    
    def _generate_security_content(self, repo_info: Dict) -> str:
        """Generate security content."""
        project_name = repo_info.get('project_name', 'Project')
        languages = repo_info.get('languages', [])
        
        content = f"""---
title: {escape_yaml_value("Security Guide")}
---

# Security Guide

This document outlines the security practices and considerations for {project_name}.

## Security Philosophy

Security is a fundamental aspect of {project_name}. We follow security-by-design principles and implement defense-in-depth strategies to protect against various threats.

## Security Principles

### Core Principles
- **Least Privilege**: Grant minimum necessary permissions
- **Defense in Depth**: Multiple layers of security controls
- **Fail Secure**: Default to secure state on failure
- **Complete Mediation**: Check every access request
- **Open Design**: Security through proper design, not obscurity

### Development Practices
- **Secure Coding Standards**: Following OWASP guidelines
- **Code Reviews**: Security-focused code reviews
- **Static Analysis**: Automated security scanning
- **Dependency Management**: Regular updates and vulnerability scanning

## Authentication and Authorization

### Authentication Mechanisms
- **Strong Passwords**: Minimum complexity requirements
- **Multi-Factor Authentication (MFA)**: Additional security layer
- **Session Management**: Secure session handling
- **Account Lockout**: Protection against brute force attacks

### Authorization Controls
- **Role-Based Access Control (RBAC)**: Users assigned roles with specific permissions
- **Principle of Least Privilege**: Minimal access rights
- **Access Reviews**: Regular permission audits
- **Separation of Duties**: Critical operations require multiple approvals

## Data Protection

### Data Classification
- **Public**: No restrictions
- **Internal**: Restricted to organization
- **Confidential**: Limited access required
- **Restricted**: Highest level of protection

### Encryption Standards
- **Data at Rest**: AES-256 encryption
- **Data in Transit**: TLS 1.3 minimum
- **Key Management**: Secure key storage and rotation
- **Certificate Management**: Regular certificate updates

### Data Handling
- **Data Minimization**: Collect only necessary data
- **Data Retention**: Clear retention policies
- **Data Disposal**: Secure deletion procedures
- **Backup Security**: Encrypted backups with access controls

## Input Validation and Sanitization

### Input Validation
- **Whitelist Approach**: Allow only expected input patterns
- **Data Type Validation**: Ensure correct data types
- **Length Limits**: Prevent buffer overflow attacks
- **Character Encoding**: Proper encoding validation

### Common Vulnerabilities Prevention
"""
        
        if 'Python' in languages:
            content += """
#### SQL Injection Prevention (Python)
```python
# Good: Using parameterized queries
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))

# Bad: String concatenation
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
```
"""
        
        if 'JavaScript' in languages or 'TypeScript' in languages:
            content += """
#### Cross-Site Scripting (XSS) Prevention (JavaScript)
```javascript
// Good: Proper escaping
const safeHTML = escapeHtml(userInput);

// Bad: Direct insertion
element.innerHTML = userInput;
```
"""
        
        content += """
### Output Encoding
- **HTML Encoding**: Prevent XSS in web applications
- **URL Encoding**: Safe URL parameter handling
- **JSON Encoding**: Prevent injection in JSON responses

## Network Security

### Communication Security
- **HTTPS Only**: All communications encrypted
- **HSTS Headers**: Force HTTPS connections
- **Certificate Pinning**: Prevent man-in-the-middle attacks
- **API Security**: Secure API design and implementation

### Network Controls
- **Firewall Rules**: Restrict network access
- **VPN Access**: Secure remote access
- **Network Segmentation**: Isolate critical systems
- **Intrusion Detection**: Monitor for suspicious activity

## Application Security

### Secure Configuration
- **Default Passwords**: Change all default credentials
- **Error Handling**: Avoid information disclosure
- **Logging**: Security event logging without sensitive data
- **File Permissions**: Restrict file system access

### Security Headers
```http
# Example security headers
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
Referrer-Policy: strict-origin-when-cross-origin
```

### Dependency Security
- **Dependency Scanning**: Regular vulnerability scans
- **Update Policies**: Timely security updates
- **License Compliance**: Track open source licenses
- **Supply Chain Security**: Verify dependency integrity

## Incident Response

### Incident Classification
- **Low**: Minor security events
- **Medium**: Potential security impact
- **High**: Confirmed security breach
- **Critical**: Severe security incident

### Response Procedures
1. **Detection**: Identify security incidents
2. **Containment**: Limit incident impact
3. **Investigation**: Determine root cause
4. **Recovery**: Restore normal operations
5. **Lessons Learned**: Improve security measures

### Communication Plan
- **Internal Notifications**: Alert security team
- **External Communications**: Customer/user notifications
- **Regulatory Reporting**: Compliance requirements
- **Documentation**: Incident documentation

## Security Testing

### Security Testing Types
- **Static Application Security Testing (SAST)**: Code analysis
- **Dynamic Application Security Testing (DAST)**: Runtime testing
- **Interactive Application Security Testing (IAST)**: Hybrid approach
- **Penetration Testing**: Simulated attacks

### Automated Security Scanning
- **Dependency Scanning**: Check for vulnerable dependencies
- **Secret Scanning**: Detect exposed credentials
- **Container Scanning**: Secure container images
- **Infrastructure Scanning**: Secure cloud resources

## Compliance and Standards

### Relevant Standards
- **OWASP Top 10**: Web application security risks
- **ISO 27001**: Information security management
- **NIST Cybersecurity Framework**: Security guidelines
- **SOC 2**: Security and availability controls

### Compliance Requirements
- Regular security assessments
- Security training for developers
- Incident response procedures
- Data protection measures

## Security Training and Awareness

### Developer Training
- Secure coding practices
- Common vulnerability patterns
- Security testing techniques
- Incident response procedures

### Security Resources
- **OWASP**: Open Web Application Security Project
- **CWE**: Common Weakness Enumeration
- **CVE**: Common Vulnerabilities and Exposures
- **Security Advisories**: Vendor security notifications

## Reporting Security Issues

### Responsible Disclosure
If you discover a security vulnerability, please:

1. **Do Not** disclose publicly
2. **Email** security@[organization].com
3. **Provide** detailed vulnerability information
4. **Allow** reasonable time for response

### Bug Bounty Program
- Scope of eligible vulnerabilities
- Reward structure
- Submission guidelines
- Response timelines

## Security Checklist

### Development
- [ ] Input validation implemented
- [ ] Output encoding applied
- [ ] Authentication and authorization in place
- [ ] Secure configuration applied
- [ ] Security headers configured

### Deployment
- [ ] Secrets management configured
- [ ] Network security controls applied
- [ ] Monitoring and logging enabled
- [ ] Backup and recovery tested
- [ ] Incident response plan ready

### Operations
- [ ] Regular security updates applied
- [ ] Access reviews conducted
- [ ] Security monitoring active
- [ ] Incident response tested
- [ ] Security training completed
"""
        return content
    
    def _generate_guides_content(self, repo_info: Dict) -> str:
        """Generate guides content."""
        project_name = repo_info.get('project_name', 'Project')
        languages = repo_info.get('languages', [])
        
        content = f"""---
title: {escape_yaml_value("User Guides")}
---

# User Guides

Welcome to the {project_name} user guides! This section provides comprehensive guidance for users and developers.

## Quick Start Guide

### Getting Started in 5 Minutes

1. **Installation**: Follow the [Installation Guide](./installation.md)
2. **Configuration**: Set up your basic configuration
3. **First Steps**: Try the basic functionality
4. **Next Steps**: Explore advanced features

### Basic Usage

```bash
# Example basic commands
{project_name.lower()} --help
{project_name.lower()} init
{project_name.lower()} run
```

## User Guides

### For End Users

#### Getting Started
- **Prerequisites**: What you need before starting
- **Installation**: Step-by-step installation
- **Configuration**: Initial setup and configuration
- **First Use**: Your first experience with {project_name}

#### Common Tasks
- **Daily Operations**: Frequent tasks and workflows
- **Configuration Management**: Managing settings and preferences
- **Troubleshooting**: Common issues and solutions
- **Best Practices**: Tips for effective usage

#### Advanced Features
- **Power User Features**: Advanced functionality
- **Customization**: Personalizing your experience
- **Integration**: Working with other tools
- **Automation**: Automating repetitive tasks

### For Administrators

#### System Administration
- **Installation and Setup**: System-wide installation
- **User Management**: Managing users and permissions
- **Configuration Management**: System configuration
- **Monitoring and Maintenance**: Keeping the system healthy

#### Security Administration
- **Security Configuration**: Secure setup
- **Access Control**: Managing permissions
- **Audit and Compliance**: Monitoring and reporting
- **Incident Response**: Handling security events

## Developer Guides

### For New Developers

#### Development Environment Setup
1. **Prerequisites**: Required tools and software
2. **Repository Setup**: Cloning and initial setup
3. **Dependencies**: Installing development dependencies
4. **IDE Configuration**: Setting up your development environment

#### First Contribution
1. **Code Style**: Understanding the coding standards
2. **Development Workflow**: How we work with code
3. **Testing**: Running and writing tests
4. **Submitting Changes**: Creating pull requests

### For Experienced Developers

#### Architecture Deep Dive
- **System Design**: How the system is architected
- **Code Organization**: Understanding the codebase
- **Design Patterns**: Patterns used in the project
- **Extension Points**: How to extend functionality

#### Advanced Development
- **Performance Optimization**: Making the code faster
- **Security Considerations**: Security best practices
- **Debugging Techniques**: Troubleshooting complex issues
- **Testing Strategies**: Advanced testing approaches

## API Guides

### REST API Guide

#### Authentication
```bash
# Example API authentication
curl -H "Authorization: Bearer YOUR_TOKEN" \\
     https://api.example.com/v1/endpoint
```

#### Common Operations
- **CRUD Operations**: Create, Read, Update, Delete
- **Filtering and Sorting**: Query parameters
- **Pagination**: Handling large result sets
- **Error Handling**: Understanding API errors

#### Advanced API Usage
- **Batch Operations**: Processing multiple items
- **Webhooks**: Real-time notifications
- **Rate Limiting**: Managing API usage
- **Versioning**: Working with different API versions

### SDK/Library Guide

"""
        
        if 'Python' in languages:
            content += """#### Python SDK
```python
import {}_sdk

# Initialize client
client = {}_sdk.Client(api_key="your_key")

# Basic operations
result = client.get_data()
client.create_item(data)
```
""".format(project_name.lower().replace('-', '_'), project_name.lower().replace('-', '_'))
        
        if 'JavaScript' in languages:
            content += """#### JavaScript SDK
```javascript
const {{ Client }} = require('{}-sdk');

// Initialize client
const client = new Client({{ apiKey: 'your_key' }});

// Basic operations
const result = await client.getData();
await client.createItem(data);
```
""".format(project_name.lower())
        
        content += """
## Integration Guides

### Third-Party Integrations

#### Popular Integrations
- **Tool A**: Integration with Tool A
- **Tool B**: Integration with Tool B
- **Tool C**: Integration with Tool C

#### Custom Integrations
- **API Integration**: Building custom API integrations
- **Webhook Integration**: Setting up webhooks
- **Plugin Development**: Creating custom plugins
- **Extension Development**: Building extensions

### CI/CD Integration

#### GitHub Actions
```yaml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup
        run: |
          # Setup commands
      - name: Test
        run: |
          # Test commands
```

#### Jenkins Integration
- **Pipeline Setup**: Creating Jenkins pipelines
- **Environment Configuration**: Setting up build environments
- **Deployment Automation**: Automated deployments
- **Monitoring Integration**: Build monitoring

## Troubleshooting Guides

### Common Issues

#### Installation Problems
**Problem**: Installation fails with dependency errors
**Solution**: 
1. Check system requirements
2. Update package managers
3. Install missing dependencies
4. Try alternative installation methods

#### Configuration Issues
**Problem**: Application won't start with configuration errors
**Solution**:
1. Validate configuration file syntax
2. Check required configuration values
3. Verify file permissions
4. Review log files for specific errors

#### Performance Issues
**Problem**: Application running slowly
**Solution**:
1. Check system resources (CPU, memory)
2. Review database performance
3. Analyze network connectivity
4. Optimize configuration settings

### Error Messages

#### Common Error Codes
- **Error 400**: Bad Request - Check input parameters
- **Error 401**: Unauthorized - Verify authentication
- **Error 403**: Forbidden - Check permissions
- **Error 404**: Not Found - Verify resource exists
- **Error 500**: Internal Server Error - Check logs

#### Debugging Steps
1. **Reproduce the Issue**: Consistent reproduction steps
2. **Check Logs**: Application and system logs
3. **Verify Configuration**: Configuration file validation
4. **Test Components**: Isolate the problem area
5. **Gather Information**: System information and context

## Best Practices

### General Best Practices
- **Regular Updates**: Keep software updated
- **Backup Strategy**: Regular backups of important data
- **Monitoring**: Set up monitoring and alerting
- **Documentation**: Keep configuration documented
- **Security**: Follow security best practices

### Performance Best Practices
- **Resource Management**: Efficient resource usage
- **Caching Strategy**: Appropriate caching implementation
- **Database Optimization**: Optimized database queries
- **Network Optimization**: Minimize network overhead

### Security Best Practices
- **Access Control**: Implement proper access controls
- **Data Protection**: Protect sensitive data
- **Regular Audits**: Conduct security audits
- **Incident Response**: Have incident response procedures

## Getting Help

### Community Resources
- **Documentation**: This comprehensive documentation
- **Community Forums**: User community discussions
- **Stack Overflow**: Q&A with the community
- **GitHub Issues**: Bug reports and feature requests

### Professional Support
- **Enterprise Support**: Professional support options
- **Consulting Services**: Implementation assistance
- **Training Programs**: Formal training options
- **Custom Development**: Tailored development services

### Contributing Back
- **Bug Reports**: Help improve the software
- **Feature Requests**: Suggest new features
- **Documentation**: Improve documentation
- **Code Contributions**: Contribute to the codebase
"""
        return content
    
    def _save_section_content(self, section_key: str, content: str) -> None:
        """Save section content to the appropriate file."""
        # Determine output file path based on section
        docs_dir = self.output_dir / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        filename_map = {
            "overview": "overview.md",
            "installation": "installation.md", 
            "api": "api.md",
            "development": "development.md",
            "contributing": "contributing.md",
            "changelog": "changelog.md",
            "deployment": "deployment.md",
            "architecture": "architecture.md",
            "testing": "testing.md",
            "security": "security.md",
            "guides": "guides.md"
        }
        
        filename = filename_map.get(section_key, f"{section_key}.md")
        file_path = docs_dir / filename
        
        # Apply MDX escaping
        escaped_content = escape_mdx_special_characters(content)
        
        # Save content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(escaped_content)
        
        self.logger.debug(f"Saved {section_key} content to {file_path}")
        
        # Clean API documentation if needed
        if section_key == "api":
            clean_api_doc(str(file_path))
    
    def _update_configuration(self, repo_info: Dict) -> bool:
        """Update site configuration."""
        try:
            self.logger.debug("Updating site configuration")
            
            config_data = {
                'title': repo_info.get('project_name', 'Documentation'),
                'tagline': repo_info.get('description', 'Project documentation'),
                'url': repo_info.get('repo_url', ''),
                'organizationName': repo_info.get('org_name', ''),
                'projectName': repo_info.get('project_name', '')
            }
            
            return self.config_updater.update_config(config_data)
            
        except Exception as e:
            self.logger.error(f"Error updating configuration: {str(e)}")
            return False
    
    def _revise_site(self) -> bool:
        """Revise the site landing page."""
        try:
            self.logger.debug("Revising site landing page")
            
            # Import and use site reviser
            from jpl.slim.best_practices.docs_website_impl.site_reviser import SiteReviser
            from jpl.slim.utils.ai_utils import enhance_content
            
            # Create AI enhancer if available
            ai_enhancer = None
            if self.use_ai:
                class SimpleAIEnhancer:
                    def __init__(self, model):
                        self.model = model
                    
                    def enhance(self, content, section_name):
                        return enhance_content(content, "docgen", section_name, self.model)
                
                ai_enhancer = SimpleAIEnhancer(self.use_ai)
            
            site_reviser = SiteReviser(str(self.output_dir), self.logger, ai_enhancer)
            return site_reviser.revise_site()
            
        except Exception as e:
            self.logger.error(f"Error revising site: {str(e)}")
            return False
    
    def _replace_basic_placeholders(self, repo_info: Dict) -> bool:
        """Replace universal placeholders in template files."""
        try:
            self.logger.debug("Replacing basic placeholders")
            
            # Extract basic project information
            project_name = repo_info.get('project_name', 'Documentation Site')
            project_description = repo_info.get('description', 'A software project documentation site')
            project_overview = repo_info.get('overview', project_description)
            github_org = repo_info.get('github_org', 'your-org')
            github_repo = repo_info.get('github_repo', 'your-repo')
            
            # Define placeholder mappings (simplified set)
            placeholders = {
                '{{PROJECT_NAME}}': project_name,
                '{{PROJECT_DESCRIPTION}}': project_description,
                '{{PROJECT_OVERVIEW}}': project_overview,
                '{{GITHUB_ORG}}': github_org,
                '{{GITHUB_REPO}}': github_repo,
            }
            
            # Extract and add feature placeholders
            features = self._extract_features(repo_info)
            for i, feature in enumerate(features[:6], 1):  # Limit to 6 features
                placeholders[f'{{{{FEATURE_{i}_TITLE}}}}'] = feature.get('title', f'Feature {i}')
                placeholders[f'{{{{FEATURE_{i}_DESCRIPTION}}}}'] = feature.get('description', f'Description for feature {i}')
            
            # Fill remaining feature slots if needed
            for i in range(len(features) + 1, 7):
                placeholders[f'{{{{FEATURE_{i}_TITLE}}}}'] = f'Feature {i}'
                placeholders[f'{{{{FEATURE_{i}_DESCRIPTION}}}}'] = f'Description for feature {i}'
            
            # Replace placeholders in all files
            return self._replace_placeholders_in_files(placeholders)
            
        except Exception as e:
            self.logger.error(f"Error replacing basic placeholders: {str(e)}")
            return False
    
    def _extract_features(self, repo_info: Dict) -> List[Dict]:
        """Extract key features from repository analysis."""
        features = []
        
        # Extract features from README if available
        readme_content = repo_info.get('readme_content', '')
        if readme_content:
            # Simple feature extraction logic
            lines = readme_content.split('\n')
            current_feature = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('- ') or line.startswith('* '):
                    # Found a bullet point - potential feature
                    feature_text = line[2:].strip()
                    if len(feature_text) > 10:  # Only consider substantial bullet points
                        features.append({
                            'title': feature_text[:50] + ('...' if len(feature_text) > 50 else ''),
                            'description': feature_text
                        })
        
        # If no features found, generate generic ones based on project type
        if not features:
            languages = repo_info.get('languages', [])
            if 'Python' in languages:
                features.extend([
                    {'title': 'Python-Based', 'description': 'Built with Python for reliability and ease of use'},
                    {'title': 'Easy Installation', 'description': 'Simple pip install process'},
                ])
            if 'JavaScript' in languages:
                features.extend([
                    {'title': 'Modern JavaScript', 'description': 'Built with modern JavaScript frameworks'},
                    {'title': 'NPM Package', 'description': 'Easy installation via npm'},
                ])
            
            # Add generic features
            features.extend([
                {'title': 'Open Source', 'description': 'Open source project with community contributions'},
                {'title': 'Well Documented', 'description': 'Comprehensive documentation and examples'},
                {'title': 'Actively Maintained', 'description': 'Regular updates and bug fixes'},
                {'title': 'Cross Platform', 'description': 'Works on multiple operating systems'},
            ])
        
        return features[:6]  # Return max 6 features
    
    def _replace_placeholders_in_files(self, placeholders: Dict[str, str]) -> bool:
        """Replace placeholders in all template files."""
        try:
            # Find all files that might contain placeholders
            files_to_process = []
            for root, dirs, files in os.walk(self.output_dir):
                for file in files:
                    if file.endswith(('.js', '.md', '.json', '.tsx', '.jsx')):
                        files_to_process.append(os.path.join(root, file))
            
            for file_path in files_to_process:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Replace all placeholders
                    modified = False
                    for placeholder, replacement in placeholders.items():
                        if placeholder in content:
                            content = content.replace(placeholder, replacement)
                            modified = True
                    
                    # Write back if modified
                    if modified:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        self.logger.debug(f"Updated placeholders in {file_path}")
                
                except Exception as e:
                    self.logger.warning(f"Error processing file {file_path}: {str(e)}")
                    continue
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error replacing placeholders in files: {str(e)}")
            return False
    
    def _ai_enhance_content(self, repo_info: Dict) -> bool:
        """Use AI to fill [INSERT_CONTENT] markers in markdown files with multi-pass processing."""
        try:
            self.logger.debug("AI enhancing content with multi-pass processing")
            
            # Find all markdown files in docs directory
            docs_dir = self.output_dir / "docs"
            if not docs_dir.exists():
                self.logger.warning("No docs directory found")
                return True
            
            markdown_files = []
            for root, dirs, files in os.walk(docs_dir):
                for file in files:
                    if file.endswith('.md'):
                        markdown_files.append(os.path.join(root, file))
            
            # Sort files by priority (core files first)
            priority_files = []
            regular_files = []
            
            for file_path in markdown_files:
                file_name = os.path.basename(file_path).lower()
                if any(priority in file_name for priority in ['installation', 'quick-start', 'features', 'contributing']):
                    priority_files.append(file_path)
                else:
                    regular_files.append(file_path)
            
            # Process files in batches to avoid context window issues
            all_files = priority_files + regular_files
            batch_size = 3  # Process 3 files at a time to stay within context limits
            
            for i in range(0, len(all_files), batch_size):
                batch = all_files[i:i + batch_size]
                self.logger.debug(f"Processing batch {i//batch_size + 1}: {[os.path.basename(f) for f in batch]}")
                
                for file_path in batch:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Check if file contains [INSERT_CONTENT] marker or generic placeholders
                        if '[INSERT_CONTENT]' in content or '[Project Name]' in content:
                            enhanced_content = self._ai_fill_content(content, file_path, repo_info)
                            if enhanced_content and enhanced_content != content:
                                # Clean the AI response
                                cleaned_content = self._clean_ai_response(enhanced_content, content)
                                with open(file_path, 'w', encoding='utf-8') as f:
                                    f.write(cleaned_content)
                                self.logger.debug(f"AI enhanced content in {os.path.basename(file_path)}")
                    
                    except Exception as e:
                        self.logger.warning(f"Error AI enhancing file {os.path.basename(file_path)}: {str(e)}")
                        continue
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error during AI content enhancement: {str(e)}")
            return False
    
    def _ai_fill_content(self, content: str, file_path: str, repo_info: Dict) -> str:
        """Use AI to fill [INSERT_CONTENT] marker in a specific file."""
        try:
            # Determine file type and section from path
            file_name = os.path.basename(file_path)
            section_type = file_name.replace('.md', '')
            
            # Build context for AI
            project_name = repo_info.get('project_name', 'this project')
            project_type = self._determine_project_type(repo_info)
            languages = repo_info.get('languages', [])
            
            # Extract key features for better context
            features = self._extract_features(repo_info)
            
            # Create comprehensive AI context
            feature_titles = [feature.get('title', '') for feature in features[:3]] if features else []
            context_info = f"""
Project: {project_name}
Type: {project_type}
Technologies: {', '.join(languages[:5])}
Structure: {repo_info.get('structure_summary', 'Standard project structure')}
Key Features: {', '.join(feature_titles) if feature_titles else 'General software features'}
File being processed: {section_type}.md
"""
            
            # Use the general docs-website prompt for all sections
            enhanced_content = enhance_content(
                content=content,
                practice_type="docs-website",
                section_name="generate_documentation",
                model=self.use_ai,
                additional_context=context_info
            )
            
            return enhanced_content
            
        except Exception as e:
            self.logger.error(f"Error AI filling content for {os.path.basename(file_path)}: {str(e)}")
            return content  # Return original content if AI fails
    
    def _clean_ai_response(self, ai_response: str, original_content: str) -> str:
        """Clean AI response to remove conversation artifacts and preserve structure."""
        try:
            # Remove common conversation artifacts
            lines = ai_response.split('\n')
            cleaned_lines = []
            skip_next = False
            in_content = False
            
            for line in lines:
                line_lower = line.lower().strip()
                
                # Skip conversation markers
                if any(marker in line_lower for marker in [
                    '### user:', '### assistant:', 'here is the enhanced',
                    'here is the content', 'content to enhance:',
                    'you are a software', 'based on the repository'
                ]):
                    skip_next = True
                    continue
                    
                # Skip empty lines after conversation markers
                if skip_next and not line.strip():
                    continue
                elif skip_next:
                    skip_next = False
                
                # Look for the start of actual content (YAML front matter)
                if line.strip().startswith('---') and not in_content:
                    in_content = True
                    cleaned_lines.append(line)
                    continue
                
                if in_content:
                    cleaned_lines.append(line)
            
            # If we couldn't find proper content, try to extract it differently
            if not cleaned_lines or not any('---' in line for line in cleaned_lines[:5]):
                # Look for content after "CONTENT TO ENHANCE:" or similar
                content_start = -1
                for i, line in enumerate(lines):
                    if 'content to enhance:' in line.lower() or line.strip().startswith('---'):
                        content_start = i + 1 if 'content to enhance:' in line.lower() else i
                        break
                
                if content_start >= 0:
                    cleaned_lines = lines[content_start:]
                else:
                    # Fallback: return original content
                    return original_content
            
            result = '\n'.join(cleaned_lines).strip()
            
            # Ensure we have valid content
            if not result or len(result) < 50:
                return original_content
                
            return result
            
        except Exception as e:
            self.logger.warning(f"Error cleaning AI response: {str(e)}")
            return original_content
    
    def _determine_project_type(self, repo_info: Dict) -> str:
        """Determine the type of project based on repository analysis."""
        languages = repo_info.get('languages', [])
        files = repo_info.get('files', [])
        
        # Check for specific project types
        if any('package.json' in f for f in files):
            if any('react' in f.lower() for f in files):
                return "React web application"
            elif any('vue' in f.lower() for f in files):
                return "Vue.js web application"
            else:
                return "Node.js application"
        
        if any('setup.py' in f or 'pyproject.toml' in f for f in files):
            if any('fastapi' in f.lower() or 'flask' in f.lower() for f in files):
                return "Python web API"
            elif any('cli' in f.lower() or 'main.py' in f for f in files):
                return "Python CLI tool"
            else:
                return "Python library"
        
        if any('pom.xml' in f or 'build.gradle' in f for f in files):
            return "Java application"
        
        if any('Cargo.toml' in f for f in files):
            return "Rust application"
        
        if any('go.mod' in f for f in files):
            return "Go application"
        
        # Default based on primary language
        if 'JavaScript' in languages:
            return "JavaScript application"
        elif 'Python' in languages:
            return "Python project"
        elif 'Java' in languages:
            return "Java project"
        else:
            return "software project"