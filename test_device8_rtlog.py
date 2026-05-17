# Read real-time logs from ACP-260
# ReadRTLog returned True - now we need to extract the entries

import sys
import time
import win32com.client

print("Connecting to ACP-260...")
zk = win32com.client.Dispatch("zkemkeeper.ZKEM.1")
r = zk.Connect_Net("192.168.1.201", 4370)
print(f"Connect_Net: {r}\n")
time.sleep(0.5)

print(f"Log count: {zk.GetDeviceStatus(1, 2)}")

# Load real-time logs
print("\nLoading real-time logs...")
r = zk.ReadRTLog(1)
print(f"ReadRTLog(1): {r}")

if r:
    print("Logs loaded! Reading entries...\n")

    # Try different methods to read the RT log entries
    print("=" * 60)
    print("Method A: SSR_GetGeneralLogData after ReadRTLog")
    print("=" * 60)
    logs = []
    count = 0
    while count < 50:
        try:
            result = zk.SSR_GetGeneralLogData(1)
            if not result or (isinstance(result, tuple) and not result[0]):
                print(f"  No more entries after {count} reads")
                break
            print(f"  Entry {count+1}: {result}")
            if isinstance(result, tuple) and len(result) >= 10:
                logs.append(result)
            count += 1
        except Exception as e:
            print(f"  Error at {count}: {e}")
            break

    if logs:
        print(f"\n  Total entries read: {len(logs)}")
        # Parse and display nicely
        print("\n  PARSED:")
        for i, entry in enumerate(logs):
            if len(entry) >= 10:
                _, uid, verify, inout, yr, mo, dy, hr, mi, sc = entry[:10]
                ts = f"{yr:04d}-{mo:02d}-{dy:02d} {hr:02d}:{mi:02d}:{sc:02d}"
                direction = "IN" if inout == 0 else "OUT"
                print(f"    [{i+1}] User {uid} | {direction} | {ts}")

    # Method B: try GetRTLog
    print()
    print("=" * 60)
    print("Method B: GetRTLog")
    print("=" * 60)
    # Re-load
    zk.ReadRTLog(1)
    count = 0
    while count < 10:
        try:
            result = zk.GetRTLog(1)
            if not result:
                break
            print(f"  Entry {count+1}: {result}")
            count += 1
        except Exception as e:
            print(f"  Error: {e}")
            break
    if count == 0:
        print("  No entries via GetRTLog")

    # Method C: try with GetGeneralLogData (non-SSR)
    print()
    print("=" * 60)
    print("Method C: GetGeneralLogData after ReadRTLog")
    print("=" * 60)
    zk.ReadRTLog(1)
    count = 0
    while count < 10:
        try:
            result = zk.GetGeneralLogData(1)
            if not result or (isinstance(result, tuple) and not result[0]):
                break
            print(f"  Entry {count+1}: {result}")
            count += 1
        except Exception as e:
            print(f"  Error: {e}")
            break
    if count == 0:
        print("  No entries via GetGeneralLogData")

    # Method D: try GetAllLogData
    print()
    print("=" * 60)
    print("Method D: GetAllLogData after ReadRTLog")
    print("=" * 60)
    zk.ReadRTLog(1)
    count = 0
    while count < 10:
        try:
            result = zk.GetAllLogData(1)
            if not result or (isinstance(result, tuple) and not result[0]):
                break
            print(f"  Entry {count+1}: {result}")
            count += 1
        except Exception as e:
            print(f"  Error: {e}")
            break
    if count == 0:
        print("  No entries via GetAllLogData")

    # Method E: try reading as string/delimited
    print()
    print("=" * 60)
    print("Method E: GetDeviceLogData (string format)")
    print("=" * 60)
    zk.ReadRTLog(1)
    try:
        result = zk.GetDeviceLogData(1, 1)
        print(f"  GetDeviceLogData(1, 1): {result}")
    except Exception as e:
        print(f"  Error: {e}")
    try:
        result = zk.GetDeviceLogData(1, 1, "")
        print(f"  GetDeviceLogData(1, 1, ''): {result}")
    except Exception as e:
        print(f"  Error: {e}")

    # Method F: try reading events in raw format
    print()
    print("=" * 60)
    print("Method F: ReadRTLog then SSR_GetRTLog")
    print("=" * 60)
    zk.ReadRTLog(1)
    count = 0
    while count < 10:
        try:
            result = zk.SSR_GetRTLog(1)
            if not result or (isinstance(result, tuple) and not result[0]):
                break
            print(f"  Entry {count+1}: {result}")
            count += 1
        except Exception as e:
            print(f"  Error: {e}")
            break
    if count == 0:
        print("  No entries via SSR_GetRTLog")

    # Method G: try GetRTLog with params
    print()
    print("=" * 60)
    print("Method G: GetRTLog with different param counts")
    print("=" * 60)
    zk.ReadRTLog(1)
    for nparams in [1, 2, 3]:
        try:
            if nparams == 1:
                result = zk.GetRTLog(1)
            elif nparams == 2:
                result = zk.GetRTLog(1, "")
            elif nparams == 3:
                result = zk.GetRTLog(1, "", "")
            print(f"  GetRTLog ({nparams} params): {result}")
        except Exception as e:
            print(f"  GetRTLog ({nparams} params): error - {e}")

else:
    print("ReadRTLog failed!")

print()
zk.Disconnect()
print("Disconnected.")
