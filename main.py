import argparse
import datetime
import re
import subprocess
import sys
import threading
from time import sleep

import rumps


class OVPNMenuBarApp(rumps.App):
    """
   A menu bar application to run OpenVPN and display the assigned IP address.

   Features:
   - Displays VPN IP in menu bar
   - Logs operations to a file (default: /tmp/ovpn_debug.log)
   - Supports custom log file path

   Usage:
       app = OVPNMenuBarApp("OVPN IP", log_file="/path/to/custom.log")
   """

    def __init__(self, name, title=None, icon=None, template=None, menu=None, quit_button=None,
                 log_file='/tmp/ovpn_debug.log'):
        """
        Initialize the OVPNMenuBarApp with the given parameters.
        """
        super().__init__(name, title, icon, template, menu, quit_button=None)
        self.menu = [
            rumps.MenuItem("Disconnect", callback=self.quit_application)
        ]
        self.vpn_process = None
        self.ip_address = None

        # Try to open log file with error handling
        self.log_path = log_file
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
        Logs are in the format: "YYYY-MM-DD HH:MM:SS (SOURCE) - MESSAGE"
        """
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

        # Command to run OpenVPN
        cmd = ['sudo', 'openvpn', ovpn_file]

        # Print the banner
        self.print_banner()

        # Start the process
        self.vpn_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

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

        try:
            # Read the output line by line
            while True:
                line = self.vpn_process.stdout.readline()
                if not line:
                    break

                # Print the log line immediately
                print(line, end='')
                sys.stdout.flush()  # Ensure output is printed immediately

                # Log important events
                if any(event in line for event in important_events):
                    self._log(line.strip(), source="OVPN")

                # Look for the PUSH_REPLY line if we haven't found the IP yet
                if not ip_address and 'PUSH_REPLY' in line:
                    # Use regex to find the IP address in the ifconfig part
                    match = re.search(r'ifconfig (\d+\.\d+\.\d+\.\d+)', line)
                    if match:
                        ip_address = match.group(1)
                        self.update_title(ip_address)
                        self._log(f"VPN IP Address assigned: {ip_address}", source="OVPN")

            return ip_address

        except KeyboardInterrupt:
            """
            Handle keyboard interrupt (Ctrl+C) to stop the OpenVPN process.
            """
            self._log("Received keyboard interrupt", source="OVPN")
            rumps.quit_application()
            return None

    def update_title(self, ip):
        """
        Update the menu bar title with the given IP address.

        Args:
            ip (str): The IP address to display in the menu bar.
        """
        self.title = f"{ip}"

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
- Logs operations with timestamps
- Gracefully handles VPN disconnection
- Menu bar integration with disconnect option

Note: This application requires sudo privileges to run OpenVPN correctly.
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,  # This preserves the formatting
        epilog="""
Examples:
    sudo python main.py config.ovpn                      # Use default log location
    sudo python main.py config.ovpn --log-file ~/vpn.log # Specify custom log file

Log files can be monitored in real-time using:
    tail -f /tmp/ovpn_debug.log  (or your custom log path)
""")

    parser.add_argument(
        'ovpn_file',
        help='Path to the OpenVPN configuration file (.ovpn). This file should contain your VPN configuration settings.'
    )

    parser.add_argument(
        '--log-file',
        default='/tmp/ovpn_debug.log',
        help='Path to the log file for debugging and monitoring (default: /tmp/ovpn_debug.log)'
    )

    args = parser.parse_args()

    app = OVPNMenuBarApp("OVPN IP", log_file=args.log_file)

    # Start VPN in a separate thread
    vpn_thread = threading.Thread(target=app.run_openvpn, args=(args.ovpn_file,))
    vpn_thread.daemon = True
    vpn_thread.start()

    # Run the app
    app.run()
