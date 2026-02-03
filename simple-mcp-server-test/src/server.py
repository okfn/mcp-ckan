"""MCP Server with dual-mode transport support.

Supports both stdio (local) and HTTP (infrastructure) transports.
Set MCP_TRANSPORT environment variable to control mode:
    - MCP_TRANSPORT=stdio (default): For local development and Claude Desktop integration
    - MCP_TRANSPORT=http: For remote infrastructure deployment
"""

import os
from mcp.server.mcpserver import MCPServer

# Create an MCP server
mcp = MCPServer("Demo")


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


# Add a prompt
@mcp.prompt()
def greet_user(name: str, style: str = "friendly") -> str:
    """Generate a greeting prompt"""
    styles = {
        "friendly": "Please write a warm, friendly greeting",
        "formal": "Please write a formal, professional greeting",
        "casual": "Please write a casual, relaxed greeting",
    }

    return f"{styles.get(style, styles['friendly'])} for someone named {name}."


# Run with configured transport
if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()

    if transport == "http":
        # HTTP mode for infrastructure deployment
        mcp.run(transport="streamable-http", json_response=True)
    else:
        # stdio mode (default) for local development
        mcp.run(transport="stdio")
