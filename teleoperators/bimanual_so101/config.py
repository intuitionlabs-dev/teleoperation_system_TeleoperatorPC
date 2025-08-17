"""
Configuration for Bimanual SO101 Leader teleoperator.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from teleoperators.config import TeleoperatorConfig
from teleoperators.so101.config import SO101LeaderConfig


@dataclass  
class BimanualSO101LeaderConfig(TeleoperatorConfig):
    """Configuration for bimanual SO101 leader arms."""
    left_arm: SO101LeaderConfig = field(default_factory=lambda: SO101LeaderConfig(port="/dev/ttyACM0"))
    right_arm: SO101LeaderConfig = field(default_factory=lambda: SO101LeaderConfig(port="/dev/ttyACM1"))
    left_calib_name: str = "left_arm"
    right_calib_name: str = "right_arm"