# Read ZKAccess database (Access.mdb)
# This has all members, fingerprints, and attendance logs

import os

DB_PATH = r"C:\Program Files (x86)\ZKTeco\ZKAccess3.5\Access.mdb"
print(f"Database: {DB_PATH}")
print(f"Exists: {os.path.exists(DB_PATH)}")
print(f"Size: {os.path.getsize(DB_PATH):,} bytes\n")

# Try connecting with pyodbc
print("Connecting to Access database...")
try:
    import pyodbc
    print("pyodbc available")
except ImportError:
    print("pyodbc not installed. Installing...")
    import subprocess
    subprocess.run([
        r"C:\Users\hp\AppData\Local\Programs\Python\Python312-32\python.exe",
        "-m", "pip", "install", "pyodbc"
    ], timeout=60)
    import pyodbc
    print("pyodbc installed")

# Try different connection strings
conn = None
for driver in [
    "Driver={Microsoft Access Driver (*.mdb, *.accdb)}",
    "Driver={Microsoft Access Driver (*.mdb)}",
    "Driver={Driver do Microsoft Access (*.mdb)}",
]:
    try:
        conn_str = f"{driver};DBQ={DB_PATH};"
        conn = pyodbc.connect(conn_str)
        print(f"Connected with: {driver}")
        break
    except Exception as e:
        print(f"  Failed: {driver} - {e}")

if not conn:
    # Try pypyodbc as fallback
    print("\nTrying pypyodbc...")
    try:
        import pypyodbc
        conn = pypyodbc.connect(f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={DB_PATH};")
        print("Connected with pypyodbc")
    except ImportError:
        print("pypyodbc not installed either. Installing...")
        import subprocess
        subprocess.run([
            r"C:\Users\hp\AppData\Local\Programs\Python\Python312-32\python.exe",
            "-m", "pip", "install", "pypyodbc"
        ], timeout=60)
        import pypyodbc
        conn = pypyodbc.connect(f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={DB_PATH};")
        print("Connected with pypyodbc")

if not conn:
    print("\nCould not connect to database.")
    print("You may need to install Microsoft Access Database Engine 2016 Redistributable (32-bit)")
    print("Download from: https://www.microsoft.com/en-us/download/details.aspx?id=54920")
    print("Choose the 32-bit version (AccessDatabaseEngine.exe /passive)")
    import sys
    sys.exit(1)

cursor = conn.cursor()

# List all tables
print("\n" + "=" * 60)
print("TABLES IN DATABASE")
print("=" * 60)
tables = []
for table_info in cursor.tables(tableType="TABLE"):
    name = table_info.table_name
    tables.append(name)
    print(f"  {name}")

# Read each table's structure and row count
print("\n" + "=" * 60)
print("TABLE DETAILS")
print("=" * 60)
for table in tables:
    try:
        # Get columns
        cols = []
        for col in cursor.columns(table):
            cols.append(f"{col.column_name}({col.type_name})")

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM [{table}]")
        count = cursor.fetchone()[0]

        print(f"\n  [{table}] ({count} rows)")
        if len(cols) <= 15:
            print(f"    Columns: {', '.join(cols)}")
        else:
            print(f"    Columns ({len(cols)}): {', '.join(cols[:15])}...")
    except Exception as e:
        print(f"\n  [{table}] Error: {e}")

# Read USER table (most important)
print("\n" + "=" * 60)
print("USER DATA")
print("=" * 60)
for user_table in ["USER", "USERINFO", "USERS", "User", "UserInfo"]:
    try:
        cursor.execute(f"SELECT * FROM [{user_table}]")
        rows = cursor.fetchall()
        if rows:
            cols = [desc[0] for desc in cursor.description]
            print(f"  Table: {user_table} ({len(rows)} users)")
            print(f"  Columns: {cols}")
            print()
            for i, row in enumerate(rows[:30]):
                print(f"    {dict(zip(cols, row))}")
            if len(rows) > 30:
                print(f"    ... and {len(rows) - 30} more")
            break
    except:
        continue

# Read ATTENDANCE / TRANSACTION log table
print("\n" + "=" * 60)
print("ATTENDANCE / TRANSACTION LOGS")
print("=" * 60)
for log_table in ["TRANSACTION", "ATTLOG", "CHECKINOUT", "Attendance", "ACC_TRANSACTION", "Transaction", "AttLog"]:
    try:
        cursor.execute(f"SELECT * FROM [{log_table}] ORDER BY 1 DESC")
        rows = cursor.fetchall()
        if rows:
            cols = [desc[0] for desc in cursor.description]
            print(f"  Table: {log_table} ({len(rows)} logs)")
            print(f"  Columns: {cols}")
            print()
            for i, row in enumerate(rows[:20]):
                print(f"    {dict(zip(cols, row))}")
            if len(rows) > 20:
                print(f"    ... and {len(rows) - 20} more")
            break
    except:
        continue

conn.close()
print("\nDatabase connection closed.")
