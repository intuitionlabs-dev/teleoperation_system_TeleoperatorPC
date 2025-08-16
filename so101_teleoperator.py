"""Minimal SO101 bimanual teleoperator for controlling Piper robots"""
import time
import json
from typing import Dict, Any
from pathlib import Path
from dataclasses import dataclass, asdict

try:
    import scservo_sdk as scs
except ImportError:
    print("WARNING: scservo_sdk not installed. Install with: pip install scservo-sdk")
    scs = None


@dataclass
class MotorCalibration:
    """Simple motor calibration data"""
    id: int
    homing_offset: int
    range_min: int
    range_max: int


class SO101Teleoperator:
    """Minimal bimanual SO101 leader arms teleoperator"""
    
    def __init__(self, 
                 left_port: str = "/dev/ttyACM0", 
                 right_port: str = "/dev/ttyACM1",
                 calibration_dir: str = "./calibration",
                 left_calib_name: str = "left_arm",
                 right_calib_name: str = "right_arm"):
        self.left_port = left_port
        self.right_port = right_port
        self.left_motors = None
        self.right_motors = None
        self._is_connected = False
        
        # Motor IDs for each arm (6 motors per arm)
        self.motor_ids = [1, 2, 3, 4, 5, 6]  # shoulder_pan, shoulder_lift, elbow_flex, wrist_flex, wrist_roll, gripper
        self.motor_names = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"]
        
        # Protocol settings for feetech motors
        self.protocol_version = 0  # SCS protocol
        self.baudrate = 1000000  # 1Mbps
        
        # Calibration
        self.calibration_dir = Path(calibration_dir)
        self.calibration_dir.mkdir(parents=True, exist_ok=True)
        self.left_calib_file = self.calibration_dir / f"{left_calib_name}.json"
        self.right_calib_file = self.calibration_dir / f"{right_calib_name}.json"
        self.left_calibration = {}
        self.right_calibration = {}
        
        # Load calibration if exists
        self._load_calibration()
        
    @property
    def is_connected(self) -> bool:
        return self._is_connected
    
    @property
    def is_calibrated(self) -> bool:
        """Check if both arms are calibrated"""
        left_calibrated = len(self.left_calibration) == len(self.motor_ids)
        right_calibrated = len(self.right_calibration) == len(self.motor_ids)
        return left_calibrated and right_calibrated
    
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
        
        # Check calibration status
        if not self.is_calibrated:
            print("\n⚠️  WARNING: Arms not calibrated! Run calibration first for accurate control.")
    
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
    
    def calibrate(self) -> None:
        """Run calibration for both arms"""
        print("\n=== SO101 Leader Arms Calibration ===")
        print("This will calibrate the joint ranges for accurate teleoperation.")
        
        # Calibrate left arm
        print("\n--- Calibrating LEFT arm ---")
        self.left_calibration = self._calibrate_arm(self.left_motors, "LEFT")
        self._save_calibration(self.left_calibration, self.left_calib_file)
        print(f"Left arm calibration saved to: {self.left_calib_file}")
        
        # Calibrate right arm
        print("\n--- Calibrating RIGHT arm ---")
        self.right_calibration = self._calibrate_arm(self.right_motors, "RIGHT")
        self._save_calibration(self.right_calibration, self.right_calib_file)
        print(f"Right arm calibration saved to: {self.right_calib_file}")
        
        print("\n✅ Calibration complete!")
    
    def _calibrate_arm(self, arm_motors, arm_name: str) -> Dict[str, MotorCalibration]:
        """Calibrate a single arm"""
        calibration = {}
        
        input(f"\nMove the {arm_name} arm to the MIDDLE/HOME position and press ENTER...")
        
        # Read home positions
        home_positions = self._read_positions(arm_motors)
        
        print(f"\nNow move each joint of the {arm_name} arm through its FULL range of motion.")
        print("Press ENTER when done...")
        
        # Record min/max while user moves the arm
        min_positions = list(home_positions)
        max_positions = list(home_positions)
        
        import threading
        stop_recording = threading.Event()
        
        def record_ranges():
            while not stop_recording.is_set():
                positions = self._read_positions(arm_motors)
                for i in range(len(positions)):
                    min_positions[i] = min(min_positions[i], positions[i])
                    max_positions[i] = max(max_positions[i], positions[i])
                time.sleep(0.05)  # 20Hz sampling
        
        # Start recording thread
        record_thread = threading.Thread(target=record_ranges)
        record_thread.start()
        
        # Wait for user
        input()
        stop_recording.set()
        record_thread.join()
        
        # Create calibration entries
        for i, motor_name in enumerate(self.motor_names):
            calibration[motor_name] = MotorCalibration(
                id=self.motor_ids[i],
                homing_offset=home_positions[i],
                range_min=min_positions[i],
                range_max=max_positions[i]
            )
            print(f"  {motor_name}: home={home_positions[i]}, "
                  f"min={min_positions[i]}, max={max_positions[i]}")
        
        return calibration
    
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
        
        # Left arm - SO101 has 6 motors, map to Piper's 7 joints
        action[f"action.left_piper.shoulder_pan.pos"] = self._normalize_joint(
            left_positions[0], self.left_calibration.get("shoulder_pan")
        )
        action[f"action.left_piper.shoulder_lift.pos"] = self._normalize_joint(
            left_positions[1], self.left_calibration.get("shoulder_lift")
        )
        action[f"action.left_piper.elbow_flex.pos"] = self._normalize_joint(
            left_positions[2], self.left_calibration.get("elbow_flex")
        )
        action[f"action.left_piper.joint_3.pos"] = 0.0  # SO101 doesn't have this joint
        action[f"action.left_piper.wrist_flex.pos"] = self._normalize_joint(
            left_positions[3], self.left_calibration.get("wrist_flex")
        )
        action[f"action.left_piper.wrist_roll.pos"] = self._normalize_joint(
            left_positions[4], self.left_calibration.get("wrist_roll")
        )
        action[f"action.left_piper.gripper.pos"] = self._normalize_gripper(
            left_positions[5], self.left_calibration.get("gripper")
        )
        
        # Right arm
        action[f"action.right_piper.shoulder_pan.pos"] = self._normalize_joint(
            right_positions[0], self.right_calibration.get("shoulder_pan")
        )
        action[f"action.right_piper.shoulder_lift.pos"] = self._normalize_joint(
            right_positions[1], self.right_calibration.get("shoulder_lift")
        )
        action[f"action.right_piper.elbow_flex.pos"] = self._normalize_joint(
            right_positions[2], self.right_calibration.get("elbow_flex")
        )
        action[f"action.right_piper.joint_3.pos"] = 0.0  # SO101 doesn't have this joint
        action[f"action.right_piper.wrist_flex.pos"] = self._normalize_joint(
            right_positions[3], self.right_calibration.get("wrist_flex")
        )
        action[f"action.right_piper.wrist_roll.pos"] = self._normalize_joint(
            right_positions[4], self.right_calibration.get("wrist_roll")
        )
        action[f"action.right_piper.gripper.pos"] = self._normalize_gripper(
            right_positions[5], self.right_calibration.get("gripper")
        )
        
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
    
    def _normalize_joint(self, position: int, calibration: MotorCalibration = None) -> float:
        """Normalize motor position to -100 to 100 range"""
        if calibration:
            # Use calibration data for accurate normalization
            center = calibration.homing_offset
            if position < center:
                # Map [min, center] to [-100, 0]
                range_size = center - calibration.range_min
                if range_size > 0:
                    normalized = ((position - center) / range_size) * 100
                else:
                    normalized = 0
            else:
                # Map [center, max] to [0, 100]
                range_size = calibration.range_max - center
                if range_size > 0:
                    normalized = ((position - center) / range_size) * 100
                else:
                    normalized = 0
        else:
            # Fallback: assume 2048 as center (12-bit resolution)
            normalized = ((position - 2048) / 2048) * 100
        
        return max(-100, min(100, normalized))
    
    def _normalize_gripper(self, position: int, calibration: MotorCalibration = None) -> float:
        """Normalize gripper position to 0-100 range"""
        if calibration:
            # Use calibration data
            range_size = calibration.range_max - calibration.range_min
            if range_size > 0:
                normalized = ((position - calibration.range_min) / range_size) * 100
            else:
                normalized = 50
        else:
            # Fallback: map 0-4095 to 0-100
            normalized = (position / 4095) * 100
        
        return max(0, min(100, normalized))
    
    def _load_calibration(self) -> None:
        """Load calibration from files if they exist"""
        if self.left_calib_file.exists():
            with open(self.left_calib_file, 'r') as f:
                data = json.load(f)
                self.left_calibration = {
                    k: MotorCalibration(**v) for k, v in data.items()
                }
            print(f"Loaded left arm calibration from: {self.left_calib_file}")
        
        if self.right_calib_file.exists():
            with open(self.right_calib_file, 'r') as f:
                data = json.load(f)
                self.right_calibration = {
                    k: MotorCalibration(**v) for k, v in data.items()
                }
            print(f"Loaded right arm calibration from: {self.right_calib_file}")
    
    def _save_calibration(self, calibration: Dict[str, MotorCalibration], filepath: Path) -> None:
        """Save calibration to file"""
        data = {k: asdict(v) for k, v in calibration.items()}
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
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