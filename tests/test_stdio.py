"""Tests for MCP server via stdio transport"""

import asyncio
import os
import sys
import unittest

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


FIXTURES_TOOLS = os.path.join(os.path.dirname(__file__), "fixtures", "tools")

SERVER_PARAMS = StdioServerParameters(
    command=sys.executable,
    args=["src/mcp_server/server.py"],
    env={
        "MCP_TRANSPORT": "stdio",
        "MCP_HOST": "127.0.0.1",
        "MCP_PORT": "8063",
        "MCP_TOOLS_DIR": FIXTURES_TOOLS,
        "MCP_FETCH_REMOTE": "false",
    },
)


class TestStdioInitialization(unittest.TestCase):
    """Server responds to MCP handshake via stdio"""

    def test_server_initializes(self):
        asyncio.run(self._test_server_initializes())

    async def _test_server_initializes(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                result = await session.initialize()
                self.assertEqual(result.serverInfo.name, "Demo")


class TestStdioToolDiscovery(unittest.TestCase):
    """Tool listing works via stdio"""

    def test_lists_tools(self):
        asyncio.run(self._test_lists_tools())

    async def _test_lists_tools(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                tool_names = [t.name for t in tools.tools]
                self.assertIn("hello_world", tool_names)
                self.assertIn("add_numbers", tool_names)

    def test_hello_world_schema(self):
        asyncio.run(self._test_hello_world_schema())

    async def _test_hello_world_schema(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                hw = next(t for t in tools.tools if t.name == "hello_world")
                props = hw.inputSchema.get("properties", {})
                self.assertIn("name", props)

    def test_add_numbers_schema(self):
        asyncio.run(self._test_add_numbers_schema())

    async def _test_add_numbers_schema(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                add = next(t for t in tools.tools if t.name == "add_numbers")
                props = add.inputSchema.get("properties", {})
                self.assertIn("a", props)
                self.assertIn("b", props)


class TestStdioHelloWorld(unittest.TestCase):
    """hello_world tool works via stdio"""

    def test_default_greeting(self):
        asyncio.run(self._test_default_greeting())

    async def _test_default_greeting(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("hello_world", arguments={})
                self.assertFalse(result.isError)
                text = result.content[0].text
                self.assertIn("Hello", text)
                self.assertIn("World", text)

    def test_custom_name(self):
        asyncio.run(self._test_custom_name())

    async def _test_custom_name(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "hello_world", arguments={"name": "Claudio"}
                )
                self.assertFalse(result.isError)
                text = result.content[0].text
                self.assertIn("Claudio", text)


class TestStdioAddNumbers(unittest.TestCase):
    """add_numbers tool works via stdio"""

    def test_basic_addition(self):
        asyncio.run(self._test_basic_addition())

    async def _test_basic_addition(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "add_numbers", arguments={"a": 5, "b": 7}
                )
                self.assertFalse(result.isError)
                self.assertIn("12", result.content[0].text)

    def test_negative_numbers(self):
        asyncio.run(self._test_negative_numbers())

    async def _test_negative_numbers(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "add_numbers", arguments={"a": -3, "b": 8}
                )
                self.assertFalse(result.isError)
                self.assertIn("5", result.content[0].text)

    def test_zeros(self):
        asyncio.run(self._test_zeros())

    async def _test_zeros(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "add_numbers", arguments={"a": 0, "b": 0}
                )
                self.assertFalse(result.isError)
                self.assertIn("0", result.content[0].text)


if __name__ == "__main__":
    unittest.main()
