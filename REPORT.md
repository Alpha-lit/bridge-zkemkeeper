# Gym Fingerprint Gate Integration — Investigation Report

**Date:** 2026-05-13 to 2026-05-17
**Goal:** Connect the gym's turnstile fingerprint gate to Django for automated member attendance tracking.
**Result:** FAILED — hardware limitation, requires reader upgrade.

---

## Hardware Setup

```
ZKTeco Fingerprint Reader (Wiegand-only, model unknown)
  → Scans finger, matches locally against its own internal database
  → Sends only a binary "open gate" signal via Wiegand wire
  → NO network connection, NO USB, NO SDK access
  → Stores users and fingerprint templates in its own memory

ACP-260 Access Control Panel (192.168.1.201:4370)
  → Receives relay trigger from reader
  → Opens the gate arm
  → Firmware: AC Ver 5.2.5 Jun 6 2019
  → Serial: BRI3225160081
  → MAC: 00:17:61:11:9A:86

ZK-TS1000-PRO Tripod Turnstile Gate
  → Physical barrier with 2 doors (Gate Control-1, Gate Control-2)
  → 4 reader connections (In/Out for each door)
  → Only "In" readers are active

ZKAccess 3.5 (on entrance Windows PC)
  → Installed at C:\Program Files (x86)\ZKTeco\ZKAccess3.5\
  → Database: Access.mdb (Microsoft Access)
  → Database is EMPTY: 0 users, 0 logs, 0 fingerprint templates
  → Was installed but never actually used
```

---

## What We Tried

### Attempt 1: zkemkeeper COM SDK (12+ test scripts)

**Tool:** `zkemkeeper.dll` via `win32com.client` (ZKTeco's official SDK)
**Setup:** 32-bit Python required, DLL registered via `regsvr32`

| Test | Method | Result |
|------|--------|--------|
| TCP connection | `Connect_Net("192.168.1.201", 4370)` | OK — connects |
| Device IP | `GetDeviceIP(1)` | OK — returns `192.168.1.201` |
| Device MAC | `GetDeviceMAC(1)` | OK — returns `00:17:61:11:9A:86` |
| Device time | `GetDeviceTime(1)` | OK — returns current time |
| Firmware version | `GetFirmwareVersion(1)` | OK — `AC Ver 5.2.5 Jun 6 2019` |
| Product code | `GetProductCode(1)` | OK — `ACP-260` |
| Beep | `Beep(150)` | FAILED — no sound |
| Read users | `ReadAllUserID`, `GetAllUserID`, `SSR_GetUserInfo` | FAILED — all return False/empty |
| Read logs | `ReadGeneralLogData`, `ReadAllGLogData`, + 8 more methods | FAILED — all return False |
| Real-time logs | `ReadRTLog` returns True but no extractable data | FAILED |
| Write user | `SSR_SetUserInfo`, `SetUserInfo`, `SetUserName` | FAILED — all return False |
| Enroll fingerprint | `StartEnrollEx`, `StartEnroll` | FAILED — return False |
| Delete user | `SSR_DeleteEnrollData` | FAILED — returns False |
| Event listener | `DispatchWithEvents` + `RegEvent` + `OnAttTransaction` | FAILED — no events |
| Log count polling | `GetDeviceStatus(1, 2)` in loop | Count stays at 1027, never changes on scan |

**Verdict:** The ACP-260 responds to basic device-info commands but ALL data operations fail. It doesn't store or expose user data, attendance logs, or fingerprint templates.

### Attempt 2: ZKAccess Database (Access.mdb)

**Tool:** `pyodbc` reading Microsoft Access database

| Table | Rows | Content |
|-------|------|---------|
| USERINFO | 0 | No users registered in ZKAccess |
| CHECKINOUT | 0 | No attendance records |
| TEMPLATE | 0 | No fingerprint templates |
| acc_monitor_log | 9 | Old door events from March 2024 only |
| Machines | 1 | ACP-260 device config |
| acc_reader | 4 | Gate Control-1 In/Out, Gate Control-2 In/Out |
| acc_door | 2 | 2 door configurations |

Also tried "Download Logs" / "Sync" from ZKAccess UI — CHECKINOUT remained empty.

**Verdict:** ZKAccess was installed but never used. It cannot pull data from the ACP-260 either.

### Attempt 3: pyzatt (Raw ZK Protocol over TCP)

**Tool:** `pyzatt` library — pure Python, no DLL, no Windows dependency
**GitHub:** https://github.com/adrobinoga/pyzatt

```
TCP connection to 192.168.1.201:4370 → SUCCESS
Sent ZK connect command → NO RESPONSE (timed out after 5 seconds)
```

The ACP-260 accepts TCP connections on port 4370 but completely ignores all ZK protocol commands. It never sends any data back.

**Verdict:** Raw protocol doesn't work either. The panel isn't a ZK protocol device — it's a relay controller.

---

## Root Cause

The fingerprint readers are **Wiegand-only devices** connected to the ACP-260 via Wiegand cable with NO network connection of their own. They:

1. Store the entire user database and fingerprint templates in their own internal memory
2. Match fingerprints entirely locally
3. Only send a binary "open gate" relay trigger to the ACP-260
4. Send NO user ID, NO timestamp, NO identification data through the Wiegand wire

The ACP-260 panel:
- Receives only a relay trigger (not user data)
- Cannot read or write user data or fingerprint templates
- Cannot respond to ZK protocol commands (accepts TCP but ignores everything)
- Has 1,027 old door events from 2024 that are NOT fingerprint scans (just relay triggers)

**No software solution exists for this hardware configuration.** The data we need (user ID, timestamp per scan) is never transmitted outside the reader.

---

## Solution: Hardware Upgrade Required

Replace the Wiegand-only readers with **network-enabled fingerprint readers** that:

1. Have their own IP address on the local network
2. Support full ZK protocol or zkemkeeper SDK (users, fingerprints, logs, enrollment)
3. Have Wiegand output (to connect to the ACP-260 for gate relay — keeps existing gate working)
4. Compatible with the ZK-TS1000-PRO turnstile

**Recommended:** ZKTeco SpeedFace V4L (~$100-150)

Once a network reader is installed:
- pyzatt or zkemkeeper bridge connects directly to the reader's IP
- Django endpoints (already built) receive attendance data from the bridge
- Frontend gym portal (already built) displays check-in/check-out
- Reader still triggers the gate via Wiegand to ACP-260 (no changes to gate wiring)

---

## What's Already Built (Ready to Use After Hardware Upgrade)

### Backend (Django)
- `GymMember` model (name, phone, email, fingerprint_template, zk_user_id)
- `MembershipPass` model (MONTHLY/ANNUAL/CUSTOM, duration, price, status)
- `CheckInLog` model (check_in_time, check_out_time, verified_via)
- Full API: members CRUD, pass management, check-in/check-out, fingerprint enrollment
- Migration: `0019_add_gym_store_and_models.py`

### Frontend (React)
- Separate gym portal: `/gym/login`, `/gym/checkin`, `/gym/members`
- `GymCheckInScreen` — full-screen check-in with sound feedback
- `GymMembersScreen` — member management, search, pass issuing
- Emerald-themed layout with inactivity timeout

### Bridge (in this repo)
- `test_pyzatt_connect.py` — connection test
- `test_pyzatt_data.py` — read users, fingerprints, attendance logs
- `test_pyzatt_realtime.py` — live event monitoring
- Old COM-based bridge backed up (zkemkeeper approach, works with network readers too)

### Entrance PC Setup
- Python 3.12 installed (both 32-bit for COM and 64-bit for pyzatt)
- `zkemkeeper.dll` registered (for COM approach)
- pyzatt installed from GitHub
- Firefox required (Chrome blocks localhost requests from public origins)
- Project files at `C:\Users\hp\Downloads\bridge-zkemkeeper-main\`

---

## Time Wasted

| Approach | Scripts Written | Time | Result |
|----------|----------------|------|--------|
| zkemkeeper COM | 14 test scripts | ~6 hours | Device info works, all data ops fail |
| ZKAccess database | 3 scripts | ~1 hour | Database completely empty |
| pyzatt raw protocol | 3 test scripts | ~1 hour | TCP connects, protocol ignored |

**Don't repeat these attempts.** All three approaches fail for the same reason: the hardware physically cannot provide the data. Skip straight to buying a network-enabled reader.
