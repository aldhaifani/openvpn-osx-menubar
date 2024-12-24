"""
OpenVPN Menu Bar Application for macOS.

This module provides a menu bar application that manages OpenVPN connections
and displays the assigned IP address.
"""
import argparse
import datetime
import logging
import pathlib
import re
import select
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from typing import Optional, List

import rumps
from pyperclip import copy


@dataclass
class VPNConfig:
    """Configuration settings for the VPN connection."""
    ovpn_file: pathlib.Path
    log_file: Optional[pathlib.Path] = None
    connection_timeout: int = 10  # seconds
    important_events: List[str] = (
    'CONNECTED', 'DISCONNECT', 'AUTH_FAILED', 'TLS_ERROR', 'PUSH_REPLY', 'Initialization Sequence Completed', 'ERROR:',
    'FATAL:', 'TCP connection established', 'Peer Connection Initiated', 'Connection reset')


class VPNConnectionError(Exception):
    """Custom exception for VPN connection related errors."""
    pass


class OpenVPNManager:
    """Manages OpenVPN process and connection state."""

    def __init__(self, config: VPNConfig):
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Configure logging based on the provided configuration."""
        self.logger = logging.getLogger('OVPN')

        # Set up logging format
        formatter = logging.Formatter(
            '%(asctime)s (%(name)s) - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        if self.config.log_file:
            # File handler for logging to file
            file_handler = logging.FileHandler(self.config.log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        else:
            # NullHandler when no logging file is specified
            self.logger.addHandler(logging.NullHandler())

        self.logger.setLevel(logging.INFO)

    def validate_config_file(self) -> None:
        """Validate the OpenVPN configuration file."""
        try:
            content = self.config.ovpn_file.read_text()
            required_params = ['remote ', 'dev ', 'proto ']
            if not any(param in content for param in required_params):
                raise VPNConnectionError("Invalid OpenVPN configuration - missing required parameters")
        except (IOError, PermissionError) as e:
            raise VPNConnectionError(f"Failed to read OpenVPN config: {e}")

    def start_connection(self) -> Optional[str]:
        """Start the OpenVPN connection and return the assigned IP address."""
        self.validate_config_file()

        cmd = ['sudo', 'openvpn', str(self.config.ovpn_file)]

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            return self._monitor_connection()

        except Exception as e:
            self.logger.error(f"Failed to start OpenVPN: {e}")
            self.cleanup()
            raise VPNConnectionError(f"Failed to start OpenVPN: {e}")

    def _monitor_connection(self) -> Optional[str]:
        """Monitor the OpenVPN connection and extract the IP address."""
        start_time = last_output_time = datetime.datetime.now()
        ip_address = None

        while True:
            if self.process.poll() is not None:
                raise VPNConnectionError(f"OpenVPN process terminated with code {self.process.returncode}")

            reads = [self.process.stdout.fileno()]
            if select.select(reads, [], [], 1.0)[0]:
                line = self.process.stdout.readline()
                if not line:
                    break

                last_output_time = datetime.datetime.now()
                self._handle_output_line(line.strip())

                if not ip_address and 'PUSH_REPLY' in line:
                    ip_match = re.search(r'ifconfig (\d+\.\d+\.\d+\.\d+)', line)
                    if ip_match:
                        ip_address = ip_match.group(1)
                        self.logger.info(f"VPN IP Address assigned: {ip_address}")
                        return ip_address

            if (datetime.datetime.now() - last_output_time).total_seconds() > self.config.connection_timeout:
                raise VPNConnectionError("OpenVPN process not responding")

    def _handle_output_line(self, line: str) -> None:
        """Process and log OpenVPN output lines."""
        print(line)
        sys.stdout.flush()

        if any(event in line for event in self.config.important_events):
            self.logger.info(line)

    def cleanup(self) -> None:
        """Clean up OpenVPN processes."""
        if self.process:
            self.process.kill()
            self.process.wait()
            subprocess.run(['sudo', 'killall', 'openvpn'], check=False)
            self.logger.info("VPN connection stopped")


class OVPNMenuBarApp(rumps.App):
    """Menu bar application for OpenVPN management."""

    def __init__(self, config: VPNConfig):
        """Initialize the menu bar application."""
        super().__init__(
            "OVPN IP",
            quit_button=None
        )
        self.config = config
        self.vpn_manager = OpenVPNManager(config)
        self.ip_address: Optional[str] = None
        self._setup_menu()

    def _setup_menu(self) -> None:
        """Set up the menu bar items."""
        self.menu = [
            rumps.MenuItem("Copy IP", callback=self.copy_ip),
            rumps.MenuItem("Disconnect", callback=self.quit_application)
        ]

    @staticmethod
    def print_banner() -> None:
        """Display the application banner."""
        banner = '''
    $$$$$$\  $$\    $$\ $$$$$$$\  $$\   $$\       $$\      $$\               
    $$  __$$\ $$ |   $$ |$$  __$$\ $$$\  $$ |      $$$\    $$$ |              
    $$ /  $$ |$$ |   $$ |$$ |  $$ |$$$$\ $$ |      $$$$\  $$$$ | $$$$$$\  $$$$$$$\  $$\   $$\ 
    $$ |  $$ |\$$\  $$  |$$$$$$$  |$$ $$\$$ |      $$\$$\$$ $$ |$$  __$$\ $$  __$$\ $$ |  $$ |
    $$ |  $$ | \$$\$$  / $$  ____/ $$ \$$$$ |      $$ \$$$  $$ |$$$$$$$$ |$$ |  $$ |$$ |  $$ |
    $$ |  $$ |  \$$$  /  $$ |      $$ |\$$$ |      $$ |\$  /$$ |$$   ____|$$ |  $$ |$$ |  $$ |
    $$$$$$  |   \$  /   $$ |      $$ | \$$ |      $$ | \_/ $$ |\$$$$$$$\ $$ |  $$ |\$$$$$$  |
    \______/     \_/    \__|      \__|  \__|      \__|     \__| \_______|\__|  \__| \______/ 

            OpenVPN Menu Bar App for macOS - GitHub: @aldhifani
            "Keeping your connection secure, one click at a time"
        '''
        print(banner)
        time.sleep(2)

    def update_title(self, ip: str) -> None:
        """Update the menu bar title with the IP address."""
        self.ip_address = ip
        self.title = ip

    def copy_ip(self, _=None) -> None:
        """Copy the current IP address to clipboard."""
        if self.ip_address:
            copy(self.ip_address)
            self.title = f"✓ {self.ip_address}"
            threading.Timer(1.0, lambda: self.update_title(self.ip_address)).start()

    def quit_application(self, _=None) -> None:
        """Clean up and quit the application."""
        try:
            self.vpn_manager.cleanup()
            time.sleep(1)
            print("Bye!")
            sys.stdout.flush()
            time.sleep(1)
        finally:
            rumps.quit_application()

    def run_vpn(self) -> None:
        """Start the VPN connection in a separate thread."""
        self.print_banner()
        try:
            ip_address = self.vpn_manager.start_connection()
            if ip_address:
                self.update_title(ip_address)
        except VPNConnectionError as e:
            print(f"Error: {e}")
            self.quit_application()


def parse_arguments() -> VPNConfig:
    """Parse command line arguments and return VPN configuration."""
    parser = argparse.ArgumentParser(
        description="OpenVPN Menu Bar Application for macOS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    sudo python main.py config.ovpn                   # Run without logging
    sudo python main.py config.ovpn --log-file ~/vpn.log  # Enable logging
        """
    )

    parser.add_argument(
        'ovpn_file',
        type=pathlib.Path,
        help='Path to the OpenVPN configuration file (.ovpn)'
    )

    parser.add_argument(
        '--log-file',
        type=pathlib.Path,
        help='Enable logging and write logs to the specified file path'
    )

    args = parser.parse_args()
    return VPNConfig(
        ovpn_file=args.ovpn_file,
        log_file=args.log_file
    )


def main() -> None:
    """Main entry point for the application."""
    config = parse_arguments()
    app = OVPNMenuBarApp(config)

    vpn_thread = threading.Thread(target=app.run_vpn)
    vpn_thread.daemon = True
    vpn_thread.start()

    app.run()


if __name__ == "__main__":
    main()
