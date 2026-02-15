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


if __name__ == "__main__":
    agent = build_agent()
    toto = input("Ask the agent: ")
    result = agent.run_sync(toto)
    print(result.output)
