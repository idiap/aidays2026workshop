# SPDX-FileCopyrightText: Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: William Droz <william.droz@idiap.ch>
# SPDX-License-Identifier: GPL-3.0-only

"""
Tests for aidays2026workshop.common utilities.

These tests use the real environment variables (LLM_BASE_URL, LLM_API_KEY, etc.)
as configured by the user. They verify that the setup works and that an agent
can produce a response, without asserting on response content.
"""

import pytest
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIResponsesModel
from pydantic_ai.providers.openai import OpenAIProvider
from smolagents import CodeAgent, OpenAIModel

from aidays2026workshop.common import (
    pydantic_ai_build_provider_openai,
    pydantic_ai_build_model_openai_chat,
    pydantic_ai_build_model_openai_responses,
    pydantic_ai_build_model,
    smolagents_build_model,
)


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------


def test_build_provider_returns_openai_provider():
    provider = pydantic_ai_build_provider_openai()
    assert isinstance(provider, OpenAIProvider)


def test_build_provider_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(ValueError, match="LLM_API_KEY"):
        pydantic_ai_build_provider_openai()


# ---------------------------------------------------------------------------
# Model builders
# ---------------------------------------------------------------------------


def test_build_model_openai_chat_returns_chat_model():
    model = pydantic_ai_build_model_openai_chat()
    assert isinstance(model, OpenAIChatModel)


def test_build_model_openai_responses_returns_responses_model():
    model = pydantic_ai_build_model_openai_responses()
    assert isinstance(model, OpenAIResponsesModel)


def test_build_model_defaults_to_chat(monkeypatch):
    monkeypatch.delenv("LLM_USE_OPENRESPONSES", raising=False)
    model = pydantic_ai_build_model()
    assert isinstance(model, OpenAIChatModel)


def test_build_model_uses_responses_when_enabled(monkeypatch):
    monkeypatch.setenv("LLM_USE_OPENRESPONSES", "true")
    model = pydantic_ai_build_model()
    assert isinstance(model, OpenAIResponsesModel)


def test_build_model_with_explicit_provider():
    provider = pydantic_ai_build_provider_openai()
    model = pydantic_ai_build_model(provider=provider)
    assert isinstance(model, (OpenAIChatModel, OpenAIResponsesModel))


# ---------------------------------------------------------------------------
# Agent integration - just verify it responds
# ---------------------------------------------------------------------------


def test_agent_responds():
    """Build an agent with the user's environment and verify it produces a non-empty response."""
    model = pydantic_ai_build_model()
    agent = Agent(model)
    result = agent.run_sync("Say hello")
    assert result.output is not None
    assert isinstance(result.output, str)
    assert len(result.output) > 0


# ---------------------------------------------------------------------------
# smolagents - model builder
# ---------------------------------------------------------------------------


def test_smolagents_build_model_returns_openai_model():
    model = smolagents_build_model()
    assert isinstance(model, OpenAIModel)


def test_smolagents_build_model_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    with pytest.raises(ValueError, match="LLM_API_KEY"):
        smolagents_build_model()


# ---------------------------------------------------------------------------
# smolagents - agent integration
# ---------------------------------------------------------------------------


def test_smolagents_code_agent_responds():
    """Build a CodeAgent with the user's environment and verify it produces a non-empty response."""
    model = smolagents_build_model()
    agent = CodeAgent(model=model, tools=[])
    result = agent.run("What is 2 + 2?")
    assert result is not None
    assert str(result).strip() != ""
