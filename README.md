# Simple MCP Server to answer questions with data

**Note:** This project is currently in early research phase. Breaking changes are expected.

MCP Server that allows admins to register custom tools, by installing python packages, to consistently and accurately answer user questions using data.

## Running locally

### Install the project using UV
Sync dependencies:
```bash
uv sync
```

Run the tests:
```bash
uv run pytest
```

Run the server:
```bash
uv run mcp-ckan
```

## Fetching Remote Tools

To register remote tools just install a Python package that can register MCP tools for your particular datasets.
You can see an example at [https://github.com/okfn/mcp-ckan-examplepythontools](https://github.com/okfn/mcp-ckan-examplepythontools)

In a nutshell, you can extend by installing python plugins:

```bash
uv pip install "git+https://github.com/okfn/mcp-ckan"
uv pip install "git+https://github.com/okfn/mcp-ckan-examplepythontools"
uv run mcp-ckan
```

The MCP server is configured to load the tools at startup time by iterating throug all the installed python packages looking for `mcp_ckan` entrypoints.

### Developing a new MCP CKAN plugin

The Plugin needs to:

1. Be a proper python pip-installable package:

```bash
uv init --package mcp-ckan-exampleplugin
```

2. Define a `register_tools(mcp)` function that register tools in a MCP Server registry:

```python
from mcp_server import ToolOutput

def register_tools(registry):
    @registry.tool()
    def greetings_from_examplepythontools() -> ToolOutput:
        return ToolOutput(
            source="https://example.org",
            content="Hello from mcp_ckan_examplepythontools!"
        )
```

**Note:** This MCP server enforces [structured output](https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file#structured-output) and validates that the type returned is `ToolOutput`. If the function does not have the type annotation `-> ToolOutput` it will not be registered.

3. Register a new `mcp_ckan` entrypoint in the `pyproject.toml` file that calls the `register_tools` function.

```toml
[project.entry-points."mcp_ckan"]
mcp-ckan-examplepythontools = "mcp_ckan_examplepythontools:register_tools"
```

## ToolOutput

This MCP Server has a light-validation of the return type of the tools it registers. The goal of `ToolOutput` is to have a standarized communication between plugins and server.

Because Python is a dynamically typed language we can only validate (at startup time) function signatures. This will not ensure that the actual value returned at Runtime will
be a ToolOutput serialized object but it is a good-enough approach for early implementations.

You can check the [class documentation](./src/mcp_server/__init__.py) for more information.

## Server Settings

This (and other settings) can be configured via the `settings.py` file (or environment variables if defined).

- Set `MCP_TRANSPORT=stdio` (default) for local development and Claude Desktop integration
- Set `MCP_TRANSPORT=http` for remote infrastructure deployment
- Set `MCP_HOST` and `MCP_PORT` to control the server's host and port (default: 127.0.0.1:8063).

## Testing the server

### Test in VSCode with GitHub Copilot

Create the file `.vscode/mcp.json`:

```json
{
  "servers": {
    "mybcie-server": {
      "url": "http://127.0.0.1:8063",
      "type": "http"
    }
  },
  "inputs": []
}
```

### Run MCP Inspector

This tool allows you to test tools locally without any AI model.

```bash
npx @modelcontextprotocol/inspector uv run mcp-ckan
```

