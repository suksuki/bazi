import unittest
from unittest.mock import MagicMock, patch
import json
from learning.theory_miner import TheoryMiner

class TestCaseMining(unittest.TestCase):
    
    def setUp(self):
        # Mock Ollama Client
        self.mock_client_patch = patch('learning.theory_miner.ollama.Client')
        self.MockClient = self.mock_client_patch.start()
        self.mock_client_instance = self.MockClient.return_value
        
        # Mock DB (Patched at source because it is imported locally in __init__)
        self.mock_db_patch = patch('learning.db.LearningDB')
        self.MockDB = self.mock_db_patch.start()
        
        self.miner = TheoryMiner()

    def tearDown(self):
        self.mock_client_patch.stop()
        self.mock_db_patch.stop()

    def test_mine_cases_success(self):
        # 1. Simulate LLM response
        fake_response_content = """
        Here is the JSON:
        ```json
        [
            {
                "name": "Generated Case",
                "gender": "Female",
                "chart": {
                    "year": {"stem": "甲", "branch": "子"}
                },
                "truth": {"wealth": 90}
            }
        ]
        ```
        """
        self.mock_client_instance.chat.return_value = {
            'message': {'content': fake_response_content}
        }
        
        # 2. Call method
        result = self.miner.mine_cases_from_text("Some text about a rich woman born in JiaZi year.")
        
        # 3. Assertions
        self.assertEqual(len(result), 1)
        case = result[0]
        self.assertEqual(case['name'], "Generated Case")
        self.assertEqual(case['gender'], "Female")
        self.assertEqual(case['truth']['wealth'], 90)
        self.assertEqual(case['chart']['year']['stem'], "甲")

    def test_mine_cases_empty(self):
        self.mock_client_instance.chat.return_value = {
            'message': {'content': "No cases found in this text."}
        }
        result = self.miner.mine_cases_from_text("Just theory.")
        self.assertEqual(result, [])
        
    def test_mine_cases_malformed_json(self):
        # JSON missing closing bracket
        self.mock_client_instance.chat.return_value = {
            'message': {'content': "[ {'name': 'Broken' "}
        }
        result = self.miner.mine_cases_from_text("Broken text")
        self.assertEqual(result, [])

if __name__ == '__main__':
    unittest.main()
