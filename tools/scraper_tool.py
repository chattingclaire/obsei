"""
Web Scraper Tool
Uses requests, BeautifulSoup, newspaper3k, and news-please for web scraping
"""

import os
import logging
from typing import Dict, List, Optional, Any
import time
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
import newspaper
from newsplease import NewsPlease

logger = logging.getLogger(__name__)


class ScraperTool:
    """
    Web scraping tool with multiple backend engines
    """

    def __init__(
        self,
        timeout: int = 30,
        max_retries: int = 3,
        rate_limit_delay: float = 1.0,
        user_agent: Optional[str] = None
    ):
        """
        Initialize scraper tool

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            rate_limit_delay: Delay between requests in seconds
            user_agent: Custom user agent string
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.rate_limit_delay = rate_limit_delay

        self.user_agent = user_agent or os.getenv(
            "USER_AGENT",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

        logger.info("Scraper tool initialized")

    def _make_request(self, url: str, method: str = "GET", **kwargs) -> Optional[requests.Response]:
        """
        Make HTTP request with retries

        Args:
            url: Target URL
            method: HTTP method
            **kwargs: Additional requests parameters

        Returns:
            Response object or None
        """
        for attempt in range(self.max_retries):
            try:
                response = self.session.request(
                    method,
                    url,
                    timeout=self.timeout,
                    **kwargs
                )
                response.raise_for_status()

                # Rate limiting
                if self.rate_limit_delay > 0:
                    time.sleep(self.rate_limit_delay)

                return response

            except requests.RequestException as e:
                logger.warning(f"Request attempt {attempt + 1} failed for {url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"All retry attempts failed for {url}")
                    return None

    def scrape_html(self, url: str) -> Dict[str, Any]:
        """
        Scrape HTML content using BeautifulSoup

        Args:
            url: Target URL

        Returns:
            Dict with title, text, html, links, images
        """
        try:
            response = self._make_request(url)
            if not response:
                return self._empty_result(url, error="Request failed")

            soup = BeautifulSoup(response.content, "html.parser")

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Extract data
            title = soup.find("title")
            title_text = title.string if title else ""

            # Get text content
            text = soup.get_text(separator="\n", strip=True)

            # Extract links
            links = []
            for link in soup.find_all("a", href=True):
                absolute_url = urljoin(url, link["href"])
                links.append({
                    "text": link.get_text(strip=True),
                    "url": absolute_url
                })

            # Extract images
            images = []
            for img in soup.find_all("img", src=True):
                absolute_url = urljoin(url, img["src"])
                images.append({
                    "src": absolute_url,
                    "alt": img.get("alt", "")
                })

            # Extract metadata
            metadata = self._extract_metadata(soup)

            result = {
                "url": url,
                "title": title_text,
                "text": text,
                "html": str(soup),
                "links": links,
                "images": images,
                "metadata": metadata,
                "success": True
            }

            logger.debug(f"Successfully scraped {url}")
            return result

        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return self._empty_result(url, error=str(e))

    def scrape_article(self, url: str, engine: str = "newspaper") -> Dict[str, Any]:
        """
        Scrape article content using newspaper3k or news-please

        Args:
            url: Article URL
            engine: Scraping engine (newspaper or newsplease)

        Returns:
            Dict with article data
        """
        if engine == "newspaper":
            return self._scrape_with_newspaper(url)
        elif engine == "newsplease":
            return self._scrape_with_newsplease(url)
        else:
            logger.error(f"Unknown engine: {engine}")
            return self._empty_result(url, error=f"Unknown engine: {engine}")

    def _scrape_with_newspaper(self, url: str) -> Dict[str, Any]:
        """Scrape article using newspaper3k"""
        try:
            article = newspaper.Article(url)
            article.download()
            article.parse()

            # Try NLP extraction
            try:
                article.nlp()
                keywords = article.keywords
                summary = article.summary
            except:
                keywords = []
                summary = ""

            result = {
                "url": url,
                "title": article.title,
                "text": article.text,
                "authors": article.authors,
                "publish_date": article.publish_date.isoformat() if article.publish_date else None,
                "top_image": article.top_image,
                "images": list(article.images),
                "videos": list(article.movies),
                "keywords": keywords,
                "summary": summary,
                "meta_description": article.meta_description,
                "meta_keywords": article.meta_keywords,
                "success": True
            }

            logger.debug(f"Successfully scraped article: {url}")
            return result

        except Exception as e:
            logger.error(f"Error scraping article with newspaper: {e}")
            return self._empty_result(url, error=str(e))

    def _scrape_with_newsplease(self, url: str) -> Dict[str, Any]:
        """Scrape article using news-please"""
        try:
            article = NewsPlease.from_url(url)

            result = {
                "url": url,
                "title": article.title,
                "text": article.maintext,
                "authors": article.authors if article.authors else [],
                "publish_date": article.date_publish.isoformat() if article.date_publish else None,
                "source": article.source_domain,
                "description": article.description,
                "language": article.language,
                "image_url": article.image_url,
                "success": True
            }

            logger.debug(f"Successfully scraped article with news-please: {url}")
            return result

        except Exception as e:
            logger.error(f"Error scraping article with news-please: {e}")
            return self._empty_result(url, error=str(e))

    def scrape_multiple(self, urls: List[str], engine: str = "html") -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs

        Args:
            urls: List of URLs
            engine: Scraping engine (html, article_newspaper, article_newsplease)

        Returns:
            List of scrape results
        """
        results = []

        for url in urls:
            if engine == "html":
                result = self.scrape_html(url)
            elif engine == "article_newspaper":
                result = self.scrape_article(url, "newspaper")
            elif engine == "article_newsplease":
                result = self.scrape_article(url, "newsplease")
            else:
                result = self._empty_result(url, error=f"Unknown engine: {engine}")

            results.append(result)

        logger.info(f"Scraped {len(results)} URLs")
        return results

    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from HTML"""
        metadata = {}

        # Open Graph metadata
        og_tags = soup.find_all("meta", property=lambda x: x and x.startswith("og:"))
        for tag in og_tags:
            key = tag.get("property", "").replace("og:", "")
            value = tag.get("content", "")
            if key and value:
                metadata[f"og_{key}"] = value

        # Twitter Card metadata
        twitter_tags = soup.find_all("meta", attrs={"name": lambda x: x and x.startswith("twitter:")})
        for tag in twitter_tags:
            key = tag.get("name", "").replace("twitter:", "")
            value = tag.get("content", "")
            if key and value:
                metadata[f"twitter_{key}"] = value

        # Standard meta tags
        description_tag = soup.find("meta", attrs={"name": "description"})
        if description_tag:
            metadata["description"] = description_tag.get("content", "")

        keywords_tag = soup.find("meta", attrs={"name": "keywords"})
        if keywords_tag:
            metadata["keywords"] = keywords_tag.get("content", "")

        author_tag = soup.find("meta", attrs={"name": "author"})
        if author_tag:
            metadata["author"] = author_tag.get("content", "")

        return metadata

    def _empty_result(self, url: str, error: str = "") -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            "url": url,
            "title": "",
            "text": "",
            "success": False,
            "error": error
        }

    def extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        parsed = urlparse(url)
        return parsed.netloc

    def is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False


class RSSScraperTool(ScraperTool):
    """
    Specialized scraper for RSS/Atom feeds
    """

    def scrape_rss(self, feed_url: str) -> Dict[str, Any]:
        """
        Scrape RSS/Atom feed

        Args:
            feed_url: RSS feed URL

        Returns:
            Dict with feed data and entries
        """
        try:
            import feedparser

            feed = feedparser.parse(feed_url)

            entries = []
            for entry in feed.entries:
                entries.append({
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "description": entry.get("description", ""),
                    "published": entry.get("published", ""),
                    "author": entry.get("author", ""),
                    "tags": [tag.term for tag in entry.get("tags", [])]
                })

            result = {
                "feed_url": feed_url,
                "title": feed.feed.get("title", ""),
                "description": feed.feed.get("description", ""),
                "link": feed.feed.get("link", ""),
                "entries": entries,
                "entry_count": len(entries),
                "success": True
            }

            logger.info(f"Scraped RSS feed with {len(entries)} entries")
            return result

        except Exception as e:
            logger.error(f"Error scraping RSS feed: {e}")
            return {
                "feed_url": feed_url,
                "entries": [],
                "success": False,
                "error": str(e)
            }


# Convenience functions
def scrape_url(url: str, engine: str = "html") -> Dict[str, Any]:
    """
    Convenience function to scrape a URL

    Args:
        url: Target URL
        engine: Scraping engine

    Returns:
        Scrape result
    """
    scraper = ScraperTool()

    if engine == "html":
        return scraper.scrape_html(url)
    elif engine.startswith("article"):
        article_engine = engine.split("_")[1] if "_" in engine else "newspaper"
        return scraper.scrape_article(url, article_engine)
    else:
        return scraper.scrape_html(url)


def scrape_article(url: str) -> Dict[str, Any]:
    """
    Convenience function to scrape an article

    Args:
        url: Article URL

    Returns:
        Article data
    """
    scraper = ScraperTool()
    return scraper.scrape_article(url, "newspaper")
