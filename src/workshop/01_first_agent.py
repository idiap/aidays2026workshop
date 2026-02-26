"""
How to make your first agent with pydantic
"""

from pydantic_ai import Agent
from dotenv import load_dotenv

load_dotenv()


def build_agent() -> Agent:  # type: ignore
    # https://ai.pydantic.dev/models/openai/#custom-openai-client
    # I suggest openai-compatible or OpenResponses
    # Do not commit or put API keys in the code, use environment variables and load them with dotenv
    # For this workshop, we use LLM_BASE_URL, LLM_API_KEY and LLM_MODEL_NAME environment variables to configure the agent's model
    NotImplementedError(
        "You need to implement the build_agent function to create your agent. Check the solution file for reference."
    )


if __name__ == "__main__":
    agent = build_agent()
    user_input = input("Ask the agent: ")
    result = agent.run_sync(user_input)
    print(result.output)
