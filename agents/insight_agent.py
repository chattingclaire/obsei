"""
Insight Agent
Generates weekly USD-fund style long-form insights
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta

from anthropic import Anthropic

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import get_agent_logger
from core.cache_manager import get_cache_manager
from database.supabase_client import get_supabase_client

logger = get_agent_logger("insight_agent")


class InsightAgent:
    """
    Long-form insight generation agent
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize insight agent"""
        self.config = config or {}
        self.agent_name = "insight_agent"

        # Initialize Claude client
        self.claude = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
        self.model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")

        # Initialize cache
        self.cache_manager = get_cache_manager()

        # Initialize database
        self.db = get_supabase_client()

        # Load system prompt
        self.system_prompt = self._load_system_prompt()

        logger.info(f"{self.agent_name} initialized")

    def _load_system_prompt(self) -> str:
        """Load system prompt"""
        try:
            with open(f"prompts/agents/{self.agent_name}.md", "r") as f:
                return f.read()
        except:
            return f"You are {self.agent_name}, generating investment insights."

    def run(self, lookback_days: int = 7) -> Dict[str, Any]:
        """Run weekly insight generation"""
        logger.info(f"{self.agent_name} starting weekly insight generation...")

        self.db.update_agent_status(self.agent_name, status="running")

        try:
            # Get data for analysis
            period_end = datetime.now(timezone.utc)
            period_start = period_end - timedelta(days=lookback_days)

            # Fetch signals and classified items from the period
            signals = self._get_period_signals(period_start, period_end)
            classified_items = self._get_period_classified_items(period_start, period_end)

            # Generate insight
            insight = self.generate_insight(signals, classified_items, period_start, period_end)

            if insight:
                # Save insight
                insight_record = {
                    "title": insight.get("title"),
                    "subtitle": insight.get("subtitle"),
                    "insight_type": "weekly",
                    "content": insight.get("content"),
                    "executive_summary": insight.get("executive_summary"),
                    "key_findings": insight.get("key_findings"),
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat(),
                    "items_analyzed": len(signals) + len(classified_items),
                    "trending_topics": insight.get("trending_topics", []),
                    "emerging_patterns": insight.get("emerging_patterns"),
                    "investment_themes": insight.get("investment_themes")
                }

                self.db.insert_insight(insight_record)

                logger.info(f"{self.agent_name} generated weekly insight")

                self.db.update_agent_status(
                    self.agent_name,
                    status="idle",
                    processed_count=1
                )

                return {"success": True, "insight_id": insight_record.get("id")}

        except Exception as e:
            logger.error(f"Error in {self.agent_name}: {e}")
            self.db.update_agent_status(self.agent_name, status="error", error_message=str(e))
            raise

    def _get_period_signals(self, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        """Get signals from period"""
        # In production, query Supabase with date range
        # For now, return empty
        return []

    def _get_period_classified_items(self, start: datetime, end: datetime) -> List[Dict[str, Any]]:
        """Get classified items from period"""
        # In production, query Supabase with date range
        return self.db.get_classified_items(limit=100)

    def generate_insight(
        self,
        signals: List[Dict[str, Any]],
        classified_items: List[Dict[str, Any]],
        period_start: datetime,
        period_end: datetime
    ) -> Optional[Dict[str, Any]]:
        """Generate insight using Claude"""
        try:
            # Prepare data summary
            data_summary = self._summarize_data(signals, classified_items)

            prompt = f"""
Generate a weekly USD-fund style investment insight report.

PERIOD: {period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}

DATA SUMMARY:
{json.dumps(data_summary, indent=2)}

Provide insight in JSON format:
{{
    "title": "Weekly Insight: [Theme]",
    "subtitle": "Subtitle",
    "executive_summary": "3-5 sentence summary",
    "content": "Full markdown content (500-1000 words)",
    "key_findings": ["finding1", "finding2", "finding3"],
    "trending_topics": ["topic1", "topic2"],
    "emerging_patterns": {{"pattern1": "description"}},
    "investment_themes": ["theme1", "theme2"]
}}
"""

            cache_params = self.cache_manager.build_claude_cache_params(self.agent_name, prompt, self.model)

            response = self.claude.messages.create(
                model=self.model,
                max_tokens=4096,
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
            logger.error(f"Error generating insight: {e}")
            return None

    def _summarize_data(self, signals: List[Dict[str, Any]], classified_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize data for analysis"""
        # Category distribution
        category_counts = {}
        for item in classified_items:
            cat = f"{item.get('category_l1')}/{item.get('category_l2')}"
            category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            "total_signals": len(signals),
            "total_items": len(classified_items),
            "category_distribution": category_counts,
            "top_categories": sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        }


# Main execution
def main():
    agent = InsightAgent()
    result = agent.run(lookback_days=7)
    print(f"Insight generation completed: {result}")


if __name__ == "__main__":
    main()
