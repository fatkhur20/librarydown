from playwright.async_api import async_playwright, Browser, Page
import asyncio
import os
from src.core.config import settings

class SessionManager:
    def __init__(self, headless=settings.HEADLESS_MODE, proxy_url=None):
        self._playwright = None
        self._browser = None
        self.headless = headless
        self.proxy_url = proxy_url
        self._pages_queue = asyncio.Queue(maxsize=settings.SESSION_POOL_SIZE)

    async def start(self):
        self._playwright = await async_playwright().start()
        proxy_config = {"server": self.proxy_url} if self.proxy_url else None
        
        browser_args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu'
        ]

        env = {
            **os.environ,
            'DEBUG': "pw:browser*,pw:api*"
        }

        launch_options = {
            "headless": self.headless,
            "proxy": proxy_config,
            "args": browser_args,
            "env": env,
            "slow_mo": 50,
            # --- LAST RESORT FOR HANGING ISSUES ---
            # These options prevent the Python script from managing the browser's lifecycle
            # via OS signals. This can resolve hangs in unusual environments where
            # process I/O or signal handling is unstable.
            "handle_sigint": False,
            "handle_sigterm": False,
            "handle_sighup": False,
        }

        if settings.CHROMIUM_EXECUTABLE_PATH:
            launch_options["executable_path"] = settings.CHROMIUM_EXECUTABLE_PATH
        else:
            print("Warning: CHROMIUM_EXECUTABLE_PATH not set. Playwright will use its own browser.")
        
        print(f"--- Launching Browser ---")
        print(f"  Mode: {'Headless' if self.headless else 'Headed'}")
        print(f"  Executable: {launch_options.get('executable_path', 'Playwright Default')}")
        print(f"  Args: {browser_args}")
        print("-------------------------")

        self._browser = await self._playwright.chromium.launch(**launch_options)
        
        for _ in range(settings.SESSION_POOL_SIZE):
            page = await self._browser.new_page()
            await self._pages_queue.put(page)

    async def get_page(self) -> Page:
        return await self._pages_queue.get()

    async def release_page(self, page: Page):
        try:
            await page.goto("about:blank")
        except Exception:
            try:
                await page.close()
            except Exception:
                pass
            page = await self._browser.new_page()

        await self._pages_queue.put(page)


    async def stop(self):
        if self._browser:
            while not self._pages_queue.empty():
                page = await self._pages_queue.get()
                await page.close()
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

session_manager = SessionManager(proxy_url=settings.PROXY_URL)
