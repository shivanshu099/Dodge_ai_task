import sqlite3

conn = sqlite3.connect("sap_o2c.db")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("Schema Overview:")
for t in tables:
    table_name = t[0]
    cursor.execute(f"PRAGMA table_info('{table_name}')")
    cols = cursor.fetchall()
    print(f"\nTable: {table_name}")
    for c in cols:
        print(f"  - {c[1]}")
    
conn.close()
