#!/bin/bash
# Simple launch script for Teleoperator PC

echo "Starting teleoperation..."
echo ""

# Run bimanual teleoperation
python teleoperate.py \
    --robot-hostname 100.104.247.35 \
    --cmd-port 5555 \
    --fps 60 \
    --left-leader-port /dev/tty.usbmodem5A680101071 \
    --right-leader-port /dev/tty.usbmodem58FA0968181 \
    --calibration-dir calibration \
    --left-arm-calib-name left_arm \
    --right-arm-calib-name right_arm \
    "$@"
