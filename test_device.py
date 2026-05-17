"""
Quick ZK9500 connection test.

Run on the entrance PC with 32-bit Python:
  "C:\\Users\\hp\\AppData\\Local\\Programs\\Python\\Python312-32\\python.exe" test_device.py

Make sure ZKAccess 3.5 is CLOSED before running.
"""

import sys

# --- Test 1: Import and create COM object ---
print("=" * 50)
print("TEST 1: Import zkemkeeper COM")
print("=" * 50)
try:
    import win32com.client
    print("[OK] win32com.client imported")
except ImportError as e:
    print(f"[FAIL] win32com not installed: {e}")
    print("  Run: pip install pywin32")
    sys.exit(1)

try:
    zk = win32com.client.Dispatch("zkemkeeper.ZKEM.1")
    print("[OK] zkemkeeper.ZKEM.1 COM object created")
except Exception as e:
    print(f"[FAIL] Cannot create COM object: {e}")
    print("  Make sure zkemkeeper.dll is registered:")
    print('  Run: %windir%\\SysWOW64\\regsvr32.exe zkemkeeper.dll')
    sys.exit(1)

# --- Test 2: Connect to device ---
print()
print("=" * 50)
print("TEST 2: Connect to ZK9500 at 192.168.1.201:4370")
print("=" * 50)
try:
    result = zk.Connect_Net("192.168.1.201", 4370)
    if result:
        print("[OK] Connected to ZK9500")
    else:
        print("[FAIL] Connect_Net returned False")
        print("  Check: is the device powered on? correct IP?")
        print("  Check: is ZKAccess 3.5 CLOSED?")
        sys.exit(1)
except Exception as e:
    print(f"[FAIL] Connection error: {e}")
    sys.exit(1)

# --- Test 3: Read device info ---
print()
print("=" * 50)
print("TEST 3: Read device info")
print("=" * 50)
try:
    import win32com.client.pythoncom

    # Firmware version
    strVersion = win32com.client.VARIANT(
        win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_BSTR, ""
    )
    zk.GetFirmwareVersion(1, strVersion)
    print(f"  Firmware: {strVersion.value}")

    # Serial number
    strSN = win32com.client.VARIANT(
        win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_BSTR, ""
    )
    zk.GetSerialNumber(1, strSN)
    print(f"  Serial:   {strSN.value}")

    # User count
    dwValue = win32com.client.VARIANT(
        win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
    )
    zk.GetDeviceStatus(1, 1, dwValue)  # 1 = user count
    user_count = dwValue.value if isinstance(dwValue.value, int) else 0
    print(f"  Users:    {user_count}")

    # Log count
    dwLogCount = win32com.client.VARIANT(
        win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
    )
    zk.GetDeviceStatus(1, 2, dwLogCount)  # 2 = log count
    log_count = dwLogCount.value if isinstance(dwLogCount.value, int) else 0
    print(f"  Logs:     {log_count}")

    print("[OK] Device info read successfully")
except Exception as e:
    print(f"[WARN] Could not read all device info: {e}")

# --- Test 4: Read all users ---
print()
print("=" * 50)
print("TEST 4: Read all users from device")
print("=" * 50)
try:
    result = zk.ReadAllUserID(1)
    if not result:
        print("[OK] No users on device (empty)")
    else:
        users = []
        while True:
            dwEnrollNumber = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            Name = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_BSTR, ""
            )
            Password = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_BSTR, ""
            )
            Privilege = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            Enabled = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_BOOL, False
            )
            result = zk.SSR_GetAllUserInfo(
                1, dwEnrollNumber, Name, Password, Privilege, Enabled
            )
            if not result:
                break
            uid = int(dwEnrollNumber.value) if dwEnrollNumber.value else 0
            name = str(Name.value) if Name.value else ""
            users.append({"user_id": uid, "name": name})

        print(f"  Found {len(users)} users:")
        for u in users:
            print(f"    - ID={u['user_id']}, Name={u['name'] or '(no name)'}")
        print("[OK] Users read successfully")
except Exception as e:
    print(f"[FAIL] Could not read users: {e}")

# --- Test 5: Read attendance logs ---
print()
print("=" * 50)
print("TEST 5: Read attendance logs")
print("=" * 50)
try:
    result = zk.ReadGeneralLogData(1)
    if not result:
        print("[OK] No attendance logs on device")
    else:
        logs = []
        while True:
            dwEnrollNumber = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwVerifyMode = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwInOutMode = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwYear = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwMonth = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwDay = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwHour = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwMinute = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwSecond = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            dwWorkCode = win32com.client.VARIANT(
                win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
            )
            result = zk.SSR_GetGeneralLogData(
                1, dwEnrollNumber, dwVerifyMode, dwInOutMode,
                dwYear, dwMonth, dwDay, dwHour, dwMinute, dwSecond, dwWorkCode
            )
            if not result:
                break
            ts = f"{dwYear.value:04d}-{dwMonth.value:02d}-{dwDay.value:02d} {dwHour.value:02d}:{dwMinute.value:02d}:{dwSecond.value:02d}"
            logs.append({
                "user_id": int(dwEnrollNumber.value) if dwEnrollNumber.value else 0,
                "in_out": dwInOutMode.value if dwInOutMode.value else 0,
                "timestamp": ts,
            })

        print(f"  Found {len(logs)} attendance logs:")
        for l in logs[-10:]:  # Show last 10
            mode = "CHECK-IN" if l["in_out"] == 0 else "CHECK-OUT"
            print(f"    - User {l['user_id']} {mode} at {l['timestamp']}")
        if len(logs) > 10:
            print(f"    ... and {len(logs) - 10} more")
        print("[OK] Attendance logs read successfully")
except Exception as e:
    print(f"[FAIL] Could not read attendance logs: {e}")

# --- Test 6: Write (create a test user) ---
print()
print("=" * 50)
print("TEST 6: Create test user on device")
print("=" * 50)
TEST_USER_ID = 99999
TEST_USER_NAME = "Test User - DELETE ME"
try:
    result = zk.SSR_SetUserInfo(1, str(TEST_USER_ID), TEST_USER_NAME, "", 0, True)
    if result:
        print(f"[OK] Created test user: ID={TEST_USER_ID}, Name={TEST_USER_NAME}")
    else:
        print("[FAIL] SSR_SetUserInfo returned False")
except Exception as e:
    print(f"[FAIL] Could not create test user: {e}")

# Verify it was created
print("  Verifying user exists...")
try:
    dwEnrollNumber = win32com.client.VARIANT(
        win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_BSTR, ""
    )
    Name = win32com.client.VARIANT(
        win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_BSTR, ""
    )
    Password = win32com.client.VARIANT(
        win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_BSTR, ""
    )
    Privilege = win32com.client.VARIANT(
        win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_I4, 0
    )
    Enabled = win32com.client.VARIANT(
        win32com.client.pythoncom.VT_BYREF | win32com.client.pythoncom.VT_BOOL, False
    )
    result = zk.SSR_GetUserInfo(1, str(TEST_USER_ID), dwEnrollNumber, Name, Password, Privilege, Enabled)
    if result:
        print(f"  Confirmed: user {Name.value} exists on device")
    else:
        print("  [WARN] Could not verify user (SSR_GetUserInfo returned False)")
except Exception as e:
    print(f"  [WARN] Verification error: {e}")

# --- Test 7: Delete the test user ---
print()
print("=" * 50)
print("TEST 7: Delete test user (cleanup)")
print("=" * 50)
try:
    result = zk.SSR_DeleteEnrollData(1, str(TEST_USER_ID), 12)
    if result:
        print(f"[OK] Deleted test user ID={TEST_USER_ID}")
    else:
        print(f"[WARN] Delete returned False — user may need manual cleanup on device")
except Exception as e:
    print(f"[WARN] Delete error: {e}")

# --- Disconnect ---
print()
print("=" * 50)
print("ALL TESTS COMPLETE")
print("=" * 50)
zk.Disconnect()
print("Disconnected from ZK9500.")
print()
print("Summary:")
print("  If all tests passed, the ZK9500 is fully accessible for read/write.")
print("  We can proceed with the attendance sync implementation.")
