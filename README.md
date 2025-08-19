# Teleoperator PC - Multi-System Leader Control

Controls remote robot arms using either SO101 or Dynamixel (YAM) leader arms.

## Supported Systems

- **piper-so101**: Piper follower arms controlled by SO101 leaders
- **yam-dynamixel**: YAM follower arms controlled by Dynamixel leaders

## Setup

### For Piper-SO101 System
```bash
# Create environment
conda create -n teleop_control python=3.10 -y
conda activate teleop_control

# Install dependencies
pip install -r requirements.txt
```

### For YAM-Dynamixel System
```bash
# Use the existing gello virtual environment
source /home/francesco/meta-tele-RTX/clean_version/i2rt/gello_software/.venv/bin/activate

# Install additional dependencies if needed
pip install -r requirements.txt
```

## Calibration

### SO101 Leaders (First Time Only)
```bash
python -m teleoperate --system piper-so101 --bimanual=true --remote_ip=<ROBOT_IP>
# Follow on-screen calibration instructions
```

### Dynamixel Leaders
No calibration needed - uses absolute encoders

## Run

### Quick Start

```bash
# For Piper-SO101 system (default)
./run_teleoperate.sh

# For YAM-Dynamixel system
./run_teleoperate.sh --system yam-dynamixel

# With custom robot IP
./run_teleoperate.sh --system yam-dynamixel --remote-ip 192.168.1.100
```

### Manual Commands

#### Piper-SO101 System
```bash
python -m teleoperate \
    --system piper-so101 \
    --bimanual=true \
    --remote_ip=100.117.16.87 \
    --left_arm_port_teleop=/dev/ttyACM0 \
    --right_arm_port_teleop=/dev/ttyACM1 \
    --teleop_calibration_dir=calibration/so101 \
    --left_arm_calib_name=my_left \
    --right_arm_calib_name=my_right
```

#### YAM-Dynamixel System
```bash
python -m teleoperate \
    --system yam-dynamixel \
    --bimanual=true \
    --remote_ip=100.119.166.86 \
    --fps=60
```

### Motor Enable Control (Optional)

#### Piper System
Run in a separate terminal to remotely enable/reset Piper motors:

```bash
python motor_enable_publisher.py --remote_ip 100.117.16.87
```

#### YAM System
Run in a separate terminal to remotely enable/reset YAM motors:

```bash
# Quick start with defaults (connects to 100.119.166.86)
./run_yam_motor_publisher.sh

# Or with custom robot IP
./run_yam_motor_publisher.sh --remote-ip 192.168.1.100

# Or manually
python yam_motor_enable_publisher.py --remote-ip 100.119.166.86
```

Interactive commands (both systems):
- `l`: Enable left arm (partial mode)
- `r`: Enable right arm (partial mode)
- `b`: Enable both arms (partial mode)
- `L`: Full reset left arm (caution: arm may move)
- `R`: Full reset right arm (caution: arm may move)
- `B`: Full reset both arms (caution: arms may move)
- `s`: Request status (YAM only)
- `q`: Quit

## Configuration

### Network
- Default Robot PC IPs (via Tailscale):
  - Piper-SO101 system: `100.117.16.87`
  - YAM-Dynamixel system: `100.119.166.86`
- Update `--remote_ip` with your Robot PC's IP address if different

### SO101 System
- Check USB ports for SO101 arms (`/dev/ttyACM*`)
- Calibration files are saved in `calibration/so101/` directory

### YAM-Dynamixel System
- Configuration files: `/home/francesco/meta-tele-RTX/clean_version/i2rt/gello_software/configs/`
- No calibration files needed (absolute encoders)
- Uses ports 5565-5568 for teleoperation (vs 5555-5558 for Piper)
- Motor enable on port 5569 (vs 5559 for Piper)
