"""
ACUnlock test — fixed COM method calls.
zkemkeeper COM methods return (success, value) tuples.
"""

import win32com.client
import time

DEVICE_IP = "192.168.1.201"
DEVICE_PORT = 4370

print("=" * 60)
print("ACUNLOCK TEST — Can the DLL trigger the gate?")
print("=" * 60)

zk = win32com.client.Dispatch("zkemkeeper.ZKEM.1")
print(f"\nConnecting to {DEVICE_IP}:{DEVICE_PORT}...")
result = zk.Connect_Net(DEVICE_IP, DEVICE_PORT)
print(f"Connect_Net: {result}")

if not result:
    print("CONNECTION FAILED")
    exit(1)

# Verify connection
try:
    fw = zk.GetFirmwareVersion(1)
    print(f"Firmware: {fw}")
except Exception as e:
    print(f"Firmware check: {e}")

# ---- ACUNLOCK ----
print("\n" + "=" * 60)
print("TEST: ACUnlock — gate should open for 5 seconds")
print("Watch the gate!")
print("=" * 60)
input("Press ENTER to unlock the gate...")

try:
    result = zk.ACUnlock(1, 5)
    print(f"ACUnlock result: {result}")
    if result:
        print("*** SUCCESS! Gate should be opening! ***")
    else:
        print("ACUnlock returned False")
except Exception as e:
    print(f"ACUnlock error: {e}")

time.sleep(2)

# Try second unlock with different delay
print("\n--- Second attempt (3 sec delay) ---")
input("Press ENTER to unlock again...")
try:
    result = zk.ACUnlock(1, 3)
    print(f"ACUnlock(3) result: {result}")
except Exception as e:
    print(f"ACUnlock error: {e}")

# Try SetDeviceTime (write test)
print("\n--- Write test: SetDeviceTime ---")
try:
    result = zk.SetDeviceTime(1)
    print(f"SetDeviceTime: {result}")
except Exception as e:
    print(f"SetDeviceTime: {e}")

zk.Disconnect()
print("\nDisconnected.")
print("\nDID THE GATE OPEN?")
print("If YES -> re-engineering plan works, no hardware needed!")
print("If NO -> we need a USB relay ($3)")
