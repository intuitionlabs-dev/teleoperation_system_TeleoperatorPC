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
from gello_teleoperator import GelloTeleoperator


def main():
    parser = argparse.ArgumentParser()
    # Only bimanual configuration is supported
    parser.add_argument("--robot-hostname", type=str, default="192.168.123.139",
                       help="Hostname/IP of the Robot PC")
    parser.add_argument("--cmd-port", type=int, default=5555)
    parser.add_argument("--obs-port", type=int, default=5556)
    parser.add_argument("--fps", type=int, default=30,
                       help="Target teleoperation frequency")
    parser.add_argument("--gello-left-port", type=str, default="/dev/GELLO_L",
                       help="Left GELLO device port")
    parser.add_argument("--gello-right-port", type=str, default="/dev/GELLO_R", 
                       help="Right GELLO device port")
    
    args = parser.parse_args()
    
    print(f"Starting minimal teleoperation...")
    print(f"Robot PC: {args.robot_hostname}:{args.cmd_port}/{args.obs_port}")
    print(f"Target FPS: {args.fps}")
    print()
    
    # Create bimanual robot client
    config = BimanualPiperClientConfig(
        hostname=args.robot_hostname,
        cmd_port=args.cmd_port,
        obs_port=args.obs_port
    )
    robot = BimanualPiperClient(config)
    
    # Create teleoperator
    teleop = GelloTeleoperator(
        left_port=args.gello_left_port,
        right_port=args.gello_right_port
    )
    
    # Connect everything
    print("Connecting to robot...")
    robot.connect()
    
    print("Connecting to GELLO...")
    teleop.connect()
    
    print("\nTeleoperation ready! Press Ctrl+C to stop.")
    print("=" * 50)
    
    # Main teleoperation loop
    loop_time = 1.0 / args.fps
    stats_time = time.time()
    cmd_count = 0
    obs_count = 0
    
    try:
        while True:
            loop_start = time.time()
            
            # Step 1: Get action from teleoperator (GELLO)
            action = teleop.get_action()
            
            # Step 2: Send action to robot
            robot.send_action(action)
            cmd_count += 1
            
            # Step 3: Get observation (optional - don't block on it)
            try:
                obs = robot.get_observation()
                if obs:
                    obs_count += 1
            except Exception as e:
                # Don't let observation errors stop teleoperation
                pass
            
            # Rate limiting
            elapsed = time.time() - loop_start
            if elapsed < loop_time:
                time.sleep(loop_time - elapsed)
            
            # Print stats every 2 seconds
            if time.time() - stats_time > 2.0:
                duration = time.time() - stats_time
                cmd_rate = cmd_count / duration
                obs_rate = obs_count / duration
                
                print(f"Cmd: {cmd_rate:.1f} Hz | Obs: {obs_rate:.1f} Hz")
                
                stats_time = time.time()
                cmd_count = 0
                obs_count = 0
    
    except KeyboardInterrupt:
        print("\n\nStopping teleoperation...")
    
    finally:
        # Cleanup
        teleop.disconnect()
        robot.disconnect()
        print("Teleoperation stopped.")


if __name__ == "__main__":
    main()
