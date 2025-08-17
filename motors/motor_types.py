#!/usr/bin/env python

# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
# Simplified version for teleoperation system

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias

NameOrID: TypeAlias = str | int
Value: TypeAlias = int | float


class MotorNormMode(str, Enum):
    RANGE_0_100 = "range_0_100"
    RANGE_M100_100 = "range_m100_100"
    DEGREES = "degrees"


@dataclass
class MotorCalibration:
    id: int
    drive_mode: int
    homing_offset: int
    range_min: int
    range_max: int


@dataclass
class Motor:
    id: int
    model: str
    norm_mode: MotorNormMode