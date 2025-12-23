
import unittest
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.unified_arbitrator_master import UnifiedArbitratorMaster
from core.trinity.core.intelligence.logic_arbitrator import LogicArbitrator

class TestPerturbationArbitrationV11_5(unittest.TestCase):
    
    def setUp(self):
        self.master = UnifiedArbitratorMaster()

    def test_cross_layer_arbitration(self):
        """验证跨层触发：伤官在月令/大运，正官在流年。"""
        # 戊日主
        # 辛酉是大运 (Shang Guan)
        # 乙巳是流年 (Zheng Guan)
        # 庚子是月令 (Shi Shen - 也能贡献一部分场强)
        natal = ["丙寅", "庚子", "戊辰", "丙辰"]
        context = {
            "luck_pillar": "辛酉",
            "annual_pillar": "乙巳",
            "phase_progress": 0.5,
            "geo_factor": 1.0
        }
        
        res = self.master.arbitrate_bazi(natal, current_context=context)
        rules = [r['id'] for r in res.get("rules", [])]
        
        # 辛在酉是大运，辛是戊的伤官
        # 乙在巳是流年，乙是戊的正官
        # 应触发 PH28_01 (伤官见官)
        self.assertIn("PH28_01", rules)
        
        # 检查强度值是否存在
        oppose_rule = next(r for r in res.get("rules", []) if r['id'] == "PH28_01")
        self.assertGreater(oppose_rule.get("intensity", 0), 144.0)

    def test_hidden_energy_capture(self):
        """验证隐藏能量捕捉：正财仅在地支余气中。"""
        # 戊日主，地支有辰 (藏癸水正财)
        # 庚申时柱 (庚为食神)
        natal = ["丙寅", "庚子", "戊辰", "庚申"]
        
        # Calculate Intensities manually via LogicArbitrator
        # Pillars order: year, month, day, hour, luck, annual
        all_pillars = natal + ["甲子", "甲子"]
        intensities = LogicArbitrator.calculate_field_intensities(all_pillars, "戊")
        
        # 辰中癸水是正财, 子中癸水也是正财
        self.assertGreater(intensities["Zheng Cai"], 0)
        # 子中心气贡献大，辰中余气贡献小，但至少要有贡献
        # 按算法：子中癸水权10，辰中癸水权2
        self.assertGreater(intensities["Zheng Cai"], 9.0)

    def test_geo_intensity_scaling(self):
        """验证 GEO 因子对场强的线性放缩效应。"""
        natal = ["丙寅", "庚子", "戊辰", "庚申"]
        current_dm = "戊"
        all_pillars = natal + ["甲子", "甲子"]
        
        # 基准 GEO = 1.0
        intensities_1 = LogicArbitrator.calculate_field_intensities(all_pillars, current_dm, geo_factor=1.0)
        
        # 强化 GEO = 2.0
        intensities_2 = LogicArbitrator.calculate_field_intensities(all_pillars, current_dm, geo_factor=2.0)
        
        for key in intensities_1:
            if intensities_1[key] > 0:
                self.assertAlmostEqual(intensities_2[key], intensities_1[key] * 2.0, places=2)

    def test_intensity_thresholding(self):
        """验证由于强度不足而不触发规则的情况。"""
        # 甲子时柱，戊子日柱，基本没有伤官/正官元素
        natal = ["甲子", "甲子", "戊子", "甲子"]
        context = {
            "luck_pillar": "甲子",
            "annual_pillar": "甲子",
            "phase_progress": 0.1
        }
        
        res = self.master.arbitrate_bazi(natal, current_context=context)
        rules = [r['id'] for r in res.get("rules", [])]
        
        self.assertNotIn("PH28_01", rules)

if __name__ == "__main__":
    unittest.main()
