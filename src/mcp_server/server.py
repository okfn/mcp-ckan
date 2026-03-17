"""
MCP Server with dynamic tool loading

This server automatically discovers and loads tools from installed python packages.
Each package should have an `mcp_ckan` entrypoint with a register_tools(mcp) function.
"""
import importlib
import logging
import pkgutil

from mcp.server.fastmcp import FastMCP

from mcp_server.engines import load_dataset
from mcp_server.settings import MCP_TRANSPORT, MCP_HOST, MCP_PORT

log = logging.getLogger(__name__)


def load_python_plugins(mcp):
    """Load Python tools defined in plugins."""
    for entry_point in importlib.metadata.entry_points(group='mcp_ckan'):
        log.info(f"Loading plugin: {entry_point.module}")
        register_tools = entry_point.load()
        register_tools(mcp)


def load_yaml_plugins(mcp):
    """Load YAML tools defined in plugins.

    The YAML tools are based on our engines. It will use a name-convention look for plugin
    packages (like Flask).

    https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/#using-naming-convention
    """
    discovered_plugins = [name for _, name, _ in pkgutil.iter_modules() if name.startswith('mcp_ckan_')]
    for plugin in discovered_plugins:
        resources = importlib.resources.files(plugin)
        for resource in resources.rglob('*.yaml'):
            log.info(f"Loading {resource}")
            load_dataset(mcp, resource)


def create_mcp_server(host, port):
    """Create MCP server with settings from environment variables"""
    mcp = FastMCP("Demo", host=host, port=port, streamable_http_path="/")
    load_python_plugins(mcp)
    load_yaml_plugins(mcp)
    return mcp


# Create server instance
mcp = create_mcp_server(MCP_HOST, MCP_PORT)

def main():
    print("=" * 60)
    print(
        f"Settings: host={MCP_HOST}, port={MCP_PORT} transport={MCP_TRANSPORT}"
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
