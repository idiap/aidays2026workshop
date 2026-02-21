import asyncio
from playwright.async_api import async_playwright
from urllib.parse import urlparse, parse_qs


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Navigate
        await page.goto("https://www.digitec.ch/fr/s1/producttype/carte-mere-65")
        print(await page.title())

        # Click the "Chipset" button
        await page.locator('button:has-text("Chipset")').wait_for()
        await page.get_by_role("button", name="Chipset").click()

        # Wait for the Chipset dialog to appear
        await page.wait_for_timeout(3000)  # 3 seconds

        # Locate all checkboxes inside the Chipset dialog
        chipset_dialog = page.locator('div[role="dialog"]:has(h3:text("Chipset"))')
        checkboxes = chipset_dialog.locator('input[role="checkbox"]')
        count = await checkboxes.count()

        print(f"Found {count} chipset checkboxes:")
        for i in range(count):
            checkbox = checkboxes.nth(i)
            aria_label = await checkbox.get_attribute("aria-label")
            name = aria_label.split(",")[0].strip() if aria_label else "Unknown"
            print(f"  - {name}")
            await checkbox.check()  # Check the checkbox
            await page.locator("#dialog-submit").click()
            # Grab URL and parse params
            current_url = page.url
            parsed = urlparse(current_url)
            query = parse_qs(parsed.query)
            print(f"\t  - {name} - URL params: {query}")
            break

        # Screenshot
        await page.screenshot(path="screenshot.png")

        # Close
        await browser.close()


asyncio.run(main())
