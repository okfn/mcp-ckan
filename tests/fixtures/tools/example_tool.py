"""
Example tool module for testing
"""


def register_tools(mcp):
    """Register example tools with the MCP server"""

    @mcp.tool()
    def hello_world(name="World"):
        """A simple hello world tool

        Args:
            name (str, optional): Name to greet. Defaults to "World".

        Returns:
            str: A greeting message
        """
        return f"Hello, {name}! This is an example MCP tool."

    @mcp.tool()
    def add_numbers(a: int, b: int):
        """Add two numbers together

        Args:
            a (int): First number
            b (int): Second number

        Returns:
            str: The sum of the two numbers
        """
        result = a + b
        return f"The sum of {a} + {b} = {result}"
