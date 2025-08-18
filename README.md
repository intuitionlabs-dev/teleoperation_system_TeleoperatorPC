# Teleoperator PC - SO101 Leader Control

Controls remote Piper arms using two SO101 leader arms.

## Setup

```bash
# Create environment
conda create -n teleop_control python=3.10 -y
conda activate teleop_control

# Install dependencies
pip install -r requirements.txt
```

## Calibration (First Time Only)

```bash
python -m teleoperate --bimanual=true --remote_ip=<ROBOT_IP>
# Follow on-screen calibration instructions
```

## Run

### Main Teleoperation

```bash
./run_teleoperate.sh
```

Or manually:
```bash
python -m teleoperate \
    --bimanual=true \
    --remote_ip=100.104.247.35 \
    --left_arm_port_teleop=/dev/ttyACM1 \
    --right_arm_port_teleop=/dev/ttyACM0 \
    --teleop_calibration_dir=calibration \
    --left_arm_calib_name=my_left \
    --right_arm_calib_name=my_right
```

### Motor Enable Control (Optional)

Run in a separate terminal to remotely enable/reset robot motors:

```bash
python motor_enable_publisher.py --remote_ip 100.104.247.35
```

Interactive commands:
- `l`: Enable left arm (smart mode)
- `r`: Enable right arm (smart mode)
- `b`: Enable both arms (smart mode)
- `L`: Full reset left arm (caution: arm may fall)
- `R`: Full reset right arm (caution: arm may fall)
- `B`: Full reset both arms (caution: arms may fall)
- `q`: Quit

## Configuration
- Update `--remote_ip` with your Robot PC's IP address
- Check USB ports for SO101 arms (`/dev/ttyACM*`)
- Calibration files are saved in `calibration/` directory
