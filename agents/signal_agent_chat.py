"""
Signal Agent with Chat Interface
Conversational interface for generating and exploring signals
"""

import os
import sys
from typing import Dict, List, Optional, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.agent_chat_interface import AgentChatInterface
from agents.signal_agent import SignalAgent


class SignalAgentChat(AgentChatInterface):
    """
    Signal Agent with conversational interface
    """

    def __init__(self):
        # Load system prompt
        with open("prompts/agents/signal_agent.md", "r") as f:
            system_prompt = f.read()

        super().__init__("signal_agent", system_prompt)

        # Initialize signal agent for background tasks
        self.signal_agent = SignalAgent()

    async def process_user_request(
        self,
        user_message: str,
        auto_query_kb: bool = True
    ) -> Dict[str, Any]:
        """
        Process user request with knowledge base integration

        Args:
            user_message: User's message
            auto_query_kb: Automatically query knowledge base

        Returns:
            Response with message and any generated signals
        """
        context = {}

        # Auto-query knowledge base if enabled
        if auto_query_kb:
            # Extract intent and keywords from message
            intent = self._extract_intent(user_message)

            if intent.get("needs_kb_query"):
                kb_results = self.query_knowledge_base(
                    query=user_message,
                    categories=intent.get("categories"),
                    limit=10
                )
                context["knowledge_base"] = kb_results

        # Get response
        response = self.chat(user_message, context=context)

        # Check if user wants to generate signals
        if "生成信号" in user_message or "generate signal" in user_message.lower():
            # Extract parameters from conversation
            params = self._extract_signal_params(user_message)

            # Generate signals based on conversation
            if params.get("item_ids"):
                signals = await self._generate_signals_for_items(params["item_ids"])
                response["generated_signals"] = signals

        return response

    def _extract_intent(self, message: str) -> Dict[str, Any]:
        """Extract user intent from message"""
        intent = {
            "needs_kb_query": False,
            "categories": None,
            "action": None
        }

        # Simple keyword-based intent detection
        # In production, use LLM for intent classification

        query_keywords = ["查询", "搜索", "找", "有哪些", "query", "search", "find"]
        if any(kw in message.lower() for kw in query_keywords):
            intent["needs_kb_query"] = True

        # Category detection
        if "AI" in message or "人工智能" in message:
            intent["categories"] = ["TECH"]

        if "web3" in message.lower() or "区块链" in message:
            intent["categories"] = ["TECH"]

        return intent

    def _extract_signal_params(self, message: str) -> Dict[str, Any]:
        """Extract signal generation parameters"""
        params = {
            "item_ids": [],
            "signal_type": "general",
            "min_score": 0.5
        }

        # In production, use LLM to extract structured params
        return params

    async def _generate_signals_for_items(self, item_ids: List[str]) -> List[Dict[str, Any]]:
        """Generate signals for specific items"""
        signals = []

        for item_id in item_ids:
            # Get classified item
            items = self.db.get_classified_items(limit=100)
            item = next((i for i in items if i["id"] == item_id), None)

            if item:
                signal = await self.signal_agent.generate_signal(item)
                if signal:
                    signals.append(signal)

        return signals


# Convenience function
async def chat_with_signal_agent(message: str) -> Dict[str, Any]:
    """Convenience function to chat with signal agent"""
    agent = SignalAgentChat()
    return await agent.process_user_request(message)
