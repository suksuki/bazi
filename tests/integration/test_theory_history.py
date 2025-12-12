import pytest
from unittest.mock import MagicMock, patch
from learning.theory_miner import TheoryMiner

@pytest.fixture
def mock_db():
    with patch('learning.db.LearningDB') as MockDB:
        db_instance = MockDB.return_value
        # Setup default behaviors
        db_instance.get_read_history.return_value = []
        db_instance.is_book_read.return_value = False
        yield db_instance

def test_mark_book_as_read(mock_db):
    """Verify that mark_book_as_read delegates to DB."""
    miner = TheoryMiner()
    
    # 1. Initial State provided by mock
    assert miner.get_read_history() == []
    
    # 2. Mark as read
    miner.mark_book_as_read("test_book.txt")
    
    # 3. Verify DB call
    mock_db.mark_book_read.assert_called_with("test_book.txt")

def test_is_book_read(mock_db):
    """Verify is_book_read delegates to DB."""
    miner = TheoryMiner()
    mock_db.is_book_read.return_value = True
    
    assert miner.is_book_read("already_read.txt") == True
    mock_db.is_book_read.assert_called_with("already_read.txt")
