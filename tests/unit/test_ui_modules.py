import unittest
from unittest.mock import MagicMock, patch
import sys
from datetime import datetime as dt

# Mock modules to avoid importing real core/learning logic and streamlit
sys.modules['streamlit'] = MagicMock()
sys.modules['core.profile_manager'] = MagicMock()
sys.modules['learning.bio_miner'] = MagicMock()
sys.modules['learning.web_hunter'] = MagicMock()
sys.modules['learning.db'] = MagicMock()

# Import module under test
import ui.modules.profile_section as ps
import importlib
importlib.reload(ps)

class TestProfileSectionLogic(unittest.TestCase):
    def setUp(self):
        self.st_mock = ps.st
        self.st_mock.session_state = {}

    def test_sync_profile_to_session(self):
        # Data dictionary simulating a loaded profile from DB/JSON
        loaded_data = {
            'name': 'Test User',
            'gender': 'Female',
            'year': '1995',
            'month': '5',
            'day': '20',
            'hour': '14'
        }
        
        # Access the private function directly
        ps._sync_profile_to_session(loaded_data)
        
        # Verify Session State Updated
        self.assertEqual(self.st_mock.session_state['input_name'], 'Test User')
        self.assertEqual(self.st_mock.session_state['input_gender'], 'Female')
        self.assertEqual(self.st_mock.session_state['input_time'], 14)
        
        # Check Date Object
        expected_date = dt(1995, 5, 20)
        self.assertEqual(self.st_mock.session_state['input_date'], expected_date)

    def test_sync_profile_invalid_date(self):
        # Case where date is invalid
        loaded_data = {
            'name': 'Test User',
            'gender': 'Male',
            'year': 'invalid',
            'month': '5',
            'day': '20',
            'hour': '10'
        }
        
        ps._sync_profile_to_session(loaded_data)
        
        # Verify basic fields
        self.assertEqual(self.st_mock.session_state['input_name'], 'Test User')
        # Date should NOT be set (key not present or raises error caught in except)
        self.assertNotIn('input_date', self.st_mock.session_state)

if __name__ == '__main__':
    unittest.main()
