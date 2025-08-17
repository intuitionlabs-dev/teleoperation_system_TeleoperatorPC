"""
SO101 Leader Arm teleoperator.
"""

import logging
import time
from pathlib import Path

from motors import Motor, MotorCalibration, MotorNormMode
from motors.feetech import FeetechMotorsBus, OperatingMode
from teleoperators.teleoperator import Teleoperator
from teleoperators.so101.config import SO101LeaderConfig
from serial import SerialException

logger = logging.getLogger(__name__)


class SO101Leader(Teleoperator):
    """
    SO-101 Leader Arm teleoperator.
    """
    
    config_class = SO101LeaderConfig
    name = "so101_leader"
    
    def __init__(self, config: SO101LeaderConfig):
        super().__init__(config)
        self.config = config
        norm_mode_body = MotorNormMode.DEGREES if config.use_degrees else MotorNormMode.RANGE_M100_100
        self.bus = FeetechMotorsBus(
            port=self.config.port,
            motors={
                "shoulder_pan": Motor(1, "sts3215", norm_mode_body),
                "shoulder_lift": Motor(2, "sts3215", norm_mode_body),
                "elbow_flex": Motor(3, "sts3215", norm_mode_body),
                "wrist_flex": Motor(4, "sts3215", norm_mode_body),
                "wrist_roll": Motor(5, "sts3215", norm_mode_body),
                "gripper": Motor(6, "sts3215", MotorNormMode.RANGE_0_100),
            },
            calibration=self.calibration,
        )
    
    @property
    def action_features(self) -> dict[str, type]:
        return {f"{motor}.pos": float for motor in self.bus.motors}
    
    @property
    def feedback_features(self) -> dict[str, type]:
        return {}
    
    @property
    def is_connected(self) -> bool:
        return self.bus.is_connected
    
    def connect(self, calibrate: bool = True) -> None:
        if self.is_connected:
            raise RuntimeError(f"{self} already connected")
        
        try:
            self.bus.connect(handshake=False)
        except SerialException as e:
            raise RuntimeError(
                f"Failed to connect to the leader arm on port {self.config.port}. "
                "Please make sure the device is connected and the port is correct."
            ) from e
        
        if self.is_connected and calibrate and not self.is_calibrated:
            self.calibrate()
        
        self.configure()
        logger.info(f"{self} connected.")
    
    @property
    def is_calibrated(self) -> bool:
        return self.bus.is_calibrated
    
    def calibrate(self) -> None:
        logger.info(f"\nRunning calibration of {self}")
        self.bus.disable_torque()
        for motor in self.bus.motors:
            self.bus.write("Operating_Mode", motor, OperatingMode.POSITION.value)
        
        input(f"Move {self} to the middle of its range of motion and press ENTER....")
        homing_offsets = self.bus.set_half_turn_homings()
        
        print(
            "Move all joints sequentially through their entire ranges "
            "of motion.\nRecording positions. Press ENTER to stop..."
        )
        range_mins, range_maxes = self.bus.record_ranges_of_motion()
        
        self.calibration = {}
        for motor, m in self.bus.motors.items():
            self.calibration[motor] = MotorCalibration(
                id=m.id,
                drive_mode=0,
                homing_offset=homing_offsets[motor],
                range_min=range_mins[motor],
                range_max=range_maxes[motor],
            )
        
        self.bus.write_calibration(self.calibration)
        self._save_calibration()
        print(f"Calibration saved to {self.calibration_fpath}")
    
    def configure(self) -> None:
        self.bus.disable_torque()
        self.bus.configure_motors()
        for motor in self.bus.motors:
            self.bus.write("Operating_Mode", motor, OperatingMode.POSITION.value)
    
    def setup_motors(self) -> None:
        for motor in reversed(self.bus.motors):
            input(f"Connect the controller board to the '{motor}' motor only and press enter.")
            self.bus.setup_motor(motor)
            print(f"'{motor}' motor id set to {self.bus.motors[motor].id}")
    
    def get_action(self) -> dict[str, float]:
        start = time.perf_counter()
        action = self.bus.sync_read("Present_Position")
        action = {f"{motor}.pos": val for motor, val in action.items()}
        dt_ms = (time.perf_counter() - start) * 1e3
        logger.debug(f"{self} read action: {dt_ms:.1f}ms")
        return action
    
    def send_feedback(self, feedback: dict[str, float]) -> None:
        # Force feedback not implemented yet
        raise NotImplementedError
    
    def disconnect(self) -> None:
        if not self.is_connected:
            raise RuntimeError(f"{self} is not connected.")
        
        self.bus.disconnect()
        logger.info(f"{self} disconnected.")