import os


MCP_TRANSPORT = "stdio"

# HTTP mode settings (only used when MCP_TRANSPORT=http)
# Host to bind to - use 127.0.0.1 for localhost-only (recommended with nginx)
# Default: 127.0.0.1
MCP_HOST = "127.0.0.1"

# Port to listen on in HTTP mode
MCP_PORT = 8063
MCP_FETCH_REMOTE = True
MCP_TOOLS_DIR = None

# Optionally override settings with local_settings.py (not committed to git)
try:
    from local_settings import *  # noqa: F401 F403
    print(" - Loaded settings from local_settings.py")
except ImportError:
    pass

# after all, if the use want to use env vars, we can also override settings with environment variables
MCP_TRANSPORT = os.getenv("MCP_TRANSPORT", MCP_TRANSPORT)
MCP_HOST = os.getenv("MCP_HOST", MCP_HOST)
MCP_PORT = int(os.getenv("MCP_PORT", MCP_PORT))
MCP_FETCH_REMOTE = os.getenv("MCP_FETCH_REMOTE", str(MCP_FETCH_REMOTE)).lower() in ("true", "1", "yes")
MCP_TOOLS_DIR = os.getenv("MCP_TOOLS_DIR", MCP_TOOLS_DIR)
