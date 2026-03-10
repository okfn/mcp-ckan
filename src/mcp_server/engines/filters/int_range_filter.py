"""Integer range filter. Generates <param>_from and <param>_to parameters."""

import inspect
from typing import Optional


def get_params(param):
    return [
        inspect.Parameter(
            f"{param}_from",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=None,
            annotation=Optional[int],
        ),
        inspect.Parameter(
            f"{param}_to",
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=None,
            annotation=Optional[int],
        ),
    ]


def apply(df, col, param, kwargs, label_cfg):
    from_val = int(kwargs[f"{param}_from"]) if kwargs.get(f"{param}_from") is not None else None
    to_val = int(kwargs[f"{param}_to"]) if kwargs.get(f"{param}_to") is not None else None

    if from_val is not None and to_val is not None and from_val > to_val:
        raise ValueError(f"{param}_from ({from_val}) no puede ser mayor que {param}_to ({to_val}).")

    if from_val is not None:
        df = df[df[col] >= from_val]
    if to_val is not None:
        df = df[df[col] <= to_val]

    ctx = {f"{param}_from": from_val, f"{param}_to": to_val}
    if from_val is not None and to_val is not None and from_val == to_val:
        tmpl = label_cfg.get("same", f"en {from_val}")
    elif from_val is not None and to_val is not None:
        tmpl = label_cfg.get("both", f"from {from_val} to {to_val}")
    elif from_val is not None:
        tmpl = label_cfg.get("from_only", f"from {from_val}")
    elif to_val is not None:
        tmpl = label_cfg.get("to_only", f"until {to_val}")
    else:
        return df, ""

    return df, tmpl.format(**ctx)


def get_doc_lines(param, desc):
    return [
        f"    {param}_from (int, optional): {desc} (start of range)",
        f"    {param}_to (int, optional): {desc} (end of range)",
    ]
