"""
How to make your first agent with pydantic - solution
"""

from pathlib import Path
from dotenv import load_dotenv
from smolagents import CodeAgent
from workshop.common import smolagents_build_model
from grimoireplot.client import push_plot_sync  # noqa: F401
from smolagents import tool  # noqa: F401

load_dotenv()


def build_agent():
    model = smolagents_build_model()
    # TODO:
    #  - docs: https://huggingface.co/docs/smolagents/en/guided_tour#tools
    #  - create a tool with the push_plot_sync function
    #  - the tools should be named "push_plot_sync_tool"
    #  - add the tool to the agent
    agent = CodeAgent(
        model=model,
        tools=[],
        additional_authorized_imports=[
            "pandas",
            "plotly.*",
            "math",
            "stat",
            "numpy",
        ],
    )
    return agent


if __name__ == "__main__":
    # In a terminal, run
    # uv run grimoireplot serve
    # Then browse to http://localhost:8080 to see the plots
    agent = build_agent()
    # Try asking: plot at least 5 relevant plots, I let you decide
    user_question = input("Ask the agent: ")
    dataset_path = Path(__file__).parent.parent.parent / "dataset" / "voting.csv"
    prompt = f"You are a data analyst, you have the following dataset:\n{dataset_path}\nPlease use pandas and plotly to create plots then use the push_plot_sync tool to push plots that answer the user's question (don't use the last two arguments). Here the question: {user_question}"
    result = agent.run(prompt)
