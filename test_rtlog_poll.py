# Poll ACP-260 in a loop while someone scans their finger
# ReadRTLog returned True before - maybe we need to poll it continuously

import sys
import time
import win32com.client
import pythoncom

def get_log_count(zk):
    result = zk.GetDeviceStatus(1, 2)
    # Returns (True, count) or (False, 0)
    if isinstance(result, tuple):
        return result[1]
    return result

print("Connecting...")
zk = win32com.client.dynamic.Dispatch("zkemkeeper.ZKEM.1")
r = zk.Connect_Net("192.168.1.201", 4370)
print(f"Connect_Net: {r}")
time.sleep(0.5)

# Get current log count as baseline
baseline_val = get_log_count(zk)
print(f"Current log count: {baseline_val}")
time.sleep(0.5)

print()
print("=" * 50)
print("POLLING FOR NEW EVENTS")
print("=" * 50)
print("Have someone scan their finger at the gate NOW.")
print("Watching for log count to change...")
print("Press Ctrl+C to stop.\n")

count = 0
try:
    while True:
        count += 1

        # Check log count
        val = get_log_count(zk)
        if val != baseline_val:
            print(f"\n>>> LOG COUNT CHANGED!")
            print(f"    Was: {baseline_val}")
            print(f"    Now: {val}")
            baseline_val = val

            # Try to read the new log
            print("    Attempting to read new log...")
            try:
                r = zk.ReadRTLog(1)
                print(f"    ReadRTLog: {r}")

                for method_name, method_call in [
                    ("SSR_GetGeneralLogData", lambda: zk.SSR_GetGeneralLogData(1)),
                    ("GetGeneralLogData", lambda: zk.GetGeneralLogData(1)),
                    ("GetRTLog", lambda: zk.GetRTLog(1)),
                ]:
                    try:
                        entry = method_call()
                        if entry and not (isinstance(entry, tuple) and entry[0] is False):
                            print(f"    {method_name}: {entry}")
                    except:
                        pass

            except Exception as e:
                print(f"    Error: {e}")

            # Also try ReadGeneralLogData after count change
            try:
                r = zk.ReadGeneralLogData(1)
                if r:
                    print(f"    ReadGeneralLogData NOW returned True!")
                    entry = zk.SSR_GetGeneralLogData(1)
                    print(f"    Entry: {entry}")
            except:
                pass

        # Also try ReadRTLog on every iteration
        try:
            rt = zk.ReadRTLog(1)
            if rt:
                try:
                    entry = zk.SSR_GetGeneralLogData(1)
                    if entry and not (isinstance(entry, tuple) and entry[0] is False and entry[1] == ''):
                        print(f"\n>>> RTLOG DATA: {entry}")
                except:
                    pass
                try:
                    entry = zk.GetRTLog(1)
                    if entry and entry != False:
                        print(f"\n>>> RTLOG GET: {entry}")
                except:
                    pass
        except:
            pass

        if count % 30 == 0:  # Every ~3 seconds
            print(f"  still polling... (log_count={baseline_val})")

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nStopped.")

# Final check
print(f"\nFinal log count: {get_log_count(zk)}")
zk.Disconnect()
print("Disconnected.")
