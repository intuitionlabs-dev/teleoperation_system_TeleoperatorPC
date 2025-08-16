#!/bin/bash
# Calibration script for SO101 leader arms

echo "=== SO101 Leader Arms Calibration ==="
echo "Make sure the conda environment is activated"
echo ""

# Run calibration mode
python teleoperate.py \
    --calibrate \
    --left-leader-port /dev/ttyACM1 \
    --right-leader-port /dev/ttyACM0 \
    --calibration-dir calibration \
    --left-arm-calib-name left_arm \
    --right-arm-calib-name right_arm \
    "$@"
