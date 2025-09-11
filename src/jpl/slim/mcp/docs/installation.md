# Installing SLIM-CLI MCP Server in Claude Code

This guide shows you how to install and use the SLIM-CLI MCP server with Claude Code.

## 📋 Prerequisites

The SLIM CLI MCP server requires FastMCP to run. The server will attempt to install it automatically, but may require manual installation depending on your system configuration:

- **Python 3.9+**
- **FastMCP** (installed automatically or manually via `pipx install fastmcp`)

## 🚀 Quick Setup

### Quick Setup (Recommended)

1. **Install the MCP server using Claude Code CLI**:
```bash
# From your SLIM CLI installation directory
claude mcp add slim-cli $(pwd)/src/jpl/slim/mcp/scripts/start_mcp_server.sh -s user
```

2. **Verify the installation**:
```bash
claude mcp list
# Should show: slim-cli - ✓ Connected
```

3. **Start using SLIM in Claude Code** - the server will automatically install FastMCP on first run if needed.

### Manual Configuration (Alternative)

If you prefer manual configuration, add this to your Claude Code MCP configuration:

```json
{
  "mcpServers": {
    "slim-cli": {
      "command": "/path/to/slim-cli/src/jpl/slim/mcp/scripts/start_mcp_server.sh"
    }
  }
}
```

## 🧪 Testing the Installation

Once installed, you can test the MCP server with these natural language commands in Claude Code:

### List Available Best Practices
```
"Show me all available SLIM best practices"
"List documentation-related best practices" 
"What security practices are available?"
```

### Apply Best Practices
```
"Apply the README best practice to https://github.com/user/repo"
"Apply contributing guidelines and changelog to my repository"
"Apply the README practice with AI customization using Claude"
```

### Get AI Model Recommendations
```
"What are the best AI models for documentation generation?"
"Recommend premium AI models for code generation"
"Show me local AI models I can use"
```

### Validate AI Models
```
"Check if the OpenAI GPT-4 model is properly configured"
"Validate the Anthropic Claude model"
```

### Deploy Changes
```
"Deploy the applied best practices to my repository"
"Push the README and contributing files to the main branch"
```

## 🔧 Available Tools

The MCP server provides these tools:

- **slim_apply**: Apply best practices to repositories
- **slim_deploy**: Deploy changes to git repositories
- **slim_list**: List available best practices
- **slim_models_recommend**: Get AI model recommendations  
- **slim_models_validate**: Validate AI model configuration

## 📚 Available Resources

- **slim://registry**: Complete SLIM registry data
- **slim://models**: AI model information and recommendations

## 💬 Available Prompts

- **apply_best_practice**: Template for applying practices
- **review_practices**: Template for reviewing practices

## 🎯 Example Usage Scenarios

### 1. **New Open Source Project Setup**
```
"I'm starting a new open source Python project. What SLIM best practices should I apply and how?"
```

### 2. **Documentation Enhancement**
```
"Help me apply documentation best practices to my repository at https://github.com/user/my-project using AI"
```

### 3. **Security Improvement**
```
"Show me security-related best practices and apply them to my local repository"
```

### 4. **Governance Setup**
```
"Apply governance best practices for a small team to my project"
```

## 🔍 Verification

To verify the MCP server is working:

1. **Check server status** in Claude Code MCP settings
2. **Try a simple command**: "List all SLIM best practices"
3. **Look for the tools** in Claude Code's available tools list

## 📖 Server Information

- **Name**: SLIM-CLI MCP Server
- **Version**: 1.0.0
- **Protocol**: Model Context Protocol (MCP)
- **Framework**: FastMCP
- **Python Version**: 3.12+

## 🛠️ Troubleshooting

### Common Issues:

1. **"FastMCP not available"**
   - Make sure the virtual environment is activated
   - Install FastMCP: `pip install fastmcp`

2. **"SLIM-CLI modules not found"**
   - Ensure you're running from the SLIM-CLI directory
   - Check the PYTHONPATH in the configuration

3. **"Server not responding"**
   - Restart Claude Code
   - Check the MCP server logs
   - Verify the configuration file syntax

### Getting Help:

- Check the server logs for error messages
- Verify all dependencies are installed
- Ensure the server file path is correct in the configuration

## 🎉 Success!

Once installed, you can use natural language to interact with SLIM best practices through Claude Code. The MCP server will handle the technical details while providing a conversational interface for applying, deploying, and managing SLIM best practices.

**Example conversation:**
```
You: "Apply the README and contributing guidelines to my repository using AI"
Claude: "I'll help you apply those SLIM best practices. Let me use the SLIM MCP server to apply the README and contributing practices with AI customization..."
```

The server makes SLIM best practices more accessible and user-friendly through natural language interaction!