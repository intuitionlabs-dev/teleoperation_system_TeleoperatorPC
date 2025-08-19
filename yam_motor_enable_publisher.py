#!/usr/bin/env python
"""
YAM Motor Enable Publisher - Send motor enable commands to remote YAM robot.
Provides interactive terminal interface for enabling/resetting YAM motors.
"""

import json
import logging
import sys
import time
from dataclasses import dataclass
from typing import Optional

import zmq

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class YAMMotorEnableConfig:
    """Configuration for YAM motor enable publisher."""
    remote_ip: str = "100.117.16.87"
    remote_port: int = 5569  # YAM uses 5569 for motor enable
    timeout_ms: int = 1000


class YAMMotorEnablePublisher:
    """Publisher for sending motor enable commands to YAM robot."""
    
    def __init__(self, config: YAMMotorEnableConfig):
        self.config = config
        self.zmq_context = None
        self.zmq_socket = None
        self._is_connected = False
    
    def connect(self):
        """Connect to remote YAM motor enable listener."""
        if self._is_connected:
            logger.warning("Already connected")
            return
        
        self.zmq_context = zmq.Context()
        self.zmq_socket = self.zmq_context.socket(zmq.PUSH)
        
        zmq_url = f"tcp://{self.config.remote_ip}:{self.config.remote_port}"
        self.zmq_socket.connect(zmq_url)
        self.zmq_socket.setsockopt(zmq.SNDTIMEO, self.config.timeout_ms)
        
        self._is_connected = True
        logger.info(f"Connected to YAM motor enable listener at {zmq_url}")
    
    def disconnect(self):
        """Disconnect from remote listener."""
        if not self._is_connected:
            return
        
        if self.zmq_socket:
            self.zmq_socket.close()
        if self.zmq_context:
            self.zmq_context.term()
        
        self._is_connected = False
        logger.info("Disconnected")
    
    def send_command(self, command: dict) -> bool:
        """Send a command to the remote listener."""
        if not self._is_connected:
            logger.error("Not connected")
            return False
        
        try:
            msg = json.dumps(command)
            self.zmq_socket.send_string(msg)
            return True
        except zmq.error.Again:
            logger.error("Send timeout - robot may be offline")
            return False
        except Exception as e:
            logger.error(f"Failed to send command: {e}")
            return False
    
    def enable_motors(self, target: str = "both", mode: str = "partial"):
        """Enable motors on specified arms."""
        command = {
            "action": "enable",
            "target": target,
            "mode": mode,
        }
        
        if self.send_command(command):
            logger.info(f"Sent enable command: target={target}, mode={mode}")
        else:
            logger.error("Failed to send enable command")
    
    def reset_motors(self, target: str = "both"):
        """Reset (full enable) motors on specified arms."""
        command = {
            "action": "reset",
            "target": target,
        }
        
        if self.send_command(command):
            logger.info(f"Sent reset command: target={target}")
        else:
            logger.error("Failed to send reset command")
    
    def request_status(self):
        """Request motor status from robot."""
        command = {
            "action": "status",
        }
        
        if self.send_command(command):
            logger.info("Requested motor status")
        else:
            logger.error("Failed to request status")
    
    def interactive_mode(self):
        """Run interactive terminal interface."""
        print("\n" + "="*60)
        print("YAM Motor Enable Control")
        print("="*60)
        print("\nCommands:")
        print("  l  - Enable left arm (partial mode - only disabled motors)")
        print("  r  - Enable right arm (partial mode)")
        print("  b  - Enable both arms (partial mode)")
        print("  L  - Reset left arm (full mode - all motors)")
        print("  R  - Reset right arm (full mode)")
        print("  B  - Reset both arms (full mode)")
        print("  s  - Request motor status")
        print("  q  - Quit")
        print("\nPartial mode: Only enables motors that are currently disabled")
        print("Full mode: Resets and enables all motors (use with caution)")
        print("="*60 + "\n")
        
        while True:
            try:
                cmd = input("Command> ").strip().lower()
                
                if cmd == 'q':
                    print("Exiting...")
                    break
                elif cmd == 'l':
                    self.enable_motors("left", "partial")
                elif cmd == 'r':
                    self.enable_motors("right", "partial")
                elif cmd == 'b':
                    self.enable_motors("both", "partial")
                elif cmd == 'L':
                    print("WARNING: Full reset may cause arm to move!")
                    confirm = input("Confirm reset left arm? (y/n): ").strip().lower()
                    if confirm == 'y':
                        self.reset_motors("left")
                elif cmd == 'R':
                    print("WARNING: Full reset may cause arm to move!")
                    confirm = input("Confirm reset right arm? (y/n): ").strip().lower()
                    if confirm == 'y':
                        self.reset_motors("right")
                elif cmd == 'B':
                    print("WARNING: Full reset may cause both arms to move!")
                    confirm = input("Confirm reset both arms? (y/n): ").strip().lower()
                    if confirm == 'y':
                        self.reset_motors("both")
                elif cmd == 's':
                    self.request_status()
                else:
                    print(f"Unknown command: {cmd}")
                
            except KeyboardInterrupt:
                print("\nInterrupted")
                break
            except Exception as e:
                logger.error(f"Error: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="YAM Motor Enable Publisher")
    parser.add_argument("--remote-ip", default="100.117.16.87",
                        help="Remote robot IP address")
    parser.add_argument("--remote-port", type=int, default=5569,
                        help="Remote motor enable port")
    parser.add_argument("--one-shot", action="store_true",
                        help="Send single enable command and exit")
    parser.add_argument("--target", default="both",
                        choices=["left", "right", "both"],
                        help="Target arm(s) for one-shot mode")
    parser.add_argument("--mode", default="partial",
                        choices=["partial", "full"],
                        help="Enable mode for one-shot")
    args = parser.parse_args()
    
    config = YAMMotorEnableConfig(
        remote_ip=args.remote_ip,
        remote_port=args.remote_port,
    )
    
    publisher = YAMMotorEnablePublisher(config)
    
    try:
        publisher.connect()
        
        if args.one_shot:
            # One-shot mode - send command and exit
            if args.mode == "full":
                publisher.reset_motors(args.target)
            else:
                publisher.enable_motors(args.target, args.mode)
            time.sleep(0.5)  # Give time for command to send
        else:
            # Interactive mode
            publisher.interactive_mode()
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise
    finally:
        publisher.disconnect()


if __name__ == "__main__":
    main()