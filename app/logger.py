"""Logging configuration for the Magic Shop application.

This module provides a centralized logging configuration with consistent
formatting and output to stdout for container-based deployments.
"""

import logging
import sys

from app.config import Config


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance.

    Creates or retrieves a logger with the specified name and configures
    it with the application's logging settings from config.yaml.

    Args:
        name: The name of the logger, typically __name__ of the calling module.

    Returns:
        A configured logging.Logger instance.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        # Get log level from config
        try:
            log_level_str = Config.get_log_level()
            log_level = getattr(logging, log_level_str.upper(), logging.INFO)
        except Exception:
            # Fallback to INFO if config fails
            log_level = logging.INFO

        logger.setLevel(log_level)

        # Create console handler (stdout)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)

        # Create formatter with timestamp
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(handler)

        # Prevent propagation to root logger to avoid duplicate logs
        logger.propagate = False

    return logger
