# Teleoperation Client (Teleoperator PC)

Minimal ZMQ client for bimanual robot teleoperation using SO101 leader arms.

## Requirements
- Python with `lerobot` conda environment
- `scservo-sdk` package (for feetech motors)
- ZeroMQ (pyzmq)
- SO101 leader arms connected via USB

## Installation
```bash
conda activate lerobot
pip install -r requirements.txt
```

## Launch
```bash
conda activate lerobot
./run_teleoperate.sh --robot-hostname <ROBOT_IP>
```

## Options
- `--robot-hostname`: Robot PC IP (default: 100.104.247.35)
- `--cmd-port`: Command port (default: 5555)
- `--fps`: Target frequency (default: 60Hz)
- `--left-leader-port`: Left SO101 port (default: /dev/ttyACM0)
- `--right-leader-port`: Right SO101 port (default: /dev/ttyACM1)

## Architecture
- Read positions from SO101 leader arms (feetech motors)
- Send commands via ZMQ PUSH (unidirectional)
- No observation feedback
- Simple loop: read leader positions → send command → rate limit
