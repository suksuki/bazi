import sys
import os
import pytest

# Add project root to sys.path so we can import 'core', 'learning', etc.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def mock_chart_standard():
    """
    Returns a standard, balanced Bazi chart for testing.
    Example: Jia Mu born in Spring.
    """
    return {
        "year": {"stem": "甲", "branch": "子", "hidden_stems": ["癸"]},
        "month": {"stem": "丙", "branch": "寅", "hidden_stems": ["甲", "丙", "戊"]},
        "day": {"stem": "甲", "branch": "辰", "hidden_stems": ["戊", "乙", "癸"]},
        "hour": {"stem": "丁", "branch": "卯", "hidden_stems": ["乙"]}
    }
