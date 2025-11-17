"""
Signal Agent
Converts classified items to Xiaohongshu signals with lightweight enrichment
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import asyncio

from anthropic import Anthropic

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import get_agent_logger
from core.tool_loader import get_tool_loader
from core.cache_manager import get_cache_manager
from database.supabase_client import get_supabase_client
from tools.rss_tool import XiaohongshuFormatter

logger = get_agent_logger("signal_agent")


class SignalAgent:
    """
    Signal generation and enrichment agent
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize signal agent"""
        self.config = config or {}
        self.agent_name = "signal_agent"

        # Initialize Claude client
        self.claude = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
        self.model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")

        # Initialize tools
        tool_loader = get_tool_loader()
        self.tools = tool_loader.get_tools_for_agent(self.agent_name)

        # Initialize cache
        self.cache_manager = get_cache_manager()

        # Initialize database
        self.db = get_supabase_client()

        # Load system prompt
        self.system_prompt = self._load_system_prompt()

        # Xiaohongshu formatter
        self.xhs_formatter = XiaohongshuFormatter()

        logger.info(f"{self.agent_name} initialized")

    def _load_system_prompt(self) -> str:
        """Load system prompt"""
        try:
            with open(f"prompts/agents/{self.agent_name}.md", "r") as f:
                return f.read()
        except:
            return f"You are {self.agent_name}, generating signals from classified items."

    async def run(self, batch_size: int = 30) -> Dict[str, Any]:
        """Run signal generation"""
        logger.info(f"{self.agent_name} starting run...")

        self.db.update_agent_status(self.agent_name, status="running")

        stats = {"generated": 0, "enriched": 0, "errors": 0}

        try:
            # Get recent classified items
            classified_items = self.db.get_recent_classified_items(hours=24, limit=batch_size)

            for item in classified_items:
                try:
                    # Generate signal
                    signal = await self.generate_signal(item)

                    if signal:
                        self.db.insert_signal(signal)
                        stats["generated"] += 1

                except Exception as e:
                    logger.error(f"Error generating signal: {e}")
                    stats["errors"] += 1

            logger.info(f"{self.agent_name} completed: {stats}")

            self.db.update_agent_status(
                self.agent_name,
                status="idle",
                processed_count=stats["generated"],
                payload=stats
            )

            return stats

        except Exception as e:
            logger.error(f"Error in {self.agent_name}: {e}")
            self.db.update_agent_status(self.agent_name, status="error", error_message=str(e))
            raise

    async def generate_signal(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate signal from classified item"""
        try:
            # Enrich with external data
            enrichment = await self.enrich_item(item)

            # Generate signal content with Claude
            signal_content = self.generate_signal_content(item, enrichment)

            if not signal_content:
                return None

            # Format for Xiaohongshu
            xhs_data = self.xhs_formatter.format_signal(
                title=signal_content.get("title", ""),
                content=signal_content.get("content", ""),
                hashtags=signal_content.get("hashtags", [])
            )

            # Build signal record
            signal = {
                "classified_item_id": item["id"],
                "title": signal_content.get("title"),
                "content": signal_content.get("content"),
                "summary": signal_content.get("summary"),
                "xhs_title": xhs_data["xhs_title"],
                "xhs_content": xhs_data["xhs_content"],
                "xhs_hashtags": xhs_data["xhs_hashtags"],
                "rss_guid": item["id"],
                "rss_link": item.get("source_url"),
                "rss_pub_date": datetime.now(timezone.utc).isoformat(),
                "verified_info": enrichment,
                "signal_score": signal_content.get("score", 0.5),
                "signal_type": signal_content.get("type", "general")
            }

            return signal

        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return None

    async def enrich_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Lightweight enrichment using browser/scraper tools"""
        enrichment = {}

        try:
            source_url = item.get("source_url", "")

            # GitHub-specific enrichment
            if "github.com" in source_url and "github_tool" in self.tools:
                # Extract owner/repo from URL
                parts = source_url.split("/")
                if len(parts) >= 5:
                    owner, repo = parts[3], parts[4]
                    github = self.tools["github_tool"]
                    repo_data = github.get_repository(owner, repo)
                    if repo_data:
                        enrichment["github"] = repo_data

            # Browser search for verification
            if "browser_tool" in self.tools:
                # Lightweight search
                title = item.get("title", "")
                # In production, perform targeted search
                pass

            return enrichment

        except Exception as e:
            logger.error(f"Error in enrichment: {e}")
            return {}

    def generate_signal_content(self, item: Dict[str, Any], enrichment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate signal content with Claude"""
        try:
            prompt = f"""
Generate a Xiaohongshu-style signal from this classified item.

ITEM:
Title: {item.get('title')}
Summary: {item.get('summary')}
Category: {item.get('category_l1')}/{item.get('category_l2')}/{item.get('category_l3')}

ENRICHMENT DATA:
{json.dumps(enrichment, indent=2)}

Provide signal in JSON format:
{{
    "title": "Engaging title (max 100 chars)",
    "content": "Signal content (max 1000 chars)",
    "summary": "Brief summary",
    "hashtags": ["tag1", "tag2"],
    "score": 0.0-1.0,
    "type": "trending|funding|launch|general"
}}
"""

            cache_params = self.cache_manager.build_claude_cache_params(self.agent_name, prompt, self.model)

            response = self.claude.messages.create(
                model=self.model,
                max_tokens=2048,
                system=self.system_prompt,
                messages=[{"role": "user", "content": prompt}],
                **cache_params
            )

            # Parse response
            response_text = response.content[0].text
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1

            if start_idx >= 0:
                return json.loads(response_text[start_idx:end_idx])

            return None

        except Exception as e:
            logger.error(f"Error generating signal content: {e}")
            return None


# Main execution
async def main():
    agent = SignalAgent()
    stats = await agent.run()
    print(f"Signal generation completed: {stats}")


if __name__ == "__main__":
    asyncio.run(main())
