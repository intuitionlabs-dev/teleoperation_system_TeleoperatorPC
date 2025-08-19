#!/usr/bin/env python
"""
Main teleoperation script for controlling bimanual robots (Piper or YAM) with various leaders.
"""

import logging
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
    yam_left_config: str = "/home/francesco/meta-tele-RTX/clean_version/i2rt/gello_software/configs/yam_auto_generated_left.yaml"
    yam_right_config: str = "/home/francesco/meta-tele-RTX/clean_version/i2rt/gello_software/configs/yam_auto_generated_right.yaml"
    
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
                config_path=cfg.yam_left_config,
                hardware_port=6001,
                id="left"
            ),
            right_arm=DynamixelLeaderConfig(
                config_path=cfg.yam_right_config,
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