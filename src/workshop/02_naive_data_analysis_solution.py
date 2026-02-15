"""
How to make your first agent with pydantic - solution
"""

from pathlib import Path
from pydantic_ai import Agent
from dotenv import load_dotenv

from workshop.common import pydantic_ai_build_model

load_dotenv()


def build_agent() -> Agent:
    model = pydantic_ai_build_model()
    agent = Agent(model)
    return agent


agent = build_agent()
dataset_path = Path(__file__).parent.parent.parent / "dataset" / "voting.csv"
data = dataset_path.read_text()
print("Data loaded, asking the agent to analyze it... length:", len(data))
intruction = f"""You are a data analyst, you have the following dataset:
{data}
Please analyze it and give me insights about when the user asks for it. Be concise and precise, do not give me the whole dataset back, just insights."""
app = agent.to_web(instructions=intruction)
# run with uv run uvicorn workshop.02_naive_data_analysis_solution:app
