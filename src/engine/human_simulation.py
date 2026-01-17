import random
import asyncio
from playwright.async_api import Page

class HumanSimulator:
    """
    Handles browser interactions to simulate human-like behavior.
    """

    @staticmethod
    async def gentle_scroll(page: Page, scroll_delay: float = 0.5):
        """Simulates a gentle scroll down the page."""
        await page.evaluate("window.scrollBy(0, window.innerHeight / 2);")
        await asyncio.sleep(scroll_delay + random.uniform(0.1, 0.5))

    @staticmethod
    async def random_delay(min_delay: float = 0.5, max_delay: float = 2.0):
        """Waits for a random duration."""
        await asyncio.sleep(random.uniform(min_delay, max_delay))

    @staticmethod
    async def smart_wait_for_selector(page: Page, selector: str, timeout: int = 10000):
        """Waits for a selector to be present in the DOM."""
        await page.wait_for_selector(selector, timeout=timeout)
