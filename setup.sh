#!/bin/bash
# Setup script for teleoperation system (both piper-SO101 and yam-dynamixel)

echo "============================================"
echo "Setting up Teleoperation System"
echo "============================================"

# Install uv if not present (globally)
if ! command -v uv &> /dev/null; then
    echo ""
    echo "Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
    echo "✓ uv installed"
fi

# Check if Python 3.10+ is available
echo ""
echo "Checking Python version..."
PYTHON_VERSION=$(python3.10 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>/dev/null || echo "not found")
if [ "$PYTHON_VERSION" = "not found" ]; then
    echo "Error: Python 3.10 not found"
    echo "Please install Python 3.10 or higher"
    exit 1
else
    echo "Found Python $PYTHON_VERSION"
    PYTHON_CMD="python3.10"
fi

# Create virtual environment with uv
echo ""
echo "Creating virtual environment with uv..."
if [ ! -d ".venv" ]; then
    uv venv .venv --python $PYTHON_CMD
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
source .venv/bin/activate

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