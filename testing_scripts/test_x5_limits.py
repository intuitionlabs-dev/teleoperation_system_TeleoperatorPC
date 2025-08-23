#!/usr/bin/env python3
"""Test X5 joint limits and command processing."""

import sys
import time
import numpy as np
from pathlib import Path

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_x5_joint_limits():
    """Test X5 joint limits and command clipping."""
    
    print("Testing X5 Joint Limits")
    print("=" * 60)
    
    # Test values that were being sent
    test_values = {
        "left": {
            "joint_0": 0.173,
            "joint_1": -0.248,  # Negative!
            "joint_2": -1.115,  # Negative!  
            "joint_3": -0.725,  # Negative!
            "joint_4": -0.099,
            "joint_5": -0.194,
            "joint_6": 1.0
        },
        "right": {
            "joint_0": -0.029,
            "joint_1": -0.015,
            "joint_2": -0.010,
            "joint_3": -0.012,
            "joint_4": -0.009,
            "joint_5": -0.019,
            "joint_6": 0.994
        }
    }
    
    # X5 typical joint limits (from ARX documentation)
    # These might be the actual limits causing the issue
    x5_joint_limits = [
        [-3.14, 3.14],  # Joint 0
        [0, 3.65],      # Joint 1 - NO NEGATIVE VALUES!
        [0, 3.14],      # Joint 2 - NO NEGATIVE VALUES!
        [-1.57, 1.57],  # Joint 3
        [-1.57, 1.57],  # Joint 4  
        [-2.09, 2.09],  # Joint 5
        [0, 1.0]        # Gripper
    ]
    
    print("\nX5 Joint Limits (suspected):")
    for i, limits in enumerate(x5_joint_limits):
        print(f"  Joint {i}: [{limits[0]:.2f}, {limits[1]:.2f}] rad")
    
    print("\nTesting LEFT arm commands:")
    for joint, value in test_values["left"].items():
        joint_idx = int(joint.split("_")[1])
        limits = x5_joint_limits[joint_idx]
        
        if value < limits[0] or value > limits[1]:
            clipped = np.clip(value, limits[0], limits[1])
            print(f"  {joint}: {value:.3f} rad -> OUT OF RANGE! Clipped to {clipped:.3f}")
        else:
            print(f"  {joint}: {value:.3f} rad -> OK")
    
    print("\nTesting RIGHT arm commands:")
    for joint, value in test_values["right"].items():
        joint_idx = int(joint.split("_")[1])
        limits = x5_joint_limits[joint_idx]
        
        if value < limits[0] or value > limits[1]:
            clipped = np.clip(value, limits[0], limits[1])
            print(f"  {joint}: {value:.3f} rad -> OUT OF RANGE! Clipped to {clipped:.3f}")
        else:
            print(f"  {joint}: {value:.3f} rad -> OK")
    
    print("\n" + "=" * 60)
    print("ISSUE IDENTIFIED:")
    print("=" * 60)
    print("X5 robots have joint limits where:")
    print("  - Joint 1 cannot go negative (min=0)")
    print("  - Joint 2 cannot go negative (min=0)")
    print("\nThe calibrated Dynamixel leaders are sending negative values")
    print("for these joints, which get clipped to 0, preventing movement.")
    print("\nSOLUTION:")
    print("1. Recalibrate with the arms in a position where joints 1,2 are positive")
    print("2. Or add an offset to ensure commands stay within valid range")
    print("3. Or check if X5 robot has different joint limit configuration")


if __name__ == "__main__":
    test_x5_joint_limits()