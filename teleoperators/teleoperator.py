"""
Base abstract class for all teleoperators.
"""

import abc
import json
from pathlib import Path
from typing import Any, Type

from teleoperators.config import TeleoperatorConfig


class Teleoperator(abc.ABC):
    """Base abstract class for all teleoperators."""
    
    config_class: Type[TeleoperatorConfig]
    name: str
    
    def __init__(self, config: TeleoperatorConfig):
        self.teleop_type = self.name
        self.id = config.id
        self.calibration_dir = config.calibration_dir if config.calibration_dir else Path("calibration") / self.name
        self.calibration_dir.mkdir(parents=True, exist_ok=True)
        self.calibration_fpath = self.calibration_dir / f"{self.id}.json"
        self.calibration = {}
        if self.calibration_fpath.is_file():
            self._load_calibration()
    
    def __str__(self) -> str:
        return f"{self.id} {self.__class__.__name__}"
    
    def _load_calibration(self):
        """Load calibration from file."""
        with open(self.calibration_fpath, "r") as f:
            calibration_dict = json.load(f)
        
        # Convert calibration dict to proper format
        from motors import MotorCalibration
        self.calibration = {}
        for motor_name, calib_data in calibration_dict.items():
            self.calibration[motor_name] = MotorCalibration(**calib_data)
    
    def _save_calibration(self):
        """Save calibration to file."""
        calibration_dict = {}
        for motor_name, motor_calib in self.calibration.items():
            calibration_dict[motor_name] = {
                "id": motor_calib.id,
                "drive_mode": motor_calib.drive_mode,
                "homing_offset": motor_calib.homing_offset,
                "range_min": motor_calib.range_min,
                "range_max": motor_calib.range_max,
            }
        
        with open(self.calibration_fpath, "w") as f:
            json.dump(calibration_dict, f, indent=2)
    
    @property
    @abc.abstractmethod
    def action_features(self) -> dict[str, type]:
        """Dictionary describing the structure and types of actions produced."""
        pass
    
    @property
    @abc.abstractmethod
    def feedback_features(self) -> dict[str, type]:
        """Dictionary describing the structure and types of feedback expected."""
        pass
    
    @property
    @abc.abstractmethod
    def is_connected(self) -> bool:
        """Whether the teleoperator is currently connected."""
        pass
    
    @abc.abstractmethod
    def connect(self, calibrate: bool = True) -> None:
        """Establish communication with the teleoperator."""
        pass
    
    @abc.abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the teleoperator."""
        pass
    
    @abc.abstractmethod
    def get_action(self) -> dict[str, Any]:
        """Get the current action from the teleoperator."""
        pass
    
    @abc.abstractmethod
    def send_feedback(self, feedback: dict[str, Any]) -> None:
        """Send feedback to the teleoperator."""
        pass