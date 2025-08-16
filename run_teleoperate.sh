#!/bin/bash
# Simple launch script for Teleoperator PC

echo "Starting minimal teleoperation..."
echo "Make sure the conda environment 'lerobot' is activated"
echo ""

# Run bimanual teleoperation
python teleoperate.py \
    --robot-hostname 100.104.247.35 \
    --cmd-port 5555 \
    --obs-port 5556 \
    --fps 60 \
    --gello-left-port /dev/ttyACM0 \
    --gello-right-port /dev/ttyACM1 \
    "$@"
