# Teleoperation Leader (Teleoperator PC side)

ZMQ client for bimanual robot teleoperation using SO101 leader arms.


## Installation
```bash
git clone https://github.com/intuitionlabs-dev/teleoperation_system_TeleoperatorPC.git
cd teleoperation_system_TeleoperatorPC
conda create -n teleoperate-TeleoperatorPC python=3.10
conda activate teleoperate-TeleoperatorPC
python -m pip install -r requirements.txt
```

## Calibration (First Time Setup)
```bash
cd teleoperation_system_TeleoperatorPC
conda activate teleoperate-TeleoperatorPC
./calibrate_leader.sh
```

Follow the on-screen instructions to calibrate the joint ranges of both arms.

## Launch
```bash
cd teleoperation_system_TeleoperatorPC
conda activate teleoperate-TeleoperatorPC
./run_teleoperate.sh --robot-hostname <ROBOT_IP> 
For example, if the Robot PC IP is 100.104.247.35: ./run_teleoperate.sh --robot-hostname 100.104.247.35
```

## Options
- `--robot-hostname`: Robot PC IP (default: 100.104.247.35)
- `--cmd-port`: Command port (default: 5555)
- `--fps`: Target frequency (default: 60Hz)
- `--left-leader-port`: Left SO101 port (default: /dev/ttyACM0)
- `--right-leader-port`: Right SO101 port (default: /dev/ttyACM1)
- `--calibration-dir`: Directory for calibration files (default: ./calibration)
- `--left-arm-calib-name`: Left arm calibration filename (default: left_arm)
- `--right-arm-calib-name`: Right arm calibration filename (default: right_arm)
- `--calibrate`: Run calibration mode

## Architecture
- Read positions from SO101 leader arms (feetech motors)
- Apply calibration for accurate joint mapping
- Send commands via ZMQ PUSH (unidirectional)
- No observation feedback
- Simple loop: read leader positions → normalize → send command → rate limit
