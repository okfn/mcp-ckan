"""Tests for MCP server via HTTP transport"""

import asyncio
import os
import socket
import subprocess
import sys
import time
import unittest

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


FIXTURES_TOOLS = os.path.join(os.path.dirname(__file__), "fixtures", "tools")

HTTP_PORT = 9753
HTTP_URL = f"http://127.0.0.1:{HTTP_PORT}/"

_server_process = None


def setUpModule():
    global _server_process
    env = os.environ.copy()
    env.update({
        "MCP_TRANSPORT": "http",
        "MCP_HOST": "127.0.0.1",
        "MCP_PORT": str(HTTP_PORT),
        "MCP_TOOLS_DIR": FIXTURES_TOOLS,
        "MCP_FETCH_REMOTE": "false",
    })
    _server_process = subprocess.Popen(
        [sys.executable, "src/mcp_server/server.py"],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _wait_for_server()


def tearDownModule():
    global _server_process
    if _server_process:
        _server_process.terminate()
        _server_process.wait(timeout=5)
        _server_process = None


def _wait_for_server(timeout=10):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            sock = socket.create_connection(("127.0.0.1", HTTP_PORT), timeout=1)
            sock.close()
            return
        except OSError:
            time.sleep(0.2)
    raise RuntimeError(f"HTTP server did not start within {timeout}s")


class TestHttpInitialization(unittest.TestCase):
    """Server responds to MCP handshake via HTTP"""

    def test_server_initializes(self):
        asyncio.run(self._test_server_initializes())

    async def _test_server_initializes(self):
        async with streamable_http_client(HTTP_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                result = await session.initialize()
                self.assertEqual(result.serverInfo.name, "Demo")


class TestHttpToolDiscovery(unittest.TestCase):
    """Tool listing works via HTTP"""

    def test_lists_tools(self):
        asyncio.run(self._test_lists_tools())

    async def _test_lists_tools(self):
        async with streamable_http_client(HTTP_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                tool_names = [t.name for t in tools.tools]
                self.assertIn("hello_world", tool_names)
                self.assertIn("add_numbers", tool_names)


class TestHttpHelloWorld(unittest.TestCase):
    """hello_world tool works via HTTP"""

    def test_default_greeting(self):
        asyncio.run(self._test_default_greeting())

    async def _test_default_greeting(self):
        async with streamable_http_client(HTTP_URL) as (read, write, _):
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
        async with streamable_http_client(HTTP_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "hello_world", arguments={"name": "Claudio"}
                )
                self.assertFalse(result.isError)
                self.assertIn("Claudio", result.content[0].text)


class TestHttpAddNumbers(unittest.TestCase):
    """add_numbers tool works via HTTP"""

    def test_basic_addition(self):
        asyncio.run(self._test_basic_addition())

    async def _test_basic_addition(self):
        async with streamable_http_client(HTTP_URL) as (read, write, _):
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
        async with streamable_http_client(HTTP_URL) as (read, write, _):
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
        async with streamable_http_client(HTTP_URL) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "add_numbers", arguments={"a": 0, "b": 0}
                )
                self.assertFalse(result.isError)
                self.assertIn("0", result.content[0].text)


if __name__ == "__main__":
    unittest.main()
