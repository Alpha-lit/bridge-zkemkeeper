# ZK9500 Discover actual COM interface + test with correct params
# The previous tests showed methods return (success, value) tuples
# and have different parameter counts than documented.

import sys
import time
import win32com.client

print("Connecting...")
zk = win32com.client.Dispatch("zkemkeeper.ZKEM.1")
r = zk.Connect_Net("192.168.1.201", 4370)
print(f"Connect_Net: {r}\n")
time.sleep(0.5)

# --- Discover: try calling methods with fewer params ---
print("=" * 50)
print("PART 1: Read device info (tuple-return style)")
print("=" * 50)

# These returned (True, value) last time
print(f"GetDeviceIP: {zk.GetDeviceIP(1)}")
print(f"GetDeviceMAC: {zk.GetDeviceMAC(1)}")

# Try GetDeviceTime without VARIANT
print("\nTrying GetDeviceTime...")
try:
    result = zk.GetDeviceTime(1)
    print(f"  GetDeviceTime(1): {result}")
except Exception as e:
    print(f"  Error: {e}")

# Try with more params
try:
    result = zk.GetDeviceTime(1, 0, 0, 0, 0, 0, 0)
    print(f"  GetDeviceTime(1,0,0,0,0,0,0): {result}")
except Exception as e:
    print(f"  Error: {e}")

# Try GetFirmwareVersion
try:
    result = zk.GetFirmwareVersion(1)
    print(f"GetFirmwareVersion(1): {result}")
except Exception as e:
    print(f"GetFirmwareVersion error: {e}")

# Try GetProductCode
try:
    result = zk.GetProductCode(1)
    print(f"GetProductCode(1): {result}")
except Exception as e:
    print(f"GetProductCode error: {e}")

# Try GetDevicePlatform
try:
    result = zk.GetDevicePlatform(1)
    print(f"GetDevicePlatform(1): {result}")
except Exception as e:
    print(f"GetDevicePlatform error: {e}")

# Try GetSerialNumber
try:
    result = zk.GetSerialNumber(1)
    print(f"GetSerialNumber(1): {result}")
except Exception as e:
    print(f"GetSerialNumber error: {e}")

# Device status (user count) - try without VARIANT
print("\nDevice status...")
try:
    result = zk.GetDeviceStatus(1, 1)  # 1=user count
    print(f"GetDeviceStatus(1, 1) user count: {result}")
except Exception as e:
    print(f"  Error: {e}")

try:
    result = zk.GetDeviceStatus(1, 2)  # 2=log count
    print(f"GetDeviceStatus(1, 2) log count: {result}")
except Exception as e:
    print(f"  Error: {e}")

# Try with VARIANT as third param
try:
    import pythoncom
    v = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
    result = zk.GetDeviceStatus(1, 1, v)
    print(f"GetDeviceStatus(1, 1, VARIANT): result={result}, value={v.value}")
except Exception as e:
    print(f"  VARIANT error: {e}")


# --- PART 2: Read users ---
print()
print("=" * 50)
print("PART 2: Read users (trying different approaches)")
print("=" * 50)

# ReadAllUserID
print(f"ReadAllUserID(1): {zk.ReadAllUserID(1)}")

# Try reading user directly - try with fewer params
print("\nTrying SSR_GetUserInfo with different param counts...")
for test_id in [1, 2, 3]:
    try:
        # Try with 2 params (machineNum, enrollNumber)
        result = zk.SSR_GetUserInfo(1, str(test_id))
        print(f"  SSR_GetUserInfo(1, '{test_id}'): {result}")
    except Exception as e:
        print(f"  SSR_GetUserInfo(1, '{test_id}') error: {e}")

# Try GetAllUserInfo without VARIANT
print("\nTrying GetAllUserID...")
try:
    result = zk.GetAllUserID(1)
    print(f"  GetAllUserID(1): {result}")
except Exception as e:
    print(f"  Error: {e}")

# Try ReadAllUserID then SSR_GetAllUserInfo without VARIANT
print("\nReadAllUserID + SSR_GetAllUserInfo (no VARIANT)...")
try:
    r = zk.ReadAllUserID(1)
    print(f"  ReadAllUserID: {r}")
    if r:
        count = 0
        while count < 50:
            try:
                result = zk.SSR_GetAllUserInfo(1)
                if not result or (isinstance(result, tuple) and not result[0]):
                    break
                print(f"  User: {result}")
                count += 1
            except:
                break
        print(f"  Found {count} users")
except Exception as e:
    print(f"  Error: {e}")


# --- PART 3: Write user (try correct param counts) ---
print()
print("=" * 50)
print("PART 3: Create test user (trying correct param counts)")
print("=" * 50)

TEST_ID = "1"
TEST_NAME = "TestIbrahim"

# SSR_SetUserInfo - try different param counts
print("Trying SSR_SetUserInfo...")
for params in [
    (1, TEST_ID, TEST_NAME, "", 0, True),      # 6 params (what we tried)
    (TEST_ID, TEST_NAME, "", 0, True),          # 5 params (no machine num)
    (1, TEST_ID, TEST_NAME),                     # 4 params (minimal)
    (TEST_ID, TEST_NAME),                        # 3 params
]:
    try:
        result = zk.SSR_SetUserInfo(*params)
        print(f"  SSR_SetUserInfo{params}: {result}")
    except Exception as e:
        print(f"  SSR_SetUserInfo{params}: error - {e}")

# SetUserInfo - try different param counts
print("\nTrying SetUserInfo...")
for params in [
    (1, 1, TEST_NAME, "", 0, True),             # 6 params
    (1, TEST_NAME, "", 0, True),                # 5 params
    (1, 1, TEST_NAME),                           # 4 params
]:
    try:
        result = zk.SetUserInfo(*params)
        print(f"  SetUserInfo{params}: {result}")
    except Exception as e:
        print(f"  SetUserInfo{params}: error - {e}")


# --- PART 4: Enrollment ---
print()
print("=" * 50)
print("PART 4: Try enrollment with correct param counts")
print("=" * 50)

print("Trying StartEnrollEx...")
for params in [
    (1, TEST_ID, 0, 0),     # 4 params (what we tried - failed)
    (TEST_ID, 0, 0),        # 3 params
    (1, TEST_ID, 0),        # 3 params (no flag)
    (TEST_ID, 0),           # 2 params
]:
    try:
        result = zk.StartEnrollEx(*params)
        print(f"  StartEnrollEx{params}: {result}")
    except Exception as e:
        print(f"  StartEnrollEx{params}: error - {e}")

print("\nTrying StartEnroll...")
for params in [
    (1, TEST_ID, 0),     # 3 params (what we tried - failed)
    (TEST_ID, 0),        # 2 params
    (TEST_ID,),          # 1 param
]:
    try:
        result = zk.StartEnroll(*params)
        print(f"  StartEnroll{params}: {result}")
    except Exception as e:
        print(f"  StartEnroll{params}: error - {e}")


print()
zk.Disconnect()
print("Disconnected.")
