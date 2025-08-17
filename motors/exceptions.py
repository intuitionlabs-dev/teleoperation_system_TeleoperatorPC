#!/usr/bin/env python

# Copyright 2024 The HuggingFace Inc. team. All rights reserved.
# Simplified version for teleoperation system

class DeviceNotConnectedError(ConnectionError):
    """Exception raised when the device is not connected."""

    def __init__(self, message="This device is not connected. Try calling `connect()` first."):
        self.message = message
        super().__init__(self.message)


class DeviceAlreadyConnectedError(ConnectionError):
    """Exception raised when the device is already connected."""

    def __init__(
        self,
        message="This device is already connected. Try not calling `connect()` twice.",
    ):
        self.message = message
        super().__init__(self.message)


class JointOutOfRangeError(Exception):
    def __init__(self, message="Joint is out of range"):
        self.message = message
        super().__init__(self.message)