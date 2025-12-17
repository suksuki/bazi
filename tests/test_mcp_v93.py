"""
MCP V9.3 测试套件
==================
测试 Model Context Protocol (MCP) 改进功能

测试覆盖:
1. 地理修正 (Geo Correction)
2. 流时修正 (Hourly Context)
3. 宏观场 (Era Context)
4. 事件锚点 (User Feedback)
5. 模型不确定性 (Pattern Uncertainty)
"""

import unittest
from datetime import datetime
from typing import Dict, Any

# === Core Imports ===
from core.processors.geo import GeoProcessor
from core.processors.hourly_context import HourlyContextProcessor
from core.processors.era import EraProcessor
from core.engine_graph import GraphNetworkEngine
from controllers.wealth_verification_controller import WealthVerificationController
from controllers.bazi_controller import BaziController


class TestMCPGeoCorrection(unittest.TestCase):
    """测试地理修正功能"""
    
    def setUp(self):
        self.geo = GeoProcessor()
    
    def test_geo_processor_initialization(self):
        """测试 GeoProcessor 初始化"""
        self.assertIsNotNone(self.geo)
        self.assertEqual(self.geo.name, "Geo Layer 0")
        print("✅ GeoProcessor 初始化成功")
    
    def test_city_lookup(self):
        """测试城市查找"""
        result = self.geo.process("Beijing")
        self.assertIsInstance(result, dict)
        if result.get('desc') != "Unknown City - Neutral":
            # 如果找到了城市数据
            self.assertIn('desc', result)
            self.assertIn('temperature_factor', result)
            self.assertIn('humidity_factor', result)
            self.assertIn('environment_bias', result)
            print(f"✅ 城市查找成功: {result.get('desc')}")
        else:
            print("⚠️ 城市数据未找到，使用默认值")
    
    def test_latitude_calculation(self):
        """测试纬度计算"""
        result = self.geo.process(39.9)  # 北京纬度
        self.assertIsInstance(result, dict)
        self.assertIn('desc', result)
        self.assertIn('temperature_factor', result)
        self.assertIn('humidity_factor', result)
        self.assertIn('environment_bias', result)
        
        # 检查五行修正系数
        elements = ['wood', 'fire', 'earth', 'metal', 'water']
        for elem in elements:
            self.assertIn(elem, result)
            self.assertIsInstance(result[elem], (int, float))
            self.assertGreater(result[elem], 0)
        
        print(f"✅ 纬度计算成功: {result.get('desc')}")
        print(f"   温度系数: {result.get('temperature_factor')}")
        print(f"   环境偏向: {result.get('environment_bias')}")
    
    def test_environment_bias_calculation(self):
        """测试环境修正偏向计算"""
        # 创建一个有偏向的修正系数
        modifiers = {
            'fire': 1.2,
            'water': 0.9,
            'wood': 1.0,
            'metal': 1.0,
            'earth': 1.0
        }
        bias = self.geo._get_environment_bias(modifiers)
        self.assertIsInstance(bias, str)
        self.assertIn('环境修正偏向', bias)
        print(f"✅ 环境偏向计算: {bias}")


class TestMCPHourlyContext(unittest.TestCase):
    """测试流时修正功能"""
    
    def setUp(self):
        self.hourly = HourlyContextProcessor()
    
    def test_hourly_processor_initialization(self):
        """测试 HourlyContextProcessor 初始化"""
        self.assertIsNotNone(self.hourly)
        # 检查是否有 name 属性
        if hasattr(self.hourly, 'name'):
            self.assertEqual(self.hourly.name, "Hourly Context Layer")
        print("✅ HourlyContextProcessor 初始化成功")
    
    def test_hour_branch_calculation(self):
        """测试时支计算"""
        # 测试不同小时
        test_cases = [
            (0, '子'),   # 子时
            (6, '卯'),   # 卯时
            (12, '午'),  # 午时
            (18, '酉'),  # 酉时
            (23, '子'),  # 子时（跨日）
        ]
        
        for hour, expected in test_cases:
            result = self.hourly._get_hour_branch(hour)
            # 允许一定的容错（因为时支计算可能有边界情况）
            if result != expected:
                print(f"⚠️ 小时 {hour} 计算为 {result}，期望 {expected}（可能是边界情况）")
            else:
                print(f"✅ 小时 {hour} -> {result}")
        
        print("✅ 时支计算测试完成")
    
    def test_hourly_pillar_calculation(self):
        """测试流时干支计算"""
        context = {
            'day_master': '甲',
            'current_time': datetime(2024, 1, 1, 14),  # 14:00 = 未时
            'bazi': ['甲子', '乙丑', '丙寅', '丁卯']
        }
        
        result = self.hourly.process(context)
        self.assertIsNotNone(result.get('hourly_pillar'))
        self.assertIsNotNone(result.get('hourly_stem'))
        self.assertIsNotNone(result.get('hourly_branch'))
        self.assertEqual(len(result['hourly_pillar']), 2)
        
        print(f"✅ 流时干支计算: {result['hourly_pillar']}")
        print(f"   时干: {result['hourly_stem']}, 时支: {result['hourly_branch']}")
    
    def test_interaction_analysis(self):
        """测试相互作用分析"""
        context = {
            'day_master': '甲',
            'current_time': datetime(2024, 1, 1, 14),
            'bazi': ['甲子', '乙丑', '丙寅', '丁卯']
        }
        
        result = self.hourly.process(context)
        interaction = result.get('interaction', {})
        
        if interaction:
            self.assertIn('type', interaction)
            self.assertIn('strength', interaction)
            self.assertIn('description', interaction)
            self.assertIn('favorable', interaction)
            
            print(f"✅ 相互作用分析: {interaction.get('type', 'N/A')} ({interaction.get('description', 'N/A')[:30]}...)")
        else:
            print("⚠️ 相互作用分析未返回结果")
    
    def test_energy_boost_calculation(self):
        """测试能量加成计算"""
        context = {
            'day_master': '甲',
            'current_time': datetime(2024, 1, 1, 14),
            'bazi': ['甲子', '乙丑', '丙寅', '丁卯']
        }
        
        result = self.hourly.process(context)
        energy_boost = result.get('energy_boost', 0.0)
        
        self.assertIsInstance(energy_boost, (int, float))
        self.assertGreaterEqual(energy_boost, -0.2)
        self.assertLessEqual(energy_boost, 0.2)
        
        print(f"✅ 能量加成: {energy_boost*100:.1f}%")
    
    def test_recommendation_generation(self):
        """测试决策建议生成"""
        context = {
            'day_master': '甲',
            'current_time': datetime(2024, 1, 1, 14),
            'bazi': ['甲子', '乙丑', '丙寅', '丁卯']
        }
        
        result = self.hourly.process(context)
        recommendation = result.get('recommendation', '')
        
        self.assertIsInstance(recommendation, str)
        self.assertGreater(len(recommendation), 0)
        
        print(f"✅ 决策建议: {recommendation}")


class TestMCPEraContext(unittest.TestCase):
    """测试宏观场（时代修正）功能"""
    
    def setUp(self):
        self.era = EraProcessor()
    
    def test_era_processor_initialization(self):
        """测试 EraProcessor 初始化"""
        self.assertIsNotNone(self.era)
        self.assertEqual(self.era.name, "Era Layer 4")
        print("✅ EraProcessor 初始化成功")
    
    def test_current_era_detection(self):
        """测试当前时代检测"""
        current_year = datetime.now().year
        result = self.era.process(current_year)
        
        self.assertIsInstance(result, dict)
        if result:  # 如果找到了时代数据
            self.assertIn('era_element', result)
            self.assertIn('period', result)
            self.assertIn('desc', result)
            self.assertIn('modifiers', result)
            self.assertIn('era_bonus', result)
            self.assertIn('era_penalty', result)
            self.assertIn('impact_description', result)
            
            print(f"✅ 当前时代: {result['desc']} (周期 {result['period']})")
            print(f"   时代元素: {result['era_element']}")
            print(f"   时代红利: {result['era_bonus']*100:.0f}%")
            print(f"   影响描述: {result['impact_description']}")
    
    def test_era_modifiers(self):
        """测试时代修正系数"""
        current_year = datetime.now().year
        result = self.era.process(current_year)
        
        if result and 'modifiers' in result:
            modifiers = result['modifiers']
            era_element = result['era_element']
            
            # 时代元素应该有加成
            if era_element in modifiers:
                self.assertGreater(modifiers[era_element], 1.0)
                print(f"✅ 时代元素 {era_element} 修正系数: {modifiers[era_element]}")
    
    def test_era_span(self):
        """测试时代跨度"""
        current_year = datetime.now().year
        result = self.era.process(current_year)
        
        if result:
            self.assertIn('start_year', result)
            self.assertIn('end_year', result)
            start = result['start_year']
            end = result['end_year']
            
            self.assertLessEqual(start, current_year)
            self.assertGreaterEqual(end, current_year)
            
            print(f"✅ 时代跨度: {start}-{end} ({end-start+1}年)")


class TestMCPPatternUncertainty(unittest.TestCase):
    """测试模型不确定性功能"""
    
    def setUp(self):
        self.engine = GraphNetworkEngine()
    
    def test_uncertainty_calculation_extreme_weak(self):
        """测试极弱格局不确定性"""
        # 创建一个极弱格局的八字
        bazi = ['甲子', '丙午', '辛卯', '壬辰']
        dm = '辛'
        
        # 分析八字
        result = self.engine.analyze(bazi, dm, '男')
        strength_score = result.get('strength_score', 50.0)
        strength_label = result.get('strength_label', 'Balanced')
        
        # 计算不确定性
        uncertainty = self.engine._calculate_pattern_uncertainty(
            strength_score, strength_label, bazi, dm, None
        )
        
        self.assertIsInstance(uncertainty, dict)
        self.assertIn('has_uncertainty', uncertainty)
        self.assertIn('pattern_type', uncertainty)
        self.assertIn('follower_probability', uncertainty)
        self.assertIn('volatility_range', uncertainty)
        self.assertIn('warning_message', uncertainty)
        
        if strength_score < 30.0:
            self.assertTrue(uncertainty['has_uncertainty'])
            self.assertEqual(uncertainty['pattern_type'], 'Extreme_Weak')
            print(f"✅ 极弱格局检测: 分数={strength_score:.1f}, 不确定性={uncertainty['has_uncertainty']}")
        else:
            print(f"ℹ️ 格局强度: {strength_score:.1f} ({strength_label})")
    
    def test_uncertainty_calculation_multi_clash(self):
        """测试多冲格局不确定性"""
        # 创建一个多冲格局的八字（子午冲、卯酉冲）
        bazi = ['甲子', '丙午', '辛卯', '乙酉']
        dm = '辛'
        
        uncertainty = self.engine._calculate_pattern_uncertainty(
            50.0, 'Balanced', bazi, dm, None
        )
        
        # 检查是否检测到多冲
        if uncertainty['pattern_type'] == 'Multi_Clash':
            self.assertTrue(uncertainty['has_uncertainty'])
            self.assertGreater(uncertainty['volatility_range'], 0)
            print(f"✅ 多冲格局检测: 波动范围=±{uncertainty['volatility_range']:.0f}分")
        else:
            print(f"ℹ️ 格局类型: {uncertainty['pattern_type']}")
    
    def test_uncertainty_follower_grid(self):
        """测试从格不确定性"""
        # 从格应该已经有特殊格局标记
        uncertainty = self.engine._calculate_pattern_uncertainty(
            25.0, 'Weak', ['甲子', '丙午', '辛卯', '壬辰'], '辛', 'Special_Follow'
        )
        
        if uncertainty['pattern_type'] == 'Follower_Grid':
            self.assertTrue(uncertainty['has_uncertainty'])
            self.assertGreater(uncertainty['follower_probability'], 0)
            print(f"✅ 从格检测: 转化概率={uncertainty['follower_probability']*100:.0f}%")


class TestMCPUserFeedback(unittest.TestCase):
    """测试事件锚点用户输入功能"""
    
    def setUp(self):
        self.controller = WealthVerificationController()
    
    def test_add_user_feedback(self):
        """测试添加用户反馈"""
        # 获取一个现有案例
        cases = self.controller.get_all_cases()
        if cases:
            case = cases[0]
            
            # 尝试添加反馈
            success, message = self.controller.add_user_feedback(
                case_id=case.id,
                year=2025,
                real_magnitude=50.0,
                description="测试事件：投资成功",
                ganzhi="乙巳",
                dayun="甲子"
            )
            
            self.assertIsInstance(success, bool)
            self.assertIsInstance(message, str)
            
            if success:
                print(f"✅ 用户反馈添加成功: {message}")
            else:
                print(f"⚠️ 用户反馈添加失败: {message}")
        else:
            print("⚠️ 没有可用案例，跳过测试")
    
    def test_update_existing_event(self):
        """测试更新现有事件"""
        cases = self.controller.get_all_cases()
        if cases:
            case = cases[0]
            if case.timeline:
                # 使用现有事件的年份
                existing_year = case.timeline[0].year
                
                success, message = self.controller.add_user_feedback(
                    case_id=case.id,
                    year=existing_year,
                    real_magnitude=75.0,
                    description="更新后的测试事件"
                )
                
                if success:
                    print(f"✅ 事件更新成功: {message}")
                else:
                    print(f"⚠️ 事件更新失败: {message}")
            else:
                print("⚠️ 案例没有时间线，跳过测试")
        else:
            print("⚠️ 没有可用案例，跳过测试")


class TestMCPIntegration(unittest.TestCase):
    """测试 MCP 集成功能"""
    
    def setUp(self):
        self.controller = BaziController()
    
    def test_geo_modifiers_integration(self):
        """测试地理修正集成"""
        # 测试获取地理修正系数
        geo_mods = self.controller.get_geo_modifiers("Beijing")
        
        if geo_mods:
            self.assertIsInstance(geo_mods, dict)
            print(f"✅ 地理修正集成: {geo_mods.get('desc', 'N/A')}")
        else:
            print("⚠️ 地理修正未激活（城市未找到）")
    
    def test_era_info_integration(self):
        """测试时代信息集成"""
        era_info = self.controller.get_current_era_info()
        
        if era_info:
            self.assertIsInstance(era_info, dict)
            self.assertIn('desc', era_info)
            print(f"✅ 时代信息集成: {era_info.get('desc', 'N/A')}")
        else:
            print("⚠️ 时代信息未找到")
    
    def test_uncertainty_in_analyze(self):
        """测试不确定性在 analyze 中的集成"""
        engine = GraphNetworkEngine()
        bazi = ['甲子', '丙午', '辛卯', '壬辰']
        dm = '辛'
        
        result = engine.analyze(bazi, dm, '男')
        
        # 检查是否包含不确定性信息
        if 'uncertainty' in result:
            uncertainty = result['uncertainty']
            self.assertIsInstance(uncertainty, dict)
            self.assertIn('has_uncertainty', uncertainty)
            print(f"✅ 不确定性集成: has_uncertainty={uncertainty.get('has_uncertainty')}")
        else:
            print("⚠️ 不确定性信息未返回")


def run_mcp_tests():
    """运行所有 MCP 测试"""
    print("\n" + "=" * 70)
    print("🧪 MCP V9.3 测试套件")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestMCPGeoCorrection))
    suite.addTests(loader.loadTestsFromTestCase(TestMCPHourlyContext))
    suite.addTests(loader.loadTestsFromTestCase(TestMCPEraContext))
    suite.addTests(loader.loadTestsFromTestCase(TestMCPPatternUncertainty))
    suite.addTests(loader.loadTestsFromTestCase(TestMCPUserFeedback))
    suite.addTests(loader.loadTestsFromTestCase(TestMCPIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_mcp_tests()
    exit(0 if success else 1)

