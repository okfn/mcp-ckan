"""
Dynamic tool loader for MCP server
Automatically discovers and loads tools from this directory
and from remote repositories declared in tool_sources.yaml.

Supports both Python modules (register_tools) and YAML dataset
definitions (routed to the engine system).
"""

import importlib
import logging
import yaml
from pathlib import Path
from mcp_server.engines import load_dataset
from mcp_server.lib.remote_tools import fetch_remote_tools
from mcp_server.settings import MCP_FETCH_REMOTE, MCP_TOOLS_DIR


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


def _load_remote_tools(mcp):
    """ Load tool modules from remote repos declared in tool_sources.yaml.
        This way, we can register mcp tools defined in remote repositories
        without having to deploy new code to the MCP server.
    """
    log.info("Loading remote tools from manifest...")
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    manifest = project_root / "deploy/tool_sources.yaml"
    remote_dir = project_root / "remote_tools"

    if not manifest.exists():
        log.warning(f"Remote tool manifest not found: {manifest}. Skipping remote tools.")
        return 0

    with open(manifest) as f:
        config = yaml.safe_load(f)

    sources = config.get("sources") or []
    if not sources:
        log.warning(f"No remote tool sources defined in manifest: {manifest}")
        return 0

    loaded = 0
    for source in sources:
        log.info(f" - Loading remote tools from source: {source.get('name', 'unknown')}")
        name = source["name"]
        path = source.get("path", ".")
        tools_path = remote_dir / name / path

        if not tools_path.is_dir():
            log.warning(f"Remote tool directory not found for source {name}: {tools_path} (run fetch_remote_tools.py first)")
            continue

        # Load Python tool modules
        py_files = [
            f for f in tools_path.glob("*.py")
            if not f.stem.startswith("_")
        ]

        for py_file in py_files:
            module_name = f"remote_tools.{name}.{py_file.stem}"
            log.info(f"Attempting to load remote tool module: {module_name} from {py_file}")
            try:
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, "register_tools"):
                    module.register_tools(mcp)
                    loaded += 1
                    log.info(f"  [remote:{name}] {py_file.stem}")
                else:
                    log.warning(f"  [remote:{name}] skipping {py_file.stem}: no register_tools()")
            except Exception as e:
                log.error(f"  [remote:{name}] error loading {py_file.stem}: {e}")

        # Load YAML dataset definitions
        loaded += _load_yaml_datasets(mcp, tools_path, f"remote:{name}")

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
    log.info(f"Scanning for YAML datasets in {directory}...")
    yaml_files = sorted(directory.glob("*.yaml"))
    if not yaml_files:
        log.info(f"No YAML datasets found in {directory}.")
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


def load_tools(mcp):
    """
    Dynamically load all tools from the tools directory
    and from remote repositories declared in tool_sources.yaml.

    Supports both Python modules (with register_tools function)
    and SQL or YAML dataset definitions (routed to the engine system).

    Args:
        mcp: FastMCP server instance

    Each tool module should have a register_tools(mcp) function that
    registers its tools with the MCP server using decorators.
    """
    log.info("\nLocal tools:")
    local_count = _load_local_tools(mcp)

    # When MCP_TOOLS_DIR is set, skip remote tools entirely
    if MCP_TOOLS_DIR:
        log.info("\nSkipping remote tools (MCP_TOOLS_DIR is set)")
        log.info(f"\nTotal tools loaded: {local_count}")
        return local_count

    # Fetch remote tool repositories before loading (default: enabled)
    if MCP_FETCH_REMOTE:
        log.info("\nFetching remote tool repositories...")
        errors = fetch_remote_tools()
        if errors:
            log.warning(f"Remote fetch completed with {errors} error(s)")
    else:
        log.info("\nSkipping remote tool fetch (MCP_FETCH_REMOTE=false)")

    log.info("\nRemote tools:")
    remote_count = _load_remote_tools(mcp)

    total = local_count + remote_count
    log.info(f"\nTotal tools loaded: {total} ({local_count} local, {remote_count} remote)")
    return total
