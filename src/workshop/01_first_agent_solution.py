"""
How to make your first agent with pydantic - solution
"""

from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from dotenv import load_dotenv
from loguru import logger
import os

load_dotenv()


def build_agent() -> Agent:
    if (base_url := os.getenv("LLM_BASE_URL")) is None:
        logger.warning(
            "LLM_BASE_URL environment variable is not set, defaulting to https://api.openai.com/v1"
        )
        base_url = "https://api.openai.com/v1"
    if (api_key := os.getenv("LLM_API_KEY")) is None:
        raise ValueError("LLM_API_KEY environment variable is not set")
    if (model_name := os.getenv("LLM_MODEL_NAME")) is None:
        model_name = "gpt-5.2"
        logger.warning(
            f"LLM_MODEL_NAME environment variable is not set, defaulting to {model_name}"
        )
    provider = OpenAIProvider(
        base_url=base_url,
        api_key=api_key,
    )
    model = OpenAIResponsesModel(model_name=model_name, provider=provider)
    agent = Agent(model)
    return agent


if __name__ == "__main__":
    agent = build_agent()
    toto = input("Ask the agent: ")
    result = agent.run_sync(toto)
    print(result.output)
