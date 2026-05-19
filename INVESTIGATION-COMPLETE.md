# Gym Fingerprint Gate — Complete Investigation & Re-engineering Plan

**Date:** 2026-05-13 to 2026-05-19
**Location:** Golsan Sports Gym
**Investigator:** Ibrahim (with Claude AI assistance)
**Status:** Software dead end identified, re-engineering plan designed

---

## Table of Contents

1. [The Goal](#1-the-goal)
2. [Hardware Inventory](#2-hardware-inventory)
3. [Network Map](#3-network-map)
4. [Investigation Timeline](#4-investigation-timeline)
5. [What We Learned](#5-what-we-learned)
6. [The Mystery: Why Raw Sockets Fail](#6-the-mystery)
7. [Key Discovery: Device Architecture](#7-key-discovery)
8. [Re-engineering Plan](#8-re-engineering-plan)
9. [Scripts Reference](#9-scripts-reference)

---

## 1. The Goal

Connect the gym's turnstile fingerprint gate to the Django backend so that:
- Member fingerprints are stored in **our** Django database
- When a member scans their finger, **our system** verifies identity and checks membership
- Active members → gate opens, check-in logged
- Expired members → denied, gate stays closed
- All attendance data flows into Django for reporting

---

## 2. Hardware Inventory

### ZKTeco TS1022 Pro Tripod Turnstile
- Metal barrier with 2 gate passages (Gate Control-1, Gate Control-2)
- 4 reader connection points (In/Out for each door)
- Only "In" readers are active (readers 1 and 3)
- Power: AC 100-240V, 60W
- Weight: ~35 kg
- IP54 rated
- Passage rate: 30 per minute
- DIP switch (K1, 8 pins): opening duration, direction, continue passing, alarm
- Connectors: J1 (power), J2 (motor), J3-J6 (sensors), J7 (relay), J9 (12V to access control, max 3A)

### ACP-260 Access Control Panel
- IP: 192.168.1.201, Port: 4370 (TCP), Gateway: 192.168.1.254
- Mainboard: **C3-260-MAIN 2.0-11AV**
- Micro PC board: **565HB-Inbio 1.1-52A-V** (this is the ZEM560 Linux board)
- Firmware: AC Ver 5.2.5 Jun 6 2019
- Serial: BRI3225160081
- MAC: 00:17:61:11:9A:86
- device_type: 9, acpanel_type: 2, DevSDKType: 1
- **Same hardware as InBio-260 / C3-260** — different firmware branding
- 2 doors, 4 readers, 2 aux in, 2 aux out
- max_finger_count: 10, BiometricType: 000000000
- comm_type: 3
- Runs Linux 2.6.24 on MIPS (ZEM560)
- **Open ports: 4370 (TCP) and 23 (Telnet)**
- Telnet login: shows "Welcome to Linux (ZEM560) for MIPS" then "ZEM560 login:" — password unknown

### Fingerprint Readers (2x)
- Mounted on the turnstile, one per gate passage
- Originally assumed to be "Wiegand-only" but research suggests they may be **FR1200** (RS-485 slave readers)
- FR1200 specs: optical sensor, ZKFinger VX10.0, RS-485 + OSDP, AES128 encryption, IP65
- If FR1200: they send raw fingerprint templates to the controller (don't match internally)
- If generic Wiegand: they match internally and only send a binary trigger

### ZK4500 USB Fingerprint Scanner
- Already owned by the gym
- USB connection to PC
- Used for desktop fingerprint capture
- Currently unused in the gate setup

### Entrance PC
- Windows, connected to the same network as the gate
- ZKAccess 3.5 installed at `C:\Program Files (x86)\ZKTeco\ZKAccess3.5\`
- Access.mdb database (Microsoft Access) — empty (0 users, 0 logs, 0 templates)
- Python 3.12 installed
- zkemkeeper.dll registered via regsvr32
- pyzatt installed from GitHub
- Bridge files at `C:\Users\hp\Downloads\bridge-zkemkeeper-main\`

---

## 3. Network Map

```
                         Local Network (192.168.1.x)
                         Gateway: 192.168.1.254
                              │
              ┌───────────────┼───────────────┐
              │               │               │
        Entrance PC    ACP-260 Panel     (other devices)
      192.168.1.xxx   192.168.1.201
              │          Port 4370 (TCP)
              │          Port 23 (Telnet)
              │               │
         ZK4500 USB          │ RS-485 (or Wiegand)
         (available)         │
              │         ┌────┴────┐
              │    Reader 1    Reader 3
              │    (Gate 1 In) (Gate 2 In)
              │
         ZKAccess 3.5
         (installed, empty)
```

---

## 4. Investigation Timeline

### Day 1-2 (May 13-14): zkemkeeper COM SDK
**Mental process:** Start with ZKTeco's official SDK. If their own SDK can't read data, something is fundamentally wrong.

**Scripts written:** 14 test scripts using `win32com.client.Dispatch("zkemkeeper.ZKEM.1")`

| Test | Method | Result |
|------|--------|--------|
| TCP connect | `Connect_Net("192.168.1.201", 4370)` | **WORKS** |
| Device IP | `GetDeviceIP(1)` | **WORKS** — 192.168.1.201 |
| Device MAC | `GetDeviceMAC(1)` | **WORKS** — 00:17:61:11:9A:86 |
| Device time | `GetDeviceTime(1)` | **WORKS** |
| Firmware | `GetFirmwareVersion(1)` | **WORKS** — AC Ver 5.2.5 |
| Product code | `GetProductCode(1)` | **WORKS** — ACP-260 |
| Serial | `GetSerialNumber(1)` | **WORKS** — BRI3225160081 |
| Beep | `Beep(150)` | FAILED |
| Read users | `ReadAllUserID`, `SSR_GetAllUserInfo`, etc. | FAILED — all return False |
| Read logs | `ReadGeneralLogData`, + 8 more methods | FAILED — all return False |
| Write user | `SSR_SetUserInfo`, etc. | FAILED |
| Enroll FP | `StartEnrollEx` | FAILED |
| Delete user | `SSR_DeleteEnrollData` | FAILED |
| Events | `RegEvent` + `OnAttTransaction` | FAILED — no events |
| Log count | `GetDeviceStatus(1, 2)` | Returns 1027, never changes on scan |
| RTLog | `ReadRTLog` | Returns True but no extractable data |

**Conclusion:** The ACP-260 responds to basic device-info commands but ALL data operations fail. The 1,027 "logs" are old door events from 2024, not fingerprint scans.

### Day 2 (May 14): ZKAccess Database
**Mental process:** Maybe ZKAccess already has the data synced. Check the database.

| Table | Rows | Content |
|-------|------|---------|
| USERINFO | 0 | Empty |
| CHECKINOUT | 0 | Empty |
| TEMPLATE | 0 | Empty |
| acc_monitor_log | 9 | Old door events from March 2024 |
| Machines | 1 | ACP-260 device config (144 columns) |
| acc_reader | 4 | 4 reader configs |
| acc_door | 2 | 2 door configs |

**Conclusion:** ZKAccess was installed but never used. "Download Logs" from UI kept the database empty.

### Day 3 (May 17): pyzatt Raw Protocol
**Mental process:** The COM SDK is a black box. Try a pure Python library that implements the raw ZK protocol. If the protocol itself gets responses, we bypass the DLL.

**Scripts:** test_pyzatt_connect.py, test_pyzatt_data.py, test_pyzatt_realtime.py

**Result:** TCP connects to 192.168.1.201:4370, but the device **completely ignores all ZK protocol packets**. No response to connect command (timeout after 5 seconds).

**Raw socket confirmation:**
```
TCP connected to 192.168.1.201:4370
Sent ZK connect (5050827d...): TIMED OUT
```

**Conclusion:** The device accepts TCP connections but doesn't speak the standard ZK standalone protocol.

### Day 4 (May 17): Last Resort Tests
**Mental process:** Read the zk-protocol spec cover to cover. Find ANY untried approach.

**Script:** test_pyzatt_last_resort.py — three tests:

| Test | Result |
|------|--------|
| UDP on 4370 | TIMED OUT — no response |
| TCP commands without connect handshake | TIMED OUT — no response |
| Port scan | Only 4370 and **23** open |

**Surprise finding:** Port 23 (Telnet) is OPEN.

### Day 4 (May 17): Telnet Discovery
**Mental process:** Telnet is open! This is a Linux shell. If we get in, we can access the filesystem, databases, configuration.

**Result:** Connected to port 23, received:
```
Welcome to Linux (ZEM560) for MIPS
Kernel 2.6.24 Treckle on an MIPS
ZEM560 login:
```

**This changes everything.** The device is a full Linux computer. But the password is unknown.

### Day 4-5 (May 17-19): Telnet Brute Force
**Mental process:** ZKTeco devices have known default passwords. Try all of them.

**Scripts:** test_telnet.py, test_telnet_bruteforce.py, test_telnet_zkaccess_creds.py

**Credentials tried:** 32+ combinations including root/sola, root/zksoftware, admin/admin, the ZKAccess user credentials (ayub@24/ay305408), device serial, MAC address, etc.

**Result:** ALL returned "Login incorrect". The Telnet password was changed from factory defaults by whoever set up the system.

### Day 5 (May 19): ZKAccess Password Search
**Mental process:** Maybe the communication password is stored in ZKAccess config files or the Access.mdb database.

**Script:** test_zkaccess_imports.py

**Searched:**
- All .ini, .cfg, .xml config files in ZKAccess directory — only language translations, no actual passwords
- Access.mdb Machines table — 144 columns, no password/comm_key stored
- Windows Registry — no ZKTeco keys found

**Key database findings:**
```
device_name = ACP-260
max_finger_count = 10
BiometricType = 000000000
comm_type = 3
door_count = 2
reader_count = 4
```

**Conclusion:** Communication password is not set. The Telnet/Linux password is separate and unknown.

### Day 5 (May 19): C3 Protocol Attempt
**Mental process:** Major breakthrough from research — the ACP-260 is actually a C3-260/InBio-260 board. We've been using the WRONG protocol (ZK standalone). The C3 panel protocol is completely different.

**Script:** test_c3_protocol.py, test_c3_library.py

**C3 Protocol format:**
- Header: 0xAA, Version: 0x01, Footer: 0x55
- CRC-16 checksum
- Commands: Connect(0x01), GetParams(0x04), GetData(0x08), RealtimeLog(0x0B), etc.

**Result:** ALL C3 protocol commands got NO RESPONSE. Same as ZK standalone protocol via raw sockets.

**Also tried:** zkaccess-c3 Python library (installed but import fails), session connect (0x76), device discovery (0x14), realtime log KV (0x79) — all no response.

---

## 5. What We Learned

### Confirmed Facts
1. The ACP-260 is **same hardware as InBio-260/C3-260** (mainboard: C3-260-MAIN, ZEM560 MIPS Linux)
2. It runs **Linux 2.6.24** and has a **Telnet server** on port 23
3. The zkemkeeper COM DLL is the **ONLY thing** that gets responses from the device
4. ALL raw socket protocols (ZK standalone, C3 panel, UDP) get zero responses
5. The device has 1,027 old door events from 2024 but no fingerprint/user data
6. No communication password is set
7. The Telnet password was changed from factory defaults

### Unknown / Unresolved
1. **Why do raw sockets fail but the COM DLL works?** — The DLL and raw sockets both target 192.168.1.201:4370 over TCP. The DLL gets responses, raw sockets don't. Possible explanations:
   - The DLL uses a proprietary protocol variant not documented in open-source specs
   - The DLL sets specific Windows socket options that the embedded device requires
   - The DLL does an undocumented handshake before the standard protocol
   - The device firmware has a bug that only responds to the DLL's specific implementation
   - Only Wireshark packet capture could resolve this

2. **Are the readers FR1200 (RS-485) or generic Wiegand?** — The TS1022 Pro manual says FR1200 (RS-485, sends templates to controller), but we haven't physically verified. If they're FR1200, the controller SHOULD have fingerprint templates and matching capability — but all data operations fail.

3. **What's the Telnet password?** — Changed from defaults, not stored in ZKAccess.

4. **Can the COM DLL trigger door unlock?** — We tested device info commands but never tested `ACUnlock()`. This is the critical untested operation.

---

## 6. The Mystery: Why Raw Sockets Fail But DLL Works

This is the central unresolved puzzle. Both approaches target the same IP:port:

```
zkemkeeper DLL  → 192.168.1.201:4370 → RESPONSE ✓
Python socket   → 192.168.1.201:4370 → NO RESPONSE ✗
```

**Hypotheses (most to least likely):**

1. **Proprietary protocol variant:** The zkemkeeper DLL is ZKTeco's compiled binary. It may use protocol extensions, different checksums, or additional handshake bytes that aren't documented in the open-source protocol specs we referenced (zk-protocol, pyzatt, zkaccess-c3).

2. **Windows socket behavior:** The DLL might set specific TCP options (TCP_NODELAY, SO_KEEPALIVE, specific buffer sizes, selective ACK) that the embedded Linux on the ZEM560 requires before responding. The device firmware might be sensitive to TCP handshake parameters.

3. **Multi-step handshake:** The DLL might send an initial "wakeup" or "identification" packet before the standard protocol exchange. Our scripts only send the documented protocol packets.

4. **Firmware-level filtering:** The ZEM560 firmware might have a connection whitelist or rate limiter that only responds to connections matching the DLL's exact TCP fingerprint.

**How to resolve:** Install Wireshark on the entrance PC, run a zkemkeeper COM test that connects, and capture the actual TCP traffic. This would show exactly what bytes the DLL sends and receives.

---

## 7. Key Discovery: Device Architecture

The biggest finding came from reading the TS1022 Pro documentation:

```
ACTUAL ARCHITECTURE (according to TS1022 Pro specs):

FR1200 Reader ──RS-485──► ACP-260 (C3-260/InBio-260 board)
(captures fingerprint)     (stores templates, does matching,
                            controls gate relay, has TCP/IP)
                               │
                               └──TCP/IP──► Network (192.168.1.201)

WHAT WE INITIALLY ASSUMED:

Wiegand Reader ──Wiegand──► ACP-260
(matches internally)        (dumb relay, no data)
                               │
                               └──TCP/IP──► Network
```

The TS1022 Pro is supposed to use FR1200 readers connected via RS-485 that send raw fingerprint templates to the controller for matching. The controller is supposed to store templates and logs. But ALL data operations fail, suggesting either:
- The readers are actually Wiegand (not FR1200)
- The firmware is a stripped-down ACP-260 version that disabled data features
- The RS-485 reader connection isn't properly configured

---

## 8. Re-engineering Plan

### The Insight

We don't need the gate hardware to do fingerprint matching or user management. We just need it to:
1. **Open the gate** when we tell it to
2. **Stay closed** when we tell it to

Everything else (fingerprint matching, membership checking, attendance logging) happens in **our Django app**.

### Architecture

```
                            ENTRANCE PC
                         ┌──────────────────────┐
                         │                      │
  Person scans     ZK4500│    Python Script      │zkemkeeper
  finger on     ────────►│    (bridge)           │COM DLL
  USB scanner            │    1. Capture FP      │
                         │    2. POST to Django  │
                         │    3. If approved:    │──────┐
                         │       ACUnlock()      │      │
                         │    4. Log check-in    │      │
                         └──────────────────────┘      │
                              │                        │
                              │ HTTP                   │ TCP
                              ▼                        ▼
                         ┌──────────┐          ┌──────────────┐
                         │  Django  │          │   ACP-260    │
                         │  Backend │          │  Controller  │
                         │          │          │ 192.168.1.201│
                         │ - Users  │          │              │
                         │ - FP     │          │  UNLOCK →    │──► Gate opens
                         │   templates│        │  relay fires │
                         │ - Members│          └──────────────┘
                         │ - Logs   │
                         └──────────┘
```

### Flow

1. Person walks up to the entrance PC
2. They scan their finger on the ZK4500 USB scanner
3. Python bridge captures the fingerprint template
4. Bridge sends template to Django via HTTP
5. Django matches template against stored templates (1:N match)
6. Django checks: is this member's subscription active?
7. **If ACTIVE:** Django returns "approved" → bridge calls `ACUnlock()` via COM DLL → gate opens → check-in logged
8. **If EXPIRED:** Django returns "denied" → show "Membership expired" on screen → gate stays closed

### What Already Exists (No Rebuilding Needed)

- **Django models:** GymMember, MembershipPass, CheckInLog (migration 0019)
- **Django API:** members CRUD, pass management, check-in/check-out, fingerprint enrollment
- **Frontend:** Gym portal (/gym/login, /gym/checkin, /gym/members)
- **ZK4500 scanner:** Already owned
- **zkemkeeper COM DLL:** Installed and registered, connects to device
- **ACP-260 controller:** Operational, opens gate on relay trigger

### What Needs to Be Built

1. **Python bridge script** (runs on entrance PC):
   - ZK4500 fingerprint capture
   - Template extraction and encoding
   - HTTP POST to Django for matching
   - ACUnlock() call via COM DLL on approval
   - Sound/screen feedback

2. **Django fingerprint matching endpoint**:
   - Receives fingerprint template
   - 1:N match against stored templates
   - Returns user ID + membership status

3. **USB relay (backup)**: If ACUnlock() doesn't work via DLL, a $3 USB relay module connected to the ACP-260's relay input as a fallback.

### Critical Test Needed

**Before building anything**, verify that `ACUnlock()` works through the COM DLL. If the DLL can trigger the gate, the entire plan works with zero hardware purchases.

---

## 9. Scripts Reference

All scripts are in the `bridge-zkemkeeper` GitHub repo:
https://github.com/Alpha-lit/bridge-zkemkeeper

### Working / Informative Scripts
| Script | Purpose | Status |
|--------|---------|--------|
| test_device.py | zkemkeeper COM basic connect + device info | WORKS |
| test_pyzatt_connect.py | pyzatt raw ZK protocol connect | Connects TCP, protocol times out |
| test_pyzatt_last_resort.py | UDP, raw cmds, port scan | Found port 23 open |
| test_telnet.py | Telnet probe to port 23 | Found Linux login prompt |
| test_telnet_bruteforce.py | Credential brute force | All defaults failed |
| test_telnet_zkaccess_creds.py | ZKAccess user credentials attempt | Failed |
| test_zkaccess_imports.py | Config file + database search | No password found |
| test_c3_protocol.py | C3 panel protocol test | No response |
| test_c3_library.py | zkaccess-c3 library + raw C3 | No response |

### Test Results Summary
- **zkemkeeper COM DLL:** ONLY method that gets responses from the device
- **Raw sockets (any protocol):** Device accepts TCP but sends nothing back
- **Telnet:** Login prompt exists, password unknown
- **ZKAccess database:** Empty, no useful data

### Next Script to Run
`test_acunlock.py` — Test if the COM DLL can trigger the gate unlock. This determines if the re-engineering plan works without any hardware purchases.

---

## Mental Process Summary

### Phase 1: "Use the official SDK"
Started with zkemkeeper COM SDK because it's ZKTeco's official tool. Connected successfully, got device info, but ALL data operations failed. This suggested either the device doesn't have data, or the SDK can't access it.

### Phase 2: "Check the database"
Looked at ZKAccess's Access.mdb — completely empty. The system was installed but never used. No users, no logs, no templates.

### Phase 3: "Bypass the SDK, use raw protocol"
Switched to pyzatt (open-source Python library) to implement the raw ZK protocol. TCP connects but device ignores all protocol commands. This was surprising — the device accepts connections but sends nothing back.

### Phase 4: "Exhaust ALL protocol options"
Read the zk-protocol specification cover to cover. Found two untried approaches: UDP and commands without connect handshake. Also discovered port 23 (Telnet) open. All protocol attempts failed. Telnet gave us a Linux login prompt but unknown password.

### Phase 5: "Find the password"
Tried 32+ default credentials, ZKAccess user credentials, device serial, MAC address. Searched ZKAccess config files, database, registry. No password found.

### Phase 6: "Wrong protocol?"
Research revealed the ACP-260 is actually a C3-260/InBio-260 board. We may have been using the wrong protocol (ZK standalone instead of C3 panel). Tried C3 protocol — also no response via raw sockets. But the COM DLL works, suggesting the DLL implements something our raw packets don't.

### Phase 7: "Step back, think differently"
Realized we've been trying to READ data from the gate hardware. But what we actually need is to CONTROL the gate (open/close) from our software. The zkemkeeper DLL CAN connect to the device. If it can also trigger unlock, we just need: ZK4500 scanner → Django matching → DLL unlock → gate opens. No need to read anything from the gate itself.

---

*End of investigation document. Created 2026-05-19.*
