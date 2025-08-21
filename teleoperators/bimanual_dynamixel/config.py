"""Configuration for bimanual Dynamixel (YAM leader) teleoperator."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from teleoperators.config import TeleoperatorConfig


@dataclass
class DynamixelLeaderConfig(TeleoperatorConfig):
    """Configuration for a single Dynamixel leader arm."""
    config_path: str = ""
    """Path to the YAML configuration file for the arm."""
    
    hardware_port: int = 6001
    """ZMQ server port for hardware communication."""


@dataclass 
class BimanualDynamixelLeaderConfig(TeleoperatorConfig):
    """Configuration for bimanual Dynamixel leader arms."""
    left_arm: DynamixelLeaderConfig = None
    right_arm: DynamixelLeaderConfig = None
    
    # Path to third-party modules (relative to teleoperation_system_TeleoperatorPC)
    gello_path: str = "third_party"