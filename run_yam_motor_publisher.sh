#!/bin/bash
# Launch script for YAM motor enable publisher

# Activate virtual environment if it exists
VENV_PATH="/home/francesco/meta-tele-RTX/clean_version/i2rt/gello_software/.venv"
if [ -f "$VENV_PATH/bin/activate" ]; then
    source "$VENV_PATH/bin/activate"
fi

# Default configuration
REMOTE_IP="100.119.166.86"
REMOTE_PORT=5569

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --remote-ip)
            REMOTE_IP="$2"
            shift 2
            ;;
        --remote-port)
            REMOTE_PORT="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--remote-ip IP] [--remote-port PORT]"
            echo "  --remote-ip: Robot PC IP address (default: 100.119.166.86)"
            echo "  --remote-port: Motor enable port (default: 5569)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo "Starting YAM Motor Enable Publisher"
echo "Remote IP: $REMOTE_IP"
echo "Remote port: $REMOTE_PORT"
echo ""
echo "Connecting to YAM robot..."

python yam_motor_enable_publisher.py \
    --remote-ip "$REMOTE_IP" \
    --remote-port "$REMOTE_PORT"