import sqlite3
import os

DB_PATH = "learning/brain.db"

def explore_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all tables
    tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
    
    print(f"=== Tables in {DB_PATH} ===")
    for table_name in tables:
        name = table_name[0]
        count = cursor.execute(f"SELECT count(*) FROM {name}").fetchone()[0]
        print(f"\nTable: {name} ({count} rows)")
        
        # Get schema
        schema = cursor.execute(f"PRAGMA table_info({name})").fetchall()
        columns = [col[1] for col in schema]
        print(f"  Columns: {columns}")

    conn.close()

if __name__ == "__main__":
    explore_db()
