
"""
[SSEP] [CEQS] Screening Experiment
Simulating Penetration Screening on Mock Database for Transmutation Purity.
"""
import sys
import unittest

workspace_root = "/home/jin/bazi_predict"
sys.path.append(workspace_root)

from core.trinity.core.engines.ssep_physics import SSEPQuantumPhysics

class TestSSEPCEQSScreening(unittest.TestCase):
    def test_purity_screening(self):
        print("\n[SSEP] Calculating Transmutation Purity for Sample Batch...")
        
        # 1. True Transmutation (Jia-Ji -> Earth, Month=Earth, No Wood/Metal impurity)
        # Chart: Jia Chen / Ji Chou / Wu Chen / Bing Chen
        # Pairs: Jia + Ji. Month: Chou (Earth). Impurities: Wood (None else), Metal (None). All Earth/Fire.
        c_true = [('甲', '辰'), ('己', '丑'), ('戊', '辰'), ('丙', '辰')] 
        res_true = SSEPQuantumPhysics.audit_ceqs_transmutation(c_true)
        print(f"  Sample A (True): Purity={res_true['purity']} | State={res_true['phase_transition']}")
        self.assertEqual(res_true['phase_transition'], "SUPERCONDUCTING (Zero Resistance)")

        # 2. Pseudo Transmutation (Jia-Ji -> Earth, but with strong Wood impurity)
        # Chart: Jia Yin / Ji Mao / Wu Chen / Yi Mao
        # Pairs: Jia + Ji. Impurities: Yin (Wood), Mao (Wood), Yi (Wood).
        c_pseudo = [('甲', '寅'), ('己', '卯'), ('戊', '辰'), ('乙', '卯')]
        res_pseudo = SSEPQuantumPhysics.audit_ceqs_transmutation(c_pseudo)
        print(f"  Sample B (Pseudo/Impure): Purity={res_pseudo['purity']} | State={res_pseudo['phase_transition']}")
        self.assertNotEqual(res_pseudo['phase_transition'], "SUPERCONDUCTING (Zero Resistance)")
        
        # 3. Mixed Case (Jia-Ji -> Earth, some Water/Metal but manageable?)
        # Chart: Jia Zi / Ji Chou ...
        c_mixed = [('甲', '子'), ('己', '丑'), ('戊', '辰'), ('庚', '午')]
        # Geng is Metal (drains Earth? Map says Drain=Metal). 
        # But wait, logic says Impurity=Wood for Jia-Ji. Metal is 'Drain'.
        # Let's check logic: 'imp'=['木']. Metal is NOT in 'imp', so it doesn't reduce purity in Alpha logic?
        # Actually logic only subtracts for 'imp'.
        res_mixed = SSEPQuantumPhysics.audit_ceqs_transmutation(c_mixed)
        print(f"  Sample C (Mixed): Purity={res_mixed['purity']} | State={res_mixed['phase_transition']}")
        
        print("  ✅ Penetration Screening Logic Verified")

if __name__ == '__main__':
    unittest.main()
