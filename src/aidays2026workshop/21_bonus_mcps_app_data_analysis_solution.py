# SPDX-FileCopyrightText: Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: William Droz <william.droz@idiap.ch>
# SPDX-License-Identifier: GPL-3.0-only

"""
Bonus: Data analysis with MCP Apps UI (prefab_ui)

This exercise builds on exercise 08 (MCP-based CSV analysis) but replaces
grimoireplot / plotly with prefab_ui charts rendered as MCP Apps.

Instead of pushing plots to a remote grimoire server, tools return a
PrefabApp whose view is an AreaChart or BarChart.  MCP-compatible
clients (e.g. Claude Desktop, VS Code Copilot) render the chart inline.

Two chart types are supported: AreaChart and BarChart.

Run the MCP server (stdio transport):
    uv run python -m aidays2026workshop.21_bonus_mcps_app_data_analysis_solution --serve

Run the web agent:
    uv run python -m aidays2026workshop.21_bonus_mcps_app_data_analysis_solution
"""

import argparse
import sys
from pathlib import Path
from typing import List, Literal, Optional

import pandas as pd
import uvicorn
from dotenv import load_dotenv
from fastmcp import FastMCP
from prefab_ui.components.charts import AreaChart, BarChart, ChartSeries
from prefab_ui.app import PrefabApp
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

from aidays2026workshop.common import pydantic_ai_build_model

load_dotenv()


# ============================================================================
# MCP Server
# ============================================================================

mcp = FastMCP("CSV Data Analysis Server (MCP Apps)")

DATASET_DIR = Path(__file__).parent.parent.parent / "dataset"

_dataframes: dict[str, pd.DataFrame] = {}


def _resolve_csv_path(filename: str) -> Path:
    """Resolve a CSV filename, enforcing the .csv extension constraint."""
    if not filename.endswith(".csv"):
        raise ValueError(
            f"Refused to process '{filename}': only .csv files are allowed"
        )
    filepath = Path(filename)
    if not filepath.is_absolute():
        filepath = DATASET_DIR / filepath
    return filepath.resolve()


def _load_df(filename: str) -> pd.DataFrame:
    """Load (and cache) a CSV file."""
    if filename not in _dataframes:
        filepath = _resolve_csv_path(filename)
        if not filepath.exists():
            raise FileNotFoundError(f"File '{filename}' not found ({filepath})")
        _dataframes[filename] = pd.read_csv(filepath)
    return _dataframes[filename]


# ---- Pydantic models for structured queries --------------------------------


class FilterCondition(BaseModel):
    column: str
    operator: Literal["==", "!=", ">", "<", ">=", "<="]
    value: str


class DataQuery(BaseModel):
    filename: str
    select: Optional[List[str]] = None
    filters: Optional[List[FilterCondition]] = None
    group_by: Optional[List[str]] = None
    aggregation: Optional[Literal["mean", "sum", "count", "max", "min"]] = None
    sort_by: Optional[str] = None
    ascending: bool = True
    limit: Optional[int] = None


class SeriesSpec(BaseModel):
    """One series to display on the chart."""

    data_key: str
    label: str


class ChartRequest(BaseModel):
    """Describes an AreaChart or BarChart to render via MCP Apps."""

    chart_type: Literal["area", "bar"]
    x_axis: str
    series: List[SeriesSpec]
    title: str = "Chart"
    show_legend: bool = True
    data_query: DataQuery


# ---- MCP tools -------------------------------------------------------------


@mcp.tool
def list_csv_files() -> list[str]:
    """List all available CSV files in the dataset directory.

    Returns a list of filenames (e.g. ['voting.csv']).
    Use this first to discover which datasets are available.
    """
    return [f.name for f in DATASET_DIR.glob("*.csv")]


@mcp.tool
def get_csv_info(filename: str) -> dict:
    """Get metadata and a preview of a CSV file.

    Parameters
    ----------
    filename : str
        Name of the CSV file (e.g. 'voting.csv').

    Returns
    -------
    dict
        Contains 'columns', 'shape', 'dtypes', and 'head' (first 5 rows).
    """
    df = _load_df(filename)
    return {
        "columns": df.columns.tolist(),
        "shape": list(df.shape),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "head": df.head().to_dict(orient="records"),
    }


@mcp.tool
def query_csv(query: DataQuery) -> list[dict]:
    """Execute a structured and safe query against a CSV file.

    Only predefined operations (filter, group, aggregate, sort, limit)
    are supported to prevent arbitrary code execution.

    Parameters
    ----------
    query : DataQuery
        Structured query with:
        - filename: CSV file to query.
        - select: Columns to return.
        - filters: Filter conditions (column, operator, value).
        - group_by: Columns to group by.
        - aggregation: 'mean', 'sum', 'count', 'max', or 'min'.
        - sort_by: Column to sort by.
        - ascending: Sort direction (default True).
        - limit: Max rows to return.

    Returns
    -------
    list[dict]
        Query results as a list of row dicts.
    """
    df = _load_df(query.filename)
    result = df.copy()

    if query.filters:
        for f in query.filters:
            match f.operator:
                case "==":
                    result = result[result[f.column] == f.value]
                case "!=":
                    result = result[result[f.column] != f.value]
                case ">":
                    result = result[result[f.column] > float(f.value)]
                case "<":
                    result = result[result[f.column] < float(f.value)]
                case ">=":
                    result = result[result[f.column] >= float(f.value)]
                case "<=":
                    result = result[result[f.column] <= float(f.value)]

    if query.select:
        result = result[query.select]

    if query.group_by and query.aggregation:
        grouped = result.groupby(query.group_by)
        if query.aggregation == "count":
            result = grouped.count().reset_index()
        else:
            result = getattr(grouped, query.aggregation)(
                numeric_only=True
            ).reset_index()
    elif query.aggregation:
        if query.aggregation == "count":
            result = result.count().to_frame().T
        else:
            result = result.agg(query.aggregation, numeric_only=True).to_frame().T

    if query.sort_by:
        result = result.sort_values(query.sort_by, ascending=query.ascending)

    if query.limit is not None:
        result = result.head(query.limit)

    return result.reset_index(drop=True).to_dict(orient="records")


@mcp.tool
def create_chart(request: ChartRequest) -> PrefabApp:
    """Create an AreaChart or BarChart from a CSV dataset and return it as an MCP App.

    The tool first applies the data_query to filter/aggregate the CSV data,
    then builds the chart with the specified series.

    IMPORTANT: The `x_axis` and each series `data_key` MUST be actual column
    names that exist in the DataFrame AFTER the data_query is applied.
    Use get_csv_info or query_csv first to discover available column names.

    After a 'count' aggregation with group_by, the count values are stored in
    the non-grouped columns (they keep their original names). For example,
    grouping by ['kind'] with aggregation='count' and select=['kind', 'no']
    produces columns ['kind', 'no'] where 'no' holds the counts. There is
    NO column named 'count'.

    Parameters
    ----------
    request : ChartRequest
        - chart_type: 'area' or 'bar'.
        - x_axis: Column name for the x-axis.
        - series: List of SeriesSpec (data_key, label) for chart series.
        - title: Chart title.
        - show_legend: Whether to show the legend.
        - data_query: DataQuery to filter/aggregate the data before plotting.

    Returns
    -------
    PrefabApp
        An MCP App containing the rendered chart.
    """
    records = query_csv(request.data_query)
    plot_df = pd.DataFrame(records)

    available_cols = list(plot_df.columns)

    if request.x_axis not in available_cols:
        raise ValueError(
            f"Column '{request.x_axis}' (x_axis) does not exist in the data. "
            f"Available columns: {available_cols}"
        )
    for s in request.series:
        if s.data_key not in available_cols:
            raise ValueError(
                f"Column '{s.data_key}' (series data_key) does not exist in the data. "
                f"Available columns: {available_cols}"
            )

    data = plot_df.to_dict(orient="records")
    chart_series = [
        ChartSeries(dataKey=s.data_key, label=s.label) for s in request.series
    ]

    chart_cls = {"area": AreaChart, "bar": BarChart}[request.chart_type]
    view = chart_cls(
        data=data,
        series=chart_series,
        x_axis=request.x_axis,
        show_legend=request.show_legend,
    )

    return PrefabApp(view=view)


# ============================================================================
# Pydantic AI Agent
# ============================================================================


def build_agent() -> Agent:
    server = MCPServerStdio(
        sys.executable,
        args=[
            "-m",
            "aidays2026workshop.21_bonus_mcps_app_data_analysis_solution",
            "--serve",
        ],
    )

    model = pydantic_ai_build_model()
    agent = Agent(model, toolsets=[server])
    return agent


def run_agent():
    agent = build_agent()
    instruction = """You are a data analyst with access to CSV datasets and charting tools via MCP.

When the user asks a question:
1. First call list_csv_files to discover available datasets.
2. Then call get_csv_info on the relevant file to understand its structure.
3. Use query_csv to answer data questions with structured queries.
4. When the user asks for a chart or visualization, use create_chart.
   Only 'area' and 'bar' chart types are available.

Be concise and precise. Do not return the whole dataset - just the insights
the user asks for."""

    app = agent.to_web(instructions=instruction)
    uvicorn.run(app, host="127.0.0.1", port=9000, reload=False)


# ============================================================================
# CLI entry point
# ============================================================================


def main():
    parser = argparse.ArgumentParser(
        description="MCP Apps CSV Data Analysis (AreaChart / BarChart)"
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Run as MCP server (stdio transport)",
    )
    args = parser.parse_args()

    if args.serve:
        mcp.run()
    else:
        run_agent()


if __name__ == "__main__":
    main()
