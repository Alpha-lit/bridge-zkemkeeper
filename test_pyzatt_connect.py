"""
Basic connection test using pyzatt (raw ZK protocol).
No zkemkeeper.dll needed — pure Python TCP.

Target: ACP-260 at 192.168.1.201:4370
"""

from pyzatt.pyzatt import ZKSS

DEVICE_IP = "192.168.1.201"
DEVICE_PORT = 4370

zk = ZKSS()

print(f"Connecting to {DEVICE_IP}:{DEVICE_PORT} ...")
try:
    zk.connect_net(DEVICE_IP, DEVICE_PORT)
    print("Connected!")
except Exception as e:
    print(f"Connection failed: {e}")
    exit(1)

# Device info
print(f"Platform: {zk.dev_platform}")
print(f"Firmware: {zk.firmware_v}")

# Try reading device time
try:
    zk.get_device_time()
    print(f"Device time: {zk.dev_platform}")
except Exception as e:
    print(f"get_device_time failed: {e}")

# Try reading serial number
try:
    sn = zk.get_serial_number()
    print(f"Serial: {sn}")
except Exception as e:
    print(f"get_serial_number failed: {e}")

# Try reading user count
try:
    count = zk.get_user_count()
    print(f"User count: {count}")
except Exception as e:
    print(f"get_user_count failed: {e}")

# Try reading log count
try:
    log_count = zk.get_att_log_count()
    print(f"Attendance log count: {log_count}")
except Exception as e:
    print(f"get_att_log_count failed: {e}")

zk.disconnect()
print("Done.")
