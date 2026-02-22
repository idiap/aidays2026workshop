"""
Naive data analysis - solution
"""

from pathlib import Path
from pydantic_ai import Agent
from dotenv import load_dotenv
import pandas as pd
import plotly.express as px

from workshop.common import pydantic_ai_build_model
from grimoireplot.client import push_plot_sync

from typing import List, Optional, Literal
from pydantic import BaseModel


class FilterCondition(BaseModel):
    column: str
    operator: Literal["==", "!=", ">", "<", ">=", "<="]
    value: str


class DataQuery(BaseModel):
    select: Optional[List[str]] = None
    filters: Optional[List[FilterCondition]] = None
    group_by: Optional[List[str]] = None
    aggregation: Optional[Literal["mean", "sum", "count", "max", "min"]] = None
    sort_by: Optional[str] = None
    ascending: bool = True
    limit: Optional[int] = 10


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


load_dotenv()


def build_agent() -> Agent:
    model = pydantic_ai_build_model()
    agent = Agent(model)
    return agent


agent = build_agent()
dataset_path = Path(__file__).parent.parent.parent / "dataset" / "voting.csv"

df = pd.read_csv(dataset_path)


@agent.tool_plain
def query_dataframe(query: DataQuery):
    """Execute a structured and safe query against a pandas DataFrame.

    This function applies filtering, grouping, aggregation, column selection,
    sorting, and row limiting based on a validated `DataQuery` schema.
    Only predefined operations are supported to prevent arbitrary code execution.

    Parameters
    ----------
    df : pd.DataFrame
        The source dataframe to query.

    query : DataQuery
        Structured query object containing:
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
            Maximum number of rows to return (default 10).

    Returns
    -------
    List[dict]
        Query results as a list of row dictionaries
        (DataFrame converted using orient="records").
    """

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

    # Column selection (before aggregation so we aggregate only selected columns)
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
    if query.limit:
        result = result.head(query.limit)

    return result.reset_index(drop=True).to_dict(orient="records")


@agent.tool_plain(sequential=True)
def create_and_push_plot(request: PlotRequest):
    """Create a plotly express chart from the dataset and push it to the grimoire server for visualization.

    This tool builds a plotly figure using plotly express based on structured parameters,
    optionally applying a DataQuery to filter/aggregate the data first.
    The resulting plot is pushed to the grimoire server via push_plot_sync.

    IMPORTANT: The `x`, `y`, and `color` fields MUST be actual column names that exist
    in the resulting DataFrame AFTER the data_query is applied. Do NOT invent column names.
    The raw dataset columns are: no, date_of_voting, title_it, title_fr, title_de, kind,
    recommendation, total_voters, domestic_voters, overseas_voters, ballots_returned,
    participation, invalid_voting_ballots, blank_voting_ballots, valid_voting_ballots,
    total_yes, ratio_yes, total_no, ratio_no, cantons_voting_yes, cantons_voting_no, outcome.

    After a 'count' aggregation with group_by, the count values are stored in the
    non-grouped columns (they keep their original names). For example, grouping by
    ['kind'] with aggregation='count' and select=['kind', 'no'] produces columns
    ['kind', 'no'] where 'no' contains the counts. There is NO column named 'count'.
    Use query_dataframe first if unsure about the resulting column names.

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
        - plot_name: Name of the plot (default 'plot').

    Returns
    -------
    dict
        Response from the grimoire server confirming the plot was pushed.
    """
    # Prepare the data: apply DataQuery if provided
    if request.data_query:
        records = query_dataframe(request.data_query)
        plot_df = pd.DataFrame(records)
    else:
        plot_df = df.copy()

    # Validate that x, y, color columns exist in the DataFrame
    available_cols = list(plot_df.columns)
    for field_name, field_value in [
        ("x", request.x),
        ("y", request.y),
        ("color", request.color),
    ]:
        if field_value and field_value not in available_cols:
            return {
                "error": f"Column '{field_value}' (used as {field_name}) does not exist in the data. "
                f"Available columns are: {available_cols}. "
                f"Use query_dataframe first to inspect the data, or pick a valid column name."
            }

    # Build kwargs for plotly express
    kwargs = {"data_frame": plot_df, "title": request.title}
    if request.x:
        kwargs["x"] = request.x
    if request.y:
        kwargs["y"] = request.y
    if request.color:
        kwargs["color"] = request.color
    if request.labels:
        kwargs["labels"] = request.labels

    # Map chart_type to the plotly express function
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

    # For pie charts, map x -> names and y -> values
    if request.chart_type == "pie":
        if "x" in kwargs:
            kwargs["names"] = kwargs.pop("x")
        if "y" in kwargs:
            kwargs["values"] = kwargs.pop("y")

    fig = chart_fn[request.chart_type](**kwargs)

    # Push to grimoire server
    return push_plot_sync(
        grimoire_name=request.grimoire_name,
        chapter_name=request.chapter_name,
        plot_name=request.plot_name,
        fig=fig,
    )


data = df.head()
columns = df.columns.tolist()
intruction = f"""You are a data analyst, you have the following dataset (here the head):
{data}

Here the columns of the dataset:
{columns}

Please analyze it and give me insights about when the user asks for it. Be concise and precise, do not give me the whole dataset back, just what the user asks for.
When the user asks for a plot or visualization, use the create_and_push_plot tool. Give each plot a unique plot_name."""
app = agent.to_web(instructions=intruction)
# uv run uvicorn workshop.06_data_analysis_without_codeagent_solution_with_plots:app
