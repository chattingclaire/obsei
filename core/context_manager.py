"""
Global Context Manager
Manages shared context and memory across agents
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
import threading

logger = logging.getLogger(__name__)


@dataclass
class ContextEntry:
    """Single context entry"""
    key: str
    value: Any
    agent_name: str
    timestamp: str
    ttl_seconds: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None


class GlobalContextManager:
    """
    Manages global shared context across agents
    """

    def __init__(
        self,
        max_size_mb: int = 10,
        storage_backend: str = "memory"  # memory | file | supabase
    ):
        """
        Initialize context manager

        Args:
            max_size_mb: Maximum context size in MB
            storage_backend: Storage backend type
        """
        self.max_size_mb = max_size_mb
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.storage_backend = storage_backend

        # In-memory context storage
        self.context: Dict[str, ContextEntry] = {}

        # Thread lock for concurrent access
        self.lock = threading.Lock()

        # Agent-specific namespaces
        self.agent_contexts: Dict[str, Dict[str, ContextEntry]] = {}

        logger.info(f"Global context manager initialized (backend: {storage_backend})")

    def set(
        self,
        key: str,
        value: Any,
        agent_name: str,
        ttl_seconds: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Set context value

        Args:
            key: Context key
            value: Context value
            agent_name: Name of the agent setting context
            ttl_seconds: Optional TTL in seconds
            metadata: Optional metadata

        Returns:
            True if successful
        """
        with self.lock:
            try:
                entry = ContextEntry(
                    key=key,
                    value=value,
                    agent_name=agent_name,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    ttl_seconds=ttl_seconds,
                    metadata=metadata
                )

                # Check size
                entry_size = len(json.dumps(asdict(entry)))
                current_size = self._get_total_size()

                if current_size + entry_size > self.max_size_bytes:
                    logger.warning(f"Context size limit exceeded, removing old entries")
                    self._evict_old_entries()

                # Store in global context
                self.context[key] = entry

                # Store in agent-specific namespace
                if agent_name not in self.agent_contexts:
                    self.agent_contexts[agent_name] = {}

                self.agent_contexts[agent_name][key] = entry

                logger.debug(f"Set context: {key} by {agent_name}")
                return True

            except Exception as e:
                logger.error(f"Error setting context: {e}")
                return False

    def get(self, key: str, agent_name: Optional[str] = None) -> Optional[Any]:
        """
        Get context value

        Args:
            key: Context key
            agent_name: Optional agent name for namespace filtering

        Returns:
            Context value or None
        """
        with self.lock:
            # Check if expired
            entry = self.context.get(key)

            if not entry:
                return None

            if self._is_expired(entry):
                del self.context[key]
                return None

            return entry.value

    def get_all(self, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all context values

        Args:
            agent_name: Optional agent name for filtering

        Returns:
            Dict of key: value
        """
        with self.lock:
            if agent_name and agent_name in self.agent_contexts:
                # Return agent-specific context
                return {
                    k: v.value
                    for k, v in self.agent_contexts[agent_name].items()
                    if not self._is_expired(v)
                }
            else:
                # Return all context
                return {
                    k: v.value
                    for k, v in self.context.items()
                    if not self._is_expired(v)
                }

    def delete(self, key: str, agent_name: Optional[str] = None) -> bool:
        """
        Delete context entry

        Args:
            key: Context key
            agent_name: Optional agent name

        Returns:
            True if deleted
        """
        with self.lock:
            try:
                if key in self.context:
                    del self.context[key]

                if agent_name and agent_name in self.agent_contexts:
                    if key in self.agent_contexts[agent_name]:
                        del self.agent_contexts[agent_name][key]

                logger.debug(f"Deleted context: {key}")
                return True

            except Exception as e:
                logger.error(f"Error deleting context: {e}")
                return False

    def clear(self, agent_name: Optional[str] = None) -> None:
        """
        Clear context

        Args:
            agent_name: Optional agent name to clear only agent context
        """
        with self.lock:
            if agent_name:
                # Clear agent-specific context
                if agent_name in self.agent_contexts:
                    keys_to_delete = list(self.agent_contexts[agent_name].keys())

                    for key in keys_to_delete:
                        if key in self.context:
                            del self.context[key]

                    self.agent_contexts[agent_name].clear()

                logger.info(f"Cleared context for agent: {agent_name}")
            else:
                # Clear all context
                self.context.clear()
                self.agent_contexts.clear()

                logger.info("Cleared all context")

    def share_context(self, from_agent: str, to_agent: str, keys: Optional[List[str]] = None) -> int:
        """
        Share context from one agent to another

        Args:
            from_agent: Source agent name
            to_agent: Target agent name
            keys: Optional list of keys to share (None = all)

        Returns:
            Number of entries shared
        """
        with self.lock:
            if from_agent not in self.agent_contexts:
                return 0

            source_context = self.agent_contexts[from_agent]
            shared_count = 0

            for key, entry in source_context.items():
                if keys is None or key in keys:
                    # Create new entry for target agent
                    if to_agent not in self.agent_contexts:
                        self.agent_contexts[to_agent] = {}

                    self.agent_contexts[to_agent][key] = entry
                    shared_count += 1

            logger.info(f"Shared {shared_count} context entries from {from_agent} to {to_agent}")
            return shared_count

    def _is_expired(self, entry: ContextEntry) -> bool:
        """Check if context entry is expired"""
        if entry.ttl_seconds is None:
            return False

        entry_time = datetime.fromisoformat(entry.timestamp)
        now = datetime.now(timezone.utc)
        age_seconds = (now - entry_time).total_seconds()

        return age_seconds > entry.ttl_seconds

    def _get_total_size(self) -> int:
        """Get total size of context in bytes"""
        try:
            context_json = json.dumps({k: asdict(v) for k, v in self.context.items()})
            return len(context_json)
        except:
            return 0

    def _evict_old_entries(self, target_percent: float = 0.8) -> None:
        """Evict old entries to free up space"""
        # Sort by timestamp
        sorted_entries = sorted(
            self.context.items(),
            key=lambda x: x[1].timestamp
        )

        # Calculate target size
        target_size = int(self.max_size_bytes * target_percent)

        # Remove oldest entries until under target
        current_size = self._get_total_size()
        removed_count = 0

        for key, entry in sorted_entries:
            if current_size <= target_size:
                break

            del self.context[key]

            # Also remove from agent contexts
            agent_name = entry.agent_name
            if agent_name in self.agent_contexts:
                if key in self.agent_contexts[agent_name]:
                    del self.agent_contexts[agent_name][key]

            removed_count += 1
            current_size = self._get_total_size()

        logger.info(f"Evicted {removed_count} old context entries")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get context statistics

        Returns:
            Dict with stats
        """
        with self.lock:
            return {
                "total_entries": len(self.context),
                "total_size_bytes": self._get_total_size(),
                "max_size_bytes": self.max_size_bytes,
                "utilization_percent": (self._get_total_size() / self.max_size_bytes) * 100,
                "agent_count": len(self.agent_contexts),
                "agents": {
                    agent: len(ctx)
                    for agent, ctx in self.agent_contexts.items()
                }
            }

    def save_to_file(self, filepath: str) -> bool:
        """
        Save context to file

        Args:
            filepath: Path to save file

        Returns:
            True if successful
        """
        with self.lock:
            try:
                context_data = {
                    k: asdict(v)
                    for k, v in self.context.items()
                }

                with open(filepath, "w") as f:
                    json.dump(context_data, f, indent=2)

                logger.info(f"Saved context to {filepath}")
                return True

            except Exception as e:
                logger.error(f"Error saving context: {e}")
                return False

    def load_from_file(self, filepath: str) -> bool:
        """
        Load context from file

        Args:
            filepath: Path to load file

        Returns:
            True if successful
        """
        with self.lock:
            try:
                with open(filepath, "r") as f:
                    context_data = json.load(f)

                # Reconstruct context entries
                for key, entry_dict in context_data.items():
                    entry = ContextEntry(**entry_dict)
                    self.context[key] = entry

                    # Rebuild agent contexts
                    agent_name = entry.agent_name
                    if agent_name not in self.agent_contexts:
                        self.agent_contexts[agent_name] = {}
                    self.agent_contexts[agent_name][key] = entry

                logger.info(f"Loaded context from {filepath}")
                return True

            except Exception as e:
                logger.error(f"Error loading context: {e}")
                return False


# Singleton instance
_context_manager: Optional[GlobalContextManager] = None


def get_context_manager(
    max_size_mb: int = 10,
    storage_backend: str = "memory"
) -> GlobalContextManager:
    """
    Get or create singleton context manager

    Args:
        max_size_mb: Maximum context size in MB
        storage_backend: Storage backend type

    Returns:
        GlobalContextManager instance
    """
    global _context_manager

    if _context_manager is None:
        _context_manager = GlobalContextManager(max_size_mb, storage_backend)

    return _context_manager
