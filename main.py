import argparse
import subprocess
import re
import sys
import rumps
import threading


class OVPNMenuBarApp(rumps.App):
    """
   A menu bar application to run OpenVPN and display the assigned IP address.
   """

    def __int__(self):
        """
        Initialize the OVPNMenuBarApp with a default title and no IP address or VPN process.
        """
        super(OVPNMenuBarApp, self).__init__("OVPN IP")
        self.ip_address = None
        self.vpn_process = None

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
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

        ip_address = None

        try:
            # Read the output line by line
            while True:
                line = process.stdout.readline()
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
            process.terminate()
            process.wait()
            return ip_address

    def update_title(self, ip):
        """
        Update the menu bar title with the given IP address.

        Args:
            ip (str): The IP address to display in the menu bar.
        """
        self.title = f"{ip}"


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

