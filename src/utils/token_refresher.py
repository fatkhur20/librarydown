import json
import os
import asyncio
from typing import Dict, Any, Optional
from loguru import logger
from datetime import datetime

# Define path for token storage
TOKEN_STORAGE_PATH = os.path.join(os.getcwd(), "data", "youtube_tokens.json")

async def refresh_youtube_tokens() -> bool:
    """
    Launches a headless browser to fetch fresh YouTube PoToken, Visitor Data, and Cookies.
    Saves the data to data/youtube_tokens.json.
    """
    try:
        from playwright.async_api import async_playwright
        from playwright_stealth import Stealth

        logger.info("Starting YouTube token refresh...")

        async with async_playwright() as p:
            # Configure proxy if set
            proxy_config = None
            proxy_url = os.getenv("PROXY_URL")
            if proxy_url:
                logger.info(f"Using proxy: {proxy_url}")
                proxy_config = {"server": proxy_url}

            # Launch browser (chromium)
            # args are optimized for running in container/headless
            browser = await p.chromium.launch(
                headless=True,
                proxy=proxy_config,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--single-process',
                    '--disable-gpu'
                ]
            )

            # Create a new context with a realistic user agent
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}
            )

            page = await context.new_page()

            # Apply stealth measures
            stealth = Stealth()
            await stealth.apply_stealth_async(page)

            # Retry mechanism
            max_retries = 3
            success = False

            for attempt in range(max_retries):
                try:
                    # Navigate to YouTube Music (usually lighter and triggers same config)
                    logger.info(f"Navigating to YouTube Music (Attempt {attempt + 1}/{max_retries})...")
                    await page.goto("https://music.youtube.com", timeout=60000, wait_until="networkidle")

                    # Wait a bit for scripts to initialize
                    await asyncio.sleep(5)

                    # Extract PoToken and Visitor Data using JavaScript
                    logger.info("Extracting tokens...")

                    po_token = await page.evaluate("() => window.yt && window.yt.config_ && window.yt.config_.PO_TOKEN")
                    visitor_data = await page.evaluate("() => window.yt && window.yt.config_ && window.yt.config_.VISITOR_DATA")

                    # If we got tokens, break the loop
                    if po_token and visitor_data:
                        success = True
                        break
                    else:
                        logger.warning(f"Attempt {attempt + 1}: Tokens found incomplete (Po: {bool(po_token)}, Visitor: {bool(visitor_data)})")

                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    await asyncio.sleep(5) # Wait before retry

            if not success:
                logger.error("Failed to retrieve tokens after all retries.")
                await browser.close()
                return False

            # Get cookies
            cookies = await context.cookies()

            # Format data
            token_data = {
                "updated_at": datetime.utcnow().isoformat(),
                "po_token": po_token,
                "visitor_data": visitor_data,
                "cookies": cookies,
                "cookies_netscape": _convert_cookies_to_netscape(cookies)
            }

            if po_token:
                logger.info(f"Successfully retrieved PoToken: {po_token[:20]}...")
            else:
                logger.warning("PoToken not found in page config.")

            if visitor_data:
                logger.info(f"Successfully retrieved Visitor Data: {visitor_data[:20]}...")
            else:
                logger.warning("Visitor Data not found in page config.")

            # Save to file
            os.makedirs(os.path.dirname(TOKEN_STORAGE_PATH), exist_ok=True)
            with open(TOKEN_STORAGE_PATH, "w") as f:
                json.dump(token_data, f, indent=2)

            logger.info(f"Tokens saved to {TOKEN_STORAGE_PATH}")

            await browser.close()
            return True

    except ImportError:
        logger.error("Playwright is not installed. Cannot refresh tokens.")
        logger.error("Please run: pip install playwright && playwright install chromium")
        return False
    except Exception as e:
        logger.error(f"Failed to refresh YouTube tokens: {str(e)}")
        return False

def _convert_cookies_to_netscape(cookies: list) -> str:
    """Convert Playwright cookies to Netscape format string"""
    netscape_lines = ["# Netscape HTTP Cookie File"]

    for cookie in cookies:
        domain = cookie.get('domain', '')
        # Initial dot for domain
        if not domain.startswith('.'):
            domain = '.' + domain

        include_subdomains = "TRUE" if domain.startswith('.') else "FALSE"
        path = cookie.get('path', '/')
        secure = "TRUE" if cookie.get('secure', False) else "FALSE"
        expires = int(cookie.get('expires', -1))
        name = cookie.get('name', '')
        value = cookie.get('value', '')

        line = f"{domain}\t{include_subdomains}\t{path}\t{secure}\t{expires}\t{name}\t{value}"
        netscape_lines.append(line)

    return "\n".join(netscape_lines)

def get_latest_tokens() -> Dict[str, Any]:
    """Retrieve the latest tokens from the storage file."""
    if not os.path.exists(TOKEN_STORAGE_PATH):
        return {}

    try:
        with open(TOKEN_STORAGE_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading token file: {e}")
        return {}
