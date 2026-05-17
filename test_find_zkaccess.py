# Find ZKAccess database on this PC
# ZKAccess 3.5 stores data in a local database (usually .mdb or .accdb)

import os
import glob

print("Searching for ZKAccess database files...\n")

# Common ZKAccess install locations
search_paths = [
    r"C:\Program Files (x86)\ZKAccess3.5",
    r"C:\Program Files\ZKAccess3.5",
    r"C:\Program Files (x86)\ZKAccess",
    r"C:\Program Files\ZKAccess",
    r"C:\ProgramData\ZKAccess3.5",
    r"C:\ProgramData\ZKAccess",
    r"C:\Users\hp\AppData\Local\ZKAccess3.5",
    r"C:\Users\hp\AppData\Roaming\ZKAccess3.5",
    r"D:\ZKAccess3.5",
]

# Database file patterns
db_patterns = ["*.mdb", "*.accdb", "*.db", "*.sqlite", "*.sqlite3", "*.fdb"]

found_files = []

for path in search_paths:
    if os.path.exists(path):
        print(f"Found directory: {path}")
        # List all files
        for root, dirs, files in os.walk(path):
            for f in files:
                full = os.path.join(root, f)
                size = os.path.getsize(full)
                found_files.append((full, size))
                if any(f.endswith(ext[1:]) for ext in db_patterns):
                    print(f"  >>> DATABASE: {full} ({size:,} bytes)")
    # else:
    #     print(f"  Not found: {path}")

# Also search common locations for any .mdb files
print("\nSearching for .mdb files in common locations...")
for search_dir in ["C:\\", "D:\\", r"C:\ProgramData", r"C:\Users\hp"]:
    try:
        for f in glob.glob(os.path.join(search_dir, "**", "*.mdb"), recursive=True):
            if "ZKAccess" in f or "zk" in f.lower() or "ZK" in f:
                size = os.path.getsize(f)
                print(f"  >>> {f} ({size:,} bytes)")
                found_files.append((f, size))
        for f in glob.glob(os.path.join(search_dir, "**", "*.accdb"), recursive=True):
            if "ZKAccess" in f or "zk" in f.lower():
                size = os.path.getsize(f)
                print(f"  >>> {f} ({size:,} bytes)")
                found_files.append((f, size))
    except:
        pass

# Also check for ZKAccess in installed programs
print("\nChecking if ZKAccess is installed...")
import subprocess
try:
    result = subprocess.run(
        ["reg", "query", r"HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall", "/s", "/f", "ZKAccess"],
        capture_output=True, text=True, timeout=10
    )
    if "ZKAccess" in result.stdout:
        # Extract install location
        for line in result.stdout.split("\n"):
            if "InstallLocation" in line or "DisplayName" in line or "DisplayVersion" in line:
                print(f"  {line.strip()}")
    else:
        print("  ZKAccess not found in registry (32-bit)")
except Exception as e:
    print(f"  Registry check error: {e}")

try:
    result = subprocess.run(
        ["reg", "query", r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall", "/s", "/f", "ZKAccess"],
        capture_output=True, text=True, timeout=10
    )
    if "ZKAccess" in result.stdout:
        for line in result.stdout.split("\n"):
            if "InstallLocation" in line or "DisplayName" in line or "DisplayVersion" in line:
                print(f"  {line.strip()}")
except:
    pass

# Also try to find the running ZKAccess process path
print("\nChecking for ZKAccess process...")
try:
    result = subprocess.run(["tasklist", "/v"], capture_output=True, text=True, timeout=10)
    for line in result.stdout.split("\n"):
        if "ZKAccess" in line.lower() or "zk" in line.lower():
            print(f"  {line.strip()}")
except:
    pass

print()
if not found_files:
    print("No database files found yet.")
    print("\nPlease tell me:")
    print("  1. Where is ZKAccess 3.5 installed on this PC?")
    print("  2. When you open ZKAccess, can you see the list of members/users?")
    print("  3. Can you export data from ZKAccess (File > Export)?")
else:
    print(f"\nFound {len(found_files)} files total.")
