#!/bin/bash
# Calibration script for YAM-Dynamixel arms

echo "============================================"
echo "YAM-Dynamixel Calibration"
echo "============================================"

# Check if configs already exist
LEFT_CONFIG="third_party/configs/yam_auto_generated_left.yaml"
RIGHT_CONFIG="third_party/configs/yam_auto_generated_right.yaml"

if [ -f "$LEFT_CONFIG" ] && [ -f "$RIGHT_CONFIG" ]; then
    echo ""
    echo "✓ Calibration files already exist:"
    echo "  - $LEFT_CONFIG"
    echo "  - $RIGHT_CONFIG"
    echo ""
    read -p "Do you want to recalibrate? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Using existing calibration."
        exit 0
    fi
fi

# Activate environment
if [ ! -d ".venv" ]; then
    echo "Error: Virtual environment not found. Run ./setup.sh first."
    exit 1
fi

source .venv/bin/activate

# Calibrate left arm
echo ""
echo "Step 1: Calibrating LEFT arm"
echo "--------------------------------------------"
echo "Connect the LEFT Dynamixel arm to /dev/ttyACM0"
echo ""
read -p "Press Enter when ready..."

python generate_yam_config.py \
    --port /dev/ttyACM0 \
    --output_path "$LEFT_CONFIG" \
    --sim_output_path "third_party/configs/yam_auto_generated_left_sim.yaml"

if [ $? -ne 0 ]; then
    echo "Error: Failed to calibrate left arm"
    exit 1
fi

echo "✓ Left arm calibrated"

# Calibrate right arm
echo ""
echo "Step 2: Calibrating RIGHT arm"
echo "--------------------------------------------"
echo "Connect the RIGHT Dynamixel arm to /dev/ttyACM1"
echo ""
read -p "Press Enter when ready..."

python generate_yam_config.py \
    --port /dev/ttyACM1 \
    --output_path "$RIGHT_CONFIG" \
    --sim_output_path "third_party/configs/yam_auto_generated_right_sim.yaml"

if [ $? -ne 0 ]; then
    echo "Error: Failed to calibrate right arm"
    exit 1
fi

echo "✓ Right arm calibrated"

echo ""
echo "============================================"
echo "Calibration complete!"
echo ""
echo "Generated files:"
echo "  - $LEFT_CONFIG"
echo "  - $RIGHT_CONFIG"
echo ""
echo "You can now run teleoperation with:"
echo "  ./run_teleoperate.sh --system yam-dynamixel"
echo "============================================"