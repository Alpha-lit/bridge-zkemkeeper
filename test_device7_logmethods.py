# Try all possible methods to read logs from ACP-260 panel
# The device has 1031 logs but ReadGeneralLogData returns False
# Access control panels may use different log reading methods

import sys
import time
import win32com.client

print("Connecting to ACP-260...")
zk = win32com.client.Dispatch("zkemkeeper.ZKEM.1")
r = zk.Connect_Net("192.168.1.201", 4370)
print(f"Connect_Net: {r}\n")
time.sleep(0.5)

# Confirm log count
print(f"Log count: {zk.GetDeviceStatus(1, 2)}")

# Try all DeviceStatus codes to learn more about the device
print("\nDevice status codes:")
for code in range(1, 15):
    try:
        result = zk.GetDeviceStatus(1, code)
        print(f"  Status code {code}: {result}")
    except Exception as e:
        print(f"  Status code {code}: error - {e}")

print()
print("=" * 60)
print("TRYING ALL LOG READ METHODS")
print("=" * 60)

# Method 1: ReadGeneralLogData
print("\n1. ReadGeneralLogData(1)...")
try:
    r = zk.ReadGeneralLogData(1)
    print(f"   Result: {r}")
except Exception as e:
    print(f"   Error: {e}")

# Method 2: ReadAllGLogData
print("\n2. ReadAllGLogData(1)...")
try:
    r = zk.ReadAllGLogData(1)
    print(f"   Result: {r}")
except Exception as e:
    print(f"   Error: {e}")

# Method 3: ReadSuperLogData
print("\n3. ReadSuperLogData(1)...")
try:
    r = zk.ReadSuperLogData(1)
    print(f"   Result: {r}")
except Exception as e:
    print(f"   Error: {e}")

# Method 4: ReadAllSLogData
print("\n4. ReadAllSLogData(1)...")
try:
    r = zk.ReadAllSLogData(1)
    print(f"   Result: {r}")
except Exception as e:
    print(f"   Error: {e}")

# Method 5: GetDeviceDataCount for logs
print("\n5. GetDeviceDataCount (attendance)...")
try:
    r = zk.GetDeviceDataCount(1, 1, 0)
    print(f"   Result: {r}")
except Exception as e:
    print(f"   Error: {e}")

# Method 6: Try reading without loading first
print("\n6. SSR_GetGeneralLogData without ReadGeneralLogData...")
try:
    r = zk.SSR_GetGeneralLogData(1)
    print(f"   Result: {r}")
except Exception as e:
    print(f"   Error: {e}")

# Method 7: GetGeneralLogData (non-SSR)
print("\n7. GetGeneralLogData without loading...")
try:
    r = zk.GetGeneralLogData(1)
    print(f"   Result: {r}")
except Exception as e:
    print(f"   Error: {e}")

# Method 8: Try ReadNewDatabase (for newer panels)
print("\n8. ReadNewDatabase...")
try:
    r = zk.ReadNewDatabase(1)
    print(f"   Result: {r}")
except Exception as e:
    print(f"   Error: {e}")


# Method 9: Try EnableDevice + ReadGeneralLogData + longer wait
print("\n9. Lock device, wait, then ReadGeneralLogData...")
try:
    zk.EnableDevice(1, False)
    print("   Device locked, waiting 2 seconds...")
    time.sleep(2)
    r = zk.ReadGeneralLogData(1)
    print(f"   ReadGeneralLogData: {r}")
    if r:
        print("   SUCCESS! Reading entries...")
        count = 0
        while count < 20:
            try:
                result = zk.SSR_GetGeneralLogData(1)
                if not result or (isinstance(result, tuple) and not result[0]):
                    break
                print(f"     Entry: {result}")
                count += 1
            except:
                break
        print(f"   Read {count} entries")
    zk.EnableDevice(1, True)
except Exception as e:
    print(f"   Error: {e}")
    try:
        zk.EnableDevice(1, True)
    except:
        pass


# Method 10: Try using GetData from access log table
# ACP panels sometimes store logs in table format
print("\n10. Try GetDeviceData (raw data)...")
try:
    # Table 1 = attendance log
    r = zk.GetDeviceData(1, 1, "")
    print(f"   GetDeviceData(1, 1, ''): {r}")
except Exception as e:
    print(f"   Error: {e}")

try:
    # Try with specific field request
    r = zk.GetDeviceData(1, 1, "UserID\tDateTime\tStatus\tVerify")
    print(f"   GetDeviceData with fields: {r}")
except Exception as e:
    print(f"   Error: {e}")


# Method 11: Check if the panel stores logs differently
# Try reading from specific log storage
print("\n11. Try ReadALog...")
try:
    r = zk.ReadALog(1)
    print(f"   Result: {r}")
except Exception as e:
    print(f"   Error: {e}")


# Method 12: Try the event/real-time approach
print("\n12. Check if device supports real-time events...")
try:
    r = zk.ReadRTLog(1)
    print(f"   ReadRTLog: {r}")
except Exception as e:
    print(f"   Error: {e}")


# Method 13: Try getting last log directly
print("\n13. GetLastLog...")
try:
    r = zk.GetLastLog(1)
    print(f"   Result: {r}")
except Exception as e:
    print(f"   Error: {e}")


print()
zk.Disconnect()
print("Disconnected.")

print()
print("NOTE: If all methods failed, the ACP-260 panel may only expose")
print("logs through ZKAccess software or through a Push SDK mechanism")
print("where the panel sends events to a server in real-time.")
