# ZK9500 Connection + Enrollment Test
# Step 1: verify connection is truly alive (beep, time)
# Step 2: try to create a user and enroll fingerprint
# Step 3: you scan your finger to verify it works

import sys
import time
import win32com.client

print("Connecting to ZK9500...")
zk = win32com.client.Dispatch("zkemkeeper.ZKEM.1")
result = zk.Connect_Net("192.168.1.201", 4370)
print(f"Connect_Net returned: {result}")

if not result:
    print("[FAIL] Cannot connect.")
    sys.exit(1)

# Give the connection a moment
time.sleep(1)

# --- Step 1: Is the connection truly alive? ---
print()
print("STEP 1: Test if connection is alive")
print("-" * 40)

# Test 1a: Beep the device (simplest possible operation)
print("Test 1a: Beep the device...")
try:
    zk.Beep(150)  # 150ms beep
    print("  Beep() called - did the device make a sound? (Y/N)")
except Exception as e:
    print(f"  Beep error: {e}")

# Test 1b: Get device IP (should work even with bad connection)
print()
print("Test 1b: Get device IP...")
try:
    ip = zk.GetDeviceIP(1)
    print(f"  Device IP: {ip}")
except Exception as e:
    print(f"  Error: {e}")

# Test 1c: Try getting device time a simpler way
print()
print("Test 1c: Get device time...")
try:
    import pythoncom
    dwYear = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    dwMonth = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    dwDay = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    dwHour = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    dwMinute = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    dwSecond = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    r = zk.GetDeviceTime(1, dwYear, dwMonth, dwDay, dwHour, dwMinute, dwSecond)
    if r:
        print(f"  Device time: {dwYear.value}-{dwMonth.value:02d}-{dwDay.value:02d} {dwHour.value:02d}:{dwMinute.value:02d}:{dwSecond.value:02d}")
    else:
        print("  GetDeviceTime returned False")
except Exception as e:
    print(f"  Error: {e}")

# Test 1d: Check if device is actually a ZK9500
print()
print("Test 1d: Device identification...")
try:
    # Try GetDeviceMAC
    mac = zk.GetDeviceMAC(1)
    print(f"  MAC: {mac}")
except Exception as e:
    print(f"  MAC error: {e}")

# Test 1e: Try GetVendor
try:
    vendor = zk.GetVendor(1)
    print(f"  Vendor: {vendor}")
except Exception as e:
    print(f"  Vendor error: {e}")


# --- Step 2: Try creating a test user ---
print()
print("STEP 2: Create test user")
print("-" * 40)

TEST_UID = 1
TEST_NAME = "Test Ibrahim"

# Enable device for operations
print("Locking device for write...")
zk.EnableDevice(1, False)

print(f"Creating user ID={TEST_UID}, Name={TEST_NAME}...")
try:
    # Method A: SSR_SetUserInfo
    r = zk.SSR_SetUserInfo(1, str(TEST_UID), TEST_NAME, "", 0, True)
    print(f"  SSR_SetUserInfo: {r}")
except Exception as e:
    print(f"  SSR_SetUserInfo error: {e}")

try:
    # Method B: SetUserInfo (integer-based)
    r = zk.SetUserInfo(1, TEST_UID, TEST_NAME, "", 0, True)
    print(f"  SetUserInfo: {r}")
except Exception as e:
    print(f"  SetUserInfo error: {e}")

try:
    # Method C: SetUserName
    r = zk.SetUserName(1, str(TEST_UID), TEST_NAME)
    print(f"  SetUserName: {r}")
except Exception as e:
    print(f"  SetUserName error: {e}")

# Verify: read back
print()
print("Verifying user was created...")
try:
    import pythoncom
    uid = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_BSTR, str(TEST_UID))
    name = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_BSTR, "")
    pwd = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_BSTR, "")
    priv = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    en = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_BOOL, False)
    r = zk.SSR_GetUserInfo(1, uid, name, pwd, priv, en)
    if r:
        print(f"  Found: ID={uid.value}, Name={name.value}")
    else:
        print("  SSR_GetUserInfo returned False")
except Exception as e:
    print(f"  Error: {e}")

# Unlock device
zk.EnableDevice(1, True)
print("Device unlocked.")


# --- Step 3: Enroll fingerprint ---
print()
print("STEP 3: Enroll fingerprint")
print("-" * 40)
print("This will tell the device to wait for a finger placement.")
print("Place your finger on the scanner when prompted.")
print()

try:
    # StartEnrollEx(machineNum, enrollNumber, fingerIndex, flag)
    r = zk.StartEnrollEx(1, str(TEST_UID), 0, 0)
    print(f"StartEnrollEx: {r}")
    if r:
        print()
        print(">>> PLACE YOUR FINGER ON THE SCANNER NOW <<<")
        print("The device should be waiting for your finger.")
        print("You may need to lift and place 2-3 times.")
        print()
    else:
        # Try StartEnroll (non-Ex version)
        try:
            r = zk.StartEnroll(str(TEST_UID), 0, 0)
            print(f"StartEnroll: {r}")
            if r:
                print()
                print(">>> PLACE YOUR FINGER ON THE SCANNER NOW <<<")
        except Exception as e2:
            print(f"StartEnroll error: {e2}")
except Exception as e:
    print(f"StartEnrollEx error: {e}")
    try:
        r = zk.StartEnroll(str(TEST_UID), 0, 0)
        print(f"StartEnroll (fallback): {r}")
        if r:
            print()
            print(">>> PLACE YOUR FINGER ON THE SCANNER NOW <<<")
    except Exception as e2:
        print(f"StartEnroll fallback error: {e2}")

# Wait and let device process enrollment
print("Waiting 15 seconds for enrollment...")
time.sleep(15)

# Check if enrollment worked by trying to read the template
print()
print("Checking if fingerprint was enrolled...")
try:
    import pythoncom
    tmpFlag = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    tmpData = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_BSTR, "")
    tmpLength = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    r = zk.GetUserTmpStr(1, str(TEST_UID), 0, tmpFlag, tmpData, tmpLength)
    if r and tmpData.value:
        print(f"  Fingerprint enrolled! Template length: {tmpLength.value}")
    else:
        print("  No fingerprint template found (enrollment may have failed)")
except Exception as e:
    print(f"  Template check error: {e}")


print()
print("=" * 50)
print("DONE")
print("=" * 50)
print()
print("If enrollment worked, you can test by scanning your finger")
print("at the gate to see if it recognizes you.")
print()
zk.Disconnect()
print("Disconnected.")
