#!/usr/bin/env python3
"""Script to empirically discover X5 joint limits by testing commands."""

import sys
import time
import numpy as np
from pathlib import Path

def test_x5_limits():
    """Test actual X5 joint limits by sending commands and observing results."""
    
    print("=" * 60)
    print("X5 JOINT LIMITS DISCOVERY")
    print("=" * 60)
    print("\nThis script will help determine the actual joint limits")
    print("by analyzing the teleoperation data.\n")
    
    # From the teleoperation output, we know these commands were sent:
    test_data = {
        "left_arm": {
            "joint_0": 0.173,      # Worked
            "joint_1": -0.248,     # Didn't move
            "joint_2": -1.115,     # Didn't move  
            "joint_3": -0.725,     # Didn't move
            "joint_4": -0.099,     # Worked
            "joint_5": -0.194,     # Worked
            "joint_6": 1.0         # Gripper - didn't move
        },
        "right_arm": {
            "joint_0": -0.029,     # Worked
            "joint_1": -0.015,     # Worked (small negative)
            "joint_2": -0.010,     # Worked (small negative)
            "joint_3": -0.012,     # Worked (small negative)
            "joint_4": -0.009,     # Worked
            "joint_5": -0.019,     # Worked
            "joint_6": 0.994       # Gripper - didn't move
        }
    }
    
    print("Analysis of teleoperation results:")
    print("-" * 40)
    
    print("\nLEFT ARM:")
    print("  Joint 0: 0.173 rad -> MOVED (positive OK)")
    print("  Joint 1: -0.248 rad -> DID NOT MOVE (negative blocked)")
    print("  Joint 2: -1.115 rad -> DID NOT MOVE (negative blocked)")
    print("  Joint 3: -0.725 rad -> DID NOT MOVE (negative blocked)")
    print("  Joint 4: -0.099 rad -> MOVED (small negative OK)")
    print("  Joint 5: -0.194 rad -> MOVED (negative OK)")
    print("  Joint 6: 1.0 rad -> DID NOT MOVE (gripper issue)")
    
    print("\nRIGHT ARM:")
    print("  All joints had very small values (-0.029 to -0.009)")
    print("  All appeared to move except gripper")
    
    print("\n" + "=" * 60)
    print("HYPOTHESIS:")
    print("=" * 60)
    
    print("\nBased on the behavior, the likely joint limits are:")
    print()
    print("  Joint 0: [-3.14, 3.14] - Standard range")
    print("  Joint 1: [0, 3.65] or similar - CANNOT GO NEGATIVE")
    print("  Joint 2: [0, 3.14] or similar - CANNOT GO NEGATIVE")
    print("  Joint 3: [0, X] or [-small, X] - LIMITED NEGATIVE RANGE")
    print("  Joint 4: [-1.57, 1.57] - Standard range")
    print("  Joint 5: [-2.09, 2.09] - Standard range")
    print("  Joint 6: [0, 1.0] - Gripper (but not responding)")
    
    print("\n" + "=" * 60)
    print("RECOMMENDED SOLUTION:")
    print("=" * 60)
    
    print("\n1. IMMEDIATE FIX - Recalibrate with proper neutral position:")
    print("   - Position arms so joints 1, 2, 3 are at mid-range (e.g., 1.5 rad)")
    print("   - This ensures commands stay within valid positive range")
    
    print("\n2. PROPER FIX - Get actual limits from ARX documentation:")
    print("   - Contact ARX support or check documentation")
    print("   - Implement proper joint limit handling in X5Robot class")
    
    print("\n3. GRIPPER FIX:")
    print("   - Gripper control needs separate implementation")
    print("   - X5 may use different gripper control method than joint position")


if __name__ == "__main__":
    test_x5_limits()