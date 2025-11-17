"""
RSS Feed Generation Tool
Generate RSS/Atom feeds from signals using feedgen
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from feedgen.feed import FeedGenerator

logger = logging.getLogger(__name__)


class RSSTool:
    """
    RSS/Atom feed generation tool
    """

    def __init__(
        self,
        feed_title: str = "AI Intelligence Signals",
        feed_description: str = "Curated signals from multi-agent intelligence platform",
        feed_url: str = "https://your-domain.com/rss",
        feed_link: str = "https://your-domain.com",
        author_name: str = "Multi-Agent Intelligence System",
        author_email: str = "info@your-domain.com"
    ):
        """
        Initialize RSS tool

        Args:
            feed_title: Feed title
            feed_description: Feed description
            feed_url: Feed URL
            feed_link: Website link
            author_name: Author name
            author_email: Author email
        """
        self.feed_title = feed_title
        self.feed_description = feed_description
        self.feed_url = feed_url
        self.feed_link = feed_link
        self.author_name = author_name
        self.author_email = author_email

        logger.info("RSS tool initialized")

    def create_feed(self) -> FeedGenerator:
        """
        Create a new FeedGenerator instance

        Returns:
            FeedGenerator object
        """
        fg = FeedGenerator()

        # Set feed properties
        fg.title(self.feed_title)
        fg.description(self.feed_description)
        fg.link(href=self.feed_link, rel="alternate")
        fg.link(href=self.feed_url, rel="self")
        fg.language("en")
        fg.author({"name": self.author_name, "email": self.author_email})
        fg.logo(f"{self.feed_link}/logo.png")
        fg.subtitle(self.feed_description)

        # Set generator
        fg.generator("Multi-Agent Intelligence System")

        return fg

    def add_signal_to_feed(
        self,
        fg: FeedGenerator,
        signal: Dict[str, Any]
    ) -> None:
        """
        Add a signal as a feed entry

        Args:
            fg: FeedGenerator object
            signal: Signal data dict
        """
        try:
            fe = fg.add_entry()

            # Required fields
            guid = signal.get("rss_guid", signal.get("id", ""))
            fe.id(guid)

            title = signal.get("xhs_title") or signal.get("title", "Untitled")
            fe.title(title)

            link = signal.get("rss_link") or signal.get("source_url", self.feed_link)
            fe.link(href=link)

            # Content
            content = signal.get("xhs_content") or signal.get("content", "")
            summary = signal.get("summary", "")

            if content:
                fe.content(content, type="html")
            if summary:
                fe.summary(summary)

            # Published date
            pub_date = signal.get("rss_pub_date") or signal.get("published_at") or signal.get("generated_at")
            if pub_date:
                if isinstance(pub_date, str):
                    pub_date = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                fe.published(pub_date)
                fe.updated(pub_date)

            # Author
            fe.author({"name": self.author_name, "email": self.author_email})

            # Categories (from hashtags)
            hashtags = signal.get("xhs_hashtags", [])
            for tag in hashtags:
                fe.category(term=tag)

            # Media enclosure (if images available)
            images = signal.get("xhs_images", [])
            if images and len(images) > 0:
                fe.enclosure(url=images[0], type="image/jpeg")

            logger.debug(f"Added signal to feed: {title}")

        except Exception as e:
            logger.error(f"Error adding signal to feed: {e}")

    def generate_rss(
        self,
        signals: List[Dict[str, Any]],
        output_path: Optional[str] = None,
        max_items: int = 100
    ) -> str:
        """
        Generate RSS feed from signals

        Args:
            signals: List of signal dicts
            output_path: Optional path to save RSS file
            max_items: Maximum number of items in feed

        Returns:
            RSS XML string
        """
        try:
            fg = self.create_feed()

            # Add signals (most recent first)
            for signal in signals[:max_items]:
                self.add_signal_to_feed(fg, signal)

            # Generate RSS XML
            rss_str = fg.rss_str(pretty=True).decode("utf-8")

            # Save to file if path provided
            if output_path:
                fg.rss_file(output_path)
                logger.info(f"RSS feed saved to {output_path}")

            logger.info(f"Generated RSS feed with {min(len(signals), max_items)} items")
            return rss_str

        except Exception as e:
            logger.error(f"Error generating RSS feed: {e}")
            return ""

    def generate_atom(
        self,
        signals: List[Dict[str, Any]],
        output_path: Optional[str] = None,
        max_items: int = 100
    ) -> str:
        """
        Generate Atom feed from signals

        Args:
            signals: List of signal dicts
            output_path: Optional path to save Atom file
            max_items: Maximum number of items in feed

        Returns:
            Atom XML string
        """
        try:
            fg = self.create_feed()

            # Add signals
            for signal in signals[:max_items]:
                self.add_signal_to_feed(fg, signal)

            # Generate Atom XML
            atom_str = fg.atom_str(pretty=True).decode("utf-8")

            # Save to file if path provided
            if output_path:
                fg.atom_file(output_path)
                logger.info(f"Atom feed saved to {output_path}")

            logger.info(f"Generated Atom feed with {min(len(signals), max_items)} items")
            return atom_str

        except Exception as e:
            logger.error(f"Error generating Atom feed: {e}")
            return ""

    def create_category_feed(
        self,
        signals: List[Dict[str, Any]],
        category: str,
        output_path: Optional[str] = None
    ) -> str:
        """
        Create RSS feed for a specific category

        Args:
            signals: List of all signals
            category: Category to filter by
            output_path: Optional path to save RSS file

        Returns:
            RSS XML string
        """
        try:
            # Filter signals by category
            filtered_signals = [
                s for s in signals
                if category in s.get("xhs_hashtags", [])
            ]

            # Create feed with category-specific title
            fg = self.create_feed()
            fg.title(f"{self.feed_title} - {category}")
            fg.description(f"{self.feed_description} - {category}")

            # Add signals
            for signal in filtered_signals:
                self.add_signal_to_feed(fg, signal)

            # Generate RSS
            rss_str = fg.rss_str(pretty=True).decode("utf-8")

            if output_path:
                fg.rss_file(output_path)
                logger.info(f"Category RSS feed saved to {output_path}")

            logger.info(f"Generated category RSS feed with {len(filtered_signals)} items")
            return rss_str

        except Exception as e:
            logger.error(f"Error generating category RSS feed: {e}")
            return ""


class XiaohongshuFormatter:
    """
    Format signals for Xiaohongshu (Little Red Book) style
    """

    @staticmethod
    def format_signal(
        title: str,
        content: str,
        hashtags: Optional[List[str]] = None,
        max_title_length: int = 100,
        max_content_length: int = 1000
    ) -> Dict[str, Any]:
        """
        Format signal in Xiaohongshu style

        Args:
            title: Signal title
            content: Signal content
            hashtags: List of hashtags
            max_title_length: Maximum title length
            max_content_length: Maximum content length

        Returns:
            Formatted signal
        """
        # Format title
        xhs_title = title[:max_title_length]
        if len(title) > max_title_length:
            xhs_title += "..."

        # Format content
        xhs_content = content[:max_content_length]
        if len(content) > max_content_length:
            xhs_content += "..."

        # Add hashtags to content
        if hashtags:
            hashtag_str = " ".join([f"#{tag}" for tag in hashtags])
            xhs_content += f"\n\n{hashtag_str}"

        return {
            "xhs_title": xhs_title,
            "xhs_content": xhs_content,
            "xhs_hashtags": hashtags or []
        }

    @staticmethod
    def extract_hashtags(content: str, categories: Dict[str, str]) -> List[str]:
        """
        Extract and generate hashtags from content and categories

        Args:
            content: Signal content
            categories: Category labels (l1, l2, l3)

        Returns:
            List of hashtags
        """
        hashtags = []

        # Add category-based tags
        if categories.get("category_l2"):
            hashtags.append(categories["category_l2"])
        if categories.get("category_l3"):
            hashtags.append(categories["category_l3"])

        # Common AI/startup tags
        common_tags = ["AI", "Startup", "Tech", "Innovation", "Funding", "Product"]

        # Add relevant common tags
        content_lower = content.lower()
        for tag in common_tags:
            if tag.lower() in content_lower and tag not in hashtags:
                hashtags.append(tag)

        return hashtags[:5]  # Limit to 5 hashtags


# Convenience functions
def generate_rss_feed(
    signals: List[Dict[str, Any]],
    output_path: Optional[str] = None
) -> str:
    """
    Convenience function to generate RSS feed

    Args:
        signals: List of signals
        output_path: Optional path to save RSS file

    Returns:
        RSS XML string
    """
    tool = RSSTool()
    return tool.generate_rss(signals, output_path)


def format_for_xiaohongshu(
    title: str,
    content: str,
    hashtags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Convenience function to format for Xiaohongshu

    Args:
        title: Signal title
        content: Signal content
        hashtags: List of hashtags

    Returns:
        Formatted signal
    """
    formatter = XiaohongshuFormatter()
    return formatter.format_signal(title, content, hashtags)
