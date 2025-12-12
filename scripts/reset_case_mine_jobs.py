
import sqlite3
import os

DB_PATH = "learning/brain.db"

def reset_jobs():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check count first
    c.execute("SELECT COUNT(*) FROM job_queue WHERE job_type='case_mine' AND status='finished'")
    count = c.fetchone()[0]
    
    if count == 0:
        print("No finished 'case_mine' jobs found to reset.")
        conn.close()
        return

    print(f"Found {count} finished Case Mining jobs that may have missed Theory Rules.")
    confirm = input(f"Do you want to reset them to PENDING to re-scan for Rules? (y/n): ")
    
    if confirm.lower() == 'y':
        c.execute("""
            UPDATE job_queue 
            SET status='pending', current_progress=0, total_work=0 
            WHERE job_type='case_mine' AND status='finished'
        """)
        conn.commit()
        print(f"✅ Successfully reset {count} jobs. Restart the app (run_bazi_wsl.sh) to start processing.")
    else:
        print("Operation cancelled.")
    
    conn.close()

if __name__ == "__main__":
    reset_jobs()
