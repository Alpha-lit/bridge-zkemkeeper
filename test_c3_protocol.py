"""
Test connection to ACP-260 using C3 Access Control Panel protocol.
This is the CORRECT protocol for this device — NOT the ZK standalone protocol.

The ACP-260 is actually a C3-260 / InBio-260 board (mainboard: C3-260-MAIN).
It uses C3 binary protocol: header 0xAA, footer 0x55, CRC-16.

Library: zkaccess-c3-py
Install: pip install zkaccess-c3

Target: ACP-260 at 192.168.1.201:4370
"""

import socket
import struct
import time

DEVICE_IP = "192.168.1.201"
DEVICE_PORT = 4370
TIMEOUT = 5

# C3 Protocol constants
C3_START = 0xAA
C3_VERSION = 0x01
C3_END = 0x55

# C3 Commands
CMD_CONNECT = 0x01
CMD_DISCONNECT = 0x02
CMD_SET_DATETIME = 0x03
CMD_GET_PARAMETERS = 0x04
CMD_DEVICE_CONTROL = 0x05
CMD_GET_DATATABLE_CONFIG = 0x06
CMD_RETRIEVE_DATA = 0x08
CMD_REALTIME_LOG = 0x0B
CMD_DEVICE_DISCOVERY = 0x14
CMD_CONNECT_SESSION = 0x76
CMD_REALTIME_LOG_KV = 0x79

# Response codes
RSP_OK = 0xC8
RSP_ERROR = 0xC9


def calc_crc16(data):
    """C3 protocol CRC-16 calculation."""
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0x8408
            else:
                crc >>= 1
    return crc & 0xFFFF


def make_c3_packet(cmd, data=None):
    """Build a C3 protocol packet."""
    payload = bytearray()
    if data:
        payload.extend(data)

    length = len(payload) + 6  # cmd(1) + length(2) + crc(2) + end(1)
    packet = bytearray()
    packet.append(C3_START)       # 0xAA
    packet.append(C3_VERSION)     # 0x01
    packet.append(cmd)            # Command
    packet.extend(struct.pack('<H', length))  # Length (little-endian)
    packet.extend(payload)        # Data payload

    # CRC over everything except start byte
    crc = calc_crc16(packet[1:])
    packet.extend(struct.pack('<H', crc))
    packet.append(C3_END)         # 0x55

    return bytes(packet)


def recv_c3(sock, timeout=5):
    """Receive a C3 protocol response."""
    sock.settimeout(timeout)
    data = b""

    # Read until we get 0x55 end marker
    while True:
        try:
            byte = sock.recv(1)
            if not byte:
                break
            data += byte
            if byte == b'\x55' and len(data) >= 7:
                # Check if this looks like a complete C3 packet
                if data[0] == C3_START:
                    break
        except socket.timeout:
            break

    return data


def parse_response(data):
    """Parse a C3 protocol response."""
    if not data or len(data) < 7:
        return None

    if data[0] != C3_START:
        return None

    cmd = data[2]
    length = struct.unpack('<H', data[3:5])[0]
    payload = data[5:-3]  # Exclude CRC and END
    crc_received = struct.unpack('<H', data[-3:-1])[0]
    end = data[-1]

    # Verify CRC
    crc_calc = calc_crc16(data[1:-3])
    crc_ok = crc_calc == crc_received

    return {
        'cmd': cmd,
        'length': length,
        'payload': payload,
        'crc_ok': crc_ok,
        'raw': data,
    }


print("=" * 60)
print("C3 PROTOCOL TEST — ACP-260 (C3-260/InBio-260)")
print(f"Target: {DEVICE_IP}:{DEVICE_PORT}")
print("=" * 60)

# Connect TCP
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(TIMEOUT)
sock.connect((DEVICE_IP, DEVICE_PORT))
print(f"TCP connected to {DEVICE_IP}:{DEVICE_PORT}\n")

# --- TEST 1: C3 Connect (session-less) ---
print("--- TEST 1: C3 Connect (0x01) ---")
pkt = make_c3_packet(CMD_CONNECT)
print(f"  Sending: {pkt.hex()}")
sock.send(pkt)
resp = recv_c3(sock)
print(f"  Received: {resp.hex() if resp else 'None'}")
parsed = parse_response(resp)
if parsed:
    print(f"  Cmd: 0x{parsed['cmd']:02x}  CRC OK: {parsed['crc_ok']}  Payload: {parsed['payload'].hex()}")
    if parsed['payload']:
        # Response payload: 4 bytes controller serial + firmware info
        print(f"  Payload text: {parsed['payload']}")
        try:
            print(f"  Payload ascii: {parsed['payload'].decode('ascii', errors='replace')}")
        except:
            pass
else:
    print("  No valid C3 response")

# --- TEST 2: Get Parameters (serial number) ---
print("\n--- TEST 2: Get Parameters ~SerialNumber ---")
param_data = b"~SerialNumber\x00"
pkt = make_c3_packet(CMD_GET_PARAMETERS, data=param_data)
print(f"  Sending: {pkt.hex()}")
sock.send(pkt)
resp = recv_c3(sock)
print(f"  Received: {resp.hex() if resp else 'None'}")
parsed = parse_response(resp)
if parsed:
    print(f"  Cmd: 0x{parsed['cmd']:02x}  CRC OK: {parsed['crc_ok']}")
    try:
        print(f"  Value: {parsed['payload'].decode('ascii', errors='replace')}")
    except:
        print(f"  Payload: {parsed['payload'].hex()}")
else:
    print("  No valid C3 response")

# --- TEST 3: Get Parameters (firmware) ---
print("\n--- TEST 3: Get Parameters ~FirmVer ---")
param_data = b"~FirmVer\x00"
pkt = make_c3_packet(CMD_GET_PARAMETERS, data=param_data)
sock.send(pkt)
resp = recv_c3(sock)
parsed = parse_response(resp)
if parsed:
    try:
        print(f"  Firmware: {parsed['payload'].decode('ascii', errors='replace')}")
    except:
        print(f"  Payload: {parsed['payload'].hex()}")
else:
    print("  No response")

# --- TEST 4: Get Parameters (product code / machine type) ---
for param in [b"~MachineType\x00", b"~ProductCode\x00", b"~DeviceName\x00", b"~ZKFPVersion\x00"]:
    print(f"\n--- Get Parameter: {param.rstrip(b'\\x00').decode()} ---")
    pkt = make_c3_packet(CMD_GET_PARAMETERS, data=param)
    sock.send(pkt)
    resp = recv_c3(sock)
    parsed = parse_response(resp)
    if parsed:
        try:
            print(f"  Value: {parsed['payload'].decode('ascii', errors='replace')}")
        except:
            print(f"  Payload: {parsed['payload'].hex()}")
    else:
        print("  No response")

# --- TEST 5: Get DataTable config (see what tables exist) ---
print("\n--- TEST 5: Get DataTable Config (0x06) ---")
pkt = make_c3_packet(CMD_GET_DATATABLE_CONFIG)
sock.send(pkt)
resp = recv_c3(sock, timeout=3)
parsed = parse_response(resp)
if parsed:
    print(f"  Cmd: 0x{parsed['cmd']:02x}  Payload size: {len(parsed['payload'])}")
    print(f"  Payload hex: {parsed['payload'][:128].hex()}")
else:
    print("  No response")

# --- TEST 6: Retrieve realtime log ---
print("\n--- TEST 6: Realtime Log (0x0B) ---")
pkt = make_c3_packet(CMD_REALTIME_LOG)
sock.send(pkt)
resp = recv_c3(sock, timeout=3)
parsed = parse_response(resp)
if parsed:
    print(f"  Cmd: 0x{parsed['cmd']:02x}  Payload size: {len(parsed['payload'])}")
    print(f"  Payload hex: {parsed['payload'][:128].hex()}")
else:
    print("  No response")

# --- TEST 7: Retrieve Data from 'user' table ---
print("\n--- TEST 7: Retrieve Data — user table ---")
# C3 data retrieve: table name + parameters
user_req = b"user\x00" + struct.pack('<HH', 0, 100)  # table, offset, count
pkt = make_c3_packet(CMD_RETRIEVE_DATA, data=user_req)
sock.send(pkt)
resp = recv_c3(sock, timeout=3)
parsed = parse_response(resp)
if parsed:
    print(f"  Cmd: 0x{parsed['cmd']:02x}  Payload size: {len(parsed['payload'])}")
    print(f"  Payload hex: {parsed['payload'][:128].hex()}")
else:
    print("  No response")

# --- TEST 8: Retrieve Data from 'transaction' table ---
print("\n--- TEST 8: Retrieve Data — transaction table ---")
trans_req = b"transaction\x00" + struct.pack('<HH', 0, 100)
pkt = make_c3_packet(CMD_RETRIEVE_DATA, data=trans_req)
sock.send(pkt)
resp = recv_c3(sock, timeout=3)
parsed = parse_response(resp)
if parsed:
    print(f"  Cmd: 0x{parsed['cmd']:02x}  Payload size: {len(parsed['payload'])}")
    print(f"  Payload hex: {parsed['payload'][:128].hex()}")
else:
    print("  No response")

# Disconnect
print("\n--- Disconnect ---")
pkt = make_c3_packet(CMD_DISCONNECT)
sock.send(pkt)
time.sleep(0.5)

sock.close()
print("\nDone.")
