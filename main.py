import argparse
import subprocess
import re
import sys
import rumps
import threading
from time import sleep


class OVPNMenuBarApp(rumps.App):
    """
   A menu bar application to run OpenVPN and display the assigned IP address.
   """

    def __init__(self, name, title=None, icon=None, template=None, menu=None, quit_button=None):
        super().__init__(name, title, icon, template, menu, quit_button=None)
        self.menu = [
            rumps.MenuItem("Disconnect", callback=self.quit_application)
        ]
        self.vpn_process = None
        self.ip_address = None

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

        # Start the process
        self.vpn_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        ip_address = None

        try:
            # Read the output line by line
            while True:
                line = self.vpn_process.stdout.readline()
                if not line:
                    break

                # Print the log line immediately
                print(line, end='')
                sys.stdout.flush()  # Ensure output is printed immediately

                # Look for the PUSH_REPLY line if we haven't found the IP yet
                if not ip_address and 'PUSH_REPLY' in line:
                    # Use regex to find the IP address in the ifconfig part
                    match = re.search(r'ifconfig (\d+\.\d+\.\d+\.\d+)', line)
                    if match:
                        ip_address = match.group(1)
                        self.update_title(ip_address)

            return ip_address

        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            print("\nStopping VPN connection...")
            self.quit_application()


    def update_title(self, ip):
        """
        Update the menu bar title with the given IP address.

        Args:
            ip (str): The IP address to display in the menu bar.
        """
        self.title = f"{ip}"

    def quit_application(self):
        """
        Quit the application and stop the OpenVPN process.
        """
        print("Quitting application...")
        sys.stdout.flush()

        try:
            if self.vpn_process:
                sys.stdout.flush()

                # Stop the OpenVPN process
                self.vpn_process.kill()
                self.vpn_process.wait()

                # Stop all OpenVPN processes, if any
                subprocess.run(['sudo', 'killall', 'openvpn'], check=False)

                print("VPN connection stopped")
                sys.stdout.flush()

            sleep(1)  # Short delay to let OpenVPN messages appear
            print("Bye!")  # Add the goodbye message
            sys.stdout.flush()
            sleep(1)  # Give time for the bye message to appear

        except Exception as e:
            print(f"Error during shutdown: {e}")
            sys.stdout.flush()

        rumps.quit_application()

# Test the function
if __name__ == "__main__":
    """
    Main entry point for the application. Parses command-line arguments and starts the OVPNMenuBarApp.
    """
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Run OpenVPN and get assigned IP address')
    parser.add_argument('ovpn_file', help='Path to the OpenVPN configuration file (.ovpn)')

    # Parse arguments
    args = parser.parse_args()

    app = OVPNMenuBarApp("OVPN IP")

    # Start VPN in a separate thread
    vpn_thread = threading.Thread(target=app.run_openvpn, args=(args.ovpn_file,))
    vpn_thread.daemon = True
    vpn_thread.start()

    # Run the app
    app.run()

