import argparse
import subprocess
import re
import sys


def run_vpn_and_get_ip(ovpn_file):
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
                    print(f"\nFound VPN IP: {ip_address}\n")

        return ip_address

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        print("\nStopping VPN connection...")
        process.terminate()
        process.wait()
        return ip_address


# Test the function
if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Run OpenVPN and get assigned IP address')
    parser.add_argument('ovpn_file', help='Path to the OpenVPN configuration file (.ovpn)')

    # Parse arguments
    args = parser.parse_args()

    # Run VPN with provided config file
    ip = run_vpn_and_get_ip(args.ovpn_file)
    print(f"Final VPN IP: {ip}")

