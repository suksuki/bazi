import unittest
from core.quantum_engine import QuantumEngine
from core.bazi_profile import BaziProfile

class TestV7Tuning(unittest.TestCase):
    def test_wang_shuai_tuning(self):
        print("\n--- V7.0 Auto-Tuning: Wang Shuai Sensitivity Test ---")
        
        # 1. Initialize Engine (Default Config)
        engine = QuantumEngine()
        
        # 2. Setup a Case (Sample: Maybe weak or balanced)
        # 甲 wood born in 申 month (Metal) -> Generally Weak (Metal kills Wood)
        # But let's assume we want to tune the weights to make it Strong artificially.
        # Chart: Year=..., Month=壬申 (Water/Metal), Day=甲子 (Wood/Water)
        # Month Branch 申 (Metal) is against Day Master 甲 (Wood). 
        # But Day Branch 子 (Water) supports Wood.
        
        # We'll use the internal _evaluate_wang_shuai method for direct testing.
        dm_char = '甲'
        # [Year, Month, Day, Hour]
        # Year: 庚午 (Metal/Fire)
        # Month: 壬申 (Water/Metal) - Month Command is Metal (Oppose)
        # Day: 甲子 (Wood/Water)   - Day Branch is Water (Support)
        # Hour: 乙亥 (Wood/Water)  - Hour is Support
        bazi_list = ['庚午', '壬申', '甲子', '乙亥']
        
        # Under default weights:
        # Month Command (Oppose) weight 0.40 -> Huge penalty
        # Day Branch (Support) weight 0.15
        # Likely Weak.
        
        strength_default, score_default = engine._evaluate_wang_shuai(dm_char, bazi_list)
        print(f"Default Config -> Strength: {strength_default}, Score: {score_default:.2f}")
        
        # 3. TUNE IT!
        # Let's reduce Month Command weight (Enemy) and increase Day Branch weight (Ally).
        # This represents a different school of thought in Bazi.
        new_config = {
            "baseEnergy": {
                "positionWeights": {
                    "monthCommand": 0.10, # Was 0.40 (Downgrade the enemy)
                    "dayBranch": 0.50,    # Was 0.15 (Upgrade the ally)
                    "stem": 0.10,
                    "branch": 0.05
                }
            }
        }
        
        engine.update_full_config(new_config)
        print(">>> Updated Config: Reduced Month Impact, Increased Day Impact.")
        
        # 4. Re-calculate
        strength_tuned, score_tuned = engine._evaluate_wang_shuai(dm_char, bazi_list)
        print(f"Tuned Config   -> Strength: {strength_tuned}, Score: {score_tuned:.2f}")
        
        # 5. Verify Impact
        # The score should have increased significantly because we downgraded the opposing force (Month)
        # and upgraded the supporting force (Day Branch).
        # Note: In _evaluate_wang_shuai logic:
        # Month Branch (Metal vs Wood) -> Oppose -> Adds to total_oppose
        # Day Branch (Water vs Wood) -> Support -> Adds to total_support
        # final_score = score + total_support
        # Verdict depends on final_score > total_oppose
        
        # By reducing Month weight, total_oppose should drop.
        # By increasing Day weight, total_support should rise.
        # Thus, Score should rise.
        
        self.assertGreater(score_tuned, score_default, "Tuning failed: Score did not increase as expected.")
        
        # Check if verdict changed (Optional, depends on threshold)
        if strength_default == "Weak" and strength_tuned == "Strong":
            print("✅ SUCCESS: Tuning flipped the verdict from Weak to Strong!")
        elif strength_default == strength_tuned:
            print("ℹ️ Verdict remained same, but score shifted.")
        
        print(f"Delta: {score_tuned - score_default:.2f}")

if __name__ == "__main__":
    unittest.main()
