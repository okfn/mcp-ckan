"""
Engine registry and dataset loader

Routes YAML dataset definitions to the appropriate engine (yaml or sql)
and provides a meta-tool to list all loaded datasets.
"""

from pathlib import Path

import yaml

from mcp_server.engines.unique_values_engine import load_unique_values_dataset
from mcp_server.engines.aggregate_engine import load_aggregate_dataset
from mcp_server.engines.top_row_engine import load_top_row_dataset
from mcp_server.engines.row_list_engine import load_row_list_dataset


ENGINES = {
    "unique_values": load_unique_values_dataset,
    "aggregate": load_aggregate_dataset,
    "top_row": load_top_row_dataset,
    "row_list": load_row_list_dataset,
}

# Track all loaded datasets for the meta-tool
_loaded_datasets = []


def load_dataset(mcp, yaml_path):
    """Load a single YAML dataset definition and register its tools.

    Args:
        mcp: FastMCP server instance
        yaml_path: Path to the .yaml dataset file
    """
    yaml_path = Path(yaml_path)

    with open(yaml_path) as f:
        config = yaml.safe_load(f)

    engine_name = config.get("engine")
    if not engine_name:
        raise ValueError(f"{yaml_path}: missing 'engine' field")

    loader = ENGINES.get(engine_name)
    if not loader:
        raise ValueError(f"{yaml_path}: unknown engine '{engine_name}'. Available: {list(ENGINES.keys())}")

    tool_count = loader(mcp, config, yaml_path)

    # Track the loaded dataset
    dataset_info = config.get("dataset", {})
    _loaded_datasets.append({
        "name": dataset_info.get("name", yaml_path.stem),
        "description": dataset_info.get("description", ""),
        "engine": engine_name,
        "source": dataset_info.get("source", {}),
        "file": str(yaml_path),
        "tool_count": tool_count,
    })

    return tool_count


def load_datasets_from_dir(mcp, directory):
    """Scan a directory for .yaml dataset files and load each one.

    Args:
        mcp: FastMCP server instance
        directory: Path to scan for .yaml files

    Returns:
        int: Number of tools loaded
    """
    directory = Path(directory)
    if not directory.is_dir():
        return 0

    total = 0
    for yaml_file in sorted(directory.glob("*.yaml")):
        try:
            count = load_dataset(mcp, yaml_file)
            total += count
        except Exception as e:
            print(f"  [engine] error loading {yaml_file.name}: {e}")

    return total
