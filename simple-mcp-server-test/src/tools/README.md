# MCP Tools Directory

This directory contains dynamically loaded MCP tools.

## How It Works

1. The server automatically discovers all `.py` files in this directory
2. Each file should have a `register_tools(mcp)` function
3. Tools are registered using the `@mcp.tool()` decorator
4. When the server starts, all tools are loaded automatically

## Adding a New Tool

1. **Create a new Python file** (e.g., `my_tool.py`)
2. **Implement the registration function:**

```python
def register_tools(mcp):
    """Register your tools with the MCP server"""

    @mcp.tool()
    def my_tool_name(param1, param2=None):
        """Tool description that AI will see

        Args:
            param1 (str): Description of parameter
            param2 (int, optional): Description of optional parameter

        Returns:
            str: Description of what the tool returns
        """
        # Your tool logic here
        result = do_something(param1, param2)
        return f"Result: {result}"
```

3. **Restart the server** - your tool will be automatically loaded!

## Best Practices

- **Clear docstrings**: AI uses these to understand when and how to use your tool
- **Type hints**: Help with parameter validation
- **Return strings**: MCP clients expect text responses
- **Error handling**: Return user-friendly error messages as strings
- **Validation**: Validate inputs and return helpful error messages

## Examples

- `bcie_loans.py` - Real-world tool fetching data from an API
- `example_tool.py` - Simple examples showing basic patterns

## Tool Naming

- Use descriptive names: `get_loan_data` not `tool1`
- Use snake_case: `fetch_user_info` not `fetchUserInfo`
- Be specific: `get_bcie_loans` better than `get_loans`
