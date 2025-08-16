# Teleoperation Client (Teleoperator PC)

Minimal ZMQ client for bimanual robot teleoperation using GELLO devices.

## Requirements
- Python with `lerobot` conda environment
- `gello` package
- ZeroMQ (pyzmq)

## Launch
```bash
conda activate lerobot
./run_teleoperate.sh --robot-hostname <ROBOT_IP>
```

## Options
- `--robot-hostname`: Robot PC IP (default: 192.168.123.139)
- `--cmd-port`: Command port (default: 5555)
- `--obs-port`: Observation port (default: 5556)
- `--fps`: Target frequency (default: 30Hz)
- `--gello-left-port`: Left GELLO port (default: /dev/GELLO_L)
- `--gello-right-port`: Right GELLO port (default: /dev/GELLO_R)

## Architecture
- Send commands at 30Hz via ZMQ PUSH
- Receive observations via ZMQ PULL
- Action-first pattern: get action → send → try observation
