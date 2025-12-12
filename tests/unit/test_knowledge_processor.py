import unittest
from unittest.mock import MagicMock, patch
import json
from learning.knowledge_processor import KnowledgeProcessor

class TestKnowledgeProcessor(unittest.TestCase):
    
    def setUp(self):
        # Mock DB
        self.mock_db_patch = patch('learning.knowledge_processor.LearningDB')
        self.MockDB = self.mock_db_patch.start()
        self.mock_db_instance = self.MockDB.return_value
        
        # Mock TheoryMiner
        self.mock_miner_patch = patch('learning.knowledge_processor.TheoryMiner')
        self.MockMiner = self.mock_miner_patch.start()
        self.mock_miner_instance = self.MockMiner.return_value
        
        # Mock Ollama Client
        self.mock_client_patch = patch('learning.knowledge_processor.ollama.Client')
        self.MockClient = self.mock_client_patch.start()
        self.mock_client_instance = self.MockClient.return_value
        
        self.kp = KnowledgeProcessor()

    def tearDown(self):
        self.mock_db_patch.stop()
        self.mock_miner_patch.stop()
        self.mock_client_patch.stop()

    def test_classify_text_theory(self):
        self.mock_client_instance.generate.return_value = {'response': 'THEORY'}
        res = self.kp._classify_text("Some text")
        self.assertEqual(res, "PROBABLY_THEORY")

    def test_classify_text_case(self):
        self.mock_client_instance.generate.return_value = {'response': 'CASE'}
        res = self.kp._classify_text("Some case text")
        self.assertEqual(res, "PROBABLY_CASE")
        
    def test_classify_text_mixed(self):
        self.mock_client_instance.generate.return_value = {'response': 'MIXED'}
        res = self.kp._classify_text("Mixed content")
        self.assertEqual(res, "MIXED")

    def test_extract_case_data_success(self):
        # Mock LLM response for case extraction
        case_json = {
            "profile": {
                "name": "Test Case",
                "gender": "Male",
                "birth_year": 1990,
                "birth_month": 1,
                "birth_day": 1,
                "birth_hour": 12,
                "birth_minute": 0,
                "birth_city": "TestCity"
            },
            "life_events": [{"year": 2020, "description": "Rich"}],
            "quality_score": 85,
            "valid_for_validation": True
        }
        self.mock_client_instance.generate.return_value = {'response': json.dumps(case_json)}
        
        # Patch the CaseExtractor in the service layer where it's imported
        with patch('service.extractor.CaseExtractor') as mock_extractor_class:
            mock_extractor = MagicMock()
            mock_extractor.extract.return_value = case_json
            mock_extractor_class.return_value = mock_extractor
            
            data = self.kp._extract_case_data("Some case text")
            self.assertEqual(data['profile']['name'], "Test Case")

    def test_process_chunk_case(self):
        # Setup mocks
        self.kp._classify_text = MagicMock(return_value="PROBABLY_CASE")
        self.kp._extract_case_data = MagicMock(return_value={"name": "Case 1"})
        
        # Run
        res = self.kp.process_content_chunk("text", "source")
        
        # Verify
        self.assertEqual(res['type'], "PROBABLY_CASE")
        self.assertIn("Case: Case 1", res['extracted'])
        self.mock_db_instance.add_case.assert_called_once()

    def test_process_chunk_theory(self):
        # Setup mocks
        self.kp._classify_text = MagicMock(return_value="PROBABLY_THEORY")
        self.mock_miner_instance.extract_rules.return_value = [{"rule_name": "Rule 1"}]
        
        # Run
        res = self.kp.process_content_chunk("text", "source")
        
        # Verify
        self.assertEqual(res['type'], "PROBABLY_THEORY")
        self.assertIn("Rules: 1", res['extracted'])
        self.mock_db_instance.add_rule.assert_called_once()

    def test_process_chunk_mixed(self):
        # Setup mocks
        self.kp._classify_text = MagicMock(return_value="MIXED")
        self.kp._extract_case_data = MagicMock(return_value={"name": "Mixed Case"})
        self.mock_miner_instance.extract_rules.return_value = [{"rule_name": "Mixed Rule"}]
        
        # Run
        res = self.kp.process_content_chunk("text", "source")
        
        # Verify
        self.assertEqual(res['type'], "MIXED")
        # Should call both add_case and add_rule
        self.mock_db_instance.add_case.assert_called_once()
        self.mock_db_instance.add_rule.assert_called_once()
        self.assertIn("Case: Mixed Case", res['extracted'])
        self.assertIn("Rules: 1", res['extracted'])

if __name__ == '__main__':
    unittest.main()
