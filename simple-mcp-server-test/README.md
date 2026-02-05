# Simple MCP server test

MCP Server with dual-mode transport support.

Supports both stdio (local) and HTTP (infrastructure) transports.  

Set MCP_TRANSPORT environment variable to control mode:

  - MCP_TRANSPORT=stdio (default): For local development and Claude Desktop integration
  - MCP_TRANSPORT=http: For remote infrastructure deployment

## Test

Run the actual MCP server:
# For local stdio mode
MCP_TRANSPORT=stdio MCP_HOST=127.0.0.1 MCP_PORT=8063 .venv/bin/python src/server.py

# For HTTP mode (infrastructure deployment)
MCP_TRANSPORT=http MCP_HOST=127.0.0.1 MCP_PORT=8063 .venv/bin/python src/server.py

## Run the server

```
MCP_TRANSPORT=http MCP_HOST=127.0.0.1 MCP_PORT=8063 .venv/bin/python src/server.py
```

## Test in vscode with GH copilot

Create the file `.vscode/mcp.json`

{
  "servers": {
    "mybcie-server": {
      "url": "http://127.0.0.1:8063",
      "type": "http",
    }
  },
  "inputs": []
}

## Run inspector

This tool allow you to test tools locally without any AI model.

```
npx @modelcontextprotocol/inspector .venv/bin/python src/server.py
MCP_TRANSPORT=stdio MCP_HOST=127.0.0.1 MCP_PORT=8063 npx @modelcontextprotocol/inspector .venv/bin/python src/server.py
```

## Dynamic MCP tools

Tools are dynamically loaded from external sources.  
This MCP will serve tools that our users will manually define.  

