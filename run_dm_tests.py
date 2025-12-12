import unittest
import sys
import os

if __name__ == "__main__":
    # Add project root to path
    sys.path.append(os.getcwd())
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = 'tests/unit'
    suite = loader.discover(start_dir, pattern='test_case_mining.py')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    if result.wasSuccessful():
        print("✅ All Data Mining tests passed!")
        exit(0)
    else:
        print("❌ Some tests failed.")
        exit(1)
