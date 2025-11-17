"""
Data Agent
Multi-source data ingestion from GitHub, Twitter/X, Reddit, ProductHunt, etc.
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import asyncio

# API clients
import tweepy
import praw
from github import Github
import yt_dlp

# Local imports
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import get_agent_logger
from core.tool_loader import get_tool_loader
from core.memory_store import get_memory_store
from database.supabase_client import get_supabase_client

logger = get_agent_logger("data_agent")


class DataAgent:
    """
    Multi-source data ingestion agent
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize data agent

        Args:
            config: Agent configuration
        """
        self.config = config or {}
        self.agent_name = "data_agent"

        # Initialize tools
        tool_loader = get_tool_loader()
        self.tools = tool_loader.get_tools_for_agent(self.agent_name)

        # Initialize database client
        self.db = get_supabase_client()

        # Initialize memory
        self.memory = get_memory_store(self.agent_name)

        # Load system prompt
        self.system_prompt = self._load_system_prompt()

        # API clients
        self._init_api_clients()

        logger.info(f"{self.agent_name} initialized")

    def _load_system_prompt(self) -> str:
        """Load system prompt from markdown file"""
        try:
            with open(f"prompts/agents/{self.agent_name}.md", "r") as f:
                return f.read()
        except:
            return f"You are {self.agent_name}, responsible for multi-source data ingestion."

    def _init_api_clients(self):
        """Initialize API clients for various sources"""
        # Twitter
        try:
            self.twitter_client = tweepy.Client(
                bearer_token=os.getenv("TWITTER_BEARER_TOKEN")
            )
        except:
            self.twitter_client = None
            logger.warning("Twitter client not initialized")

        # Reddit
        try:
            self.reddit_client = praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID"),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                user_agent=os.getenv("REDDIT_USER_AGENT", "multi-agent-bot/1.0")
            )
        except:
            self.reddit_client = None
            logger.warning("Reddit client not initialized")

        # GitHub
        try:
            self.github_client = Github(os.getenv("GITHUB_TOKEN"))
        except:
            self.github_client = None
            logger.warning("GitHub client not initialized")

    async def run(self) -> Dict[str, Any]:
        """
        Run data ingestion from all sources

        Returns:
            Dict with run statistics
        """
        logger.info(f"{self.agent_name} starting run...")

        # Update agent status
        self.db.update_agent_status(
            self.agent_name,
            status="running",
            payload={"run_started_at": datetime.now(timezone.utc).isoformat()}
        )

        stats = {
            "github": 0,
            "twitter": 0,
            "reddit": 0,
            "producthunt": 0,
            "youtube": 0,
            "techcrunch": 0,
            "total": 0
        }

        try:
            # Run all ingestion tasks concurrently
            tasks = [
                self.ingest_github(),
                self.ingest_twitter(),
                self.ingest_reddit(),
                self.ingest_youtube(),
                self.ingest_techcrunch()
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Aggregate stats
            for i, result in enumerate(results):
                if isinstance(result, dict):
                    source = ["github", "twitter", "reddit", "youtube", "techcrunch"][i]
                    count = result.get("count", 0)
                    stats[source] = count
                    stats["total"] += count

            logger.info(f"{self.agent_name} completed: {stats['total']} items ingested")

            # Update agent status
            self.db.update_agent_status(
                self.agent_name,
                status="idle",
                processed_count=stats["total"],
                payload=stats
            )

            return stats

        except Exception as e:
            logger.error(f"Error in {self.agent_name}: {e}")
            self.db.update_agent_status(
                self.agent_name,
                status="error",
                error_message=str(e)
            )
            raise

    async def ingest_github(self) -> Dict[str, Any]:
        """Ingest data from GitHub"""
        try:
            if not self.github_client:
                return {"count": 0}

            logger.info("Ingesting from GitHub...")

            items = []
            topics = ["artificial-intelligence", "machine-learning", "web3", "cryptocurrency"]

            for topic in topics:
                query = f"topic:{topic} stars:>100"
                repos = self.github_client.search_repositories(
                    query=query,
                    sort="stars",
                    order="desc"
                )

                for repo in repos[:20]:  # Limit per topic
                    item = {
                        "source": "github",
                        "source_id": str(repo.id),
                        "source_url": repo.html_url,
                        "title": repo.name,
                        "description": repo.description,
                        "author": repo.owner.login,
                        "author_url": repo.owner.html_url,
                        "published_at": repo.created_at.isoformat() if repo.created_at else None,
                        "metadata": {
                            "stars": repo.stargazers_count,
                            "forks": repo.forks_count,
                            "language": repo.language,
                            "topics": repo.get_topics()
                        },
                        "raw_data": {
                            "full_name": repo.full_name,
                            "watchers": repo.watchers_count
                        }
                    }
                    items.append(item)

            # Bulk insert to database
            if items:
                self.db.bulk_insert_raw_items(items)
                logger.info(f"Ingested {len(items)} items from GitHub")

            return {"count": len(items)}

        except Exception as e:
            logger.error(f"Error ingesting from GitHub: {e}")
            return {"count": 0, "error": str(e)}

    async def ingest_twitter(self) -> Dict[str, Any]:
        """Ingest data from Twitter/X"""
        try:
            if not self.twitter_client:
                return {"count": 0}

            logger.info("Ingesting from Twitter...")

            items = []
            keywords = ["AI startup", "web3", "YC", "funding"]

            for keyword in keywords:
                tweets = self.twitter_client.search_recent_tweets(
                    query=keyword,
                    max_results=25,
                    tweet_fields=["created_at", "author_id", "public_metrics"]
                )

                if tweets.data:
                    for tweet in tweets.data:
                        item = {
                            "source": "twitter",
                            "source_id": str(tweet.id),
                            "source_url": f"https://twitter.com/i/web/status/{tweet.id}",
                            "title": tweet.text[:100],
                            "description": tweet.text,
                            "content": tweet.text,
                            "published_at": tweet.created_at.isoformat() if tweet.created_at else None,
                            "metadata": {
                                "author_id": str(tweet.author_id),
                                "metrics": getattr(tweet, "public_metrics", {})
                            }
                        }
                        items.append(item)

            if items:
                self.db.bulk_insert_raw_items(items)
                logger.info(f"Ingested {len(items)} items from Twitter")

            return {"count": len(items)}

        except Exception as e:
            logger.error(f"Error ingesting from Twitter: {e}")
            return {"count": 0, "error": str(e)}

    async def ingest_reddit(self) -> Dict[str, Any]:
        """Ingest data from Reddit"""
        try:
            if not self.reddit_client:
                return {"count": 0}

            logger.info("Ingesting from Reddit...")

            items = []
            subreddits = ["startups", "MachineLearning", "CryptoCurrency"]

            for subreddit_name in subreddits:
                subreddit = self.reddit_client.subreddit(subreddit_name)

                for post in subreddit.hot(limit=20):
                    item = {
                        "source": "reddit",
                        "source_id": post.id,
                        "source_url": f"https://reddit.com{post.permalink}",
                        "title": post.title,
                        "description": post.selftext[:500],
                        "content": post.selftext,
                        "author": str(post.author),
                        "published_at": datetime.fromtimestamp(post.created_utc, tz=timezone.utc).isoformat(),
                        "metadata": {
                            "subreddit": subreddit_name,
                            "score": post.score,
                            "num_comments": post.num_comments
                        }
                    }
                    items.append(item)

            if items:
                self.db.bulk_insert_raw_items(items)
                logger.info(f"Ingested {len(items)} items from Reddit")

            return {"count": len(items)}

        except Exception as e:
            logger.error(f"Error ingesting from Reddit: {e}")
            return {"count": 0, "error": str(e)}

    async def ingest_youtube(self) -> Dict[str, Any]:
        """Ingest data from YouTube"""
        try:
            logger.info("Ingesting from YouTube...")

            items = []
            channels = ["YCombinator", "TechCrunch"]

            for channel in channels:
                # Use video tool to get channel videos
                if "video_tool" in self.tools:
                    # In production, implement YouTube channel search
                    # For now, return empty
                    pass

            return {"count": len(items)}

        except Exception as e:
            logger.error(f"Error ingesting from YouTube: {e}")
            return {"count": 0, "error": str(e)}

    async def ingest_techcrunch(self) -> Dict[str, Any]:
        """Ingest data from TechCrunch"""
        try:
            logger.info("Ingesting from TechCrunch...")

            items = []

            # Use scraper tool
            if "scraper_tool" in self.tools:
                scraper = self.tools["scraper_tool"]

                # TechCrunch RSS feed
                from tools.scraper_tool import RSSScraperTool
                rss_scraper = RSSScraperTool()

                feed_url = "https://techcrunch.com/feed/"
                result = rss_scraper.scrape_rss(feed_url)

                if result.get("success"):
                    for entry in result.get("entries", [])[:30]:
                        item = {
                            "source": "techcrunch",
                            "source_id": entry.get("link"),
                            "source_url": entry.get("link"),
                            "title": entry.get("title"),
                            "description": entry.get("description"),
                            "author": entry.get("author"),
                            "published_at": entry.get("published"),
                            "metadata": {
                                "tags": entry.get("tags", [])
                            }
                        }
                        items.append(item)

            if items:
                self.db.bulk_insert_raw_items(items)
                logger.info(f"Ingested {len(items)} items from TechCrunch")

            return {"count": len(items)}

        except Exception as e:
            logger.error(f"Error ingesting from TechCrunch: {e}")
            return {"count": 0, "error": str(e)}


# Main execution
async def main():
    """Main execution function"""
    agent = DataAgent()
    stats = await agent.run()
    print(f"Data ingestion completed: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
