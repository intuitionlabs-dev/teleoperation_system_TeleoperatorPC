"""
Base configuration for teleoperators.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class TeleoperatorConfig:
    """Base configuration class for teleoperators."""
    id: str = "default"
    calibration_dir: Optional[Path] = None