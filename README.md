# TeleoperatorPC - Teleoperation Client

Supports **Piper-SO101**, **YAM-Dynamixel**, and **X5-Dynamixel** teleoperation systems.

## Requirements

- Python 3.10 or higher
- USB access for leader arms

## Quick Start

```bash
# 1. Setup (first time only)
./setup.sh

# 2. Activate environment
source .venv/bin/activate

# 3. Run teleoperation
./run_teleoperate.sh --system piper-so101 --remote-ip 100.104.247.35  # For Piper
./run_teleoperate.sh --system yam-dynamixel --remote-ip 100.119.166.86  # For YAM
./run_teleoperate.sh --system x5-dynamixel --remote-ip 127.0.0.1  # For X5 (local test)
./run_teleoperate.sh --system x5-dynamixel --remote-ip 100.119.166.86  # For X5 (remote)
```

## Systems

### Piper-SO101Default)
- Leader: SO101 arms via USB
- Follower: Piper robots
- Default IP: 100.117.16.87
- Ports: 5555-5558

### YAM-Dynamixel
- Leader: Dynamixel arms via USB
- Follower: YAM robots
- Default IP: 100.119.166.86
- Ports: 5565-5568

### X5-Dynamixel
- Leader: Dynamixel arms via USB
- Follower: ARX X5 robots
- Default IP: 127.0.0.1 (local) or 100.119.166.86 (remote)
- Ports: 5575-5578

## USB Ports
- Piper/YAM: `/dev/ttyACM0` (left) and `/dev/ttyACM1` (right)
- X5: `/dev/ttyACM3` (left) and `/dev/ttyACM2` (right)

## Calibration

### SO101
Run calibration on first use:
```bash
python -m teleoperate --system piper-so101 --bimanual=true --remote_ip=100.104.247.35
```

### YAM-Dynamixel
Run calibration to generate config files:
```bash
./calibrate_yam.sh
```
Position arms straight up (known position) when prompted.

### X5-Dynamixel
Run calibration to generate config files:
```bash
./calibrate_x5.sh
```
Position both leader and follower arms in matching neutral positions when prompted.
The script will:
1. Capture current positions from both systems
2. Calculate joint offsets and signs
3. Generate configuration files automatically

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