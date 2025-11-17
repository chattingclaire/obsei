"""
Browser Automation Tool
Supports both Playwright and Browserless for headless browser operations
"""

import os
import logging
from typing import Dict, List, Optional, Any
import asyncio
from enum import Enum

import aiohttp
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

logger = logging.getLogger(__name__)


class BrowserProvider(Enum):
    """Supported browser automation providers"""
    PLAYWRIGHT = "playwright"
    BROWSERLESS = "browserless"


class BrowserTool:
    """
    Browser automation tool with support for Playwright and Browserless
    """

    def __init__(
        self,
        provider: BrowserProvider = BrowserProvider.PLAYWRIGHT,
        headless: bool = True,
        timeout: int = 30000,
        viewport: Optional[Dict[str, int]] = None
    ):
        """
        Initialize browser tool

        Args:
            provider: Browser provider (playwright or browserless)
            headless: Run in headless mode
            timeout: Default timeout in milliseconds
            viewport: Viewport size {width, height}
        """
        self.provider = provider
        self.headless = headless
        self.timeout = timeout
        self.viewport = viewport or {"width": 1920, "height": 1080}

        # Browserless configuration
        self.browserless_url = os.getenv("BROWSERLESS_URL", "https://chrome.browserless.io")
        self.browserless_api_key = os.getenv("BROWSERLESS_API_KEY")

        # Playwright browser instance
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

        logger.info(f"Browser tool initialized with provider: {provider.value}")

    async def __aenter__(self):
        """Async context manager entry"""
        if self.provider == BrowserProvider.PLAYWRIGHT:
            await self._init_playwright()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    async def _init_playwright(self):
        """Initialize Playwright browser"""
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(headless=self.headless)
            self.context = await self.browser.new_context(
                viewport=self.viewport,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            logger.info("Playwright browser initialized")
        except Exception as e:
            logger.error(f"Error initializing Playwright: {e}")
            raise

    async def navigate(self, url: str, wait_until: str = "networkidle") -> Dict[str, Any]:
        """
        Navigate to a URL and return page content

        Args:
            url: Target URL
            wait_until: Wait condition (load, domcontentloaded, networkidle)

        Returns:
            Dict with html, text, title, url
        """
        if self.provider == BrowserProvider.PLAYWRIGHT:
            return await self._navigate_playwright(url, wait_until)
        else:
            return await self._navigate_browserless(url)

    async def _navigate_playwright(self, url: str, wait_until: str) -> Dict[str, Any]:
        """Navigate using Playwright"""
        try:
            page = await self.context.new_page()
            await page.goto(url, wait_until=wait_until, timeout=self.timeout)

            # Extract content
            html = await page.content()
            text = await page.inner_text("body")
            title = await page.title()

            result = {
                "html": html,
                "text": text,
                "title": title,
                "url": page.url,
                "success": True
            }

            await page.close()
            logger.debug(f"Successfully navigated to {url}")
            return result

        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return {
                "html": "",
                "text": "",
                "title": "",
                "url": url,
                "success": False,
                "error": str(e)
            }

    async def _navigate_browserless(self, url: str) -> Dict[str, Any]:
        """Navigate using Browserless API"""
        try:
            if not self.browserless_api_key:
                raise ValueError("BROWSERLESS_API_KEY not set")

            endpoint = f"{self.browserless_url}/content"
            params = {
                "token": self.browserless_api_key
            }

            payload = {
                "url": url,
                "waitFor": self.timeout
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, json=payload, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "html": data.get("html", ""),
                            "text": data.get("text", ""),
                            "title": data.get("title", ""),
                            "url": url,
                            "success": True
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"Browserless error: {error_text}")
                        return {
                            "html": "",
                            "text": "",
                            "title": "",
                            "url": url,
                            "success": False,
                            "error": error_text
                        }

        except Exception as e:
            logger.error(f"Error with Browserless: {e}")
            return {
                "html": "",
                "text": "",
                "title": "",
                "url": url,
                "success": False,
                "error": str(e)
            }

    async def search(self, query: str, engine: str = "google") -> List[Dict[str, Any]]:
        """
        Perform a web search and return results

        Args:
            query: Search query
            engine: Search engine (google, bing, duckduckgo)

        Returns:
            List of search results
        """
        search_urls = {
            "google": f"https://www.google.com/search?q={query}",
            "bing": f"https://www.bing.com/search?q={query}",
            "duckduckgo": f"https://duckduckgo.com/?q={query}"
        }

        url = search_urls.get(engine, search_urls["google"])

        if self.provider == BrowserProvider.PLAYWRIGHT:
            return await self._search_playwright(url)
        else:
            # For simplicity, just navigate and extract
            result = await self.navigate(url)
            return [{"title": result["title"], "text": result["text"][:500], "url": url}]

    async def _search_playwright(self, url: str) -> List[Dict[str, Any]]:
        """Perform search using Playwright and extract results"""
        try:
            page = await self.context.new_page()
            await page.goto(url, wait_until="networkidle", timeout=self.timeout)

            # Extract search results (Google-specific selectors)
            results = []
            result_elements = await page.query_selector_all("div.g")

            for element in result_elements[:10]:  # Top 10 results
                try:
                    title_elem = await element.query_selector("h3")
                    link_elem = await element.query_selector("a")
                    snippet_elem = await element.query_selector("div.VwiC3b")

                    title = await title_elem.inner_text() if title_elem else ""
                    link = await link_elem.get_attribute("href") if link_elem else ""
                    snippet = await snippet_elem.inner_text() if snippet_elem else ""

                    if title and link:
                        results.append({
                            "title": title,
                            "url": link,
                            "snippet": snippet
                        })
                except Exception as e:
                    logger.debug(f"Error extracting result element: {e}")
                    continue

            await page.close()
            logger.info(f"Extracted {len(results)} search results")
            return results

        except Exception as e:
            logger.error(f"Error performing search: {e}")
            return []

    async def screenshot(self, url: str, full_page: bool = False) -> Optional[bytes]:
        """
        Take a screenshot of a page

        Args:
            url: Target URL
            full_page: Capture full page or just viewport

        Returns:
            Screenshot as bytes
        """
        if self.provider == BrowserProvider.PLAYWRIGHT:
            return await self._screenshot_playwright(url, full_page)
        else:
            return await self._screenshot_browserless(url, full_page)

    async def _screenshot_playwright(self, url: str, full_page: bool) -> Optional[bytes]:
        """Take screenshot using Playwright"""
        try:
            page = await self.context.new_page()
            await page.goto(url, wait_until="networkidle", timeout=self.timeout)

            screenshot = await page.screenshot(full_page=full_page)
            await page.close()

            logger.info(f"Screenshot captured for {url}")
            return screenshot

        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None

    async def _screenshot_browserless(self, url: str, full_page: bool) -> Optional[bytes]:
        """Take screenshot using Browserless"""
        try:
            if not self.browserless_api_key:
                raise ValueError("BROWSERLESS_API_KEY not set")

            endpoint = f"{self.browserless_url}/screenshot"
            params = {
                "token": self.browserless_api_key
            }

            payload = {
                "url": url,
                "options": {
                    "fullPage": full_page,
                    "type": "png"
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, json=payload, params=params) as response:
                    if response.status == 200:
                        screenshot = await response.read()
                        logger.info(f"Screenshot captured for {url}")
                        return screenshot
                    else:
                        error_text = await response.text()
                        logger.error(f"Screenshot error: {error_text}")
                        return None

        except Exception as e:
            logger.error(f"Error with Browserless screenshot: {e}")
            return None

    async def extract_links(self, url: str) -> List[str]:
        """Extract all links from a page"""
        if self.provider == BrowserProvider.PLAYWRIGHT:
            try:
                page = await self.context.new_page()
                await page.goto(url, wait_until="networkidle", timeout=self.timeout)

                links = await page.eval_on_selector_all("a[href]", "elements => elements.map(e => e.href)")
                await page.close()

                logger.info(f"Extracted {len(links)} links from {url}")
                return links

            except Exception as e:
                logger.error(f"Error extracting links: {e}")
                return []
        else:
            # For Browserless, use navigate and parse HTML
            result = await self.navigate(url)
            # Simple parsing - in production, use BeautifulSoup
            return []

    async def close(self):
        """Close browser and cleanup"""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")


# Convenience function
async def browse_url(url: str, provider: str = "playwright") -> Dict[str, Any]:
    """
    Convenience function to browse a URL

    Args:
        url: Target URL
        provider: Browser provider (playwright or browserless)

    Returns:
        Page content
    """
    provider_enum = BrowserProvider(provider)

    async with BrowserTool(provider=provider_enum) as browser:
        return await browser.navigate(url)


# Sync wrapper for compatibility
def browse_url_sync(url: str, provider: str = "playwright") -> Dict[str, Any]:
    """Synchronous wrapper for browse_url"""
    return asyncio.run(browse_url(url, provider))
