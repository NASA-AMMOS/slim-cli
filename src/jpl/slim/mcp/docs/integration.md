# SLIM CLI Integration for Claude Code (Non-MCP)

Since MCP servers are not working in your environment, here's how to use SLIM CLI functionality directly with Claude Code:

## Available Commands

### 1. List Available Best Practices
```bash
# Using the enhanced script
python3 /home/rverma/src/slim-cli/quick_list_practices.py
```

### 2. Apply Best Practices with AI
```bash
# Apply README template with AI customization
python3 /home/rverma/src/slim-cli/apply_with_ai.py readme /path/to/repo

# Apply governance template
python3 /home/rverma/src/slim-cli/apply_with_ai.py governance /path/to/repo

# Apply any practice
python3 /home/rverma/src/slim-cli/apply_with_ai.py [practice-id] [repo-path]
```

### 3. Get AI Model Recommendations
```bash
python3 /home/rverma/src/slim-cli/get_models.py documentation balanced
```

## Integration Scripts Created

1. **quick_list_practices.py** - Lists all 9 SLIM best practices
2. **apply_with_ai.py** - Applies practices with AI coordination prompts
3. **get_models.py** - Provides AI model recommendations
4. **analyze_repo.py** - Analyzes repository context for customization

## Usage in Claude Code

Since MCP isn't working, you can still use SLIM functionality by:

1. **Running scripts directly**: Use the bash tool to run the integration scripts
2. **Following prompts**: The scripts provide AI coordination prompts for you to use
3. **Manual template application**: Apply templates and then use AI for customization

## Example Workflow

1. **List practices**: `python3 quick_list_practices.py`
2. **Choose practice**: Pick from the 9 available options
3. **Apply with AI**: `python3 apply_with_ai.py readme .`
4. **Follow prompts**: Use the generated prompts for AI customization

This gives you all the SLIM functionality without requiring MCP to work.