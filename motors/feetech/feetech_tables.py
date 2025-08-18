#!/usr/bin/env python

# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
# Simplified version for teleoperation system

FIRMWARE_MAJOR_VERSION = (0, 1)
FIRMWARE_MINOR_VERSION = (1, 1)
MODEL_NUMBER = (3, 2)

# Control table for STS/SMS series motors (commonly used in SO101)
STS_SMS_SERIES_CONTROL_TABLE = {
    # EPROM
    "Firmware_Major_Version": FIRMWARE_MAJOR_VERSION,  # read-only
    "Firmware_Minor_Version": FIRMWARE_MINOR_VERSION,  # read-only
    "Model_Number": MODEL_NUMBER,  # read-only
    "ID": (5, 1),
    "Baud_Rate": (6, 1),
    "Return_Delay_Time": (7, 1),
    "Response_Status_Level": (8, 1),
    "Min_Position_Limit": (9, 2),
    "Max_Position_Limit": (11, 2),
    "Max_Temperature_Limit": (13, 1),
    "Max_Voltage_Limit": (14, 1),
    "Min_Voltage_Limit": (15, 1),
    "Max_Torque_Limit": (16, 2),
    "Phase": (18, 1),
    "Unloading_Condition": (19, 1),
    "LED_Alarm_Condition": (20, 1),
    "P_Coefficient": (21, 1),
    "D_Coefficient": (22, 1),
    "I_Coefficient": (23, 1),
    "Minimum_Startup_Force": (24, 2),
    "CW_Dead_Zone": (26, 1),
    "CCW_Dead_Zone": (27, 1),
    "Protection_Current": (28, 2),
    "Angular_Resolution": (30, 1),
    "Homing_Offset": (31, 2),
    "Operating_Mode": (33, 1),
    "Protective_Torque": (34, 1),
    "Protection_Time": (35, 1),
    "Overload_Torque": (36, 1),
    "Velocity_closed_loop_P_proportional_coefficient": (37, 1),
    "Over_Current_Protection_Time": (38, 1),
    "Velocity_closed_loop_I_integral_coefficient": (39, 1),
    # SRAM
    "Torque_Enable": (40, 1),
    "Acceleration": (41, 1),
    "Goal_Position": (42, 2),
    "Goal_Time": (44, 2),
    "Goal_Velocity": (46, 2),
    "Torque_Limit": (48, 2),
    "Lock": (55, 1),
    "Present_Position": (56, 2),  # read-only
    "Present_Velocity": (58, 2),  # read-only
    "Present_Load": (60, 2),  # read-only
    "Present_Voltage": (62, 1),  # read-only
    "Present_Temperature": (63, 1),  # read-only
    "Status": (65, 1),  # read-only
    "Moving": (66, 1),  # read-only
    "Present_Current": (69, 2),  # read-only
    "Goal_Position_2": (71, 2),  # read-only
    # Factory
    "Moving_Velocity": (80, 1),
    "Moving_Velocity_Threshold": (80, 1),
    "DTs": (81, 1),  # (ms)
    "Velocity_Unit_factor": (82, 1),
    "Hts": (83, 1),  # (ns) valid for firmware >= 2.54, other versions keep 0
    "Maximum_Velocity_Limit": (84, 1),
    "Maximum_Acceleration": (85, 1),
    "Acceleration_Multiplier ": (86, 1),  # Acceleration multiplier in effect when acceleration is 0
}

STS_SMS_SERIES_BAUDRATE_TABLE = {
    1_000_000: 0,
    500_000: 1,
    250_000: 2,
    128_000: 3,
    115_200: 4,
    57_600: 5,
    38_400: 6,
    19_200: 7,
}

MODEL_CONTROL_TABLE = {
    "sts_series": STS_SMS_SERIES_CONTROL_TABLE,
    "sms_series": STS_SMS_SERIES_CONTROL_TABLE,
    "sts3215": STS_SMS_SERIES_CONTROL_TABLE,
    "sts3250": STS_SMS_SERIES_CONTROL_TABLE,
    "sm8512bl": STS_SMS_SERIES_CONTROL_TABLE,
}

MODEL_RESOLUTION = {
    "sts_series": 4096,
    "sms_series": 4096,
    "sts3215": 4096,
    "sts3250": 4096,
    "sm8512bl": 4096,
}

MODEL_BAUDRATE_TABLE = {
    "sts_series": STS_SMS_SERIES_BAUDRATE_TABLE,
    "sms_series": STS_SMS_SERIES_BAUDRATE_TABLE,
    "sm8512bl": STS_SMS_SERIES_BAUDRATE_TABLE,
    "sts3215": STS_SMS_SERIES_BAUDRATE_TABLE,
    "sts3250": STS_SMS_SERIES_BAUDRATE_TABLE,
}

# Sign-Magnitude encoding bits
STS_SMS_SERIES_ENCODINGS_TABLE = {
    "Homing_Offset": 11,
    "Goal_Velocity": 15,
    "Present_Velocity": 15,
}

MODEL_ENCODING_TABLE = {
    "sts_series": STS_SMS_SERIES_ENCODINGS_TABLE,
    "sms_series": STS_SMS_SERIES_ENCODINGS_TABLE,
    "sts3215": STS_SMS_SERIES_ENCODINGS_TABLE,
    "sts3250": STS_SMS_SERIES_ENCODINGS_TABLE,
    "sm8512bl": STS_SMS_SERIES_ENCODINGS_TABLE,
}

SCAN_BAUDRATES = [
    19_200,
    38_400,
    57_600,
    115_200,
    128_000,
    250_000,
    500_000,
    1_000_000,
]

MODEL_NUMBER_TABLE = {
    "sts3215": 777,
    "sts3250": 2825,
    "sm8512bl": 11272,
}

MODEL_PROTOCOL = {
    "sts_series": 0,
    "sms_series": 0,
    "sts3215": 0,
    "sts3250": 0,
    "sm8512bl": 0,
}