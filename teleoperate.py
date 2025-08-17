#!/usr/bin/env python
"""
Main teleoperation script for controlling bimanual Piper robots with SO101 leaders.
"""

import logging
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from pprint import pformat

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
    # Robot parameters
    remote_ip: str = "100.117.16.87"
    
    # Teleop parameters
    left_arm_port_teleop: str = "/dev/ttyACM0"
    right_arm_port_teleop: str = "/dev/ttyACM1"
    teleop_calibration_dir: Path | None = None
    
    # Calibration file base names (without .json)
    left_arm_calib_name: str = "my_left"
    right_arm_calib_name: str = "my_right"
    
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
    
    if cfg.bimanual:
        # Configure bimanual robot client
        robot_config = BimanualPiperClientConfig(remote_ip=cfg.remote_ip)
        
        # Configure bimanual SO101 teleoperator
        teleop_config = BimanualSO101LeaderConfig(
            left_arm=SO101LeaderConfig(port=cfg.left_arm_port_teleop),
            right_arm=SO101LeaderConfig(port=cfg.right_arm_port_teleop),
            calibration_dir=cfg.teleop_calibration_dir,
            left_calib_name=cfg.left_arm_calib_name,
            right_calib_name=cfg.right_arm_calib_name,
            id="bimanual",
        )
    else:
        raise NotImplementedError("Single arm teleoperation not implemented yet")
    
    robot = BimanualPiperClient(robot_config)
    teleop = BimanualSO101Leader(teleop_config)
    
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