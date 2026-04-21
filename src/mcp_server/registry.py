import inspect

from mcp.server.fastmcp import FastMCP

from mcp_server import ToolOutput


class ToolRegistry:
    def __init__(self, mcp: FastMCP):
        self._mcp = mcp

    def tool(self):
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
