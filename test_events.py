# Real-time event listener for ACP-260
# Captures fingerprint scan events as they happen
# 1. Run this script
# 2. Have someone scan their finger at the gate
# 3. See if the event appears here

import sys
import time
import pythoncom
import win32com.client

# Event handler class - captures all COM events from the device
class ZKEventHandler:
    def OnAttTransaction(self, *args):
        print(f"\n>>> ATTENDANCE EVENT: {args}")
        print(f"    User ID: {args[0] if args else '?'}")
        print(f"    Verify mode: {args[1] if len(args) > 1 else '?'}")
        print(f"    In/Out: {args[2] if len(args) > 2 else '?'}")

    def OnAttTransactionEx(self, *args):
        print(f"\n>>> ATTENDANCE EX EVENT: {args}")

    def OnDoor(self, *args):
        print(f"\n>>> DOOR EVENT: {args}")

    def OnAlarm(self, *args):
        print(f"\n>>> ALARM EVENT: {args}")

    def OnConnected(self):
        print("\n>>> DEVICE CONNECTED")

    def OnDisConnected(self):
        print("\n>>> DEVICE DISCONNECTED")

    def OnVerify(self, *args):
        print(f"\n>>> VERIFY EVENT: {args}")

    def OnFinger(self, *args):
        print(f"\n>>> FINGER EVENT: {args}")

    def OnNewUser(self, *args):
        print(f"\n>>> NEW USER EVENT: {args}")

    def OnWriteCard(self, *args):
        print(f"\n>>> WRITE CARD EVENT: {args}")

    def OnEmptyCard(self, *args):
        print(f"\n>>> EMPTY CARD EVENT: {args}")

    def OnEMData(self, *args):
        print(f"\n>>> EM DATA EVENT: {args}")

    def OnHIDNum(self, *args):
        print(f"\n>>> HID NUM EVENT: {args}")

    def OnKeyPress(self, *args):
        print(f"\n>>> KEY PRESS EVENT: {args}")

    def OnEnrollFinger(self, *args):
        print(f"\n>>> ENROLL FINGER EVENT: {args}")

    def OnEnrollFingerEx(self, *args):
        print(f"\n>>> ENROLL FINGER EX EVENT: {args}")

    def OnDeleteTemplate(self, *args):
        print(f"\n>>> DELETE TEMPLATE EVENT: {args}")

    def OnNewTemplate(self, *args):
        print(f"\n>>> NEW TEMPLATE EVENT: {args}")

    def OnCoverOldTemp(self, *args):
        print(f"\n>>> COVER OLD TEMPLATE EVENT: {args}")

    def OnRTLog(self, *args):
        print(f"\n>>> RT LOG EVENT: {args}")


print("Connecting to ACP-260 with event handler...")

# Use DispatchWithEvents instead of Dispatch
zk = win32com.client.DispatchWithEvents("zkemkeeper.ZKEM.1", ZKEventHandler)

r = zk.Connect_Net("192.168.1.201", 4370)
print(f"Connect_Net: {r}")

if not r:
    print("Failed to connect!")
    sys.exit(1)

print("Connected! Setting up real-time monitoring...\n")

# Enable real-time events
# For ACP-260, we need to register for event notifications
try:
    r = zk.RegEvent(1, 1)  # Register for all events on machine 1
    print(f"RegEvent(1, 1): {r}")
except Exception as e:
    print(f"RegEvent error: {e}")

# Also try enabling real-time log transfer
try:
    zk.EnableRTLog(1)
    print("EnableRTLog: called")
except Exception as e:
    print(f"EnableRTLog error: {e}")

print()
print("=" * 50)
print("LISTENING FOR EVENTS...")
print("=" * 50)
print("Have someone scan their finger at the gate.")
print("Press Ctrl+C to stop.\n")

# Main loop - pump COM messages and wait for events
try:
    while True:
        pythoncom.PumpWaitingMessages()
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n\nStopped by user.")

zk.Disconnect()
print("Disconnected.")
