#!/usr/bin/env python

# Simple test script to verify motor classes are working
# This is for teleoperation system validation

from .motor_types import Motor, MotorCalibration, MotorNormMode
from .feetech_motors import FeetechMotorsBus, OperatingMode, TorqueMode
from .exceptions import DeviceNotConnectedError

def test_motor_creation():
    """Test that we can create motor instances."""
    motor = Motor(
        id=1,
        model="sts3215",
        norm_mode=MotorNormMode.RANGE_M100_100
    )
    
    calibration = MotorCalibration(
        id=1,
        drive_mode=0,
        homing_offset=0,
        range_min=0,
        range_max=4095
    )
    
    print(f"Created motor: {motor}")
    print(f"Created calibration: {calibration}")
    print("✓ Motor creation test passed")

def test_operating_modes():
    """Test OperatingMode enum."""
    assert OperatingMode.POSITION.value == 0
    assert OperatingMode.VELOCITY.value == 1
    assert OperatingMode.PWM.value == 2
    assert OperatingMode.STEP.value == 3
    print("✓ OperatingMode test passed")

def test_torque_modes():
    """Test TorqueMode enum."""
    assert TorqueMode.ENABLED.value == 1
    assert TorqueMode.DISABLED.value == 0
    print("✓ TorqueMode test passed")

def test_feetech_bus_creation():
    """Test FeetechMotorsBus creation (without actual connection)."""
    motors = {
        "shoulder": Motor(id=1, model="sts3215", norm_mode=MotorNormMode.RANGE_M100_100),
        "elbow": Motor(id=2, model="sts3215", norm_mode=MotorNormMode.RANGE_M100_100),
    }
    
    try:
        bus = FeetechMotorsBus(
            port="/dev/ttyUSB0",  # Dummy port
            motors=motors
        )
        print(f"Created FeetechMotorsBus: {bus}")
        print("✓ FeetechMotorsBus creation test passed")
    except ImportError as e:
        print(f"⚠ FeetechMotorsBus creation skipped (scservo_sdk not installed): {e}")

if __name__ == "__main__":
    print("Testing simplified motor classes for teleoperation system...")
    test_motor_creation()
    test_operating_modes() 
    test_torque_modes()
    test_feetech_bus_creation()
    print("\n✓ All basic tests passed! Motor classes are ready for SO101 leader arm control.")