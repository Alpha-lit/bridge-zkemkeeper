"""
CRITICAL TEST: Can zkemkeeper COM DLL trigger the gate unlock?

If this works, the re-engineering plan works with ZERO hardware purchases.
The flow would be: ZK4500 scan → Django match → ACUnlock() → gate opens.

The zkemkeeper DLL is the ONLY thing that gets responses from this device.
We know basic device commands work. The question is: does ACUnlock() work?

Target: ACP-260 at 192.168.1.201:4370
Requires: 32-bit Python, zkemkeeper.dll registered
"""

import win32com.client
import time

DEVICE_IP = "192.168.1.201"
DEVICE_PORT = 4370
MACHINE_NUM = 1

print("=" * 60)
print("ACUNLOCK TEST — Can the DLL trigger the gate?")
print("If this works, we can control the gate from Django!")
print("=" * 60)

# Connect
zk = win32com.client.Dispatch("zkemkeeper.ZKEM.1")
print(f"\nConnecting to {DEVICE_IP}:{DEVICE_PORT}...")
result = zk.Connect_Net(DEVICE_IP, DEVICE_PORT)
print(f"Connect_Net: {result}")

if not result:
    print("CONNECTION FAILED — cannot proceed")
    exit(1)

# Verify connection with device info
fw = zk.GetFirmwareVersion(MACHINE_NUM)
print(f"Firmware: {fw}")

pc = zk.GetProductCode(MACHINE_NUM)
print(f"Product: {pc}")

# ---- TEST 1: ACUnlock ----
print("\n" + "-" * 40)
print("TEST 1: ACUnlock(machineNum=1, delaySeconds=5)")
print("This should open the gate for 5 seconds!")
print("-" * 40)
input("Press ENTER to trigger UNLOCK (make sure someone can see the gate)...")

result = zk.ACUnlock(MACHINE_NUM, 5)
print(f"ACUnlock result: {result}")

if result:
    print("*** GATE SHOULD BE OPENING NOW! ***")
    print("If the gate opened, the re-engineering plan WORKS!")
else:
    print("ACUnlock returned False — gate may not have opened")

time.sleep(2)

# ---- TEST 2: Try with different delay ----
print("\n" + "-" * 40)
print("TEST 2: ACUnlock with 3 second delay")
print("-" * 40)
input("Press ENTER to try again with 3 second delay...")

result = zk.ACUnlock(MACHINE_NUM, 3)
print(f"ACUnlock(3) result: {result}")

# ---- TEST 3: Door control methods ----
print("\n" + "-" * 40)
print("TEST 3: Other door control methods")
print("-" * 40)

# Try GetDoorState
try:
    result = zk.GetDoorState(MACHINE_NUM)
    print(f"GetDoorState: {result}")
except Exception as e:
    print(f"GetDoorState error: {e}")

# Try EnableDevice
try:
    result = zk.EnableDevice(MACHINE_NUM, 1)
    print(f"EnableDevice(1, 1): {result}")
except Exception as e:
    print(f"EnableDevice error: {e}")

# Try Beep (basic output test)
try:
    result = zk.Beep(150)
    print(f"Beep(150): {result}")
except Exception as e:
    print(f"Beep error: {e}")

# Try SetDeviceFlag or other control methods
methods_to_try = [
    ("ACUnlock", lambda: zk.ACUnlock(MACHINE_NUM, 2)),
    ("CancelAlarm", lambda: zk.CancelAlarm()),
]

# ---- TEST 4: SetDeviceTime (write test) ----
print("\n" + "-" * 40)
print("TEST 4: Can we WRITE to the device?")
print("-" * 40)

# Try setting device time (this is a WRITE operation)
try:
    result = zk.SetDeviceTime(MACHINE_NUM)
    print(f"SetDeviceTime: {result}")
    if result:
        print("  WRITE operations WORK — the device accepts commands!")
except Exception as e:
    print(f"SetDeviceTime error: {e}")

# ---- TEST 5: Read device status ----
print("\n" + "-" * 40)
print("TEST 5: Device status")
print("-" * 40)

# GetDoorState
try:
    result = zk.GetDoorState(MACHINE_NUM)
    print(f"GetDoorState: {result}")
except Exception as e:
    print(f"GetDoorState: {e}")

# GetDeviceStatus - various types
for status_type in range(1, 8):
    try:
        result = zk.GetDeviceStatus(MACHINE_NUM, status_type)
        print(f"  Status type {status_type}: {result}")
    except Exception as e:
        print(f"  Status type {status_type}: error - {e}")

# Disconnect
zk.Disconnect()
print("\nDisconnected.")
print("\n" + "=" * 60)
print("DID THE GATE OPEN DURING ANY OF THESE TESTS?")
print("If YES → the re-engineering plan works, no hardware needed!")
print("If NO → we need a USB relay ($3) as fallback")
print("=" * 60)
