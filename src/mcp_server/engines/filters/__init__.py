"""
Shared filter layer for all engines.

Provides three functions that any engine can use to add optional
filtering to its generated MCP tool:

  - build_filter_params(tool_cfg)        -> inspect.Parameter list for __signature__
  - apply_filters(df, tool_cfg, kwargs)  -> (filtered_df, filter_label)
  - build_filter_doc(tool_cfg, base_doc) -> docstring with Args block appended

Each filter type is handled by its own module:
  - str_filter       (default) case-insensitive string match
  - int_filter       exact integer match
  - float_filter     exact float match
  - int_range_filter range match, generates <param>_from and <param>_to params

YAML filter config example:

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
"""

from mcp_server.engines.filters import str_filter, int_filter, float_filter, int_range_filter


_FILTER_TYPES = {
    "str": str_filter,
    "int": int_filter,
    "float": float_filter,
    "int_range": int_range_filter,
}


def _get_handler(ptype):
    handler = _FILTER_TYPES.get(ptype)
    if not handler:
        raise ValueError(f"Unknown filter type '{ptype}'. Available: {list(_FILTER_TYPES.keys())}")
    return handler


def build_filter_params(tool_cfg):
    """Return a list of inspect.Parameter objects for all declared filters."""
    params = []
    for f in tool_cfg.get("filters", []):
        handler = _get_handler(f.get("type", "str"))
        params.extend(handler.get_params(f["param"]))
    return params


def apply_filters(df, tool_cfg, kwargs):
    """Apply declared filters to a dataframe.

    Returns:
        (df, filter_label): filtered dataframe and a label string
        built from the active filters, ready to use in a response template.
    """
    label_parts = []
    for f in tool_cfg.get("filters", []):
        handler = _get_handler(f.get("type", "str"))
        df, label = handler.apply(df, f["column"], f["param"], kwargs, f.get("label", {}))
        if label:
            label_parts.append(label)
    return df, " ".join(label_parts)


def build_filter_doc(tool_cfg, base_doc):
    """Append an Args block to a docstring based on declared filters."""
    filters = tool_cfg.get("filters", [])
    if not filters:
        return base_doc

    lines = [base_doc.strip(), "", "Args:"]
    for f in filters:
        handler = _get_handler(f.get("type", "str"))
        lines.extend(handler.get_doc_lines(f["param"], f.get("description", "")))

    return "\n".join(lines)
