# SLIM-CLI MCP Server

A Model Context Protocol (MCP) server for the SLIM-CLI tool, enabling natural language interaction with SLIM best practices through LLMs.

## Overview

The SLIM-CLI MCP Server provides a standardized interface for LLMs to interact with SLIM (Software Lifecycle Improvement & Modernization) best practices. It exposes SLIM functionality through tools, resources, and prompts that can be used by compatible LLM clients.

## Features

### Tools
- **slim_apply**: Apply SLIM best practices to repositories
- **slim_deploy**: Deploy best practices to git repositories  
- **slim_list**: List available best practices
- **slim_models_list**: List available AI models
- **slim_models_recommend**: Get AI model recommendations
- **slim_models_validate**: Validate AI model configuration

### Resources
- **slim_registry**: Access to the complete SLIM registry
- **slim_best_practices**: Detailed best practice information
- **slim_prompts**: Available prompt templates
- **slim_models**: AI model information and recommendations

### Prompts
- **apply_best_practice**: Template for applying best practices
- **customize_with_ai**: Template for AI-powered customization
- **review_changes**: Template for reviewing modifications

## Installation

1. Install the MCP Python SDK with FastMCP:
```bash
pip install 'mcp[cli]'
```

2. Ensure SLIM-CLI dependencies are available:
```bash
pip install typer rich gitpython litellm
```

## Usage

### Running the Server

```bash
# From the SLIM-CLI root directory
python -m mcp.server
```

### Using with Claude Desktop

Add to your Claude Desktop MCP settings:

```json
{
  "mcpServers": {
    "slim-cli": {
      "command": "python",
      "args": ["-m", "mcp.server"],
      "cwd": "/path/to/slim-cli"
    }
  }
}
```

### Example Commands

Once connected, you can use natural language to interact with SLIM:

```
"Apply the README best practice to https://github.com/user/repo using AI"

"List all available security best practices"

"Recommend AI models for documentation generation"

"Deploy the governance best practices to my local repository"
```

## Tool Examples

### Apply Best Practice
```python
# Apply README best practice with AI customization
result = slim_apply_tool(
    best_practice_ids=["readme"],
    repo_urls=["https://github.com/user/repo"],
    use_ai="anthropic/claude-3-5-sonnet-20241022"
)
```

### Deploy Changes
```python
# Deploy multiple best practices
result = slim_deploy_tool(
    best_practice_ids=["readme", "contributing"],
    repo_dir="/path/to/repo",
    commit_message="Add SLIM best practices"
)
```

### List Practices
```python
# List documentation-related practices
result = slim_list_tool(
    category="documentation",
    detailed=True
)
```

## Resource Examples

### Access Registry
```python
# Get complete SLIM registry
registry_data = slim_registry_resource()
```

### Get Best Practice Details
```python
# Get specific practice information
practice_info = slim_best_practices_resource("readme")
```

### Model Information
```python
# Get AI model recommendations
models_data = slim_models_resource()
```

## Configuration

The server uses the following configuration:
- **Registry URI**: `https://raw.githubusercontent.com/NASA-AMMOS/slim/main/static/data/slim-registry.json`
- **Default AI Model**: Recommendations based on task and tier
- **Logging Level**: INFO (configurable)

## Error Handling

The server provides comprehensive error handling:
- Parameter validation
- Network connectivity checks
- AI model availability validation
- Git operation error handling
- Detailed error messages in responses

## Dependencies

### Required
- `mcp[cli]` - MCP Python SDK with FastMCP
- `typer` - CLI framework
- `rich` - Rich text formatting
- `gitpython` - Git operations

### Optional
- `litellm` - Enhanced AI model support
- `detect-secrets` - Security scanning (for secrets practices)

## Best Practices

### Using AI Models
1. Validate models before use with `slim_models_validate`
2. Use recommended models from `slim_models_recommend`
3. Set up provider API keys as environment variables

### Repository Operations
1. Use `dry_run=True` to preview changes
2. Ensure repository is in clean state before applying practices
3. Review changes before deploying

### Error Handling
1. Check tool response `success` field
2. Log errors appropriately
3. Provide fallback options for failures

## Troubleshooting

### Common Issues

1. **"No models found"**: Install LiteLLM with `pip install litellm`
2. **"Git operation failed"**: Ensure repository is accessible and has proper permissions
3. **"Registry fetch failed"**: Check network connectivity
4. **"AI model not available"**: Verify API keys and model configuration

### Debugging

Enable debug logging:
```python
import logging
logging.getLogger('mcp').setLevel(logging.DEBUG)
```

## Contributing

1. Follow the existing code structure
2. Add comprehensive error handling
3. Include docstrings for all public functions
4. Test with various repository types
5. Update documentation for new features

## License

This MCP server is part of the SLIM-CLI project and follows the same license terms.