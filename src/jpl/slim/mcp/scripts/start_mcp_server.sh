#!/bin/bash
# SLIM CLI MCP Server Wrapper Script
# Minimal wrapper that preserves working directory and starts the server

# Save the original working directory where Claude Code is running
ORIGINAL_CWD="$(pwd)"

# Auto-detect the script directory 
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Start the server from the original directory so repository analysis works correctly
cd "$ORIGINAL_CWD"
exec python3 "$SCRIPT_DIR/../server.py" "$@"