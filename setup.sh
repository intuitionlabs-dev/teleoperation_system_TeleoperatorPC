#!/bin/bash
# Setup script for teleoperation system (both piper-SO101 and yam-dynamixel)

echo "============================================"
echo "Setting up Teleoperation System"
echo "============================================"

# Check if Python 3.8+ is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Found Python $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source .venv/bin/activate

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo ""
    echo "Installing uv package manager..."
    pip install --upgrade pip
    pip install uv
    echo "✓ uv installed"
else
    echo "✓ uv already installed"
fi

# Install dependencies
echo ""
echo "Installing dependencies..."
uv pip install -r requirements.txt

# Install piper_sdk if available
if [ -d "piper_sdk" ]; then
    echo ""
    echo "Installing piper_sdk..."
    uv pip install -e piper_sdk/
    echo "✓ piper_sdk installed"
fi

# Check installation
echo ""
echo "Verifying installation..."
python -c "import zmq; print(f'✓ ZMQ version: {zmq.zmq_version()}')"
python -c "import draccus; print('✓ draccus imported')"
python -c "import omegaconf; print('✓ omegaconf imported')"
python -c "import can; print('✓ python-can imported')"

# Check for Dynamixel ports (optional for YAM system)
echo ""
echo "Checking USB ports for Dynamixel..."
if [ -e "/dev/ttyACM0" ]; then
    echo "✓ Found /dev/ttyACM0"
else
    echo "⚠ /dev/ttyACM0 not found (needed for YAM/Dynamixel left arm)"
fi

if [ -e "/dev/ttyACM1" ]; then
    echo "✓ Found /dev/ttyACM1"
else
    echo "⚠ /dev/ttyACM1 not found (needed for YAM/Dynamixel right arm)"
fi

echo ""
echo "============================================"
echo "Setup complete!"
echo ""
echo "To use the teleoperation system:"
echo "  1. Activate the environment: source .venv/bin/activate"
echo "  2. Run teleoperation: ./run_teleoperate.sh --system [piper-so101|yam-dynamixel]"
echo ""
echo "For more details, see README.md"
echo "============================================"