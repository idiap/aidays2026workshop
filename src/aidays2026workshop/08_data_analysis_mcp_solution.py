# SPDX-FileCopyrightText: Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: William Droz <william.droz@idiap.ch>
# SPDX-License-Identifier: GPL-3.0-only

"""
Data analysis with MCP - solution

This exercise introduces the Model Context Protocol (MCP).
Instead of registering tools directly on the agent (like exercise 07),
the tools live in a FastMCP server and the agent connects to them
over the MCP stdio transport - all in the same file.

Key differences from exercise 07:
- Tools are defined in a FastMCP server (same file, --serve mode)
- The agent discovers tools at runtime via the MCP protocol
- The agent can list and select CSV files dynamically (not hardcoded)
- This decouples the agent from the tool implementation

Run the web agent (spawns the MCP server as a subprocess):
    uv run python -m aidays2026workshop.08_data_analysis_mcp_solution

Run as MCP server only (stdio transport, used internally by the agent):
    uv run python -m aidays2026workshop.08_data_analysis_mcp_solution --serve

Installing as a CLI tool (makes `plot_mcp` available globally):
    uv tool install . -e

    This installs the `plot_mcp` console script defined in pyproject.toml.
    After installation you can run:
        plot_mcp --serve

Configuring as an MCP server in VS Code:
    Add the following to your VS Code MCP config
    (Settings > MCP or in ~/.config/Code/User/mcp.json):

    {
        "servers": {
            "plot and analysis csv": {
                "type": "stdio",
                "command": "plot_mcp",
                "args": ["--serve"]
            }
        }
    }

    If VS Code runs on Windows with a WSL workspace, use "wsl" as the
    command so it can reach the Linux-side binary:

    {
        "servers": {
            "plot and analysis csv": {
                "type": "stdio",
                "command": "wsl",
                "args": ["plot_mcp", "--serve"]
            }
        }
    }

    Once configured, VS Code Copilot (or any MCP-aware client) will
    automatically discover the list_csv_files, get_csv_info, query_csv,
    and create_and_push_plot tools.

    Try this prompt in VS Code Copilot Chat:
      for each csv in dataset/, do 5 relevants plots. use parallel subagents for each csv to speed up the process. Use the csv basename as chapter.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Literal, Optional

import pandas as pd
import plotly.express as px
import uvicorn
from dotenv import load_dotenv
from fastmcp import FastMCP
from grimoireplot.client import push_plot_sync
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStdio

from aidays2026workshop.common import pydantic_ai_build_model

load_dotenv()


# ============================================================================
# MCP Server - FastMCP tools for CSV data analysis
# ============================================================================

mcp = FastMCP("CSV Data Analysis Server")

DATASET_DIR = Path(__file__).parent.parent.parent / "dataset"

_dataframes: dict[str, pd.DataFrame] = {}


def _resolve_csv_path(filename: str) -> Path:
    """Resolve a CSV filename or path, enforcing the .csv extension constraint.

    Accepts either a bare filename (looked up in DATASET_DIR) or an absolute /
    relative path to any location on the filesystem.  Only ``.csv`` files are
    allowed regardless of where they live.
    """
    if not filename.endswith(".csv"):
        raise ValueError(
            f"Refused to process '{filename}': only .csv files are allowed"
        )
    filepath = Path(filename)
    if not filepath.is_absolute():
        filepath = DATASET_DIR / filepath
    return filepath.resolve()


def _load_df(filename: str) -> pd.DataFrame:
    """Load (and cache) a CSV file.  Bare names are resolved against DATASET_DIR."""
    if filename not in _dataframes:
        filepath = _resolve_csv_path(filename)
        if not filepath.exists():
            raise FileNotFoundError(f"File '{filename}' not found ({filepath})")
        _dataframes[filename] = pd.read_csv(filepath)
    return _dataframes[filename]


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
    """Execute a structured and safe query against a CSV file loaded as a pandas DataFrame.

    This function applies filtering, grouping, aggregation, column selection,
    sorting, and row limiting based on a validated `DataQuery` schema.
    Only predefined operations are supported to prevent arbitrary code execution.

    Parameters
    ----------
    query : DataQuery
        Structured query object containing:
        - filename: Name of the CSV file to query.
        - select: Optional[List[str]]
            Columns to return.
        - filters: Optional[List[FilterCondition]]
            List of filter conditions with column, operator, and value.
        - group_by: Optional[List[str]]
            Columns to group by.
        - aggregation: Optional[str]
            Aggregation function to apply ('mean', 'sum', 'count', 'max', 'min').
            Requires `group_by` to be set.
        - sort_by: Optional[str]
            Column to sort results by.
        - ascending: bool
            Sort direction (default True).
        - limit: Optional[int]
            Maximum number of rows to return. If omitted, no limit is applied.

    Returns
    -------
    List[dict]
        Query results as a list of row dictionaries
        (DataFrame converted using orient="records").
    """
    df = _load_df(query.filename)
    result = df.copy()

    # Apply filters
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

    # Column selection
    if query.select:
        result = result[query.select]

    # Grouping + aggregation, or aggregation alone
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

    # Sorting
    if query.sort_by:
        result = result.sort_values(query.sort_by, ascending=query.ascending)

    # Limit rows
    if query.limit is not None:
        result = result.head(query.limit)

    return result.reset_index(drop=True).to_dict(orient="records")


class PlotRequest(BaseModel):
    """Describes a plotly express chart to create and push to the grimoire server."""

    chart_type: Literal[
        "bar", "line", "scatter", "pie", "histogram", "box", "violin", "area"
    ]
    x: Optional[str] = None
    y: Optional[str] = None
    color: Optional[str] = None
    title: str = "Plot"
    labels: Optional[dict] = None
    data_query: Optional[DataQuery] = None
    grimoire_name: str = "workshop"
    chapter_name: str = "analysis"
    plot_name: str = "plot"


@mcp.tool
def create_and_push_plot(request: PlotRequest) -> dict:
    """Create a plotly express chart from a CSV dataset and push it to the grimoire server for visualization.

    This tool builds a plotly figure using plotly express based on structured parameters,
    optionally applying a DataQuery to filter/aggregate the data first.
    The resulting plot is pushed to the grimoire server via push_plot_sync.

    IMPORTANT: The `x`, `y`, and `color` fields MUST be actual column names that exist
    in the resulting DataFrame AFTER the data_query is applied. Do NOT invent column names.
    Use get_csv_info to discover available columns, or query_csv to inspect the data.

    After a 'count' aggregation with group_by, the count values are stored in the
    non-grouped columns (they keep their original names). For example, grouping by
    ['kind'] with aggregation='count' and select=['kind', 'no'] produces columns
    ['kind', 'no'] where 'no' contains the counts. There is NO column named 'count'.
    Use query_csv first if unsure about the resulting column names.

    Parameters
    ----------
    request : PlotRequest
        Structured plot request containing:
        - chart_type: Type of plotly express chart ('bar', 'line', 'scatter', 'pie', 'histogram', 'box', 'violin', 'area').
        - x: Optional column name for the x-axis. MUST be an actual column in the data.
        - y: Optional column name for the y-axis. MUST be an actual column in the data.
        - color: Optional column name for color grouping. MUST be an actual column in the data.
        - title: Title of the plot.
        - labels: Optional dict mapping column names to display labels.
        - data_query: Optional DataQuery to filter/aggregate the data before plotting.
        - grimoire_name: Name of the grimoire (default 'workshop').
        - chapter_name: Name of the chapter (default 'analysis').
        - plot_name: Unique name for the plot (default 'plot').

    Returns
    -------
    dict
        Response from the grimoire server confirming the plot was pushed.
    """
    # Prepare the data: apply DataQuery if provided
    if request.data_query:
        records = query_csv(request.data_query)
        plot_df = pd.DataFrame(records)
    else:
        return {
            "error": "data_query is required so we know which CSV file to plot. "
            "Set at least data_query.filename."
        }

    available_cols = list(plot_df.columns)
    for field_name, field_value in [
        ("x", request.x),
        ("y", request.y),
        ("color", request.color),
    ]:
        if field_value and field_value not in available_cols:
            return {
                "error": f"Column '{field_value}' (used as {field_name}) does not exist "
                f"in the data. Available columns are: {available_cols}."
            }

    kwargs = {"data_frame": plot_df, "title": request.title}
    if request.x:
        kwargs["x"] = request.x
    if request.y:
        kwargs["y"] = request.y
    if request.color:
        kwargs["color"] = request.color
    if request.labels:
        kwargs["labels"] = request.labels

    chart_fn = {
        "bar": px.bar,
        "line": px.line,
        "scatter": px.scatter,
        "pie": px.pie,
        "histogram": px.histogram,
        "box": px.box,
        "violin": px.violin,
        "area": px.area,
    }

    if request.chart_type == "pie":
        if "x" in kwargs:
            kwargs["names"] = kwargs.pop("x")
        if "y" in kwargs:
            kwargs["values"] = kwargs.pop("y")

    fig = chart_fn[request.chart_type](**kwargs)

    return push_plot_sync(
        grimoire_name=request.grimoire_name,
        chapter_name=request.chapter_name,
        plot_name=request.plot_name,
        fig=fig,
    )


# ============================================================================
# Pydantic AI Agent - connects to this same file's MCP server via stdio
# ============================================================================


def build_agent() -> Agent:
    server = MCPServerStdio(
        sys.executable,
        args=["-m", "aidays2026workshop.08_data_analysis_mcp_solution", "--serve"],
    )

    model = pydantic_ai_build_model()
    agent = Agent(model, toolsets=[server])
    return agent


def run_agent():
    agent = build_agent()
    instruction = """You are a data analyst with access to CSV datasets and plotting tools via MCP.

When the user asks a question:
1. First call list_csv_files to discover available datasets.
2. Then call get_csv_info on the relevant file to understand its structure.
3. Use query_csv to answer data questions with structured queries.
4. When the user asks for a plot or visualization, use create_and_push_plot.
   Give each plot a unique plot_name.

Be concise and precise. Do not return the whole dataset - just the insights
the user asks for."""

    app = agent.to_web(instructions=instruction)
    uvicorn.run(app, host="127.0.0.1", port=9000, reload=False)


# ============================================================================
# CLI entry point: --serve runs the MCP server, otherwise prints usage
# ============================================================================


def main():
    """Entry point for the `plot_mcp` console script."""
    parser = argparse.ArgumentParser(description="MCP CSV Data Analysis & Plotting")
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
