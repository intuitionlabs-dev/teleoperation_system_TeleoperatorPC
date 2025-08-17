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

```bash
./run_teleoperate.sh
```

Or manually:
```bash
python -m teleoperate \
    --bimanual=true \
    --remote_ip=100.117.16.87 \
    --left_arm_port_teleop=/dev/ttyACM2 \
    --right_arm_port_teleop=/dev/ttyACM0 \
    --teleop_calibration_dir=calibration \
    --left_arm_calib_name=my_left \
    --right_arm_calib_name=my_right
```

## Configuration
- Update `--remote_ip` with your Robot PC's IP address
- Check USB ports for SO101 arms (`/dev/ttyACM*`)
- Calibration files are saved in `calibration/` directory
