import unittest
from unittest.mock import MagicMock, patch
from learning.video_downloader import VideoDownloader

class TestVideoLogic(unittest.TestCase):
    
    @patch('learning.video_downloader.yt_dlp.YoutubeDL')
    def test_get_channel_info_with_cc(self, MockYDL):
        # Setup
        dl = VideoDownloader()
        mock_ydl_instance = MockYDL.return_value
        mock_ydl_instance.__enter__.return_value = mock_ydl_instance
        
        # Mock extract_info response
        mock_resp = {
            'channel': 'Test Channel',
            'entries': [
                {
                    'id': 'vid1',
                    'title': 'Video No CC',
                    'url': 'https://www.youtube.com/watch?v=vid1',
                    'ie_key': 'Youtube' 
                },
                {
                    'id': 'vid2',
                    'title': 'Video With CC',
                    'url': 'https://www.youtube.com/watch?v=vid2',
                    'subtitles': {'en': []}, # Mock presence
                    'ie_key': 'Youtube'
                },
                {
                    'id': 'vid3',
                    'title': 'Video Auto Cap',
                    'url': 'https://www.youtube.com/watch?v=vid3',
                    'automatic_captions': {'en': []},
                    'ie_key': 'Youtube'
                }
            ]
        }
        mock_ydl_instance.extract_info.return_value = mock_resp
        
        # Execute
        videos, title = dl.get_channel_info("http://channel")
        
        # Verify
        self.assertEqual(len(videos), 3)
        
        # Video 1: No CC tag
        v1 = next(v for v in videos if v['id'] == 'vid1')
        self.assertNotIn("💬", v1['title'])
        
        # Video 2: Has CC tag
        v2 = next(v for v in videos if v['id'] == 'vid2')
        self.assertIn("💬", v2['title'])
        
        # Video 3: Has CC tag (Auto Caps)
        v3 = next(v for v in videos if v['id'] == 'vid3')
        self.assertIn("💬", v3['title'])

    @patch('learning.video_downloader.yt_dlp.YoutubeDL')
    @patch('learning.video_downloader.os.path.exists')
    @patch('learning.video_downloader.os.listdir')
    @patch('learning.video_downloader.os.remove')
    @patch('learning.video_downloader.VideoDownloader._vtt_to_txt')
    def test_try_download_subs_returns_title(self, MockVttToTxt, MockRemove, MockListDir, MockExists, MockYDL):
        dl = VideoDownloader()
        MockExists.return_value = True 
        MockListDir.return_value = ['vid1.zh-Hans.vtt']
        
        mock_ydl_instance = MockYDL.return_value
        mock_ydl_instance.__enter__.return_value = mock_ydl_instance
        
        mock_info = {
            'id': 'vid1',
            'title': 'Real Video Title',
            'requested_subtitles': {'zh-Hans': {'filepath': '/tmp/sub.vtt'}}
        }
        mock_ydl_instance.extract_info.return_value = mock_info
        
        # Execute
        path, title = dl._try_download_subs("http://vid1")
        
        # Verify
        self.assertEqual(title, "Real Video Title")
        # Path might be None if file check fails in real code, but here we just test logic return
        # Actually _try_download_subs has check `if os.path.exists`.
        # We might need to mock os.path.exists or just check that it TRIES to return title.
        
