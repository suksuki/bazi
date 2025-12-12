
import pytest
from unittest.mock import MagicMock, patch
import datetime
import sys

# Mock streamlit before importing the module
sys.modules['streamlit'] = MagicMock()
import streamlit as st

# Mock other external dependencies if needed
sys.modules['plotly.graph_objects'] = MagicMock()

# Import the module to test
from ui.pages.prediction_dashboard import render_prediction_dashboard

def test_render_prediction_dashboard_smoke():
    """
    Smoke test to verify render_prediction_dashboard runs without basic NameErrors/SyntaxErrors.
    We mock st.session_state and other st calls.
    """
    # Setup Session State
    st.session_state = {
        'input_name': 'TestUser',
        'input_gender': '男',
        'input_date': datetime.date(1990, 1, 1),
        'input_time': 12,
        'input_enable_solar_time': False,
        'ollama_host': 'http://localhost:11434',
        'selected_model_name': 'qwen2.5'
    }

    # Mock st.columns to return list of mocks 
    # (The dashboard uses st.columns(2) or st.columns([1,1]))
    def mock_columns(n):
        count = n if isinstance(n, int) else len(n)
        return [MagicMock() for _ in range(count)]
    st.columns.side_effect = mock_columns
    
    # Mock st.expander to be a context manager
    st.expander.return_value.__enter__.return_value = MagicMock()

    # Mock selectbox/radio/select_slider to return the first option or value
    def mock_selection(label, options, **kwargs):
        if not options: return None
        # If options is list
        if isinstance(options, list):
             return options[0]
        return options
        
    st.selectbox.side_effect = mock_selection
    st.radio.side_effect = mock_selection
    st.select_slider.side_effect = mock_selection
    
    try:
        render_prediction_dashboard()
    except Exception as e:
        pytest.fail(f"Dashboard render failed with: {e}")

