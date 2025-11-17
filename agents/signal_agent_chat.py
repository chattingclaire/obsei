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
from core.advanced_memory import get_advanced_memory_manager


class SignalAgentChat(AgentChatInterface):
    """
    Signal Agent with conversational interface
    """

    def __init__(self):
        # Load system prompt
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config", "prompts", "signal_agent_prompt.md"
        )
        try:
            with open(prompt_path, "r") as f:
                system_prompt = f.read()
        except FileNotFoundError:
            system_prompt = "You are a Signal Agent that generates insights and signals from startup data."

        super().__init__("signal_agent", system_prompt)

        # Initialize signal agent for background tasks
        self.signal_agent = SignalAgent()

        # Initialize advanced memory system (Mem0 + Zep)
        self.memory = get_advanced_memory_manager("signal_agent")

    async def process_user_request(
        self,
        user_message: str,
        user_id: str = "default_user",
        session_id: Optional[str] = None,
        auto_query_kb: bool = True
    ) -> Dict[str, Any]:
        """
        Process user request with knowledge base integration and advanced memory

        Args:
            user_message: User's message
            user_id: User identifier
            session_id: Session identifier (generated if not provided)
            auto_query_kb: Automatically query knowledge base

        Returns:
            Response with message and any generated signals
        """
        # Generate session ID if not provided
        if not session_id:
            import uuid
            session_id = f"signal_session_{uuid.uuid4().hex[:8]}"

        # Ensure session exists in Zep
        self.memory.create_session(session_id, user_id, metadata={"agent": "signal_agent"})

        context = {}

        # 1. Retrieve context from advanced memory system
        memory_context = self.memory.retrieve_context(
            query=user_message,
            session_id=session_id,
            user_id=user_id,
            include_long_term=True
        )

        # 2. Auto-query knowledge base if enabled
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

        # 3. Combine all context
        context["memory"] = memory_context

        # 4. Get response from Claude
        response = self.chat(user_message, context=context)

        # 5. Save conversation to memory systems
        self.memory.add_conversation(
            user_message=user_message,
            assistant_message=response.get("message", ""),
            session_id=session_id,
            user_id=user_id,
            metadata={
                "kb_results_count": len(context.get("knowledge_base", {}).get("classified_items", [])),
                "has_memory": bool(memory_context.get("long_term_memories"))
            }
        )

        # 6. Check if user wants to generate signals
        if "生成信号" in user_message or "generate signal" in user_message.lower():
            # Extract parameters from conversation
            params = self._extract_signal_params(user_message)

            # Generate signals based on conversation
            if params.get("item_ids"):
                signals = await self._generate_signals_for_items(params["item_ids"])
                response["generated_signals"] = signals

        # 7. Add session info to response
        response["session_id"] = session_id
        response["memory_stats"] = self.memory.get_stats()

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
