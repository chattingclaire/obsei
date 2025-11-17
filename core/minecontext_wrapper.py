"""
MineContext Wrapper
Integrates minecontext-style context management for enhanced memory and context engineering
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import json

logger = logging.getLogger(__name__)


class MineContextManager:
    """
    Advanced context manager inspired by minecontext
    Provides hierarchical context, relevance scoring, and intelligent retrieval
    """

    def __init__(self, agent_name: str, db_client=None):
        """
        Initialize MineContext manager

        Args:
            agent_name: Name of the agent
            db_client: Database client for persistence
        """
        self.agent_name = agent_name
        self.db = db_client

        # Context layers
        self.immediate_context = []  # Current conversation
        self.session_context = []  # Current session
        self.long_term_context = []  # Cross-session knowledge

        # Context embeddings (in production, use actual embeddings)
        self.context_index = {}

        logger.info(f"MineContext initialized for {agent_name}")

    def add_context(
        self,
        content: str,
        context_type: str = "conversation",
        metadata: Optional[Dict[str, Any]] = None,
        relevance_score: float = 1.0
    ) -> str:
        """
        Add context with automatic layering

        Args:
            content: Context content
            context_type: Type of context (conversation, knowledge, task)
            metadata: Optional metadata
            relevance_score: Relevance score (0-1)

        Returns:
            Context ID
        """
        context_id = self._generate_context_id()

        context_entry = {
            "id": context_id,
            "content": content,
            "type": context_type,
            "metadata": metadata or {},
            "relevance_score": relevance_score,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "agent_name": self.agent_name,
            "access_count": 0
        }

        # Add to appropriate layer
        if context_type == "conversation":
            self.immediate_context.append(context_entry)
            # Keep only recent conversation
            if len(self.immediate_context) > 20:
                self.immediate_context.pop(0)

        elif context_type == "session":
            self.session_context.append(context_entry)

        elif context_type == "knowledge":
            self.long_term_context.append(context_entry)
            # Persist to database
            if self.db:
                self._persist_context(context_entry)

        # Update index
        self.context_index[context_id] = context_entry

        return context_id

    def retrieve_relevant_context(
        self,
        query: str,
        max_contexts: int = 5,
        context_types: Optional[List[str]] = None,
        min_relevance: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context based on query

        Args:
            query: Query string
            max_contexts: Maximum contexts to return
            context_types: Filter by context types
            min_relevance: Minimum relevance score

        Returns:
            List of relevant contexts
        """
        # In production, use embeddings and vector search
        # For now, use simple keyword matching

        all_contexts = (
            self.immediate_context +
            self.session_context +
            self.long_term_context
        )

        # Filter by type if specified
        if context_types:
            all_contexts = [
                c for c in all_contexts
                if c["type"] in context_types
            ]

        # Simple relevance scoring (replace with embeddings in production)
        scored_contexts = []
        query_lower = query.lower()

        for context in all_contexts:
            content_lower = context["content"].lower()

            # Simple keyword matching
            score = 0.0
            query_words = set(query_lower.split())
            content_words = set(content_lower.split())
            common_words = query_words & content_words

            if common_words:
                score = len(common_words) / len(query_words)

            # Boost by stored relevance score
            score = (score + context["relevance_score"]) / 2

            if score >= min_relevance:
                context["computed_relevance"] = score
                scored_contexts.append(context)

        # Sort by relevance
        scored_contexts.sort(key=lambda x: x["computed_relevance"], reverse=True)

        # Update access count
        for context in scored_contexts[:max_contexts]:
            context["access_count"] += 1

        return scored_contexts[:max_contexts]

    def get_context_summary(self, window_size: int = 10) -> str:
        """
        Get a summary of recent context

        Args:
            window_size: Number of recent contexts to include

        Returns:
            Context summary string
        """
        recent = self.immediate_context[-window_size:]

        summary_parts = []
        for context in recent:
            summary_parts.append(
                f"[{context['type']}] {context['content'][:100]}"
            )

        return "\n".join(summary_parts)

    def add_knowledge_from_db(
        self,
        knowledge_items: List[Dict[str, Any]],
        knowledge_type: str = "classified_item"
    ):
        """
        Add knowledge from database query results

        Args:
            knowledge_items: List of knowledge items from database
            knowledge_type: Type of knowledge (classified_item, signal, etc.)
        """
        for item in knowledge_items:
            # Extract relevant content
            if knowledge_type == "classified_item":
                content = f"{item.get('title')}: {item.get('summary', '')}"
                metadata = {
                    "category": f"{item.get('category_l1')}/{item.get('category_l2')}/{item.get('category_l3')}",
                    "source": item.get("source"),
                    "confidence": item.get("confidence")
                }

            elif knowledge_type == "signal":
                content = f"Signal: {item.get('title')} - {item.get('summary', '')}"
                metadata = {
                    "signal_type": item.get("signal_type"),
                    "score": item.get("signal_score")
                }

            elif knowledge_type == "founder":
                content = f"Founder: {item.get('name')} - {item.get('bio', '')}"
                metadata = {
                    "ethnicity": item.get("ethnicity"),
                    "github": item.get("github_url")
                }

            else:
                content = str(item)
                metadata = {}

            self.add_context(
                content=content,
                context_type="knowledge",
                metadata=metadata,
                relevance_score=0.8
            )

    def build_context_for_prompt(
        self,
        user_query: str,
        include_conversation: bool = True,
        include_knowledge: bool = True,
        max_length: int = 4000
    ) -> str:
        """
        Build context string for LLM prompt

        Args:
            user_query: User's current query
            include_conversation: Include conversation history
            include_knowledge: Include relevant knowledge
            max_length: Maximum context length in chars

        Returns:
            Formatted context string
        """
        context_parts = []

        # Add relevant knowledge
        if include_knowledge:
            relevant = self.retrieve_relevant_context(
                user_query,
                max_contexts=5,
                context_types=["knowledge", "session"]
            )

            if relevant:
                context_parts.append("=== 相关知识库信息 ===")
                for ctx in relevant:
                    context_parts.append(ctx["content"])
                    if ctx["metadata"]:
                        context_parts.append(f"元数据: {json.dumps(ctx['metadata'], ensure_ascii=False)}")
                context_parts.append("")

        # Add conversation history
        if include_conversation and self.immediate_context:
            context_parts.append("=== 对话历史 ===")
            for ctx in self.immediate_context[-5:]:  # Last 5
                context_parts.append(f"{ctx['type']}: {ctx['content']}")
            context_parts.append("")

        # Join and truncate
        full_context = "\n".join(context_parts)

        if len(full_context) > max_length:
            # Truncate from the middle, keep most recent
            full_context = full_context[-max_length:]

        return full_context

    def clear_session_context(self):
        """Clear session context"""
        self.session_context = []
        logger.info(f"Session context cleared for {self.agent_name}")

    def _generate_context_id(self) -> str:
        """Generate unique context ID"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        return f"{self.agent_name}_ctx_{timestamp}"

    def _persist_context(self, context_entry: Dict[str, Any]):
        """Persist context to database"""
        # In production, save to a contexts table in Supabase
        # For now, log it
        if self.db:
            try:
                self.db.log_agent_activity(
                    agent_name=self.agent_name,
                    log_level="INFO",
                    message="Context stored",
                    operation="context_persist",
                    metadata=context_entry
                )
            except Exception as e:
                logger.error(f"Error persisting context: {e}")


# Convenience function
def get_mine_context_manager(agent_name: str, db_client=None) -> MineContextManager:
    """Get MineContext manager for agent"""
    return MineContextManager(agent_name, db_client)
