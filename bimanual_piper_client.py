"""Minimal bimanual Piper client for teleoperation"""
import json
import time
import zmq
import numpy as np
from typing import Any, Dict


class BimanualPiperClient:
    """Client for controlling bimanual Piper robot remotely"""
    
    def __init__(self, config):
        self.config = config
        self.context = None
        self.push_cmd = None
        self.pull_obs = None
        self._is_connected = False
        
        # Simple observation cache
        self._last_obs = None
        self._last_obs_time = 0
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected
    
    def connect(self) -> None:
        """Connect to robot PC via ZMQ"""
        if self._is_connected:
            print("Already connected")
            return
        
        print(f"Connecting to {self.config.hostname}...")
        
        self.context = zmq.Context()
        
        # Command sender (PUSH)
        self.push_cmd = self.context.socket(zmq.PUSH)
        self.push_cmd.setsockopt(zmq.SNDTIMEO, 100)  # 100ms timeout
        self.push_cmd.connect(f"tcp://{self.config.hostname}:{self.config.cmd_port}")
        
        # Observation receiver (PULL)
        self.pull_obs = self.context.socket(zmq.PULL)
        self.pull_obs.setsockopt(zmq.RCVTIMEO, 35)  # 35ms timeout for 30Hz
        self.pull_obs.connect(f"tcp://{self.config.hostname}:{self.config.obs_port}")
        
        self._is_connected = True
        print(f"Connected to robot at {self.config.hostname}")
    
    def send_action(self, action: Dict[str, Any]) -> None:
        """Send action to robot"""
        if not self._is_connected:
            raise RuntimeError("Not connected")
        
        # Convert numpy arrays to lists for JSON
        action_json = {}
        for key, val in action.items():
            if isinstance(val, np.ndarray):
                action_json[key] = val.tolist()
            else:
                action_json[key] = val
        
        # Send command
        try:
            self.push_cmd.send_string(json.dumps({"action": action_json}))
        except zmq.Again:
            print("Warning: Failed to send command (timeout)")
    
    def get_observation(self) -> Dict[str, Any]:
        """Get latest observation from robot"""
        if not self._is_connected:
            raise RuntimeError("Not connected")
        
        # Try to receive observation
        try:
            obs_str = self.pull_obs.recv_string()
            obs = json.loads(obs_str)
            
            # Convert to expected format
            formatted_obs = {}
            
            # Left arm
            if "left_pos" in obs:
                formatted_obs["observation.left_piper.position"] = np.array(obs["left_pos"])
                formatted_obs["observation.left_piper.velocity"] = np.array(obs.get("left_vel", [0]*7))
                formatted_obs["observation.left_piper.gripper_position"] = obs.get("left_gripper", 0.0)
            
            # Right arm  
            if "right_pos" in obs:
                formatted_obs["observation.right_piper.position"] = np.array(obs["right_pos"])
                formatted_obs["observation.right_piper.velocity"] = np.array(obs.get("right_vel", [0]*7))
                formatted_obs["observation.right_piper.gripper_position"] = obs.get("right_gripper", 0.0)
            
            self._last_obs = formatted_obs
            self._last_obs_time = time.time()
            
            return formatted_obs
            
        except zmq.Again:
            # Return cached observation if recent enough
            if self._last_obs and (time.time() - self._last_obs_time < 0.1):
                return self._last_obs
            return None
    
    def disconnect(self) -> None:
        """Disconnect from robot"""
        if not self._is_connected:
            return
        
        if self.push_cmd:
            self.push_cmd.close()
        if self.pull_obs:
            self.pull_obs.close()
        if self.context:
            self.context.term()
        
        self._is_connected = False
        print("Disconnected from robot")
