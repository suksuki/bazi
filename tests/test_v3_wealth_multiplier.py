import sys
import os
import unittest

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.quantum_engine import QuantumEngine

class TestV3Champagne(unittest.TestCase):
    def setUp(self):
        self.engine = QuantumEngine()

    def test_bill_gates_scenario(self):
        """
        Simulate a Bill Gates-like scenario (Water DM, Dog Wealth Tomb, Dragon Year).
        V3.5: Also test ethical safety valve (strong vs weak DM).
        """
        print("\n🍾 Testing Champagne Scenario: Water DM, Dog Wealth Tomb, Dragon Year")
        
        # 1. Setup: Water Day Master (Ren), Dog in Day Pillar (Wealth Treasury)
        # Ren Water controls Fire. Dog (Xu) is Fire Tomb -> Wealth Tomb.
        birth_chart_strong = {
            'year_pillar': '乙未', 
            'month_pillar': '丙戌', # Dog is present
            'day_pillar': '壬戌', # Ren Water sitting on Dog (Wealth Tomb)
            'hour_pillar': '辛亥',
            'day_master': '壬',  # Ren (Water)
            'energy_self': 5.0  # Strong DM - can handle wealth
        }
        
        favorable = ['metal', 'water', 'fire']
        unfavorable = ['earth', 'wood']
        
        # 2. Control Year: No Clash
        year_pillar_control = "壬寅"
        result_control = self.engine.calculate_year_score(year_pillar_control, favorable, unfavorable, birth_chart_strong)
        score_control = result_control['score']
        details_control = result_control['details']
        
        print(f"Control Year ({year_pillar_control}): Score = {score_control}")
        print(f"Details: {details_control}")

        # 3. Test Year: Dragon (Chen) -> Clashes with Dog (Xu)
        year_pillar_test = "甲辰" 
        result_test = self.engine.calculate_year_score(year_pillar_test, favorable, unfavorable, birth_chart_strong)
        score_test = result_test['score']
        details_test = result_test['details']
        treasury_icon = result_test.get('treasury_icon')
        
        print(f"Test Year ({year_pillar_test}): Score = {score_test}")
        print(f"Details: {details_test}")
        print(f"Treasury Icon: {treasury_icon}")
        
        # 4. Verification: Strong DM should get 🏆
        self.assertEqual(treasury_icon, "🏆", "Strong DM should get gold trophy")
        bg_msg_found = any("身强胜财" in d for d in details_test)
        self.assertTrue(bg_msg_found, "Should have '身强胜财' message")
        
        print(f"Score Delta: {score_test - score_control}")
        self.assertGreater(score_test, 10.0, "Score should be high due to Wealth Treasury opening")
        print("✅ Champagne Test Passed: Strong DM gets 🏆!")
        
    def test_weak_dm_warning(self):
        """
        V3.5 Sprint 5: Test ethical safety valve for weak Day Master.
        """
        print("\n⚠️ Testing Weak DM Safety Valve")
        
        # Weak Water DM
        birth_chart_weak = {
            'year_pillar': '乙未', 
            'month_pillar': '丙戌',
            'day_pillar': '壬戌',
            'hour_pillar': '辛亥',
            'day_master': '壬',
            'energy_self': 1.5  # Weak DM - can't handle wealth
        }
        
        favorable = ['metal', 'water']
        unfavorable = ['fire', 'earth', 'wood']
        
        year_pillar = "甲辰"  # Clash opens wealth treasury
        result = self.engine.calculate_year_score(year_pillar, favorable, unfavorable, birth_chart_weak)
        
        score = result['score']
        icon = result.get('treasury_icon')
        details = result['details']
        
        print(f"Score: {score}, Icon: {icon}")
        print(f"Details: {details}")
        
        # Verification: Weak DM should get ⚠️
        self.assertEqual(icon, "⚠️", "Weak DM should get warning icon")
        warning_found = any("身弱不胜财" in d for d in details)
        self.assertTrue(warning_found, "Should have '身弱不胜财' warning")
        
        # Score should be negatively affected
        self.assertLess(score, 0, "Weak DM opening wealth treasury should have negative impact")
        print("✅ Safety Valve Test Passed: Weak DM gets ⚠️!")

if __name__ == '__main__':
    unittest.main()
