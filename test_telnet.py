"""
Test port 23 (Telnet) — discovered open during port scan.
Access control panels sometimes expose a CLI management interface.

Target: ACP-260 at 192.168.1.201:23
"""

import socket
import time

DEVICE_IP = "192.168.1.201"
TIMEOUT = 5

print("=" * 60)
print("TELNET TEST — Port 23 is open, probing for CLI")
print("=" * 60)

# Connect to Telnet port
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(TIMEOUT)
sock.connect((DEVICE_IP, 23))
print(f"Connected to {DEVICE_IP}:23")

# Read initial banner (device may send a welcome message)
time.sleep(1)
try:
    data = sock.recv(4096)
    if data:
        print(f"Banner: {data}")
        print(f"Banner (hex): {data.hex()}")
        try:
            print(f"Banner (text): {data.decode('ascii', errors='replace')}")
        except:
            pass
    else:
        print("No banner received")
except socket.timeout:
    print("No banner (timed out)")

# Try common CLI commands
commands = [
    b"\r\n",
    b"help\r\n",
    b"?\r\n",
    b"status\r\n",
    b"info\r\n",
    b"version\r\n",
    b"list\r\n",
    b"show\r\n",
    b"show users\r\n",
    b"show log\r\n",
    b"show config\r\n",
    b"get users\r\n",
    b"get log\r\n",
    b"get config\r\n",
    b"cat /etc/passwd\r\n",
    b"admin\r\n",
    b"root\r\n",
    b"\x03",  # Ctrl+C
    b"\x04",  # Ctrl+D
]

for cmd in commands:
    try:
        sock.send(cmd)
        time.sleep(0.5)
        data = sock.recv(4096)
        if data:
            text = data.decode('ascii', errors='replace').strip()
            if text:
                cmd_label = cmd.decode('ascii', errors='replace').strip() or repr(cmd)
                print(f"  [{cmd_label}] → {text}")
    except socket.timeout:
        pass
    except Exception as e:
        print(f"  Error: {e}")
        break

sock.close()
print("\nDone.")
