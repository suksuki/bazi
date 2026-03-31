#!/usr/bin/env python3
"""
Case Database Module (SQLite)
Project Crimson Vein - Storage Layer

Schema:
1. cases (id, name, gender, birth_iso, birth_city, rodden_rating, quality_tier, created_at)
2. life_events (id, case_id, year, age, event_type, description, verified)
"""

import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "data/cases.db"

class CaseDatabase:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initialize database schema if not exists, and migrate if outdated."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # Table: cases
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS cases (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            gender TEXT,
            birth_year INTEGER,
            birth_month INTEGER,
            birth_day INTEGER,
            birth_hour INTEGER,
            birth_minute INTEGER,
            birth_city TEXT,
            rodden_rating TEXT,
            quality_tier TEXT,
            quality_score INTEGER DEFAULT 0,
            valid_for_validation BOOLEAN DEFAULT 0,
            source_url TEXT,
            tags TEXT,  -- JSON string
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # --- Migration Logic: Check for missing columns in existing table ---
        # This handles the case where DB exists but lacks new V6.0 fields
        cursor.execute("PRAGMA table_info(cases)")
        columns = [info[1] for info in cursor.fetchall()]
        
        if 'quality_score' not in columns:
            print("🔧 [DB Migration] Adding column 'quality_score' to table 'cases'")
            try:
                cursor.execute("ALTER TABLE cases ADD COLUMN quality_score INTEGER DEFAULT 0")
            except sqlite3.OperationalError: 
                pass # Already exists (rare race condition)

        if 'valid_for_validation' not in columns:
            print("🔧 [DB Migration] Adding column 'valid_for_validation' to table 'cases'")
            try:
                cursor.execute("ALTER TABLE cases ADD COLUMN valid_for_validation BOOLEAN DEFAULT 0")
            except sqlite3.OperationalError:
                pass

        # Table: life_events
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS life_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT,
            year INTEGER,
            age INTEGER,
            event_type TEXT,
            description TEXT,
            verified BOOLEAN DEFAULT 0,
            FOREIGN KEY(case_id) REFERENCES cases(id)
        )
        ''')
        
        conn.commit()
        conn.close()

    def insert_case(self, case_json):
        """
        Insert a complete case (profile + events) from JSON dict.
        Updates if case_id exists.
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        
        try:
            # 1. Insert Case Profile
            profile = case_json['profile']
            tags_str = json.dumps(case_json.get('tags', []), ensure_ascii=False)
            
            cursor.execute('''
            INSERT OR REPLACE INTO cases (
                id, name, gender, 
                birth_year, birth_month, birth_day, birth_hour, birth_minute,
                birth_city, rodden_rating, quality_tier, quality_score, valid_for_validation, 
                source_url, tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                case_json['id'],
                profile['name'],
                profile['gender'],
                profile['birth_year'],
                profile['birth_month'],
                profile['birth_day'],
                profile.get('birth_hour'),
                profile.get('birth_minute'),
                profile.get('birth_city'),
                profile.get('rodden_rating'),
                case_json.get('quality_tier', 'B'),
                case_json.get('quality_score', 0),
                case_json.get('valid_for_validation', False),
                case_json.get('source_url'),
                tags_str
            ))
            
            # 2. Insert Life Events
            # First, clear existing events for this case (to support updates)
            cursor.execute('DELETE FROM life_events WHERE case_id = ?', (case_json['id'],))
            
            for event in case_json.get('life_events', []):
                cursor.execute('''
                INSERT INTO life_events (
                    case_id, year, age, event_type, description, verified
                ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    case_json['id'],
                    event['year'],
                    event.get('age'),
                    event['event_type'],
                    event['description'],
                    event.get('verified', False)
                ))
                
            conn.commit()
            print(f"✅ [DB] Case inserted/updated: {profile['name']} ({case_json['id']})")
            
        except sqlite3.Error as e:
            print(f"❌ [DB] Error inserting case: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_case(self, case_id):
        """Retrieve a full case with events"""
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        case = cursor.execute('SELECT * FROM cases WHERE id = ?', (case_id,)).fetchone()
        if not case:
            return None
            
        events = cursor.execute('SELECT * FROM life_events WHERE case_id = ? ORDER BY year ASC', (case_id,)).fetchall()
        
        result = dict(case)
        result['tags'] = json.loads(result['tags']) if result['tags'] else []
        result['life_events'] = [dict(e) for e in events]
        
        conn.close()
        return result

    def get_all_cases_meta(self):
        """Get minimal metadata for all cases (for list view)"""
        conn = self._get_conn()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        rows = cursor.execute('SELECT id, name, birth_year, quality_tier, rodden_rating FROM cases').fetchall()
        conn.close()
        return [dict(r) for r in rows]

# Migration Utility: Load raw JSONs into DB
def migrate_json_to_db():
    db = CaseDatabase()
    raw_dir = "data/cases/raw"
    
    if not os.path.exists(raw_dir):
        print("No raw directory found.")
        return

    for filename in os.listdir(raw_dir):
        if filename.endswith(".json"):
            path = os.path.join(raw_dir, filename)
            try:
                with open(path, 'r') as f:
                    case_data = json.load(f)
                db.insert_case(case_data)
            except Exception as e:
                print(f"Failed to migrate {filename}: {e}")

if __name__ == "__main__":
    # Test run: initialize and migrate
    print("🔄 Initializing CaseDatabase and migrating raw JSONs...")
    migrate_json_to_db()
