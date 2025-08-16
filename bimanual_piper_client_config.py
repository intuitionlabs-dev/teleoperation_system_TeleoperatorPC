"""Configuration for bimanual Piper client"""
from dataclasses import dataclass


@dataclass
class BimanualPiperClientConfig:
    """Configuration for BimanualPiperClient"""
    hostname: str = "192.168.123.139"  # Robot PC IP address
    cmd_port: int = 5555  # Port for sending commands
    obs_port: int = 5556  # Port for receiving observations
