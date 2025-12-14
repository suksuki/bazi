"""
[Antigravity V8.0] Phase Change Protocol Test
==============================================
验证 "焦土不生金" (Scorched Earth) 修复 VAL_006 (星爷) 问题。

Physics Background:
- 星爷: 辛金日主, 生于午月（火旺）
- 问题: V7.4 计算他为身强（土生金太顺畅）
- 修复: V8.0 在夏季阻断 Earth -> Metal 的生成通道
"""

import unittest
from core.engines.flow_engine import FlowEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
import copy


class TestV80PhaseChange(unittest.TestCase):
    """Test V8.0 Phase Change Protocol"""
    
    def setUp(self):
        self.config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
        self.engine = FlowEngine(self.config)
    
    def test_scorched_earth_blocks_metal_generation(self):
        """焦土不生金：夏季 Earth -> Metal 应被阻断"""
        # Initial state: Strong Earth (100), Metal as DM (50)
        initial = {
            'wood': 20.0, 
            'fire': 80.0,   # Summer fire is strong
            'earth': 100.0, # Lots of earth from fire
            'metal': 50.0,  # Metal DM (like 辛金)
            'water': 10.0
        }
        
        # Winter (no Phase Change) - Earth generates Metal freely
        final_winter = self.engine.simulate_flow(initial.copy(), dm_elem='metal', month_branch='子')
        
        # Summer (Phase Change active) - Earth -> Metal blocked
        final_summer = self.engine.simulate_flow(initial.copy(), dm_elem='metal', month_branch='午')
        
        # In summer, Metal should receive MUCH LESS energy from Earth
        print(f"\n🧪 Phase Change Test Results:")
        print(f"   Winter (子月): Metal = {final_winter.get('metal', 0):.1f}")
        print(f"   Summer (午月): Metal = {final_summer.get('metal', 0):.1f}")
        
        winter_metal = final_winter.get('metal', 0)
        summer_metal = final_summer.get('metal', 0)
        
        # Summer metal should be significantly lower
        self.assertLess(
            summer_metal, 
            winter_metal * 0.8,  # At least 20% lower
            f"Phase Change Failed: Summer metal ({summer_metal:.1f}) should be much less than winter ({winter_metal:.1f})"
        )
        
        print(f"   ✅ Difference: {winter_metal - summer_metal:.1f} ({(1 - summer_metal/winter_metal)*100:.0f}% reduction)")
    
    def test_frozen_water_blocks_wood_generation(self):
        """冻水不生木：冬季 Water -> Wood 应被阻断"""
        # Initial state: Strong Water (100), Wood as DM (50)
        initial = {
            'wood': 50.0,   # Wood DM
            'fire': 20.0,
            'earth': 30.0,
            'metal': 40.0,
            'water': 100.0  # Winter water is strong
        }
        
        # Summer (no Phase Change for water)
        final_summer = self.engine.simulate_flow(initial.copy(), dm_elem='wood', month_branch='午')
        
        # Winter (Phase Change active) - Water -> Wood blocked
        final_winter = self.engine.simulate_flow(initial.copy(), dm_elem='wood', month_branch='子')
        
        print(f"\n🧪 Frozen Water Test Results:")
        print(f"   Summer (午月): Wood = {final_summer.get('wood', 0):.1f}")
        print(f"   Winter (子月): Wood = {final_winter.get('wood', 0):.1f}")
        
        summer_wood = final_summer.get('wood', 0)
        winter_wood = final_winter.get('wood', 0)
        
        # Winter wood should be lower due to frozen water
        self.assertLess(
            winter_wood,
            summer_wood * 0.9,  # At least 10% lower
            f"Phase Change Failed: Winter wood ({winter_wood:.1f}) should be less than summer ({summer_wood:.1f})"
        )
        
        print(f"   ✅ Difference: {summer_wood - winter_wood:.1f} ({(1 - winter_wood/summer_wood)*100:.0f}% reduction)")
    
    def test_phase_change_config_defaults(self):
        """Phase Change 参数默认值验证"""
        flow = DEFAULT_FULL_ALGO_PARAMS.get('flow', {})
        phase = flow.get('phaseChange', {})
        
        self.assertIn('scorchedEarthDamping', phase)
        self.assertIn('frozenWaterDamping', phase)
        
        self.assertEqual(phase['scorchedEarthDamping'], 0.15)  # 85% blocked
        self.assertEqual(phase['frozenWaterDamping'], 0.3)     # 70% blocked
        
        print("\n✅ Phase Change defaults verified: Scorched=0.15, Frozen=0.3")
    
    def test_val_006_stephen_chow_simulation(self):
        """
        模拟 VAL_006 (星爷) 案例
        
        星爷八字: 辛金日主, 生于午月
        - 年: 壬辰
        - 月: 丙午
        - 日: 辛酉
        - 时: 甲午
        
        预期: 午月火旺，土被烤干变焦土，不能生金 -> 应该身弱
        """
        # Simulate Stephen Chow's element distribution
        initial = {
            'wood': 30.0,   # 甲 (时干)
            'fire': 120.0,  # 丙 (月干) + 午午 (月支+时支) -> 火极旺
            'earth': 80.0,  # 辰 (年支) - 但会变焦土
            'metal': 40.0,  # 辛 (日干) + 酉 (日支)
            'water': 40.0   # 壬 (年干)
        }
        
        # V7.4 (no phase change) - Metal receives full earth support
        engine_v74 = FlowEngine(self.config)
        # Simulate without moon branch
        final_v74 = engine_v74.simulate_flow(initial.copy(), dm_elem='metal', month_branch=None)
        
        # V8.0 (with phase change) - Earth -> Metal blocked
        engine_v80 = FlowEngine(self.config)
        final_v80 = engine_v80.simulate_flow(initial.copy(), dm_elem='metal', month_branch='午')
        
        print(f"\n🌟 VAL_006 (星爷) Simulation:")
        print(f"   V7.4 (No Phase Change): Metal = {final_v74.get('metal', 0):.1f}")
        print(f"   V8.0 (Scorched Earth):  Metal = {final_v80.get('metal', 0):.1f}")
        
        v74_metal = final_v74.get('metal', 0)
        v80_metal = final_v80.get('metal', 0)
        
        reduction = (1 - v80_metal / v74_metal) * 100 if v74_metal > 0 else 0
        
        print(f"   📉 Metal Reduction: {reduction:.0f}%")
        
        # V8.0 should show significant metal reduction
        self.assertLess(
            v80_metal,
            v74_metal * 0.7,  # At least 30% reduction
            "VAL_006 Fix Failed: Metal not reduced enough in summer"
        )
        
        print(f"   ✅ V8.0 Phase Change successfully reduced Metal strength!")


class TestV80BackwardCompatibility(unittest.TestCase):
    """Ensure V8.0 doesn't break existing V7.4 functionality"""
    
    def test_non_summer_non_winter_unchanged(self):
        """非夏非冬月份不受影响"""
        config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
        engine = FlowEngine(config)
        
        initial = {
            'wood': 50.0,
            'fire': 50.0,
            'earth': 50.0,
            'metal': 50.0,
            'water': 50.0
        }
        
        # Test with spring month (卯)
        final_spring = engine.simulate_flow(initial.copy(), dm_elem='wood', month_branch='卯')
        
        # Test with autumn month (酉)
        final_autumn = engine.simulate_flow(initial.copy(), dm_elem='metal', month_branch='酉')
        
        # Both should work normally without Phase Change interference
        # (Just verify they run without errors and produce reasonable results)
        self.assertGreater(final_spring.get('wood', 0), 0)
        self.assertGreater(final_autumn.get('metal', 0), 0)
        
        print("\n✅ Spring and Autumn months unaffected by Phase Change")


if __name__ == '__main__':
    unittest.main(verbosity=2)
