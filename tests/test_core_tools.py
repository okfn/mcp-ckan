"""
Tests for the server-level core tools (src/mcp_server/tools/).

Today that is ``core_list_available_resources`` (from the core function
``list_available_resources``): the LLM does not
autodiscover MCP resources (only tools travel through tools/list), so this
tool is what lets the model answer "what resources/visualizers exist?"
with links.
"""
from collections.abc import AsyncGenerator

import pytest
from mcp.client.session import ClientSession
from mcp.server.fastmcp import FastMCP
from mcp.shared.memory import create_connected_server_and_client_session

from mcp_server.registry import PluginsRegistry
from mcp_server.tools.resources_catalog import register_core_tools


def build_server_with_resources() -> FastMCP:
    """A server with one plugin resource, mirroring how a real plugin
    declares an external reference link (text/uri-list)."""
    mcp = FastMCP("test")
    registry = PluginsRegistry(mcp)
    plugin = registry.for_plugin("mcp_server_demo")

    @plugin.resource(
        "some_ref/some_name",
        name="MCP Resource Name",
        description="Some link to a reference website.",
        mime_type="text/uri-list",
        annotations={
            "publisher": "Some publisher",
            "showcase_url": "https://example.org/showcase/ref-name",
        },
    )
    def reference_link() -> str:
        return "https://example.org/showcase/ref-name\n"

    register_core_tools(registry.for_plugin("core"), mcp)
    return mcp


@pytest.fixture
async def client_session() -> AsyncGenerator[ClientSession]:
    async with create_connected_server_and_client_session(
        build_server_with_resources(), raise_exceptions=True
    ) as session:
        yield session


@pytest.mark.anyio
async def test_catalog_tool_is_registered_under_core_namespace(client_session: ClientSession):
    tools = await client_session.list_tools()
    assert "core_list_available_resources" in [t.name for t in tools.tools]


@pytest.mark.anyio
async def test_catalog_lists_resources_with_links(client_session: ClientSession):
    result = await client_session.call_tool("core_list_available_resources", {})

    assert not result.isError
    text = result.content[0].text
    # Name, description, plugin, URI and annotation links all surface so the
    # LLM can answer "is there a visualizer?" and quote the link.
    assert "MCP Resource Name" in text
    assert "Some link to a reference website" in text
    assert "mcp_server_demo" in text
    assert "mcp://mcp_server_demo/some_ref/some_name" in text
    assert "showcase_url: https://example.org/showcase/ref-name" in text
    # Links also land in structuredContent.sources for the gateway UI.
    assert result.structuredContent["sources"] == [
        "https://example.org/showcase/ref-name"
    ]


@pytest.mark.anyio
async def test_catalog_with_no_resources():
    mcp = FastMCP("test")
    registry = PluginsRegistry(mcp)
    register_core_tools(registry.for_plugin("core"), mcp)

    async with create_connected_server_and_client_session(mcp, raise_exceptions=True) as session:
        result = await session.call_tool("core_list_available_resources", {})

    assert not result.isError
    assert "no complementary resources" in result.content[0].text
