"""
Memory Store for Agents
Provides short-term and long-term memory capabilities
"""

import os
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass, asdict
from collections import deque
import threading

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """Single memory entry"""
    id: str
    content: Any
    memory_type: str  # short_term | long_term
    agent_name: str
    timestamp: str
    importance: float = 0.5  # 0.0 to 1.0
    access_count: int = 0
    last_accessed: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class MemoryStore:
    """
    Memory storage for agents with short-term and long-term memory
    """

    def __init__(
        self,
        agent_name: str,
        short_term_max_items: int = 100,
        long_term_max_items: int = 1000,
        short_term_ttl_hours: int = 24,
        long_term_ttl_days: int = 30,
        storage_path: Optional[str] = None
    ):
        """
        Initialize memory store

        Args:
            agent_name: Name of the agent
            short_term_max_items: Max items in short-term memory
            long_term_max_items: Max items in long-term memory
            short_term_ttl_hours: TTL for short-term memory in hours
            long_term_ttl_days: TTL for long-term memory in days
            storage_path: Optional path for persistent storage
        """
        self.agent_name = agent_name
        self.short_term_max_items = short_term_max_items
        self.long_term_max_items = long_term_max_items
        self.short_term_ttl = timedelta(hours=short_term_ttl_hours)
        self.long_term_ttl = timedelta(days=long_term_ttl_days)
        self.storage_path = storage_path

        # Memory storages
        self.short_term_memory: deque = deque(maxlen=short_term_max_items)
        self.long_term_memory: Dict[str, MemoryEntry] = {}

        # Thread lock
        self.lock = threading.Lock()

        # Load from storage if available
        if storage_path and os.path.exists(storage_path):
            self.load()

        logger.info(f"Memory store initialized for {agent_name}")

    def add_short_term(
        self,
        content: Any,
        importance: float = 0.5,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add entry to short-term memory

        Args:
            content: Memory content
            importance: Importance score (0.0 to 1.0)
            tags: Optional tags
            metadata: Optional metadata

        Returns:
            Memory entry ID
        """
        with self.lock:
            entry_id = self._generate_id()

            entry = MemoryEntry(
                id=entry_id,
                content=content,
                memory_type="short_term",
                agent_name=self.agent_name,
                timestamp=datetime.now(timezone.utc).isoformat(),
                importance=importance,
                tags=tags,
                metadata=metadata
            )

            self.short_term_memory.append(entry)

            # Promote to long-term if importance is high
            if importance >= 0.8:
                self._promote_to_long_term(entry)

            logger.debug(f"Added short-term memory: {entry_id}")
            return entry_id

    def add_long_term(
        self,
        content: Any,
        importance: float = 0.7,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add entry to long-term memory

        Args:
            content: Memory content
            importance: Importance score (0.0 to 1.0)
            tags: Optional tags
            metadata: Optional metadata

        Returns:
            Memory entry ID
        """
        with self.lock:
            entry_id = self._generate_id()

            entry = MemoryEntry(
                id=entry_id,
                content=content,
                memory_type="long_term",
                agent_name=self.agent_name,
                timestamp=datetime.now(timezone.utc).isoformat(),
                importance=importance,
                tags=tags,
                metadata=metadata
            )

            self.long_term_memory[entry_id] = entry

            # Check size limit
            if len(self.long_term_memory) > self.long_term_max_items:
                self._evict_least_important()

            logger.debug(f"Added long-term memory: {entry_id}")
            return entry_id

    def get(self, entry_id: str) -> Optional[MemoryEntry]:
        """
        Get memory entry by ID

        Args:
            entry_id: Memory entry ID

        Returns:
            MemoryEntry or None
        """
        with self.lock:
            # Check long-term memory
            if entry_id in self.long_term_memory:
                entry = self.long_term_memory[entry_id]
                entry.access_count += 1
                entry.last_accessed = datetime.now(timezone.utc).isoformat()
                return entry

            # Check short-term memory
            for entry in self.short_term_memory:
                if entry.id == entry_id:
                    entry.access_count += 1
                    entry.last_accessed = datetime.now(timezone.utc).isoformat()
                    return entry

            return None

    def search(
        self,
        query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        memory_type: Optional[str] = None,
        min_importance: float = 0.0,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """
        Search memory entries

        Args:
            query: Optional text query
            tags: Optional tags to filter by
            memory_type: Optional memory type filter
            min_importance: Minimum importance score
            limit: Maximum number of results

        Returns:
            List of matching memory entries
        """
        with self.lock:
            results = []

            # Search long-term memory
            if not memory_type or memory_type == "long_term":
                for entry in self.long_term_memory.values():
                    if self._matches_criteria(entry, query, tags, min_importance):
                        results.append(entry)

            # Search short-term memory
            if not memory_type or memory_type == "short_term":
                for entry in self.short_term_memory:
                    if self._matches_criteria(entry, query, tags, min_importance):
                        results.append(entry)

            # Sort by importance and recency
            results.sort(
                key=lambda x: (x.importance, x.timestamp),
                reverse=True
            )

            return results[:limit]

    def get_recent(self, memory_type: str = "short_term", limit: int = 10) -> List[MemoryEntry]:
        """
        Get recent memory entries

        Args:
            memory_type: Memory type (short_term | long_term | all)
            limit: Maximum number of entries

        Returns:
            List of recent memory entries
        """
        with self.lock:
            results = []

            if memory_type in ["short_term", "all"]:
                results.extend(list(self.short_term_memory)[-limit:])

            if memory_type in ["long_term", "all"]:
                long_term_entries = sorted(
                    self.long_term_memory.values(),
                    key=lambda x: x.timestamp,
                    reverse=True
                )
                results.extend(long_term_entries[:limit])

            # Sort by timestamp
            results.sort(key=lambda x: x.timestamp, reverse=True)

            return results[:limit]

    def consolidate(self) -> int:
        """
        Consolidate memories: promote important short-term to long-term

        Returns:
            Number of memories promoted
        """
        with self.lock:
            promoted_count = 0

            for entry in self.short_term_memory:
                # Promote if importance is high or accessed frequently
                if entry.importance >= 0.7 or entry.access_count >= 3:
                    self._promote_to_long_term(entry)
                    promoted_count += 1

            logger.info(f"Consolidated memories: {promoted_count} promoted to long-term")
            return promoted_count

    def cleanup_expired(self) -> int:
        """
        Remove expired memory entries

        Returns:
            Number of entries removed
        """
        with self.lock:
            now = datetime.now(timezone.utc)
            removed_count = 0

            # Clean short-term memory
            short_term_to_remove = []
            for entry in self.short_term_memory:
                entry_time = datetime.fromisoformat(entry.timestamp)
                if now - entry_time > self.short_term_ttl:
                    short_term_to_remove.append(entry)

            for entry in short_term_to_remove:
                self.short_term_memory.remove(entry)
                removed_count += 1

            # Clean long-term memory
            long_term_to_remove = []
            for entry_id, entry in self.long_term_memory.items():
                entry_time = datetime.fromisoformat(entry.timestamp)
                if now - entry_time > self.long_term_ttl:
                    long_term_to_remove.append(entry_id)

            for entry_id in long_term_to_remove:
                del self.long_term_memory[entry_id]
                removed_count += 1

            logger.info(f"Cleaned up {removed_count} expired memories")
            return removed_count

    def _promote_to_long_term(self, entry: MemoryEntry) -> None:
        """Promote entry to long-term memory"""
        entry.memory_type = "long_term"

        if entry.id not in self.long_term_memory:
            self.long_term_memory[entry.id] = entry

    def _evict_least_important(self) -> None:
        """Evict least important long-term memories"""
        if len(self.long_term_memory) <= self.long_term_max_items:
            return

        # Sort by importance and access count
        sorted_entries = sorted(
            self.long_term_memory.items(),
            key=lambda x: (x[1].importance, x[1].access_count)
        )

        # Remove bottom 10%
        remove_count = int(len(self.long_term_memory) * 0.1)

        for entry_id, _ in sorted_entries[:remove_count]:
            del self.long_term_memory[entry_id]

        logger.debug(f"Evicted {remove_count} least important memories")

    def _matches_criteria(
        self,
        entry: MemoryEntry,
        query: Optional[str],
        tags: Optional[List[str]],
        min_importance: float
    ) -> bool:
        """Check if entry matches search criteria"""
        # Check importance
        if entry.importance < min_importance:
            return False

        # Check tags
        if tags:
            entry_tags = entry.tags or []
            if not any(tag in entry_tags for tag in tags):
                return False

        # Check query (simple string search)
        if query:
            content_str = json.dumps(entry.content).lower()
            if query.lower() not in content_str:
                return False

        return True

    def _generate_id(self) -> str:
        """Generate unique memory ID"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        return f"{self.agent_name}_{timestamp}"

    def save(self) -> bool:
        """
        Save memory to storage

        Returns:
            True if successful
        """
        if not self.storage_path:
            return False

        with self.lock:
            try:
                data = {
                    "agent_name": self.agent_name,
                    "short_term": [asdict(entry) for entry in self.short_term_memory],
                    "long_term": {k: asdict(v) for k, v in self.long_term_memory.items()}
                }

                with open(self.storage_path, "w") as f:
                    json.dump(data, f, indent=2)

                logger.info(f"Saved memory to {self.storage_path}")
                return True

            except Exception as e:
                logger.error(f"Error saving memory: {e}")
                return False

    def load(self) -> bool:
        """
        Load memory from storage

        Returns:
            True if successful
        """
        if not self.storage_path or not os.path.exists(self.storage_path):
            return False

        with self.lock:
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)

                # Load short-term memory
                self.short_term_memory.clear()
                for entry_dict in data.get("short_term", []):
                    entry = MemoryEntry(**entry_dict)
                    self.short_term_memory.append(entry)

                # Load long-term memory
                self.long_term_memory.clear()
                for entry_id, entry_dict in data.get("long_term", {}).items():
                    entry = MemoryEntry(**entry_dict)
                    self.long_term_memory[entry_id] = entry

                logger.info(f"Loaded memory from {self.storage_path}")
                return True

            except Exception as e:
                logger.error(f"Error loading memory: {e}")
                return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get memory statistics

        Returns:
            Dict with stats
        """
        with self.lock:
            short_term_count = len(self.short_term_memory)
            long_term_count = len(self.long_term_memory)

            return {
                "agent_name": self.agent_name,
                "short_term_count": short_term_count,
                "long_term_count": long_term_count,
                "total_count": short_term_count + long_term_count,
                "short_term_capacity": self.short_term_max_items,
                "long_term_capacity": self.long_term_max_items,
                "short_term_utilization_percent": (short_term_count / self.short_term_max_items) * 100,
                "long_term_utilization_percent": (long_term_count / self.long_term_max_items) * 100
            }


# Global memory store registry
_memory_stores: Dict[str, MemoryStore] = {}


def get_memory_store(
    agent_name: str,
    **kwargs
) -> MemoryStore:
    """
    Get or create memory store for agent

    Args:
        agent_name: Name of the agent
        **kwargs: Additional MemoryStore arguments

    Returns:
        MemoryStore instance
    """
    global _memory_stores

    if agent_name not in _memory_stores:
        _memory_stores[agent_name] = MemoryStore(agent_name, **kwargs)

    return _memory_stores[agent_name]
