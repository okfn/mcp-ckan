"""Core tool: expose the MCP resource catalog to the LLM.

MCP resources (documents, PDFs, reference datasets, external visualizers)
are not autodiscovered by the model - only tools travel through
``tools/list``, while resources live behind ``resources/list``, which the
chat gateway queries just for its UI panel. Without this tool a question
like "is there a BEN data visualizer?" ends in "I don't know" even though
the resource is registered.

``list_available_resources`` closes that gap: it returns the catalog -
name, description, type and links - as a regular tool result the model can
quote. It is server-level on purpose so every instance (Uruguay, Brasil,
...) gets it for free, whatever plugins it loads.
"""
import logging

from mcp.server.fastmcp import FastMCP

from mcp_server import DataToolOutput
from mcp_server.results import text_result

log = logging.getLogger(__name__)


def _annotation_links(annotations: dict) -> list[tuple[str, str]]:
    """Extract ``(label, url)`` pairs from a resource's annotations.

    Resource annotations are free-form; by convention link-bearing keys
    (``source_url``, ``showcase_url``, ``github_release_url``, ...) hold a
    plain http(s) URL, so anything URL-shaped is treated as a link.
    """
    return [
        (key, value)
        for key, value in annotations.items()
        if isinstance(value, str) and value.startswith(("http://", "https://"))
    ]


def register_core_tools(plugin, mcp: FastMCP) -> None:
    """Register the server's own tools on the ``core`` namespace.

    Args:
        plugin: Namespaced registry (``registry.for_plugin("core")``).
        mcp: The shared FastMCP server, queried for the resource catalog.
    """

    @plugin.tool()
    async def list_available_resources() -> DataToolOutput:
        """List every complementary resource this server offers: documents,
            publications (PDF), reference datasets and external visualizers,
            each with its description and links.

            Use this tool whenever the user asks which resources, documents,
            publications, books or visualizers exist or are available, or
            whether a specific one exists (e.g. "is there a data visualizer
            for X?", "where can I download the annual report?").
            Answer in the user's language and always include the links.

        Examples:
            - list_available_resources()
        """
        resources = await mcp.list_resources()
        if not resources:
            return text_result("This server has no complementary resources registered.")

        lines = [f"{len(resources)} complementary resource(s) available on this server:", ""]
        sources = []
        for res in resources:
            meta = res.meta or {}
            links = _annotation_links(meta.get("annotations") or {})

            details = [d for d in (res.mimeType, meta.get("plugin")) if d]
            header = f"- {res.name or res.uri}"
            if details:
                header += f" ({', '.join(details)})"
            lines.append(header)
            if res.description:
                lines.append(f"  {res.description}")
            lines.append(f"  URI: {res.uri}")
            for label, url in links:
                lines.append(f"  {label}: {url}")
                sources.append(url)
            lines.append("")

        return text_result("\n".join(lines).rstrip(), source_url=sources)
