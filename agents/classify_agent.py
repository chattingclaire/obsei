"""
Classification Agent
Classifies items using Claude SDK with 3-layer taxonomy
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
from core.memory_store import get_memory_store
from database.supabase_client import get_supabase_client

logger = get_agent_logger("classify_agent")


class ClassifyAgent:
    """
    Classification agent using Claude SDK
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize classification agent

        Args:
            config: Agent configuration
        """
        self.config = config or {}
        self.agent_name = "classify_agent"

        # Initialize Claude client
        self.claude = Anthropic(api_key=os.getenv("CLAUDE_API_KEY"))
        self.model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5-20250929")

        # Initialize cache manager
        self.cache_manager = get_cache_manager()

        # Initialize database client
        self.db = get_supabase_client()

        # Initialize memory
        self.memory = get_memory_store(self.agent_name)

        # Load taxonomy
        self.taxonomy = self._load_taxonomy()

        # Load system prompt
        self.system_prompt = self._load_system_prompt()

        logger.info(f"{self.agent_name} initialized")

    def _load_taxonomy(self) -> Dict[str, Any]:
        """Load classification taxonomy"""
        try:
            with open("config/taxonomy.json", "r") as f:
                return json.load(f)
        except:
            return {}

    def _load_system_prompt(self) -> str:
        """Load system prompt from markdown file"""
        try:
            with open(f"prompts/agents/{self.agent_name}.md", "r") as f:
                return f.read()
        except:
            return f"You are {self.agent_name}, responsible for classifying content into categories."

    def run(self, batch_size: int = 50) -> Dict[str, Any]:
        """
        Run classification on unprocessed items

        Args:
            batch_size: Number of items to process

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
            "processed": 0,
            "classified": 0,
            "errors": 0
        }

        try:
            # Get unprocessed raw items
            raw_items = self.db.get_unprocessed_raw_items(limit=batch_size)

            for item in raw_items:
                try:
                    # Classify item
                    classification = self.classify_item(item)

                    if classification:
                        # Insert classified item
                        classified_item = {
                            "raw_item_id": item["id"],
                            "category_l1": classification.get("category_l1"),
                            "category_l2": classification.get("category_l2"),
                            "category_l3": classification.get("category_l3"),
                            "categories": classification.get("all_categories"),
                            "confidence": classification.get("confidence"),
                            "title": item.get("title"),
                            "summary": classification.get("summary"),
                            "keywords": classification.get("keywords", []),
                            "source": item.get("source"),
                            "source_url": item.get("source_url"),
                            "published_at": item.get("published_at"),
                            "classification_metadata": classification.get("metadata"),
                            "classifier_version": "1.0.0"
                        }

                        self.db.insert_classified_item(classified_item)
                        stats["classified"] += 1

                        # Mark raw item as processed
                        self.db.mark_raw_item_processed(item["id"])

                    stats["processed"] += 1

                except Exception as e:
                    logger.error(f"Error classifying item {item.get('id')}: {e}")
                    stats["errors"] += 1

            logger.info(f"{self.agent_name} completed: {stats['classified']} items classified")

            # Update agent status
            self.db.update_agent_status(
                self.agent_name,
                status="idle",
                processed_count=stats["classified"],
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

    def classify_item(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Classify a single item using Claude

        Args:
            item: Raw item data

        Returns:
            Classification result
        """
        try:
            # Build classification prompt
            prompt = self._build_classification_prompt(item)

            # Get cache parameters
            cache_params = self.cache_manager.build_claude_cache_params(
                self.agent_name,
                prompt,
                self.model
            )

            # Call Claude API
            response = self.claude.messages.create(
                model=self.model,
                max_tokens=2048,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                **cache_params
            )

            # Parse response
            classification = self._parse_classification_response(response.content[0].text)

            return classification

        except Exception as e:
            logger.error(f"Error in Claude API call: {e}")
            return None

    def _build_classification_prompt(self, item: Dict[str, Any]) -> str:
        """Build classification prompt"""
        title = item.get("title", "")
        description = item.get("description", "")
        content = item.get("content", "")

        taxonomy_str = json.dumps(self.taxonomy, indent=2)

        prompt = f"""
Classify the following content into the appropriate categories from the taxonomy.

TAXONOMY:
{taxonomy_str}

CONTENT TO CLASSIFY:
Title: {title}
Description: {description}
Content: {content[:1000]}

Provide classification in JSON format:
{{
    "category_l1": "...",
    "category_l2": "...",
    "category_l3": "...",
    "confidence": 0.0-1.0,
    "summary": "Brief summary",
    "keywords": ["keyword1", "keyword2"],
    "all_categories": [
        {{"l1": "...", "l2": "...", "l3": "...", "confidence": 0.9}}
    ]
}}
"""
        return prompt

    def _parse_classification_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Claude's classification response"""
        try:
            # Extract JSON from response
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1

            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return {}

        except Exception as e:
            logger.error(f"Error parsing classification response: {e}")
            return {}


# Main execution
def main():
    """Main execution function"""
    agent = ClassifyAgent()
    stats = agent.run(batch_size=50)
    print(f"Classification completed: {stats}")


if __name__ == "__main__":
    main()
