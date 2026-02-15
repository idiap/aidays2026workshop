"""
Common utilities for the workshop.
"""

from pydantic_ai.models.openai import OpenAIChatModel, OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from dotenv import load_dotenv
from loguru import logger
import os

load_dotenv()


def pydantic_ai_build_provider_openai() -> OpenAIProvider:
    """
    For both the OpenAIChatModel and OpenAIResponsesModel, the provider is the same, so we can reuse this function.
    """
    if (base_url := os.getenv("LLM_BASE_URL")) is None:
        logger.warning(
            "LLM_BASE_URL environment variable is not set, defaulting to https://api.openai.com/v1"
        )
        base_url = "https://api.openai.com/v1"
    if (api_key := os.getenv("LLM_API_KEY")) is None:
        raise ValueError("LLM_API_KEY environment variable is not set")
    provider = OpenAIProvider(
        base_url=base_url,
        api_key=api_key,
    )
    return provider


def pydantic_ai_build_model_openai_chat(
    provider: OpenAIProvider | None = None,
) -> OpenAIChatModel:
    """
    Build an OpenAIChatModel with the given provider.
    """
    if provider is None:
        provider = pydantic_ai_build_provider_openai()

    if (model_name := os.getenv("LLM_MODEL_NAME")) is None:
        model_name = "gpt-5.2"
        logger.info(
            f"LLM_MODEL_NAME environment variable is not set, defaulting to {model_name}"
        )
    model = OpenAIChatModel(model_name=model_name, provider=provider)
    return model


def pydantic_ai_build_model_openai_responses(
    provider: OpenAIProvider | None = None,
) -> OpenAIResponsesModel:
    """
    Build an OpenAIResponsesModel with the given provider.
    """
    if provider is None:
        provider = pydantic_ai_build_provider_openai()

    if (model_name := os.getenv("LLM_MODEL_NAME")) is None:
        model_name = "gpt-5.2"
        logger.info(
            f"LLM_MODEL_NAME environment variable is not set, defaulting to {model_name}"
        )
    model = OpenAIResponsesModel(model_name=model_name, provider=provider)
    return model


def pydantic_ai_build_model(
    provider: OpenAIProvider | None = None,
) -> OpenAIChatModel | OpenAIResponsesModel:
    """
    Build either an OpenAIChatModel or an OpenAIResponsesModel based on the LLM_USE_OPENRESPONSES environment variable.
    """
    use_open_responses = os.getenv("LLM_USE_OPENRESPONSES", "false").lower() == "true"
    logger.info(
        f"LLM_USE_OPENRESPONSES is set to {use_open_responses}, using {'OpenAIResponsesModel' if use_open_responses else 'OpenAIChatModel'}"
    )
    if use_open_responses:
        return pydantic_ai_build_model_openai_responses(provider)
    else:
        return pydantic_ai_build_model_openai_chat(provider)
