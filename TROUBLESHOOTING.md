# SO101 Troubleshooting Guide

## Common Issues

### 1. Cannot find SO101 ports
```bash
# List all USB devices
ls /dev/ttyACM* /dev/ttyUSB*

# Find SO101 devices
dmesg | grep -i "usb\|tty"
```

### 2. Permission denied on port
```bash
# Add user to dialout group
sudo usermod -a -G dialout $USER
# Logout and login again
```

### 3. Wrong baudrate
Default is 1000000 (1Mbps). If motors don't respond, check:
- Motor baudrate settings
- USB-to-serial adapter compatibility

### 4. Motor IDs conflict
SO101 expects motors with IDs 1-6 on each arm. If motors have different IDs:
1. Use Feetech Debug software to check/change IDs
2. Or modify `self.motor_ids` in `so101_teleoperator.py`

### 5. Import error for scservo_sdk
```bash
pip install scservo-sdk
# or
pip install git+https://github.com/FeetechRC/Python_SDK.git
```

### 6. Motors not moving
- Check if torque is disabled (should be for leader arms)
- Verify power supply to motors
- Check mechanical limits

### 7. Position reading errors
- Ensure good USB connection
- Try lower baudrate (500000 or 250000)
- Check for electromagnetic interference
