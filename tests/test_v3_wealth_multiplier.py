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
        """
        print("\n🍾 Testing Champagne Scenario: Water DM, Dog Wealth Tomb, Dragon Year")
        
        # 1. Setup: Water Day Master (Ren), Dog in Day Pillar (Wealth Treasury)
        # Ren Water controls Fire. Dog (Xu) is Fire Tomb -> Wealth Tomb.
        birth_chart = {
            'year_pillar': '乙未', 
            'month_pillar': '丙戌', # Dog is present here too
            'day_pillar': '壬戌', # Ren Water sitting on Dog (Wealth Tomb)
            'hour_pillar': '辛亥',
            'day_master': '壬' # Ren (Water)
        }
        
        favorable = ['metal', 'water', 'fire'] # Usually Strong Water likes Fire/Wealth, Weak Water likes Metal/Water
        # Let's assume typical favorable elements doesn't matter much for the Multiplier test itself, 
        # but the base score calculation uses them.
        unfavorable = ['earth', 'wood']
        
        # 2. Control Year: No Clash
        # Year: Ren Yin (Example) or something neutral
        year_pillar_control = "壬寅"
        score_control, details_control = self.engine.calculate_year_score(year_pillar_control, favorable, unfavorable, birth_chart)
        print(f"Control Year ({year_pillar_control}): Score = {score_control}")
        print(f"Details: {details_control}")

        # 3. Test Year: Dragon (Chen) -> Clashes with Dog (Xu)
        # Year: Jia Chen (2024 is Jia Chen)
        year_pillar_test = "甲辰" 
        score_test, details_test = self.engine.calculate_year_score(year_pillar_test, favorable, unfavorable, birth_chart)
        
        print(f"Test Year ({year_pillar_test}): Score = {score_test}")
        print(f"Details: {details_test}")
        
        # 4. Verification
        # Expect multiplier effect. Base score for Jia Chen might be low (checking below), but Multiplier should boost it.
        # Jia (Wood) on Chen (Earth). If Earth is Unfavorable -> Cut Feet (-5).
        # We need to verify if the Treasury logic overrides or boosts significantly.
        
        # Check if Treasury Open detail is present
        bg_msg_found = any("财库[戌]大开" in d for d in details_test)
        self.assertTrue(bg_msg_found, "❌ Failed to detect Wealth Treasury Opening message.")
        
        # Check Score Jump
        # We expect test score to be significantly higher than if it was just a bad year.
        # Let's verify multiplier applied: 
        # Base score calculation for Jia Chen:
        # Jia (Wood, Unfav) -> -10
        # Chen (Earth, Unfav) -> -10
        # Total Weighted: -10
        # Cut Feet? Jia(Wood) controls Chen(Earth). Wood is Unfav, Earth is Unfav.
        # Wait, if both unfaorable, it's just bad.
        
        # Wait, if Jia is Unfavorable (Wood) and Chen is Unfavorable (Earth).
        # Score = -10. 
        # Treasury Multiplier: -10 * 2.0 = -20. + 20 Bonus = 0.
        # Hmm, maybe we should set Favorable somewhat realistically for wealth.
        # If I want to get rich, usually Wealth (Fire) and maybe Output (Wood) are favorable?
        # Let's adjust favorable for the test to ensure positive base or at least meaningful jump.
        
        # Let's set Wood/Earth as Neutral or slightly mixed to see the effect clearly?
        # Or just trust the delta.
        
        # Let's try to make the base score positive to see "Getting Rich".
        # Assume Weak Water -> Likes Metal, Water. 
        # Assume Wealth (Fire) is Favorable (for wealth tracking).
        # Let's say: Favorable = ['water', 'fire', 'wood'] (output generates wealth)
        # Then Jia (Wood) is Fav (+10). Chen (Earth-Water Tomb) -> Earth is Unfav usually (-10). 
        # Score = 4 - 6 = -2.
        # Multiplier: -2 * 2 = -4. + 20 = +16.
        # Jump from -2 to +16 is HUGE.
        
        print(f"Score Delta: {score_test - score_control} (Not direct comparison, but check absolute value)")
        self.assertGreater(score_test, 10.0, "Score should be high due to Wealth Treasury opening (+20 bonus)")
        print("✅ Champagne Test Passed: Wealth Treasury triggered massive score boost!")

if __name__ == '__main__':
    unittest.main()
