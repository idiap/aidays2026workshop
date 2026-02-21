import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright
from urllib.parse import urlparse, parse_qs

CATEGORIES_FILE = Path(__file__).parent / "categories.json"


def load_categories() -> dict:
    """Load existing categories from disk.

    Structure:
    {
      "<category_name>": {
        "category_id": "<id>",
        "values": {
          "<value_name>": "<value_id>",
          ...
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


BASE_URL = "https://www.digitec.ch/fr/s1/producttype/carte-mere-65"


async def open_chipset_dialog(browser):
    """Open a fresh page, navigate to base URL, and open the Chipset filter dialog.
    Returns the new page."""
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto(BASE_URL, wait_until="domcontentloaded")
    await page.wait_for_timeout(3000)
    await page.locator('button:has-text("Chipset")').wait_for()
    await page.get_by_role("button", name="Chipset").click()
    await page.wait_for_timeout(3000)
    return page


async def get_all_chipset_names(page) -> list[str]:
    """Return all checkbox names from the Chipset dialog (no scrolling)."""
    chipset_dialog = page.locator('div[role="dialog"]:has(h3:text("Chipset"))')
    checkboxes = chipset_dialog.locator('input[role="checkbox"]')
    count = await checkboxes.count()
    names = []
    for i in range(count):
        aria_label = await checkboxes.nth(i).get_attribute("aria-label")
        name = aria_label.split(",")[0].strip() if aria_label else "Unknown"
        names.append(name)
    return names


async def main():
    categories = load_categories()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # First pass: collect all chipset checkbox names
        page = await open_chipset_dialog(browser)
        all_names = await get_all_chipset_names(page)
        await page.context.close()
        print(f"Found {len(all_names)} chipset checkboxes")

        category_name = "Chipset"
        known_values = categories.get(category_name, {}).get("values", {})

        for name in all_names:
            if name in known_values:
                print(f"  - {name} (already known, skipping)")
                continue

            print(f"  - {name} (computing...)")

            # Fresh browser context for each value (avoids HTTP/2 connection reuse issues)
            page = await open_chipset_dialog(browser)

            # Find the specific checkbox by aria-label prefix
            chipset_dialog = page.locator('div[role="dialog"]:has(h3:text("Chipset"))')
            target_cb = chipset_dialog.locator(
                f'input[role="checkbox"][aria-label^="{name},"]'
            )

            await target_cb.scroll_into_view_if_needed()
            await target_cb.check()
            await page.locator("#dialog-submit").click()
            await page.wait_for_timeout(2000)

            # Grab URL and parse the filter param (e.g. "8658=3837531")
            current_url = page.url
            parsed = urlparse(current_url)
            query = parse_qs(parsed.query)
            filter_raw = query.get("filter", [""])[0]  # e.g. "8658=3837531"

            # Split into category_id and value_id
            if "=" in filter_raw:
                category_id, value_id = filter_raw.split("=", 1)
            else:
                category_id, value_id = "", filter_raw

            # Ensure the category entry exists
            if category_name not in categories:
                categories[category_name] = {
                    "category_id": category_id,
                    "values": {},
                }
            categories[category_name]["values"][name] = value_id
            save_categories(categories)
            known_values = categories[category_name]["values"]
            print(f"    saved: category_id={category_id}, value_id={value_id}")

            # Close this context before opening the next one
            await page.context.close()

        print(f"\nDone. Categories saved to {CATEGORIES_FILE}")

        # Close
        await browser.close()


asyncio.run(main())
