from typing import Dict
import sys
import os

import numpy as np

from gello.robots.robot import Robot


class X5Robot(Robot):
    """A class representing an ARX X5 robot."""

    def __init__(self, channel="can0"):
        import time
        
        # Add ARX X5 Python path
        arx_path = "/home/group/i2rt/ARX-dynamixel/RobotLearningGello/ARX_X5/py"
        if arx_path not in sys.path:
            sys.path.insert(0, arx_path)
        
        # Import SingleArm from ARX
        from arx_x5_python.bimanual.script.single_arm import SingleArm
        
        # For X5, use direct CAN port mapping
        # can0 = right arm, can1 = left arm
        can_port = channel
        if channel == "can0":
            # Add delay for right arm to prevent CAN conflicts
            print(f"Adding 2 second delay for {channel} to prevent CAN initialization conflicts...")
            time.sleep(2)
        
        # Initialize X5 robot with config
        config = {
            "can_port": can_port,
            "type": 0,  # 0 for X5 robot
            "num_joints": 7,
            "dt": 0.05
        }
        print(f"Initializing X5 robot on {can_port}...")
        self.robot = SingleArm(config)

        # X5 has 7 joints (6 arm joints + 1 gripper)
        self._joint_names = [
            "joint1",
            "joint2",
            "joint3",
            "joint4",
            "joint5",
            "joint6",
            "gripper",
        ]
        self._joint_state = np.zeros(7)  # 7 joints
        self._joint_velocities = np.zeros(7)  # 7 joints
        self._gripper_state = 0.0

    def num_dofs(self) -> int:
        return 7  # X5 has 7 DOFs

    def get_joint_state(self) -> np.ndarray:
        # Get actual joint positions from X5 robot (6 arm joints + 1 gripper)
        try:
            joint_pos = self.robot.get_joint_positions()
            
            # Handle various return types
            if joint_pos is None:
                print("Warning: get_joint_positions() returned None")
                joint_pos = np.zeros(6)
            elif isinstance(joint_pos, (int, float)):
                print(f"Warning: get_joint_positions() returned single value: {joint_pos}")
                joint_pos = np.zeros(6)
            elif isinstance(joint_pos, list):
                joint_pos = np.array(joint_pos)
                if len(joint_pos) != 6:
                    print(f"Warning: Expected 6 joints, got {len(joint_pos)}")
                    joint_pos = np.zeros(6)
            elif isinstance(joint_pos, np.ndarray):
                if len(joint_pos) != 6:
                    print(f"Warning: Expected 6 joints, got {len(joint_pos)}")
                    joint_pos = np.zeros(6)
            else:
                print(f"Warning: Unexpected type from get_joint_positions(): {type(joint_pos)}")
                joint_pos = np.zeros(6)
            
            # X5 returns 6 joints, add gripper as 7th joint (default to open)
            joint_pos = np.append(joint_pos, self._gripper_state)
            
            self._joint_state = joint_pos
            return self._joint_state
        except Exception as e:
            print(f"Error in get_joint_state: {e}")
            return np.zeros(7)

    def command_joint_state(self, joint_state: np.ndarray) -> None:
        assert (
            len(joint_state) == self.num_dofs()
        ), f"Expected {self.num_dofs()} joint values, got {len(joint_state)}"

        dt = 0.01
        self._joint_velocities = (joint_state - self._joint_state) / dt
        self._joint_state = joint_state

        # Command the X5 robot with all 7 joints (6 arm + 1 gripper)
        self.command_joint_pos(joint_state)

    def get_observations(self) -> Dict[str, np.ndarray]:
        ee_pos_quat = np.zeros(7)  # Placeholder for FK
        return {
            "joint_positions": self._joint_state,
            "joint_velocities": self._joint_velocities,
            "ee_pos_quat": ee_pos_quat,
            "gripper_position": np.array([self._gripper_state]),
        }

    def get_joint_pos(self):
        # Get 6 joints from X5 robot and add gripper
        joint_pos = self.robot.get_joint_positions()
        joint_pos = np.append(joint_pos, self._gripper_state)
        return joint_pos

    def command_joint_pos(self, target_pos):
        # X5 expects 6 joints, extract gripper separately
        if len(target_pos) >= 7:
            arm_pos = target_pos[:6]
            self._gripper_state = target_pos[6]
        else:
            arm_pos = target_pos
            
        # Command the X5 robot (only arm joints, gripper control TBD)
        self.robot.set_joint_positions(arm_pos)


def main():
    robot = X5Robot()
    print(robot.get_observations())


if __name__ == "__main__":
    main()