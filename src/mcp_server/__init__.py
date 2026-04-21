from pydantic import BaseModel, Field


class ToolOutput(BaseModel):
    """Structured output for all MCP tools in this server.

    Every tool registered through the ToolRegistry must return an instance of this
    class. The registry enforces this at startup by inspecting the function's return
    type annotation — tools without ``-> ToolOutput`` will be rejected with a
    ``TypeError`` before the server starts.

    The serialized dict (via ``model_dump()``) is returned to the MCP client,
    giving consumers direct access to all fields regardless of which ones a
    particular tool populates.
    """
    source: str = Field(
        description="Complete URL pointing to the original source of the data."
    )
    content: str = Field(
        default="",
        description="Direct response for the LLM to consume. Supports plain text, Markdown, or other text-based formats."
    )
    structured_content: dict = Field(
        default={},
        description="JSON-serializable dictionary with arbitrary keys. Provides structured data for the LLM when plain text is insufficient."
    )
    table: list = Field(
        default=[],
        description="Two-dimensional list (list of rows) representing tabular data, e.g., from CSV or TSV sources. Each row should be a list of cell values."
    )
    chart: dict = Field(
        default={},
        description="Dictionary containing data and configuration for rendering a Chart.js chart in the chat interface. Structure must follow Chart.js expected format."
    )
    force: str = Field(
        default="",
        description="Plain text message that bypasses LLM processing. Printed exactly as provided in the user interface – used for debugging or developer-to-user notifications."
    )
