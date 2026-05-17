"""
ZK9500 Write Test — diagnosing why SSR_SetUserInfo fails.

Run on entrance PC:
  "C:\Users\hp\AppData\Local\Programs\Python\Python312-32\python.exe" test_device2.py

Close ZKAccess 3.5 first!
"""

import sys
import win32com.client

# Fix: use pythoncom directly, not win32com.client.pythoncom
try:
    import pythoncom
except ImportError:
    pythoncom = None

def make_variant_int(val=0):
    if pythoncom:
        return win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, val)
    return win32com.client.VARIANT(0x4000 | 3, val)  # fallback

def make_variant_str(val=""):
    if pythoncom:
        return win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_BSTR, val)
    return win32com.client.VARIANT(0x4000 | 8, val)

def make_variant_bool(val=False):
    if pythoncom:
        return win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_BOOL, val)
    return win32com.client.VARIANT(0x4000 | 11, val)


print("Connecting to ZK9500...")
zk = win32com.client.Dispatch("zkemkeeper.ZKEM.1")
if not zk.Connect_Net("192.168.1.201", 4370):
    print("[FAIL] Cannot connect. Close ZKAccess first.")
    sys.exit(1)
print("[OK] Connected\n")


# --- Device info (fixed) ---
print("=" * 50)
print("DEVICE INFO")
print("=" * 50)
try:
    vFirmware = make_variant_str("")
    zk.GetFirmwareVersion(1, vFirmware)
    print(f"  Firmware: {vFirmware.value}")
except Exception as e:
    print(f"  Firmware: error ({e})")

try:
    vSN = make_variant_str("")
    zk.GetSerialNumber(1, vSN)
    print(f"  Serial:   {vSN.value}")
except Exception as e:
    print(f"  Serial:   error ({e})")

try:
    vCount = make_variant_int(0)
    zk.GetDeviceStatus(1, 1, vCount)  # 1=user count
    print(f"  Users:    {vCount.value}")
except Exception as e:
    print(f"  Users:    error ({e})")

try:
    vLogs = make_variant_int(0)
    zk.GetDeviceStatus(1, 2, vLogs)  # 2=log count
    print(f"  Logs:     {vLogs.value}")
except Exception as e:
    print(f"  Logs:     error ({e})")

# Device name
try:
    vName = make_variant_str("")
    zk.GetDeviceName(1, vName)
    print(f"  Name:     {vName.value}")
except Exception as e:
    print(f"  Name:     error ({e})")

# Platform/Model
try:
    vPlatform = make_variant_str("")
    zk.GetDevicePlatform(1, vPlatform)
    print(f"  Platform: {vPlatform.value}")
except Exception as e:
    print(f"  Platform: error ({e})")

# Product code
try:
    vProduct = make_variant_str("")
    zk.GetProductCode(1, vProduct)
    print(f"  Product:  {vProduct.value}")
except Exception as e:
    print(f"  Product:  error ({e})")

print()


# --- Test different write methods ---
TEST_ID = 99999
TEST_NAME = "Test User - DEL"

print("=" * 50)
print(f"WRITE TEST: Trying methods to create user {TEST_ID}")
print("=" * 50)

# Method 1: SSR_SetUserInfo (string-based, for newer devices)
print("\nMethod 1: SSR_SetUserInfo (string user ID)...")
try:
    result = zk.SSR_SetUserInfo(1, str(TEST_ID), TEST_NAME, "", 0, True)
    print(f"  Result: {result}")
except Exception as e:
    print(f"  Error: {e}")

# Method 2: SetUserInfo (integer-based, for older devices)
print("\nMethod 2: SetUserInfo (integer user ID)...")
try:
    result = zk.SetUserInfo(1, TEST_ID, TEST_NAME, "", 0, True)
    print(f"  Result: {result}")
except Exception as e:
    print(f"  Error: {e}")

# Method 3: SetStrCardNumber + SetUserInfo pattern
print("\nMethod 3: SSR_SetUserInfo with card number...")
try:
    # Some devices need card number set first
    zk.SetStrCardNumber("")
    result = zk.SSR_SetUserInfo(1, str(TEST_ID), TEST_NAME, "", 0, True)
    print(f"  Result: {result}")
except Exception as e:
    print(f"  Error: {e}")

# Method 4: Enable device explicitly before write
print("\nMethod 4: EnableDevice(False) -> write -> EnableDevice(True)...")
try:
    zk.EnableDevice(1, False)  # Lock device for operation
    result = zk.SSR_SetUserInfo(1, str(TEST_ID), TEST_NAME, "", 0, True)
    print(f"  Result: {result}")
    zk.EnableDevice(1, True)   # Unlock
except Exception as e:
    print(f"  Error: {e}")
    try:
        zk.EnableDevice(1, True)  # Make sure we unlock
    except:
        pass

# Method 5: Check if communication password is needed
print("\nMethod 5: Setting communication password to 0 (default)...")
try:
    # Some devices have a comm password that must be set before operations
    zk.SetCommPassword(0)
    result = zk.SSR_SetUserInfo(1, str(TEST_ID), TEST_NAME, "", 0, True)
    print(f"  Result: {result}")
except Exception as e:
    print(f"  Error: {e}")

# Method 6: Try with smaller user ID (some devices have limits)
print("\nMethod 6: Try with small user ID (ID=50)...")
try:
    result = zk.SSR_SetUserInfo(1, "50", "Test Small ID", "", 0, True)
    print(f"  Result: {result}")
except Exception as e:
    print(f"  Error: {e}")

print()


# --- Verify: read users again ---
print("=" * 50)
print("VERIFY: Read all users after write attempts")
print("=" * 50)
try:
    result = zk.ReadAllUserID(1)
    if not result:
        print("  No users found on device")
    else:
        found = []
        while True:
            dwEnrollNumber = make_variant_int(0)
            Name = make_variant_str("")
            Password = make_variant_str("")
            Privilege = make_variant_int(0)
            Enabled = make_variant_bool(False)
            result = zk.SSR_GetAllUserInfo(1, dwEnrollNumber, Name, Password, Privilege, Enabled)
            if not result:
                break
            uid = int(dwEnrollNumber.value) if dwEnrollNumber.value else 0
            name = str(Name.value) if Name.value else ""
            found.append({"user_id": uid, "name": name})

        if found:
            print(f"  Found {len(found)} users:")
            for u in found:
                print(f"    - ID={u['user_id']}, Name={u['name']}")
        else:
            print("  No users found (SSR_GetAllUserInfo returned nothing)")
except Exception as e:
    print(f"  Error: {e}")

print()


# --- Cleanup: delete any test users ---
print("=" * 50)
print("CLEANUP: Deleting test users")
print("=" * 50)
for uid in [99999, 50]:
    try:
        result = zk.SSR_DeleteEnrollData(1, str(uid), 12)
        if result:
            print(f"  Deleted user {uid}: OK")
        else:
            print(f"  Delete user {uid}: returned False (may not exist)")
    except Exception as e:
        print(f"  Delete user {uid}: error ({e})")

print()
zk.Disconnect()
print("Disconnected. Done.")
