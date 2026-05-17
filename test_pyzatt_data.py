"""
Read users and attendance logs from device using pyzatt.

Target: ACP-260 at 192.168.1.201:4370
"""

from pyzatt.pyzatt import ZKSS

DEVICE_IP = "192.168.1.201"
DEVICE_PORT = 4370

zk = ZKSS()

print(f"Connecting to {DEVICE_IP}:{DEVICE_PORT} ...")
zk.connect_net(DEVICE_IP, DEVICE_PORT)
print("Connected!\n")

# --- Read Users ---
print("=" * 50)
print("USERS")
print("=" * 50)
try:
    zk.read_all_user_id()
    if zk.users:
        for sn, user in zk.users.items():
            print(f"  SN={sn}  ID={user.user_id}  Name={user.user_name}  "
                  f"Group={user.user_group}  Admin={user.admin_level}")
    else:
        print("  No users found.")
except Exception as e:
    print(f"  read_all_user_id failed: {e}")

# --- Read Fingerprint Templates ---
print("\n" + "=" * 50)
print("FINGERPRINT TEMPLATES")
print("=" * 50)
try:
    zk.read_all_fptmp()
    found = False
    for sn, user in zk.users.items():
        for fp_idx, (fp_tmp, fp_flag) in enumerate(user.user_fptmps):
            if fp_tmp:
                found = True
                print(f"  User {user.user_id} ({user.user_name}) "
                      f"finger={fp_idx} flag={fp_flag} size={len(fp_tmp)}")
    if not found:
        print("  No fingerprint templates found.")
except Exception as e:
    print(f"  read_all_fptmp failed: {e}")

# --- Read Attendance Log ---
print("\n" + "=" * 50)
print("ATTENDANCE LOG")
print("=" * 50)
try:
    zk.read_att_log()
    if zk.att_log:
        for entry in zk.att_log:
            print(f"  User={entry.user_id}  Time={entry.att_time}  "
                  f"VerType={entry.ver_type}  State={entry.ver_state}")
    else:
        print("  No attendance records found.")
except Exception as e:
    print(f"  read_att_log failed: {e}")

# --- Read Operation Log ---
print("\n" + "=" * 50)
print("OPERATION LOG")
print("=" * 50)
try:
    zk.read_op_log()
    if zk.op_log:
        for entry in zk.op_log:
            print(f"  Op={entry.op_id}  Time={entry.op_time}  "
                  f"P1={entry.param1} P2={entry.param2} "
                  f"P3={entry.param3} P4={entry.param4}")
    else:
        print("  No operation records found.")
except Exception as e:
    print(f"  read_op_log failed: {e}")

zk.disconnect()
print("\nDone.")
