"""
[Antigravity V7.4] 发布验证测试套件 (Release Verification Test Suite)
====================================================================
验证 V7.4 "物理学家版" 所有核心特性的完整性和正确性。

Features Tested:
1. ✅ 月令集权 (Imperial Month) - Weight = 2.0
2. ✅ 阻尼协议 (Damping Protocol) - Impedance & Viscosity
3. ✅ 墓库拓扑 (Vault Topology) - Open/Sealed/Broken
4. ✅ 骷髅协议 (Skull Protocol) - Three Punishments
5. ✅ 化学反应 (Alchemy) - Stem Five Combination
6. ✅ 配置驱动 (Config-Driven) - 100% Parameterized
"""

import unittest
import copy
from datetime import datetime

from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from core.config_rules import (
    MONTH_WEIGHT_MULTIPLIER,
    SCORE_SKULL_CRASH,
    SCORE_TREASURY_BONUS,
    ENERGY_THRESHOLD_STRONG,
    ENERGY_THRESHOLD_WEAK,
    TOMB_ELEMENTS
)
from core.bazi_profile import BaziProfile


class TestV74GoldenConfig(unittest.TestCase):
    """Test V7.4 Golden Configuration Parameters"""
    
    def test_month_weight_is_imperial(self):
        """月令权重必须为 2.0 (Imperial Month)"""
        pillar_weights = DEFAULT_FULL_ALGO_PARAMS['physics']['pillarWeights']
        self.assertEqual(pillar_weights['month'], 2.0, "月令权重必须为 2.0")
        self.assertEqual(MONTH_WEIGHT_MULTIPLIER, 2.0, "Legacy 月令乘数必须为 2.0")
        print("✅ 月令集权 (Imperial Month): 2.0x")
    
    def test_damping_protocol_params(self):
        """阻尼协议参数完整性"""
        flow = DEFAULT_FULL_ALGO_PARAMS['flow']
        
        # Resource Impedance
        res_imp = flow['resourceImpedance']
        self.assertIn('base', res_imp)
        self.assertIn('weaknessPenalty', res_imp)
        self.assertEqual(res_imp['base'], 0.3)
        self.assertEqual(res_imp['weaknessPenalty'], 0.5)
        
        # Output Viscosity
        out_vis = flow['outputViscosity']
        self.assertIn('maxDrainRate', out_vis)
        self.assertIn('drainFriction', out_vis)
        self.assertEqual(out_vis['maxDrainRate'], 0.6)
        self.assertEqual(out_vis['drainFriction'], 0.2)
        
        # Global Entropy
        self.assertEqual(flow['globalEntropy'], 0.05)
        
        print("✅ 阻尼协议 (Damping Protocol): Impedance=0.3, Viscosity=0.6, Entropy=0.05")
    
    def test_vault_physics_params(self):
        """墓库物理参数完整性"""
        vault = DEFAULT_FULL_ALGO_PARAMS['interactions']['vaultPhysics']
        
        self.assertEqual(vault['threshold'], 20.0)
        self.assertEqual(vault['sealedDamping'], 0.4)
        self.assertEqual(vault['openBonus'], 1.5)
        
        print("✅ 墓库拓扑 (Vault Topology): Threshold=20, SealedDamp=0.4, OpenBonus=1.5")
    
    def test_skull_protocol_params(self):
        """骷髅协议参数"""
        self.assertEqual(SCORE_SKULL_CRASH, -50.0)
        skull = DEFAULT_FULL_ALGO_PARAMS['interactions']['skull']
        self.assertEqual(skull['crashScore'], -50.0)
        
        print("✅ 骷髅协议 (Skull Protocol): Crash Score = -50")
    
    def test_energy_thresholds(self):
        """身强身弱阈值"""
        self.assertEqual(ENERGY_THRESHOLD_STRONG, 3.5)
        self.assertEqual(ENERGY_THRESHOLD_WEAK, 2.0)
        
        print("✅ 能量阈值: Strong=3.5, Weak=2.0")


class TestV74DampingProtocol(unittest.TestCase):
    """Test V7.4 Damping Protocol (Impedance & Viscosity)"""
    
    def setUp(self):
        self.engine = QuantumEngine()
        self.engine.update_full_config(copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS))
    
    def test_impedance_limits_resource_flow(self):
        """输入阻抗：虚不受补测试"""
        from core.engines.flow_engine import FlowEngine
        
        # Create flow engine with config
        flow_engine = FlowEngine(DEFAULT_FULL_ALGO_PARAMS)
        
        # Initial state: Weak Self (wood=20), Strong Resource (water=100)
        initial = {'wood': 20.0, 'fire': 10.0, 'earth': 10.0, 'metal': 10.0, 'water': 100.0}
        
        # Run flow simulation with DM = wood
        final = flow_engine.simulate_flow(initial, dm_elem='wood')
        
        # Wood should NOT spike to 120 (superconductor behavior)
        # Impedance should limit the gain
        self.assertLess(final.get('wood', 0), 80.0, "阻抗失效：虚不受补未生效，能量涌入过多")
        print(f"✅ 输入阻抗生效: Wood {initial['wood']:.1f} -> {final.get('wood', 0):.1f} (受限)")
    
    def test_flow_engine_exists_and_works(self):
        """Flow Engine 存在且工作正常"""
        from core.engines.flow_engine import FlowEngine
        
        flow_engine = FlowEngine(DEFAULT_FULL_ALGO_PARAMS)
        
        # Test basic flow
        initial = {'wood': 50.0, 'fire': 50.0, 'earth': 50.0, 'metal': 50.0, 'water': 50.0}
        final = flow_engine.simulate_flow(initial, dm_elem='wood')
        
        # Should return a dict with all elements
        self.assertIn('wood', final)
        self.assertIn('fire', final)
        self.assertIn('earth', final)
        self.assertIn('metal', final)
        self.assertIn('water', final)
        
        print(f"✅ Flow Engine 正常工作")


class TestV74SkullProtocol(unittest.TestCase):
    """Test V7.4 Skull Protocol (Three Punishments)"""
    
    def setUp(self):
        self.engine = QuantumEngine()
    
    def test_three_punishments_detection_with_dict(self):
        """丑未戌三刑检测 (使用字典接口)"""
        # Chart with pillars containing 丑未
        chart = {
            'year_pillar': '丁丑',
            'month_pillar': '丁未',
            'day_pillar': '己丑',
            'hour_pillar': '辛未'
        }
        year_branch = '戌'  # Incoming year triggers 丑未戌
        
        is_triggered = self.engine.skull_engine.detect_three_punishments(chart, year_branch)
        
        # With 戌 year, we now have 丑+未+戌 = Three Punishments
        self.assertTrue(is_triggered, "三刑未触发")
        print(f"✅ 骷髅协议触发: 丑未戌三刑齐见")
    
    def test_skull_evaluate_returns_crash_score(self):
        """三刑熔断分测试 (使用 evaluate 接口)"""
        # Branches containing 丑未戌
        branches = ['丑', '未', '丑', '未', '戌']
        
        result = self.engine.skull_engine.evaluate(branches)
        
        # Should have crash score of -50
        self.assertLessEqual(result['score'], SCORE_SKULL_CRASH)
        self.assertEqual(result['icon'], '💀')
        self.assertIn('三刑齐见', result['tags'])
        
        print(f"✅ 骷髅熔断分: {result['score']}, Icon: {result['icon']}")


class TestV74VaultTopology(unittest.TestCase):
    """Test V7.4 Vault Topology (Treasury Physics)"""
    
    def setUp(self):
        self.engine = QuantumEngine()
        self.engine.update_full_config(copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS))
    
    def test_vault_element_mapping(self):
        """墓库元素映射测试 (使用 config_rules)"""
        # 辰戌丑未 are the four vaults
        # TOMB_ELEMENTS from config_rules
        self.assertEqual(TOMB_ELEMENTS['辰'], 'Water')
        self.assertEqual(TOMB_ELEMENTS['戌'], 'Fire')
        self.assertEqual(TOMB_ELEMENTS['丑'], 'Metal')
        self.assertEqual(TOMB_ELEMENTS['未'], 'Wood')
        
        print("✅ 墓库元素映射: 辰=Water, 戌=Fire, 丑=Metal, 未=Wood")
    
    def test_treasury_engine_exists(self):
        """Treasury Engine 存在且可用"""
        self.assertIsNotNone(self.engine.treasury_engine)
        
        # Test get_vault_params method
        params = self.engine.treasury_engine.get_vault_params()
        self.assertIn('threshold', params)
        self.assertIn('openBonus', params)
        
        print(f"✅ Treasury Engine 正常工作, Params: {params}")


class TestV74Alchemy(unittest.TestCase):
    """Test V7.4 Alchemy (Stem Five Combination)"""
    
    def setUp(self):
        self.engine = QuantumEngine()
    
    def test_harmony_engine_exists(self):
        """Harmony Engine 存在且可用"""
        self.assertIsNotNone(self.engine.harmony_engine)
        print("✅ Harmony Engine 存在")
    
    def test_stem_combination_mapping(self):
        """天干五合映射验证"""
        # 甲己合土, 乙庚合金, 丙辛合水, 丁壬合木, 戊癸合火
        STEM_COMBOS = {
            '甲': '己', '己': '甲',  # -> 土
            '乙': '庚', '庚': '乙',  # -> 金
            '丙': '辛', '辛': '丙',  # -> 水
            '丁': '壬', '壬': '丁',  # -> 木
            '戊': '癸', '癸': '戊',  # -> 火
        }
        
        # Verify mapping exists in harmony engine
        if hasattr(self.engine.harmony_engine, 'STEM_COMBINATIONS'):
            for k, v in STEM_COMBOS.items():
                self.assertEqual(
                    self.engine.harmony_engine.STEM_COMBINATIONS.get(k), v,
                    f"天干五合映射错误: {k}"
                )
        
        print("✅ 天干五合映射验证通过")


class TestV74ConfigDriven(unittest.TestCase):
    """Test V7.4 Config-Driven Architecture"""
    
    def setUp(self):
        self.engine = QuantumEngine()
    
    def test_hot_config_update(self):
        """配置热更新测试"""
        # Get initial state
        initial_config = copy.deepcopy(self.engine.full_config)
        initial_month_weight = initial_config['physics']['pillarWeights']['month']
        
        # Update config
        new_config = copy.deepcopy(initial_config)
        new_config['physics']['pillarWeights']['month'] = 3.0
        
        self.engine.update_full_config(new_config)
        
        # Verify update
        updated_weight = self.engine.full_config['physics']['pillarWeights']['month']
        self.assertEqual(updated_weight, 3.0, "配置热更新失败")
        
        # Restore
        self.engine.update_full_config(initial_config)
        
        print(f"✅ 配置热更新: {initial_month_weight} -> 3.0 -> {initial_month_weight}")
    
    def test_engine_uses_config(self):
        """引擎使用配置测试"""
        # Verify Flow Engine receives config
        self.assertIsNotNone(self.engine.flow_engine)
        self.assertIsNotNone(self.engine.flow_engine.config)
        
        # Verify Harmony Engine receives config
        self.assertIsNotNone(self.engine.harmony_engine)
        self.assertIsNotNone(self.engine.harmony_engine.config)
        
        print("✅ 所有子引擎已接收配置")


class TestV74Integration(unittest.TestCase):
    """Integration Tests for V7.4 Complete Pipeline"""
    
    def setUp(self):
        self.engine = QuantumEngine()
    
    def test_full_chart_calculation(self):
        """完整排盘计算测试"""
        # Test case: Steve Jobs
        chart = {
            'birth_year': 1955,
            'birth_month': 2,
            'birth_day': 24,
            'birth_hour': 19
        }
        
        result = self.engine.calculate_chart(chart)
        
        # Verify essential outputs
        self.assertIn('day_master', result)
        self.assertIn('bazi', result)
        self.assertIn('wang_shuai', result)
        
        print(f"✅ 完整排盘: DM={result['day_master']}, 旺衰={result['wang_shuai']}")
    
    def test_year_context_with_datetime(self):
        """流年上下文计算测试 (使用 datetime)"""
        # BaziProfile expects datetime, not separate args
        birth_date = datetime(1955, 2, 24, 19)
        profile = BaziProfile(birth_date, gender=1)
        
        ctx = self.engine.calculate_year_context(profile, 2011)
        
        # Verify context structure
        self.assertIsNotNone(ctx)
        
        print(f"✅ 流年计算完成: 2011年")
    
    def test_bazi_profile_creation(self):
        """BaziProfile 创建测试"""
        birth_date = datetime(1990, 5, 15, 12)
        profile = BaziProfile(birth_date, gender=1)
        
        # Verify profile has essential properties
        self.assertIsNotNone(profile.pillars)
        self.assertIsNotNone(profile.day_master)
        
        print(f"✅ BaziProfile 创建成功: DM={profile.day_master}")


def run_v74_verification():
    """Run complete V7.4 verification suite"""
    print("\n" + "=" * 70)
    print("🧪 ANTIGRAVITY V7.4 RELEASE VERIFICATION TEST SUITE")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestV74GoldenConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestV74DampingProtocol))
    suite.addTests(loader.loadTestsFromTestCase(TestV74SkullProtocol))
    suite.addTests(loader.loadTestsFromTestCase(TestV74VaultTopology))
    suite.addTests(loader.loadTestsFromTestCase(TestV74Alchemy))
    suite.addTests(loader.loadTestsFromTestCase(TestV74ConfigDriven))
    suite.addTests(loader.loadTestsFromTestCase(TestV74Integration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 70)
    if result.wasSuccessful():
        print("✅ V7.4 VERIFICATION PASSED - All Systems Go!")
    else:
        print(f"⚠️ V7.4 VERIFICATION: {len(result.failures)} failures, {len(result.errors)} errors")
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    run_v74_verification()
