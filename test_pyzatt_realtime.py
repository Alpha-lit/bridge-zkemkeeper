"""
Monitor realtime events from device using pyzatt.

Waits for fingerprint scans and prints attendance events live.
Press Ctrl+C to stop.

Target: ACP-260 at 192.168.1.201:4370
"""

import time
from pyzatt.pyzatt import ZKSS

DEVICE_IP = "192.168.1.201"
DEVICE_PORT = 4370

zk = ZKSS()

print(f"Connecting to {DEVICE_IP}:{DEVICE_PORT} ...")
zk.connect_net(DEVICE_IP, DEVICE_PORT)
print("Connected!")

print("Enabling realtime events...")
zk.enable_realtime()
print("Listening for events. Scan a finger on the reader...")
print("Press Ctrl+C to stop.\n")

try:
    while True:
        try:
            zk.recv_event()
            event_code = zk.get_last_event()

            if event_code == 0x00:
                # EF_ATTLOG - attendance event
                uid, ver_type, date_str = zk.parse_event_attlog()
                if uid:
                    ver_labels = {0: "password", 1: "fingerprint", 2: "RFID"}
                    ver_label = ver_labels.get(ver_type, f"unknown({ver_type})")
                    print(f"[ATTENDANCE] User={uid}  Method={ver_label}  Time={date_str}")
                else:
                    print(f"[EVENT 0x00] Empty attendance event")

            elif event_code == 0x05:
                # EF_VERIFY - verify event
                user_sn = zk.parse_verify_event()
                print(f"[VERIFY] User SN={user_sn}")

            elif event_code == 0x06:
                # EF_ENROLLFINGER
                success, uid, fp_idx, fp_size = zk.parse_event_enroll_fp()
                print(f"[ENROLL] Success={success} User={uid} Finger={fp_idx} Size={fp_size}")

            elif event_code == 0x07:
                # EF_FPFTR - finger score
                score = zk.parse_score_fp_event()
                print(f"[FP SCORE] Score={score}")

            elif event_code == 0x08:
                # EF_ALARM
                alarm_type, sn, match = zk.parse_duress_alarm()
                print(f"[ALARM] Type={alarm_type} SN={sn} Match={match}")

            else:
                print(f"[EVENT 0x{event_code:02x}] Unknown event")

        except Exception as e:
            print(f"Event error: {e}")
            time.sleep(0.5)

except KeyboardInterrupt:
    print("\nStopped.")

zk.disconnect()
print("Disconnected.")
