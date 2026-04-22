import inspect
import logging

from mcp.server.fastmcp import FastMCP

from mcp_server import ToolOutput

log = logging.getLogger(__name__)


class ToolRegistry:
    """Controls tool registration and enforces the ToolOutput contract.

    Wraps a FastMCP instance and intercepts every ``tool()`` call to verify that
    the function declares ``-> ToolOutput`` in its return annotation.  Validation
    happens at registration time (server startup).

    Tools that do not declare the correct return annotation are **not registered**
    and a warning is logged instead.  This allows the server to start and serve
    only its valid tools.

    Plugins and engines must use this registry instead of calling ``mcp.tool()``
    directly.  The ``tool()`` method returns the same decorator API so existing
    patterns (``@registry.tool()`` and ``registry.tool()(fn)``) work unchanged.
    """

    def __init__(self, mcp: FastMCP):
        self._mcp = mcp

    def tool(self):
        """Decorator that registers a function with FastMCP after validating its
        return type annotation.

        If the return annotation is not ``ToolOutput``, logs a warning and returns
        the original function **without** registering it with FastMCP.
        """
        def decorator(fn):
            sig = inspect.signature(fn)
            return_annotation = sig.return_annotation
            if return_annotation is inspect.Parameter.empty or return_annotation is not ToolOutput:
                got = (
                    "none"
                    if return_annotation is inspect.Parameter.empty
                    else return_annotation.__name__
                )
                log.warning(
                    "Skipping tool '%s': return annotation must be ToolOutput, got %s",
                    fn.__name__,
                    got,
                )
                return fn
            return self._mcp.tool()(fn)
        return decorator
