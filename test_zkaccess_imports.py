"""
Two tasks:
1. Find the correct import for zkaccess-c3 library
2. Search ZKAccess config files for the device Telnet password
"""

import importlib
import os
import glob

print("=" * 60)
print("TASK 1: Find zkaccess-c3 import path")
print("=" * 60)

# Try different import paths
import_attempts = [
    "zkaccess",
    "zkaccess.zkaccess",
    "zkaccess.c3",
    "zkaccess_c3",
    "zk_access",
]

for mod_name in import_attempts:
    try:
        mod = importlib.import_module(mod_name)
        print(f"  {mod_name} -> OK")
        print(f"    Contents: {dir(mod)[:20]}")
        # Try to find connection class
        for attr in dir(mod):
            obj = getattr(mod, attr)
            if callable(obj) and not attr.startswith('_'):
                print(f"    {attr}: {type(obj)}")
    except ImportError as e:
        print(f"  {mod_name} -> ImportError: {e}")
    except Exception as e:
        print(f"  {mod_name} -> Error: {e}")

# Check what's actually in the package
try:
    import zkaccess
    pkg_path = os.path.dirname(zkaccess.__file__)
    print(f"\n  Package location: {pkg_path}")
    print(f"  Package files:")
    for root, dirs, files in os.walk(pkg_path):
        for f in files:
            print(f"    {os.path.join(root, f)}")
except Exception as e:
    print(f"  Cannot inspect package: {e}")

print("\n" + "=" * 60)
print("TASK 2: Search ZKAccess for passwords")
print("=" * 60)

# Search ZKAccess installation directory
zk_paths = [
    r"C:\Program Files (x86)\ZKTeco",
    r"C:\Program Files\ZKTeco",
    r"C:\ZKTeco",
]

for zk_path in zk_paths:
    if not os.path.exists(zk_path):
        print(f"  {zk_path} — not found")
        continue

    print(f"\n  Searching {zk_path}...")

    # Find config files
    for root, dirs, files in os.walk(zk_path):
        for f in files:
            fpath = os.path.join(root, f)
            if f.endswith(('.ini', '.cfg', '.config', '.xml', '.json', '.properties')):
                print(f"\n  Config file: {fpath}")
                try:
                    with open(fpath, 'r', errors='replace') as fh:
                        content = fh.read()
                        # Search for password-related lines
                        for line_num, line in enumerate(content.split('\n'), 1):
                            line_lower = line.lower()
                            if any(kw in line_lower for kw in ['password', 'passwd', 'key', 'secret', 'credential', 'token', 'login', 'auth']):
                                print(f"    Line {line_num}: {line.strip()[:150]}")
                except Exception as e:
                    print(f"    Cannot read: {e}")

# Also check the Access.mdb database for password fields
print("\n  --- Checking Access.mdb ---")
mdb_paths = []
for zk_path in zk_paths:
    if os.path.exists(zk_path):
        for root, dirs, files in os.walk(zk_path):
            for f in files:
                if f.lower().endswith('.mdb'):
                    mdb_paths.append(os.path.join(root, f))

for mdb in mdb_paths:
    print(f"\n  Database: {mdb}")
    try:
        import pyodbc
        conn_str = f"DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={mdb}"
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        # List tables
        tables = [table.table_name for table in cursor.tables(tableType='TABLE')]
        print(f"  Tables: {tables}")

        # Check Machines table for password fields
        if 'Machines' in tables:
            cursor.execute("SELECT * FROM Machines")
            cols = [desc[0] for desc in cursor.description]
            print(f"  Machines columns: {cols}")
            for row in cursor.fetchall():
                for i, col in enumerate(cols):
                    val = row[i]
                    if val is not None and val != '' and val != 0:
                        col_lower = col.lower()
                        if any(kw in col_lower for kw in ['password', 'passwd', 'key', 'secret', 'pin', 'comm']):
                            print(f"    {col} = {val}")

        conn.close()
    except ImportError:
        print("  pyodbc not installed, cannot read .mdb")
    except Exception as e:
        print(f"  Error: {e}")

# Check registry for ZKTeco settings
print("\n  --- Checking Windows Registry ---")
try:
    import winreg
    reg_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\ZKTeco"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\ZKTeco"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\ZKAccess"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\ZKAccess"),
    ]
    for hive, path in reg_paths:
        try:
            key = winreg.OpenKey(hive, path)
            i = 0
            while True:
                try:
                    name, value, vtype = winreg.EnumValue(key, i)
                    if any(kw in name.lower() for kw in ['password', 'passwd', 'key', 'serial', 'ip', 'port', 'device']):
                        print(f"  {path}\\{name} = {value}")
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"  Registry {path}: {e}")
except ImportError:
    print("  winreg not available (not Windows?)")

print("\nDone.")
