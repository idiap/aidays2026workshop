# SPDX-FileCopyrightText: Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: William Droz <william.droz@idiap.ch>
# SPDX-License-Identifier: GPL-3.0-only

from fastmcp import FastMCP
from pydantic_ai import Agent
from dotenv import load_dotenv

from aidays2026workshop.common import pydantic_ai_build_model
from pydantic_ai.mcp import MCPServerStreamableHTTP

from aidays2026workshop.scraping.get_products import (
    load_categories,
    build_filtered_url,
    scrape_products,
)
import argparse
import uvicorn

load_dotenv()


def build_agent() -> Agent:
    server = MCPServerStreamableHTTP("http://localhost:8000/mcp")
    model = pydantic_ai_build_model()
    agent = Agent(model, toolsets=[server])
    return agent


def run_mcp_server(host: str = "0.0.0.0", port: int = 8000):

    mcp = FastMCP("My MCP Server for AI Days 2026 Workshop")

    @mcp.tool
    def load_categories_wrapper() -> dict:
        """Load available product categories and their filters from the categories file."""
        return load_categories()

    @mcp.tool
    def build_filtered_url_wrapper(
        product_name: str, filter_name: str, filter_value: str
    ) -> str:
        """Build a Digitec filtered URL for a product with a given filter name and value."""
        categories = load_categories()
        filters = [f"{filter_name}={filter_value}"]
        return build_filtered_url(categories, product_name, filters)

    @mcp.tool
    def add_price_filter(url: str, min_price: int, max_price: int) -> str:
        """Add a price range filter to a Digitec product URL.

        Args:
            url: The Digitec product URL (with or without existing filters).
            min_price: Minimum price in CHF.
            max_price: Maximum price in CHF.

        Returns:
            The URL with the price filter appended.
        """
        price_param = f"pr%3D{min_price}%3A{max_price}"
        if "?filter=" in url:
            return f"{url}%2C{price_param}"
        else:
            return f"{url}?filter={price_param}"

    @mcp.tool
    async def scrape_products_wrapper(url: str, top_n: int = 10) -> list[dict]:
        """Scrape product links from a Digitec product page URL."""
        return await scrape_products(url, top_n, headless=False)

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
