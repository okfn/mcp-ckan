"""Integration tests for the declarative dataset engine system (YAML engines)

Uses self-contained fixtures in tests/fixtures/ so no remote tools are needed.
"""

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


class TestToolDiscovery(unittest.TestCase):
    """Engine-loaded tools appear in tool listing"""

    def test_engine_tools_listed(self):
        asyncio.run(self._test())

    async def _test(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                tools = await session.list_tools()
                tool_names = [t.name for t in tools.tools]
                # Python tools
                self.assertIn("hello_world", tool_names)
                self.assertIn("add_numbers", tool_names)
                # YAML engine tools
                self.assertIn("list_projects", tool_names)
                self.assertIn("total_projects", tool_names)
                self.assertIn("top_project", tool_names)
                self.assertIn("project_countries", tool_names)
                self.assertIn("project_countries_semicolon", tool_names)


class TestRowListEngine(unittest.TestCase):
    """row_list engine works via MCP"""

    def test_all_rows(self):
        asyncio.run(self._test_all_rows())

    async def _test_all_rows(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("list_projects", arguments={})
                self.assertFalse(result.isError)
                text = result.content[0].text
                self.assertIn("10", text)  # 10 rows
                self.assertIn("Source", text)

    def test_filter_by_country(self):
        asyncio.run(self._test_filter_by_country())

    async def _test_filter_by_country(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "list_projects", arguments={"country": "Brazil"}
                )
                self.assertFalse(result.isError)
                text = result.content[0].text
                self.assertIn("Brazil", text)
                self.assertIn("4", text)  # 4 Brazil rows

    def test_invalid_country(self):
        asyncio.run(self._test_invalid_country())

    async def _test_invalid_country(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "list_projects", arguments={"country": "Atlantis"}
                )
                self.assertFalse(result.isError)
                text = result.content[0].text
                self.assertIn("error", text.lower())

    def test_filter_by_year_range(self):
        asyncio.run(self._test_filter_by_year_range())

    async def _test_filter_by_year_range(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "list_projects", arguments={"year_from": 2021, "year_to": 2022}
                )
                self.assertFalse(result.isError)
                text = result.content[0].text
                # 6 rows in 2021-2022
                self.assertIn("6", text)


class TestAggregateEngine(unittest.TestCase):
    """aggregate engine works via MCP"""

    def test_total_all(self):
        asyncio.run(self._test_total_all())

    async def _test_total_all(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("total_projects", arguments={})
                self.assertFalse(result.isError)
                text = result.content[0].text
                self.assertIn("$", text)
                self.assertIn("28,057.00", text)

    def test_filter_by_country(self):
        asyncio.run(self._test_filter_by_country())

    async def _test_filter_by_country(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "total_projects", arguments={"country": "Argentina"}
                )
                self.assertFalse(result.isError)
                text = result.content[0].text
                self.assertIn("$", text)
                self.assertIn("5,500.00", text)  # 1500+2200+1800


class TestTopRowEngine(unittest.TestCase):
    """top_row engine works via MCP"""

    def test_top_project(self):
        asyncio.run(self._test_top_project())

    async def _test_top_project(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("top_project", arguments={})
                self.assertFalse(result.isError)
                text = result.content[0].text
                self.assertIn("Chile", text)
                self.assertIn("5,000.00", text)

    def test_top_project_filtered(self):
        asyncio.run(self._test_top_project_filtered())

    async def _test_top_project_filtered(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "top_project", arguments={"country": "Brazil"}
                )
                self.assertFalse(result.isError)
                text = result.content[0].text
                self.assertIn("Brazil", text)
                self.assertIn("4,100.00", text)


class TestUniqueValuesEngine(unittest.TestCase):
    """unique_values engine works via MCP"""

    def test_list_countries(self):
        asyncio.run(self._test_list_countries())

    async def _test_list_countries(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("project_countries", arguments={})
                self.assertFalse(result.isError)
                text = result.content[0].text
                self.assertIn("Argentina", text)
                self.assertIn("Brazil", text)
                self.assertIn("Chile", text)
                self.assertIn("3", text)  # 3 countries


class TestSeparatorSupport(unittest.TestCase):
    """Semicolon-separated CSV works with separator config"""

    def test_semicolon_csv(self):
        asyncio.run(self._test_semicolon_csv())

    async def _test_semicolon_csv(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "project_countries_semicolon", arguments={}
                )
                self.assertFalse(result.isError)
                text = result.content[0].text
                self.assertIn("Argentina", text)
                self.assertIn("Brazil", text)
                self.assertIn("Chile", text)
                self.assertIn("3", text)


if __name__ == "__main__":
    unittest.main()
