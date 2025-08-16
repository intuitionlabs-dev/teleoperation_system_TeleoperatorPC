"""Minimal GELLO teleoperator for bimanual control"""
import numpy as np
from typing import Dict, Any

try:
    from gello import Gello
except ImportError:
    print("WARNING: gello package not installed")
    Gello = None


class GelloTeleoperator:
    """Teleoperator using two GELLO devices for bimanual control"""
    
    def __init__(self, left_port: str = "/dev/GELLO_L", right_port: str = "/dev/GELLO_R"):
        self.left_port = left_port
        self.right_port = right_port
        self.left_gello = None
        self.right_gello = None
        self._is_connected = False
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected
    
    def connect(self) -> None:
        """Connect to GELLO devices"""
        if self._is_connected:
            return
        
        if Gello is None:
            raise ImportError("gello package not installed")
        
        print(f"Connecting to left GELLO at {self.left_port}...")
        self.left_gello = Gello(port=self.left_port)
        
        print(f"Connecting to right GELLO at {self.right_port}...")
        self.right_gello = Gello(port=self.right_port)
        
        self._is_connected = True
        print("GELLO devices connected")
    
    def get_action(self) -> Dict[str, np.ndarray]:
        """Get current positions from both GELLO devices"""
        if not self._is_connected:
            raise RuntimeError("Not connected to GELLO devices")
        
        # Get joint positions from both devices
        left_joints = self.left_gello.get_joint_positions()
        right_joints = self.right_gello.get_joint_positions()
        
        # Format as action dictionary
        # GELLO returns 7 values: 6 joints + 1 gripper
        action = {
            # Left arm
            "action.left_piper.shoulder_pan.pos": left_joints[0],
            "action.left_piper.shoulder_lift.pos": left_joints[1],
            "action.left_piper.elbow_flex.pos": left_joints[2],
            "action.left_piper.joint_3.pos": left_joints[3],
            "action.left_piper.wrist_flex.pos": left_joints[4],
            "action.left_piper.wrist_roll.pos": left_joints[5],
            "action.left_piper.gripper.pos": left_joints[6],
            
            # Right arm
            "action.right_piper.shoulder_pan.pos": right_joints[0],
            "action.right_piper.shoulder_lift.pos": right_joints[1],
            "action.right_piper.elbow_flex.pos": right_joints[2],
            "action.right_piper.joint_3.pos": right_joints[3],
            "action.right_piper.wrist_flex.pos": right_joints[4],
            "action.right_piper.wrist_roll.pos": right_joints[5],
            "action.right_piper.gripper.pos": right_joints[6],
        }
        
        return action
    
    def disconnect(self) -> None:
        """Disconnect from GELLO devices"""
        if not self._is_connected:
            return
        
        # GELLO devices typically don't need explicit disconnect
        self.left_gello = None
        self.right_gello = None
        self._is_connected = False
        print("GELLO devices disconnected")
