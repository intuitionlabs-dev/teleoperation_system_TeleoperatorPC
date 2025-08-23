#!/usr/bin/env python3
"""
X5-Dynamixel Calibration Tool

This script calibrates the X5 robot arms with Dynamixel leader arms.
It captures the current positions when both arms are in a known configuration
and calculates the necessary offsets and signs for proper teleoperation.
"""

import argparse
import time
import numpy as np
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
import sys

# Add gello to path
sys.path.append(str(Path(__file__).parent / "third_party"))

from gello.robots.dynamixel import DynamixelRobot
from gello.robots.x5 import X5Robot
from dynamixel_sdk import *


def get_leader_positions(port: str, baudrate: int = 57600) -> np.ndarray:
    """Get current positions from Dynamixel leader arm."""
    robot = DynamixelRobot(
        port=port,
        baudrate=baudrate,
        joint_ids=[1, 2, 3, 4, 5, 6, 7],
        real=True
    )
    
    # get_joint_state() returns positions directly (not a tuple)
    positions = robot.get_joint_state()
    
    # Debug print to see what we're getting
    print(f"Raw positions from Dynamixel: {positions}")
    print(f"Type: {type(positions)}, Shape: {positions.shape if isinstance(positions, np.ndarray) else 'not array'}")
    
    # During calibration, ensure gripper is open (position = 1.0 in normalized space)
    if isinstance(positions, np.ndarray) and len(positions) == 7:
        positions[-1] = 1.0  # Set gripper to fully open for calibration
        print(f"Set leader gripper to open position (1.0) for calibration")
    
    # Ensure we have an array of 7 values
    if not isinstance(positions, np.ndarray):
        print(f"WARNING: Positions is not an array, got {type(positions)}")
        positions = np.zeros(7)  # Return zeros if we can't read
    elif len(positions) != 7:
        print(f"WARNING: Expected 7 joint positions, got {len(positions)}")
        if len(positions) == 1:
            # If we only got one value, it might be an error
            print("Only received one position value - check Dynamixel connection")
            positions = np.zeros(7)
    
    print(f"Leader joint positions (processed): {positions}")
    return positions


def get_follower_positions(channel: str) -> np.ndarray:
    """Get current positions from X5 follower arm."""
    try:
        # Add delay before initializing X5 to ensure CAN is ready
        print(f"Waiting for CAN interface {channel} to be ready...")
        time.sleep(2)
        
        robot = X5Robot(channel=channel)
        
        # Try multiple times to read positions
        for attempt in range(3):
            positions_velocities = robot.get_joint_state()
            if isinstance(positions_velocities, tuple):
                positions = positions_velocities[0]
            else:
                positions = positions_velocities
            
            # Check if we got valid positions
            if isinstance(positions, np.ndarray) and not np.all(positions == 0.0):
                # X5 returns 6 joints, add gripper placeholder
                if len(positions) == 6:
                    positions = np.append(positions, 1.0)  # 1.0 = fully open
                    print(f"Follower joint positions (6 arm + gripper): {positions}")
                    return positions
            
            print(f"Attempt {attempt+1}: Got zero positions, retrying...")
            time.sleep(1)
        
        # If all attempts failed
        print("ERROR: Could not read X5 positions after 3 attempts!")
        print("Please check:")
        print("  1. X5 arms are powered ON")
        print("  2. CAN interfaces are configured (sudo ip link set can0/can1 up type can bitrate 1000000)")
        print("  3. X5 motor drivers are enabled")
        
        # Return placeholder values to continue
        positions = np.zeros(7)
        positions[-1] = 1.0  # Set gripper to open
        return positions
        
    except Exception as e:
        print(f"Error reading follower positions: {e}")
        print("Make sure X5 arms are powered and CAN is configured!")
        # Return zeros if we can't read positions
        positions = np.zeros(7)
        positions[-1] = 1.0
        return positions


def calibrate_arm(
    leader_port: str,
    follower_channel: str,
    arm_name: str,
    reference_position: str = "neutral"
) -> Dict:
    """
    Calibrate a single arm by capturing positions and calculating offsets.
    
    Args:
        leader_port: Serial port for Dynamixel leader (e.g., /dev/ttyACM2)
        follower_channel: CAN channel for X5 follower (e.g., can0)
        arm_name: Name of the arm (left/right)
        reference_position: Reference position name (neutral/zero)
    
    Returns:
        Dictionary with calibration data
    """
    print(f"\n{'='*60}")
    print(f"Calibrating {arm_name.upper()} arm")
    print(f"{'='*60}")
    print(f"Leader port: {leader_port}")
    print(f"Follower channel: {follower_channel}")
    
    print(f"\nPlease position both {arm_name} arms in {reference_position} position.")
    print("IMPORTANT: Both grippers should be OPEN during calibration!")
    print("The leader and follower should be in matching poses with OPEN grippers.")
    input("Press Enter when ready...")
    
    # Create ONE DynamixelRobot instance that we'll use throughout calibration
    print("\nInitializing leader robot...")
    leader_robot = DynamixelRobot(
        port=leader_port,
        baudrate=57600,
        joint_ids=[1, 2, 3, 4, 5, 6, 7],
        real=True
    )
    
    # Capture positions using the robot instance directly
    print("\nCapturing positions...")
    leader_pos = leader_robot.get_joint_state()
    print(f"Leader joint positions: {leader_pos}")
    
    # During calibration, ensure gripper is open (position = 1.0 in normalized space)
    if isinstance(leader_pos, np.ndarray) and len(leader_pos) == 7:
        leader_pos[-1] = 1.0  # Set gripper to fully open for calibration
        print(f"Set leader gripper to open position (1.0) for calibration")
    
    follower_pos = get_follower_positions(follower_channel)
    
    print(f"\nLeader positions (rad): {leader_pos}")
    print(f"Follower positions (rad): {follower_pos}")
    
    # Ensure positions are numpy arrays
    if not isinstance(leader_pos, np.ndarray):
        leader_pos = np.array([leader_pos] * 7 if np.isscalar(leader_pos) else leader_pos)
    if not isinstance(follower_pos, np.ndarray):
        follower_pos = np.array([follower_pos] * 7 if np.isscalar(follower_pos) else follower_pos)
    
    # Calculate offsets (leader - follower)
    offsets = leader_pos - follower_pos
    
    # Use known joint signs for X5 (joints 2 and 3 need to be inverted)
    # This avoids the need for interactive calibration which can cause gripper issues
    signs = np.array([1.0, -1.0, -1.0, 1.0, 1.0, 1.0, 1.0])
    
    print("\n--- Using Known Joint Signs ---")
    print("Joint signs for X5: [1.0, -1.0, -1.0, 1.0, 1.0, 1.0, 1.0]")
    print("(Joints 2 and 3 are inverted for proper following)")
    
    # Capture gripper range - REUSE the existing leader_robot instead of creating a new one
    print("\n--- Gripper Range Calibration ---")
    print("Now we'll calibrate the gripper range.")
    print("Using existing leader robot instance (no new connection needed)...")
    
    input("Please CLOSE the leader gripper completely and press Enter...")
    closed_positions = leader_robot.get_joint_state()  # Use existing leader_robot
    closed_pos = closed_positions[6] if len(closed_positions) > 6 else 1.0
    closed_deg = closed_pos * 180.0 / np.pi if closed_pos != 1.0 else 235.0  # Convert to degrees
    
    input("Please OPEN the leader gripper completely and press Enter...")
    open_positions = leader_robot.get_joint_state()  # Use existing leader_robot
    open_pos = open_positions[6] if len(open_positions) > 6 else 1.0
    open_deg = open_pos * 180.0 / np.pi if open_pos != 1.0 else 258.0  # Convert to degrees
    
    print(f"Gripper range: closed={closed_deg:.1f}°, open={open_deg:.1f}°")
    # Convert numpy types to Python native types to avoid YAML serialization issues
    gripper_config = [7, float(closed_deg), float(open_deg)]  # [id, close_pos, open_pos]
    
    # Create calibration data - ensure all arrays are converted to Python native types
    # This prevents numpy scalar serialization issues in YAML
    def to_python_list(arr):
        """Convert numpy array to Python list with native types."""
        if isinstance(arr, np.ndarray):
            return [float(x) for x in arr]
        return [float(arr)] * 7
    
    calibration = {
        "arm": arm_name,
        "leader_port": leader_port,
        "follower_channel": follower_channel,
        "reference_position": reference_position,
        "joint_offsets": to_python_list(offsets),
        "joint_signs": to_python_list(signs),
        "gripper_config": gripper_config,  # Already converted to native types
        "leader_positions": to_python_list(leader_pos),
        "follower_positions": to_python_list(follower_pos),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return calibration


def save_calibration(calibration: Dict, output_dir: Path):
    """Save calibration to YAML file."""
    arm_name = calibration["arm"]
    filename = f"x5_calibration_{arm_name}.yaml"
    filepath = output_dir / filename
    
    with open(filepath, 'w') as f:
        yaml.dump(calibration, f, default_flow_style=False)
    
    print(f"\nCalibration saved to: {filepath}")
    return filepath


def create_auto_config(calibration: Dict, config_dir: Path):
    """Create auto-generated config file for teleoperation."""
    arm_name = calibration["arm"]
    
    # Create config matching expected format
    config = {
        "agent": {
            "_target_": "gello.agents.gello_agent.GelloAgent",
            "dynamixel_config": {
                "_target_": "gello.agents.gello_agent.DynamixelRobotConfig",
                "joint_ids": [1, 2, 3, 4, 5, 6, 7],
                "joint_offsets": calibration["joint_offsets"],
                "joint_signs": calibration["joint_signs"],
                "gripper_config": calibration.get("gripper_config", [7, 235.0, 258.0])  # Use calibrated gripper range
            },
            "port": calibration["leader_port"],
            "start_joints": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        },
        "hz": 60,
        "max_steps": 1000,
        "robot": {
            "_target_": "gello.robots.x5.X5Robot",
            "channel": calibration["follower_channel"]
        },
        # Keep these for backward compatibility
        "dof": 7,
        "home_offset": calibration["joint_offsets"],
        "joint_signs": calibration["joint_signs"],
        "timestamp": calibration["timestamp"]
    }
    
    # Helper for flow-style lists in YAML
    class FlowList(list):
        pass
    
    def flow_representer(dumper, data):
        return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)
    
    yaml.add_representer(FlowList, flow_representer)
    
    # Convert lists to FlowList for cleaner YAML output
    config["agent"]["dynamixel_config"]["joint_ids"] = FlowList([1, 2, 3, 4, 5, 6])
    config["agent"]["dynamixel_config"]["joint_offsets"] = FlowList(calibration["joint_offsets"][:6])
    config["agent"]["dynamixel_config"]["joint_signs"] = FlowList(calibration["joint_signs"][:6])
    config["agent"]["dynamixel_config"]["gripper_config"] = FlowList(calibration.get("gripper_config", [7, 235.0, 258.0]))
    config["agent"]["start_joints"] = FlowList([0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    config["home_offset"] = FlowList(calibration["joint_offsets"])
    config["joint_signs"] = FlowList(calibration["joint_signs"])
    
    # Save auto-generated config
    auto_filename = f"x5_auto_generated_{arm_name}.yaml"
    auto_filepath = config_dir / auto_filename
    
    with open(auto_filepath, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"Auto-config saved to: {auto_filepath}")
    
    # Also save as x5_calibrated_*.yaml for direct use
    calibrated_filename = f"x5_calibrated_{arm_name}.yaml"
    calibrated_filepath = config_dir / calibrated_filename
    
    with open(calibrated_filepath, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"Calibrated config saved to: {calibrated_filepath}")
    
    return calibrated_filepath


def main():
    parser = argparse.ArgumentParser(description="Calibrate X5-Dynamixel teleoperation system")
    parser.add_argument(
        "--arms",
        nargs="+",
        choices=["left", "right", "both"],
        default=["both"],
        help="Which arms to calibrate"
    )
    parser.add_argument(
        "--left-leader-port",
        default="/dev/ttyACM3",
        help="Serial port for left Dynamixel leader"
    )
    parser.add_argument(
        "--right-leader-port",
        default="/dev/ttyACM2",
        help="Serial port for right Dynamixel leader"
    )
    parser.add_argument(
        "--left-follower-channel",
        default="can1",
        help="CAN channel for left X5 follower"
    )
    parser.add_argument(
        "--right-follower-channel",
        default="can0",
        help="CAN channel for right X5 follower"
    )
    parser.add_argument(
        "--reference",
        default="neutral",
        help="Reference position name (neutral/zero/custom)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(__file__).parent / "calibration",
        help="Directory to save calibration files"
    )
    
    args = parser.parse_args()
    
    # Create output directories
    args.output_dir.mkdir(exist_ok=True)
    config_dir = Path(__file__).parent / "third_party" / "configs"
    config_dir.mkdir(exist_ok=True)
    
    print("\n" + "="*60)
    print("X5-DYNAMIXEL CALIBRATION TOOL")
    print("="*60)
    print("\nThis tool will calibrate the X5 follower arms with Dynamixel leaders.")
    print("Make sure both systems are powered on and connected.")
    print("\nIMPORTANT: Position both leader and follower arms in the same pose")
    print("before capturing positions. This establishes the offset mapping.")
    
    calibrations = []
    
    # Calibrate requested arms
    arms_to_calibrate = args.arms if args.arms != ["both"] else ["left", "right"]
    
    for arm in arms_to_calibrate:
        if arm == "left":
            cal = calibrate_arm(
                leader_port=args.left_leader_port,
                follower_channel=args.left_follower_channel,
                arm_name="left",
                reference_position=args.reference
            )
        elif arm == "right":
            cal = calibrate_arm(
                leader_port=args.right_leader_port,
                follower_channel=args.right_follower_channel,
                arm_name="right",
                reference_position=args.reference
            )
        else:
            continue
        
        calibrations.append(cal)
        
        # Save calibration
        save_calibration(cal, args.output_dir)
        
        # Create auto-generated config
        create_auto_config(cal, config_dir)
    
    # Summary
    print("\n" + "="*60)
    print("CALIBRATION COMPLETE")
    print("="*60)
    
    for cal in calibrations:
        arm = cal["arm"]
        print(f"\n{arm.upper()} ARM:")
        print(f"  Offsets: {[f'{o:.3f}' for o in cal['joint_offsets']]}")
        print(f"  Signs: {cal['joint_signs']}")
    
    print("\nYou can now use these calibration files with teleoperate.py")
    print("The system will automatically load the calibrated values.")
    
    # Test option
    if input("\nWould you like to test the calibration now? (y/n): ").lower() == 'y':
        print("\nTo test, run:")
        print("  ./run_teleoperate.sh x5-dynamixel")
        print("\nThe calibrated values will be automatically applied.")


if __name__ == "__main__":
    main()