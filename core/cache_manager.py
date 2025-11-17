"""
Cache Manager for Claude SDK with KV Cache Support
Manages caching for agent prompts and responses
"""

import os
import logging
import hashlib
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CacheConfig:
    """Cache configuration for an agent"""
    enabled: bool = True
    mode: str = "persistent"  # persistent, ephemeral
    ttl_seconds: int = 86400
    namespace: str = "default"


class CacheManager:
    """
    Manages KV cache for Claude SDK API calls
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize cache manager

        Args:
            config: Cache configuration dict
        """
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.default_mode = self.config.get("default_mode", "persistent")
        self.default_ttl = self.config.get("ttl_seconds", 86400)

        # Per-agent configurations
        self.agent_configs = {}
        per_agent_config = self.config.get("per_agent", {})

        for agent_name, ttl in per_agent_config.items():
            self.agent_configs[agent_name] = CacheConfig(
                enabled=self.enabled,
                mode=self.default_mode,
                ttl_seconds=ttl,
                namespace=agent_name
            )

        logger.info(f"Cache manager initialized (enabled: {self.enabled})")

    def get_cache_config(self, agent_name: str) -> CacheConfig:
        """
        Get cache configuration for agent

        Args:
            agent_name: Name of the agent

        Returns:
            CacheConfig for the agent
        """
        if agent_name in self.agent_configs:
            return self.agent_configs[agent_name]
        else:
            # Return default config
            return CacheConfig(
                enabled=self.enabled,
                mode=self.default_mode,
                ttl_seconds=self.default_ttl,
                namespace=agent_name
            )

    def generate_cache_key(
        self,
        agent_name: str,
        prompt: str,
        model: str = "claude-sonnet-4-5-20250929",
        additional_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate cache key for a prompt

        Args:
            agent_name: Name of the agent
            prompt: Prompt text
            model: Model name
            additional_params: Additional parameters to include in key

        Returns:
            Cache key string
        """
        # Include agent, prompt hash, and date in key
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()[:16]

        # Day-based key for daily cache invalidation
        day_key = datetime.now(timezone.utc).strftime("%Y%m%d")

        # Build key components
        key_parts = [agent_name, model, prompt_hash, day_key]

        # Add additional params if provided
        if additional_params:
            params_str = json.dumps(additional_params, sort_keys=True)
            params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
            key_parts.append(params_hash)

        cache_key = ":".join(key_parts)
        return cache_key

    def build_claude_cache_params(
        self,
        agent_name: str,
        prompt: str,
        model: str = "claude-sonnet-4-5-20250929"
    ) -> Dict[str, Any]:
        """
        Build cache parameters for Claude API call

        Args:
            agent_name: Name of the agent
            prompt: Prompt text
            model: Model name

        Returns:
            Dict with cache_control and kv_cache parameters
        """
        config = self.get_cache_config(agent_name)

        if not config.enabled:
            return {}

        cache_key = self.generate_cache_key(agent_name, prompt, model)

        params = {
            "cache_control": {
                "enabled": True,
                "type": config.mode,
                "key": cache_key
            },
            "kv_cache": {
                "enabled": True,
                "namespace": config.namespace,
                "max_age": config.ttl_seconds
            }
        }

        logger.debug(f"Cache params for {agent_name}: key={cache_key[:32]}...")
        return params

    def get_cache_stats(self, agent_name: str) -> Dict[str, Any]:
        """
        Get cache statistics for agent

        Args:
            agent_name: Name of the agent

        Returns:
            Dict with cache statistics
        """
        config = self.get_cache_config(agent_name)

        return {
            "agent_name": agent_name,
            "enabled": config.enabled,
            "mode": config.mode,
            "ttl_seconds": config.ttl_seconds,
            "namespace": config.namespace
        }

    def clear_agent_cache(self, agent_name: str) -> None:
        """
        Clear cache for specific agent

        Note: This is a logical operation. Actual cache clearing
        depends on Claude API implementation.

        Args:
            agent_name: Name of the agent
        """
        logger.info(f"Cache clear requested for agent: {agent_name}")
        # In practice, you would call Claude API to invalidate cache
        # or update the day_key to force new cache keys

    def update_agent_ttl(self, agent_name: str, ttl_seconds: int) -> None:
        """
        Update TTL for agent cache

        Args:
            agent_name: Name of the agent
            ttl_seconds: New TTL in seconds
        """
        if agent_name in self.agent_configs:
            self.agent_configs[agent_name].ttl_seconds = ttl_seconds
        else:
            self.agent_configs[agent_name] = CacheConfig(
                enabled=self.enabled,
                mode=self.default_mode,
                ttl_seconds=ttl_seconds,
                namespace=agent_name
            )

        logger.info(f"Updated cache TTL for {agent_name}: {ttl_seconds}s")


class PromptCacheDecorator:
    """
    Decorator to add caching to Claude API calls
    """

    def __init__(self, cache_manager: CacheManager, agent_name: str):
        """
        Initialize decorator

        Args:
            cache_manager: CacheManager instance
            agent_name: Name of the agent
        """
        self.cache_manager = cache_manager
        self.agent_name = agent_name

    def __call__(self, func):
        """
        Decorator function

        Args:
            func: Function to decorate (Claude API call)

        Returns:
            Decorated function
        """
        def wrapper(*args, **kwargs):
            # Extract prompt from kwargs
            prompt = kwargs.get("prompt", "")

            if prompt:
                # Add cache parameters
                cache_params = self.cache_manager.build_claude_cache_params(
                    self.agent_name,
                    prompt
                )

                # Merge cache params into kwargs
                kwargs.update(cache_params)

            # Call original function
            return func(*args, **kwargs)

        return wrapper


# Singleton cache manager
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(config: Optional[Dict[str, Any]] = None) -> CacheManager:
    """
    Get or create singleton cache manager

    Args:
        config: Optional cache configuration

    Returns:
        CacheManager instance
    """
    global _cache_manager

    if _cache_manager is None:
        _cache_manager = CacheManager(config)

    return _cache_manager


def with_cache(agent_name: str):
    """
    Decorator to add caching to Claude API calls

    Args:
        agent_name: Name of the agent

    Returns:
        Decorator function

    Usage:
        @with_cache("data_agent")
        def call_claude_api(prompt):
            ...
    """
    cache_manager = get_cache_manager()
    return PromptCacheDecorator(cache_manager, agent_name)
