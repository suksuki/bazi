import json
import os
import sqlite3
from learning.db import LearningDB

def migrate_rules(db):
    rule_path = "data/learned_rules.json"
    if not os.path.exists(rule_path):
        print(f"No rules file found at {rule_path}")
        return
    
    with open(rule_path, 'r', encoding='utf-8') as f:
        try:
            rules = json.load(f)
            print(f"Migrating {len(rules)} rules...")
            for r in rules:
                db.add_rule(r)
            print("Rules migration complete.")
        except json.JSONDecodeError:
            print("Error reading rules JSON.")

def migrate_history(db):
    hist_path = "data/read_history.json"
    if not os.path.exists(hist_path):
        print(f"No history file found at {hist_path}")
        return

    with open(hist_path, 'r', encoding='utf-8') as f:
        try:
            history = json.load(f)
            print(f"Migrating {len(history)} history records...")
            for h in history:
                db.mark_book_read(h)
            print("History migration complete.")
        except json.JSONDecodeError:
            print("Error reading history JSON.")

if __name__ == "__main__":
    db = LearningDB()
    print("Starting migration...")
    migrate_rules(db)
    migrate_history(db)
    print("Migration finished. Initializing DB verification...")
    
    # Verify
    r = db.get_all_rules()
    h = db.get_read_history()
    print(f"DB now has {len(r)} rules and {len(h)} read books.")
