"""Case-insensitive string exact match filter."""

import inspect
from typing import Optional


def get_params(param):
    return [inspect.Parameter(
        param,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        default=None,
        annotation=Optional[str],
    )]


def apply(df, col, param, kwargs, label_cfg):
    value = kwargs.get(param)
    if value is None:
        return df, ""

    match = df[col].str.lower() == value.lower()
    if not match.any():
        valid = sorted(df[col].dropna().unique())
        if len(valid) > 10:
            valores_validos = ", ".join(str(v) for v in valid[:10]) + ", ..."
        else:
            valores_validos = ", ".join(str(v) for v in valid)

        raise ValueError(f"'{value}' no encontrado en {param}. Valores válidos: {valores_validos}")

    df = df[match]

    if isinstance(label_cfg, str):
        return df, label_cfg.format(value=value)
    tmpl = label_cfg.get("filtered", "") if isinstance(label_cfg, dict) else ""
    return df, tmpl.format(value=value) if tmpl else ""


def get_doc_lines(param, desc):
    return [f"    {param} (str, optional): {desc}"]
