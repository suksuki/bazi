
"""
[SSEP] [EVHZ] Event Horizon Experiment
Simulating Black Hole Singularity Detection (True Follow vs Fake Follow)
"""
import sys
import unittest

workspace_root = "/home/jin/bazi_predict"
sys.path.append(workspace_root)

from core.trinity.core.engines.ssep_physics import SSEPQuantumPhysics

class TestEVHZBlackHole(unittest.TestCase):
    def test_singularity_detection(self):
        print("\n[SSEP] Calculating Event Horizon (Schwarzschild Radius)...")
        
        # 1. True Singularity (Zuan Wang / True Follow)
        # Chart: Wu Chen / Wu Chen / Wu Chen / Wu Chen (All Earth)
        # Pure Earth Monopole.
        c_sing = [('戊', '辰'), ('戊', '辰'), ('戊', '辰'), ('戊', '辰')] 
        res_sing = SSEPQuantumPhysics.audit_evhz_black_hole(c_sing)
        print(f"  Sample A (True Singularity): Mass={res_sing['mass_ratio']} | State={res_sing['schwarzschild_state']}")
        self.assertTrue(res_sing['is_black_hole'])
        self.assertEqual(res_sing['dominant_element'], "土")

        # 2. Accretion Disk (Turbulent / Fake Follow)
        # Chart: Wu Chen / Wu Chen / Wu Chen / Jia Yin (Crucial Wood Break)
        # Wood breaks the Earth Monopole.
        # Earth: 3 pillars (Mass ~75%), Wood: 1 pillar (Mass ~25%).
        # Should be Accretion Disk or Normal.
        c_disk = [('戊', '辰'), ('戊', '辰'), ('戊', '辰'), ('甲', '寅')]
        res_disk = SSEPQuantumPhysics.audit_evhz_black_hole(c_disk)
        print(f"  Sample B (Accretion Disk): Mass={res_disk['mass_ratio']} | State={res_disk['schwarzschild_state']}")
        self.assertFalse(res_disk['is_black_hole'])
        
        # 3. Normal Space (Balanced)
        c_norm = [('甲', '子'), ('丙', '寅'), ('庚', '申'), ('壬', '午')]
        res_norm = SSEPQuantumPhysics.audit_evhz_black_hole(c_norm)
        print(f"  Sample C (Normal): Mass={res_norm['mass_ratio']} | State={res_norm['schwarzschild_state']}")
        self.assertEqual(res_norm['schwarzschild_state'], "NORMAL_SPACE")
        
        print("  ✅ Black Hole Logic Verified")

if __name__ == '__main__':
    unittest.main()
