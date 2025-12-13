import sys
import os
import unittest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.quantum_engine import QuantumEngine

class TestNoneHandling(unittest.TestCase):
    def setUp(self):
        self.engine = QuantumEngine()

    def test_none_day_master(self):
        """
        Test that calculate_year_score handles None day_master gracefully.
        """
        print("\nTesting None day_master handling...")
        
        # Birth chart with None day_master
        birth_chart = {
            'year_pillar': '甲子',
            'month_pillar': '乙丑',
            'day_pillar': '丙戌',
            'hour_pillar': '丁卯',
            'day_master': None  # Explicitly None
        }
        
        favorable = ['metal', 'water']
        unfavorable = ['wood', 'fire']
        year_pillar = "甲辰"
        
        # Should not raise TypeError
        try:
            score, details = self.engine.calculate_year_score(year_pillar, favorable, unfavorable, birth_chart)
            print(f"✅ Score: {score}, Details: {details}")
            # Should not have treasury opening because dm_elem is None
            self.assertNotIn("财库", str(details), "Should not detect wealth treasury with None day_master")
        except TypeError as e:
            self.fail(f"❌ TypeError raised with None day_master: {e}")

    def test_missing_day_master(self):
        """
        Test that calculate_year_score handles missing day_master key gracefully.
        """
        print("\nTesting missing day_master key...")
        
        # Birth chart without day_master key
        birth_chart = {
            'year_pillar': '甲子',
            'month_pillar': '乙丑',
            'day_pillar': '丙戌',
            'hour_pillar': '丁卯'
            # day_master key is missing
        }
        
        favorable = ['metal', 'water']
        unfavorable = ['wood', 'fire']
        year_pillar = "甲辰"
        
        # Should not raise KeyError or TypeError
        try:
            score, details = self.engine.calculate_year_score(year_pillar, favorable, unfavorable, birth_chart)
            print(f"✅ Score: {score}, Details: {details}")
        except (KeyError, TypeError) as e:
            self.fail(f"❌ Exception raised with missing day_master: {e}")

    def test_empty_string_day_master(self):
        """
        Test that calculate_year_score handles empty string day_master.
        """
        print("\nTesting empty string day_master...")
        
        birth_chart = {
            'year_pillar': '甲子',
            'month_pillar': '乙丑',
            'day_pillar': '丙戌',
            'hour_pillar': '丁卯',
            'day_master': ''  # Empty string
        }
        
        favorable = ['metal', 'water']
        unfavorable = ['wood', 'fire']
        year_pillar = "甲辰"
        
        try:
            score, details = self.engine.calculate_year_score(year_pillar, favorable, unfavorable, birth_chart)
            print(f"✅ Score: {score}, Details: {details}")
        except TypeError as e:
            self.fail(f"❌ TypeError raised with empty string day_master: {e}")

if __name__ == '__main__':
    unittest.main()
