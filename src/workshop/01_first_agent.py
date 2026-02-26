"""
How to make your first agent with pydantic
"""

from pydantic_ai import Agent
from dotenv import load_dotenv

load_dotenv()


def build_agent() -> Agent:  # type: ignore
    # https://ai.pydantic.dev/models/openai/#custom-openai-client
    # I suggest openai-compatible or OpenResponses
    NotImplementedError(
        "You need to implement the build_agent function to create your agent. Check the solution file for reference."
    )


if __name__ == "__main__":
    agent = build_agent()
    user_input = input("Ask the agent: ")
    result = agent.run_sync(user_input)
    print(result.output)
