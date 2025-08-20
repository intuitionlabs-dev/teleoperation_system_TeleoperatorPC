"""
Bimanual Dynamixel Leader - Controls YAM leader arms with Dynamixel motors.
"""

import logging
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional

from omegaconf import OmegaConf

from teleoperators.teleoperator import Teleoperator
from .config import BimanualDynamixelLeaderConfig

logger = logging.getLogger(__name__)


class BimanualDynamixelLeader(Teleoperator):
    """
    Bimanual teleoperator using Dynamixel-based YAM leader arms.
    """
    
    config_class = BimanualDynamixelLeaderConfig
    name = "bimanual_dynamixel_leader"
    
    def __init__(self, config: BimanualDynamixelLeaderConfig):
        super().__init__(config)
        self.config = config
        self._is_connected = False
        self._stop_threads = False
        
        # Add gello_software to path - handle both absolute and relative paths
        if Path(config.gello_path).is_absolute():
            gello_path = Path(config.gello_path)
        else:
            # Relative to teleoperation_system_TeleoperatorPC directory
            base_dir = Path(__file__).parent.parent.parent
            gello_path = (base_dir / config.gello_path).resolve()
        
        if not gello_path.exists():
            logger.error(f"Could not find gello_software at: {gello_path}")
            raise RuntimeError(f"gello_software not found at {gello_path}")
        
        if str(gello_path) not in sys.path:
            sys.path.append(str(gello_path))
        
        # Import gello modules after adding to path
        try:
            from gello.utils.launch_utils import instantiate_from_dict
            from gello.agents.agent import BimanualAgent
            from gello.zmq_core.robot_node import ZMQClientRobot, ZMQServerRobot
        except ImportError as e:
            logger.error(f"Failed to import gello modules: {e}")
            logger.error("Make sure gello_software is properly installed")
            raise
        
        self._instantiate_from_dict = instantiate_from_dict
        self._BimanualAgent = BimanualAgent
        self._ZMQClientRobot = ZMQClientRobot
        self._ZMQServerRobot = ZMQServerRobot
        
        # Load configurations
        self.left_cfg = OmegaConf.to_container(
            OmegaConf.load(config.left_arm.config_path), resolve=True
        )
        self.right_cfg = OmegaConf.to_container(
            OmegaConf.load(config.right_arm.config_path), resolve=True
        )
        
        # Will be initialized on connect
        self.left_agent = None
        self.right_agent = None
        self.agent = None
        self.left_server = None
        self.right_server = None
        self.left_client = None
        self.right_client = None
        self.left_thread = None
        self.right_thread = None
    
    @property
    def is_connected(self) -> bool:
        return self._is_connected
    
    @property
    def action_features(self) -> dict[str, type]:
        """Dictionary describing the structure and types of actions produced."""
        base_features = {
            "joint_0.pos": float,
            "joint_1.pos": float,
            "joint_2.pos": float,
            "joint_3.pos": float,
            "joint_4.pos": float,
            "joint_5.pos": float,
            "joint_6.pos": float,
        }
        combined_features = {}
        for key in base_features:
            combined_features[f"left_{key}"] = base_features[key]
            combined_features[f"right_{key}"] = base_features[key]
        return combined_features
    
    @property
    def feedback_features(self) -> dict[str, type]:
        """Dictionary describing the structure and types of feedback expected."""
        # YAM teleoperators don't use feedback
        return {}
    
    def connect(self, calibrate: bool = True) -> None:
        """Connect to the Dynamixel leader arms."""
        if self._is_connected:
            raise RuntimeError(f"{self.name} is already connected")
        
        logger.info(f"Connecting {self.name}...")
        
        # Initialize agents
        logger.info("Initializing leader arm agents...")
        self.left_agent = self._instantiate_from_dict(self.left_cfg["agent"])
        self.right_agent = self._instantiate_from_dict(self.right_cfg["agent"])
        
        # Create bimanual agent
        self.agent = self._BimanualAgent(
            agent_left=self.left_agent,
            agent_right=self.right_agent
        )
        
        # Setup hardware servers for each arm
        self._setup_hardware_servers()
        
        self._is_connected = True
        logger.info(f"{self.name} connected successfully")
    
    def _setup_hardware_servers(self):
        """Setup hardware communication for Dynamixel leader arms."""
        # For teleoperator side, we don't need ZMQ servers or robot instances
        # The agents directly communicate with the Dynamixel hardware
        logger.info("Hardware servers not needed for Dynamixel leader arms - agents connect directly to hardware")
    
    def get_action(self) -> Optional[Dict[str, float]]:
        """Get current action from the Dynamixel leader arms."""
        if not self._is_connected:
            logger.warning("Trying to get action but not connected")
            return None
        
        try:
            # Get action from bimanual agent (returns numpy array)
            action_array = self.agent.act({})
            
            # Convert numpy array to dictionary with proper joint names
            # BimanualAgent returns concatenated [left_joints, right_joints]
            # Each arm has 7 joints (6 DOF + gripper)
            formatted_action = {}
            
            # First 7 values are for left arm
            for i in range(7):
                formatted_action[f"left_joint_{i}.pos"] = float(action_array[i])
            
            # Next 7 values are for right arm
            for i in range(7):
                formatted_action[f"right_joint_{i}.pos"] = float(action_array[i + 7])
            
            return formatted_action
            
        except Exception as e:
            logger.error(f"Error getting action from leader arms: {e}")
            return None
    
    def calibrate(self) -> None:
        """Calibration not needed for Dynamixel arms (uses absolute encoders)."""
        logger.info("Dynamixel arms use absolute encoders - no calibration needed")
    
    @property
    def is_calibrated(self) -> bool:
        """Dynamixel arms are always calibrated (absolute encoders)."""
        return True
    
    def send_feedback(self, feedback: dict[str, Any]) -> None:
        """Send feedback to the teleoperator (not used for YAM/Dynamixel)."""
        # YAM teleoperators don't use feedback
        pass
    
    def disconnect(self) -> None:
        """Disconnect from the Dynamixel leader arms."""
        if not self._is_connected:
            return
        
        logger.info(f"Disconnecting {self.name}...")
        
        # The agents handle their own disconnection/cleanup
        # No servers or threads to close since we're not using ZMQ
        
        self._is_connected = False
        logger.info(f"{self.name} disconnected")