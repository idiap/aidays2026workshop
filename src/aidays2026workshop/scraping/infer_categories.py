# SPDX-FileCopyrightText: Copyright © 2026 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: William Droz <william.droz@idiap.ch>
# SPDX-License-Identifier: GPL-3.0-only

import argparse
import asyncio
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright
from urllib.parse import urlparse, parse_qs

CATEGORIES_FILE = Path(__file__).parent / "categories.json"

# Product pages to scrape: (product_key, url, list of filter button names)
PRODUCT_PAGES = {
    "Motherboard": {
        "url": "https://www.digitec.ch/fr/s1/producttype/carte-mere-65",
        "filters": ["Chipset", "Socket", "Type de mémoire vive", "Marque"],
    },
    "GPU": {
        "url": "https://www.digitec.ch/fr/s1/producttype/carte-graphique-106",
        "filters": ["Modèle de carte graphique", "Marque"],
    },
    "CPU": {
        "url": "https://www.digitec.ch/fr/s1/producttype/processeur-83",
        "filters": ["Socket", "Famille de processeur", "Marque"],
    },
    "RAM": {
        "url": "https://www.digitec.ch/fr/s1/producttype/memoire-vive-2",
        "filters": ["Configuration de la mémoire", "Type de mémoire vive", "Marque"],
    },
    # Add more product types here, e.g.:
    # "Graphics Card": {
    #     "url": "https://www.digitec.ch/fr/s1/producttype/carte-graphique-54",
    #     "filters": ["Chipset", "Fabricant"],
    # },
}


def load_categories() -> dict:
    """Load existing categories from disk.

    Structure:
    {
      "<product_name>": {
        "url": "<page_url>",
        "filters": {
          "<filter_name>": {
            "category_id": "<id>",
            "values": {
              "<value_name>": "<value_id>",
              ...
            }
          }
        }
      }
    }
    """
    if CATEGORIES_FILE.exists():
        return json.loads(CATEGORIES_FILE.read_text(encoding="utf-8"))
    return {}


def save_categories(categories: dict) -> None:
    """Persist categories to disk."""
    CATEGORIES_FILE.write_text(
        json.dumps(categories, indent=2, ensure_ascii=False), encoding="utf-8"
    )


async def open_filter_dialog(browser, page_url: str, filter_name: str):
    """Open a fresh page, navigate to page_url, and open the given filter dialog.
    Returns the new page."""
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto(page_url, wait_until="domcontentloaded")
    await page.wait_for_timeout(3000)
    await page.locator(f'button:has-text("{filter_name}")').wait_for()
    await page.get_by_role("button", name=filter_name).click()
    await page.wait_for_timeout(3000)
    return page


def _parse_product_count(aria_label: str) -> int:
    """Extract the product count from an aria-label like 'AMD X870E, 42 produits'."""
    match = re.search(r"(\d+)\s+produits?$", aria_label)
    return int(match.group(1)) if match else 0


async def get_all_filter_entries(page, filter_name: str) -> list[tuple[str, int]]:
    """Return all (name, product_count) pairs from the given filter dialog,
    sorted by product count descending."""
    dialog = page.locator(f'div[role="dialog"]:has(h3:text("{filter_name}"))')
    checkboxes = dialog.locator('input[role="checkbox"]')
    count = await checkboxes.count()
    entries = []
    for i in range(count):
        aria_label = await checkboxes.nth(i).get_attribute("aria-label")
        name = aria_label.split(",")[0].strip() if aria_label else "Unknown"
        product_count = _parse_product_count(aria_label) if aria_label else 0
        entries.append((name, product_count))
    entries.sort(key=lambda e: e[1], reverse=True)
    return entries


async def scrape_filter(
    browser,
    page_url: str,
    filter_name: str,
    product_data: dict,
    top_n: int | None = None,
):
    """Scrape values for a single filter on a product page.
    If top_n is set, only process the top N values by product count."""
    filters = product_data.setdefault("filters", {})

    # First pass: collect all checkbox entries (sorted by product count)
    page = await open_filter_dialog(browser, page_url, filter_name)
    all_entries = await get_all_filter_entries(page, filter_name)
    await page.context.close()

    if top_n is not None:
        all_entries = all_entries[:top_n]

    print(
        f"  Found {len(all_entries)} checkboxes for '{filter_name}' (processing {len(all_entries)})"
    )

    known_values = filters.get(filter_name, {}).get("values", {})

    for name, product_count in all_entries:
        if name in known_values:
            print(f"    - {name} ({product_count} products, already known, skipping)")
            continue

        print(f"    - {name} ({product_count} products, computing...)")

        # Fresh browser context for each value
        page = await open_filter_dialog(browser, page_url, filter_name)

        # Find the specific checkbox by aria-label prefix
        dialog = page.locator(f'div[role="dialog"]:has(h3:text("{filter_name}"))')
        target_cb = dialog.locator(f'input[role="checkbox"][aria-label^="{name},"]')

        await target_cb.scroll_into_view_if_needed()
        await target_cb.check()
        await page.locator("#dialog-submit").click()
        await page.wait_for_timeout(2000)

        # Grab URL and parse the filter param (e.g. "8658=3837531")
        current_url = page.url
        parsed = urlparse(current_url)
        query = parse_qs(parsed.query)
        filter_raw = query.get("filter", [""])[0]

        # Split into category_id and value_id
        if "=" in filter_raw:
            category_id, value_id = filter_raw.split("=", 1)
        else:
            category_id, value_id = "", filter_raw

        # Ensure the filter entry exists
        if filter_name not in filters:
            filters[filter_name] = {
                "category_id": category_id,
                "values": {},
            }
        filters[filter_name]["values"][name] = value_id
        known_values = filters[filter_name]["values"]
        print(f"      saved: category_id={category_id}, value_id={value_id}")

        # Close this context before opening the next one
        await page.context.close()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Scrape Digitec filter categories (chipset, etc.) and persist them to JSON."
    )
    parser.add_argument(
        "products",
        nargs="*",
        default=list(PRODUCT_PAGES.keys()),
        choices=list(PRODUCT_PAGES.keys()),
        help="Product types to scrape (default: all)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Run the browser in headless mode",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=CATEGORIES_FILE,
        help=f"Output JSON file (default: {CATEGORIES_FILE})",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        dest="list_products",
        help="List available product types and exit",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=None,
        metavar="N",
        help="Only process the top N values per filter (by product count)",
    )
    return parser.parse_args()


async def main():
    args = parse_args()

    if args.list_products:
        for name, config in PRODUCT_PAGES.items():
            print(
                f"  {name}: {config['url']} (filters: {', '.join(config['filters'])})"
            )
        return

    global CATEGORIES_FILE
    CATEGORIES_FILE = args.output

    categories = load_categories()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=args.headless)

        for product_name in args.products:
            config = PRODUCT_PAGES[product_name]
            page_url = config["url"]
            filter_names = config["filters"]

            print(f"\n=== {product_name} ({page_url}) ===")

            product_data = categories.setdefault(
                product_name, {"url": page_url, "filters": {}}
            )

            for filter_name in filter_names:
                await scrape_filter(
                    browser, str(page_url), filter_name, product_data, top_n=args.top_n
                )
                save_categories(categories)

        print(f"\nDone. Categories saved to {CATEGORIES_FILE}")
        await browser.close()


asyncio.run(main())
