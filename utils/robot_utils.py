"""
Utility functions for robot control.
"""

import time
import sys


def busy_wait(duration: float):
    """Busy wait for a specific duration."""
    if duration <= 0:
        return
    start = time.perf_counter()
    while time.perf_counter() - start < duration:
        pass


def move_cursor_up(lines: int):
    """Move terminal cursor up by specified number of lines."""
    sys.stdout.write(f"\033[{lines}A")
    sys.stdout.flush()