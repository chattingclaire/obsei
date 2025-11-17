"""
Venture Agent
Investment intelligence for Chinese/Overseas Chinese founders
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from anthropic import Anthropic

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.logger import get_agent_logger
from core.cache_manager import get_cache_manager
from core.tool_loader import get_tool_loader
from database.supabase_client import get_supabase_client

logger = get_agent_logger("venture_agent")


class VentureAgent:
    """
    Investment intelligence and founder analysis agent
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize venture agent"""
        self.config = config or {}
        self.agent_name = "venture_agent"

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

        logger.info(f"{self.agent_name} initialized")

    def _load_system_prompt(self) -> str:
        """Load system prompt"""
        try:
            with open(f"prompts/agents/{self.agent_name}.md", "r") as f:
                return f.read()
        except:
            return f"You are {self.agent_name}, analyzing investment opportunities."

    def run(self, batch_size: int = 50) -> Dict[str, Any]:
        """Run venture intelligence analysis"""
        logger.info(f"{self.agent_name} starting run...")

        self.db.update_agent_status(self.agent_name, status="running")

        stats = {"analyzed": 0, "flagged": 0, "founders_identified": 0}

        try:
            # Get classified items for analysis
            items = self.db.get_classified_items(limit=batch_size)

            for item in items:
                try:
                    # Analyze for investment potential
                    analysis = self.analyze_investment_opportunity(item)

                    if analysis and analysis.get("investability_score", 0) >= 0.7:
                        # Save investment record
                        investment = {
                            "company_name": analysis.get("company_name"),
                            "company_url": item.get("source_url"),
                            "company_description": item.get("summary"),
                            "founder_names": analysis.get("founder_names", []),
                            "founder_backgrounds": analysis.get("founder_backgrounds"),
                            "funding_stage": analysis.get("funding_stage"),
                            "funding_amount_usd": analysis.get("funding_amount"),
                            "category_l1": item.get("category_l1"),
                            "category_l2": item.get("category_l2"),
                            "category_l3": item.get("category_l3"),
                            "investability_score": analysis.get("investability_score"),
                            "scoring_factors": analysis.get("scoring_factors"),
                            "unique_insights": analysis.get("insights", []),
                            "technology_assessment": analysis.get("technology_assessment"),
                            "team_assessment": analysis.get("team_assessment")
                        }

                        self.db.insert_investment(investment)
                        stats["flagged"] += 1

                        # Extract and save founders
                        if analysis.get("founders"):
                            for founder in analysis["founders"]:
                                self.db.upsert_founder(founder)
                                stats["founders_identified"] += 1

                    stats["analyzed"] += 1

                except Exception as e:
                    logger.error(f"Error analyzing item: {e}")

            logger.info(f"{self.agent_name} completed: {stats}")

            self.db.update_agent_status(
                self.agent_name,
                status="idle",
                processed_count=stats["analyzed"],
                payload=stats
            )

            return stats

        except Exception as e:
            logger.error(f"Error in {self.agent_name}: {e}")
            self.db.update_agent_status(self.agent_name, status="error", error_message=str(e))
            raise

    def analyze_investment_opportunity(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze item for investment potential"""
        try:
            prompt = f"""
Analyze this startup/company for investment potential, focusing on Chinese/Overseas Chinese founders.

ITEM:
Title: {item.get('title')}
Summary: {item.get('summary')}
Category: {item.get('category_l1')}/{item.get('category_l2')}/{item.get('category_l3')}
Source: {item.get('source_url')}

ANALYSIS CRITERIA:
- Founder background (Chinese/Overseas Chinese priority)
- Technology innovation
- Market opportunity
- Team experience
- Traction/metrics
- Funding stage and amount

Provide analysis in JSON format:
{{
    "company_name": "Company name",
    "investability_score": 0.0-1.0,
    "founder_names": ["Founder 1", "Founder 2"],
    "founder_backgrounds": [{{"name": "...", "ethnicity": "...", "background": "..."}}],
    "founders": [{{"name": "...", "ethnicity": "...", "linkedin_url": "...", "github_url": "...", "bio": "..."}}],
    "funding_stage": "pre-seed|seed|series-a|series-b",
    "funding_amount": 0,
    "scoring_factors": {{"founder_background": 0.9, "technology": 0.8}},
    "insights": ["insight1", "insight2"],
    "technology_assessment": "Assessment text",
    "team_assessment": "Assessment text"
}}
"""

            cache_params = self.cache_manager.build_claude_cache_params(self.agent_name, prompt, self.model)

            response = self.claude.messages.create(
                model=self.model,
                max_tokens=3072,
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
            logger.error(f"Error in investment analysis: {e}")
            return None


# Main execution
def main():
    agent = VentureAgent()
    stats = agent.run()
    print(f"Venture analysis completed: {stats}")


if __name__ == "__main__":
    main()
