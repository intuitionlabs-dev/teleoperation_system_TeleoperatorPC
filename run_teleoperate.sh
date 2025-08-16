#!/bin/bash
# Simple launch script for Teleoperator PC

echo "Starting minimal teleoperation..."
echo "Make sure the conda environment 'lerobot' is activated"
echo ""

# Run bimanual teleoperation
python teleoperate.py \
    --robot-hostname 192.168.123.139 \
    --cmd-port 5555 \
    --obs-port 5556 \
    --fps 30 \
    --gello-left-port /dev/GELLO_L \
    --gello-right-port /dev/GELLO_R \
    "$@"
