"""
MCP Server with dynamic tool loading

This server automatically discovers and loads tools from installed python packages.
Each package should have an `ckan_mcp` entrypoint with a register_tools(mcp) function.
"""
import importlib.metadata

from mcp.server.fastmcp import FastMCP
from mcp_server.settings import MCP_FETCH_REMOTE, MCP_TRANSPORT, MCP_HOST, MCP_PORT


def load_plugins(mcp):
    for entry_point in importlib.metadata.entry_points(group='ckan_mcp'):
        print(f"Loading plugin: {entry_point.name}")
        register_tools = entry_point.load()
        register_tools(mcp)


def create_mcp_server(host, port):
    """Create MCP server with settings from environment variables"""
    mcp = FastMCP("Demo", host=host, port=port, streamable_http_path="/")
    load_plugins(mcp)
    return mcp


# Create server instance
mcp = create_mcp_server(MCP_HOST, MCP_PORT)

def main():
    print("=" * 60)
    print(
        f"Settings: host={MCP_HOST}, port={MCP_PORT} "
        f"transport={MCP_TRANSPORT}, fetch_remote={MCP_FETCH_REMOTE}"
    )
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
