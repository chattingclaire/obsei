"""
Centralized Logging Configuration for Multi-Agent System
"""

import os
import logging
import sys
from typing import Optional
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logger(
    name: str = "multi_agent_system",
    log_level: str = "INFO",
    log_dir: str = "logs",
    log_to_file: bool = True,
    log_to_console: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Setup and configure logger

    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        log_to_file: Enable file logging
        log_to_console: Enable console logging
        max_bytes: Maximum log file size before rotation
        backup_count: Number of backup files to keep

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)

    # Clear existing handlers
    logger.handlers.clear()

    # Set log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)

    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    simple_formatter = logging.Formatter(
        fmt="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%H:%M:%S"
    )

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)

    # File handler
    if log_to_file:
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)

        # Create log filename with timestamp
        log_filename = os.path.join(
            log_dir,
            f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        )

        file_handler = RotatingFileHandler(
            log_filename,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(detailed_formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    logger.info(f"Logger '{name}' initialized at level {log_level}")
    return logger


def get_agent_logger(agent_name: str, log_level: str = "INFO") -> logging.Logger:
    """
    Get logger for specific agent

    Args:
        agent_name: Name of the agent
        log_level: Logging level

    Returns:
        Agent-specific logger
    """
    logger_name = f"agent.{agent_name}"
    return setup_logger(
        name=logger_name,
        log_level=log_level,
        log_dir=f"logs/agents/{agent_name}"
    )


def get_tool_logger(tool_name: str, log_level: str = "INFO") -> logging.Logger:
    """
    Get logger for specific tool

    Args:
        tool_name: Name of the tool
        log_level: Logging level

    Returns:
        Tool-specific logger
    """
    logger_name = f"tool.{tool_name}"
    return setup_logger(
        name=logger_name,
        log_level=log_level,
        log_dir="logs/tools"
    )


def get_pipeline_logger(log_level: str = "INFO") -> logging.Logger:
    """
    Get logger for pipeline orchestrator

    Args:
        log_level: Logging level

    Returns:
        Pipeline logger
    """
    return setup_logger(
        name="pipeline",
        log_level=log_level,
        log_dir="logs/pipeline"
    )


class AgentLoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds agent context to log messages
    """

    def __init__(self, logger: logging.Logger, agent_name: str, run_id: Optional[str] = None):
        """
        Initialize adapter

        Args:
            logger: Base logger
            agent_name: Name of the agent
            run_id: Optional run ID for tracking
        """
        super().__init__(logger, {})
        self.agent_name = agent_name
        self.run_id = run_id or datetime.now().strftime("%Y%m%d_%H%M%S")

    def process(self, msg, kwargs):
        """
        Process log message to add context

        Args:
            msg: Log message
            kwargs: Additional kwargs

        Returns:
            Processed message and kwargs
        """
        return f"[{self.agent_name}:{self.run_id}] {msg}", kwargs


# Initialize default system logger
_system_logger: Optional[logging.Logger] = None


def get_system_logger(log_level: Optional[str] = None) -> logging.Logger:
    """
    Get or create system-wide logger

    Args:
        log_level: Optional log level override

    Returns:
        System logger
    """
    global _system_logger

    if _system_logger is None:
        level = log_level or os.getenv("LOG_LEVEL", "INFO")
        _system_logger = setup_logger(
            name="multi_agent_system",
            log_level=level,
            log_dir="logs"
        )

    return _system_logger
