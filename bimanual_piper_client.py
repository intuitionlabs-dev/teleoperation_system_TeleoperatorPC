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
        self._is_connected = False
    
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
        
        # Command sender (PUB) - changed from PUSH to avoid queuing
        self.push_cmd = self.context.socket(zmq.PUB)
        self.push_cmd.setsockopt(zmq.SNDTIMEO, 100)  # 100ms timeout
        self.push_cmd.setsockopt(zmq.SNDHWM, 1)  # Keep only latest message
        self.push_cmd.setsockopt(zmq.LINGER, 0)  # Don't wait on close
        self.push_cmd.connect(f"tcp://{self.config.hostname}:{self.config.cmd_port}")
        
        # PUB sockets need time to establish connection to avoid message loss
        time.sleep(0.1)
        
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
    

    
    def disconnect(self) -> None:
        """Disconnect from robot"""
        if not self._is_connected:
            return
        
        if self.push_cmd:
            self.push_cmd.close()
        if self.context:
            self.context.term()
        
        self._is_connected = False
        print("Disconnected from robot")
