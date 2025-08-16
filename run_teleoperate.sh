#!/bin/bash
# Simple launch script for Teleoperator PC

echo "Starting minimal teleoperation..."
echo "Make sure the conda environment 'lerobot' is activated"
echo ""

# Run bimanual teleoperation
python teleoperate.py \
    --robot-hostname 100.104.247.35 \
    --cmd-port 5555 \
    --fps 60 \
    --left-leader-port /dev/ttyACM0 \
    --right-leader-port /dev/ttyACM1 \
    --calibration-dir calibration \
    --left-arm-calib-name left_arm \
    --right-arm-calib-name right_arm \
    "$@"
