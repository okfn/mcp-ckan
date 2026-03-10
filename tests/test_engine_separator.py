"""Tests for CSV separator support in all engines"""

from unittest.mock import patch, MagicMock

import pandas as pd

from mcp_server.engines.row_list_engine import load_row_list_dataset
from mcp_server.engines.aggregate_engine import load_aggregate_dataset
from mcp_server.engines.top_row_engine import load_top_row_dataset
from mcp_server.engines.unique_values_engine import load_unique_values_dataset


def _make_df():
    return pd.DataFrame({
        "COL_A": ["foo", "bar", "baz"],
        "COL_B": [10.0, 20.0, 30.0],
        "COL_C": ["x", "y", "z"],
    })


def make_config(engine, separator=None):
    """Build a minimal YAML config dict for testing."""
    source = {
        "csv": "http://example.org/data.csv",
        "url": "http://example.org",
    }
    if separator is not None:
        source["separator"] = separator

    base = {
        "engine": engine,
        "dataset": {"name": "test", "source": source},
    }

    if engine == "row_list":
        base["tool"] = {
            "name": "test_row_list",
            "description": "test",
            "columns": [
                {"column": "COL_A", "label": "A"},
                {"column": "COL_B", "label": "B"},
            ],
        }
    elif engine == "aggregate":
        base["tool"] = {
            "name": "test_aggregate",
            "description": "test",
            "column": "COL_B",
            "aggregation": "sum",
        }
    elif engine == "top_row":
        base["tool"] = {
            "name": "test_top_row",
            "description": "test",
            "column": "COL_B",
            "order": "max",
            "show": [{"column": "COL_A", "label": "A"}],
        }
    elif engine == "unique_values":
        base["tool"] = {
            "name": "test_unique_values",
            "description": "test",
            "column": "COL_A",
        }

    return base


def capture_tool_fn(mcp_mock):
    """Extract the tool function registered via mcp.tool()()."""
    return mcp_mock.tool.return_value.call_args[0][0]


# -- row_list --

@patch("mcp_server.engines.row_list_engine.pd.read_csv", return_value=_make_df())
def test_row_list_with_separator(mock_read):
    mcp = MagicMock()
    load_row_list_dataset(mcp, make_config("row_list", ";"), "test.yaml")
    fn = capture_tool_fn(mcp)
    fn()
    mock_read.assert_called_once_with("http://example.org/data.csv", sep=";")


@patch("mcp_server.engines.row_list_engine.pd.read_csv", return_value=_make_df())
def test_row_list_with_separator_comma(mock_read):
    mcp = MagicMock()
    load_row_list_dataset(mcp, make_config("row_list", ","), "test.yaml")
    fn = capture_tool_fn(mcp)
    fn()
    mock_read.assert_called_once_with("http://example.org/data.csv", sep=",")


@patch("mcp_server.engines.row_list_engine.pd.read_csv", return_value=_make_df())
def test_row_list_without_separator(mock_read):
    mcp = MagicMock()
    load_row_list_dataset(mcp, make_config("row_list"), "test.yaml")
    fn = capture_tool_fn(mcp)
    fn()
    mock_read.assert_called_once_with("http://example.org/data.csv")


# -- aggregate --

@patch("mcp_server.engines.aggregate_engine.pd.read_csv", return_value=_make_df())
def test_aggregate_with_separator(mock_read):
    mcp = MagicMock()
    load_aggregate_dataset(mcp, make_config("aggregate", ";"), "test.yaml")
    fn = capture_tool_fn(mcp)
    fn()
    mock_read.assert_called_once_with("http://example.org/data.csv", sep=";")


@patch("mcp_server.engines.aggregate_engine.pd.read_csv", return_value=_make_df())
def test_aggregate_without_separator(mock_read):
    mcp = MagicMock()
    load_aggregate_dataset(mcp, make_config("aggregate"), "test.yaml")
    fn = capture_tool_fn(mcp)
    fn()
    mock_read.assert_called_once_with("http://example.org/data.csv")


# -- top_row --

@patch("mcp_server.engines.top_row_engine.pd.read_csv", return_value=_make_df())
def test_top_row_with_separator(mock_read):
    mcp = MagicMock()
    load_top_row_dataset(mcp, make_config("top_row", ";"), "test.yaml")
    fn = capture_tool_fn(mcp)
    fn()
    mock_read.assert_called_once_with("http://example.org/data.csv", sep=";")


@patch("mcp_server.engines.top_row_engine.pd.read_csv", return_value=_make_df())
def test_top_row_without_separator(mock_read):
    mcp = MagicMock()
    load_top_row_dataset(mcp, make_config("top_row"), "test.yaml")
    fn = capture_tool_fn(mcp)
    fn()
    mock_read.assert_called_once_with("http://example.org/data.csv")


# -- unique_values --

@patch("mcp_server.engines.unique_values_engine.pd.read_csv", return_value=_make_df())
def test_unique_values_with_separator(mock_read):
    mcp = MagicMock()
    load_unique_values_dataset(mcp, make_config("unique_values", ";"), "test.yaml")
    fn = capture_tool_fn(mcp)
    fn()
    mock_read.assert_called_once_with("http://example.org/data.csv", sep=";")


@patch("mcp_server.engines.unique_values_engine.pd.read_csv", return_value=_make_df())
def test_unique_values_without_separator(mock_read):
    mcp = MagicMock()
    load_unique_values_dataset(mcp, make_config("unique_values"), "test.yaml")
    fn = capture_tool_fn(mcp)
    fn()
    mock_read.assert_called_once_with("http://example.org/data.csv")
