"""
How to make your first agent with pydantic - solution
"""

from pydantic_ai import Agent
from dotenv import load_dotenv

from workshop.common import pydantic_ai_build_model

load_dotenv()


def build_agent() -> Agent:
    model = pydantic_ai_build_model()
    agent = Agent(model)
    return agent


agent = build_agent()
app = agent.to_web()
# run with uv run uvicorn workshop.01_first_agent_solution_generic_webchat:app
