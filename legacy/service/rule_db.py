#!/usr/bin/env python3
"""
Rule Database Module (SQLite)
Project Crimson Vein - Storage Layer for Theoretical Knowledge

Schema:
1. rules (id, category, content_raw, logic_json, source, confidence, created_at)
"""

import sqlite3
import json
import os

DB_PATH = "data/rules.db"

class RuleDatabase:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initialize database schema"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = self._get_conn()
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,       -- e.g. "Pattern", "Interaction", "Seasonal"
            content_raw TEXT,    -- The original text snippet
            logic_json TEXT,     -- Structured triggering logic
            source TEXT,
            confidence REAL DEFAULT 0.5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()

    def insert_rule(self, rule_data):
        """Insert a parsed rule"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            INSERT INTO rules (category, content_raw, logic_json, source)
            VALUES (?, ?, ?, ?)
            ''', (
                rule_data.get('category', 'General'),
                rule_data['content_raw'],
                json.dumps(rule_data.get('logic', {}), ensure_ascii=False),
                rule_data.get('source', 'Unknown')
            ))
            conn.commit()
            print(f"✅ [RuleDB] Saved rule: {rule_data['content_raw'][:20]}...")
        except Exception as e:
            print(f"❌ [RuleDB] Error: {e}")
        finally:
            conn.close()

if __name__ == "__main__":
    db = RuleDatabase()
    print("Rule Database Initialized.")
