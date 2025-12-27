
"""
[SSEP] [SSLC] Resonance Experiment
Simulating Two-Element Imaging (Supersymmetric Resonance)
"""
import sys
import unittest

workspace_root = "/home/jin/bazi_predict"
sys.path.append(workspace_root)

from core.trinity.core.engines.ssep_physics import SSEPQuantumPhysics

class TestSSLCResonance(unittest.TestCase):
    def test_imaging_symmetry(self):
        print("\n[SSEP] Calculating Supersymmetric Resonance for Two-Element Imaging...")
        
        # 1. Perfect Symmetry (Water/Wood) - Shui Mu Qing Hua
        # Chart: Ren Zi / Jia Yin / Gui Hai / Yi Mao (Total Water + Wood)
        c_perf = [('壬', '子'), ('甲', '寅'), ('癸', '亥'), ('乙', '卯')]
        res_perf = SSEPQuantumPhysics.audit_two_element_imaging(c_perf)
        # Should be Perfect Symmetry
        print(f"  Sample A (Perfect): Elements={res_perf['elements']} | Sim={res_perf['symmetry_score']} | Mode={res_perf['resonance_mode']}")
        self.assertTrue(res_perf['is_imaging'])
        self.assertEqual(res_perf['resonance_mode'], "PERFECT_SYMMETRY")

        # 2. Quasi Symmetry (Metal/Wood) - Jin Mu Cheng Qi (Opposing but balanced)
        # Chart: Geng Shen / Jia Yin / Geng Shen / Jia Yin (Clash heavy, but balanced energy)
        c_quasi = [('庚', '申'), ('甲', '寅'), ('庚', '申'), ('甲', '寅')]
        res_quasi = SSEPQuantumPhysics.audit_two_element_imaging(c_quasi)
        print(f"  Sample B (Quasi/Clash): Elements={res_quasi['elements']} | Sim={res_quasi['symmetry_score']} | Mode={res_quasi['resonance_mode']}")
        self.assertTrue(res_quasi['is_imaging'])
        # Depending on weights, might be Perfect or Quasi. Let's see.
        
        # 3. Failed (Imbalanced)
        # Chart: Wu Chen (Earth) x 3 + 1 Wood.
        c_fail = [('戊', '辰'), ('戊', '辰'), ('戊', '辰'), ('甲', '子')]
        res_fail = SSEPQuantumPhysics.audit_two_element_imaging(c_fail)
        print(f"  Sample C (Fail): Is Imaging? {res_fail['is_imaging']} | Reason: {res_fail.get('reason')}")
        self.assertFalse(res_fail['is_imaging'])
        
        print("  ✅ Two-Element Imaging Logic Verified")

if __name__ == '__main__':
    unittest.main()
