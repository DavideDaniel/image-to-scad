"""
Logging configuration for image_to_scad.

This module provides consistent logging setup across the package.
"""

import logging
import sys
from typing import Optional


# Package logger name
LOGGER_NAME = "image_to_scad"

# Default format
DEFAULT_FORMAT = "%(levelname)s: %(message)s"
VERBOSE_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging(
    level: str = "INFO",
    verbose: bool = False,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Configure logging for the image_to_scad package.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR).
        verbose: If True, use verbose format with timestamps.
        log_file: Optional path to log file.

    Returns:
        logging.Logger: Configured root logger for the package.
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers
    logger.handlers.clear()

    # Choose format
    log_format = VERBOSE_FORMAT if verbose else DEFAULT_FORMAT
    formatter = logging.Formatter(log_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(VERBOSE_FORMAT))
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a module.

    Args:
        name: Module name (usually __name__).

    Returns:
        logging.Logger: Logger instance.
    """
    # Create child logger under package namespace
    if name.startswith(LOGGER_NAME):
        return logging.getLogger(name)
    return logging.getLogger(f"{LOGGER_NAME}.{name}")


def set_level(level: str) -> None:
    """
    Set the logging level for the package.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR).
    """
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
