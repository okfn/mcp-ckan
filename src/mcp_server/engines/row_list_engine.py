"""
Row List engine

Generates an MCP tool that returns a list of rows from a CSV, formatted
per-row using a configurable columns list. Supports optional filters.

YAML config example:

    engine: row_list
    dataset:
      name: prestamos-bcie
      source:
        csv: https://example.org/data.csv
        url: https://example.org/dataset
        # optional separator. Pandas will try to guess if not provided.
        separator: ","
    tool:
      name: lista_prestamos_bcie
      description: "Get list of loans approved by BCIE"
      columns:
        - column: ANIO_APROBACION
          label: Año
        - column: PAIS
          label: País
        - column: MONTO_BRUTO_USD
          label: Monto
          format: "${result:,.2f}"
        - column: SECTOR
          label: Sector
      filters:
        - column: PAIS
          param: country
          description: "Country name, e.g. Honduras, Costa Rica"
          label: "para {value}"
        - column: ANIO_APROBACION
          param: year
          type: int_range
          description: "Year of approval"
          label:
            both: "entre {year_from} y {year_to}"
            from_only: "desde {year_from}"
            to_only: "hasta {year_to}"
            same: "en {year_from}"
      limit: 50        # optional, default 50. Use 0 for no limit.
      sort:
        column: ANIO_APROBACION
        order: asc     # asc (default) or desc
      response: |
        El BCIE ha aprobado {count} préstamos {filter_label}:
        {list}
        Fuente: {source}
"""

import inspect
import json
import pandas as pd
from mcp_server.engines.filters import build_filter_params, apply_filters, build_filter_doc
from mcp_server.engines.formatters import (
    get_output_format_param,
    get_format_doc_line,
    validate_format,
    format_dataframe_csv,
    format_dataframe_table,
    format_dataframe_json,
    build_table_from_dataframe,
)

ENGINE_NAME = "row_list"


def load_row_list_dataset(mcp, config, yaml_path):
    source = config["dataset"]["source"]
    csv_url = source["csv"]
    source_url = source.get("url", "")
    separator = source.get("separator")

    tool_cfg = config["tool"]
    tool_name = tool_cfg["name"]
    tool_desc = tool_cfg["description"]
    columns = tool_cfg.get("columns", [])
    limit = tool_cfg.get("limit", 50)
    sort_cfg = tool_cfg.get("sort")
    response_template = tool_cfg.get("response")
    viz_cfg = tool_cfg.get("visualization")

    filter_params = build_filter_params(tool_cfg)
    filter_params.append(get_output_format_param(ENGINE_NAME))

    def tool_fn(**kwargs):
        output_format = kwargs.pop("output_format", "text")

        error = validate_format(output_format, ENGINE_NAME)
        if error:
            return error

        read_kwargs = {"sep": separator} if separator else {}
        df = pd.read_csv(csv_url, **read_kwargs)
        try:
            df, filter_label = apply_filters(df, tool_cfg, kwargs)
        except ValueError as e:
            return f"Error en los parámetros: {e}"

        if df.empty:
            label = f" {filter_label}" if filter_label else ""
            return f"No se encontraron resultados{label}."

        total = len(df)
        if sort_cfg:
            df = df.sort_values(
                by=sort_cfg["column"],
                ascending=sort_cfg.get("order", "asc") == "asc",
            )
        display_df = df if not limit else df.head(limit)

        # Handle non-text formats (no limit - return all data)
        if output_format != "text":
            if output_format == "csv":
                return format_dataframe_csv(df, columns)
            if output_format == "table":
                return format_dataframe_table(df, columns)
            if output_format == "json":
                return format_dataframe_json(df, columns)

        # Default text format
        rows_lines = []
        for _, row in display_df.iterrows():
            parts = []
            for field in columns:
                label = field.get("label", field["column"])
                field_fmt = field.get("format", "{result}")
                value = field_fmt.format(result=row[field["column"]])
                parts.append(f"{label}: {value}")
            rows_lines.append("  - " + " | ".join(parts))

        if limit and total > limit:
            rows_lines.append(f"  ... y {total - limit} más.")

        list_str = "\n".join(rows_lines)

        context = {
            "count": total,
            "list": list_str,
            "filter_label": filter_label,
            "source": source_url,
        }

        if response_template:
            text = response_template.format(**context)
        else:
            text = f"{total} resultados {filter_label}:\n{list_str}"

        # Embed table marker for webchat rendering (uses all data, not limited)
        if columns:
            text += build_table_from_dataframe(df, columns)

        # Embed chart marker if visualization is configured
        if viz_cfg:
            group_col = viz_cfg["group_by"]
            value_col = viz_cfg["column"]
            agg = viz_cfg.get("aggregation", "sum")
            stack_col = viz_cfg.get("stack_by")
            if group_col in df.columns and value_col in df.columns:
                grouped = df.groupby(group_col)[value_col].agg(agg)
                if viz_cfg.get("sort", "label") == "label":
                    grouped = grouped.sort_index()
                else:
                    grouped = grouped.sort_values(ascending=False)

                if stack_col and stack_col in df.columns:
                    # Multi-dataset stacked chart
                    stacked = pd.pivot_table(
                        df, index=group_col, columns=stack_col,
                        values=value_col, aggfunc=agg, fill_value=0,
                    ).sort_index()
                    labels = [str(li) for li in stacked.index.tolist()]
                    datasets = []
                    for col_name in stacked.columns:
                        datasets.append({
                            "label": str(col_name),
                            "data": [round(v, 2) for v in stacked[col_name].tolist()],
                        })
                    chart = {
                        "type": viz_cfg.get("type", "bar"),
                        "stacked": True,
                        "labels": labels,
                        "datasets": datasets,
                    }
                else:
                    chart = {
                        "type": viz_cfg.get("type", "bar"),
                        "labels": [str(li) for li in grouped.index.tolist()],
                        "data": [round(v, 2) for v in grouped.values.tolist()],
                        "label": viz_cfg.get("label", value_col),
                    }
                text += "\n<!--chart:" + json.dumps(chart) + "-->"

        return text

    tool_fn.__signature__ = inspect.Signature(filter_params)
    tool_fn.__name__ = tool_name

    doc = build_filter_doc(tool_cfg, tool_desc)
    doc += "\n" + get_format_doc_line(ENGINE_NAME)
    tool_fn.__doc__ = doc
    mcp.tool()(tool_fn)

    return 1
