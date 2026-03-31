import pytest
import time
from unittest.mock import MagicMock, patch, ANY
from core.scheduler import BackgroundWorker

@pytest.fixture
def mock_worker_dependencies():
    with patch('core.scheduler.LearningDB') as MockDB, \
         patch('core.scheduler.TheoryMiner') as MockMiner, \
         patch('builtins.open', new_callable=MagicMock) as mock_file:
        
        # Setup DB Mock
        db_instance = MockDB.return_value
        # Setup Miner Mock
        miner_instance = MockMiner.return_value
        
        yield db_instance, miner_instance, mock_file

def test_worker_process_job(mock_worker_dependencies):
    db_mock, miner_mock, file_mock = mock_worker_dependencies
    
    # Setup Data
    job = {
        'id': 123,
        'job_type': 'test',
        'target_file': 'book.txt',
        'status': 'pending',
        'current_progress': 0,
        'payload': '{"model": "test-model"}'
    }
    
    # Setup Miner return
    # process_book yields dicts
    miner_mock.process_book.return_value = [
        {'chunk_index': 1, 'total_chunks': 2, 'rule': None},
        {'chunk_index': 2, 'total_chunks': 2, 'rule': {'rule_name': 'MyRule'}}
    ]
    
    # Setup File Mock to avoid error
    import os
    with patch('os.path.exists', return_value=True):
        worker = BackgroundWorker()
        worker.db = db_mock # Inject mock explicitly if needed, but patch handles init
        worker.miner = miner_mock
        
        worker.process_job(job)
        
        # Verify Interactions
        
        # 1. Status updated to running
        db_mock.update_job_status.assert_any_call(123, 'running')
        
        # 2. Miner called
        miner_mock.process_book.assert_called_once()
        
        # 3. Progress updated (called for each chunk)
        db_mock.update_job_progress.assert_any_call(123, 1, 2)
        db_mock.update_job_progress.assert_any_call(123, 2, 2)
        
        # 4. Rule added
        db_mock.add_rule.assert_called_with({'rule_name': 'MyRule', 'source_book': 'book.txt'}, source_book='book.txt')
        
        # 5. Finished
        db_mock.update_job_status.assert_called_with(123, 'finished')
        db_mock.mark_book_read.assert_called_with('book.txt')

def test_worker_pause_logic(mock_worker_dependencies):
    db_mock, miner_mock, _ = mock_worker_dependencies
    
    job = {
        'id': 999,
        'job_type': 'test',
        'target_file': 'pause_test.txt',
        'status': 'running',
        'current_progress': 0,
        'payload': '{}'
    }
    
    # Miner yields 3 chunks
    miner_mock.process_book.return_value = [
        {'chunk_index': 1, 'total_chunks': 3},
        {'chunk_index': 2, 'total_chunks': 3},
        {'chunk_index': 3, 'total_chunks': 3}
    ]
    
    # DB behavior: Returns 'paused' status when called inside the loop
    # We need side_effect to return different values on consecutive calls
    # Call 1 (start), Call 2 (chunk 1 check), Call 3 (chunk 2 check)...
    # Let's say it returns 'running' first, then 'paused'
    db_mock.get_job.side_effect = [
        {'status': 'running'}, # check chunk 1
        {'status': 'paused'},  # check chunk 2
        {'status': 'paused'}
    ]
    
    import os
    with patch('os.path.exists', return_value=True):
        worker = BackgroundWorker()
        worker.db = db_mock
        worker.miner = miner_mock
        
        worker.process_job(job)
        
        # Verification
        # It should have processed chunk 1
        db_mock.update_job_progress.assert_any_call(999, 1, 3)
        
        # It should NOT have processed chunk 3 (implied by return)
        # Because chunk 2 check saw 'paused' and returned
        # Note: process_job logic checks "if status == paused: return"
        
        # Should NOT be marked finished
        with pytest.raises(AssertionError):
            db_mock.update_job_status.assert_called_with(999, 'finished')
