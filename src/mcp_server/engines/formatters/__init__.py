"""
Shared output formatting layer for all engines.

Provides functions to convert engine results into different output formats
(CSV, markdown table, JSON, chart specs, matplotlib images).

Each engine calls these functions when output_format != "text".
"""

import inspect
import io
import json


# Formats supported by each engine type.
# "text" is always the default and handled by the engine itself.
ENGINE_FORMATS = {
    "aggregate": [
        "text", "csv", "table", "json",
        "chart-bar", "chart-bar-horizontal", "chart-line", "chart-pie",
        "image-chart",
    ],
    "row_list": ["text", "csv", "table", "json"],
    "top_row": ["text", "csv", "table", "json"],
    "unique_values": ["text", "csv", "table", "json"],
}


def get_output_format_param(engine_name):
    """Return an inspect.Parameter for the output_format tool argument."""
    return inspect.Parameter(
        "output_format",
        inspect.Parameter.KEYWORD_ONLY,
        default="text",
        annotation=str,
    )


def get_format_doc_line(engine_name):
    """Return a docstring line describing output_format options for this engine."""
    supported = ENGINE_FORMATS.get(engine_name, ["text"])
    choices = ", ".join(supported)
    return f"    output_format: Output format. Options: {choices}. Default: text"


def validate_format(output_format, engine_name):
    """Validate that the requested format is supported. Returns error string or None."""
    supported = ENGINE_FORMATS.get(engine_name, ["text"])
    if output_format not in supported:
        return (
            f"Unsupported output format '{output_format}' for this tool. "
            f"Supported formats: {', '.join(supported)}"
        )
    return None


# ---------------------------------------------------------------------------
# DataFrame formatting (row_list, unique_values)
# ---------------------------------------------------------------------------

def format_dataframe_csv(df, columns_config=None):
    """Format a DataFrame as CSV. Uses column labels if provided."""
    if columns_config:
        col_map = {c["column"]: c.get("label", c["column"]) for c in columns_config}
        export_df = df[[c["column"] for c in columns_config]].rename(columns=col_map)
    else:
        export_df = df
    return export_df.to_csv(index=False)


def format_dataframe_table(df, columns_config=None):
    """Format a DataFrame as a markdown table."""
    if columns_config:
        col_map = {c["column"]: c.get("label", c["column"]) for c in columns_config}
        export_df = df[[c["column"] for c in columns_config]].rename(columns=col_map)
    else:
        export_df = df
    return export_df.to_markdown(index=False)


def format_dataframe_json(df, columns_config=None):
    """Format a DataFrame as JSON array of objects."""
    if columns_config:
        col_map = {c["column"]: c.get("label", c["column"]) for c in columns_config}
        export_df = df[[c["column"] for c in columns_config]].rename(columns=col_map)
    else:
        export_df = df
    return export_df.to_json(orient="records", indent=2)


# ---------------------------------------------------------------------------
# Grouped series formatting (aggregate engine with group_by)
# ---------------------------------------------------------------------------

def format_grouped_csv(grouped, group_col, value_label):
    """Format a grouped Series as CSV."""
    buf = io.StringIO()
    df = grouped.reset_index()
    df.columns = [group_col, value_label]
    df.to_csv(buf, index=False)
    return buf.getvalue()


def format_grouped_table(grouped, group_col, value_label):
    """Format a grouped Series as a markdown table."""
    df = grouped.reset_index()
    df.columns = [group_col, value_label]
    return df.to_markdown(index=False)


def format_grouped_json(grouped, group_col, value_label):
    """Format a grouped Series as JSON."""
    records = [
        {group_col: str(k), value_label: round(v, 2)}
        for k, v in grouped.items()
    ]
    return json.dumps(records, indent=2)


def format_chart_json(grouped, output_format, viz_cfg):
    """Format a grouped Series as a chart JSON spec."""
    chart_type = output_format.replace("chart-", "")
    chart = {
        "type": chart_type,
        "labels": [str(li) for li in grouped.index.tolist()],
        "datasets": [{
            "label": viz_cfg.get("label", "Value"),
            "data": [round(v, 2) for v in grouped.values.tolist()],
        }],
    }
    return json.dumps(chart, indent=2)


def format_image_chart(grouped, viz_cfg, output_format="chart-bar"):
    """Render a grouped Series as a matplotlib PNG, returned as base64.

    Returns a tuple (base64_str, mime_type) for MCP image content.
    """
    import base64
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    chart_type = viz_cfg.get("type", "bar")
    label = viz_cfg.get("label", "Value")
    labels = [str(li) for li in grouped.index.tolist()]
    values = grouped.values.tolist()

    fig, ax = plt.subplots(figsize=(10, 6))

    if chart_type in ("bar", "bar-horizontal"):
        if chart_type == "bar-horizontal":
            ax.barh(labels, values)
            ax.set_xlabel(label)
        else:
            ax.bar(labels, values)
            ax.set_ylabel(label)
            plt.xticks(rotation=45, ha="right")
    elif chart_type == "line":
        ax.plot(labels, values, marker="o")
        ax.set_ylabel(label)
        plt.xticks(rotation=45, ha="right")
    elif chart_type == "pie":
        ax.pie(values, labels=labels, autopct="%1.1f%%")
    else:
        ax.bar(labels, values)
        ax.set_ylabel(label)
        plt.xticks(rotation=45, ha="right")

    ax.set_title(label)
    plt.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    buf.seek(0)

    return base64.b64encode(buf.read()).decode("ascii"), "image/png"


# ---------------------------------------------------------------------------
# Single value formatting (aggregate without group_by, top_row)
# ---------------------------------------------------------------------------

def format_single_value_json(value, formatted, filter_label="", source="", extra=None):
    """Format a single result value as JSON."""
    result = {
        "value": round(value, 2) if isinstance(value, float) else value,
        "formatted": formatted,
    }
    if filter_label:
        result["filter"] = filter_label
    if source:
        result["source"] = source
    if extra:
        result.update(extra)
    return json.dumps(result, indent=2)


# ---------------------------------------------------------------------------
# List formatting (unique_values)
# ---------------------------------------------------------------------------

def format_values_csv(values, column_name):
    """Format a list of values as single-column CSV."""
    lines = [column_name]
    lines.extend(str(v) for v in values)
    return "\n".join(lines)


def format_values_table(values, column_name):
    """Format a list of values as a markdown table."""
    import pandas as pd
    df = pd.DataFrame({column_name: [str(v) for v in values]})
    return df.to_markdown(index=False)


def format_values_json(values, column_name):
    """Format a list of values as JSON."""
    return json.dumps({"column": column_name, "values": [str(v) for v in values]}, indent=2)


# ---------------------------------------------------------------------------
# Embedded markers for webchat (extracted by backend, rendered by frontend)
# ---------------------------------------------------------------------------

def embed_table_marker(headers, rows):
    """Build a <!--table:{...}--> marker for the webchat to render.

    Args:
        headers: list of column header strings
        rows: list of lists (each inner list is one row of cell values)
    """
    table_data = {"headers": headers, "rows": rows}
    return "\n<!--table:" + json.dumps(table_data, ensure_ascii=False) + "-->"


def build_table_from_dataframe(df, columns_config):
    """Build a table marker from a DataFrame with column config (row_list style)."""
    headers = []
    for field in columns_config:
        headers.append(field.get("label", field["column"]))

    rows = []
    for _, row in df.iterrows():
        cells = []
        for field in columns_config:
            field_fmt = field.get("format", "{result}")
            cells.append(field_fmt.format(result=row[field["column"]]))
        rows.append(cells)

    return embed_table_marker(headers, rows)


def build_table_from_grouped(grouped, group_col, value_label, fmt=None):
    """Build a table marker from a grouped Series (aggregate style)."""
    headers = [group_col, value_label]
    rows = []
    for label, value in grouped.items():
        formatted_val = fmt.format(result=value) if fmt else str(round(value, 2))
        rows.append([str(label), formatted_val])
    return embed_table_marker(headers, rows)
