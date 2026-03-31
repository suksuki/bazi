import unittest
import os
import json
import sqlite3
from learning.db import LearningDB

class TestLearningDBCore(unittest.TestCase):

    def setUp(self):
        self.test_db_path = "test_core.db"
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        self.db = LearningDB(db_path=self.test_db_path)

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_rule_management(self):
        """Test adding and retrieving rules."""
        rule_data = {"rule_name": "Test Rule", "content": "Water overcomes Fire"}
        self.db.add_rule(rule_data, source_book="Book of Changes")
        
        all_rules = self.db.get_all_rules()
        self.assertEqual(len(all_rules), 1)
        self.assertEqual(all_rules[0]['rule_name'], "Test Rule")
        self.assertEqual(all_rules[0]['source_book'], "Book of Changes")

    def test_get_history_cases(self):
        """Test retrieving historical cases (rules with chart data)."""
        # 1. Add a normal rule
        self.db.add_rule({"rule_name": "Theory 1", "type": "theory"}, "Book 1")
        
        # 2. Add a Case Study (Simulated)
        case_data = {
            "rule_name": "Emperor Qianlong", 
            "type": "case",
            "chart": {"year": "Geng Wu"},
            "description": "A wealthy fate."
        }
        self.db.add_rule(case_data, "History Records")
        
        # 3. Add ambiguous case (detected by heuristic keys)
        heuristic_case = {
            "rule_name": "Ambiguous Fateman",
            "year_stem": "Jia", # Logic detects 'year_stem'
            "desc": "Test"
        }
        self.db.add_rule(heuristic_case, "Notes")
        
        # Fetch
        cases = self.db.get_history_cases()
        
        # Expect 2 cases (Explicit type='case' AND Heuristic 'year_stem')
        self.assertEqual(len(cases), 2)
        names = [c['rule_name'] for c in cases]
        self.assertIn("Emperor Qianlong", names)
        self.assertIn("Ambiguous Fateman", names)
        self.assertNotIn("Theory 1", names)

    def test_read_history(self):
        """Test marking books as read."""
        self.assertFalse(self.db.is_book_read("test_book.txt"))
        
        self.db.mark_book_read("test_book.txt")
        
        self.assertTrue(self.db.is_book_read("test_book.txt"))
        
        # Verify persistence (list)
        history = self.db.get_read_history()
        self.assertIn("test_book.txt", history)

    def test_channel_management(self):
        """Test adding and updating channels."""
        # Add new
        is_new = self.db.add_channel("Bazi TV", "http://youtube.com/bazitv")
        self.assertTrue(is_new)
        
        # Add duplicate (Update)
        is_new_again = self.db.add_channel("Bazi TV Renamed", "http://youtube.com/bazitv")
        self.assertFalse(is_new_again) # Should be update, not new
        
        # Verify Update
        channels = self.db.get_all_channels()
        self.assertEqual(len(channels), 1)
        self.assertEqual(channels[0]['name'], "Bazi TV Renamed")
