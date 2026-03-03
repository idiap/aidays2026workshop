"""
Data analysis with CodeAgent - solution
"""

from pathlib import Path
from dotenv import load_dotenv
from loguru import logger
from smolagents import OpenAIModel, CodeAgent
import os

load_dotenv()


def build_agent():
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
    model = OpenAIModel(
        model_id=model_name,
        api_base=base_url,
        api_key=api_key,
    )
    agent = CodeAgent(model=model, tools=[], additional_authorized_imports=["pandas"])
    return agent


if __name__ == "__main__":
    agent = build_agent()
    user_question = input("Ask the agent: ")
    dataset_path = Path(__file__).parent.parent.parent / "dataset" / "voting.csv"
    prompt = f"You are a data analyst, you have the following dataset:\n{dataset_path}\nPlease use pandas to answer the user's question: {user_question}"
    result = agent.run(prompt)
    print(result)
