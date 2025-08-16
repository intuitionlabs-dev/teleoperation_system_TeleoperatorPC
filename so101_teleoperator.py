"""Minimal SO101 bimanual teleoperator for controlling Piper robots"""
import time
from typing import Dict, Any

try:
    import scservo_sdk as scs
except ImportError:
    print("WARNING: scservo_sdk not installed. Install with: pip install scservo-sdk")
    scs = None


class SO101Teleoperator:
    """Minimal bimanual SO101 leader arms teleoperator"""
    
    def __init__(self, left_port: str = "/dev/ttyACM0", right_port: str = "/dev/ttyACM1"):
        self.left_port = left_port
        self.right_port = right_port
        self.left_motors = None
        self.right_motors = None
        self._is_connected = False
        
        # Motor IDs for each arm (6 motors per arm)
        self.motor_ids = [1, 2, 3, 4, 5, 6]  # shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper
        
        # Protocol settings for feetech motors
        self.protocol_version = 0  # SCS protocol
        self.baudrate = 1000000  # 1Mbps
        
    @property
    def is_connected(self) -> bool:
        return self._is_connected
    
    def connect(self) -> None:
        """Connect to SO101 leader arms"""
        if self._is_connected:
            return
            
        if scs is None:
            raise ImportError("scservo_sdk not installed")
        
        print(f"Connecting to left SO101 at {self.left_port}...")
        self.left_motors = self._connect_arm(self.left_port)
        
        print(f"Connecting to right SO101 at {self.right_port}...")
        self.right_motors = self._connect_arm(self.right_port)
        
        self._is_connected = True
        print("SO101 leader arms connected")
    
    def _connect_arm(self, port: str):
        """Connect to a single SO101 arm"""
        # Create port handler and packet handler
        port_handler = scs.PortHandler(port)
        packet_handler = scs.PacketHandler(self.protocol_version)
        
        # Open port
        if not port_handler.openPort():
            raise RuntimeError(f"Failed to open port {port}")
        
        # Set baudrate
        if not port_handler.setBaudRate(self.baudrate):
            raise RuntimeError(f"Failed to set baudrate on {port}")
        
        # Disable torque for all motors to enable manual movement
        for motor_id in self.motor_ids:
            packet_handler.write1ByteTxRx(port_handler, motor_id, 40, 0)  # Address 40 = Torque_Enable
        
        return {"port": port_handler, "packet": packet_handler}
    
    def get_action(self) -> Dict[str, float]:
        """Read current positions from both SO101 arms"""
        if not self._is_connected:
            raise RuntimeError("Not connected to SO101 arms")
        
        # Read positions from both arms
        left_positions = self._read_positions(self.left_motors)
        right_positions = self._read_positions(self.right_motors)
        
        # Format as action dictionary matching Piper's expectations
        action = {}
        
        # Map SO101 joint positions to Piper action format
        joint_names = ["shoulder_pan", "shoulder_lift", "elbow_flex", "joint_3", "wrist_flex", "wrist_roll", "gripper"]
        
        # Left arm - normalize from motor range to [-100, 100] or [0, 100] for gripper
        for i, name in enumerate(joint_names):
            if i < len(left_positions):
                if i == 6:  # Gripper
                    # Normalize gripper to 0-100 range
                    action[f"action.left_piper.{name}.pos"] = self._normalize_gripper(left_positions[i])
                elif i == 3:  # joint_3 (not used in SO101, set to 0)
                    action[f"action.left_piper.{name}.pos"] = 0.0
                else:
                    # Normalize joints to -100 to 100 range
                    idx = i if i < 3 else i - 1  # Skip joint_3
                    action[f"action.left_piper.{name}.pos"] = self._normalize_joint(left_positions[idx])
        
        # Right arm
        for i, name in enumerate(joint_names):
            if i < len(right_positions):
                if i == 6:  # Gripper
                    action[f"action.right_piper.{name}.pos"] = self._normalize_gripper(right_positions[i])
                elif i == 3:  # joint_3 (not used in SO101, set to 0)
                    action[f"action.right_piper.{name}.pos"] = 0.0
                else:
                    idx = i if i < 3 else i - 1
                    action[f"action.right_piper.{name}.pos"] = self._normalize_joint(right_positions[idx])
        
        return action
    
    def _read_positions(self, arm_motors) -> list:
        """Read current positions from a single arm"""
        positions = []
        port_handler = arm_motors["port"]
        packet_handler = arm_motors["packet"]
        
        for motor_id in self.motor_ids:
            # Read present position (address 56, 2 bytes)
            position, _, _ = packet_handler.read2ByteTxRx(port_handler, motor_id, 56)
            positions.append(position)
        
        return positions
    
    def _normalize_joint(self, position: int) -> float:
        """Normalize motor position (0-4095) to -100 to 100 range"""
        # STS3215 has 12-bit resolution (0-4095)
        # Map 2048 as center (0), 0 as -100, 4095 as 100
        normalized = ((position - 2048) / 2048) * 100
        return max(-100, min(100, normalized))
    
    def _normalize_gripper(self, position: int) -> float:
        """Normalize gripper position to 0-100 range"""
        # Map 0-4095 to 0-100
        normalized = (position / 4095) * 100
        return max(0, min(100, normalized))
    
    def disconnect(self) -> None:
        """Disconnect from SO101 arms"""
        if not self._is_connected:
            return
        
        # Close ports
        if self.left_motors:
            self.left_motors["port"].closePort()
        if self.right_motors:
            self.right_motors["port"].closePort()
        
        self._is_connected = False
        print("SO101 leader arms disconnected")
