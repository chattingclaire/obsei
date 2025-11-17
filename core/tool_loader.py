"""
Tool Loader
Dynamically loads and manages tools for agents based on configuration
"""

import os
import logging
import importlib
from typing import Dict, List, Optional, Any, Type
import yaml

logger = logging.getLogger(__name__)


class ToolLoader:
    """
    Dynamically loads and manages tools for agents
    """

    def __init__(self, config_path: str = "config/agent_tools.yaml"):
        """
        Initialize tool loader

        Args:
            config_path: Path to agent tools configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()

        # Cache for loaded tool classes
        self.tool_classes: Dict[str, Type] = {}

        # Cache for tool instances
        self.tool_instances: Dict[str, Any] = {}

        logger.info(f"Tool loader initialized from {config_path}")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded tool configuration with {len(config.get('tool_definitions', {}))} tool definitions")
            return config
        except Exception as e:
            logger.error(f"Error loading tool config: {e}")
            return {}

    def get_agent_tools(self, agent_name: str) -> List[str]:
        """
        Get list of tools available to an agent

        Args:
            agent_name: Name of the agent

        Returns:
            List of tool names
        """
        agent_config = self.config.get(agent_name, {})
        tools = agent_config.get("tools", [])

        logger.debug(f"Agent {agent_name} has access to tools: {tools}")
        return tools

    def load_tool_class(self, tool_name: str) -> Optional[Type]:
        """
        Load tool class dynamically

        Args:
            tool_name: Name of the tool

        Returns:
            Tool class or None if not found
        """
        # Check cache first
        if tool_name in self.tool_classes:
            return self.tool_classes[tool_name]

        # Get tool definition
        tool_def = self.config.get("tool_definitions", {}).get(tool_name)
        if not tool_def:
            logger.error(f"Tool definition not found for: {tool_name}")
            return None

        try:
            # Map tool name to module and class
            module_map = {
                "browser_tool": ("tools.browser_tool", "BrowserTool"),
                "scraper_tool": ("tools.scraper_tool", "ScraperTool"),
                "image_tool": ("tools.image_tool", "ImageTool"),
                "video_tool": ("tools.video_tool", "VideoTool"),
                "github_tool": ("tools.github_tool", "GitHubTool"),
                "rss_tool": ("tools.rss_tool", "RSSTool"),
            }

            if tool_name not in module_map:
                logger.error(f"Unknown tool: {tool_name}")
                return None

            module_name, class_name = module_map[tool_name]

            # Import module
            module = importlib.import_module(module_name)

            # Get class
            tool_class = getattr(module, class_name)

            # Cache the class
            self.tool_classes[tool_name] = tool_class

            logger.info(f"Loaded tool class: {tool_name}")
            return tool_class

        except Exception as e:
            logger.error(f"Error loading tool {tool_name}: {e}")
            return None

    def get_tool_instance(
        self,
        tool_name: str,
        agent_name: Optional[str] = None,
        force_new: bool = False
    ) -> Optional[Any]:
        """
        Get tool instance (creates new or returns cached)

        Args:
            tool_name: Name of the tool
            agent_name: Name of the agent (for permission checking)
            force_new: Force creation of new instance

        Returns:
            Tool instance or None
        """
        # Check if agent has permission to use this tool
        if agent_name:
            agent_tools = self.get_agent_tools(agent_name)
            if tool_name not in agent_tools:
                logger.warning(f"Agent {agent_name} does not have permission to use {tool_name}")
                return None

        # Check cache
        cache_key = f"{agent_name}:{tool_name}" if agent_name else tool_name

        if not force_new and cache_key in self.tool_instances:
            return self.tool_instances[cache_key]

        # Load tool class
        tool_class = self.load_tool_class(tool_name)
        if not tool_class:
            return None

        # Get tool-specific configuration
        tool_config = self._get_tool_config(tool_name, agent_name)

        try:
            # Instantiate tool with config
            tool_instance = tool_class(**tool_config)

            # Cache instance
            self.tool_instances[cache_key] = tool_instance

            logger.info(f"Created tool instance: {tool_name} for {agent_name or 'system'}")
            return tool_instance

        except Exception as e:
            logger.error(f"Error instantiating tool {tool_name}: {e}")
            return None

    def _get_tool_config(self, tool_name: str, agent_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get configuration for tool instantiation

        Args:
            tool_name: Name of the tool
            agent_name: Name of the agent

        Returns:
            Configuration dict
        """
        config = {}

        # Get agent-specific permissions
        if agent_name:
            agent_config = self.config.get(agent_name, {})
            tool_permissions = agent_config.get("tool_permissions", {})

            if tool_name in tool_permissions:
                config.update(tool_permissions[tool_name])

        return config

    def get_tools_for_agent(self, agent_name: str) -> Dict[str, Any]:
        """
        Get all tool instances for an agent

        Args:
            agent_name: Name of the agent

        Returns:
            Dict of tool_name: tool_instance
        """
        tools = {}
        tool_names = self.get_agent_tools(agent_name)

        for tool_name in tool_names:
            instance = self.get_tool_instance(tool_name, agent_name)
            if instance:
                tools[tool_name] = instance

        logger.info(f"Loaded {len(tools)} tools for agent {agent_name}")
        return tools

    def get_tool_capabilities(self, tool_name: str) -> List[str]:
        """
        Get capabilities of a tool

        Args:
            tool_name: Name of the tool

        Returns:
            List of capabilities
        """
        tool_def = self.config.get("tool_definitions", {}).get(tool_name, {})
        return tool_def.get("capabilities", [])

    def reload_config(self) -> None:
        """Reload configuration from file"""
        self.config = self._load_config()

        # Clear caches
        self.tool_instances.clear()

        logger.info("Tool configuration reloaded")

    def get_all_tools(self) -> List[str]:
        """
        Get list of all available tools

        Returns:
            List of tool names
        """
        return list(self.config.get("tool_definitions", {}).keys())


class ToolRegistry:
    """
    Global registry for tool instances and metadata
    """

    def __init__(self):
        """Initialize tool registry"""
        self.tools: Dict[str, Any] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}

    def register_tool(self, name: str, instance: Any, metadata: Optional[Dict[str, Any]] = None):
        """
        Register a tool instance

        Args:
            name: Tool name
            instance: Tool instance
            metadata: Optional metadata
        """
        self.tools[name] = instance

        if metadata:
            self.metadata[name] = metadata

        logger.info(f"Registered tool: {name}")

    def get_tool(self, name: str) -> Optional[Any]:
        """
        Get tool instance by name

        Args:
            name: Tool name

        Returns:
            Tool instance or None
        """
        return self.tools.get(name)

    def list_tools(self) -> List[str]:
        """
        List all registered tools

        Returns:
            List of tool names
        """
        return list(self.tools.keys())


# Singleton instances
_tool_loader: Optional[ToolLoader] = None
_tool_registry: Optional[ToolRegistry] = None


def get_tool_loader(config_path: str = "config/agent_tools.yaml") -> ToolLoader:
    """
    Get or create singleton tool loader

    Args:
        config_path: Path to configuration file

    Returns:
        ToolLoader instance
    """
    global _tool_loader

    if _tool_loader is None:
        _tool_loader = ToolLoader(config_path)

    return _tool_loader


def get_tool_registry() -> ToolRegistry:
    """
    Get or create singleton tool registry

    Returns:
        ToolRegistry instance
    """
    global _tool_registry

    if _tool_registry is None:
        _tool_registry = ToolRegistry()

    return _tool_registry
