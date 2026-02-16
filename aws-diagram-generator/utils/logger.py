"""
Logging configuration
"""

import logging
import sys

import config


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(getattr(logging, config.LOG_LEVEL))

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, config.LOG_LEVEL))

        formatter = logging.Formatter(config.LOG_FORMAT)
        handler.setFormatter(formatter)

        logger.addHandler(handler)

    return logger
