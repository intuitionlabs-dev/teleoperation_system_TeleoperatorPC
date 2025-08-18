#!/usr/bin/env python3
"""
Motor Enable Publisher - Teleoperator Side
==========================================
Send enable commands to robot PC for ALL 7 motors per arm:
- 6 arm joint motors (1-6) 
- 1 gripper motor (7)

Run this on the teleoperator (Mac) side.

Usage:
    python motor_enable_publisher.py --remote_ip 100.104.247.35
    
Then press:
    'l' + Enter: Enable left arm motors (ALL 7 motors: 6 joints + gripper)
    'r' + Enter: Enable right arm motors (ALL 7 motors: 6 joints + gripper)
    'b' + Enter: Enable both arms (ALL 7 motors each)
    'q' + Enter: Quit
"""

import argparse
import json
import time
import zmq

class MotorEnablePublisher:
    def __init__(self, remote_ip: str, enable_port: int = 5559):
        self.remote_ip = remote_ip
        self.enable_port = enable_port
        self.context = zmq.Context()
        self.socket = None
        self.running = False
        
    def connect(self):
        """Connect to robot PC enable listener"""
        try:
            self.socket = self.context.socket(zmq.PUB)
            self.socket.connect(f"tcp://{self.remote_ip}:{self.enable_port}")
            time.sleep(0.5)  # Allow connection to establish
            print(f"✅ Connected to robot PC at {self.remote_ip}:{self.enable_port}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def send_enable_command(self, arm: str, enable_mode: str = "partial"):
        """Send enable command for specified arm (ALL 7 motors: 6 joints + gripper)
        
        Args:
            arm: "left" or "right"
            enable_mode: "partial" (smart, only disabled motors) or "full" (reset all motors)
        """
        if not self.socket:
            print("❌ Not connected!")
            return
            
        try:
            command = {
                "type": "enable",
                "arm": arm,
                "enable_mode": enable_mode,
                "timestamp": time.time()
            }
            
            mode_desc = "smart mode" if enable_mode == "partial" else "full reset"
            message = json.dumps(command)
            self.socket.send_string(message)
            print(f"📤 Sent {mode_desc} enable command for {arm} arm")
            
        except Exception as e:
            print(f"❌ Failed to send command: {e}")
    
    def start_interactive_mode(self):
        """Start interactive command mode"""
        self.running = True
        
        print("\n🎮 MOTOR ENABLE CONTROL")
        print("=" * 50)
        print("SMART MODE (recommended - only enables problem motors):")
        print("  'l' + Enter: Enable LEFT arm motors (smart - ALL 7 motors)")
        print("  'r' + Enter: Enable RIGHT arm motors (smart - ALL 7 motors)")  
        print("  'b' + Enter: Enable BOTH arms (smart - ALL 7 motors each)")
        print("")
        print("FULL RESET MODE (resets all motors, may cause arm to fall):")
        print("  'L' + Enter: Full reset LEFT arm (ALL 7 motors)")
        print("  'R' + Enter: Full reset RIGHT arm (ALL 7 motors)")
        print("  'B' + Enter: Full reset BOTH arms (ALL 7 motors each)")
        print("")
        print("OTHER:")
        print("  'q' + Enter: Quit")
        print("=" * 50)
        
        try:
            while self.running:
                try:
                    cmd = input("Enable command (l/r/b/L/R/B/q): ").strip()
                    
                    if cmd.lower() == 'q':
                        print("👋 Exiting...")
                        break
                    elif cmd == 'l':
                        self.send_enable_command("left", "partial")
                    elif cmd == 'r':
                        self.send_enable_command("right", "partial")
                    elif cmd == 'b':
                        self.send_enable_command("left", "partial")
                        time.sleep(0.1)  # Small delay between commands
                        self.send_enable_command("right", "partial")
                    elif cmd == 'L':
                        print("⚠️  Full reset mode - arm may fall!")
                        confirm = input("Are you sure? (y/N): ").strip().lower()
                        if confirm == 'y':
                            self.send_enable_command("left", "full")
                        else:
                            print("Cancelled.")
                    elif cmd == 'R':
                        print("⚠️  Full reset mode - arm may fall!")
                        confirm = input("Are you sure? (y/N): ").strip().lower()
                        if confirm == 'y':
                            self.send_enable_command("right", "full")
                        else:
                            print("Cancelled.")
                    elif cmd == 'B':
                        print("⚠️  Full reset mode - both arms may fall!")
                        confirm = input("Are you sure? (y/N): ").strip().lower()
                        if confirm == 'y':
                            self.send_enable_command("left", "full")
                            time.sleep(0.1)  # Small delay between commands
                            self.send_enable_command("right", "full")
                        else:
                            print("Cancelled.")
                    else:
                        print("❌ Invalid command. Use l/r/b (smart) or L/R/B (full reset) or q (quit)")
                        
                except KeyboardInterrupt:
                    print("\n👋 Interrupted, exiting...")
                    break
                except EOFError:
                    print("\n👋 EOF, exiting...")
                    break
                    
        finally:
            self.running = False
            
    def disconnect(self):
        """Cleanup connections"""
        if self.socket:
            self.socket.close()
        self.context.term()

def main():
    parser = argparse.ArgumentParser(description="Motor Enable Publisher for Teleoperation (ALL 7 motors per arm)")
    parser.add_argument("--remote_ip", default="100.104.247.35", 
                        help="IP address of robot PC")
    parser.add_argument("--enable_port", type=int, default=5559,
                        help="ZMQ port for enable commands")
    
    args = parser.parse_args()
    
    publisher = MotorEnablePublisher(args.remote_ip, args.enable_port)
    
    try:
        if publisher.connect():
            publisher.start_interactive_mode()
    finally:
        publisher.disconnect()

if __name__ == "__main__":
    main()