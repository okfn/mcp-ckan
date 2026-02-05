"""
Dynamic tool loader for MCP server
Automatically discovers and loads tools from this directory
"""

import importlib
from pathlib import Path


def load_tools(mcp):
    """
    Dynamically load all tools from the tools directory

    Args:
        mcp: FastMCP server instance

    Each tool module should have a register_tools(mcp) function that
    registers its tools with the MCP server using decorators.
    """
    tools_dir = Path(__file__).parent

    # Find all Python files in the tools directory (except __init__.py)
    tool_files = [
        f.stem for f in tools_dir.glob("*.py")
        if f.stem != "__init__" and not f.stem.startswith("_")
    ]

    loaded_count = 0
    for tool_name in tool_files:
        try:
            # Import the tool module
            module = importlib.import_module(f"tools.{tool_name}")

            # Check if the module has a register_tools function
            if hasattr(module, "register_tools"):
                module.register_tools(mcp)
                loaded_count += 1
                print(f"✓ Loaded tool module: {tool_name}")
            else:
                print(f"⚠ Skipping {tool_name}: no register_tools() function found")

        except Exception as e:
            print(f"✗ Error loading tool {tool_name}: {e}")

    print(f"\nTotal tools loaded: {loaded_count}")
    return loaded_count
