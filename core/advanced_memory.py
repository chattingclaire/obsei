"""
Advanced Memory Management System
Combines Mem0 (long-term semantic memory) and Zep (session memory with auto-summarization)
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class AdvancedMemoryManager:
    """
    Unified memory management combining:
    - Mem0: Long-term semantic memory with vector search
    - Zep: Session memory with automatic summarization
    """

    def __init__(self, agent_name: str):
        """
        Initialize advanced memory manager

        Args:
            agent_name: Name of the agent
        """
        self.agent_name = agent_name
        self.mem0 = None
        self.zep = None

        # Initialize Mem0 (long-term memory)
        try:
            from mem0 import Memory

            mem0_config = {
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "host": os.getenv("QDRANT_HOST", "localhost"),
                        "port": int(os.getenv("QDRANT_PORT", 6333)),
                        "collection_name": f"{agent_name}_memory"
                    }
                },
                "llm": {
                    "provider": "anthropic",
                    "config": {
                        "model": os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514"),
                        "api_key": os.getenv("CLAUDE_API_KEY")
                    }
                }
            }

            self.mem0 = Memory.from_config(mem0_config)
            logger.info(f"Mem0 initialized for {agent_name}")

        except ImportError:
            logger.warning("Mem0 not installed. Install with: pip install mem0ai")
            self.mem0 = None
        except Exception as e:
            logger.error(f"Error initializing Mem0: {e}")
            self.mem0 = None

        # Initialize Zep (session memory)
        try:
            from zep_python import ZepClient

            zep_url = os.getenv("ZEP_API_URL", "http://localhost:8000")
            self.zep = ZepClient(base_url=zep_url)
            logger.info(f"Zep initialized for {agent_name}")

        except ImportError:
            logger.warning("Zep not installed. Install with: pip install zep-python")
            self.zep = None
        except Exception as e:
            logger.error(f"Error initializing Zep: {e}")
            self.zep = None

    def add_conversation(
        self,
        user_message: str,
        assistant_message: str,
        session_id: str,
        user_id: str,
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        Add conversation to both memory systems

        Args:
            user_message: User's message
            assistant_message: Assistant's response
            session_id: Session identifier
            user_id: User identifier
            metadata: Optional metadata

        Returns:
            True if successful
        """
        success = True

        # Add to Zep (session memory)
        if self.zep:
            try:
                from zep_python.memory import Message

                self.zep.memory.add_memory(
                    session_id=session_id,
                    messages=[
                        Message(
                            role="user",
                            content=user_message,
                            metadata=metadata or {}
                        ),
                        Message(
                            role="assistant",
                            content=assistant_message,
                            metadata={
                                "agent": self.agent_name,
                                **(metadata or {})
                            }
                        )
                    ]
                )
                logger.debug(f"Added conversation to Zep: session={session_id}")

            except Exception as e:
                logger.error(f"Error adding to Zep: {e}")
                success = False

        # Add to Mem0 (long-term memory) if important
        if self.mem0:
            try:
                importance = self._calculate_importance(user_message, assistant_message)

                if importance > 0.7:
                    self.mem0.add(
                        assistant_message,
                        user_id=user_id,
                        agent_id=self.agent_name,
                        metadata={
                            "importance": importance,
                            "session_id": session_id,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            **(metadata or {})
                        }
                    )
                    logger.debug(f"Added to Mem0: importance={importance:.2f}")

            except Exception as e:
                logger.error(f"Error adding to Mem0: {e}")
                success = False

        return success

    def retrieve_context(
        self,
        query: str,
        session_id: str,
        user_id: str,
        include_long_term: bool = True
    ) -> Dict[str, Any]:
        """
        Retrieve relevant context from both memory systems

        Args:
            query: Search query
            session_id: Session identifier
            user_id: User identifier
            include_long_term: Whether to include long-term memories

        Returns:
            Dictionary containing all relevant context
        """
        context = {
            "session_summary": "",
            "recent_messages": [],
            "relevant_history": [],
            "long_term_memories": []
        }

        # Retrieve from Zep (session memory)
        if self.zep:
            try:
                # Get session memory
                session_memory = self.zep.memory.get_memory(session_id=session_id)

                if session_memory:
                    # Session summary
                    if hasattr(session_memory, 'summary') and session_memory.summary:
                        context["session_summary"] = session_memory.summary.content

                    # Recent messages
                    if hasattr(session_memory, 'messages') and session_memory.messages:
                        context["recent_messages"] = [
                            {
                                "role": msg.role,
                                "content": msg.content,
                                "metadata": getattr(msg, 'metadata', {})
                            }
                            for msg in session_memory.messages[-10:]
                        ]

                # Semantic search in session history
                try:
                    search_results = self.zep.memory.search_memory(
                        session_id=session_id,
                        search_query=query,
                        limit=5
                    )

                    if search_results:
                        context["relevant_history"] = [
                            {
                                "content": r.message.content if hasattr(r, 'message') else str(r),
                                "score": getattr(r, 'score', 0.0)
                            }
                            for r in search_results
                        ]

                except Exception as e:
                    logger.debug(f"Zep search not available: {e}")

            except Exception as e:
                logger.error(f"Error retrieving from Zep: {e}")

        # Retrieve from Mem0 (long-term memory)
        if self.mem0 and include_long_term:
            try:
                search_results = self.mem0.search(
                    query,
                    user_id=user_id,
                    agent_id=self.agent_name,
                    limit=5
                )

                if search_results and isinstance(search_results, dict):
                    results = search_results.get("results", [])
                    context["long_term_memories"] = [
                        {
                            "memory": mem.get("memory", ""),
                            "metadata": mem.get("metadata", {}),
                            "id": mem.get("id", "")
                        }
                        for mem in results
                    ]

            except Exception as e:
                logger.error(f"Error retrieving from Mem0: {e}")

        return context

    def create_session(self, session_id: str, user_id: str, metadata: Optional[Dict] = None) -> bool:
        """
        Create a new session in Zep

        Args:
            session_id: Session identifier
            user_id: User identifier
            metadata: Optional session metadata

        Returns:
            True if successful
        """
        if not self.zep:
            return False

        try:
            from zep_python.user import CreateUserRequest
            from zep_python.memory import Session

            # Ensure user exists
            try:
                self.zep.user.add(
                    user_id=user_id,
                    metadata=metadata or {}
                )
            except Exception as e:
                # User might already exist
                logger.debug(f"User might already exist: {e}")

            # Create session
            session = Session(
                session_id=session_id,
                user_id=user_id,
                metadata=metadata or {}
            )

            self.zep.memory.add_session(session)
            logger.info(f"Created session: {session_id}")
            return True

        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return False

    def get_session_summary(self, session_id: str) -> Optional[str]:
        """
        Get auto-generated summary of session

        Args:
            session_id: Session identifier

        Returns:
            Summary text or None
        """
        if not self.zep:
            return None

        try:
            memory = self.zep.memory.get_memory(session_id=session_id)
            if memory and hasattr(memory, 'summary') and memory.summary:
                return memory.summary.content
        except Exception as e:
            logger.error(f"Error getting session summary: {e}")

        return None

    def clear_session(self, session_id: str) -> bool:
        """
        Clear session memory

        Args:
            session_id: Session identifier

        Returns:
            True if successful
        """
        if not self.zep:
            return False

        try:
            self.zep.memory.delete_memory(session_id=session_id)
            logger.info(f"Cleared session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing session: {e}")
            return False

    def add_user_memory(self, content: str, user_id: str, metadata: Optional[Dict] = None) -> bool:
        """
        Add a user-specific long-term memory

        Args:
            content: Memory content
            user_id: User identifier
            metadata: Optional metadata

        Returns:
            True if successful
        """
        if not self.mem0:
            return False

        try:
            self.mem0.add(
                content,
                user_id=user_id,
                agent_id=self.agent_name,
                metadata=metadata or {}
            )
            logger.debug(f"Added user memory for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding user memory: {e}")
            return False

    def get_user_memories(self, user_id: str, limit: int = 10) -> List[Dict]:
        """
        Get all memories for a user

        Args:
            user_id: User identifier
            limit: Maximum number of memories

        Returns:
            List of memory dictionaries
        """
        if not self.mem0:
            return []

        try:
            result = self.mem0.get_all(
                user_id=user_id,
                agent_id=self.agent_name,
                limit=limit
            )

            if result and isinstance(result, dict):
                return result.get("results", [])

        except Exception as e:
            logger.error(f"Error getting user memories: {e}")

        return []

    def _calculate_importance(self, user_msg: str, assistant_msg: str) -> float:
        """
        Calculate importance score for a conversation

        Args:
            user_msg: User message
            assistant_msg: Assistant message

        Returns:
            Importance score (0.0 to 1.0)
        """
        # Simple heuristic-based importance calculation
        importance_keywords = [
            "重要", "记住", "偏好", "喜欢", "不喜欢", "总是", "从不",
            "important", "remember", "preference", "always", "never",
            "like", "dislike", "favorite"
        ]

        score = 0.5  # Base score

        combined_text = (user_msg + " " + assistant_msg).lower()

        # Increase score for importance keywords
        for keyword in importance_keywords:
            if keyword in combined_text:
                score += 0.1

        # Increase score for longer, detailed responses
        if len(assistant_msg) > 500:
            score += 0.1

        # Cap at 1.0
        return min(score, 1.0)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory system statistics

        Returns:
            Dictionary with stats
        """
        stats = {
            "agent_name": self.agent_name,
            "mem0_enabled": self.mem0 is not None,
            "zep_enabled": self.zep is not None
        }

        # Check Zep connection
        if self.zep:
            try:
                # Simple health check
                self.zep.memory.get_memory(session_id="healthcheck")
                stats["zep_status"] = "connected"
            except:
                stats["zep_status"] = "disconnected"

        # Mem0 doesn't have a simple health check
        if self.mem0:
            stats["mem0_status"] = "enabled"

        return stats

    def is_ready(self) -> bool:
        """
        Check if memory systems are ready

        Returns:
            True if at least one system is available
        """
        return self.mem0 is not None or self.zep is not None


# Global registry of memory managers
_memory_managers: Dict[str, AdvancedMemoryManager] = {}


def get_advanced_memory_manager(agent_name: str) -> AdvancedMemoryManager:
    """
    Get or create advanced memory manager for agent

    Args:
        agent_name: Name of the agent

    Returns:
        AdvancedMemoryManager instance
    """
    global _memory_managers

    if agent_name not in _memory_managers:
        _memory_managers[agent_name] = AdvancedMemoryManager(agent_name)

    return _memory_managers[agent_name]
