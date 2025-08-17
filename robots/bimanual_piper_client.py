"""
Bimanual Piper client for remote robot control via ZMQ.
"""

import json
import logging
from functools import cached_property
from typing import Any

import zmq

from robots.robot import Robot
from robots.config import BimanualPiperClientConfig


class BimanualPiperClient(Robot):
    """Client for controlling a remote bimanual Piper robot via network."""
    
    config_class = BimanualPiperClientConfig
    name = "bimanual_piper_client"
    
    def __init__(self, config: BimanualPiperClientConfig):
        # Don't call super().__init__ to avoid creating unnecessary calibration directory
        # The client doesn't need calibration - only the teleoperator arms do
        self.robot_type = self.name
        self.id = config.id
        self.calibration = {}
        # Network configuration
        self.remote_ip = config.remote_ip
        self.port_zmq_cmd = config.port_zmq_cmd
        self.port_zmq_observations = config.port_zmq_observations
        self.connect_timeout_s = config.connect_timeout_s
        self._is_connected = False
    
    @cached_property
    def action_features(self) -> dict[str, type]:
        # Bimanual actions are prefixed with left_ and right_
        base_features = {
            "shoulder_pan.pos": float,
            "shoulder_lift.pos": float,
            "elbow_flex.pos": float,
            "wrist_flex.pos": float,
            "wrist_roll.pos": float,
            "gripper.pos": float,
        }
        features = {}
        for key, val in base_features.items():
            features[f"left_{key}"] = val
            features[f"right_{key}"] = val
        return features
    
    @cached_property
    def observation_features(self) -> dict[str, type | tuple]:
        motors_ft = {f"joint_{i}.pos": float for i in range(7)}
        bimanual_motors_ft = {}
        for key, val in motors_ft.items():
            bimanual_motors_ft[f"left_{key}"] = val
            bimanual_motors_ft[f"right_{key}"] = val
        return bimanual_motors_ft
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected
    
    def connect(self, calibrate: bool = True) -> None:
        """Establishes ZMQ sockets with the remote robot."""
        if self._is_connected:
            raise RuntimeError("Bimanual Piper Client is already connected.")
        
        self.zmq_context = zmq.Context()
        self.zmq_cmd_socket = self.zmq_context.socket(zmq.PUSH)
        zmq_cmd_locator = f"tcp://{self.remote_ip}:{self.port_zmq_cmd}"
        self.zmq_cmd_socket.connect(zmq_cmd_locator)
        self.zmq_cmd_socket.setsockopt(zmq.CONFLATE, 1)
        
        self.zmq_observation_socket = self.zmq_context.socket(zmq.PULL)
        zmq_observations_locator = f"tcp://{self.remote_ip}:{self.port_zmq_observations}"
        self.zmq_observation_socket.connect(zmq_observations_locator)
        self.zmq_observation_socket.setsockopt(zmq.CONFLATE, 1)
        
        # Check connection with timeout
        poller = zmq.Poller()
        poller.register(self.zmq_observation_socket, zmq.POLLIN)
        socks = dict(poller.poll(self.connect_timeout_s * 1000))
        
        if self.zmq_observation_socket not in socks or socks[self.zmq_observation_socket] != zmq.POLLIN:
            raise RuntimeError("Timeout waiting for Bimanual Piper Host to connect expired.")
        
        self._is_connected = True
        logging.info("Connected to remote Bimanual Piper robot")
    
    def disconnect(self) -> None:
        """Disconnect from the remote robot."""
        if not self._is_connected:
            return
        
        self.zmq_observation_socket.close()
        self.zmq_cmd_socket.close()
        self.zmq_context.term()
        self._is_connected = False
        logging.info("Disconnected from remote Bimanual Piper robot")
    
    @property
    def is_calibrated(self) -> bool:
        return True
    
    def calibrate(self) -> None:
        pass
    
    def configure(self) -> None:
        pass
    
    def get_observation(self) -> dict[str, Any]:
        """Get an observation from the remote host."""
        raw_obs = self.zmq_observation_socket.recv_string()
        return json.loads(raw_obs)
    
    def send_action(self, action: dict[str, Any]) -> dict[str, Any]:
        """Send an action to the remote host."""
        logging.debug(f"[CLIENT] Sending action (keys={list(action.keys())}): {action}")
        self.zmq_cmd_socket.send_string(json.dumps(action))
        return action