"""
Dynamic tool loader for MCP server
Automatically discovers and loads tools from this directory
and from remote repositories declared in tool_sources.yaml
"""

import importlib
import importlib.util
from pathlib import Path


def _load_local_tools(mcp):
    """Load tool modules from the local tools/ directory."""
    tools_dir = Path(__file__).parent

    tool_files = [
        f.stem for f in tools_dir.glob("*.py")
        if f.stem != "__init__" and not f.stem.startswith("_")
    ]

    loaded = 0
    for tool_name in tool_files:
        try:
            module = importlib.import_module(f"tools.{tool_name}")
            if hasattr(module, "register_tools"):
                module.register_tools(mcp)
                loaded += 1
                print(f"  [local] {tool_name}")
            else:
                print(f"  [local] skipping {tool_name}: no register_tools()")
        except Exception as e:
            print(f"  [local] error loading {tool_name}: {e}")

    return loaded


def _load_remote_tools(mcp):
    """Load tool modules from remote repos declared in tool_sources.yaml."""
    project_root = Path(__file__).resolve().parent.parent.parent
    manifest = project_root / "tool_sources.yaml"
    remote_dir = project_root / "remote_tools"

    if not manifest.exists():
        return 0

    try:
        import yaml
    except ImportError:
        print("  [remote] pyyaml not installed — skipping remote tools")
        return 0

    with open(manifest) as f:
        config = yaml.safe_load(f)

    sources = config.get("sources") or []
    if not sources:
        return 0

    loaded = 0
    for source in sources:
        name = source["name"]
        path = source.get("path", ".")
        tools_path = remote_dir / name / path

        if not tools_path.is_dir():
            print(f"  [remote] skipping {name}: directory not found (run fetch_remote_tools.py first)")
            continue

        py_files = [
            f for f in tools_path.glob("*.py")
            if not f.stem.startswith("_")
        ]

        for py_file in py_files:
            module_name = f"remote_tools.{name}.{py_file.stem}"
            try:
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, "register_tools"):
                    module.register_tools(mcp)
                    loaded += 1
                    print(f"  [remote:{name}] {py_file.stem}")
                else:
                    print(f"  [remote:{name}] skipping {py_file.stem}: no register_tools()")
            except Exception as e:
                print(f"  [remote:{name}] error loading {py_file.stem}: {e}")

    return loaded


def load_tools(mcp):
    """
    Dynamically load all tools from the tools directory
    and from remote repositories declared in tool_sources.yaml.

    Args:
        mcp: FastMCP server instance

    Each tool module should have a register_tools(mcp) function that
    registers its tools with the MCP server using decorators.
    """
    print("\nLocal tools:")
    local_count = _load_local_tools(mcp)

    print("\nRemote tools:")
    remote_count = _load_remote_tools(mcp)

    total = local_count + remote_count
    print(f"\nTotal tools loaded: {total} ({local_count} local, {remote_count} remote)")
    return total
