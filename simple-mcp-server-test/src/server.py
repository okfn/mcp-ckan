"""
MCP Server with dynamic tool loading

This server automatically discovers and loads tools from the tools/ directory.
Each tool module should have a register_tools(mcp) function.
"""

import os
import sys
from mcp.server.fastmcp import FastMCP

# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from tools import load_tools


def create_mcp_server():
    """Create MCP server with settings from environment variables"""
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8063"))
    return FastMCP("Demo", host=host, port=port, streamable_http_path="/")


# Create server instance
mcp = create_mcp_server()

# Dynamically load all tools from tools/ directory
print("=" * 60)
print("Loading MCP Tools")
print("=" * 60)
load_tools(mcp)
print("=" * 60)


# Run with configured transport
if __name__ == "__main__":

    required = ["MCP_TRANSPORT", "MCP_HOST", "MCP_PORT"]
    for var in required:
        if os.getenv(var) is None:
            print(f"Error: Environment variable {var} is not set.")
            exit(1)

    transport = os.getenv("MCP_TRANSPORT")

    if transport == "http":
        # HTTP mode for infrastructure deployment
        print(f"\nStarting MCP server in HTTP mode on {os.getenv('MCP_HOST')}:{os.getenv('MCP_PORT')}\n")
        mcp.run(transport="streamable-http")
    else:
        # stdio mode (default) for local development
        mcp.run(transport="stdio")
