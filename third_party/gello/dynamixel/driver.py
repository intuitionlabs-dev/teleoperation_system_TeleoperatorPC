import os
import subprocess
import time
from threading import Event, Lock, Thread
from typing import Protocol, Sequence

import numpy as np
from dynamixel_sdk.group_sync_read import GroupSyncRead
from dynamixel_sdk.group_sync_write import GroupSyncWrite
from dynamixel_sdk.packet_handler import PacketHandler
from dynamixel_sdk.port_handler import PortHandler
from dynamixel_sdk.robotis_def import (
    COMM_SUCCESS,
    DXL_HIBYTE,
    DXL_HIWORD,
    DXL_LOBYTE,
    DXL_LOWORD,
)

# Constants
ADDR_OPERATING_MODE = 11
ADDR_TORQUE_ENABLE = 64
ADDR_HARDWARE_ERROR_STATUS = 70
ADDR_GOAL_POSITION = 116
LEN_GOAL_POSITION = 4
ADDR_PRESENT_POSITION = 132
LEN_PRESENT_POSITION = 4
ADDR_REBOOT = 8  # Reboot motor to clear errors
TORQUE_ENABLE = 1
TORQUE_DISABLE = 0
# Operating modes
CURRENT_CONTROLLED_POSITION_MODE = 5
EXTENDED_POSITION_MODE = 4
POSITION_MODE = 3


class DynamixelDriverProtocol(Protocol):
    def set_joints(self, joint_angles: Sequence[float]):
        """Set the joint angles for the Dynamixel servos.

        Args:
            joint_angles (Sequence[float]): A list of joint angles.
        """
        ...

    def torque_enabled(self) -> bool:
        """Check if torque is enabled for the Dynamixel servos.

        Returns:
            bool: True if torque is enabled, False if it is disabled.
        """
        ...

    def set_torque_mode(self, enable: bool):
        """Set the torque mode for the Dynamixel servos.

        Args:
            enable (bool): True to enable torque, False to disable.
        """
        ...

    def get_joints(self) -> np.ndarray:
        """Get the current joint angles in radians.

        Returns:
            np.ndarray: An array of joint angles.
        """
        ...

    def close(self):
        """Close the driver."""


class FakeDynamixelDriver(DynamixelDriverProtocol):
    def __init__(self, ids: Sequence[int]):
        self._ids = ids
        self._joint_angles = np.zeros(len(ids), dtype=int)
        self._torque_enabled = False

    def set_joints(self, joint_angles: Sequence[float]):
        if len(joint_angles) != len(self._ids):
            raise ValueError(
                "The length of joint_angles must match the number of servos"
            )
        if not self._torque_enabled:
            raise RuntimeError("Torque must be enabled to set joint angles")
        self._joint_angles = np.array(joint_angles)

    def torque_enabled(self) -> bool:
        return self._torque_enabled

    def set_torque_mode(self, enable: bool):
        self._torque_enabled = enable

    def get_joints(self) -> np.ndarray:
        return self._joint_angles.copy()

    def close(self):
        pass


class DynamixelDriver(DynamixelDriverProtocol):
    def __init__(
        self,
        ids: Sequence[int],
        port: str = "/dev/ttyUSB0",
        baudrate: int = 57600,
        max_retries: int = 3,
        use_fake_fallback: bool = True,
        read_period_s: float = 0.01,
    ):
        """Initialize the DynamixelDriver class.

        Args:
            ids (Sequence[int]): A list of IDs for the Dynamixel servos.
            port (str): The USB port to connect to the arm.
            baudrate (int): The baudrate for communication.
            max_retries (int): Maximum number of initialization attempts.
            use_fake_fallback (bool): Whether to fallback to FakeDynamixelDriver on failure.
        """
        self._ids = ids
        self._joint_angles = None
        self._lock = Lock()
        self._port = port
        self._baudrate = baudrate
        self._max_retries = max_retries
        self._use_fake_fallback = use_fake_fallback
        self._is_fake = False
        self._torque_enabled = False
        self._stop_thread = Event()
        self._read_period_s = max(0.001, float(read_period_s))
        self._last_comm_warn_time = 0.0

        # Initialize with retry logic
        if not self._initialize_with_retries():
            if self._use_fake_fallback:
                print("Using fake Dynamixel driver")
                self._initialize_fake_driver()
            else:
                raise RuntimeError(
                    "Failed to initialize Dynamixel driver after all retries"
                )

    def _initialize_with_retries(self) -> bool:
        """Initialize the Dynamixel driver with retry logic."""
        for attempt in range(self._max_retries):
            print(
                f"Attempting to initialize Dynamixel driver (attempt {attempt + 1}/{self._max_retries})"
            )

            # Check port availability
            if not self._check_port_availability():
                print("Port is busy, attempting to free it...")
                if not self._kill_processes_using_port():
                    print("Failed to free port, trying to fix permissions...")
                    self._fix_port_permissions()
                time.sleep(2)

            try:
                self._initialize_hardware()
                print(f"Successfully initialized Dynamixel driver on {self._port}")
                return True
            except Exception as e:
                print(f"Failed to initialize Dynamixel driver: {e}")
                if attempt < self._max_retries - 1:
                    print("Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    print("Max retries reached")

        return False

    def _initialize_hardware(self):
        """Initialize the hardware connection."""
        # Check and prepare port before connection
        self._prepare_port()

        # Initialize the port handler, packet handler, and group sync read/write
        self._portHandler = PortHandler(self._port)
        self._packetHandler = PacketHandler(2.0)
        self._groupSyncRead = GroupSyncRead(
            self._portHandler,
            self._packetHandler,
            ADDR_PRESENT_POSITION,
            LEN_PRESENT_POSITION,
        )
        self._groupSyncWrite = GroupSyncWrite(
            self._portHandler,
            self._packetHandler,
            ADDR_GOAL_POSITION,
            LEN_GOAL_POSITION,
        )

        # Open the port and set the baudrate
        if not self._portHandler.openPort():
            raise RuntimeError("Failed to open the port")

        if not self._portHandler.setBaudRate(self._baudrate):
            raise RuntimeError(f"Failed to change the baudrate, {self._baudrate}")

        # Add parameters for each Dynamixel servo to the group sync read
        for dxl_id in self._ids:
            if not self._groupSyncRead.addParam(dxl_id):
                raise RuntimeError(
                    f"Failed to add parameter for Dynamixel with ID {dxl_id}"
                )

        # Disable torque for each Dynamixel servo
        try:
            self.set_torque_mode(self._torque_enabled)
        except Exception as e:
            print(f"port: {self._port}, {e}")

        self._start_reading_thread()

    def _initialize_fake_driver(self):
        """Initialize as a fake driver."""
        self._is_fake = True
        self._fake_joint_angles = np.zeros(len(self._ids), dtype=float)

    def set_joints(self, joint_angles: Sequence[float]):
        if len(joint_angles) != len(self._ids):
            raise ValueError(
                "The length of joint_angles must match the number of servos"
            )
        if not self._torque_enabled:
            raise RuntimeError("Torque must be enabled to set joint angles")

        if self._is_fake:
            self._fake_joint_angles = np.array(joint_angles)
            return

        # Ensure read/write operations do not collide on the serial bus
        with self._lock:
            for dxl_id, angle in zip(self._ids, joint_angles):
                # Convert the angle to the appropriate value for the servo
                position_value = int(angle * 2048 / np.pi)

                # Allocate goal position value into byte array
                param_goal_position = [
                    DXL_LOBYTE(DXL_LOWORD(position_value)),
                    DXL_HIBYTE(DXL_LOWORD(position_value)),
                    DXL_LOBYTE(DXL_HIWORD(position_value)),
                    DXL_HIBYTE(DXL_HIWORD(position_value)),
                ]

                # Add goal position value to the Syncwrite parameter storage
                dxl_addparam_result = self._groupSyncWrite.addParam(
                    dxl_id, param_goal_position
                )
                if not dxl_addparam_result:
                    raise RuntimeError(
                        f"Failed to set joint angle for Dynamixel with ID {dxl_id}"
                    )

            # Syncwrite goal position
            dxl_comm_result = self._groupSyncWrite.txPacket()
            if dxl_comm_result != COMM_SUCCESS:
                raise RuntimeError("Failed to syncwrite goal position")

            # Clear syncwrite parameter storage
            self._groupSyncWrite.clearParam()

    def torque_enabled(self) -> bool:
        return self._torque_enabled

    def set_operating_mode(self, dxl_id: int, mode: int):
        """Set the operating mode for a specific Dynamixel motor."""
        if self._is_fake:
            return
        
        # Torque must be disabled to change operating mode
        was_enabled = self._torque_enabled
        if was_enabled:
            self.set_torque_mode(False)
        
        with self._lock:
            dxl_comm_result, dxl_error = self._packetHandler.write1ByteTxRx(
                self._portHandler, dxl_id, ADDR_OPERATING_MODE, mode
            )
            if dxl_comm_result != COMM_SUCCESS or dxl_error != 0:
                print(f"Failed to set operating mode for Dynamixel ID {dxl_id}")
        
        # Re-enable torque if it was enabled before
        if was_enabled:
            self.set_torque_mode(True)
    
    def check_and_clear_errors(self):
        """Check for hardware errors and clear them if present."""
        if self._is_fake:
            return
        
        print("Checking for hardware errors on all motors...")
        errors_found = False
        
        with self._lock:
            for dxl_id in self._ids:
                # Read hardware error status (returns: result, data, error)
                dxl_comm_result, dxl_data, dxl_error = self._packetHandler.read1ByteTxRx(
                    self._portHandler, dxl_id, ADDR_HARDWARE_ERROR_STATUS
                )
                
                if dxl_comm_result == COMM_SUCCESS and dxl_data > 0:
                    errors_found = True
                    print(f"  Motor {dxl_id}: Hardware error detected (error code: {dxl_data})")
                    
                    # Reboot motor to clear errors
                    print(f"  Motor {dxl_id}: Rebooting to clear error...")
                    reboot_result = self._packetHandler.reboot(self._portHandler, dxl_id)
                    
                    if reboot_result == COMM_SUCCESS:
                        print(f"  Motor {dxl_id}: Reboot command sent")
                        time.sleep(0.5)  # Wait for reboot
                    else:
                        print(f"  Motor {dxl_id}: Failed to send reboot command")
        
        if errors_found:
            print("Waiting 2 seconds for motors to complete reboot...")
            time.sleep(2)
            print("Error clearing complete")
        else:
            print("No hardware errors found")
    
    def configure_gripper_mode(self, gripper_id: int):
        """Configure gripper motor for current-controlled position mode."""
        if self._is_fake:
            return
        
        # Set gripper to current-controlled position mode for spring-back effect
        self.set_operating_mode(gripper_id, CURRENT_CONTROLLED_POSITION_MODE)
        print(f"Set Dynamixel ID {gripper_id} to current-controlled position mode")

    def set_torque_mode(self, enable: bool):
        if self._is_fake:
            self._torque_enabled = enable
            return

        torque_value = TORQUE_ENABLE if enable else TORQUE_DISABLE
        with self._lock:
            for dxl_id in self._ids:
                dxl_comm_result, dxl_error = self._packetHandler.write1ByteTxRx(
                    self._portHandler, dxl_id, ADDR_TORQUE_ENABLE, torque_value
                )
                if dxl_comm_result != COMM_SUCCESS or dxl_error != 0:
                    print(dxl_comm_result)
                    print(dxl_error)
                    raise RuntimeError(
                        f"Failed to set torque mode for Dynamixel with ID {dxl_id}"
                    )

        self._torque_enabled = enable

    def _start_reading_thread(self):
        self._reading_thread = Thread(target=self._read_joint_angles)
        self._reading_thread.daemon = True
        self._reading_thread.start()

    def _read_joint_angles(self):
        # Continuously read joint angles and update the joint_angles array
        while not self._stop_thread.is_set():
            time.sleep(self._read_period_s)
            with self._lock:
                _joint_angles = np.zeros(len(self._ids), dtype=int)
                dxl_comm_result = self._groupSyncRead.txRxPacket()
                if dxl_comm_result != COMM_SUCCESS:
                    now = time.time()
                    # Throttle warnings to at most once per second to reduce log spam
                    if now - self._last_comm_warn_time > 1.0:
                        print(f"warning, comm failed: {dxl_comm_result}")
                        self._last_comm_warn_time = now
                    continue
                for i, dxl_id in enumerate(self._ids):
                    if self._groupSyncRead.isAvailable(
                        dxl_id, ADDR_PRESENT_POSITION, LEN_PRESENT_POSITION
                    ):
                        angle = self._groupSyncRead.getData(
                            dxl_id, ADDR_PRESENT_POSITION, LEN_PRESENT_POSITION
                        )
                        angle = np.int32(np.uint32(angle))
                        _joint_angles[i] = angle
                    else:
                        raise RuntimeError(
                            f"Failed to get joint angles for Dynamixel with ID {dxl_id}"
                        )
                self._joint_angles = _joint_angles
            # self._groupSyncRead.clearParam() # TODO what does this do? should i add it

    def get_joints(self) -> np.ndarray:
        if self._is_fake:
            return self._fake_joint_angles.copy()

        # Return a copy of the joint_angles array to avoid race conditions
        while self._joint_angles is None:
            time.sleep(0.1)
        # with self._lock:
        _j = self._joint_angles.copy()
        return _j / 2048.0 * np.pi

    def _check_port_availability(self) -> bool:
        """Check if the port is available and not being used by other processes."""
        try:
            # Check if port exists
            if not os.path.exists(self._port):
                print(f"Port {self._port} does not exist")
                return False

            # Check for processes using the port
            result = subprocess.run(
                ["lsof", self._port], capture_output=True, text=True
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                if len(lines) > 1:  # Header + processes
                    print(f"Port {self._port} is being used by other processes:")
                    for line in lines[1:]:
                        print(f"  {line}")
                    return False
            return True
        except Exception as e:
            print(f"Error checking port availability: {e}")
            return False

    def _kill_processes_using_port(self) -> bool:
        """Kill processes that are using the port."""
        try:
            result = subprocess.run(
                ["fuser", "-k", self._port], capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"Killed processes using {self._port}")
                time.sleep(1)  # Give time for processes to terminate
                return True
            return False
        except Exception as e:
            print(f"Error killing processes: {e}")
            return False

    def _fix_port_permissions(self) -> bool:
        """Fix port permissions if needed."""
        try:
            result = subprocess.run(
                ["sudo", "chmod", "666", self._port], capture_output=True, text=True
            )
            if result.returncode == 0:
                print(f"Fixed permissions for {self._port}")
                return True
            return False
        except Exception as e:
            print(f"Error fixing port permissions: {e}")
            return False

    def _prepare_port(self):
        """Prepare the port for connection by checking availability and fixing issues."""
        if not self._check_port_availability():
            print(f"Port {self._port} is not available, attempting to fix...")
            self._kill_processes_using_port()
            self._fix_port_permissions()

            # Check again after fixing
            if not self._check_port_availability():
                print(f"Warning: Port {self._port} may still have issues")

    def close(self):
        if self._is_fake:
            return

        self._stop_thread.set()
        self._reading_thread.join()
        self._portHandler.closePort()


def main():
    # Set the port, baudrate, and servo IDs
    ids = [1]

    # Create a DynamixelDriver instance
    try:
        driver = DynamixelDriver(ids)
    except FileNotFoundError:
        driver = DynamixelDriver(ids, port="/dev/cu.usbserial-FT7WBMUB")

    # Test setting torque mode
    driver.set_torque_mode(True)
    driver.set_torque_mode(False)

    # Test reading the joint angles
    try:
        while True:
            joint_angles = driver.get_joints()
            print(f"Joint angles for IDs {ids}: {joint_angles}")
            # print(f"Joint angles for IDs {ids[1]}: {joint_angles[1]}")
    except KeyboardInterrupt:
        driver.close()


if __name__ == "__main__":
    main()  # Test the driver
