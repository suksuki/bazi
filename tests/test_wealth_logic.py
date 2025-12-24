import unittest
import sys
import os

# Ensure core is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.meaning import MeaningEngine

class TestWealthLogic(unittest.TestCase):
    def test_wealth_logic_ledger(self):
        # 1. Mock Flux Data
        # Simulate: DM=Wood, Fire(Tool), Metal(7K), Earth(Wealth)
        
        flux_data = {
            'particle_states': [
                {'id': 'day_stem', 'char': '甲', 'type': 'stem', 'amp': 40.0},
                {'id': 'month_branch', 'char': '申', 'type': 'branch', 'amp': 80.0},
                {'id': 'year_stem', 'char': '丁', 'type': 'stem', 'amp': 30.0},
                {'id': 'hour_branch', 'char': '丑', 'type': 'branch', 'amp': 60.0},
                {'id': 'month_stem', 'char': '乙', 'type': 'stem', 'amp': 20.0},
            ],
            'log': [],
            'spectrum': {}
        }
        
        chart = { 'day': {'stem': '甲'} }
        engine = MeaningEngine(chart, flux_data)
        
        self.assertEqual(engine.god_map['day_stem'], 'BiJian')
        self.assertEqual(engine.god_map['month_branch'], 'QiSha')
        self.assertEqual(engine.god_map['year_stem'], 'ShangGuan')
        self.assertEqual(engine.god_map['hour_branch'], 'ZhengCai')
        self.assertEqual(engine.god_map['month_stem'], 'JieCai')
        
        report = engine.analyze_wealth_logic()
        self.assertIn('ledger', report)
        self.assertIn('path_info', report)
        self.assertIn('conclusion', report)
        
        ledger = report['ledger']
        self.assertGreater(len(ledger), 0)
        
        for entry in ledger:
            self.assertIn('role', entry)
            self.assertIn('god', entry)
            self.assertIn('label', entry)
            self.assertIn('value_str', entry)
            self.assertIn('color', entry)
            self.assertIn('desc', entry)
        
        print("Logic Trace Test Passed!")

if __name__ == "__main__":
    unittest.main()
