import os


MCP_TRANSPORT = "stdio"

# HTTP mode settings (only used when MCP_TRANSPORT=http)
MCP_HOST = "127.0.0.1"
MCP_PORT = 8063

# Optionally override settings with local_settings.py (not committed to git)
try:
    from mcp_server.local_settings import *  # noqa: F401 F403
    print(" - Loaded settings from local_settings.py")
except ImportError:
    pass

# after all, if the use want to use env vars, we can also override settings with environment variables
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", MCP_TRANSPORT)
MCP_HOST = os.getenv("MCP_HOST", MCP_HOST)
MCP_PORT = int(os.getenv("MCP_PORT", MCP_PORT))
