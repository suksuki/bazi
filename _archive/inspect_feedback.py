import sqlite3

DB_PATH = "learning/brain.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

data = cursor.execute("SELECT * FROM feedback").fetchall()
print(f"Feedback Records: {len(data)}")
for row in data:
    print(row)
    
conn.close()
