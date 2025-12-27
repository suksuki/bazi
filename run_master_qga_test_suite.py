
import sys
import os
import unittest
from datetime import datetime

workspace_root = "/home/jin/bazi_predict"
sys.path.append(workspace_root)

from core.trinity.core.engines.pattern_scout import PatternScout

class TestMasterQGAuites(unittest.TestCase):
    def setUp(self):
        self.scout = PatternScout()
        print(f"\n[MasterTest] Running {self._testMethodName}")
    
    def run_audit(self, chart, pattern_id):
        return self.scout._deep_audit(chart, pattern_id, geo_context=None)

    # --- Legacy Hierarchy Upgrades (V16.4) ---

    def test_pgb_hierarchy(self):
        # MOD_151 PGB Ultra: 7-killings + BiJie
        c = [('壬', '子'), ('壬', '子'), ('丙', '午'), ('丙', '申'), ('庚', '寅'), ('辛', '卯')]
        res = self.run_audit(c, "PGB_ULTRA_FLUID")
        self.assertIsNotNone(res)
        self.assertEqual(res.get('sub_module_id'), "MOD_151_PGB_A_ULTRA")
        print("  ✅ PGB -> MOD_151")

    def test_cygs_hierarchy_a(self):
        # MOD_141 CYGS Cai: Follow Wealth
        c = [('庚', '申'), ('辛', '酉'), ('丙', '子'), ('庚', '申'), ('戊', '子'), ('己', '丑')]
        res = self.run_audit(c, "CYGS_COLLAPSE")
        self.assertIsNotNone(res)
        self.assertEqual(res.get('sub_module_id'), "MOD_141_CYGS_A_CAI")
        print("  ✅ CYGS -> MOD_141")

    def test_hgfg_hierarchy_a(self):
        # MOD_145 HGFG JiaJi
        c = [('甲', '辰'), ('甲', '戌'), ('己', '丑'), ('戊', '辰'), ('庚', '午'), ('辛', '未')]
        res = self.run_audit(c, "HGFG_TRANSMUTATION")
        self.assertIsNotNone(res)
        self.assertEqual(res.get('sub_module_id'), "MOD_145_HGFG_A_JIAJI")
        print("  ✅ HGFG -> MOD_145")

    def test_sssc_hierarchy_a(self):
        # MOD_153 SSSC God
        c = [('丙', '寅'), ('丙', '寅'), ('甲', '子'), ('戊', '辰'), ('庚', '午'), ('辛', '未')]
        res = self.run_audit(c, "SSSC_AMPLIFIER")
        self.assertIsNotNone(res)
        self.assertEqual(res.get('sub_module_id'), "MOD_153_SSSC_A_GOD")
        print("  ✅ SSSC -> MOD_153")

    def test_jltg_hierarchy_a(self):
        # MOD_155 JLTG JianLu
        c = [('丙', '寅'), ('庚', '寅'), ('甲', '子'), ('戊', '辰'), ('庚', '午'), ('辛', '未')]
        res = self.run_audit(c, "JLTG_CORE_ENERGY")
        self.assertIsNotNone(res)
        self.assertEqual(res.get('sub_module_id'), "MOD_155_JLTG_A_JIANLU")
        print("  ✅ JLTG -> MOD_155")
        
    # --- New QGA V4.5 Features (Vacuum/Storage/Mixed) ---

    def test_sksk_four_graves(self):
        # MOD_133 SKSK: Four Graves
        # 辰戌丑未 all present
        c_sksk = [('甲', '辰'), ('甲', '戌'), ('甲', '丑'), ('甲', '未'), ('甲', '子'), ('甲', '子')]
        res = self.run_audit(c_sksk, "MBGS_STORAGE_POTENTIAL")
        self.assertIsNotNone(res)
        # Assuming sub_tags="SKSK_COLLAPSE_陷阱" triggers logic
        self.assertEqual(res.get('sub_module_id'), "MOD_133_SKSK_COLLAPSE")
        print("  ✅ MBGS -> MOD_133 (SKSK)")

    def test_jsg_gold_god(self):
        # MOD_131 JSG: Gold God (Gui You / Ji Si / Yi Chou)
        # Must have active graves + Gold God pillar
        # Use active graves (Chen/Xu) + Day: 癸酉
        c_jsg = [('甲', '辰'), ('甲', '戌'), ('癸', '酉'), ('甲', '辰'), ('甲', '子'), ('甲', '子')]
        res = self.run_audit(c_jsg, "MBGS_STORAGE_POTENTIAL")
        self.assertIsNotNone(res)
        self.assertEqual(res.get('sub_module_id'), "MOD_131_JSG_CORE")
        print("  ✅ MBGS -> MOD_131 (JSG)")

    def test_tsg_mixed_excite(self):
        # MOD_134 TSG: Tou Gan Excite
        # High entropy branch (e.g. Chen: Wu, Yi, Gui). Stem: Yi.
        # Add Luck Pillar (Index 4) to test Luck Injection
        c_tsg = [('甲', '子'), ('乙', '辰'), ('甲', '子'), ('甲', '子'), ('乙', '亥'), ('甲', '子')]
        # Branch 1 is Chen (High entropy). Stem 1 is Yi. Yi is in Chen. -> TSG Active.
        res = self.run_audit(c_tsg, "ZHSG_MIXED_EXCITATION")
        self.assertIsNotNone(res)
        self.assertEqual(res.get('sub_module_id'), "MOD_134_TSG_EXCITE")
        print("  ✅ ZHSG -> MOD_134 (TSG + Luck Injection)")

    def test_zhsg_sksk_constructive(self):
        # NEW: SKSK within ZHSG forming Constructive Array
        # 辰戌丑未 all present. 
        c_sksk = [('甲', '辰'), ('甲', '戌'), ('甲', '丑'), ('甲', '未'), ('甲', '子'), ('甲', '子')]
        res = self.run_audit(c_sksk, "ZHSG_MIXED_EXCITATION")
        self.assertIsNotNone(res)
        # Should change status to "SKSK_GRAVITATIONAL_LOCK" and tags contain "SKSK_CONSTRUCTIVE_ARRAY"
        self.assertIn("SKSK_CONSTRUCTIVE_ARRAY", res.get("sub_tags", []))
        print("  ✅ ZHSG -> SKSK Constructive Array Verified")

if __name__ == '__main__':
    unittest.main()
