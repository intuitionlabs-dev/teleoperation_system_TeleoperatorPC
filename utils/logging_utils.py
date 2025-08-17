"""
Logging utilities for teleoperation.
"""

import logging


def init_logging(level=logging.INFO):
    """Initialize logging configuration."""
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )