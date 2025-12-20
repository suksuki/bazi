
from learning.db import LearningDB
import json
import os

db = LearningDB()
try:
    cases = db.get_all_cases()
    print(f"Total entries returned: {len(cases)}")
    if len(cases) > 0:
        first = cases[0]
        print(f"Type of first item: {type(first)}")
        print(f"First item content: {first}")
        
    # Manual SQL count just in case
    import sqlite3
    conn = sqlite3.connect("learning/brain.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM cases")
    print(f"Direct SQL Count: {c.fetchone()[0]}")
    conn.close()

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
