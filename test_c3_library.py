"""
Test 2 approaches:
1. zkaccess-c3 library (handles all protocol details)
2. Raw C3 packets with fixed recv (read ALL bytes, not byte-by-byte)

Also tries session-based connect (0x76) instead of session-less (0x01).
"""

import socket
import struct
import time

DEVICE_IP = "192.168.1.201"
DEVICE_PORT = 4370
TIMEOUT = 5


def calc_crc16(data):
    """C3 protocol CRC-16."""
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
    payload = bytearray()
    if data:
        payload.extend(data)
    length = len(payload) + 6
    packet = bytearray()
    packet.append(0xAA)
    packet.append(0x01)
    packet.append(cmd)
    packet.extend(struct.pack('<H', length))
    packet.extend(payload)
    crc = calc_crc16(bytes(packet[1:]))
    packet.extend(struct.pack('<H', crc))
    packet.append(0x55)
    return bytes(packet)


def recv_all(sock, timeout=3):
    """Read everything available."""
    data = b""
    sock.settimeout(timeout)
    while True:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
        except socket.timeout:
            break
        except Exception as e:
            break
    return data


def dump_resp(label, data):
    if data:
        print(f"  {label}: {len(data)} bytes")
        print(f"  Hex: {data.hex()}")
        try:
            text = data.decode('ascii', errors='replace')
            printable = ''.join(c if c.isprintable() or c in '\r\n\t' else '.' for c in text)
            print(f"  Text: {printable[:200]}")
        except:
            pass
    else:
        print(f"  {label}: NO RESPONSE")


# ============================================================
print("=" * 60)
print("APPROACH 1: zkaccess-c3 library")
print("=" * 60)

try:
    from zkaccess import ZKAccess
    print("  Library imported OK")

    # Try connection
    print(f"  Connecting to {DEVICE_IP}:{DEVICE_PORT}...")
    zk = ZKAccess(f"protocol=TCP,ipaddress={DEVICE_IP},port={DEVICE_PORT},timeout=5000")
    zk.conn.open()
    print("  CONNECTED!")

    # Read parameters
    for param in ['~SerialNumber', '~FirmVer', '~DeviceName', '~MachineType', '~ZKFPVersion', 'IPAddress', 'LockCount', 'ReaderCount']:
        try:
            val = zk.conn.get_parameter(param)
            print(f"  {param} = {val}")
        except Exception as e:
            print(f"  {param}: {e}")

    # Read user count
    try:
        users = zk.conn.get_device_data('user', count=10)
        print(f"  Users: {len(users)} records")
        for u in users:
            print(f"    {u}")
    except Exception as e:
        print(f"  Users: {e}")

    # Read transactions
    try:
        txns = zk.conn.get_device_data('transaction', count=10)
        print(f"  Transactions: {len(txns)} records")
        for t in txns:
            print(f"    {t}")
    except Exception as e:
        print(f"  Transactions: {e}")

    zk.conn.close()
    print("  Disconnected.")

except ImportError:
    print("  zkaccess-c3 not installed. Run: pip install zkaccess-c3")
except Exception as e:
    print(f"  Error: {e}")

# ============================================================
print("\n" + "=" * 60)
print("APPROACH 2: Raw C3 packets — fixed recv")
print("=" * 60)

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(TIMEOUT)
sock.connect((DEVICE_IP, DEVICE_PORT))
print(f"  TCP connected")

# Test A: Session-less connect (0x01)
print("\n  --- Session-less connect (0x01) ---")
pkt = make_c3_packet(0x01)
print(f"  Sending: {pkt.hex()}")
sock.send(pkt)
time.sleep(1)
resp = recv_all(sock, timeout=2)
dump_resp("Response", resp)

# Test B: Session-based connect (0x76)
print("\n  --- Session connect (0x76) ---")
pkt = make_c3_packet(0x76)
print(f"  Sending: {pkt.hex()}")
sock.send(pkt)
time.sleep(1)
resp = recv_all(sock, timeout=2)
dump_resp("Response", resp)

# Test C: Device discovery (0x14)
print("\n  --- Device discovery (0x14) ---")
pkt = make_c3_packet(0x14)
print(f"  Sending: {pkt.hex()}")
sock.send(pkt)
time.sleep(1)
resp = recv_all(sock, timeout=2)
dump_resp("Response", resp)

# Test D: Get realtime log KV (0x79)
print("\n  --- Realtime log KV (0x79) ---")
pkt = make_c3_packet(0x79)
print(f"  Sending: {pkt.hex()}")
sock.send(pkt)
time.sleep(1)
resp = recv_all(sock, timeout=2)
dump_resp("Response", resp)

# Test E: Try ZK standalone connect AGAIN but dump raw response
print("\n  --- ZK standalone connect (0x5050827D) for comparison ---")
zk_header = bytes([0x50, 0x50, 0x82, 0x7d])
zk_payload = struct.pack('<HHHH', 1000, 0, 0, 0)  # CMD_CONNECT
# Calc ZK checksum
chk = 0
p = list(zk_payload)
for j in range(1, len(p), 2):
    chk += struct.unpack('<H', bytes(p[j-1:j+1]))[0]
chk = ((chk >> 16) + (chk & 0xFFFF)) ^ 0xFFFF
zk_payload = struct.pack('<HHHH', 1000, chk, 0, 0)
zk_pkt = zk_header + struct.pack('<I', len(zk_payload)) + zk_payload
print(f"  Sending: {zk_pkt.hex()}")
sock.send(zk_pkt)
time.sleep(2)
resp = recv_all(sock, timeout=3)
dump_resp("Response", resp)

sock.close()
print("\nDone.")
