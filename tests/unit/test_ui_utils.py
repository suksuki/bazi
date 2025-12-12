import unittest
from unittest.mock import MagicMock, patch
import sys

# Mock streamlit and plotly before importing ui.utils
sys.modules['streamlit'] = MagicMock()
sys.modules['plotly'] = MagicMock()
sys.modules['plotly.io'] = MagicMock()

# Now import the module under test
import ui.utils 
# Reload to ensure mocks are used if it was already imported (unlikely here but good practice)
import importlib
importlib.reload(ui.utils)

class TestUIUtils(unittest.TestCase):
    def setUp(self):
        # Reset mock before each test
        # We need to access the mock injected into sys.modules['streamlit']
        # But ui.utils imported 'streamlit as st'.
        # We can perform checks on ui.utils.st
        self.st_mock = ui.utils.st 
        self.st_mock.session_state = {}
        self.st_mock.markdown = MagicMock()

    def test_init_session_state(self):
        # Setup initial state
        self.st_mock.session_state = {'existing_key': 'old_value'}
        
        defaults = {
            'existing_key': 'new_value',
            'new_key': 'default_value'
        }
        
        # Call function
        ui.utils.init_session_state(defaults)
        
        # Verify existing key NOT overwritten
        self.assertEqual(self.st_mock.session_state['existing_key'], 'old_value')
        
        # Verify new key added
        self.assertEqual(self.st_mock.session_state['new_key'], 'default_value')

    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data=".css { color: red; }")
    @patch('os.path.exists')
    def test_load_css(self, mock_exists, mock_open):
        mock_exists.return_value = True
        
        ui.utils.load_css()
        
        # Verify file opened
        mock_open.assert_called()
        
        # Verify markdown called with style tag
        self.st_mock.markdown.assert_called_with('<style>.css { color: red; }</style>', unsafe_allow_html=True)

if __name__ == '__main__':
    unittest.main()
