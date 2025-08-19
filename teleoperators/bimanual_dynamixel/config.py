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
    
    # Virtual environment path for gello_software
    venv_path: str = "/home/francesco/meta-tele-RTX/clean_version/i2rt/gello_software/.venv"
    
    # Gello software path
    gello_path: str = "/home/francesco/meta-tele-RTX/clean_version/i2rt/gello_software"