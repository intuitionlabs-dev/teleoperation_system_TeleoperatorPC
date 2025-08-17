"""
Configuration for SO101 Leader teleoperator.
"""

from dataclasses import dataclass
from teleoperators.config import TeleoperatorConfig


@dataclass
class SO101LeaderConfig(TeleoperatorConfig):
    """Configuration for SO-101 Leader arm."""
    port: str = "/dev/ttyUSB0"
    use_degrees: bool = False