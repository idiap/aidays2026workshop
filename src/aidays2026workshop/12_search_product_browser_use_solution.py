# SPDX-FileCopyrightText: Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: William Droz <william.droz@idiap.ch>
# SPDX-License-Identifier: GPL-3.0-only

from fastmcp import FastMCP
from pydantic import BaseModel
from pydantic_ai import Agent
from dotenv import load_dotenv

from pydantic_ai.mcp import MCPServerStreamableHTTP

from browser_use import Agent as BrowserUseAgent, ChatOpenAI

import argparse
import os
import uvicorn

from aidays2026workshop.common import pydantic_ai_build_model

load_dotenv()


class BrowserResult(BaseModel):
    answer: str


def _build_browser_use_llm() -> ChatOpenAI:
    """Build a ChatOpenAI instance for browser-use from env vars."""
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        raise ValueError("LLM_API_KEY environment variable is not set")
    model_name = os.getenv("LLM_MODEL_NAME", "gpt-5.2")
    base_url = os.getenv("LLM_BASE_URL")
    kwargs: dict = {"model": model_name, "api_key": api_key}
    if base_url:
        kwargs["base_url"] = base_url
    return ChatOpenAI(**kwargs)


def build_agent() -> Agent:
    server = MCPServerStreamableHTTP("http://localhost:8000/mcp")
    model = pydantic_ai_build_model()
    agent = Agent(model, toolsets=[server])
    return agent


def run_mcp_server(host: str = "0.0.0.0", port: int = 8000):

    mcp = FastMCP("My MCP Server for AI Days 2026 Workshop")

    @mcp.tool
    async def browser_use(task: str) -> BrowserResult | str:
        """Use a browser automation agent to perform a task on the web.

        The task should describe what you want the browser agent to do,
        including any URLs to visit and actions to perform.

        Args:
            task: A natural language description of the browser task to perform.

        Returns:
            The final result extracted by the browser agent.
        """
        llm = _build_browser_use_llm()
        agent = BrowserUseAgent(
            task=task,
            llm=llm,
            use_thinking=False,
            output_model_schema=BrowserResult,
        )
        history = await agent.run()
        result = history.final_result()
        if result:
            parsed = BrowserResult.model_validate_json(result)
            return parsed
        return "Browser task completed but no content was extracted."

    mcp.run(transport="http", host=host, port=port)


def run_agent():

    agent = build_agent()
    app = agent.to_web()
    uvicorn.run(app, host="127.0.0.1", port=9000, reload=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MCP Server / Agent CLI")
    parser.add_argument(
        "--server", action="store_true", help="Run the MCP server instead of the agent"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host to bind the server to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)",
    )
    args = parser.parse_args()

    if args.server:
        run_mcp_server(host=args.host, port=args.port)
    else:
        run_agent()
