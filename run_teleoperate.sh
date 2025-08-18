#!/bin/bash
# Script to run teleoperation with bimanual SO101 leaders and remote Piper followers


python -m teleoperate \
      --bimanual=true \
      --remote_ip=100.104.247.35 \
      --left_arm_port_teleop=/dev/tty.usbmodem5A680101071 \
      --right_arm_port_teleop=/dev/tty.usbmodem58FA0968181  \
      --teleop_calibration_dir=calibration/so101 \
      --left_arm_calib_name=my_left \
      --right_arm_calib_name=my_right

      
# python -m teleoperate \
#     --bimanual=true \
#     --remote_ip=100.104.247.35 \
#     --left_arm_port_teleop=/dev/ttyACM1 \
#     --right_arm_port_teleop=/dev/ttyACM0 \
#     --teleop_calibration_dir=calibration/so101 \
#     --left_arm_calib_name=my_left \
#     --right_arm_calib_name=my_right