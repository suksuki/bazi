import sys
import os
import unittest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular
from core.interaction_service import TreasuryStatus

class TestV3Clash(unittest.TestCase):

    def setUp(self):
        self.engine = QuantumEngine()

    def test_case_a_no_clash(self):
        """
        Case A: No Clash
        Chart: Rat (Day)
        Year: Dragon (2024)
        Expected: List is empty (No Treasury Opening)
        """
        print("\nTesting Case A: Rat (Day) vs Dragon (Year) - No Clash")
        birth_chart = {
            'year_pillar': '甲子',
            'month_pillar': '乙丑',
            'day_pillar': '丙子', # Rat
            'hour_pillar': '丁卯'
        }
        year_branch = '辰' # Dragon
        
        openings = self.engine.analyze_year_interaction(birth_chart, year_branch)
        
        self.assertEqual(len(openings), 0, f"Expected 0 openings, got {len(openings)}")
        print("✅ Case A Passed: No clash detected.")

    def test_case_b_clash_open(self):
        """
        Case B: Clash Open
        Chart: Dog (Day) (Fire Tomb)
        Year: Dragon (2024)
        Expected: is_open=True, pillar='day', action='clash'
        """
        print("\nTesting Case B: Dog (Day) vs Dragon (Year) - Clash Open")
        birth_chart = {
            'year_pillar': '甲子',
            'month_pillar': '乙丑',
            'day_pillar': '丙戌', # Dog (Fire Tomb)
            'hour_pillar': '丁卯'
        }
        year_branch = '辰' # Dragon
        
        openings = self.engine.analyze_year_interaction(birth_chart, year_branch)
        
        self.assertGreater(len(openings), 0, "Expected at least 1 opening")
        
        # Check details of the first opening (assuming only one for this simplified case)
        status = openings[0]
        self.assertTrue(status.is_open, "Treasury should be open")
        self.assertEqual(status.pillar_location, 'day', "Should be Day pillar")
        self.assertEqual(status.treasury_element, '戌', "Treasury should be Dog")
        self.assertEqual(status.key_element, '辰', "Key should be Dragon")
        self.assertEqual(status.action, 'clash', "Action should be clash")
        
        print(f"✅ Case B Passed: Treasury Opened! {status}")

    def test_multiple_openings(self):
        """
        Bonus Test: Multiple Openings
        Chart: Dog (Year), Dog (Day)
        Year: Dragon
        Expected: 2 openings
        """
        print("\nTesting Multiple Openings: Dog (Year) & Dog (Day)")
        birth_chart = {
            'year_pillar': '甲戌', # Dog
            'month_pillar': '乙丑',
            'day_pillar': '丙戌', # Dog
            'hour_pillar': '丁卯'
        }
        year_branch = '辰'
        
        openings = self.engine.analyze_year_interaction(birth_chart, year_branch)
        self.assertEqual(len(openings), 2, f"Expected 2 openings, got {len(openings)}")
        print("✅ Bonus Test Passed: Multiple openings detected.")

if __name__ == '__main__':
    unittest.main()
