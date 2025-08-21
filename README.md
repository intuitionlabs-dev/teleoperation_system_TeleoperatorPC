# TeleoperatorPC - Teleoperation Client

Supports both **Piper-SO101** and **YAM-Dynamixel** teleoperation systems.

## Quick Start

```bash
# 1. Setup (first time only)
./setup.sh

# 2. Activate environment
source .venv/bin/activate

# 3. Run teleoperation
./run_teleoperate.sh --system piper-so101 --remote-ip 100.104.247.35  # For Piper
./run_teleoperate.sh --system yam-dynamixel --remote-ip 100.119.166.86  # For YAM
```

## Systems

### Piper-SO101 (Default)
- Leader: SO101 arms via USB
- Follower: Piper robots
- Default IP: 100.117.16.87
- Ports: 5555-5558

### YAM-Dynamixel
- Leader: Dynamixel arms via USB
- Follower: YAM robots
- Default IP: 100.119.166.86
- Ports: 5565-5568

## USB Ports
Both systems use `/dev/ttyACM0` (left) and `/dev/ttyACM1` (right)

## Calibration

### SO101
Run calibration on first use:
```bash
python -m teleoperate --system piper-so101 --bimanual=true --remote_ip=100.104.247.35
```

### Dynamixel/YAM
Run calibration to generate config files:
```bash
./calibrate_yam.sh
```
Position arms straight up (known position) when prompted.

## Motor Control (Optional)

Enable/reset motors remotely:
```bash
# Piper
python motor_enable_publisher.py --remote_ip 100.104.247.35

# YAM
python yam_motor_enable_publisher.py --remote_ip 100.119.166.86
```

Commands:
- `l/r/b`: Enable left/right/both (partial)
- `L/R/B`: Reset left/right/both (full)
- `q`: Quit

## Troubleshooting

- **USB Permission**: `sudo usermod -a -G dialout $USER` (logout/login required)
- **Port Not Found**: Check connections with `ls /dev/ttyACM*`
- **Connection Timeout**: Verify Robot PC is running and accessible