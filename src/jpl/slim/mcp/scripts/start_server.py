#!/usr/bin/env python3
"""
SLIM-CLI MCP Server Entry Point

This script starts the MCP server for use with Claude Code or other MCP clients.
"""

import sys
import os
import logging
from pathlib import Path

# Ensure we can import the MCP modules
sys.path.insert(0, str(Path(__file__).parent))

# Set up basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Start the MCP server."""
    try:
        # Import the server
        from mcp.server import main as server_main
        
        print("🚀 Starting SLIM-CLI MCP Server...")
        print("📡 Server will be available for MCP client connections")
        print("💡 Use Ctrl+C to stop the server")
        
        # Start the server
        server_main()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure all dependencies are installed:")
        print("   pip install 'mcp[cli]' typer rich gitpython")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()