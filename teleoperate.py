#!/usr/bin/env python
"""Minimal teleoperation script for Teleoperator PC"""
import time
import argparse
from pathlib import Path
import sys

# Add path for imports
sys.path.append(str(Path(__file__).parent))

from bimanual_piper_client import BimanualPiperClient
from bimanual_piper_client_config import BimanualPiperClientConfig
from so101_teleoperator import SO101Teleoperator


def main():
    parser = argparse.ArgumentParser()
    # Only bimanual configuration is supported
    parser.add_argument("--robot-hostname", type=str, default="192.168.123.139",
                       help="Hostname/IP of the Robot PC")
    parser.add_argument("--cmd-port", type=int, default=5555)
    parser.add_argument("--fps", type=int, default=30,
                       help="Target teleoperation frequency")
    parser.add_argument("--left-leader-port", type=str, default="/dev/ttyACM0",
                       help="Left SO101 leader port")
    parser.add_argument("--right-leader-port", type=str, default="/dev/ttyACM1", 
                       help="Right SO101 leader port")
    parser.add_argument("--calibration-dir", type=str, default="./calibration",
                       help="Directory to store calibration files")
    parser.add_argument("--left-arm-calib-name", type=str, default="left_arm",
                       help="Name for left arm calibration file")
    parser.add_argument("--right-arm-calib-name", type=str, default="right_arm",
                       help="Name for right arm calibration file")
    parser.add_argument("--calibrate", action="store_true",
                       help="Run calibration mode")
    
    args = parser.parse_args()
    
    print(f"Starting minimal teleoperation...")
    print(f"Robot PC: {args.robot_hostname}:{args.cmd_port}")
    print(f"Target FPS: {args.fps}")
    print()
    
    # Create bimanual robot client
    config = BimanualPiperClientConfig(
        hostname=args.robot_hostname,
        cmd_port=args.cmd_port
    )
    robot = BimanualPiperClient(config)
    
    # Create teleoperator
    teleop = SO101Teleoperator(
        left_port=args.left_leader_port,
        right_port=args.right_leader_port,
        calibration_dir=args.calibration_dir,
        left_calib_name=args.left_arm_calib_name,
        right_calib_name=args.right_arm_calib_name
    )
    
    # Connect to leader arms
    print("Connecting to SO101 leader arms...")
    teleop.connect()
    
    # Check if calibration mode
    if args.calibrate:
        print("\n=== CALIBRATION MODE ===")
        teleop.calibrate()
        print("\nCalibration complete! You can now run teleoperation.")
        teleop.disconnect()
        return
    
    # Normal teleoperation mode
    print("Connecting to robot...")
    robot.connect()
    
    print("\nTeleoperation ready! Press Ctrl+C to stop.")
    print("=" * 50)
    
    # Main teleoperation loop
    loop_time = 1.0 / args.fps
    stats_time = time.time()
    cmd_count = 0
    
    try:
        while True:
            loop_start = time.time()
            
            # Step 1: Get action from teleoperator (GELLO)
            action = teleop.get_action()
            
            # Step 2: Send action to robot
            robot.send_action(action)
            cmd_count += 1
            
            # Rate limiting
            elapsed = time.time() - loop_start
            if elapsed < loop_time:
                time.sleep(loop_time - elapsed)
            
            # Print stats every 2 seconds
            if time.time() - stats_time > 2.0:
                duration = time.time() - stats_time
                cmd_rate = cmd_count / duration
                
                print(f"Commands: {cmd_rate:.1f} Hz")
                
                stats_time = time.time()
                cmd_count = 0
    
    except KeyboardInterrupt:
        print("\n\nStopping teleoperation...")
    
    finally:
        # Cleanup
        teleop.disconnect()
        robot.disconnect()
        print("Teleoperation stopped.")


if __name__ == "__main__":
    main()
