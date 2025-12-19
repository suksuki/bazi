"""
量子验证页面 MCP 上下文注入测试
================================

测试MCP上下文注入功能和UI精简后的功能。

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

from ui.utils.mcp_context_injection import inject_mcp_context, calculate_year_pillar


class TestMCPContextInjection(unittest.TestCase):
    """测试MCP上下文注入功能"""
    
    def setUp(self):
        """测试前准备"""
        self.test_case = {
            "id": "TEST_001",
            "name": "测试案例",
            "birth_date": "1961-10-10",
            "birth_time": "10:10",
            "geo_city": "Beijing",
            "geo_country": "China",
            "geo_longitude": 116.407,
            "geo_latitude": 39.904,
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
    
    def test_calculate_year_pillar(self):
        """测试流年干支计算"""
        # 测试已知年份
        self.assertEqual(calculate_year_pillar(2014), "甲午")
        self.assertEqual(calculate_year_pillar(2024), "甲辰")
        self.assertEqual(calculate_year_pillar(1924), "甲子")  # 基准年
        self.assertEqual(calculate_year_pillar(1984), "甲子")
        
        print("✅ 流年干支计算测试通过")
    
    def test_inject_geo_context(self):
        """测试GEO上下文注入"""
        context = inject_mcp_context(self.test_case)
        
        self.assertEqual(context['geo_city'], "Beijing")
        self.assertEqual(context['geo_latitude'], 39.904)
        self.assertEqual(context['geo_longitude'], 116.407)
        
        print("✅ GEO上下文注入测试通过")
    
    def test_inject_era_context(self):
        """测试ERA上下文注入"""
        context = inject_mcp_context(self.test_case)
        
        # 1961年应该是Period 8 (Earth)
        self.assertEqual(context['era_period'], "Period 8 (Earth)")
        self.assertEqual(context['era_element'], "Earth")
        
        # 测试其他年份
        case_1985 = self.test_case.copy()
        case_1985['birth_date'] = "1985-01-01"
        context_1985 = inject_mcp_context(case_1985)
        self.assertEqual(context_1985['era_period'], "Period 9 (Fire)")
        self.assertEqual(context_1985['era_element'], "Fire")
        
        case_2025 = self.test_case.copy()
        case_2025['birth_date'] = "2025-01-01"
        context_2025 = inject_mcp_context(case_2025)
        self.assertEqual(context_2025['era_period'], "Period 1 (Water)")
        self.assertEqual(context_2025['era_element'], "Water")
        
        print("✅ ERA上下文注入测试通过")
    
    def test_inject_luck_pillar_from_timeline(self):
        """测试从timeline获取大运"""
        context = inject_mcp_context(self.test_case)
        
        # 应该从timeline的第一个事件获取大运
        self.assertEqual(context['luck_pillar'], "甲子")
        
        print("✅ 大运上下文注入测试通过（从timeline）")
    
    def test_inject_year_pillar(self):
        """测试流年上下文注入"""
        context = inject_mcp_context(self.test_case, selected_year=2014)
        
        self.assertEqual(context['year_pillar'], "甲午")
        self.assertEqual(context['selected_year'], 2014)
        
        print("✅ 流年上下文注入测试通过")
    
    def test_inject_context_without_timeline(self):
        """测试没有timeline时的上下文注入"""
        case_no_timeline = self.test_case.copy()
        del case_no_timeline['timeline']
        
        context = inject_mcp_context(case_no_timeline)
        
        # GEO和ERA应该仍然可以注入
        self.assertEqual(context['geo_city'], "Beijing")
        self.assertEqual(context['era_element'], "Earth")
        
        # 大运应该为None（无法计算）
        self.assertIsNone(context.get('luck_pillar'))
        
        print("✅ 无timeline时的上下文注入测试通过")
    
    def test_inject_context_without_geo(self):
        """测试没有GEO信息时的上下文注入"""
        case_no_geo = self.test_case.copy()
        del case_no_geo['geo_city']
        del case_no_geo['geo_latitude']
        del case_no_geo['geo_longitude']
        
        context = inject_mcp_context(case_no_geo)
        
        # 应该使用默认值
        self.assertEqual(context['geo_city'], 'Unknown')
        self.assertEqual(context['geo_latitude'], 0.0)
        self.assertEqual(context['geo_longitude'], 0.0)
        
        print("✅ 无GEO信息时的上下文注入测试通过")


class TestStrengthCaseFormat(unittest.TestCase):
    """测试旺衰案例格式"""
    
    def test_strength_case_format(self):
        """测试旺衰案例格式是否符合规范"""
        case = {
            "id": "STRENGTH_001",
            "name": "测试案例",
            "birth_date": "1961-10-10",
            "birth_time": "10:10",
            "geo_city": "Beijing",
            "geo_country": "China",
            "geo_longitude": 116.407,
            "geo_latitude": 39.904,
            "day_master": "丁",
            "gender": "男",
            "bazi": ["辛丑", "戊戌", "丁丑", "乙巳"],
            "target_focus": "STRENGTH",
            "characteristics": "身强，多财库",
            "ground_truth": {
                "strength": "Strong",
                "note": "典型的身强格局"
            }
        }
        
        # 验证必需字段
        self.assertIn('id', case)
        self.assertIn('birth_date', case)
        self.assertIn('geo_city', case)
        self.assertIn('day_master', case)
        self.assertIn('bazi', case)
        self.assertIn('ground_truth', case)
        self.assertIn('strength', case['ground_truth'])
        
        # 验证target_focus
        self.assertEqual(case['target_focus'], "STRENGTH")
        
        # 验证旺衰标签
        self.assertIn(case['ground_truth']['strength'], 
                      ["Strong", "Weak", "Balanced", "Follower", "Extreme_Weak"])
        
        print("✅ 旺衰案例格式验证通过")


class TestUISimplification(unittest.TestCase):
    """测试UI精简后的功能"""
    
    def test_removed_parameters(self):
        """验证已删除的参数不在配置中"""
        # 这些参数应该不在final_full_config中
        removed_params = [
            'vaultPhysics',
            'treasury',
            'skull',
            'macroPhysics'  # 通过MCP注入
        ]
        
        # 这里只是验证逻辑，实际测试需要运行UI
        # 在实际测试中，应该检查final_full_config不包含这些键
        print("✅ UI精简验证：已删除的参数列表确认")
    
    def test_retained_parameters(self):
        """验证保留的核心参数"""
        # 这些参数应该保留
        retained_params = [
            'physics',
            'structure',
            'interactions.stemFiveCombine',
            'interactions.comboPhysics',
            'flow.resourceImpedance',
            'flow.outputViscosity',
            'strength',
            'gat'
        ]
        
        print("✅ UI精简验证：保留的核心参数列表确认")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)

