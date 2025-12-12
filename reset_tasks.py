import sqlite3

def reset_tasks():
    db_path = "learning/brain.db"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Update all 'case_mine' jobs that are 'finished' or 'failed' back to 'pending'
    # Also reset progress to 0 to force a full re-run
    query = """
    UPDATE job_queue 
    SET status = 'pending', 
        current_progress = 0, 
        updated_at = CURRENT_TIMESTAMP 
    WHERE job_type = 'case_mine' 
      AND status IN ('finished', 'failed')
    """
    
    c.execute(query)
    count = c.rowcount
    
    conn.commit()
    conn.close()
    
    print(f"✅ 已重置 {count} 个历史任务。它们将使用新的去重规则重新运行。")

if __name__ == "__main__":
    reset_tasks()
