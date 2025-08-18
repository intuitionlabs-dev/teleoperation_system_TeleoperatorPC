#!/usr/bin/env python

# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
# Simplified version for teleoperation system

import logging
from copy import deepcopy
from enum import Enum
from pprint import pformat

from ..encoding_utils import decode_sign_magnitude, encode_sign_magnitude
from ..motors_bus import Motor, MotorCalibration, MotorsBus
from ..motor_types import NameOrID, Value
from ..exceptions import DeviceNotConnectedError
from .feetech_tables import (
    FIRMWARE_MAJOR_VERSION,
    FIRMWARE_MINOR_VERSION,
    MODEL_BAUDRATE_TABLE,
    MODEL_CONTROL_TABLE,
    MODEL_ENCODING_TABLE,
    MODEL_NUMBER,
    MODEL_NUMBER_TABLE,
    MODEL_PROTOCOL,
    MODEL_RESOLUTION,
    SCAN_BAUDRATES,
)

DEFAULT_PROTOCOL_VERSION = 0
DEFAULT_BAUDRATE = 1_000_000
DEFAULT_TIMEOUT_MS = 1000

NORMALIZED_DATA = ["Goal_Position", "Present_Position"]

logger = logging.getLogger(__name__)


class OperatingMode(Enum):
    # position servo mode
    POSITION = 0
    # The motor is in constant speed mode, which is controlled by parameter 0x2e, and the highest bit 15 is
    # the direction bit
    VELOCITY = 1
    # PWM open-loop speed regulation mode, with parameter 0x2c running time parameter control, bit11 as
    # direction bit
    PWM = 2
    # In step servo mode, the number of step progress is represented by parameter 0x2a, and the highest bit 15
    # is the direction bit
    STEP = 3


class DriveMode(Enum):
    NON_INVERTED = 0
    INVERTED = 1


def get_address(control_table: dict, model: str, data_name: str) -> tuple[int, int]:
    """Get the address and length for a given data name from the control table."""
    if model not in control_table:
        raise ValueError(f"Model {model} not found in control table")
    if data_name not in control_table[model]:
        raise ValueError(f"Data name {data_name} not found in control table for model {model}")
    entry = control_table[model][data_name]
    return entry[0], entry[1]  # (address, length)


class TorqueMode(Enum):
    ENABLED = 1
    DISABLED = 0


def _split_into_byte_chunks(value: int, length: int) -> list[int]:
    """Convert integer to byte chunks using Feetech SDK byte order."""
    try:
        import scservo_sdk as scs
    except ImportError:
        # Fallback implementation if scservo_sdk is not available
        if length == 1:
            data = [value]
        elif length == 2:
            data = [value & 0xFF, (value >> 8) & 0xFF]  # Little endian
        elif length == 4:
            data = [
                value & 0xFF,
                (value >> 8) & 0xFF,
                (value >> 16) & 0xFF,
                (value >> 24) & 0xFF,
            ]
        else:
            raise ValueError(f"Unsupported length: {length}")
        return data
    
    if length == 1:
        data = [value]
    elif length == 2:
        data = [scs.SCS_LOBYTE(value), scs.SCS_HIBYTE(value)]
    elif length == 4:
        data = [
            scs.SCS_LOBYTE(scs.SCS_LOWORD(value)),
            scs.SCS_HIBYTE(scs.SCS_LOWORD(value)),
            scs.SCS_LOBYTE(scs.SCS_HIWORD(value)),
            scs.SCS_HIBYTE(scs.SCS_HIWORD(value)),
        ]
    return data


def patch_setPacketTimeout(self, packet_length):  # noqa: N802
    """
    HACK: This patches the PortHandler behavior to set the correct packet timeouts.
    
    It fixes https://gitee.com/ftservo/SCServoSDK/issues/IBY2S6
    """
    self.packet_start_time = self.getCurrentTime()
    self.packet_timeout = (self.tx_time_per_byte * packet_length) + (self.tx_time_per_byte * 3.0) + 50


class FeetechMotorsBus(MotorsBus):
    """
    The FeetechMotorsBus class allows to efficiently read and write to the attached motors.
    Simplified version for teleoperation - focuses on essential SO101 leader arm control.
    """

    apply_drive_mode = True
    available_baudrates = deepcopy(SCAN_BAUDRATES)
    default_baudrate = DEFAULT_BAUDRATE
    default_timeout = DEFAULT_TIMEOUT_MS
    model_baudrate_table = deepcopy(MODEL_BAUDRATE_TABLE)
    model_ctrl_table = deepcopy(MODEL_CONTROL_TABLE)
    model_encoding_table = deepcopy(MODEL_ENCODING_TABLE)
    model_number_table = deepcopy(MODEL_NUMBER_TABLE)
    model_resolution_table = deepcopy(MODEL_RESOLUTION)
    normalized_data = deepcopy(NORMALIZED_DATA)

    def __init__(
        self,
        port: str,
        motors: dict[str, Motor],
        calibration: dict[str, MotorCalibration] | None = None,
        protocol_version: int = DEFAULT_PROTOCOL_VERSION,
    ):
        super().__init__(port, motors, calibration)
        self.protocol_version = protocol_version
        self._assert_same_protocol()
        
        try:
            import scservo_sdk as scs
        except ImportError:
            raise ImportError(
                "scservo_sdk is required for FeetechMotorsBus. "
                "Install it with: pip install scservo_sdk"
            )

        self.port_handler = scs.PortHandler(self.port)
        # HACK: monkeypatch
        self.port_handler.setPacketTimeout = patch_setPacketTimeout.__get__(
            self.port_handler, scs.PortHandler
        )
        self.packet_handler = scs.PacketHandler(protocol_version)
        self.sync_reader = scs.GroupSyncRead(self.port_handler, self.packet_handler, 0, 0)
        self.sync_writer = scs.GroupSyncWrite(self.port_handler, self.packet_handler, 0, 0)
        self._comm_success = scs.COMM_SUCCESS
        self._no_error = 0x00

        if any(MODEL_PROTOCOL[model] != self.protocol_version for model in self.models):
            raise ValueError(f"Some motors are incompatible with protocol_version={self.protocol_version}")

    def _assert_same_protocol(self) -> None:
        if any(MODEL_PROTOCOL[model] != self.protocol_version for model in self.models):
            raise RuntimeError("Some motors use an incompatible protocol.")

    def _handshake(self) -> None:
        """Simplified handshake - just check if motors exist."""
        self._assert_motors_exist()

    def _assert_motors_exist(self) -> None:
        expected_models = {m.id: self.model_number_table[m.model] for m in self.motors.values()}

        found_models = {}
        for id_ in self.ids:
            model_nb = self.ping(id_)
            if model_nb is not None:
                found_models[id_] = model_nb

        missing_ids = [id_ for id_ in self.ids if id_ not in found_models]
        wrong_models = {
            id_: (expected_models[id_], found_models[id_])
            for id_ in found_models
            if expected_models.get(id_) != found_models[id_]
        }

        if missing_ids or wrong_models:
            error_lines = [f"{self.__class__.__name__} motor check failed on port '{self.port}':"]

            if missing_ids:
                error_lines.append("\nMissing motor IDs:")
                error_lines.extend(
                    f"  - {id_} (expected model: {expected_models[id_]})" for id_ in missing_ids
                )

            if wrong_models:
                error_lines.append("\nMotors with incorrect model numbers:")
                error_lines.extend(
                    f"  - {id_} ({self._id_to_name(id_)}): expected {expected}, found {found}"
                    for id_, (expected, found) in wrong_models.items()
                )

            error_lines.append("\nFull expected motor list (id: model_number):")
            error_lines.append(pformat(expected_models, indent=4, sort_dicts=False))
            error_lines.append("\nFull found motor list (id: model_number):")
            error_lines.append(pformat(found_models, indent=4, sort_dicts=False))

            raise RuntimeError("\n".join(error_lines))

    def configure_motors(self, return_delay_time=0, maximum_acceleration=254, acceleration=254) -> None:
        """Configure motors with optimal settings for teleoperation."""
        for motor in self.motors:
            # Reduce delay response time to minimum for faster communication
            self.write("Return_Delay_Time", motor, return_delay_time)
            # Set maximum acceleration for responsive movement
            if self.protocol_version == 0:
                self.write("Maximum_Acceleration", motor, maximum_acceleration)
            self.write("Acceleration", motor, acceleration)

    def disable_torque(self, motors: str | list[str] | None = None, num_retry: int = 0) -> None:
        """Disable torque on selected motors."""
        for motor in self._get_motors_list(motors):
            self.write("Torque_Enable", motor, TorqueMode.DISABLED.value, num_retry=num_retry)
            self.write("Lock", motor, 0, num_retry=num_retry)

    def _disable_torque(self, motor_id: int, model: str, num_retry: int = 0) -> None:
        addr, length = get_address(self.model_ctrl_table, model, "Torque_Enable")
        self._write(addr, length, motor_id, TorqueMode.DISABLED.value, num_retry=num_retry)
        addr, length = get_address(self.model_ctrl_table, model, "Lock")
        self._write(addr, length, motor_id, 0, num_retry=num_retry)

    def enable_torque(self, motors: str | list[str] | None = None, num_retry: int = 0) -> None:
        """Enable torque on selected motors."""
        for motor in self._get_motors_list(motors):
            self.write("Torque_Enable", motor, TorqueMode.ENABLED.value, num_retry=num_retry)
            self.write("Lock", motor, 1, num_retry=num_retry)

    def _encode_sign(self, data_name: str, ids_values: dict[int, int]) -> dict[int, int]:
        for id_ in ids_values:
            model = self._id_to_model(id_)
            encoding_table = self.model_encoding_table.get(model)
            if encoding_table and data_name in encoding_table:
                sign_bit = encoding_table[data_name]
                ids_values[id_] = encode_sign_magnitude(ids_values[id_], sign_bit)

        return ids_values

    def _decode_sign(self, data_name: str, ids_values: dict[int, int]) -> dict[int, int]:
        for id_ in ids_values:
            model = self._id_to_model(id_)
            encoding_table = self.model_encoding_table.get(model)
            if encoding_table and data_name in encoding_table:
                sign_bit = encoding_table[data_name]
                ids_values[id_] = decode_sign_magnitude(ids_values[id_], sign_bit)

        return ids_values

    def _split_into_byte_chunks(self, value: int, length: int) -> list[int]:
        return _split_into_byte_chunks(value, length)

    def sync_read(
        self,
        data_name: str,
        motors: str | list[str] | None = None,
        *,
        normalize: bool = True,
        num_retry: int = 0,
    ) -> dict[str, Value]:
        """Read the same register from several motors at once."""
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self.__class__.__name__}('{self.port}') is not connected.")

        if self.protocol_version == 1:
            raise NotImplementedError(
                "'Sync Read' is not available with Feetech motors using Protocol 1. Use 'Read' sequentially instead."
            )

        names = self._get_motors_list(motors)
        ids = [self.motors[motor].id for motor in names]
        models = [self.motors[motor].model for motor in names]

        if self._has_different_ctrl_tables:
            from .motors_bus import assert_same_address
            assert_same_address(self.model_ctrl_table, models, data_name)

        model = next(iter(models))
        addr, length = get_address(self.model_ctrl_table, model, data_name)

        err_msg = f"Failed to sync read '{data_name}' on {ids=} after {num_retry + 1} tries."
        ids_values, _ = self._sync_read(
            addr, length, ids, num_retry=num_retry, raise_on_error=True, err_msg=err_msg
        )

        ids_values = self._decode_sign(data_name, ids_values)

        if normalize and data_name in self.normalized_data:
            ids_values = self._normalize(ids_values)

        return {self._id_to_name(id_): value for id_, value in ids_values.items()}

    def _sync_read(
        self,
        addr: int,
        length: int,
        motor_ids: list[int],
        *,
        num_retry: int = 0,
        raise_on_error: bool = True,
        err_msg: str = "",
    ) -> tuple[dict[int, int], int]:
        self._setup_sync_reader(motor_ids, addr, length)
        for n_try in range(1 + num_retry):
            comm = self.sync_reader.txRxPacket()
            if self._is_comm_success(comm):
                break
            logger.debug(
                f"Failed to sync read @{addr=} ({length=}) on {motor_ids=} ({n_try=}): "
                + self.packet_handler.getTxRxResult(comm)
            )

        if not self._is_comm_success(comm) and raise_on_error:
            raise ConnectionError(f"{err_msg} {self.packet_handler.getTxRxResult(comm)}")

        values = {id_: self.sync_reader.getData(id_, addr, length) for id_ in motor_ids}
        return values, comm

    def _setup_sync_reader(self, motor_ids: list[int], addr: int, length: int) -> None:
        self.sync_reader.clearParam()
        self.sync_reader.start_address = addr
        self.sync_reader.data_length = length
        for id_ in motor_ids:
            self.sync_reader.addParam(id_)

    def sync_write(
        self,
        data_name: str,
        values: Value | dict[str, Value],
        *,
        normalize: bool = True,
        num_retry: int = 0,
    ) -> None:
        """Write the same register on multiple motors."""
        if not self.is_connected:
            raise DeviceNotConnectedError(f"{self.__class__.__name__}('{self.port}') is not connected.")

        ids_values = self._get_ids_values_dict(values)
        models = [self._id_to_model(id_) for id_ in ids_values]
        if self._has_different_ctrl_tables:
            from .motors_bus import assert_same_address
            assert_same_address(self.model_ctrl_table, models, data_name)

        model = next(iter(models))
        addr, length = get_address(self.model_ctrl_table, model, data_name)

        if normalize and data_name in self.normalized_data:
            ids_values = self._unnormalize(ids_values)

        ids_values = self._encode_sign(data_name, ids_values)

        err_msg = f"Failed to sync write '{data_name}' with {ids_values=} after {num_retry + 1} tries."
        self._sync_write(addr, length, ids_values, num_retry=num_retry, raise_on_error=True, err_msg=err_msg)

    def _sync_write(
        self,
        addr: int,
        length: int,
        ids_values: dict[int, int],
        num_retry: int = 0,
        raise_on_error: bool = True,
        err_msg: str = "",
    ) -> int:
        self._setup_sync_writer(ids_values, addr, length)
        for n_try in range(1 + num_retry):
            comm = self.sync_writer.txPacket()
            if self._is_comm_success(comm):
                break
            logger.debug(
                f"Failed to sync write @{addr=} ({length=}) with {ids_values=} ({n_try=}): "
                + self.packet_handler.getTxRxResult(comm)
            )

        if not self._is_comm_success(comm) and raise_on_error:
            raise ConnectionError(f"{err_msg} {self.packet_handler.getTxRxResult(comm)}")

        return comm

    def _setup_sync_writer(self, ids_values: dict[int, int], addr: int, length: int) -> None:
        self.sync_writer.clearParam()
        self.sync_writer.start_address = addr
        self.sync_writer.data_length = length
        for id_, value in ids_values.items():
            data = self._serialize_data(value, length)
            self.sync_writer.addParam(id_, data)

    def _get_ids_values_dict(self, values: Value | dict[str, Value] | None) -> dict[int, Value]:
        if isinstance(values, (int, float)):
            return dict.fromkeys(self.ids, values)
        elif isinstance(values, dict):
            return {self.motors[motor].id: val for motor, val in values.items()}
        else:
            raise TypeError(f"'values' is expected to be a single value or a dict. Got {values}")

    # Simplified calibration methods for teleoperation
    @property
    def is_calibrated(self) -> bool:
        """Check if motors are calibrated - simplified version."""
        return bool(self.calibration) and set(self.calibration.keys()) == set(self.motors.keys())

    def read_calibration(self) -> dict[str, MotorCalibration]:
        """Read calibration parameters from the motors."""
        calibration = {}
        for motor, m in self.motors.items():
            min_pos = self.read("Min_Position_Limit", motor, normalize=False)
            max_pos = self.read("Max_Position_Limit", motor, normalize=False)
            offset = 0
            if self.protocol_version == 0:
                offset = self.read("Homing_Offset", motor, normalize=False)
            
            calibration[motor] = MotorCalibration(
                id=m.id,
                drive_mode=0,
                homing_offset=offset,
                range_min=min_pos,
                range_max=max_pos,
            )

        return calibration

    def write_calibration(self, calibration_dict: dict[str, MotorCalibration], cache: bool = True) -> None:
        """Write calibration parameters to the motors."""
        for motor, calibration in calibration_dict.items():
            if self.protocol_version == 0:
                self.write("Homing_Offset", motor, calibration.homing_offset)
            self.write("Min_Position_Limit", motor, calibration.range_min)
            self.write("Max_Position_Limit", motor, calibration.range_max)

        if cache:
            self.calibration = calibration_dict