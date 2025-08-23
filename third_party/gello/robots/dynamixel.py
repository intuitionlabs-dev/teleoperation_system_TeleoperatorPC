from typing import Dict, Optional, Sequence, Tuple
import time

import numpy as np

from gello.robots.robot import Robot


class DynamixelRobot(Robot):
    """A class representing a UR robot."""

    def __init__(
        self,
        joint_ids: Sequence[int],
        joint_offsets: Optional[Sequence[float]] = None,
        joint_signs: Optional[Sequence[int]] = None,
        real: bool = False,
        port: str = "/dev/ttyUSB0",
        baudrate: int = 57600,
        gripper_config: Optional[Tuple[int, float, float]] = None,
        start_joints: Optional[np.ndarray] = None,
    ):
        from gello.dynamixel.driver import (
            DynamixelDriver,
            DynamixelDriverProtocol,
            FakeDynamixelDriver,
        )

        print(f"attempting to connect to port: {port}")
        self.gripper_open_close: Optional[Tuple[float, float]]
        if gripper_config is not None:
            assert joint_offsets is not None
            assert joint_signs is not None

            # joint_ids.append(gripper_config[0])
            # joint_offsets.append(0.0)
            # joint_signs.append(1)
            joint_ids = tuple(joint_ids) + (gripper_config[0],)
            joint_offsets = tuple(joint_offsets) + (0.0,)
            joint_signs = tuple(joint_signs) + (1,)
            self.gripper_open_close = (
                gripper_config[1] * np.pi / 180,
                gripper_config[2] * np.pi / 180,
            )
        else:
            self.gripper_open_close = None

        self._joint_ids = joint_ids
        self._driver: DynamixelDriverProtocol

        if joint_offsets is None:
            self._joint_offsets = np.zeros(len(joint_ids))
        else:
            self._joint_offsets = np.array(joint_offsets)

        if joint_signs is None:
            self._joint_signs = np.ones(len(joint_ids))
        else:
            self._joint_signs = np.array(joint_signs)

        assert len(self._joint_ids) == len(self._joint_offsets), (
            f"joint_ids: {len(self._joint_ids)}, "
            f"joint_offsets: {len(self._joint_offsets)}"
        )
        assert len(self._joint_ids) == len(self._joint_signs), (
            f"joint_ids: {len(self._joint_ids)}, "
            f"joint_signs: {len(self._joint_signs)}"
        )
        assert np.all(
            np.abs(self._joint_signs) == 1
        ), f"joint_signs: {self._joint_signs}"

        if real:
            self._driver = DynamixelDriver(joint_ids, port=port, baudrate=baudrate)
            
            # FIRST: Check and clear any hardware errors
            print(f"\n{'='*60}")
            print(f"Initializing {port} - Checking and clearing motor errors...")
            self._driver.check_and_clear_errors()
            
            # THEN: Disable torque on ALL motors
            print(f"Disabling torque on ALL motors...")
            print(f"Joint IDs being controlled: {joint_ids}")
            self._driver.set_torque_mode(False)
            self._torque_on = False
            
            # Give time for motors to fully disable
            time.sleep(0.5)
            print(f"All motors should now be disabled and error-free")
            print(f"{'='*60}\n")
            
            # Configure gripper for current-controlled position mode if present
            if gripper_config is not None:
                # Configure gripper motor for spring-back effect
                self._driver.configure_gripper_mode(gripper_config[0])
                
                # Determine which position is open based on port
                # Different arms have different gripper orientations
                pos1_deg = gripper_config[1]
                pos2_deg = gripper_config[2]
                
                # Port assignments are now corrected:
                # Left arm is on /dev/ttyACM1
                # The gripper_config format is [id, close_pos, open_pos]
                # So pos1_deg is close position and pos2_deg is open position
                # Use them directly without any max/min logic
                gripper_close_deg = pos1_deg  # First position is close
                gripper_open_deg = pos2_deg   # Second position is open
                print(f"Gripper on {port}: close={gripper_close_deg:.1f}°, open={gripper_open_deg:.1f}°")
                
                print(f"Gripper config: open={gripper_open_deg}°, closed={gripper_close_deg}°")
                print(f"Setting gripper to OPEN position: {gripper_open_deg} degrees for spring-back effect")
                
                # Now enable torque to allow setting positions
                self._driver.set_torque_mode(True)
                self._torque_on = True
                
                # Set gripper to open position directly
                gripper_open_rad = gripper_open_deg * np.pi / 180
                
                # Try direct approach: set only the gripper motor position
                print(f"Setting gripper directly to {gripper_open_deg} degrees ({gripper_open_rad} rad)")
                
                # Get all current positions
                current_joints = self._driver.get_joints()
                
                # Prepare positions for all motors
                target_joints = current_joints.copy()
                
                # For the gripper (last motor), apply the open position WITH offsets/signs
                # This matches how positions are set in the normal operation
                target_joints[-1] = gripper_open_rad
                
                # Set positions for all joints
                self._driver.set_joints(target_joints)
                
                # Verify the position was set
                time.sleep(0.5)  # Wait for motor to move
                new_pos = self._driver.get_joints()
                actual_gripper_deg = new_pos[-1] * 180 / np.pi
                print(f"Gripper actual position after setting: {actual_gripper_deg:.1f} degrees")
                print("Gripper configured with spring-back to OPEN position")
            else:
                # For arms without gripper, just enable torque
                self._driver.set_torque_mode(True)
                self._torque_on = True
        else:
            self._driver = FakeDynamixelDriver(joint_ids)
            self._torque_on = False
        self._last_pos = None
        self._alpha = 0.99

        if start_joints is not None:
            # loop through all joints and add +- 2pi to the joint offsets to get the closest to start joints
            new_joint_offsets = []
            current_joints = self.get_joint_state()
            assert current_joints.shape == start_joints.shape
            if gripper_config is not None:
                current_joints = current_joints[:-1]
                start_joints = start_joints[:-1]
            for idx, (c_joint, s_joint, joint_offset) in enumerate(
                zip(current_joints, start_joints, self._joint_offsets)
            ):
                new_joint_offsets.append(
                    np.pi
                    * 2
                    * np.round((-s_joint + c_joint) / (2 * np.pi))
                    * self._joint_signs[idx]
                    + joint_offset
                )
            if gripper_config is not None:
                new_joint_offsets.append(self._joint_offsets[-1])
            self._joint_offsets = np.array(new_joint_offsets)

    def num_dofs(self) -> int:
        return len(self._joint_ids)

    def get_joint_state(self) -> np.ndarray:
        pos = (self._driver.get_joints() - self._joint_offsets) * self._joint_signs
        assert len(pos) == self.num_dofs()

        if self.gripper_open_close is not None:
            # Debug: print raw gripper position before normalization
            raw_gripper_deg = pos[-1] * 180 / np.pi  # Convert to degrees for debugging
            
            # map pos to [0, 1]
            g_pos = (pos[-1] - self.gripper_open_close[0]) / (
                self.gripper_open_close[1] - self.gripper_open_close[0]
            )
            
            # Debug: print normalized value before clamping
            if abs(g_pos - 1.0) < 0.01 or abs(g_pos) < 0.01 or g_pos > 1.0 or g_pos < 0.0:
                print(f"Gripper DEBUG: raw={raw_gripper_deg:.1f}°, normalized={g_pos:.3f}, range=[{self.gripper_open_close[0]*180/np.pi:.1f}, {self.gripper_open_close[1]*180/np.pi:.1f}]°")
            
            g_pos = min(max(0, g_pos), 1)
            pos[-1] = g_pos

        if self._last_pos is None:
            self._last_pos = pos
        else:
            # exponential smoothing
            pos = self._last_pos * (1 - self._alpha) + pos * self._alpha
            self._last_pos = pos

        return pos

    def command_joint_state(self, joint_state: np.ndarray) -> None:
        self._driver.set_joints((joint_state + self._joint_offsets).tolist())

    def set_torque_mode(self, mode: bool):
        if mode == self._torque_on:
            return
        self._driver.set_torque_mode(mode)
        self._torque_on = mode

    def get_observations(self) -> Dict[str, np.ndarray]:
        return {"joint_state": self.get_joint_state()}
