"""
Venture Agent with Chat Interface
Conversational interface for investment analysis and founder research
"""

import os
import sys
from typing import Dict, List, Optional, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent_chat_interface import AgentChatInterface
from agents.venture_agent import VentureAgent


class VentureAgentChat(AgentChatInterface):
    """
    Venture Agent with conversational interface
    """

    def __init__(self):
        # Load system prompt
        with open("prompts/agents/venture_agent.md", "r") as f:
            system_prompt = f.read()

        super().__init__("venture_agent", system_prompt)

        # Initialize venture agent
        self.venture_agent = VentureAgent()

    def process_user_request(
        self,
        user_message: str,
        auto_query_kb: bool = True
    ) -> Dict[str, Any]:
        """
        Process user request for investment analysis

        Args:
            user_message: User's message
            auto_query_kb: Automatically query knowledge base

        Returns:
            Response with investment analysis
        """
        context = {}

        # Query knowledge base
        if auto_query_kb:
            # Query for investment opportunities
            kb_results = self.query_knowledge_base(
                query=user_message,
                limit=15
            )
            context["knowledge_base"] = kb_results

            # Add high-score investments
            investments = self.db.get_high_score_investments(min_score=0.7, limit=20)
            context["high_score_investments"] = investments

            # Add founder data
            founders = self.db.search_founders(
                ethnicity="Chinese" if "中国" in user_message or "Chinese" in user_message else None
            )
            context["founders"] = founders[:10]

        # Get response
        response = self.chat(user_message, context=context)

        # Check for specific requests
        if "分析" in user_message or "analyze" in user_message.lower():
            # Extract company/founder name
            entity = self._extract_entity(user_message)

            if entity:
                analysis = self._analyze_entity(entity, context)
                response["entity_analysis"] = analysis

        if "推荐" in user_message or "recommend" in user_message.lower():
            recommendations = self._generate_recommendations(user_message, context)
            response["recommendations"] = recommendations

        return response

    def _extract_entity(self, message: str) -> Optional[str]:
        """Extract company or founder name from message"""
        # Simple extraction - in production use NER
        # For now, return None and let LLM handle it
        return None

    def _analyze_entity(
        self,
        entity: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze specific company or founder"""
        analysis = {
            "entity": entity,
            "type": "unknown",
            "data": {},
            "investment_potential": {}
        }

        # Search in knowledge base
        kb = context.get("knowledge_base", {})

        # Check if it's in classified items
        items = kb.get("classified_items", [])
        matching_items = [
            item for item in items
            if entity.lower() in item.get("title", "").lower()
        ]

        if matching_items:
            analysis["type"] = "company"
            analysis["data"] = matching_items[0]

        # Check founders
        founders = context.get("founders", [])
        matching_founders = [
            f for f in founders
            if entity.lower() in f.get("name", "").lower()
        ]

        if matching_founders:
            analysis["type"] = "founder"
            analysis["data"] = matching_founders[0]

        return analysis

    def _generate_recommendations(
        self,
        message: str,
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate investment recommendations"""
        recommendations = []

        # Get high-score investments
        investments = context.get("high_score_investments", [])

        # Filter based on message context
        if "AI" in message or "人工智能" in message:
            investments = [
                inv for inv in investments
                if inv.get("category_l1") == "TECH" and inv.get("category_l2") == "AI_ML"
            ]

        if "web3" in message.lower() or "区块链" in message:
            investments = [
                inv for inv in investments
                if inv.get("category_l2") == "WEB3"
            ]

        if "中国" in message or "Chinese" in message:
            # Already filtered by founder background in query

            pass

        # Top 5 recommendations
        for inv in investments[:5]:
            recommendations.append({
                "company_name": inv.get("company_name"),
                "score": inv.get("investability_score"),
                "category": f"{inv.get('category_l1')}/{inv.get('category_l2')}/{inv.get('category_l3')}",
                "funding_stage": inv.get("funding_stage"),
                "key_insights": inv.get("unique_insights", [])[:3],
                "founder_background": inv.get("founder_backgrounds", [])
            })

        return recommendations


# Convenience function
def chat_with_venture_agent(message: str) -> Dict[str, Any]:
    """Convenience function to chat with venture agent"""
    agent = VentureAgentChat()
    return agent.process_user_request(message)
