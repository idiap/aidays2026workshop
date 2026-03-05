"""
How to make your first agent with pydantic - solution
"""

from pydantic_ai import Agent
from dotenv import load_dotenv
import uvicorn

from workshop.common import pydantic_ai_build_model

load_dotenv()


def build_agent() -> Agent:
    model = pydantic_ai_build_model()
    agent = Agent(model)
    return agent


def run_agent():
    agent = build_agent()
    app = agent.to_web()
    uvicorn.run(app, host="127.0.0.1", port=9000, reload=False)


if __name__ == "__main__":
    run_agent()
