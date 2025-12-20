
import os
import sqlite3
import json
from learning.db import LearningDB

def reprocess_video_cases():
    print("🚀 开始批量创建重跑任务...")
    
    db = LearningDB()
    book_dir = "data/books"
    
    # 1. 获取所有视频转录文件
    all_files = [f for f in os.listdir(book_dir) if f.startswith("[Video]") and f.endswith(".txt")]
    print(f"📂 发现 {len(all_files)} 个视频转录文件")
    
    # 2. 获取当前活跃任务，避免重复
    conn = sqlite3.connect(db.db_path)
    c = conn.cursor()
    c.execute("SELECT target_file FROM job_queue WHERE status IN ('pending', 'running', 'paused') AND job_type = 'case_mine'")
    active_files = set(row[0] for row in c.fetchall())
    conn.close()
    
    print(f"🔄 当前已有 {len(active_files)} 个活跃的挖掘任务")
    
    # 3. 批量创建任务
    count = 0
    skipped = 0
    
    for fname in all_files:
        if fname in active_files:
            skipped += 1
            continue
            
        # Create Job
        payload = {
            "type": "case_mine", 
            "filename": fname, 
            "model": "qwen2.5:3b", # Default model, or fetch from config
            "reprocess": True
        }
        db.create_job("case_mine", target_file=fname, payload=payload)
        count += 1
        
        if count % 50 == 0:
            print(f"   ...已入队 {count} 个任务")

    print("-" * 30)
    print(f"✅ 完成！")
    print(f"➕ 新增任务: {count}")
    print(f"⏭️ 跳过已有: {skipped}")
    print(f"📚 建议前往【任务中心】确认为并发数=1，然后静待后台处理。")

if __name__ == "__main__":
    reprocess_video_cases()
