"""Exact integer match filter."""

import inspect
from typing import Optional


def get_params(param):
    return [inspect.Parameter(
        param,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        default=None,
        annotation=Optional[int],
    )]


def apply(df, col, param, kwargs, label_cfg):
    value = kwargs.get(param)
    if value is None:
        return df, ""

    df = df[df[col] == int(value)]

    if isinstance(label_cfg, str):
        return df, label_cfg.format(value=value)
    tmpl = label_cfg.get("filtered", "") if isinstance(label_cfg, dict) else ""
    return df, tmpl.format(value=value) if tmpl else ""


def get_doc_lines(param, desc):
    return [f"    {param} (int, optional): {desc}"]
