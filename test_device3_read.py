# ZK9500 Read Test - trying multiple methods to read existing users
# Run: python test_device3_read.py
# IMPORTANT: Close ZKAccess 3.5 completely first (check system tray)

import sys
import win32com.client

try:
    import pythoncom
except ImportError:
    pythoncom = None

def vint(val=0):
    if pythoncom:
        return win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, val)
    return win32com.client.VARIANT(0x4000 | 3, val)

def vstr(val=""):
    if pythoncom:
        return win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_BSTR, val)
    return win32com.client.VARIANT(0x4000 | 8, val)

def vbool(val=False):
    if pythoncom:
        return win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_BOOL, val)
    return win32com.client.VARIANT(0x4000 | 11, val)


print("Connecting to ZK9500...")
zk = win32com.client.Dispatch("zkemkeeper.ZKEM.1")
if not zk.Connect_Net("192.168.1.201", 4370):
    print("[FAIL] Cannot connect. Close ZKAccess first!")
    sys.exit(1)
print("[OK] Connected\n")

# Device info first
print("=" * 50)
print("DEVICE INFO")
print("=" * 50)
try:
    v = vstr("")
    zk.GetFirmwareVersion(1, v)
    print(f"  Firmware: {v.value}")
except Exception as e:
    print(f"  Firmware: ({e})")

try:
    v = vstr("")
    zk.GetDevicePlatform(1, v)
    print(f"  Platform: {v.value}")
except Exception as e:
    print(f"  Platform: ({e})")

try:
    v = vstr("")
    zk.GetProductCode(1, v)
    print(f"  Product:  {v.value}")
except Exception as e:
    print(f"  Product:  ({e})")

# User count via GetDeviceStatus
try:
    v = vint(0)
    zk.GetDeviceStatus(1, 1, v)
    print(f"  User count (status): {v.value}")
except Exception as e:
    print(f"  User count: ({e})")

# Log count
try:
    v = vint(0)
    zk.GetDeviceStatus(1, 2, v)
    print(f"  Log count:          {v.value}")
except Exception as e:
    print(f"  Log count: ({e})")

print()


# ============================================================
# Method 1: ReadAllUserID + SSR_GetAllUserInfo
# ============================================================
print("=" * 50)
print("Method 1: ReadAllUserID + SSR_GetAllUserInfo")
print("=" * 50)
try:
    result = zk.ReadAllUserID(1)
    print(f"  ReadAllUserID returned: {result}")
    if result:
        count = 0
        while True:
            uid = vint(0)
            name = vstr("")
            pwd = vstr("")
            priv = vint(0)
            en = vbool(False)
            r = zk.SSR_GetAllUserInfo(1, uid, name, pwd, priv, en)
            if not r:
                break
            count += 1
            print(f"    [{count}] ID={uid.value}, Name={name.value}")
        print(f"  Total: {count} users")
    else:
        print("  Returned False — no data")
except Exception as e:
    print(f"  Error: {e}")


# ============================================================
# Method 2: ReadAllUserID + GetAllUserInfo (integer-based)
# ============================================================
print()
print("=" * 50)
print("Method 2: ReadAllUserID + GetAllUserInfo (non-SSR)")
print("=" * 50)
try:
    result = zk.ReadAllUserID(1)
    print(f"  ReadAllUserID returned: {result}")
    if result:
        count = 0
        while True:
            uid = vint(0)
            name = vstr("")
            pwd = vstr("")
            priv = vint(0)
            en = vbool(False)
            r = zk.GetAllUserInfo(1, uid, name, pwd, priv, en)
            if not r:
                break
            count += 1
            print(f"    [{count}] ID={uid.value}, Name={name.value}")
        print(f"  Total: {count} users")
    else:
        print("  Returned False — no data")
except Exception as e:
    print(f"  Error: {e}")


# ============================================================
# Method 3: ReadAllTemplate + GetAllUserID + GetUserTmpStr
# ============================================================
print()
print("=" * 50)
print("Method 3: ReadAllTemplate then read users")
print("=" * 50)
try:
    # Some devices need templates loaded into buffer first
    result = zk.ReadAllTemplate(1)
    print(f"  ReadAllTemplate returned: {result}")
except Exception as e:
    print(f"  ReadAllTemplate error: {e}")

try:
    result = zk.ReadAllUserID(1)
    print(f"  ReadAllUserID returned: {result}")
    if result:
        count = 0
        while True:
            uid = vint(0)
            name = vstr("")
            pwd = vstr("")
            priv = vint(0)
            en = vbool(False)
            r = zk.SSR_GetAllUserInfo(1, uid, name, pwd, priv, en)
            if not r:
                break
            count += 1
            print(f"    [{count}] ID={uid.value}, Name={name.value}")
        print(f"  Total: {count} users")
    else:
        print("  Still no data")
except Exception as e:
    print(f"  Error: {e}")


# ============================================================
# Method 4: EnableDevice(False) then read
# ============================================================
print()
print("=" * 50)
print("Method 4: Lock device then read")
print("=" * 50)
try:
    zk.EnableDevice(1, False)
    print("  Device locked")

    result = zk.ReadAllUserID(1)
    print(f"  ReadAllUserID returned: {result}")
    if result:
        count = 0
        while True:
            uid = vint(0)
            name = vstr("")
            pwd = vstr("")
            priv = vint(0)
            en = vbool(False)
            r = zk.SSR_GetAllUserInfo(1, uid, name, pwd, priv, en)
            if not r:
                break
            count += 1
            print(f"    [{count}] ID={uid.value}, Name={name.value}")
        print(f"  Total: {count} users")
    else:
        print("  Still no data")

    zk.EnableDevice(1, True)
    print("  Device unlocked")
except Exception as e:
    print(f"  Error: {e}")
    try:
        zk.EnableDevice(1, True)
    except:
        pass


# ============================================================
# Method 5: Direct query one-by-one (common user IDs 1-100)
# ============================================================
print()
print("=" * 50)
print("Method 5: Query specific user IDs directly (1-50)")
print("=" * 50)
found = 0
for test_id in range(1, 51):
    try:
        # Try SSR_GetUserInfo
        uid = vstr(str(test_id))
        name = vstr("")
        pwd = vstr("")
        priv = vint(0)
        en = vbool(False)
        # SSR_GetUserInfo(machineNum, enrollNumber, name, password, privilege, enabled)
        r = zk.SSR_GetUserInfo(1, uid, name, pwd, priv, en)
        if r and name.value:
            found += 1
            print(f"    [{found}] ID={test_id}, Name={name.value}")
    except:
        pass

if found == 0:
    print("  No users found in range 1-50 via SSR_GetUserInfo")
else:
    print(f"  Found {found} users in range 1-50")


# ============================================================
# Method 6: Try GetUserIDBySN approach
# ============================================================
print()
print("=" * 50)
print("Method 6: GetUserID with different ID ranges")
print("=" * 50)
found = 0
for test_id in range(1, 301):
    try:
        uid = vstr(str(test_id))
        name = vstr("")
        pwd = vstr("")
        priv = vint(0)
        en = vbool(False)
        r = zk.SSR_GetUserInfo(1, uid, name, pwd, priv, en)
        if r and name.value:
            found += 1
            print(f"    [{found}] ID={test_id}, Name={name.value}")
    except:
        pass

if found == 0:
    print("  No users found in range 1-300")
else:
    print(f"  Total found: {found} users")


print()
zk.Disconnect()
print("Disconnected. Done.")
