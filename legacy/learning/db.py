
import sqlite3
import json
import os
import datetime

class LearningDB:
    def __init__(self, db_path="learning/brain.db"):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        folder = os.path.dirname(self.db_path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # 1. Cases Table: Stores real-world profile data
        c.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                chart_data TEXT,  -- JSON: {year:..., month:...}
                ground_truth TEXT, -- JSON: {wealth: 90, career: 80}
                source TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 2. Weights Table: Stores evolution history of parameters
        c.execute("""
            CREATE TABLE IF NOT EXISTS weights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_json TEXT, -- JSON: {san_he_bonus: 100, ...}
                loss_score REAL,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. Rules Table: Stores extracted theory knowledge
        c.execute("""
            CREATE TABLE IF NOT EXISTS rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT,
                rule_json TEXT, -- Full JSON content
                source_book TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(rule_name, source_book) ON CONFLICT REPLACE
            )
        """)

        # 4. Read History Table: Tracks processed books
        c.execute("""
            CREATE TABLE IF NOT EXISTS read_history (
                file_name TEXT PRIMARY KEY,
                last_read_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'finished'
            )
        """)

        # 5. Job Queue Table: Async Task Management
        c.execute("""
            CREATE TABLE IF NOT EXISTS job_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_type TEXT,        -- e.g. 'theory_mining'
                target_file TEXT,     -- e.g. 'book.txt'
                status TEXT,          -- pending, running, paused, finished, failed
                current_progress INTEGER DEFAULT 0,
                total_work INTEGER DEFAULT 0,
                payload TEXT,         -- JSON args
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 6. Channels Table: Manage YouTube/Video Channels
        c.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                url TEXT UNIQUE,
                platform TEXT, -- YouTube, Bilibili
                last_scanned TIMESTAMP,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()

    def add_case(self, name, chart_data, ground_truth, source="manual"):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Normalize chart data for consistent comparison
        chart_str = json.dumps(chart_data, sort_keys=True)
        gt_str = json.dumps(ground_truth, sort_keys=True)
        
        # 1. Strict Duplicate Check: Same Name AND Same Chart
        c.execute("SELECT id FROM cases WHERE name = ? AND chart_data = ?", (name, chart_str))
        if c.fetchone():
            print(f"Duplicate Case (Name+Chart): {name}. Skipping.")
            conn.close()
            return False

        # 2. Name Collision Check: Same Name but Different Chart
        # We want to keep it, but maybe distinguish the name to avoid UI confusion?
        # User request: "Every Bazi should be saved".
        c.execute("SELECT id FROM cases WHERE name = ?", (name,))
        if c.fetchone():
            # Name collision found. Append Year Pillar or random discriminator to new name?
            # Or just keep the name and rely on user to check details.
            # User suggested "Index" diversification. 
            # Let's try to append the Year Pillar from chart if available
            pk_year = chart_data.get('year', '') or chart_data.get('year_pillar', '')
            if pk_year:
                new_name = f"{name} ({pk_year})"
                # Check if this new name exists too
                c.execute("SELECT id FROM cases WHERE name = ?", (new_name,))
                if not c.fetchone():
                     name = new_name
                else:
                     # Even that exists? add timestamp suffix
                     name = f"{name} ({int(datetime.datetime.now().timestamp())})"
            else:
                 name = f"{name} ({int(datetime.datetime.now().timestamp())})"
            print(f"Name collision resolved: Saving as '{name}'")
            
        c.execute("""
            INSERT INTO cases (name, chart_data, ground_truth, source)
            VALUES (?, ?, ?, ?)
        """, (name, chart_str, gt_str, source))
        
        conn.commit()
        conn.close()
        return True

    def get_all_cases(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM cases")
        rows = c.fetchall()
        
        cases = []
        for r in rows:
            cases.append({
                "id": r["id"],
                "name": r["name"],
                "chart": json.loads(r["chart_data"]),
                "truth": json.loads(r["ground_truth"]),
                "source": r["source"]
            })
        conn.close()
        return cases

    def save_weights(self, config, loss, note=""):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO weights (config_json, loss_score, note)
            VALUES (?, ?, ?)
        """, (json.dumps(config), loss, note))
        conn.commit()
        conn.close()

    def load_best_weights(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        # Get weight with lowest loss
        c.execute("SELECT config_json FROM weights ORDER BY loss_score ASC LIMIT 1")
        row = c.fetchone()
        conn.close()
        
        if row:
            return json.loads(row["config_json"])
        return None

    def get_latest_weights(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT config_json FROM weights ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        
        if row:
            return json.loads(row["config_json"])
        return None

    # --- Knowledge Base Methods ---

    def add_rule(self, rule_data, source_book="Unknown"):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        rule_name = rule_data.get('rule_name', 'Untitled')
        try:
            c.execute("""
                INSERT INTO rules (rule_name, rule_json, source_book)
                VALUES (?, ?, ?)
            """, (rule_name, json.dumps(rule_data), source_book))
            conn.commit()
        except sqlite3.Error as e:
            print(f"DB Error: {e}")
        finally:
            conn.close()

    def get_all_rules(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT id, rule_name, rule_json, source_book FROM rules")
        rows = c.fetchall()
        conn.close()
        
        results = []
        for r in rows:
            data = {}
            try:
                data = json.loads(r["rule_json"])
            except:
                pass
            
            # Merit fields
            data['id'] = r['id']
            if not data.get('rule_name') and r['rule_name']:
                 data['rule_name'] = r['rule_name']
            data['source_book'] = r['source_book']
            results.append(data)
            
        return results

    # --- History Methods ---

    def mark_book_read(self, file_name):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO read_history (file_name, last_read_at)
            VALUES (?, CURRENT_TIMESTAMP)
            ON CONFLICT(file_name) DO UPDATE SET last_read_at=CURRENT_TIMESTAMP
        """, (file_name,))
        conn.commit()
        conn.close()

    def get_read_history(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT file_name FROM read_history")
        rows = c.fetchall()
        conn.close()
        return [r[0] for r in rows]
    
    def is_book_read(self, file_name):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT 1 FROM read_history WHERE file_name = ?", (file_name,))
        exists = c.fetchone() is not None
        conn.close()
        return exists

    def get_history_cases(self):
        """
        Retrieves rules that appear to be Case Studies (containing Bazi chart structures).
        """
        # Retrieve all rules and filter for those that look like cases
        # A Case Study usually contains specific GanZhi data
        all_rules = self.get_all_rules()
        cases = []
        for r in all_rules:
            # Heuristic checks for Bazi Chart Data
            # Note: r is a dict merged from rule_json
            if 'chart' in r or 'year_stem' in r or 'day_master' in r or r.get('type') == 'case':
                cases.append(r)
        return cases

    # --- Job Queue Methods (Async Task System) ---

    def create_job(self, job_type, target_file, payload=None):
        """
        Creates a new async job.
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        if payload is None: payload = {}
        
        c.execute("""
            INSERT INTO job_queue (job_type, target_file, status, current_progress, total_work, payload)
            VALUES (?, ?, 'pending', 0, 0, ?)
        """, (job_type, target_file, json.dumps(payload)))
        job_id = c.lastrowid
        conn.commit()
        conn.close()
        return job_id

    def get_job(self, job_id):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM job_queue WHERE id = ?", (job_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    def get_jobs_by_status(self, statuses, limit=50, offset=0):
        """
        statuses: list of strings, e.g. ['pending', 'running']
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        placeholders = ','.join('?' * len(statuses))
        query = f"SELECT * FROM job_queue WHERE status IN ({placeholders}) ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params = statuses + [limit, offset]
        
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_job_counts(self):
        """
        Returns a dict of counts per status, e.g. {'running': 5, 'pending': 100}
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT status, COUNT(*) FROM job_queue GROUP BY status")
        rows = c.fetchall()
        conn.close()
        return {r[0]: r[1] for r in rows}

    def update_job_status(self, job_id, status):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE job_queue SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (status, job_id))
        conn.commit()
        conn.close()

    # --- Feedback Loop Methods (Ground Truth) ---

    def create_feedback_table(self):
        # Helper to ensure table exists (called in _init_db usually, but safe to call here)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                year INTEGER,
                aspect TEXT,        -- Career, Wealth, etc.
                actual_score INTEGER, -- 0-100
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def add_feedback(self, year, aspect, score, note=""):
        self.create_feedback_table() # Ensure exists
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT INTO feedback (year, aspect, actual_score, note)
            VALUES (?, ?, ?, ?)
        """, (year, aspect, score, note))
        conn.commit()
        conn.close()
        
    def get_all_feedback(self):
        self.create_feedback_table()
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM feedback ORDER BY year ASC")
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # --- Job Queue Methods (Async Task System) ---
    # ... (Rest of Job Queue Methods)
    
    def update_job_progress(self, job_id, current, total):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            UPDATE job_queue 
            SET current_progress = ?, total_work = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE id = ?
        """, (current, total, job_id))
        conn.commit()
        conn.close()

    # --- Channel Management Methods ---

    def add_channel(self, name, url, platform="YouTube", note=""):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Check existence to potentially update Name
        c.execute("SELECT name FROM channels WHERE url = ?", (url,))
        row = c.fetchone()
        
        if row:
            # Update name if new name is better (not a URL) and current might be a URL
            current_name = row[0]
            # Simple heuristic: if new name is not a URL, update it.
            if name and "http" not in name and name != current_name:
                c.execute("UPDATE channels SET name = ? WHERE url = ?", (name, url))
                conn.commit()
            
            conn.close()
            return False
            
        try:
            c.execute("""
                INSERT INTO channels (name, url, platform, note)
                VALUES (?, ?, ?, ?)
            """, (name, url, platform, note))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
             try: conn.close()
             except: pass

    def get_all_channels(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM channels ORDER BY created_at DESC")
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def update_channel_last_scanned(self, url):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            UPDATE channels 
            SET last_scanned = CURRENT_TIMESTAMP 
            WHERE url = ?
        """, (url,))
        conn.commit()
        conn.close()

    def delete_channel(self, url):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM channels WHERE url = ?", (url,))
        conn.commit()
        conn.close()
    
    # --- Batch Job Operations ---
    
    def batch_update_status(self, job_ids, new_status):
        """
        批量更新多个任务的状态
        job_ids: list of integers
        new_status: string, e.g. 'paused', 'pending', 'deleted'
        """
        if not job_ids:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        placeholders = ','.join('?' * len(job_ids))
        query = f"UPDATE job_queue SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id IN ({placeholders})"
        params = [new_status] + job_ids
        c.execute(query, params)
        count = c.rowcount
        conn.commit()
        conn.close()
        return count
    
    def batch_delete_jobs(self, job_ids):
        """
        批量删除任务（设置为deleted状态）
        job_ids: list of integers
        """
        return self.batch_update_status(job_ids, 'deleted')

    def deduplicate_jobs(self):
        """
        Identify and remove duplicate jobs.
        Rule: Same job_type and target_file/URL.
        Keep: The one with highest progress, or latest created_at if same progress.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # 1. Get all active jobs
        c.execute("SELECT * FROM job_queue WHERE status != 'deleted'")
        rows = c.fetchall()
        
        jobs = [dict(r) for r in rows]
        
        # 2. Group by signature
        # Signature = video:url OR book:filename
        groups = {}
        for j in jobs:
            sig = f"{j['job_type']}:{j['target_file']}"
            try:
                p = json.loads(j['payload'])
                if 'url' in p:
                    sig = f"{j['job_type']}:{p['url']}"
            except:
                pass
            
            if sig not in groups:
                groups[sig] = []
            groups[sig].append(j)
            
        # 3. Find duplicates
        ids_to_delete = []
        for sig, group in groups.items():
            if len(group) > 1:
                # Sort by status priority (finished > running > paused > pending > failed), then progress, then created_at
                # Actually, simple heuristic: Sort by progress desc, then created_at desc
                # We want to KEEP the first one
                group.sort(key=lambda x: (x['current_progress'], x['created_at']), reverse=True)
                
                # Keep active running one if exists?
                # If we have a running one, keep it.
                running = next((g for g in group if g['status'] == 'running'), None)
                if running:
                    # If there's a running job, keep it. Delete others.
                    for j in group:
                        if j['id'] != running['id']:
                            ids_to_delete.append(j['id'])
                else:
                    # Keep the top one (highest progress/newest)
                    for j in group[1:]:
                        ids_to_delete.append(j['id'])
                        
        conn.close()
        
        # 4. Delete
        if ids_to_delete:
            return self.batch_delete_jobs(ids_to_delete)
        return 0

    
    def delete_completed_jobs(self):
        """
        删除所有已完成的任务
        """
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE job_queue SET status = 'deleted' WHERE status = 'finished'")
        count = c.rowcount
        conn.commit()
        conn.close()
        return count
    
    def get_all_jobs(self, include_deleted=False):
        """
        获取所有任务
        include_deleted: 是否包含已删除的任务
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        if include_deleted:
            c.execute("SELECT * FROM job_queue ORDER BY created_at DESC")
        else:
            c.execute("SELECT * FROM job_queue WHERE status != 'deleted' ORDER BY created_at DESC")
        
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]
