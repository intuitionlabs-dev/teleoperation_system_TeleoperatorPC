#!/bin/bash

# X5-Dynamixel Calibration Script
# This script helps calibrate the X5 follower arms with Dynamixel leader arms

echo "========================================"
echo "X5-DYNAMIXEL CALIBRATION"
echo "========================================"
echo ""

# Kill any existing processes using the USB ports
echo "Checking for processes using USB ports..."
for port in /dev/ttyACM2 /dev/ttyACM3; do
    if [ -e "$port" ]; then
        PIDS=$(lsof -t "$port" 2>/dev/null)
        if [ ! -z "$PIDS" ]; then
            echo "Killing processes using $port: $PIDS"
            kill -9 $PIDS 2>/dev/null
            sleep 1
        fi
    fi
done

# Kill any existing calibration or teleoperation processes
echo "Checking for existing calibration/teleoperation processes..."
pkill -f "calibrate_x5.py" 2>/dev/null
pkill -f "teleoperate.py" 2>/dev/null
sleep 1

echo ""
echo "This script will help you calibrate the X5 teleoperation system."
echo ""
echo "PREPARATION CHECKLIST:"
echo "  ✓ X5 follower arms powered on"
echo "  ✓ CAN interfaces configured (can0, can1)"
echo "  ✓ Dynamixel leader arms connected"
echo "  ✓ USB ports: ACM2 (right), ACM3 (left)"
echo ""
echo "CALIBRATION STEPS:"
echo "1. Position both arms in neutral/home position"
echo "2. Ensure leader and follower poses match"
echo "3. Run calibration to capture offsets"
echo "4. Test with teleoperation"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Check CAN interfaces
echo "Checking CAN interfaces..."
if ! ip link show can0 &>/dev/null; then
    echo "ERROR: can0 interface not found!"
    echo "Please configure CAN: sudo ip link set can0 up type can bitrate 1000000"
    exit 1
fi

if ! ip link show can1 &>/dev/null; then
    echo "ERROR: can1 interface not found!"
    echo "Please configure CAN: sudo ip link set can1 up type can bitrate 1000000"
    exit 1
fi

# Check if CAN interfaces are UP
CAN0_STATUS=$(ip link show can0 | grep -o "state [A-Z]*" | cut -d' ' -f2)
CAN1_STATUS=$(ip link show can1 | grep -o "state [A-Z]*" | cut -d' ' -f2)

if [ "$CAN0_STATUS" != "UP" ]; then
    echo "WARNING: can0 is not UP (status: $CAN0_STATUS)"
    echo "Bringing up can0..."
    sudo ip link set can0 up type can bitrate 1000000
fi

if [ "$CAN1_STATUS" != "UP" ]; then
    echo "WARNING: can1 is not UP (status: $CAN1_STATUS)"
    echo "Bringing up can1..."
    sudo ip link set can1 up type can bitrate 1000000
fi

echo "CAN interfaces are ready!"
echo ""

# Set library path for ARX module
export LD_LIBRARY_PATH=/home/group/i2rt/ARX-dynamixel/RobotLearningGello/ARX_X5/py/arx_x5_python/bimanual/lib/arx_x5_src:$LD_LIBRARY_PATH

# Run the calibration script
python calibrate_x5.py \
    --arms both \
    --left-leader-port /dev/ttyACM3 \
    --right-leader-port /dev/ttyACM2 \
    --left-follower-channel can1 \
    --right-follower-channel can0 \
    --reference neutral \
    "$@"

echo ""
echo "========================================"
echo "Calibration process complete!"
echo ""
echo "To test the calibration:"
echo "  ./run_teleoperate.sh x5-dynamixel"
echo ""
echo "If calibration is incorrect, run this script again"
echo "with the arms in a different reference position."
echo "========================================"