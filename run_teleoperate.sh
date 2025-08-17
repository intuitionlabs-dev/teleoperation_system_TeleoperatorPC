#!/bin/bash
# Script to run teleoperation with bimanual SO101 leaders and remote Piper followers

python -m teleoperate \
    --bimanual=true \
    --remote_ip=100.117.16.87 \
    --left_arm_port_teleop=/dev/ttyACM2 \
    --right_arm_port_teleop=/dev/ttyACM0 \
    --teleop_calibration_dir=calibration \
    --left_arm_calib_name=my_left \
    --right_arm_calib_name=my_right