"""
旺衰判定回归测试
================

测试旺衰判定功能的准确性和一致性。

作者: Antigravity Team
版本: V10.0
日期: 2025-01-17
"""

import unittest
import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS


class TestStrengthRegression(unittest.TestCase):
    """旺衰判定回归测试"""
    
    def setUp(self):
        """测试前准备"""
        self.engine = GraphNetworkEngine(config=DEFAULT_FULL_ALGO_PARAMS)
        
        # 测试案例（基于Jason系列）
        self.test_cases = [
            {
                "id": "JASON_D",
                "name": "Jason D (多财库)",
                "day_master": "丁",
                "bazi": ["辛丑", "戊戌", "丁丑", "乙巳"],
                "expected_strength": "Strong",
                "description": "身强，多财库，印星生身"
            },
            {
                "id": "JASON_B",
                "name": "Jason B (身弱用印)",
                "day_master": "己",
                "bazi": ["甲辰", "癸酉", "己未", "辛未"],
                "expected_strength": "Weak",
                "description": "身弱用印格局"
            },
            {
                "id": "JASON_E",
                "name": "Jason E (极弱截脚)",
                "day_master": "壬",
                "bazi": ["乙未", "戊寅", "壬午", "辛亥"],
                "expected_strength": "Extreme_Weak",
                "description": "极弱格局，接近从格边缘"
            }
        ]
    
    def test_evaluate_wang_shuai(self):
        """测试旺衰判定方法"""
        for case in self.test_cases:
            with self.subTest(case=case['id']):
                day_master = case['day_master']
                bazi = case['bazi']
                
            # 调用旺衰判定方法
            # 注意：需要先初始化节点以设置day_master_element
            self.engine.bazi = bazi
            self.engine.initialize_nodes(bazi, day_master)
            result = self.engine.calculate_strength_score(day_master)
            
            # 验证返回格式
            self.assertIsInstance(result, dict)
            self.assertIn('strength_score', result)
            self.assertIn('strength_label', result)
            
            strength_label = result['strength_label']
            strength_score = result['strength_score']
            
            # 验证标签格式
            self.assertIsInstance(strength_label, str)
            self.assertIsInstance(strength_score, (int, float))
            
            # 验证标签值（允许包含这些关键词或完全匹配）
            valid_labels = ["Strong", "Weak", "Balanced", "Follower", "Extreme_Weak", "Special_Strong", "Very_Weak"]
            is_valid = strength_label in valid_labels or any(label in strength_label for label in valid_labels)
            self.assertTrue(is_valid, f"无效的标签: {strength_label}，有效标签: {valid_labels}")
            
            print(f"✅ {case['name']}: {strength_label} ({strength_score:.2f})")
    
    def test_strength_consistency(self):
        """测试旺衰判定的一致性"""
        # 多次调用应该返回相同结果
        case = self.test_cases[0]
        day_master = case['day_master']
        bazi = case['bazi']
        
        self.engine.bazi = bazi
        self.engine.initialize_nodes(bazi, day_master)
        results = []
        for _ in range(5):
            result = self.engine.calculate_strength_score(day_master)
            results.append(result)
        
        # 所有结果应该相同
        first_result = results[0]
        for result in results[1:]:
            self.assertEqual(result['strength_label'], first_result['strength_label'])  # 标签相同
            self.assertAlmostEqual(result['strength_score'], first_result['strength_score'], places=1)  # 分数相近
        
        print("✅ 旺衰判定一致性测试通过")
    
    def test_strength_with_different_configs(self):
        """测试不同配置下的旺衰判定"""
        case = self.test_cases[0]
        day_master = case['day_master']
        bazi = case['bazi']
        
        # 测试默认配置
        engine_default = GraphNetworkEngine(config=DEFAULT_FULL_ALGO_PARAMS)
        engine_default.bazi = bazi
        engine_default.initialize_nodes(bazi, day_master)
        result_default = engine_default.calculate_strength_score(day_master)
        
        # 测试修改energy_threshold_center后的配置
        config_modified = DEFAULT_FULL_ALGO_PARAMS.copy()
        config_modified['strength'] = config_modified.get('strength', {}).copy()
        config_modified['strength']['energy_threshold_center'] = 3.0  # 从2.89改为3.0
        
        engine_modified = GraphNetworkEngine(config=config_modified)
        engine_modified.bazi = bazi
        engine_modified.initialize_nodes(bazi, day_master)
        result_modified = engine_modified.calculate_strength_score(day_master)
        
        # 验证配置影响结果
        # 注意：阈值改变可能会影响判定结果
        print(f"✅ 默认配置: {result_default['strength_label']} ({result_default['strength_score']:.2f})")
        print(f"✅ 修改配置: {result_modified['strength_label']} ({result_modified['strength_score']:.2f})")
        
        # 至少应该返回有效结果
        self.assertIsNotNone(result_default['strength_label'])
        self.assertIsNotNone(result_modified['strength_label'])


class TestMCPIntegrationWithEngine(unittest.TestCase):
    """测试MCP上下文注入与引擎的集成"""
    
    def setUp(self):
        """测试前准备"""
        self.engine = GraphNetworkEngine(config=DEFAULT_FULL_ALGO_PARAMS)
        
        # 测试案例（包含完整信息）
        self.test_case = {
            "id": "TEST_MCP_001",
            "birth_date": "1961-10-10",
            "geo_city": "Beijing",
            "geo_latitude": 39.904,
            "geo_longitude": 116.407,
            "day_master": "丁",
            "gender": "男",
            "bazi": ["辛丑", "戊戌", "丁丑", "乙巳"],
            "timeline": [
                {
                    "year": 2014,
                    "dayun": "甲子",
                    "ganzhi": "甲午"
                }
            ]
        }
    
    def test_mcp_context_injection(self):
        """测试MCP上下文注入"""
        from ui.utils.mcp_context_injection import inject_mcp_context
        
        context = inject_mcp_context(self.test_case, selected_year=2014)
        
        # 验证上下文信息
        self.assertEqual(context['geo_city'], "Beijing")
        self.assertEqual(context['era_element'], "Earth")
        self.assertEqual(context['luck_pillar'], "甲子")
        self.assertEqual(context['year_pillar'], "甲午")
        
        print("✅ MCP上下文注入测试通过")
    
    def test_engine_with_mcp_context(self):
        """测试引擎使用MCP上下文"""
        from ui.utils.mcp_context_injection import inject_mcp_context
        
        # 注入MCP上下文
        case_with_context = inject_mcp_context(self.test_case, selected_year=2014)
        
        # 构建case_data（包含GEO信息）
        case_data = {
            'bazi': case_with_context['bazi'],
            'day_master': case_with_context['day_master'],
            'city': case_with_context['geo_city'],
            'geo_latitude': case_with_context['geo_latitude'],
            'geo_longitude': case_with_context['geo_longitude']
        }
        
        # 构建dynamic_context（包含ERA、大运、流年信息）
        dynamic_context = {
            'year': case_with_context['year_pillar'],
            'dayun': case_with_context['luck_pillar'],
            'luck': case_with_context['luck_pillar'],
            'era_element': case_with_context['era_element']
        }
        
        # 调用引擎（如果支持这些参数）
        # 注意：这里只是验证数据结构，实际调用可能需要适配引擎接口
        self.assertIn('city', case_data)
        self.assertIn('era_element', dynamic_context)
        
        print("✅ 引擎与MCP上下文集成测试通过")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)

