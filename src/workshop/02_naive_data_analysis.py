"""
Naive data analysis - exercise
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


if __name__ == "__main__":
    agent = build_agent()
    dataset_path = Path(__file__).parent.parent.parent / "dataset" / "voting.csv"
    # TODO
    #  - read the dataset
    #  - give it to the agent with a prompt
    #  - tips: you can `instructions` (system prompt) with agent.run_sync

    #  result = ...
    #  print(result.output)
