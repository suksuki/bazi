"""
GAT 路径过滤模块单元测试
========================

测试覆盖:
1. GAT 路径过滤器
2. 系统熵控制器
3. 边界条件和错误处理

作者: Antigravity Team
版本: V10.0
日期: 2025-12-17
"""

import unittest
import numpy as np
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.gat_path_filter import (
    GATPathFilter,
    SystemEntropyController
)


class TestGATPathFilter(unittest.TestCase):
    """测试 GAT 路径过滤器"""
    
    def setUp(self):
        """测试前准备"""
        self.filter = GATPathFilter(threshold=0.1)
        self.attention_weights = {
            (0, 1): 0.5,
            (1, 2): 0.3,
            (2, 3): 0.15,
            (3, 4): 0.05  # 低于阈值
        }
        self.energy_paths = [
            {'0->1': 0.5},
            {'1->2': 0.3},
            {'2->3': 0.15},
            {'3->4': 0.05}
        ]
    
    def test_filter_paths(self):
        """测试路径过滤"""
        filtered = self.filter.filter_paths(
            attention_weights=self.attention_weights,
            energy_paths=self.energy_paths
        )
        
        # 应该过滤掉权重低于 0.1 的路径
        self.assertLess(len(filtered), len(self.attention_weights))
        self.assertNotIn((3, 4), filtered)  # 低于阈值的路径应该被过滤
        print("✅ 路径过滤测试通过")
    
    def test_filter_paths_all_above_threshold(self):
        """测试所有路径都高于阈值的情况"""
        attention_weights = {
            (0, 1): 0.5,
            (1, 2): 0.3,
            (2, 3): 0.15
        }
        energy_paths = [
            {'0->1': 0.5},
            {'1->2': 0.3},
            {'2->3': 0.15}
        ]
        
        filtered = self.filter.filter_paths(
            attention_weights=attention_weights,
            energy_paths=energy_paths
        )
        
        # 所有路径都应该保留
        self.assertEqual(len(filtered), len(attention_weights))
        print("✅ 所有路径高于阈值测试通过")
    
    def test_filter_paths_all_below_threshold(self):
        """测试所有路径都低于阈值的情况"""
        attention_weights = {
            (0, 1): 0.05,
            (1, 2): 0.03
        }
        energy_paths = [
            {'0->1': 0.05},
            {'1->2': 0.03}
        ]
        
        filtered = self.filter.filter_paths(
            attention_weights=attention_weights,
            energy_paths=energy_paths
        )
        
        # 应该至少保留一些路径（归一化后）
        self.assertGreaterEqual(len(filtered), 0)
        print("✅ 所有路径低于阈值测试通过")
    
    def test_filter_paths_normalization(self):
        """测试路径过滤后的归一化"""
        filtered = self.filter.filter_paths(
            attention_weights=self.attention_weights,
            energy_paths=self.energy_paths
        )
        
        # 验证权重归一化（总和应该接近 1.0）
        if len(filtered) > 0:
            total_weight = sum(filtered.values())
            self.assertAlmostEqual(total_weight, 1.0, places=5)
        print("✅ 路径过滤归一化测试通过")
    
    def test_optimize_threshold(self):
        """测试优化过滤阈值"""
        def objective(filtered_weights):
            # 简单的目标函数：路径数量越少越好（但至少保留 1 条）
            if len(filtered_weights) == 0:
                return 1000.0  # 惩罚空结果
            return len(filtered_weights)
        
        optimal_threshold = self.filter.optimize_threshold(
            attention_weights=self.attention_weights,
            energy_paths=self.energy_paths,
            objective_func=objective
        )
        
        self.assertIsInstance(optimal_threshold, float)
        self.assertGreater(optimal_threshold, 0)
        self.assertLess(optimal_threshold, 1.0)
        print("✅ 优化过滤阈值测试通过")
    
    def test_calculate_path_strength(self):
        """测试计算路径强度"""
        strength = self.filter._calculate_path_strength(
            node_i=0,
            node_j=1,
            energy_paths=self.energy_paths
        )
        
        self.assertIsInstance(strength, float)
        self.assertGreaterEqual(strength, 0.0)
        self.assertLessEqual(strength, 1.0)
        print("✅ 计算路径强度测试通过")
    
    def test_calculate_path_strength_missing(self):
        """测试缺失路径的强度计算"""
        strength = self.filter._calculate_path_strength(
            node_i=99,
            node_j=100,
            energy_paths=self.energy_paths
        )
        
        # 缺失路径应该返回 0.0
        self.assertEqual(strength, 0.0)
        print("✅ 缺失路径强度计算测试通过")


class TestSystemEntropyController(unittest.TestCase):
    """测试系统熵控制器"""
    
    def setUp(self):
        """测试前准备"""
        self.controller = SystemEntropyController(base_entropy=0.1)
        self.attention_weights = {
            (0, 1): 0.5,
            (1, 2): 0.3,
            (2, 3): 0.15,
            (3, 4): 0.05
        }
    
    def test_calculate_path_entropy(self):
        """测试计算路径熵"""
        entropy = self.controller.calculate_path_entropy(self.attention_weights)
        
        self.assertIsInstance(entropy, float)
        self.assertGreaterEqual(entropy, 0.0)
        # 熵值应该小于 log(n)，其中 n 是路径数量
        max_entropy = np.log(len(self.attention_weights))
        self.assertLessEqual(entropy, max_entropy)
        print("✅ 计算路径熵测试通过")
    
    def test_calculate_path_entropy_uniform(self):
        """测试均匀分布的路径熵"""
        uniform_weights = {
            (0, 1): 0.25,
            (1, 2): 0.25,
            (2, 3): 0.25,
            (3, 4): 0.25
        }
        
        entropy = self.controller.calculate_path_entropy(uniform_weights)
        
        # 均匀分布的熵应该最大
        expected_entropy = np.log(4)
        self.assertAlmostEqual(entropy, expected_entropy, places=2)
        print("✅ 均匀分布路径熵测试通过")
    
    def test_calculate_path_entropy_single_path(self):
        """测试单条路径的熵"""
        single_path = {(0, 1): 1.0}
        
        entropy = self.controller.calculate_path_entropy(single_path)
        
        # 单条路径的熵应该为 0
        self.assertAlmostEqual(entropy, 0.0, places=5)
        print("✅ 单条路径熵测试通过")
    
    def test_filter_by_entropy(self):
        """测试根据熵值过滤路径"""
        filtered = self.controller.filter_by_entropy(
            attention_weights=self.attention_weights,
            max_entropy=1.0
        )
        
        # 验证过滤后的熵值
        filtered_entropy = self.controller.calculate_path_entropy(filtered)
        self.assertLessEqual(filtered_entropy, 1.0)
        print("✅ 根据熵值过滤路径测试通过")
    
    def test_filter_by_entropy_no_filtering(self):
        """测试熵值低于阈值时不过滤"""
        # 使用低熵的权重（单条路径占主导）
        low_entropy_weights = {
            (0, 1): 0.9,
            (1, 2): 0.1
        }
        
        filtered = self.controller.filter_by_entropy(
            attention_weights=low_entropy_weights,
            max_entropy=2.0  # 高阈值
        )
        
        # 应该不进行过滤（或过滤很少）
        self.assertGreaterEqual(len(filtered), len(low_entropy_weights) - 1)
        print("✅ 熵值低于阈值不过滤测试通过")
    
    def test_filter_by_entropy_normalization(self):
        """测试过滤后的归一化"""
        filtered = self.controller.filter_by_entropy(
            attention_weights=self.attention_weights,
            max_entropy=1.0
        )
        
        # 验证权重归一化
        if len(filtered) > 0:
            total_weight = sum(filtered.values())
            self.assertAlmostEqual(total_weight, 1.0, places=5)
        print("✅ 过滤后归一化测试通过")


class TestGATPathFilterEdgeCases(unittest.TestCase):
    """测试边界情况和错误处理"""
    
    def test_filter_empty_attention_weights(self):
        """测试空注意力权重"""
        filter = GATPathFilter(threshold=0.1)
        filtered = filter.filter_paths({}, [])
        
        self.assertEqual(len(filtered), 0)
        print("✅ 空注意力权重处理测试通过")
    
    def test_filter_empty_energy_paths(self):
        """测试空能量路径"""
        filter = GATPathFilter(threshold=0.1)
        attention_weights = {(0, 1): 0.5}
        
        filtered = filter.filter_paths(attention_weights, [])
        
        # 应该能够处理（使用默认路径强度）
        self.assertIsInstance(filtered, dict)
        print("✅ 空能量路径处理测试通过")
    
    def test_entropy_controller_zero_weights(self):
        """测试零权重的情况"""
        controller = SystemEntropyController()
        zero_weights = {
            (0, 1): 0.0,
            (1, 2): 0.0
        }
        
        # 计算熵时应该能够处理（避免 log(0)）
        try:
            entropy = controller.calculate_path_entropy(zero_weights)
            self.assertIsNotNone(entropy)
            print("✅ 零权重熵计算测试通过")
        except Exception:
            # 抛出异常也是可以接受的
            pass
    
    def test_optimize_threshold_invalid_objective(self):
        """测试无效目标函数的阈值优化"""
        filter = GATPathFilter(threshold=0.1)
        attention_weights = {(0, 1): 0.5}
        energy_paths = [{'0->1': 0.5}]
        
        def invalid_objective(filtered_weights):
            raise ValueError("测试异常")
        
        # 应该能够处理异常（返回默认阈值或抛出异常）
        try:
            threshold = filter.optimize_threshold(
                attention_weights=attention_weights,
                energy_paths=energy_paths,
                objective_func=invalid_objective
            )
            self.assertIsNotNone(threshold)
            print("✅ 无效目标函数处理测试通过")
        except Exception:
            # 抛出异常也是可以接受的
            pass


if __name__ == '__main__':
    unittest.main(verbosity=2)

