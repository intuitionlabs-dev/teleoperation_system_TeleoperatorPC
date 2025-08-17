"""
Configuration classes for robots (client side).
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class RobotConfig:
    """Base configuration class for robots."""
    id: str = "default"
    calibration_dir: Optional[Path] = None


@dataclass
class BimanualPiperClientConfig(RobotConfig):
    """Configuration for bimanual Piper client."""
    # Network Configuration
    remote_ip: str = "100.117.16.87"
    port_zmq_cmd: int = 5555
    port_zmq_observations: int = 5556
    polling_timeout_ms: int = 15
    connect_timeout_s: int = 5