"""Configuration for bimanual Piper client"""
from dataclasses import dataclass


@dataclass
class BimanualPiperClientConfig:
    """Configuration for BimanualPiperClient"""
    hostname: str = "100.104.247.35"  # Robot PC IP address
    cmd_port: int = 5555  # Port for sending commands
