"""
Data analysis without CodeAgent - solution
"""

from pathlib import Path
from pydantic_ai import Agent
from dotenv import load_dotenv
import pandas as pd

from workshop.common import pydantic_ai_build_model

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
        result = getattr(result.groupby(query.group_by), query.aggregation)(
            numeric_only=True
        ).reset_index()
    elif query.aggregation:
        result = result.agg(query.aggregation, numeric_only=True).to_frame().T

    # Sorting
    if query.sort_by:
        result = result.sort_values(query.sort_by, ascending=query.ascending)

    # Limit rows
    if query.limit:
        result = result.head(query.limit)

    return result.reset_index(drop=True).to_dict(orient="records")


data = df.head()
columns = df.columns.tolist()
intruction = f"""You are a data analyst, you have the following dataset (here the head):
{data}

Here the columns of the dataset:
{columns}

Please analyze it and give me insights about when the user asks for it. Be concise and precise, do not give me the whole dataset back, just what the user asks for."""
app = agent.to_web(instructions=intruction)
# uv run uvicorn workshop.07_data_analysis_without_codeagent_solution:app
