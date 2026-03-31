import unittest
import sqlite3
import os
import json
from learning.db import LearningDB

class TestDBJobs(unittest.TestCase):

    def setUp(self):
        self.start_db = "assignment_test.db"
        if os.path.exists(self.start_db):
            os.remove(self.start_db)
        self.db = LearningDB(db_path=self.start_db)

    def tearDown(self):
        if os.path.exists(self.start_db):
            try:
                os.remove(self.start_db)
            except:
                pass

    def test_job_lifecycle(self):
        # 1. Create
        payload = {"model": "test-model"}
        job_id = self.db.create_job("test_type", "test_file.txt", payload)
        self.assertIsNotNone(job_id)
        
        # 2. Get
        job = self.db.get_job(job_id)
        self.assertEqual(job['target_file'], "test_file.txt")
        self.assertEqual(job['status'], "pending")
        self.assertEqual(json.loads(job['payload'])['model'], "test-model")
        
        # 3. Update Status
        self.db.update_job_status(job_id, "running")
        job = self.db.get_job(job_id)
        self.assertEqual(job['status'], "running")
        
        # 4. Update Progress
        self.db.update_job_progress(job_id, 5, 100)
        job = self.db.get_job(job_id)
        self.assertEqual(job['current_progress'], 5)
        self.assertEqual(job['total_work'], 100)

    def test_get_jobs_by_status(self):
        self.db.create_job("type1", "f1.txt")
        job2 = self.db.create_job("type2", "f2.txt")
        self.db.update_job_status(job2, "running")
        self.db.create_job("type3", "f3.txt") # pending
        
        # Get pending
        pending = self.db.get_jobs_by_status(['pending'])
        self.assertEqual(len(pending), 2)
        
        # Get running
        running = self.db.get_jobs_by_status(['running'])
        self.assertEqual(len(running), 1)
        self.assertEqual(running[0]['target_file'], "f2.txt")
        
        # Get both
        all_active = self.db.get_jobs_by_status(['pending', 'running'])
        self.assertEqual(len(all_active), 3)
