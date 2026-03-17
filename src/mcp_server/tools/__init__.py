"""
Dynamic tool loader for MCP server
Automatically discovers and loads tools from this directory
and from remote repositories declared in tool_sources.yaml.

Supports both Python modules (register_tools) and YAML dataset
definitions (routed to the engine system).
"""

import importlib
import logging
from pathlib import Path
from mcp_server.engines import load_dataset
from mcp_server.settings import MCP_TOOLS_DIR


log = logging.getLogger(__name__)


def _load_local_tools(mcp):
    """ Load tool modules from the local tools/ directory (or MCP_TOOLS_DIR if set).
        We look for all python files in the directory
        (except __init__.py and files starting with _)
        and try to import them as modules. If they have a register_tools(mcp) function,
        we call it to register their tools with the MCP server.
        We also look for any YAML dataset definitions in the same directory.
    """
    if MCP_TOOLS_DIR:
        tools_dir = Path(MCP_TOOLS_DIR)
        log.info(f"Loading local tools from MCP_TOOLS_DIR={tools_dir}")
    else:
        tools_dir = Path(__file__).parent
        log.info("Loading local tools from tools/ directory")

    py_files = [
        f for f in tools_dir.glob("*.py")
        if f.stem != "__init__" and not f.stem.startswith("_")
    ]

    loaded = 0
    for py_file in py_files:
        tool_name = py_file.stem
        log.debug(f" - Attempting to load local tool module: {tool_name}")
        try:
            if MCP_TOOLS_DIR:
                spec = importlib.util.spec_from_file_location(f"tools.{tool_name}", py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                module = importlib.import_module(f"tools.{tool_name}")
            if hasattr(module, "register_tools"):
                module.register_tools(mcp)
                loaded += 1
                log.info(f"Loaded local tool module: {tool_name}")
            else:
                log.warning(f"Local tool module {tool_name} does not have register_tools() function")
        except Exception as e:
            log.error(f"Error loading local tool module {tool_name}: {e}")

    # Also load YAML datasets from the tools directory
    loaded += _load_yaml_datasets(mcp, tools_dir, "local")

    return loaded


def _load_yaml_datasets(mcp, directory, label):
    """Scan a directory for .yaml dataset files and load via engine system.

    Args:
        mcp: FastMCP server instance
        directory: Path to scan
        label: Label for log messages (e.g. "local" or "remote:portal-bcie")

    Returns:
        int: Number of tools loaded
    """
    yaml_files = sorted(directory.glob("*.yaml"))
    if not yaml_files:
        return 0

    loaded = 0
    for yaml_file in yaml_files:
        try:
            count = load_dataset(mcp, yaml_file)
            loaded += count
            log.info(f"  [{label}] {yaml_file.stem} ({count} tools via engine)")
        except Exception as e:
            log.error(f"  [{label}] error loading {yaml_file.stem}.yaml: {e}")

    return loaded

