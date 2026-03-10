# Simple MCP server test

MCP Server with dual-mode transport support.
Supports both stdio (local) and HTTP (infrastructure) transports.

## Running locally

### Install the project using UV
Sync dependencies:
```bash
uv sync
```

Activate the virtual environment:
```bash
source .venv/bin/activate
```

Run the server:
```bash
uv run mcp-server
# or
python src/mcp_server/server.py
```

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
npx @modelcontextprotocol/inspector uv run mcp-server
# or
npx @modelcontextprotocol/inspector .venv/bin/python src/mcp_server/server.py
```

### Running Tests

```bash
source .venv/bin/activate
pytest
```

## Server Settings

This (and other settings) can be configured via the `settings.py` file (or environment variables if defined).

- Set `MCP_TRANSPORT=stdio` (default) for local development and Claude Desktop integration
- Set `MCP_TRANSPORT=http` for remote infrastructure deployment
- Set `MCP_FETCH_REMOTE` True/False to control whether to fetch remote tools on startup (default: True).
- Set `MCP_HOST` and `MCP_PORT` to control the server's host and port (default: 127.0.0.1:8063).

## Fetching Remote Tools

Remote tools are configured in `deploy/tool_sources.yaml`. To fetch them:

1. Ensure SSH keys are in place at `deploy/keys/` (if using private repos)
2. Run the fetch script:
   ```bash
   python src/mcp_server/scripts/fetch_remote_tools.py
   ```
3. Restart the server to load the new tools

## Dynamic MCP tools

Tools are dynamically loaded from external sources.
This MCP will serve tools that our users will manually define.

