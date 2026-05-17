"""
Last resort tests — UDP, raw commands without connect, port scan.
If all of these fail, the hardware is definitively a dead end.

Target: ACP-260 at 192.168.1.201:4370
"""

import socket
import struct

DEVICE_IP = "192.168.1.201"
DEVICE_PORT = 4370
TIMEOUT = 5

# ZK protocol header
START_TAG = bytes([0x50, 0x50, 0x82, 0x7d])

# Command codes from zk-protocol spec
CMD_CONNECT = 1000      # 0x03e8
CMD_EXIT = 1001         # 0x03e9
CMD_ENABLEDEVICE = 1002 # 0x03ea
CMD_GET_TIME = 201      # 0x00c9
CMD_GET_VERSION = 1100  # 0x044c
CMD_OPTIONS_RRQ = 11    # 0x000b
CMD_GET_FREE_SIZES = 50 # 0x0032
CMD_REG_EVENT = 500     # 0x01f4
CMD_UNLOCK = 31         # 0x001f


def calc_checksum(payload):
    """ZK protocol checksum calculation."""
    chk_32b = 0
    j = 1
    p = list(payload)
    if len(p) % 2 == 1:
        p.append(0x00)
    while j < len(p):
        chk_32b += struct.unpack('<H', bytes(p[j-1:j+1]))[0]
        j += 2
    chk_32b = (chk_32b >> 16) + (chk_32b & 0xFFFF)
    chk_16b = chk_32b ^ 0xFFFF
    return chk_16b


def make_packet(cmd, data=None, session_id=0, reply_number=0):
    """Build a raw ZK protocol packet."""
    payload = bytearray()
    payload.extend(struct.pack('<H', cmd))
    payload.extend([0x00, 0x00])  # checksum placeholder
    payload.extend(struct.pack('<H', session_id))
    payload.extend(struct.pack('<H', reply_number))
    if data:
        payload.extend(data)
    # calc checksum
    chk = calc_checksum(payload)
    payload[2:4] = struct.pack('<H', chk)
    # build full packet
    packet = bytearray(START_TAG)
    packet.extend(struct.pack('<I', len(payload)))
    packet.extend(payload)
    return bytes(packet)


def try_recv(sock, label, size=1024):
    """Try to receive with timeout, print result."""
    try:
        data = sock.recv(size)
        if data:
            print(f"  {label}: Got {len(data)} bytes: {data[:64].hex()}")
            return data
        else:
            print(f"  {label}: Empty response")
    except socket.timeout:
        print(f"  {label}: TIMED OUT (no response)")
    except Exception as e:
        print(f"  {label}: Error: {e}")
    return None


print("=" * 60)
print("TEST 1: UDP — try UDP instead of TCP")
print("=" * 60)

# UDP test
udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp_sock.settimeout(TIMEOUT)

# Send connect command via UDP
pkt = make_packet(CMD_CONNECT)
print(f"  Sending connect via UDP to {DEVICE_IP}:{DEVICE_PORT}...")
udp_sock.sendto(pkt, (DEVICE_IP, DEVICE_PORT))
try_recv(udp_sock, "UDP connect")

# Try device info request via UDP
pkt = make_packet(CMD_OPTIONS_RRQ, data=b"~SerialNumber\x00")
print(f"  Sending serial request via UDP...")
udp_sock.sendto(pkt, (DEVICE_IP, DEVICE_PORT))
try_recv(udp_sock, "UDP serial")

# Try version request via UDP
pkt = make_packet(CMD_GET_VERSION)
print(f"  Sending version request via UDP...")
udp_sock.sendto(pkt, (DEVICE_IP, DEVICE_PORT))
try_recv(udp_sock, "UDP version")

udp_sock.close()

print()
print("=" * 60)
print("TEST 2: TCP — raw commands WITHOUT connect handshake")
print("=" * 60)

tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_sock.settimeout(TIMEOUT)
tcp_sock.connect((DEVICE_IP, DEVICE_PORT))
print(f"  TCP connected to {DEVICE_IP}:{DEVICE_PORT}")

# Try version request directly (no connect first)
pkt = make_packet(CMD_GET_VERSION)
print(f"  Sending CMD_GET_VERSION without connect...")
tcp_sock.send(pkt)
try_recv(tcp_sock, "GET_VERSION")

# Try time request
pkt = make_packet(CMD_GET_TIME)
print(f"  Sending CMD_GET_TIME without connect...")
tcp_sock.send(pkt)
try_recv(tcp_sock, "GET_TIME")

# Try free sizes (status)
pkt = make_packet(CMD_GET_FREE_SIZES)
print(f"  Sending CMD_GET_FREE_SIZES without connect...")
tcp_sock.send(pkt)
try_recv(tcp_sock, "GET_FREE_SIZES")

# Try options request
pkt = make_packet(CMD_OPTIONS_RRQ, data=b"~SerialNumber\x00")
print(f"  Sending ~SerialNumber without connect...")
tcp_sock.send(pkt)
try_recv(tcp_sock, "SerialNumber")

pkt = make_packet(CMD_OPTIONS_RRQ, data=b"~DeviceName\x00")
print(f"  Sending ~DeviceName without connect...")
tcp_sock.send(pkt)
try_recv(tcp_sock, "DeviceName")

pkt = make_packet(CMD_OPTIONS_RRQ, data=b"~Platform\x00")
print(f"  Sending ~Platform without connect...")
tcp_sock.send(pkt)
try_recv(tcp_sock, "Platform")

# Try unlock door command (might trigger the gate relay!)
pkt = make_packet(CMD_UNLOCK, data=struct.pack('<I', 5))
print(f"  Sending CMD_UNLOCK (5 seconds) without connect...")
tcp_sock.send(pkt)
try_recv(tcp_sock, "UNLOCK")

# Try enable realtime events
pkt = make_packet(CMD_REG_EVENT, data=bytes([0xff, 0xff, 0x00, 0x00]))
print(f"  Sending CMD_REG_EVENT without connect...")
tcp_sock.send(pkt)
try_recv(tcp_sock, "REG_EVENT")

tcp_sock.close()

print()
print("=" * 60)
print("TEST 3: Port scan — check for other open ports")
print("=" * 60)

common_ports = [80, 443, 4370, 8080, 8000, 5000, 5555, 23, 22, 21, 5000, 8821]
for port in common_ports:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(2)
    try:
        s.connect((DEVICE_IP, port))
        print(f"  Port {port}: OPEN")
        s.close()
    except socket.timeout:
        print(f"  Port {port}: closed/filtered")
    except Exception as e:
        print(f"  Port {port}: closed ({e})")

print()
print("=" * 60)
print("DONE — if ALL tests timed out or returned nothing,")
print("the ACP-260 does not speak ZK protocol at all.")
print("Hardware upgrade is the only option.")
print("=" * 60)
