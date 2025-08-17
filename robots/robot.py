"""
Base abstract class for robots (client side).
"""

import abc
from pathlib import Path
from typing import Any, Type

from robots.config import RobotConfig


class Robot(abc.ABC):
    """Base abstract class for all robots."""
    
    config_class: Type[RobotConfig]
    name: str
    
    def __init__(self, config: RobotConfig):
        self.robot_type = self.name
        self.id = config.id
        self.calibration_dir = config.calibration_dir if config.calibration_dir else Path("calibration") / self.name
        self.calibration_dir.mkdir(parents=True, exist_ok=True)
        self.calibration_fpath = self.calibration_dir / f"{self.id}.json"
        self.calibration = {}
    
    def __str__(self) -> str:
        return f"{self.id} {self.__class__.__name__}"
    
    @property
    @abc.abstractmethod
    def observation_features(self) -> dict:
        """Dictionary describing the structure and types of observations."""
        pass
    
    @property
    @abc.abstractmethod
    def action_features(self) -> dict:
        """Dictionary describing the structure and types of actions."""
        pass
    
    @property
    @abc.abstractmethod
    def is_connected(self) -> bool:
        """Whether the robot is currently connected."""
        pass
    
    @abc.abstractmethod
    def connect(self, calibrate: bool = True) -> None:
        """Establish communication with the robot."""
        pass
    
    @abc.abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the robot."""
        pass
    
    @abc.abstractmethod
    def get_observation(self) -> dict[str, Any]:
        """Retrieve the current observation from the robot."""
        pass
    
    @abc.abstractmethod
    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Send an action command to the robot."""
        pass