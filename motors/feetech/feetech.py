"""
Feetech motors bus implementation for SO101 leader arms.
"""

import logging
import time
from enum import Enum
from typing import Dict, Any

from ..motors_bus import Motor, MotorCalibration, MotorsBus

logger = logging.getLogger(__name__)


class OperatingMode(Enum):
    """Operating modes for Feetech motors."""
    POSITION = 0
    VELOCITY = 1
    PWM = 2
    STEP = 3


class FeetechMotorsBus(MotorsBus):
    """
    Feetech motors bus for communicating with SO101 leader arms.
    Uses the scservo SDK to communicate with motors.
    """
    
    def __init__(
        self,
        port: str,
        motors: dict[str, Motor],
        calibration: dict[str, MotorCalibration] | None = None,
        protocol_version: int = 0,
    ):
        super().__init__(port, motors, calibration)
        self.protocol_version = protocol_version
        
        # These will be initialized on connect
        self.port_handler = None
        self.packet_handler = None
        self.sync_reader = None
        self.sync_writer = None
    
    def connect(self, handshake: bool = False):
        """Connect to the Feetech motors."""
        import scservo_sdk as scs
        
        self.port_handler = scs.PortHandler(self.port)
        self.packet_handler = scs.PacketHandler(self.protocol_version)
        
        if not self.port_handler.openPort():
            raise RuntimeError(f"Failed to open port {self.port}")
        
        if not self.port_handler.setBaudRate(1_000_000):
            raise RuntimeError(f"Failed to set baudrate on port {self.port}")
        
        self._is_connected = True
        logger.info(f"Connected to Feetech motors on {self.port}")
    
    def disconnect(self):
        """Disconnect from the motors."""
        if self.port_handler:
            self.port_handler.closePort()
        self._is_connected = False
        logger.info(f"Disconnected from Feetech motors on {self.port}")
    
    def sync_read(self, data_name: str) -> dict[str, float]:
        """Read data synchronously from all motors."""
        import scservo_sdk as scs
        
        results = {}
        
        # For SO101 leader, we read Present_Position
        if data_name == "Present_Position":
            for motor_name, motor in self.motors.items():
                # Read position from motor
                dxl_present_position, dxl_comm_result, dxl_error = self.packet_handler.read2ByteTxRx(
                    self.port_handler, motor.id, 56  # Address for Present_Position
                )
                
                if dxl_comm_result != scs.COMM_SUCCESS:
                    logger.warning(f"Failed to read from motor {motor_name}")
                    results[motor_name] = 0.0
                else:
                    # Convert to normalized value based on motor's norm_mode
                    raw_value = dxl_present_position
                    if motor_name in self.calibration:
                        calib = self.calibration[motor_name]
                        # Don't apply homing_offset - it's already applied by the hardware
                        # Normalize based on range
                        if motor.norm_mode.value == "range_m100_100":
                            normalized = ((raw_value - calib.range_min) / (calib.range_max - calib.range_min)) * 200 - 100
                        elif motor.norm_mode.value == "range_0_100":
                            normalized = ((raw_value - calib.range_min) / (calib.range_max - calib.range_min)) * 100
                        else:
                            normalized = raw_value
                        results[motor_name] = normalized
                    else:
                        results[motor_name] = float(raw_value)
        
        return results
    
    def sync_write(self, data_name: str, values: dict[str, float]):
        """Write data synchronously to all motors."""
        # Not needed for leader arms in teleoperation
        pass
    
    def write(self, data_name: str, motor_name: str, value: Any):
        """Write a single value to a motor."""
        import scservo_sdk as scs
        
        motor = self.motors[motor_name]
        
        if data_name == "Operating_Mode":
            # Set operating mode
            self.packet_handler.write1ByteTxRx(
                self.port_handler, motor.id, 33, value  # Address for Operating_Mode
            )
        elif data_name == "Torque_Enable":
            # Enable/disable torque
            self.packet_handler.write1ByteTxRx(
                self.port_handler, motor.id, 40, value  # Address for Torque_Enable  
            )
    
    def disable_torque(self):
        """Disable torque for all motors."""
        for motor_name in self.motors:
            self.write("Torque_Enable", motor_name, 0)
    
    def enable_torque(self):
        """Enable torque for all motors."""
        for motor_name in self.motors:
            self.write("Torque_Enable", motor_name, 1)
    
    def configure_motors(self):
        """Configure motors for operation."""
        # Basic configuration for SO101 leader
        pass
    
    def setup_motor(self, motor_name: str):
        """Setup a single motor."""
        # Used during initial motor setup
        pass
    
    def set_half_turn_homings(self) -> dict[str, int]:
        """Set homing offsets for all motors at their current positions."""
        import scservo_sdk as scs
        
        homing_offsets = {}
        for motor_name, motor in self.motors.items():
            # Read current position
            position, _, _ = self.packet_handler.read2ByteTxRx(
                self.port_handler, motor.id, 56  # Present_Position address
            )
            # Set as homing offset (middle of range)
            homing_offsets[motor_name] = position
        
        return homing_offsets
    
    def record_ranges_of_motion(self) -> tuple[dict[str, int], dict[str, int]]:
        """Record the range of motion for all motors with live display."""
        import scservo_sdk as scs
        import select
        import sys
        
        range_mins = {motor: float('inf') for motor in self.motors}
        range_maxes = {motor: float('-inf') for motor in self.motors}
        
        user_pressed_enter = False
        while not user_pressed_enter:
            # Read positions and update ranges
            for motor_name, motor in self.motors.items():
                position, _, _ = self.packet_handler.read2ByteTxRx(
                    self.port_handler, motor.id, 56  # Present_Position
                )
                if range_mins[motor_name] == float('inf'):
                    range_mins[motor_name] = position
                    range_maxes[motor_name] = position
                else:
                    range_mins[motor_name] = min(range_mins[motor_name], position)
                    range_maxes[motor_name] = max(range_maxes[motor_name], position)
            
            # Display current ranges
            print("\n-------------------------------------------")
            print(f"{'NAME':<15} | {'MIN':>6} | {'POS':>6} | {'MAX':>6}")
            for motor_name, motor in self.motors.items():
                position, _, _ = self.packet_handler.read2ByteTxRx(
                    self.port_handler, motor.id, 56  # Present_Position
                )
                print(f"{motor_name:<15} | {range_mins[motor_name]:>6} | {position:>6} | {range_maxes[motor_name]:>6}")
            
            # Check if user pressed enter
            if sys.stdin in select.select([sys.stdin], [], [], 0)[0]:
                _ = sys.stdin.readline()
                user_pressed_enter = True
            
            if not user_pressed_enter:
                # Move cursor up to overwrite the previous output
                print(f"\033[{len(self.motors) + 3}A", end="")
            
            time.sleep(0.01)
        
        return range_mins, range_maxes
    
    def write_calibration(self, calibration: dict[str, MotorCalibration]):
        """Write calibration to the motors."""
        import scservo_sdk as scs
        
        # Write calibration values to hardware
        for motor_name, calib in calibration.items():
            motor = self.motors[motor_name]
            
            # Write homing offset (address 20 for Homing_Offset)
            self.packet_handler.write2ByteTxRx(
                self.port_handler, motor.id, 20, calib.homing_offset
            )
            
            # Write min position limit (address 22 for Min_Position_Limit)
            self.packet_handler.write2ByteTxRx(
                self.port_handler, motor.id, 22, calib.range_min
            )
            
            # Write max position limit (address 24 for Max_Position_Limit)
            self.packet_handler.write2ByteTxRx(
                self.port_handler, motor.id, 24, calib.range_max
            )
        
        self.calibration = calibration