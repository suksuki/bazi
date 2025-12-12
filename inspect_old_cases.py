import sqlite3
import json

DB_PATH = "learning/brain.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

sample = cursor.execute("SELECT name, chart_data, ground_truth FROM cases LIMIT 3").fetchall()

print("=== Old Cases Sample ===")
for name, chart_raw, truth_raw in sample:
    print(f"\nName: {name}")
    print(f"Chart: {chart_raw}")
    print(f"Truth: {truth_raw}")
    
conn.close()
