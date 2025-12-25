"""
Logging configuration for Resume Customizer MCP Server.

This module provides a centralized logging setup with configurable levels,
formatting, and output destinations.
"""

import logging
import sys
from pathlib import Path


def setup_logger(
    name: str = "resume_customizer",
    level: str = "INFO",
    log_file: Path | None = None,
    format_string: str | None = None,
) -> logging.Logger:
    """
    Set up and configure a logger.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file. If provided, logs to both file and console.
        format_string: Optional custom format string. If not provided, uses default format.

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Default format
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - " "%(filename)s:%(lineno)d - %(message)s"
        )

    formatter = logging.Formatter(format_string, datefmt="%Y-%m-%d %H:%M:%S")

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "resume_customizer") -> logging.Logger:
    """
    Get an existing logger or create a new one with default settings.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    # If logger hasn't been set up yet, set it up with defaults
    if not logger.handlers:
        logger = setup_logger(name)

    return logger


# Module-level logger for convenience
logger = get_logger()
