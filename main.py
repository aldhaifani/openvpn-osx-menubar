import argparse
import datetime
import re
import subprocess
import sys
import threading
from time import sleep

import rumps
from pyperclip import copy


class OVPNMenuBarApp(rumps.App):
    """
    A menu bar application to run OpenVPN and display the assigned IP address.

    Features:
    - Displays VPN IP in menu bar
    - Optional logging to file (disabled by default)
    - Enable logging by specifying a log file path

    Usage:
        app = OVPNMenuBarApp("OVPN IP")  # No logging
        app = OVPNMenuBarApp("OVPN IP", log_file="/path/to/custom.log")  # With logging
    """

    def __init__(self, name, title=None, icon=None, template=None, menu=None, quit_button=None, log_file=None):
        """
        Initialize the OVPNMenuBarApp with the given parameters.
        """
        super().__init__(name, title, icon, template, menu, quit_button=None)
        self.menu = [
            rumps.MenuItem("Copy IP", callback=self.copy_ip),
            rumps.MenuItem("Disconnect", callback=self.quit_application)
        ]
        self.vpn_process = None
        self.ip_address = None
        self.logging_enabled = log_file is not None
        self.log_path = log_file
        self.log_file = None

        if self.logging_enabled:
            try:
                self.log_file = open(self.log_path, 'a')
                self._log(f"Application started (logging to {self.log_path})")
            except PermissionError:
                print(f"Error: Permission denied when creating log file at {self.log_path}")
                print("Please ensure you have write permissions to the directory")
                print("Try running the application with sudo: sudo python main.py")
                sys.exit(1)
            except IOError as e:
                print(f"Error: Could not create/open log file at {self.log_path}")
                print(f"Details: {e}")
                print("If this is a permissions issue, try running with sudo: sudo python main.py")
                sys.exit(1)

    def _log(self, message, source="APP"):
        """
        Log the given message to the log file with a timestamp and source.
        Logs are in the format: "YYYY-MM-DD HH:MM:SS (SOURCE) - MESSAGE
        Args:
            message (str): The message to log.
            source (str): The source of the log message (default: APP).
        Returns:
            None
        """
        if self.logging_enabled and self.log_file:
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.log_file.write(f"{timestamp} ({source}) - {message}\n")
            self.log_file.flush()

    def run_openvpn(self, ovpn_file):
        """
        Run the OpenVPN process with the given configuration file and update the menu bar title with the assigned IP address.

        Args:
            ovpn_file (str): Path to the OpenVPN configuration file (.ovpn).

        Returns:
            str: The assigned IP address, or None if not found.
        """
        # First verify the file exists and is readable
        try:
            with open(ovpn_file, 'r') as f:
                config_content = f.read()

            # Basic validation of OpenVPN config file
            if not any(keyword in config_content for keyword in ['remote ', 'dev ', 'proto ']):
                self._log("Error: Invalid OpenVPN configuration file - missing required parameters", source="APP")
                print("Error: Invalid OpenVPN configuration file")
                rumps.quit_application()
                return None

        except (IOError, PermissionError) as e:
            self._log(f"Error reading OpenVPN config file: {str(e)}", source="APP")
            print(f"Error: Could not read OpenVPN config file - {str(e)}")
            rumps.quit_application()
            return None

        # Command to run OpenVPN
        cmd = ['sudo', 'openvpn', ovpn_file]

        # Print the banner
        self.print_banner()

        try:
            # Start the process with a timeout
            self.vpn_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            # Add a timer to check if we're getting any output
            start_time = datetime.datetime.now()
            no_output_timeout = 10  # seconds
            last_output_time = start_time

            ip_address = None

            # Important OVPN events to log
            important_events = [
                'CONNECTED',
                'DISCONNECT',
                'AUTH_FAILED',
                'TLS_ERROR',
                'PUSH_REPLY',
                'Initialization Sequence Completed',
                'ERROR:',
                'FATAL:',
                'TCP connection established',
                'Peer Connection Initiated',
                'Connection reset'
            ]

            while True:
                # Use readline with timeout using select
                import select
                reads = [self.vpn_process.stdout.fileno()]
                timeout = 1.0  # Check every second

                # Wait for output with timeout
                if select.select(reads, [], [], timeout)[0]:
                    line = self.vpn_process.stdout.readline()
                    if not line:
                        break

                    last_output_time = datetime.datetime.now()

                    # Print the log line immediately
                    print(line, end='')
                    sys.stdout.flush()

                    # Log important events
                    if any(event in line for event in important_events):
                        self._log(line.strip(), source="OVPN")

                    # Look for the PUSH_REPLY line if we haven't found the IP yet
                    if not ip_address and 'PUSH_REPLY' in line:
                        match = re.search(r'ifconfig (\d+\.\d+\.\d+\.\d+)', line)
                        if match:
                            ip_address = match.group(1)
                            self.update_title(ip_address)
                            self._log(f"VPN IP Address assigned: {ip_address}", source="OVPN")

                # Check if we've been waiting too long without output
                if (datetime.datetime.now() - last_output_time).total_seconds() > no_output_timeout:
                    self._log("Error: OpenVPN process is not responding or config file might be corrupt", source="APP")
                    print("Error: OpenVPN process is not responding or config file might be corrupt")
                    self.vpn_process.kill()
                    rumps.quit_application()
                    return None

                # Check if process has terminated
                if self.vpn_process.poll() is not None:
                    error_code = self.vpn_process.returncode
                    self._log(f"OpenVPN process terminated with code {error_code}", source="APP")
                    print(f"Error: OpenVPN process terminated unexpectedly with code {error_code}")
                    rumps.quit_application()
                    return None

            return ip_address

        except Exception as e:
            self._log(f"Error running OpenVPN: {str(e)}", source="APP")
            print(f"Error: Failed to run OpenVPN - {str(e)}")
            if self.vpn_process:
                self.vpn_process.kill()
            rumps.quit_application()
            return None

        except KeyboardInterrupt:
            self._log("Received keyboard interrupt", source="OVPN")
            if self.vpn_process:
                self.vpn_process.kill()
            rumps.quit_application()
            return None

    def update_title(self, ip):
        """
        Update the menu bar title with the given IP address.

        Args:
            ip (str): The IP address to display in the menu bar.
        """
        self.ip_address = ip
        self.title = f"{self.ip_address}"

    def quit_application(self, _=None):
        """
        Quit the application and stop the OpenVPN process.
        """
        try:
            if self.vpn_process:
                self._log("Stopping VPN connection...")

                # Kill the OpenVPN process
                self.vpn_process.kill()
                self.vpn_process.wait()

                # Additional cleanup with killall
                subprocess.run(['sudo', 'killall', 'openvpn'], check=False)

                self._log("VPN connection stopped")

            self._log("Application shutdown complete")
        except Exception as e:
            self._log(f"Error during shutdown: {e}")
        finally:
            if self.logging_enabled and self.log_file:
                self.log_file.close()
            sleep(1)  # Short delay to let OpenVPN messages appear
            print("Bye!")  # Add the goodbye message
            sys.stdout.flush()
            sleep(1)  # Give time for the bye message to appear
            rumps.quit_application()

    def print_banner(self):
        """
        Print the banner for the application.
        """
        banner = r"""
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
        """
        print(banner)
        sleep(2)

    def copy_ip(self, _=None):
        """
        Copy the IP address to the clipboard and show confirmation.
        """
        if self.ip_address:
            copy(self.ip_address)
            # Add a visual confirmation
            self.title = f"✓ {self.ip_address}"  # Show checkmark
            self._log(f"IP address copied to clipboard: {self.ip_address}")
            # Reset title after 1 second
            threading.Timer(1.0, lambda: self.update_title(self.ip_address)).start()
        else:
            self._log("No IP address found to copy")


if __name__ == "__main__":
    """
    Main entry point for the application. Parses command-line arguments and starts the OVPNMenuBarApp.
    """
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="""
OpenVPN Menu Bar Application for macOS

This application runs OpenVPN in the background and displays the assigned IP address
in your menu bar. It provides an easy way to monitor your VPN connection status
and disconnect when needed.

Features:
- Displays VPN IP address in the menu bar
- Automatically detects and displays assigned IP address
- Optional logging (enabled by specifying --log-file)
- Gracefully handles VPN disconnection
- Menu bar integration with disconnect option

Note: This application requires sudo privileges to run OpenVPN correctly.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    sudo python main.py config.ovpn                   # Run without logging
    sudo python main.py config.ovpn --log-file ~/vpn.log  # Enable logging to specified file

When logging is enabled, logs can be monitored in real-time using:
    tail -f <log-file-path>
""")

    parser.add_argument(
        'ovpn_file',
        help='Path to the OpenVPN configuration file (.ovpn). This file should contain your VPN configuration settings.'
    )

    parser.add_argument(
        '--log-file',
        help='Enable logging and write logs to the specified file path.'
    )

    args = parser.parse_args()

    app = OVPNMenuBarApp("OVPN IP", log_file=args.log_file)

    # Start VPN in a separate thread
    vpn_thread = threading.Thread(target=app.run_openvpn, args=(args.ovpn_file,))
    vpn_thread.daemon = True
    vpn_thread.start()

    # Run the app
    app.run()