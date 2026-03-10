"""Integration tests for the declarative dataset engine system (YAML engines)

Uses self-contained fixtures in tests/fixtures/ so no remote tools are needed.
"""

import asyncio
import json
import os
import re
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

    def test_all_rows_has_table(self):
        """row_list text response embeds table marker"""
        asyncio.run(self._test_all_rows_has_table())

    async def _test_all_rows_has_table(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("list_projects", arguments={})
                text = result.content[0].text
                match = re.search(r"<!--table:(.*?)-->", text)
                self.assertIsNotNone(match, "Response should contain table data")
                table = json.loads(match.group(1))
                self.assertEqual(table["headers"], ["Country", "Year", "Sector", "Amount"])
                self.assertEqual(len(table["rows"]), 10)

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

    def test_all_rows_has_chart(self):
        """row_list text response embeds chart marker when visualization is configured"""
        asyncio.run(self._test_all_rows_has_chart())

    async def _test_all_rows_has_chart(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("list_projects", arguments={})
                text = result.content[0].text
                match = re.search(r"<!--chart:(.*?)-->", text)
                self.assertIsNotNone(match, "Response should contain chart data")
                chart = json.loads(match.group(1))
                self.assertEqual(chart["type"], "bar")
                self.assertIn("labels", chart)
                self.assertIn("data", chart)
                # Years should be sorted as labels
                self.assertEqual(chart["labels"], sorted(chart["labels"]))

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

    def test_total_all_has_chart(self):
        """When visualization is configured, response includes chart data"""
        asyncio.run(self._test_total_all_has_chart())

    async def _test_total_all_has_chart(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("total_projects", arguments={})
                text = result.content[0].text
                match = re.search(r"<!--chart:(.*?)-->", text)
                self.assertIsNotNone(match, "Response should contain chart data")
                chart = json.loads(match.group(1))
                self.assertEqual(chart["type"], "bar")
                self.assertIn("Argentina", chart["labels"])
                self.assertIn("Brazil", chart["labels"])
                self.assertIn("Chile", chart["labels"])
                self.assertEqual(len(chart["data"]), 3)

    def test_total_all_has_table(self):
        """When visualization is configured, response includes table data"""
        asyncio.run(self._test_total_all_has_table())

    async def _test_total_all_has_table(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool("total_projects", arguments={})
                text = result.content[0].text
                match = re.search(r"<!--table:(.*?)-->", text)
                self.assertIsNotNone(match, "Response should contain table data")
                table = json.loads(match.group(1))
                self.assertIn("headers", table)
                self.assertIn("rows", table)
                self.assertEqual(len(table["headers"]), 2)
                self.assertEqual(len(table["rows"]), 3)  # 3 countries

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


class TestOutputFormatAggregate(unittest.TestCase):
    """output_format parameter works for aggregate engine"""

    def test_default_text(self):
        """Default output_format=text returns same as before"""
        asyncio.run(self._test())

    async def _test(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "total_projects", arguments={"output_format": "text"}
                )
                self.assertFalse(result.isError)
                text = result.content[0].text
                self.assertIn("$28,057.00", text)
                self.assertIn("<!--chart:", text)

    def test_csv_format(self):
        asyncio.run(self._test_csv())

    async def _test_csv(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "total_projects", arguments={"output_format": "csv"}
                )
                self.assertFalse(result.isError)
                text = result.content[0].text
                self.assertIn("COUNTRY", text)
                self.assertIn("Argentina", text)
                self.assertIn("Brazil", text)
                self.assertIn("Chile", text)

    def test_table_format(self):
        asyncio.run(self._test_table())

    async def _test_table(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "total_projects", arguments={"output_format": "table"}
                )
                self.assertFalse(result.isError)
                text = result.content[0].text
                # Markdown table has pipes
                self.assertIn("|", text)
                self.assertIn("Argentina", text)

    def test_json_format(self):
        asyncio.run(self._test_json())

    async def _test_json(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "total_projects", arguments={"output_format": "json"}
                )
                self.assertFalse(result.isError)
                data = json.loads(result.content[0].text)
                self.assertIn("value", data)
                self.assertIn("formatted", data)
                self.assertIn("groups", data)
                self.assertEqual(len(data["groups"]), 3)

    def test_chart_bar_format(self):
        asyncio.run(self._test_chart_bar())

    async def _test_chart_bar(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "total_projects", arguments={"output_format": "chart-bar"}
                )
                self.assertFalse(result.isError)
                chart = json.loads(result.content[0].text)
                self.assertEqual(chart["type"], "bar")
                self.assertIn("labels", chart)
                self.assertIn("datasets", chart)
                self.assertEqual(len(chart["datasets"]), 1)
                self.assertEqual(len(chart["datasets"][0]["data"]), 3)

    def test_chart_pie_format(self):
        asyncio.run(self._test_chart_pie())

    async def _test_chart_pie(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "total_projects", arguments={"output_format": "chart-pie"}
                )
                self.assertFalse(result.isError)
                chart = json.loads(result.content[0].text)
                self.assertEqual(chart["type"], "pie")

    def test_image_chart_format(self):
        asyncio.run(self._test_image_chart())

    async def _test_image_chart(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "total_projects", arguments={"output_format": "image-chart"}
                )
                self.assertFalse(result.isError)
                text = result.content[0].text
                self.assertTrue(text.startswith("data:image/png;base64,"))

    def test_invalid_format(self):
        asyncio.run(self._test_invalid())

    async def _test_invalid(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "total_projects", arguments={"output_format": "xml"}
                )
                self.assertFalse(result.isError)
                text = result.content[0].text
                self.assertIn("Unsupported", text)

    def test_csv_with_filter(self):
        asyncio.run(self._test_csv_filtered())

    async def _test_csv_filtered(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "total_projects",
                    arguments={"output_format": "csv", "country": "Brazil"},
                )
                self.assertFalse(result.isError)
                text = result.content[0].text
                self.assertIn("Brazil", text)
                self.assertNotIn("Argentina", text)


class TestOutputFormatRowList(unittest.TestCase):
    """output_format parameter works for row_list engine"""

    def test_csv_format(self):
        asyncio.run(self._test_csv())

    async def _test_csv(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "list_projects", arguments={"output_format": "csv"}
                )
                self.assertFalse(result.isError)
                text = result.content[0].text
                lines = text.strip().split("\n")
                self.assertEqual(len(lines), 11)  # header + 10 rows
                self.assertIn("Country", lines[0])

    def test_table_format(self):
        asyncio.run(self._test_table())

    async def _test_table(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "list_projects", arguments={"output_format": "table"}
                )
                self.assertFalse(result.isError)
                text = result.content[0].text
                self.assertIn("|", text)
                self.assertIn("Country", text)

    def test_json_format(self):
        asyncio.run(self._test_json())

    async def _test_json(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "list_projects", arguments={"output_format": "json"}
                )
                self.assertFalse(result.isError)
                data = json.loads(result.content[0].text)
                self.assertEqual(len(data), 10)
                self.assertIn("Country", data[0])

    def test_csv_with_filter(self):
        asyncio.run(self._test_csv_filtered())

    async def _test_csv_filtered(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "list_projects",
                    arguments={"output_format": "csv", "country": "Argentina"},
                )
                self.assertFalse(result.isError)
                text = result.content[0].text
                lines = text.strip().split("\n")
                self.assertEqual(len(lines), 4)  # header + 3 Argentina rows

    def test_unsupported_chart_format(self):
        asyncio.run(self._test_unsupported())

    async def _test_unsupported(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "list_projects", arguments={"output_format": "chart-bar"}
                )
                self.assertFalse(result.isError)
                text = result.content[0].text
                self.assertIn("Unsupported", text)


class TestOutputFormatTopRow(unittest.TestCase):
    """output_format parameter works for top_row engine"""

    def test_csv_format(self):
        asyncio.run(self._test_csv())

    async def _test_csv(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "top_project", arguments={"output_format": "csv"}
                )
                self.assertFalse(result.isError)
                text = result.content[0].text
                lines = text.strip().split("\n")
                self.assertEqual(len(lines), 2)  # header + 1 row
                self.assertIn("Country", lines[0])
                self.assertIn("Chile", text)

    def test_table_format(self):
        asyncio.run(self._test_table())

    async def _test_table(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "top_project", arguments={"output_format": "table"}
                )
                self.assertFalse(result.isError)
                text = result.content[0].text
                self.assertIn("|", text)
                self.assertIn("Chile", text)

    def test_json_format(self):
        asyncio.run(self._test_json())

    async def _test_json(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "top_project", arguments={"output_format": "json"}
                )
                self.assertFalse(result.isError)
                data = json.loads(result.content[0].text)
                self.assertIn("value", data)
                self.assertIn("row", data)
                self.assertEqual(data["row"]["Country"], "Chile")


class TestOutputFormatUniqueValues(unittest.TestCase):
    """output_format parameter works for unique_values engine"""

    def test_csv_format(self):
        asyncio.run(self._test_csv())

    async def _test_csv(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "project_countries", arguments={"output_format": "csv"}
                )
                self.assertFalse(result.isError)
                text = result.content[0].text
                self.assertIn("COUNTRY", text)
                lines = text.strip().split("\n")
                self.assertEqual(len(lines), 4)  # header + 3 countries

    def test_table_format(self):
        asyncio.run(self._test_table())

    async def _test_table(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "project_countries", arguments={"output_format": "table"}
                )
                self.assertFalse(result.isError)
                text = result.content[0].text
                self.assertIn("|", text)
                self.assertIn("COUNTRY", text)
                self.assertIn("Argentina", text)

    def test_json_format(self):
        asyncio.run(self._test_json())

    async def _test_json(self):
        async with stdio_client(SERVER_PARAMS) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(
                    "project_countries", arguments={"output_format": "json"}
                )
                self.assertFalse(result.isError)
                data = json.loads(result.content[0].text)
                self.assertIn("values", data)
                self.assertEqual(len(data["values"]), 3)


if __name__ == "__main__":
    unittest.main()
