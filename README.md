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

## Architecture
- Read positions from SO101 leader arms (feetech motors)
- Send commands via ZMQ PUSH (unidirectional)
- No observation feedback
- Simple loop: read leader positions → send command → rate limit
