"""
MCP Server with dynamic tool loading

This server automatically discovers and loads tools from the tools/ directory.
Each tool module should have a register_tools(mcp) function.
"""

import os
import sys
from mcp.server.fastmcp import FastMCP
from mcp_server.tools import load_tools
from mcp_server.settings import MCP_FETCH_REMOTE, MCP_TRANSPORT, MCP_HOST, MCP_PORT


# Add src directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))


def create_mcp_server(host, port):
    """Create MCP server with settings from environment variables"""
    return FastMCP("Demo", host=host, port=port, streamable_http_path="/")


# Create server instance
mcp = create_mcp_server(MCP_HOST, MCP_PORT)

def main():
    print("=" * 60)
    print("Loading MCP Tools")
    print("=" * 60)
    print(
        f"Settings: host={MCP_HOST}, port={MCP_PORT} "
        f"transport={MCP_TRANSPORT}, fetch_remote={MCP_FETCH_REMOTE}"
    )
    load_tools(mcp)
    print("=" * 60)

    if MCP_TRANSPORT == "http":
        # HTTP mode for infrastructure deployment
        mcp.run(transport="streamable-http")
    else:
        # stdio mode (default) for local development
        mcp.run(transport="stdio")

if __name__ == "__main__":
    # Required for tests.
    # TODO: Refactor tests properly.
    main()
