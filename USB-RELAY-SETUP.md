# USB Relay Setup Guide — Gym Gate Control

## What to Buy

### Recommended: KMTronic USB Relay 1-Channel

- **Search:** "KMTronic USB relay 1 channel" on Amazon or AliExpress
- **Price:** ~$8-12
- **Why this one:** Shows up as COM port on Windows, simple serial commands, dry contact relay, well-documented

### Alternative: DSD TECH USB Relay Module

- **Search:** "DSD TECH USB relay" on AliExpress
- **Price:** ~$5-7
- Same approach, different serial commands

### What to Look For (any brand)

| Requirement | Why |
|------------|-----|
| **1 channel** | We only need one relay (one gate control) |
| **Dry contact / SPDT** | Acts as a simple switch, won't send voltage into the turnstile |
| **USB powered** | No external power supply needed |
| **Shows as COM port** | Python can control it via serial (no special drivers on Windows 10/11) |
| **Rated 12V / 2A minimum** | The turnstile control board uses 12V |

### Do NOT Buy

- Relay modules that need Arduino or Raspberry Pi (GPIO controlled, not USB)
- Relay modules that only switch AC mains power
- Relay modules without dry contact output (ones that output 5V on trigger)

---

## Physical Setup

### Tools Needed

- Small flathead screwdriver (for relay terminals)
- USB-A cable long enough to reach from PC to turnstile (~3 meters)
- 2 short wires (20-22 AWG, ~30 cm)

### Step 1: Open the Turnstile

The turnstile has an access panel. Open it to expose the control board inside. You'll see a circuit board with connectors labeled J1 through J9.

### Step 2: Locate J7 Connector

Find the **J7** connector on the turnstile control board. This is the relay input — the same connector where the ACP-260 sends its "open gate" signal. There should already be wires from the ACP-260 connected here.

**DO NOT disconnect the existing ACP-260 wires.** We're adding wires alongside them.

### Step 3: Wire the USB Relay

The USB relay module has 3 screw terminals:

```
USB Relay Module
┌──────────────┐
│  COM   NO  NC│
│   ●    ●   ● │
└──────────────┘
     │    │
     │    └── connect to J7 terminal 2
     └─────── connect to J7 terminal 1
```

1. Strip ~5mm of insulation from each wire end
2. Connect one wire from **COM** to one side of **J7**
3. Connect one wire from **NO** to the other side of **J7**
4. Tighten all screw terminals securely

### Step 4: Connect USB Cable

Run a USB cable from the entrance PC to the USB relay module inside the turnstile. Use a USB extension cable if needed (~3 meters).

### Step 5: Verify COM Port

1. Plug the USB relay into the PC
2. Open **Device Manager** (Win+X → Device Manager)
3. Look under **Ports (COM & LPT)**
4. Note the COM port number (e.g., "COM3", "COM5")
5. You'll need this number for the Python script

---

## How It Works

### Wiring Diagram

```
ENTRANCE PC                              TURNSTILE (inside)
┌─────────────┐                         ┌─────────────────────┐
│             │                         │                     │
│  USB Port   │──USB cable──3m──────────│  USB Relay Module   │
│             │                         │                     │
│             │                         │  COM ───wire──┐     │
│             │                         │  NO  ───wire──┤     │
│             │                         │               │     │
│             │                         │           J7 connector
│             │                         │           ●  ●  ←── existing ACP-260 wires
│             │                         │           ●  ●  ←── new USB relay wires
│             │                         │                     │
│  ZK4500 USB │ (fingerprint scanner)  │     Gate Control    │
│  Scanner    │                         │     Board           │
└─────────────┘                         └─────────────────────┘
```

### Signal Flow

```
Both paths open the same gate:

Path 1 (existing — keep working):
  Reader scans finger → ACP-260 → relay signal → J7 → gate opens

Path 2 (new — our system):
  ZK4500 scans finger → Python → Django verifies → USB relay → J7 → gate opens
```

The USB relay acts as a second switch in parallel. Either the ACP-260 OR the USB relay can trigger the gate. They don't interfere with each other.

### Electrical Explanation

The USB relay has a **dry contact** output. This means when triggered, it simply connects COM to NO — like closing a switch. It doesn't send any voltage of its own. The turnstile's J7 connector provides a small voltage and detects when the circuit is closed (switch is on). This is identical to how the ACP-260's relay output works.

---

## Python Control

### KMTronic Commands

```python
import serial
import time

relay = serial.Serial('COM3', 9600, timeout=1)  # Change COM3 to your port

# Turn ON (open gate)
relay.write(bytes([0xFF, 0x01, 0x01]))

# Wait for gate to open
time.sleep(5)

# Turn OFF (close relay)
relay.write(bytes([0xFF, 0x01, 0x00]))

relay.close()
```

### DSD TECH Commands

```python
# Turn ON
relay.write(bytes([0xA0, 0x01, 0x01, 0xA2]))

# Turn OFF
relay.write(bytes([0xA0, 0x01, 0x00, 0xA1]))
```

---

## Testing

### Test 1: Relay Click
1. Plug in USB relay
2. Find COM port in Device Manager
3. Run test script
4. You should hear a **click** from the relay module
5. LED on the relay should turn on/off

### Test 2: Gate Opens
1. Wire relay to J7 (with turnstile power OFF)
2. Turn turnstile power ON
3. Run test script
4. Gate arm should rotate/release for the relay ON duration

### Test 3: Existing Reader Still Works
1. Scan finger on the existing fingerprint reader
2. Gate should still open normally
3. Our relay wiring did not affect the existing system

---

## Safety Notes

- Always turn off turnstile power before wiring
- The USB relay is dry contact — it cannot damage the turnstile board
- Keep wires away from the motor drive connectors (J2)
- If anything goes wrong, just disconnect the USB relay wires from J7 — the gate works exactly as before
- The USB relay draws power from USB only (~50mA) — no battery or external power needed

---

## Shopping Links (search terms)

- Amazon: "KMTronic USB relay 1 channel dry contact"
- AliExpress: "USB relay module 1 channel COM port dry contact"
- eBay: "USB relay 12V dry contact serial controlled"

Expected delivery: 2-5 days (local), 2-4 weeks (AliExpress)
