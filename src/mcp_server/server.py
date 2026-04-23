"""
MCP Server with dynamic tool loading

This server automatically discovers and loads tools from installed python packages.
Each package should have an `mcp_ckan` entrypoint with a register_tools(registry) function.
"""
import importlib
import logging
import pkgutil

from mcp.server.fastmcp import FastMCP

from mcp_server.engines import load_dataset
from mcp_server.registry import ToolRegistry
from mcp_server.settings import MCP_TRANSPORT, MCP_HOST, MCP_PORT

log = logging.getLogger(__name__)


def load_python_plugins(registry):
    """Load Python tools defined in plugins."""
    for entry_point in importlib.metadata.entry_points():
        if entry_point.group == "mcp_ckan":
            log.info(f"[{entry_point.module}] - python tools.")
            register_tools = entry_point.load()
            register_tools(registry)


def load_yaml_plugins(registry):
    """Load YAML tools defined in plugins.

    The YAML tools are based on our engines. It will use a name-convention look for plugin
    packages (like Flask).

    https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/#using-naming-convention
    """
    discovered_plugins = [name for _, name, _ in pkgutil.iter_modules() if name.startswith('mcp_ckan_')]
    for plugin in discovered_plugins:
        resources = importlib.resources.files(plugin)
        for resource in resources.rglob('*.yaml'):
            log.info(f"[{plugin}] - {resource.name}")
            load_dataset(registry, resource)


def create_mcp_server(host, port):
    """Create MCP server with settings from environment variables"""
    mcp = FastMCP("Demo", host=host, port=port, streamable_http_path="/")
    registry = ToolRegistry(mcp)
    load_python_plugins(registry)
    load_yaml_plugins(registry)
    return mcp


# Create server instance
mcp = create_mcp_server(MCP_HOST, MCP_PORT)


def main():
    log.info("=" * 60)
    log.info(f"Settings: host={MCP_HOST}, port={MCP_PORT} transport={MCP_TRANSPORT}")
    log.info("=" * 60)

    if MCP_TRANSPORT == "http":
        # HTTP mode for infrastructure deployment
        mcp.run(transport="streamable-http")
    else:
        # stdio mode (default) for local development
        mcp.run(transport="stdio")
