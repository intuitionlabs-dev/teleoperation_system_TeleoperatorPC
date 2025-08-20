#!/bin/bash
# Script to run teleoperation with various leader-follower systems

# Default configuration
SYSTEM="piper-so101"
REMOTE_IP=""  # Will be set based on system
FPS=60

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --system)
            SYSTEM="$2"
            shift 2
            ;;
        --remote-ip)
            REMOTE_IP="$2"
            shift 2
            ;;
        --fps)
            FPS="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--system SYSTEM] [--remote-ip IP] [--fps FPS]"
            echo "  --system: piper-so101 or yam-dynamixel (default: piper-so101)"
            echo "  --remote-ip: Robot PC IP address"
            echo "             Default for piper-so101: 100.117.16.87"
            echo "             Default for yam-dynamixel: 100.119.166.86"
            echo "  --fps: Control frequency (default: 60)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Set default IP based on system if not specified
if [ -z "$REMOTE_IP" ]; then
    if [ "$SYSTEM" = "yam-dynamixel" ]; then
        REMOTE_IP="100.119.166.86"
    else
        REMOTE_IP="100.104.247.35"
    fi
fi

echo "Starting teleoperation client"
echo "System: $SYSTEM"
echo "Remote IP: $REMOTE_IP"
echo "FPS: $FPS"

# Activate virtual environment if using YAM system
if [ "$SYSTEM" = "yam-dynamixel" ]; then
    # Get the directory where this script is located
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    VENV_PATH="$SCRIPT_DIR/../i2rt/gello_software/.venv"
    if [ -f "$VENV_PATH/bin/activate" ]; then
        echo "Activating virtual environment for YAM system..."
        source "$VENV_PATH/bin/activate"
        # Add i2rt to PYTHONPATH for YAM system
        export PYTHONPATH="$SCRIPT_DIR/../i2rt:$PYTHONPATH"
    fi
fi

# Run the teleoperation client with system-specific defaults
if [ "$SYSTEM" = "piper-so101" ]; then
    python -m teleoperate \
        --system "$SYSTEM" \
        --bimanual=true \
        --remote_ip="$REMOTE_IP" \
        --left_arm_port_teleop=/dev/ttyACM0 \
        --right_arm_port_teleop=/dev/ttyACM1 \
        --teleop_calibration_dir=calibration/so101 \
        --left_arm_calib_name=my_left \
        --right_arm_calib_name=my_right \
        --fps="$FPS"
elif [ "$SYSTEM" = "yam-dynamixel" ]; then
    python -m teleoperate \
        --system "$SYSTEM" \
        --bimanual=true \
        --remote_ip="$REMOTE_IP" \
        --yam_left_port=/dev/ttyACM0 \
        --yam_right_port=/dev/ttyACM1 \
        --fps="$FPS"
else
    echo "Unknown system: $SYSTEM"
    exit 1
fi