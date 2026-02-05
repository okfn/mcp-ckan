#!/usr/bin/env python3
"""
Full MCP client using official SDK
"""

import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_local():
    """Test local MCP server via stdio"""
    server_params = StdioServerParameters(
        command=".venv/bin/python",
        args=["src/server.py"],
        env={
            "MCP_TRANSPORT": "stdio",
            "MCP_HOST": "127.0.0.1",
            "MCP_PORT": "8063"
        }
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List tools
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"  • {tool.name}: {tool.description[:80]}...")

            # Call a tool
            print("\nTesting prestamos_por_pais for Honduras:")
            result = await session.call_tool(
                "prestamos_por_pais",
                arguments={"country": "Honduras"}
            )
            print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(test_local())
