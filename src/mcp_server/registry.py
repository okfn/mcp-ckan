import inspect

from mcp.server.fastmcp import FastMCP

from mcp_server import ToolOutput


class ToolRegistry:
    """Controls tool registration and enforces the ToolOutput contract.

    Wraps a FastMCP instance and intercepts every ``tool()`` call to verify that
    the function declares ``-> ToolOutput`` in its return annotation.  Validation
    happens at registration time (server startup), not at call time, so invalid
    tools fail fast before any client request is served.

    Plugins and engines must use this registry instead of calling ``mcp.tool()``
    directly.  The ``tool()`` method returns the same decorator API as FastMCP
    so existing patterns (``@registry.tool()`` and ``registry.tool()(fn)``) work
    unchanged.
    """

    def __init__(self, mcp: FastMCP):
        self._mcp = mcp

    def tool(self):
        """Decorator that registers a function with FastMCP after validating its
        return type annotation.

        Raises:
            TypeError: If the function's return annotation is not ``ToolOutput``.
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
                raise TypeError(
                    f"{fn.__name__}: return annotation must be ToolOutput, got {got}"
                )
            return self._mcp.tool()(fn)
        return decorator
