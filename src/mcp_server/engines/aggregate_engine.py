"""
Aggregate engine

Generates an MCP tool that computes a single aggregate value (sum, avg,
count) from one column in a CSV file. Supports optional filters to
narrow the rows before aggregating.

YAML config example:

    engine: aggregate
    dataset:
      name: total-prestamos-bcie
      source:
        csv: https://example.org/data.csv
        url: https://example.org/dataset
        # optional separator. Pandas will try to guess if not provided.
        separator: ","
    tool:
      name: total_prestamos_bcie
      description: "Get total approved loans from BCIE in USD"
      column: MONTO_BRUTO_USD
      aggregation: sum
      format: "${result:,.2f}"
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
      response: |
        El monto total de préstamos aprobados por el BCIE {filter_label} es {result}.
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
    format_grouped_csv,
    format_grouped_table,
    format_chart_json,
    format_image_chart,
    format_single_value_json,
    build_table_from_grouped,
)


AGGREGATIONS = {
    "sum": lambda s: s.sum(),
    "avg": lambda s: s.mean(),
    "count": lambda s: len(s),
}

ENGINE_NAME = "aggregate"


def load_aggregate_dataset(mcp, config, yaml_path):
    source = config["dataset"]["source"]
    csv_url = source["csv"]
    source_url = source.get("url", "")
    separator = source.get("separator")

    tool_cfg = config["tool"]
    tool_name = tool_cfg["name"]
    tool_desc = tool_cfg["description"]
    column = tool_cfg["column"]
    aggregation = tool_cfg.get("aggregation", "sum")
    fmt = tool_cfg.get("format", "{result}")
    response_template = tool_cfg.get("response")
    viz_cfg = tool_cfg.get("visualization")

    agg_fn = AGGREGATIONS.get(aggregation)
    if not agg_fn:
        raise ValueError(f"Unknown aggregation '{aggregation}'. Available: {list(AGGREGATIONS.keys())}")

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

        value = agg_fn(df[column].dropna())
        result = fmt.format(result=value)

        # Compute grouped data if visualization is configured
        grouped = None
        stacked = None
        if viz_cfg:
            group_col = viz_cfg["group_by"]
            stack_col = viz_cfg.get("stack_by")
            if group_col in df.columns:
                grouped = df.groupby(group_col)[column].agg(aggregation).sort_values(ascending=False)
                # Stacked: pivot by stack_by column to get multi-dataset chart data
                if stack_col and stack_col in df.columns:
                    stacked = pd.pivot_table(
                        df, index=group_col, columns=stack_col,
                        values=column, aggfunc=aggregation, fill_value=0,
                    ).sort_index()

        # Handle non-text formats
        if output_format != "text":
            if output_format == "json":
                extra = {}
                if grouped is not None:
                    extra["groups"] = [
                        {"label": str(k), "value": round(v, 2)}
                        for k, v in grouped.items()
                    ]
                return format_single_value_json(
                    value, result, filter_label, source_url, extra
                )

            # Formats that require grouped data
            if grouped is None:
                return (
                    f"Format '{output_format}' requires visualization config with group_by. "
                    f"This tool only supports 'text' and 'json' without visualization config."
                )

            group_col = viz_cfg["group_by"]
            value_label = viz_cfg.get("label", column)

            if output_format == "csv":
                return format_grouped_csv(grouped, group_col, value_label)
            if output_format == "table":
                return format_grouped_table(grouped, group_col, value_label)
            if output_format.startswith("chart-"):
                return format_chart_json(grouped, output_format, viz_cfg)
            if output_format == "image-chart":
                b64, mime = format_image_chart(grouped, viz_cfg)
                return f"data:{mime};base64,{b64}"

        # Default text format
        context = {
            "result": result,
            "filter_label": filter_label,
            "source": source_url,
        }

        if response_template:
            text = response_template.format(**context)
        else:
            text = f"Result {filter_label}: {result}"

        if grouped is not None:
            group_col = viz_cfg["group_by"]
            value_label = viz_cfg.get("label", column)
            text += build_table_from_grouped(grouped, group_col, value_label, fmt)

            if stacked is not None:
                # Multi-dataset stacked chart
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
                    "label": viz_cfg.get("label", column),
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
