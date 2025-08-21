#!/usr/bin/env python
"""
Main teleoperation script for controlling bimanual robots (Piper or YAM) with various leaders.
"""

import logging
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from pprint import pformat
from typing import Literal

import draccus

from robots.bimanual_piper_client import BimanualPiperClient
from robots.config import BimanualPiperClientConfig
from teleoperators.bimanual_so101 import BimanualSO101Leader
from teleoperators.bimanual_so101.config import BimanualSO101LeaderConfig
from teleoperators.so101.config import SO101LeaderConfig
from utils.robot_utils import busy_wait, move_cursor_up
from utils.logging_utils import init_logging


@dataclass
class TeleoperateConfig:
    """Configuration for the teleoperation script."""
    # System selection
    system: Literal["piper-so101", "yam-dynamixel"] = "piper-so101"
    """Which teleoperation system to use."""
    
    # Robot parameters
    remote_ip: str = "100.117.16.87"
    
    # SO101 teleop parameters (for piper-so101 system)
    left_arm_port_teleop: str = "/dev/ttyACM0"
    right_arm_port_teleop: str = "/dev/ttyACM1"
    teleop_calibration_dir: Path | None = None
    
    # Calibration file base names (without .json)
    left_arm_calib_name: str = "my_left"
    right_arm_calib_name: str = "my_right"
    
    # YAM-Dynamixel parameters
    yam_left_port: str = "/dev/ttyACM0"
    yam_right_port: str = "/dev/ttyACM1"
    yam_left_config: str = "third_party/configs/yam_auto_generated_left.yaml"
    yam_right_config: str = "third_party/configs/yam_auto_generated_right.yaml"
    
    # General parameters
    bimanual: bool = True
    fps: int = 60
    teleop_time_s: int | None = None


def teleop_loop(teleop, robot, fps: int, duration: int | None = None):
    """Main teleoperation control loop."""
    display_len = max(len(key) for key in robot.action_features)
    start = time.perf_counter()
    
    while True:
        loop_start = time.perf_counter()
        action = teleop.get_action()
        
        if not action:
            print("Waiting for teleoperator data...")
            busy_wait(1 / fps)
            continue
        
        robot.send_action(action)
        dt_s = time.perf_counter() - loop_start
        busy_wait(1 / fps - dt_s)
        
        loop_s = time.perf_counter() - loop_start
        
        # Display action values
        print("\n" + "-" * (display_len + 10))
        print(f"{'NAME':<{display_len}} | {'NORM':>7}")
        for motor, value in action.items():
            print(f"{motor:<{display_len}} | {value:>7.2f}")
        print(f"\ntime: {loop_s * 1e3:.2f}ms ({1 / loop_s:.0f} Hz)")
        
        if duration is not None and time.perf_counter() - start >= duration:
            return
        
        move_cursor_up(len(action) + 5)


def _update_yam_config_port(config_path: str, port: str):
    """Update the port in a YAM configuration file if needed."""
    import yaml
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check if port needs updating
        if 'agent' in config and 'port' in config['agent']:
            if config['agent']['port'] != port:
                logging.info(f"Updating port in {config_path} from {config['agent']['port']} to {port}")
                config['agent']['port'] = port
                
                # Write back the updated config
                with open(config_path, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
    except Exception as e:
        logging.warning(f"Could not update port in {config_path}: {e}")


@draccus.wrap()
def teleoperate(cfg: TeleoperateConfig):
    """Main teleoperation entry point."""
    init_logging()
    logging.info(pformat(asdict(cfg)))
    
    if not cfg.bimanual:
        raise NotImplementedError("Single arm teleoperation not implemented yet")
    
    if cfg.system == "piper-so101":
        # Configure bimanual Piper robot with SO101 leaders
        robot_config = BimanualPiperClientConfig(remote_ip=cfg.remote_ip)
        robot = BimanualPiperClient(robot_config)
        
        # Configure bimanual SO101 teleoperator
        teleop_config = BimanualSO101LeaderConfig(
            left_arm=SO101LeaderConfig(port=cfg.left_arm_port_teleop),
            right_arm=SO101LeaderConfig(port=cfg.right_arm_port_teleop),
            calibration_dir=cfg.teleop_calibration_dir,
            left_calib_name=cfg.left_arm_calib_name,
            right_calib_name=cfg.right_arm_calib_name,
            id="bimanual",
        )
        teleop = BimanualSO101Leader(teleop_config)
        
    elif cfg.system == "yam-dynamixel":
        # Configure bimanual YAM robot with Dynamixel leaders
        from teleoperators.bimanual_dynamixel import BimanualDynamixelLeader
        from teleoperators.bimanual_dynamixel.config import BimanualDynamixelLeaderConfig, DynamixelLeaderConfig
        import os
        import subprocess
        
        # Handle relative paths for config files
        base_dir = Path(__file__).parent
        if Path(cfg.yam_left_config).is_absolute():
            left_config_path = Path(cfg.yam_left_config)
            right_config_path = Path(cfg.yam_right_config)
        else:
            left_config_path = (base_dir / cfg.yam_left_config).resolve()
            right_config_path = (base_dir / cfg.yam_right_config).resolve()
        
        # Check if YAM config files exist, if not prompt for calibration
        configs_exist = left_config_path.exists() and right_config_path.exists()
        
        if not configs_exist:
            print("\n" + "="*60)
            print("YAM Configuration Not Found")
            print("="*60)
            print("\nThe YAM arm configuration files have not been generated yet.")
            print("Please run the calibration process first:\n")
            print("1. Position both YAM arms in their default build position")
            print("   (straight up, as shown in the documentation)\n")
            print("2. Run the following commands:")
            print(f"   cd /home/francesco/meta-tele-RTX/clean_version/i2rt/gello_software")
            print(f"   source .venv/bin/activate")
            print(f"   python scripts/generate_yam_config.py --port {cfg.yam_left_port} --output-path configs/yam_auto_generated_left.yaml")
            print(f"   python scripts/generate_yam_config.py --port {cfg.yam_right_port} --output-path configs/yam_auto_generated_right.yaml\n")
            print("3. After calibration, run this teleoperation script again.")
            print("="*60)
            sys.exit(1)
        
        # Update config files with correct ports if specified
        # This allows overriding the port without regenerating the entire config
        _update_yam_config_port(str(left_config_path), cfg.yam_left_port)
        _update_yam_config_port(str(right_config_path), cfg.yam_right_port)
        
        # For YAM system, use different ports to avoid conflicts
        robot_config = BimanualPiperClientConfig(
            remote_ip=cfg.remote_ip,
            port_zmq_cmd=5565,  # YAM uses 5565-5568 instead of 5555-5558
            port_zmq_observations=5566
        )
        robot = BimanualPiperClient(robot_config)
        
        # Configure bimanual Dynamixel teleoperator
        teleop_config = BimanualDynamixelLeaderConfig(
            left_arm=DynamixelLeaderConfig(
                config_path=str(left_config_path),
                hardware_port=6001,
                id="left"
            ),
            right_arm=DynamixelLeaderConfig(
                config_path=str(right_config_path),
                hardware_port=6002,
                id="right"
            ),
            id="bimanual",
        )
        teleop = BimanualDynamixelLeader(teleop_config)
        
    else:
        raise ValueError(f"Unknown system: {cfg.system}")
    
    logging.info(f"Starting {cfg.system} teleoperation system")
    
    teleop.connect()
    robot.connect()
    
    try:
        teleop_loop(teleop, robot, cfg.fps, duration=cfg.teleop_time_s)
    except KeyboardInterrupt:
        pass
    finally:
        teleop.disconnect()
        robot.disconnect()


if __name__ == "__main__":
    teleoperate()