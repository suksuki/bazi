import unittest
from unittest.mock import MagicMock, patch, mock_open
import json
from core.scheduler import BackgroundWorker

class TestSchedulerLogic(unittest.TestCase):
    
    def setUp(self):
        self.mock_db_patch = patch('core.scheduler.LearningDB')
        self.MockDB = self.mock_db_patch.start()
        self.db = self.MockDB.return_value
        
        # Stop event
        self.worker = BackgroundWorker()
        # Mock DB methods used in init
        
    def tearDown(self):
        self.mock_db_patch.stop()

    @patch('learning.knowledge_processor.KnowledgeProcessor')
    @patch('os.path.exists', return_value=True)
    def test_video_job_knowledge_processing(self, mock_exists, MockKP):
        # Pre-load modules to avoid side-effects of open() mock on imports
        try:
            import learning.video_downloader
            import learning.media_miner
        except Exception:
            pass

        # Setup Job
        job = {
            'id': 'job_123',
            'status': 'running',
            'target_file': 'video.mp4',
            'current_progress': 2, # Ready for Mining
            'total_work': 3,
            'payload': json.dumps({'type': 'video', 'url': 'http://video.com', 'title': 'Test'})
        }
        
        # Mock DB get_job
        self.db.get_job.return_value = job
        
        # Mock KP instance
        kp_instance = MockKP.return_value
        kp_instance.process_content_chunk.return_value = {'type': 'MIXED', 'extracted': ['Case', 'Rule']}
        
        # Mock VideoDownloader to avoid network/disk calls
        with patch('learning.video_downloader.VideoDownloader') as MockVD:
            vd_instance = MockVD.return_value
            # return file_path, title, duration, is_sub
            vd_instance.download_audio.return_value = ("dummy.mp4", "Test", 100, False)
            
            # Execute with patched open (for reading book content)
            with patch('builtins.open', mock_open(read_data="Dummy content")):
                 self.worker._process_video_job(job, json.loads(job['payload']))
        
        # Verify
        # Should instantiate KP
        MockKP.assert_called_once()
        # Should call process_content_chunk
        kp_instance.process_content_chunk.assert_called()
        # Should update progress to 3
        self.db.update_job_progress.assert_called_with('job_123', 3, 3)
        self.db.update_job_status.assert_called_with('job_123', 'finished')

if __name__ == '__main__':
    unittest.main()
