"""
QuantumLabController 单元测试
测试量子验证页面的Controller层功能
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from controllers.quantum_lab_controller import QuantumLabController
from core.bazi_profile import VirtualBaziProfile


class TestQuantumLabController(unittest.TestCase):
    """QuantumLabController 测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.controller = QuantumLabController()
        self.test_case = {
            'id': 'TEST_001',
            'name': '测试案例',
            'bazi': ['甲子', '丙寅', '庚辰', '戊午'],
            'day_master': '庚',
            'gender': '男',
            'birth_date': '2000-01-01',
            'birth_time': '12:00'
        }
    
    def test_controller_initialization(self):
        """测试Controller初始化"""
        self.assertIsNotNone(self.controller)
        self.assertIsNotNone(self.controller.quantum_engine)
        # graph_engine 通过 engine 属性访问（lazy initialization）
        self.assertIsNotNone(self.controller.engine)
        print("✅ Controller初始化测试通过")
    
    def test_create_profile_from_case(self):
        """测试从案例创建Profile"""
        profile = self.controller.create_profile_from_case(
            self.test_case, 
            "癸卯"
        )
        
        self.assertIsInstance(profile, VirtualBaziProfile)
        self.assertEqual(profile.day_master, '庚')
        self.assertEqual(profile.gender, 1)  # 男性 = 1
        print("✅ create_profile_from_case 测试通过")
    
    def test_create_profile_from_case_female(self):
        """测试女性案例"""
        female_case = self.test_case.copy()
        female_case['gender'] = '女'
        
        profile = self.controller.create_profile_from_case(
            female_case,
            "癸卯"
        )
        
        self.assertEqual(profile.gender, 0)  # 女性 = 0
        print("✅ 女性案例测试通过")
    
    def test_inject_mcp_context(self):
        """测试MCP上下文注入"""
        case_with_context = self.controller.inject_mcp_context(
            self.test_case,
            selected_year=2024
        )
        
        self.assertIsInstance(case_with_context, dict)
        # 检查是否包含MCP相关字段（具体字段取决于inject_mcp_context的实现）
        print("✅ MCP上下文注入测试通过")
    
    def test_get_luck_pillar_from_mcp(self):
        """测试从MCP上下文获取大运"""
        mcp_context = {
            'luck_pillar': '甲子'
        }
        
        luck_pillar = self.controller.get_luck_pillar(
            self.test_case,
            target_year=2024,
            mcp_context=mcp_context
        )
        
        self.assertEqual(luck_pillar, '甲子')
        print("✅ 从MCP获取大运测试通过")
    
    @patch('controllers.quantum_lab_controller.GraphNetworkEngine')
    def test_calculate_strength_score(self, mock_engine_class):
        """测试计算旺衰分数"""
        # Mock engine
        mock_engine = MagicMock()
        mock_engine.calculate_strength_score.return_value = {
            'strength_score': 65.5,
            'strength_label': 'Strong',
            'energy_ratio': 2.8
        }
        mock_engine_class.return_value = mock_engine
        
        controller = QuantumLabController()
        controller.graph_engine = mock_engine
        
        result = controller.calculate_strength_score(
            case=self.test_case,
            luck_pillar='癸卯',
            year_pillar='甲辰',
            geo_context={'city': 'Beijing'},
            era_context={'element': 'Fire'}
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('strength_score', result)
        self.assertIn('strength_label', result)
        print("✅ calculate_strength_score 测试通过")
    
    def test_evaluate_wang_shuai(self):
        """测试评估旺衰"""
        bazi_list = ['甲子', '丙寅', '庚辰', '戊午']
        day_master = '庚'
        
        result = self.controller.evaluate_wang_shuai(day_master, bazi_list)
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)  # (label, score)
        print(f"✅ evaluate_wang_shuai 测试通过: {result}")
    
    def test_calculate_year_pillar(self):
        """测试计算流年干支"""
        year_pillar = self.controller.calculate_year_pillar(2024)
        
        self.assertIsInstance(year_pillar, str)
        self.assertEqual(len(year_pillar), 2)  # 干支应为2个字符
        print(f"✅ calculate_year_pillar 测试通过: {year_pillar}")
    
    def test_update_config(self):
        """测试更新配置"""
        new_params = {
            'strength': {
                'energy_threshold_center': 3.0,
                'phase_transition_width': 12.0
            }
        }
        
        # 应该能正常执行而不报错
        try:
            self.controller.update_config(new_params)
            print("✅ update_config 测试通过")
        except Exception as e:
            self.fail(f"update_config 失败: {e}")


class TestQuantumLabControllerIntegration(unittest.TestCase):
    """QuantumLabController 集成测试"""
    
    def setUp(self):
        """测试前准备"""
        self.controller = QuantumLabController()
        self.test_case = {
            'id': 'INTEGRATION_TEST_001',
            'name': '集成测试案例',
            'bazi': ['辛卯', '丁酉', '庚午', '丙子'],
            'day_master': '庚',
            'gender': '男',
            'birth_date': '1711-09-25',
            'birth_time': '00:00'
        }
    
    def test_full_workflow(self):
        """测试完整工作流程"""
        # 1. 注入MCP上下文
        case_with_context = self.controller.inject_mcp_context(
            self.test_case,
            selected_year=1711
        )
        
        # 2. 获取大运
        luck_pillar = self.controller.get_luck_pillar(
            case_with_context,
            target_year=1711
        )
        
        # 3. 创建Profile
        profile = self.controller.create_profile_from_case(
            case_with_context,
            luck_pillar
        )
        
        # 4. 计算流年干支
        year_pillar = self.controller.calculate_year_pillar(1711)
        
        # 5. 评估旺衰
        ws_label, ws_score = self.controller.evaluate_wang_shuai(
            profile.day_master,
            [profile.pillars['year'], profile.pillars['month'], 
             profile.pillars['day'], profile.pillars['hour']]
        )
        
        # 验证结果
        self.assertIsNotNone(profile)
        self.assertIsNotNone(luck_pillar)
        self.assertIsNotNone(year_pillar)
        self.assertIsNotNone(ws_label)
        self.assertIsNotNone(ws_score)
        
        print(f"✅ 完整工作流程测试通过")
        print(f"   大运: {luck_pillar}, 流年: {year_pillar}")
        print(f"   旺衰判定: {ws_label}, 分数: {ws_score}")


if __name__ == '__main__':
    unittest.main()

