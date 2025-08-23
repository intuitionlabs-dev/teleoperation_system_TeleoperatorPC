#!/usr/bin/env python3
"""Test reading positions from Dynamixel leaders to debug joint mapping."""

import sys
import time
import numpy as np
from pathlib import Path

# Add third_party to path
sys.path.insert(0, str(Path(__file__).parent.parent / "third_party"))

from gello.dynamixel.driver import DynamixelDriver


def test_dynamixel_reading(port: str, joint_ids: list, offsets: list, signs: list):
    """Test reading from Dynamixel motors with offsets and signs."""
    
    print(f"\nTesting {port}")
    print("=" * 60)
    
    # Initialize driver
    driver = DynamixelDriver(joint_ids, port=port, baudrate=57600)
    
    print(f"Joint IDs: {joint_ids}")
    print(f"Offsets: {[f'{o:.4f}' for o in offsets]}")
    print(f"Signs: {signs}")
    print()
    
    # Read for a few seconds
    for i in range(5):
        raw_positions = driver.get_joints()
        
        # Apply offsets and signs (same as in DynamixelRobot)
        adjusted_positions = (raw_positions[:6] - np.array(offsets)) * np.array(signs)
        
        print(f"\nIteration {i+1}:")
        print("Motor ID | Raw Pos (rad) | Offset | Sign | Final Pos (rad) | Final (deg)")
        print("-" * 75)
        
        for j in range(6):
            motor_id = joint_ids[j]
            raw = raw_positions[j]
            offset = offsets[j]
            sign = signs[j]
            final = adjusted_positions[j]
            final_deg = final * 180 / np.pi
            
            print(f"   {motor_id:2d}    | {raw:7.4f}      | {offset:6.4f} | {sign:4.0f} | {final:7.4f}        | {final_deg:7.1f}")
        
        # Show gripper separately
        if len(raw_positions) > 6:
            gripper_raw = raw_positions[6]
            gripper_deg = gripper_raw * 180 / np.pi
            print(f"\nGripper (ID 7): {gripper_raw:.4f} rad ({gripper_deg:.1f} deg)")
        
        time.sleep(0.5)
    
    driver.close()


def main():
    # Test left leader (ACM3)
    print("\n" + "="*60)
    print("LEFT DYNAMIXEL LEADER (/dev/ttyACM3)")
    print("="*60)
    
    # From the X5 left config
    left_offsets = [3.894777220441643, 4.735398692202974, 1.5677283652191252, 
                    4.7139229611725755, 4.703185095657376, 4.70165111486949]
    left_signs = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
    
    test_dynamixel_reading(
        port="/dev/ttyACM3",
        joint_ids=[1, 2, 3, 4, 5, 6, 7],
        offsets=left_offsets,
        signs=left_signs
    )
    
    # Test right leader (ACM2)
    print("\n" + "="*60)
    print("RIGHT DYNAMIXEL LEADER (/dev/ttyACM2)")
    print("="*60)
    
    # Need to load right config
    import yaml
    config_path = Path(__file__).parent.parent / "third_party/configs/x5_auto_generated_right.yaml"
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        right_offsets = config['agent']['dynamixel_config']['joint_offsets']
        right_signs = config['agent']['dynamixel_config']['joint_signs']
    else:
        print(f"Warning: {config_path} not found, using default values")
        right_offsets = [0, 0, 0, 0, 0, 0]
        right_signs = [1, 1, 1, 1, 1, 1]
    
    test_dynamixel_reading(
        port="/dev/ttyACM2",
        joint_ids=[1, 2, 3, 4, 5, 6, 7],
        offsets=right_offsets[:6],
        signs=right_signs[:6]
    )


if __name__ == "__main__":
    main()