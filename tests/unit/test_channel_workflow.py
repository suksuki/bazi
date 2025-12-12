import unittest
from unittest.mock import MagicMock, patch
import json
import os
from learning.db import LearningDB

class TestChannelWorkflow(unittest.TestCase):
    
    def setUp(self):
        # Use an in-memory DB or temporary file DB for testing
        self.test_db_path = "tests/test_brain.db"
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        self.db = LearningDB(self.test_db_path)

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_add_channel(self):
        # Test adding a channel
        url = "https://www.youtube.com/@TestChannel"
        name = "Test Channel"
        result = self.db.add_channel(name, url, "YouTube")
        self.assertTrue(result)
        
        # Verify it exists
        channels = self.db.get_all_channels()
        self.assertEqual(len(channels), 1)
        self.assertEqual(channels[0]['name'], name)
        
        # Test duplicate
        result_dupe = self.db.add_channel(name, url, "YouTube")
        self.assertFalse(result_dupe)

    @patch('learning.video_downloader.VideoDownloader')
    @patch('learning.video_miner.VideoMiner')
    def test_scan_and_queue(self, MockVideoMiner, MockVideoDownloader):
        # Setup Mocks
        mock_dl = MockVideoDownloader.return_value
        mock_vm = MockVideoMiner.return_value
        
        # Mock Channel Videos
        mock_videos = [
            {'url': 'https://youtu.be/vid1', 'title': 'Video 1'},
            {'url': 'https://youtu.be/vid2', 'title': 'Video 2'},
        ]
        mock_dl.get_channel_info.return_value = mock_videos
        
        # Mock History (vid1 is done)
        mock_vm.get_history.return_value = {'vid1'}
        mock_vm.get_video_id.side_effect = lambda x: x.split('/')[-1]
        
        # 1. Add Channel
        self.db.add_channel("Test", "http://channel", "YouTube")
        
        # 2. Simulate Scan Logic (as done in UI)
        # Fetch status
        channels = self.db.get_all_channels()
        ch = channels[0]
        
        # Simulating UI Button Press -> Get Info
        vids = mock_dl.get_channel_info(ch['url'])
        history = mock_vm.get_history()
        
        processed_videos = []
        new_videos = []
        
        for v in vids:
            v_id = mock_vm.get_video_id(v['url'])
            if v_id in history:
                processed_videos.append(v)
            else:
                new_videos.append(v)
                
        self.assertEqual(len(processed_videos), 1) 
        self.assertEqual(processed_videos[0]['title'], 'Video 1')
        self.assertEqual(len(new_videos), 1)
        self.assertEqual(new_videos[0]['title'], 'Video 2')
        
        # 3. Simulate "Queue Selected" (Selecting only the new one)
        for v in new_videos:
            payload = {"type": "video", "url": v['url'], "title": v['title']}
            self.db.create_job("video_learn", target_file=v['title'], payload=payload)
            
        # 4. Verify Job Queue
        jobs = self.db.get_jobs_by_status(['pending'])
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]['target_file'], 'Video 2')
        
        # 5. Verify Update Last Scanned
        # (Wait a tiny bit or just allow it, SQLite timestamp is second precision usually)
        self.db.update_channel_last_scanned(ch['url'])
        
        updated_ch = self.db.get_all_channels()[0]
        self.assertIsNotNone(updated_ch['last_scanned'])

if __name__ == '__main__':
    unittest.main()
