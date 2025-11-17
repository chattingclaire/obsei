"""
Insight Agent with Chat Interface
Conversational interface for generating insights and analysis
"""

import os
import sys
from typing import Dict, List, Optional, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent_chat_interface import AgentChatInterface
from agents.insight_agent import InsightAgent
from core.advanced_memory import get_advanced_memory_manager


class InsightAgentChat(AgentChatInterface):
    """
    Insight Agent with conversational interface
    """

    def __init__(self):
        # Load system prompt
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config", "prompts", "insight_agent_prompt.md"
        )
        try:
            with open(prompt_path, "r") as f:
                system_prompt = f.read()
        except FileNotFoundError:
            system_prompt = "You are an Insight Agent that analyzes trends and patterns in startup data."

        super().__init__("insight_agent", system_prompt)

        # Initialize insight agent
        self.insight_agent = InsightAgent()

        # Initialize advanced memory system (Mem0 + Zep)
        self.memory = get_advanced_memory_manager("insight_agent")

    def process_user_request(
        self,
        user_message: str,
        user_id: str = "default_user",
        session_id: Optional[str] = None,
        auto_query_kb: bool = True
    ) -> Dict[str, Any]:
        """
        Process user request for insights with advanced memory

        Args:
            user_message: User's message
            user_id: User identifier
            session_id: Session identifier
            auto_query_kb: Automatically query knowledge base

        Returns:
            Response with insights and analysis
        """
        # Generate session ID if not provided
        if not session_id:
            import uuid
            session_id = f"insight_session_{uuid.uuid4().hex[:8]}"

        # Ensure session exists
        self.memory.create_session(session_id, user_id, metadata={"agent": "insight_agent"})

        context = {}

        # Retrieve context from memory systems
        memory_context = self.memory.retrieve_context(
            query=user_message,
            session_id=session_id,
            user_id=user_id,
            include_long_term=True
        )

        # Query knowledge base
        if auto_query_kb:
            kb_results = self.query_knowledge_base(
                query=user_message,
                limit=20
            )
            context["knowledge_base"] = kb_results

            # Add statistics
            context["stats"] = self.db.get_pipeline_metrics()
            context["category_distribution"] = self.db.get_category_distribution()

        # Add memory context
        context["memory"] = memory_context

        # Get response
        response = self.chat(user_message, context=context)

        # Save to memory
        self.memory.add_conversation(
            user_message=user_message,
            assistant_message=response.get("message", ""),
            session_id=session_id,
            user_id=user_id,
            metadata={"kb_query": auto_query_kb}
        )

        # Check if user wants custom analysis
        if "分析" in user_message or "analysis" in user_message.lower():
            analysis_type = self._extract_analysis_type(user_message)
            custom_analysis = self._generate_custom_analysis(analysis_type, context)
            response["custom_analysis"] = custom_analysis

        response["session_id"] = session_id
        return response

    def _extract_analysis_type(self, message: str) -> str:
        """Extract type of analysis requested"""
        if "趋势" in message or "trend" in message.lower():
            return "trend_analysis"
        elif "类别" in message or "category" in message.lower():
            return "category_analysis"
        elif "创始人" in message or "founder" in message.lower():
            return "founder_analysis"
        else:
            return "general_analysis"

    def _generate_custom_analysis(
        self,
        analysis_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate custom analysis based on type"""
        analysis = {
            "type": analysis_type,
            "timestamp": self.db.get_pipeline_metrics().get("timestamp"),
            "insights": []
        }

        if analysis_type == "trend_analysis":
            # Analyze trends from knowledge base
            kb = context.get("knowledge_base", {})
            items = kb.get("classified_items", [])

            # Group by category
            category_counts = {}
            for item in items:
                cat = f"{item.get('category_l1')}/{item.get('category_l2')}"
                category_counts[cat] = category_counts.get(cat, 0) + 1

            analysis["insights"].append({
                "title": "分类分布",
                "data": category_counts,
                "top_categories": sorted(
                    category_counts.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            })

        elif analysis_type == "category_analysis":
            dist = context.get("category_distribution", {})
            analysis["insights"].append({
                "title": "类别详细分析",
                "data": dist,
                "total_categories": len(dist)
            })

        return analysis


# Convenience function
def chat_with_insight_agent(message: str) -> Dict[str, Any]:
    """Convenience function to chat with insight agent"""
    agent = InsightAgentChat()
    return agent.process_user_request(message)
