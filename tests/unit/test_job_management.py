import unittest
from unittest.mock import MagicMock, patch
import os
import time
from learning.db import LearningDB

class TestJobManagement(unittest.TestCase):
    
    def setUp(self):
        self.test_db_path = "tests/test_jobs.db"
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        self.db = LearningDB(self.test_db_path)
        
        # Create dummy jobs
        for i in range(10):
            payload = {"type": "test", "data": i}
            status = 'pending'
            if i < 3: status = 'running'
            elif i < 6: status = 'paused'
            elif i < 8: status = 'finished'
            else: status = 'failed'
            
            # Use raw SQL to force status (create_job sets pending default)
            self.db.create_job("test_job", f"Job {i}", payload)
            # Fetch ID (it's auto increment, so i+1)
            self.db.update_job_status(f"{i+1}", status)

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_job_counts(self):
        # Verify setup
        jobs = self.db.get_jobs_by_status(['running', 'pending', 'paused', 'finished', 'failed'])
        self.assertEqual(len(jobs), 10)
        
        run = [j for j in jobs if j['status'] == 'running']
        self.assertEqual(len(run), 3)

    def test_concurency_logic_simulation(self):
        # Simulator logic from BackgroundWorker logic
        import concurrent.futures
        
        limit = 3
        active_futures = {'1': 'future_obj', '2': 'future_obj'} # 2 slots taken
        
        current_load = len(active_futures)
        slots = limit - current_load
        self.assertEqual(slots, 1)
        
        # Should pick 1 pending job
        pending_jobs = self.db.get_jobs_by_status(['pending'])
        # pending_jobs are [10, 9] (dummy IDs 9, 10... wait ids are strings)
        # 0,1,2 running. 3,4,5 paused. 6,7 finished. 8,9 failed. 
        # Wait, create_job: 0->pending. update->running.
        # Pending ones? None in my setup?
        # Let's check setUp logic.
        # i: 0,1,2 -> running
        # i: 3,4,5 -> paused
        # i: 6,7 -> finished
        # i: 8,9 -> failed
        # So NO pending jobs!
        
        # Create pending
        self.db.create_job("test_job", "Pending Job", {})
        pending_jobs = self.db.get_jobs_by_status(['pending'])
        self.assertEqual(len(pending_jobs), 1)
        
        if slots > 0 and pending_jobs:
            job_to_run = pending_jobs[-1] # Oldest
            self.assertEqual(job_to_run['target_file'], "Pending Job")

    def test_cleanup_logic(self):
        # Simulate "Stop & Clear All"
        import sqlite3
        conn = sqlite3.connect(self.db.db_path)
        conn.execute("DELETE FROM job_queue WHERE status IN ('pending', 'running', 'paused')")
        conn.commit()
        conn.close()
        
        # Verify remnants
        jobs = self.db.get_jobs_by_status(['running', 'pending', 'paused', 'finished', 'failed'])
        # Should only have finished and failed
        self.assertEqual(len(jobs), 4) # 2 finished, 2 failed
        
        statuses = set(j['status'] for j in jobs)
        self.assertNotIn('running', statuses)
        self.assertNotIn('pending', statuses)
        self.assertNotIn('paused', statuses)
        self.assertIn('finished', statuses)

if __name__ == '__main__':
    unittest.main()
