# SPDX-FileCopyrightText: Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: William Droz <william.droz@idiap.ch>
# SPDX-License-Identifier: GPL-3.0-only

"""CLI to query Digitec product pages using pre-scraped filter categories.

Builds a filtered URL from categories.json, opens the page with Playwright,
and extracts the top N product links.

Examples:
    # List available products and their filters
    python get_products.py --list

    # Get top 5 DDR5 RAM sticks with 2x32GB configuration
    python get_products.py RAM --filters "Configuration de la mémoire=2 x 32GB" "Type de mémoire vive=RAM DDR5" --top-n 5

    # Get top 10 motherboards with AMD B850 chipset and AM5 socket
    python get_products.py Motherboard --filters "Chipset=AMD B850" "Socket=AM5" --top-n 10

    # Get top 3 GPUs with a specific model
    python get_products.py GPU --filters "Modèle de carte graphique=GeForce RTX 5080"
"""

import argparse
import asyncio
import json
from pathlib import Path
from urllib.parse import quote

from playwright.async_api import async_playwright

CATEGORIES_FILE = Path(__file__).parent / "categories.json"

BASE_URL = "https://www.digitec.ch"


def load_categories(path: Path = CATEGORIES_FILE) -> dict:
    """Load categories from JSON file."""
    if not path.exists():
        raise FileNotFoundError(
            f"Categories file not found: {path}\n"
            "Run infer_categories.py first to generate it."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def build_filtered_url(categories: dict, product_name: str, filters: list[str]) -> str:
    """Build a Digitec URL with filter query parameters.

    Args:
        categories: The loaded categories dict.
        product_name: e.g. "RAM", "Motherboard".
        filters: List of "FilterName=ValueName" strings.

    Returns:
        Full URL with encoded filter query string.
    """
    product = categories[product_name]
    base_url = product["url"]

    if not filters:
        return base_url

    filter_parts = []
    for f in filters:
        if "=" not in f:
            raise ValueError(
                f"Invalid filter format '{f}'. Expected 'FilterName=ValueName'."
            )
        filter_name, value_name = f.split("=", 1)

        if filter_name not in product["filters"]:
            available = ", ".join(product["filters"].keys())
            raise ValueError(
                f"Unknown filter '{filter_name}' for {product_name}. "
                f"Available filters: {available}"
            )

        filter_info = product["filters"][filter_name]
        category_id = filter_info["category_id"]
        values = filter_info["values"]

        if value_name not in values:
            available = ", ".join(values.keys())
            raise ValueError(
                f"Unknown value '{value_name}' for filter '{filter_name}'. "
                f"Available values: {available}"
            )

        value_id = values[value_name]
        filter_parts.append(f"{category_id}={value_id}")

    # Join multiple filters with comma, then URL-encode
    filter_param = quote(",".join(filter_parts), safe="")
    return f"{base_url}?filter={filter_param}"


async def scrape_products(url: str, top_n: int, headless: bool = True) -> list[dict]:
    """Open the filtered product page and extract product links.

    Returns a list of dicts with 'name' and 'url' keys.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=["--disable-http2"],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        await page.goto(url, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        # Find all links whose href starts with /fr/s1/product/
        links = page.locator('a[href^="/fr/s1/product/"]')
        count = await links.count()

        seen = set()
        products = []
        for i in range(count):
            href = await links.nth(i).get_attribute("href")
            if href in seen:
                continue
            seen.add(href)

            # Extract product name from aria-label
            name = await links.nth(i).get_attribute("aria-label") or href

            products.append(
                {
                    "name": name,
                    "url": f"{BASE_URL}{href}",
                }
            )

            if len(products) >= top_n:
                break

        await browser.close()
        return products


def list_products(categories: dict) -> None:
    """Print available products and their filter options."""
    for product_name, product_data in categories.items():
        print(f"\n{product_name}")
        print(f"  URL: {product_data['url']}")
        for filter_name, filter_info in product_data.get("filters", {}).items():
            values = ", ".join(filter_info.get("values", {}).keys())
            print(f"  Filter: {filter_name}")
            print(f"    Values: {values}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Query Digitec product pages with filters and return top N products.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  %(prog)s RAM --filters "Type de mémoire vive=RAM DDR5" --top-n 5\n'
            '  %(prog)s Motherboard --filters "Chipset=AMD B850" "Socket=AM5"\n'
            "  %(prog)s --list\n"
        ),
    )
    parser.add_argument(
        "product",
        nargs="?",
        help="Product type to query (e.g. RAM, GPU, CPU, Motherboard)",
    )
    parser.add_argument(
        "--filters",
        nargs="*",
        default=[],
        metavar="FILTER=VALUE",
        help='Filter specifications as "FilterName=ValueName" pairs',
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=5,
        metavar="N",
        help="Number of products to return (default: 5)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Run browser in headless mode (default: True)",
    )
    parser.add_argument(
        "--no-headless",
        action="store_false",
        dest="headless",
        help="Run browser in visible mode",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_products",
        help="List available product types and filters, then exit",
    )
    parser.add_argument(
        "--categories",
        type=Path,
        default=CATEGORIES_FILE,
        help=f"Path to categories JSON file (default: {CATEGORIES_FILE})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output results as JSON",
    )
    return parser.parse_args()


async def main():
    args = parse_args()
    categories = load_categories(args.categories)

    if args.list_products:
        list_products(categories)
        return

    if not args.product:
        available = ", ".join(categories.keys())
        print(f"Error: Please specify a product type. Available: {available}")
        print("Use --list to see all products and filter options.")
        return

    if args.product not in categories:
        available = ", ".join(categories.keys())
        print(f"Error: Unknown product '{args.product}'. Available: {available}")
        return

    url = build_filtered_url(categories, args.product, args.filters)
    print(f"URL: {url}\n")

    products = await scrape_products(url, args.top_n, headless=args.headless)

    if not products:
        print("No products found.")
        return

    if args.output_json:
        print(json.dumps(products, indent=2, ensure_ascii=False))
    else:
        print(f"Top {len(products)} products:\n")
        for i, product in enumerate(products, 1):
            print(f"  {i}. {product['name']}")
            print(f"     {product['url']}\n")


if __name__ == "__main__":
    asyncio.run(main())
