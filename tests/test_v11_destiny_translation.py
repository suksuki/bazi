
import unittest
import json
from core.trinity.core.unified_arbitrator_master import UnifiedArbitratorMaster
from core.trinity.core.intelligence.destiny_translator import DestinyTranslator, TranslationStyle

class TestDestinyTranslation(unittest.TestCase):
    def setUp(self):
        self.arbitrator = UnifiedArbitratorMaster()
        # Test with WKW style for specific template matching
        self.translator = DestinyTranslator(style=TranslationStyle.WONG_KAR_WAI)

    def test_translation_logic(self):
        # Case 1: High SAI
        state_high_sai = {
            "physics": {
                "entropy": 1.0,
                "stress": {"SAI": 2.5, "IC": 0.5},
                "wealth": {"State": "LAMINAR"},
                "relationship": {"State": "UNBOUND"}
            }
        }
        verdict = self.translator.translate_state(state_high_sai)
        templates = self.translator.DICTIONARIES[TranslationStyle.WONG_KAR_WAI]["SAI"]
        self.assertTrue(any(t in verdict for t in templates))
        print(f"High SAI Verdict: {verdict}")

        # Case 2: Signal Loss
        state_signal_loss = {
            "physics": {
                "entropy": 1.0,
                "stress": {"SAI": 1.0, "IC": 0.1},
                "wealth": {"State": "LAMINAR"},
                "relationship": {"State": "UNBOUND"}
            }
        }
        verdict = self.translator.translate_state(state_signal_loss)
        templates = self.translator.DICTIONARIES[TranslationStyle.WONG_KAR_WAI]["SIGNAL_LOSS"]
        self.assertTrue(any(t in verdict for t in templates))
        print(f"Signal Loss Verdict: {verdict}")

    def test_full_arbitration_report(self):
        # STRESS_TEST_V11 Case: High Stress
        bazi = ["癸卯", "乙卯", "戊辰", "庚申"] # High wood vs Earth
        birth_info = {
            "birth_year": 1963,
            "birth_month": 3,
            "birth_day": 30,
            "birth_hour": 16,
            "gender": "男"
        }
        ctx = {
            "luck_pillar": "辛亥",
            "annual_pillar": "甲辰",
            "months_since_switch": 6,
            "data": {"city": "北京 (Beijing)"}
        }
        
        report = self.arbitrator.arbitrate_bazi(bazi, birth_info, ctx)
        self.assertIn("physics", report)
        
        holographic = self.arbitrator.generate_holographic_report(report)
        print("--- HOLOGRAPHIC REPORT ---")
        print(holographic)
        
        self.assertIn("🔮", holographic)
        self.assertIn("第一部分", holographic)
        self.assertIn("🚀", holographic)
        self.assertIn("第三部分", holographic)
        # Verify that the report contains Chow-style quotes (since UnifiedArbitratorMaster defaults to Chow)
        self.assertTrue("咸鱼" in holographic or "功夫" in holographic or "酱爆" in holographic or "运气" in holographic or "一万年" in holographic or "如花" in holographic)

if __name__ == "__main__":
    unittest.main()
