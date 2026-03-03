"""
Data analysis with CodeAgent plots
"""

from pathlib import Path
from dotenv import load_dotenv
from smolagents import CodeAgent
from workshop.common import smolagents_build_model
from grimoireplot.client import push_plot_sync  # noqa: F401

load_dotenv()


def build_agent():
    model = smolagents_build_model()
    agent = CodeAgent(
        model=model,
        tools=[],
        additional_authorized_imports=[
            "pandas",
            "plotly.*",
            "grimoireplot.client",
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
    prompt = f"You are a data analyst, you have the following dataset:\n{dataset_path}\nPlease use pandas and plotly to create plots then use push_plot_sync from grimoireplot.client to push plots that answer to answer the user's question. Here the question: {user_question}"
    #  TODO how to explain the model how to use push_plot_sync?
    #  prompt = ...
    result = agent.run(prompt)
