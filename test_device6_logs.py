# Read access logs from ACP-260 (the gate controller)
# The panel has 1031 logs — these are the check-in/check-out records

import sys
import time
import win32com.client

print("Connecting to ACP-260...")
zk = win32com.client.Dispatch("zkemkeeper.ZKEM.1")
r = zk.Connect_Net("192.168.1.201", 4370)
print(f"Connect_Net: {r}\n")
time.sleep(0.5)

# Confirm device
print(f"Firmware: {zk.GetFirmwareVersion(1)}")
print(f"Product:  {zk.GetProductCode(1)}")
print(f"Serial:   {zk.GetSerialNumber(1)}")
print(f"Log count: {zk.GetDeviceStatus(1, 2)}")
print()

# Read access logs
print("=" * 60)
print("READING ACCESS LOGS")
print("=" * 60)

# ReadGeneralLogData loads logs into buffer
print("Loading logs into buffer...")
r = zk.ReadGeneralLogData(1)
print(f"ReadGeneralLogData(1): {r}")

if not r:
    print("Failed to load logs. Trying with EnableDevice(False)...")
    zk.EnableDevice(1, False)
    time.sleep(0.5)
    r = zk.ReadGeneralLogData(1)
    print(f"ReadGeneralLogData retry: {r}")

if r:
    print("Logs loaded. Reading entries...\n")
    logs = []
    count = 0
    while count < 2000:  # safety limit
        try:
            # Try SSR_GetGeneralLogData - access control panels use this
            # Method returns tuple: (success, enrollNumber, verifyMode, inOutMode, year, month, day, hour, minute, second, workCode)
            result = zk.SSR_GetGeneralLogData(1)
            if not result or (isinstance(result, tuple) and not result[0]):
                break
            if isinstance(result, tuple) and len(result) >= 10:
                _, enroll_num, verify_mode, in_out, yr, mo, dy, hr, mi, sc = result[:10]
                work_code = result[10] if len(result) > 10 else 0
                ts = f"{yr:04d}-{mo:02d}-{dy:02d} {hr:02d}:{mi:02d}:{sc:02d}"
                in_out_str = "IN" if in_out == 0 else "OUT"
                verify_str = {1: "FP", 2: "FP", 3: "FP", 4: "PIN", 5: "CARD", 6: "FP+PIN", 7: "FP+CARD", 8: "PIN+CARD", 9: "FP+PIN+CARD", 10: "FACE", 15: "PALM"}.get(verify_mode, str(verify_mode))
                logs.append({
                    "user_id": enroll_num,
                    "timestamp": ts,
                    "in_out": in_out,
                    "in_out_str": in_out_str,
                    "verify": verify_str,
                })
                count += 1
            else:
                print(f"  Unexpected result format: {result}")
                break
        except Exception as e:
            print(f"  Error at entry {count}: {e}")
            break

    print(f"Total logs read: {len(logs)}")
    print()

    if logs:
        # Show first 20
        print("FIRST 20 entries:")
        for i, l in enumerate(logs[:20]):
            print(f"  [{i+1}] User {l['user_id']:>5} | {l['in_out_str']:3s} | {l['verify']:5s} | {l['timestamp']}")

        if len(logs) > 20:
            print(f"  ... ({len(logs) - 20} more)")

        # Show last 10
        if len(logs) > 30:
            print(f"\nLAST 10 entries:")
            for i, l in enumerate(logs[-10:]):
                idx = len(logs) - 10 + i + 1
                print(f"  [{idx}] User {l['user_id']:>5} | {l['in_out_str']:3s} | {l['verify']:5s} | {l['timestamp']}")

        # Summary
        print(f"\nSUMMARY:")
        unique_users = set(l["user_id"] for l in logs)
        print(f"  Total logs:    {len(logs)}")
        print(f"  Unique users:  {len(unique_users)}")
        print(f"  Check-ins:     {sum(1 for l in logs if l['in_out'] == 0)}")
        print(f"  Check-outs:    {sum(1 for l in logs if l['in_out'] == 1)}")

        # Date range
        if logs:
            dates = set(l["timestamp"][:10] for l in logs)
            print(f"  Date range:    {min(dates)} to {max(dates)}")

        # Unique user IDs
        print(f"\n  Unique user IDs: {sorted(unique_users)}")

else:
    print("Could not read logs.")

print()
zk.Disconnect()
print("Disconnected.")
