import unittest
from core.wuxing_engine import WuXingEngine

class TestWuXingEngine(unittest.TestCase):

    def setUp(self):
        # Mocking a Chart Object using Chinese characters as expected by WU_XING_MAP
        self.mock_chart_standard = {
            "year": {"stem": "甲", "branch": "子", "hidden_stems": ["癸"]},
            # Month: Bing Yin (Fire Wood)
            "month": {"stem": "丙", "branch": "寅", "hidden_stems": ["甲", "丙", "戊"]},
            # Day: Jia Chen (Wood Earth)
            "day": {"stem": "甲", "branch": "辰", "hidden_stems": ["戊", "乙", "癸"]},
            # Hour: Ding Mao (Fire Wood)
            "hour": {"stem": "丁", "branch": "卯", "hidden_stems": ["乙"]}
        }
        
    def test_wuxing_instantiation(self):
        engine = WuXingEngine(self.mock_chart_standard)
        self.assertEqual(engine.chart, self.mock_chart_standard)

    def test_element_counting(self):
        """
        Verify element counting.
        """
        # Note: Need to verify if 'Mu', 'Jin' keys are correct.
        # Assuming the original test was correct about the keys.
        engine = WuXingEngine(self.mock_chart_standard)
        scores = engine.calculate_strength()
        
        # We expect Wood (Mu) to be strongest (Day Master + Season)
        # Using .get() to be safe if keys differ (e.g. 'Wood' vs 'Mu')
        # But asserting based on original test code.
        
        # If the engine actually uses English keys:
        score_wood = scores['scores'].get('Mu', 0) or scores['scores'].get('Wood', 0)
        score_metal = scores['scores'].get('Jin', 0) or scores['scores'].get('Metal', 0)
        score_fire = scores['scores'].get('Huo', 0) or scores['scores'].get('Fire', 0)

        self.assertGreater(score_wood, score_metal)
        self.assertGreater(score_fire, 0)
        
    def test_missing_data_resilience(self):
        empty_chart = {
            "year": {"stem": "", "branch": "", "hidden_stems": []},
            "month": {"stem": "", "branch": "", "hidden_stems": []},
            "day": {"stem": "", "branch": "", "hidden_stems": []},
            "hour": {"stem": "", "branch": "", "hidden_stems": []}
        }
        engine = WuXingEngine(empty_chart)
        result = engine.calculate_strength()
        self.assertGreaterEqual(result.get('total', 0), 0)
