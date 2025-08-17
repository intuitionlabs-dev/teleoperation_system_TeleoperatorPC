"""
Base motor bus implementation for teleoperation.
"""

import abc
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

logger = logging.getLogger(__name__)


class MotorNormMode(str, Enum):
    """Normalization modes for motor values."""
    RANGE_0_100 = "range_0_100"
    RANGE_M100_100 = "range_m100_100"
    DEGREES = "degrees"


@dataclass
class MotorCalibration:
    """Calibration data for a single motor."""
    id: int
    drive_mode: int
    homing_offset: int
    range_min: int
    range_max: int


@dataclass
class Motor:
    """Motor configuration."""
    id: int
    model: str
    norm_mode: MotorNormMode


class MotorsBus(abc.ABC):
    """Abstract base class for motor bus implementations."""
    
    def __init__(self, port: str, motors: dict[str, Motor], calibration: dict[str, MotorCalibration] = None):
        self.port = port
        self.motors = motors
        self.calibration = calibration or {}
        self._is_connected = False
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected
    
    @property
    def is_calibrated(self) -> bool:
        return len(self.calibration) == len(self.motors)
    
    @abc.abstractmethod
    def connect(self, handshake: bool = True):
        """Connect to the motor bus."""
        pass
    
    @abc.abstractmethod
    def disconnect(self):
        """Disconnect from the motor bus."""
        pass
    
    @abc.abstractmethod
    def sync_read(self, data_name: str) -> dict[str, float]:
        """Synchronously read data from all motors."""
        pass
    
    @abc.abstractmethod
    def sync_write(self, data_name: str, values: dict[str, float]):
        """Synchronously write data to all motors."""
        pass
    
    @abc.abstractmethod
    def disable_torque(self):
        """Disable torque for all motors."""
        pass
    
    @abc.abstractmethod
    def enable_torque(self):
        """Enable torque for all motors."""
        pass