# Read ZKAccess setup tables to understand device configuration
# This will tell us about the reader, doors, and device settings

import os
import pyodbc

DB_PATH = r"C:\Program Files (x86)\ZKTeco\ZKAccess3.5\Access.mdb"
conn = pyodbc.connect(f"Driver={{Microsoft Access Driver (*.mdb)}};DBQ={DB_PATH};")
cursor = conn.cursor()

def read_table(table_name, limit=50):
    print(f"\n{'=' * 60}")
    print(f"TABLE: {table_name}")
    print(f"{'=' * 60}")
    try:
        cursor.execute(f"SELECT * FROM [{table_name}]")
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        print(f"Columns: {cols}")
        print(f"Rows: {len(rows)}\n")
        for row in rows[:limit]:
            d = dict(zip(cols, row))
            # Truncate long values
            for k, v in d.items():
                if isinstance(v, str) and len(v) > 100:
                    d[k] = v[:100] + "..."
                if isinstance(v, bytes) and len(v) > 50:
                    d[k] = f"<blob {len(v)} bytes>"
            print(f"  {d}")
        if len(rows) > limit:
            print(f"  ... and {len(rows) - limit} more")
    except Exception as e:
        print(f"  Error: {e}")

# Device configuration
read_table("Machines")

# Reader configuration
read_table("acc_reader")

# Door configuration
read_table("acc_door")

# Monitor log (recent events)
read_table("acc_monitor_log")

# Auxiliary
read_table("acc_auxiliary")

conn.close()
print("\nDone.")
