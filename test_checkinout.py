# Quick check: does ZKAccess capture attendance in CHECKINOUT?
# 1. Open ZKAccess and make sure it's connected
# 2. Have someone scan finger at gate
# 3. Run this script

import pyodbc

DB = r"C:\Program Files (x86)\ZKTeco\ZKAccess3.5\Access.mdb"
conn = pyodbc.connect(f"Driver={{Microsoft Access Driver (*.mdb)}};DBQ={DB};")
cur = conn.cursor()

# CHECKINOUT table
print("CHECKINOUT table:")
cur.execute("SELECT COUNT(*) FROM [CHECKINOUT]")
count = cur.fetchone()[0]
print(f"  Total rows: {count}")

if count > 0:
    cur.execute("SELECT TOP 20 * FROM [CHECKINOUT] ORDER BY LOGID DESC")
    cols = [d[0] for d in cur.description]
    print(f"  Columns: {cols}")
    for row in cur.fetchall():
        print(f"  {dict(zip(cols, row))}")
else:
    print("  Empty - ZKAccess has not pulled any attendance logs yet.")

# Also check monitor log for recent events
print("\nacc_monitor_log (last 5):")
cur.execute("SELECT TOP 5 * FROM [acc_monitor_log] ORDER BY id DESC")
cols = [d[0] for d in cur.description]
for row in cur.fetchall():
    d = dict(zip(cols, row))
    print(f"  time={d.get('time')}, pin={d.get('pin')}, event_type={d.get('event_type')}, verified={d.get('verified')}, point={d.get('event_point_name')}")

conn.close()
print("\nDone.")
