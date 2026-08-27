"""Playwright browser automation, with an honest failure when it is not installed."""
from __future__ import annotations


async def fetch_page(url: str, timeout_ms: int = 15000) -> dict:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        return {"ok": False, "error": "playwright not installed (pip install playwright)"}

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url, timeout=timeout_ms)
            title = await page.title()
            text = (await page.inner_text("body"))[:2000]
            await browser.close()
        return {"ok": True, "url": url, "title": title, "text_preview": text}
    except Exception as exc:
        return {"ok": False, "url": url,
                "error": f"{type(exc).__name__}: {exc}",
                "hint": "run: playwright install chromium"}
