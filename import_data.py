import os
import json
import sqlite3

def convert_value(val):
    if isinstance(val, (dict, list, bool)):
        return json.dumps(val)
    return val

def main():
    base_dir = "sap-order-to-cash-dataset/sap-o2c-data"
    db_path = "sap_o2c.db"
    
    if not os.path.exists(base_dir):
        print(f"Directory {base_dir} does not exist.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for folder in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, folder)
        if not os.path.isdir(folder_path):
            continue
            
        table_name = folder.strip()
        print(f"Processing table: {table_name}")
        
        # 1. First pass: Collect all possible columns from JSONL files
        columns = set()
        files = [f for f in os.listdir(folder_path) if f.endswith(".jsonl")]
        if not files:
            continue
            
        for file in files:
            with open(os.path.join(folder_path, file), "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip(): continue
                    try:
                        data = json.loads(line)
                        columns.update(data.keys())
                    except json.JSONDecodeError:
                        pass
                        
        if not columns:
            continue
            
        columns = list(columns)
        
        # 2. Create table (dropping it first if it exists to refresh data)
        cols_def = ", ".join([f'"{col}" TEXT' for col in columns])
        create_stmt = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({cols_def})'
        cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
        cursor.execute(create_stmt)
        
        # 3. Second pass: Insert data
        insert_stmt = f'INSERT INTO "{table_name}" ({", ".join([f"{col}" for col in columns])}) VALUES ({", ".join(["?" for _ in columns])})'
        
        for file in files:
            with open(os.path.join(folder_path, file), "r", encoding="utf-8") as f:
                batch = []
                for line in f:
                    if not line.strip(): continue
                    try:
                        data = json.loads(line)
                        row = [convert_value(data.get(col)) for col in columns]
                        batch.append(row)
                    except json.JSONDecodeError:
                        continue
                        
                    if len(batch) >= 2000:
                        cursor.executemany(insert_stmt, batch)
                        batch = []
                if batch:
                    cursor.executemany(insert_stmt, batch)
                    
        conn.commit()

    conn.close()
    print(f"Data successfully imported into {db_path}")

if __name__ == "__main__":
    main()
