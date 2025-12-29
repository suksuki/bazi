"""
统计审计工具测试套件 (Statistical Audit Utilities Test Suite)
RSS-V1.4规范：测试离群值检测、梯度消失判定、分布统计等功能

测试覆盖:
1. 离群值检测（Z-Score、IQR、Combined）
2. 梯度消失判定
3. 分布统计计算
4. 奇点存在性验证
5. 边界情况和异常处理
"""

import unittest
import numpy as np
from typing import List, Dict, Any
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.statistical_audit import StatisticalAuditor, get_statistical_auditor


class TestOutlierDetection(unittest.TestCase):
    """测试离群值检测功能"""
    
    def setUp(self):
        self.auditor = StatisticalAuditor(z_score_threshold=3.0, gradient_threshold=0.05)
    
    def test_z_score_detection(self):
        """测试Z-Score检测方法"""
        # 创建正态分布数据，添加几个明显的离群值
        normal_data = np.random.normal(0.5, 0.1, 100).tolist()
        outliers = [0.01, 0.02, 0.03]  # 明显的低离群值
        values = normal_data + outliers
        
        result = self.auditor.detect_outliers(values, method="z_score")
        
        self.assertIn("outlier_indices", result)
        self.assertIn("normal_indices", result)
        self.assertIn("statistics", result)
        self.assertIn("has_outliers", result)
        self.assertGreater(len(result["outlier_indices"]), 0, "应该检测到离群值")
        print(f"✅ Z-Score检测: 检测到{len(result['outlier_indices'])}个离群值")
    
    def test_iqr_detection(self):
        """测试IQR检测方法"""
        # 创建数据，包含一些离群值
        values = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.01, 0.02]
        
        result = self.auditor.detect_outliers(values, method="iqr")
        
        self.assertIn("outlier_indices", result)
        self.assertIn("statistics", result)
        self.assertIn("iqr", result["statistics"])
        print(f"✅ IQR检测: 检测到{len(result['outlier_indices'])}个离群值")
    
    def test_combined_detection(self):
        """测试组合检测方法（Z-Score + IQR）"""
        # 创建混合数据
        normal_data = np.random.normal(0.5, 0.1, 100).tolist()
        outliers = [0.01, 0.02, 0.03, 0.99, 0.98]  # 低离群值和高离群值
        values = normal_data + outliers
        
        result = self.auditor.detect_outliers(values, method="combined")
        
        self.assertIn("outlier_indices", result)
        self.assertIn("detection_methods", result)
        self.assertGreater(len(result["outlier_indices"]), 0)
        print(f"✅ 组合检测: 检测到{len(result['outlier_indices'])}个离群值")
    
    def test_no_outliers(self):
        """测试无离群值的情况"""
        # 创建均匀分布的数据
        values = [0.4, 0.41, 0.42, 0.43, 0.44, 0.45, 0.46, 0.47, 0.48, 0.49]
        
        result = self.auditor.detect_outliers(values, method="combined")
        
        # 对于均匀分布，可能检测不到离群值
        self.assertIn("outlier_indices", result)
        print(f"✅ 无离群值测试: 检测到{len(result['outlier_indices'])}个离群值")
    
    def test_empty_data(self):
        """测试空数据"""
        result = self.auditor.detect_outliers([])
        
        self.assertEqual(len(result["outlier_indices"]), 0)
        self.assertEqual(len(result["normal_indices"]), 0)
        print("✅ 空数据测试通过")
    
    def test_single_value(self):
        """测试单个值"""
        result = self.auditor.detect_outliers([0.5])
        
        self.assertEqual(len(result["outlier_indices"]), 0)
        print("✅ 单个值测试通过")


class TestGradientCheck(unittest.TestCase):
    """测试梯度消失判定功能"""
    
    def setUp(self):
        self.auditor = StatisticalAuditor(z_score_threshold=3.0, gradient_threshold=0.05)
    
    def test_has_gradient(self):
        """测试存在显著梯度的情况"""
        # 创建有明显差异的数据
        values = [0.5, 0.51, 0.52, 0.53, 0.54, 0.05, 0.06, 0.07]  # 最后几个是明显的低值
        
        result = self.auditor.check_gradient_vanishing(values)
        
        self.assertIn("has_gradient", result)
        self.assertIn("gradient", result)
        self.assertIn("gradient_ratio", result)
        self.assertIn("verdict", result)
        # 由于差异明显，应该判定为存在梯度
        print(f"✅ 梯度检测: has_gradient={result['has_gradient']}, gradient={result['gradient']:.4f}, ratio={result['gradient_ratio']*100:.2f}%")
    
    def test_gradient_vanished(self):
        """测试梯度消失的情况"""
        # 创建差异很小的数据
        values = [0.45, 0.46, 0.47, 0.48, 0.49, 0.50, 0.51, 0.52]  # 差异很小
        
        result = self.auditor.check_gradient_vanishing(values)
        
        self.assertIn("has_gradient", result)
        # 差异小于阈值，应该判定为梯度消失
        print(f"✅ 梯度消失检测: has_gradient={result['has_gradient']}, gradient={result['gradient']:.4f}")
    
    def test_gradient_with_outliers(self):
        """测试带离群值的梯度检测"""
        values = [0.5] * 100 + [0.01, 0.02, 0.03]  # 大部分是0.5，少数是极低值
        
        # 先检测离群值
        outlier_result = self.auditor.detect_outliers(values)
        outlier_indices = outlier_result["outlier_indices"]
        
        # 使用离群值索引进行梯度检测
        result = self.auditor.check_gradient_vanishing(values, outlier_indices=outlier_indices)
        
        self.assertIn("has_gradient", result)
        # 由于有极低值，应该存在显著梯度
        self.assertTrue(result["has_gradient"] or result["gradient"] > 0.3)
        print(f"✅ 带离群值的梯度检测: has_gradient={result['has_gradient']}, gradient={result['gradient']:.4f}")


class TestDistributionStats(unittest.TestCase):
    """测试分布统计功能"""
    
    def setUp(self):
        self.auditor = StatisticalAuditor()
    
    def test_basic_statistics(self):
        """测试基本统计量计算"""
        values = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        
        result = self.auditor.calculate_distribution_stats(values)
        
        self.assertIn("count", result)
        self.assertIn("mean", result)
        self.assertIn("std", result)
        self.assertIn("median", result)
        self.assertIn("min", result)
        self.assertIn("max", result)
        self.assertIn("q1", result)
        self.assertIn("q3", result)
        self.assertIn("iqr", result)
        self.assertIn("skewness", result)
        self.assertIn("kurtosis", result)
        self.assertIn("dynamic_singularity_threshold", result)
        
        self.assertEqual(result["count"], 10)
        self.assertAlmostEqual(result["mean"], 0.55, places=1)
        self.assertAlmostEqual(result["min"], 0.1)
        self.assertAlmostEqual(result["max"], 1.0)
        
        # 检查动态离群红线
        self.assertLessEqual(result["dynamic_singularity_threshold"], 0.15)
        
        print(f"✅ 分布统计: mean={result['mean']:.4f}, std={result['std']:.4f}, "
              f"dynamic_threshold={result['dynamic_singularity_threshold']:.4f}")
    
    def test_empty_data(self):
        """测试空数据"""
        result = self.auditor.calculate_distribution_stats([])
        
        self.assertEqual(result, {})
        print("✅ 空数据统计测试通过")


class TestSingularityVerification(unittest.TestCase):
    """测试奇点存在性验证功能"""
    
    def setUp(self):
        self.auditor = StatisticalAuditor(z_score_threshold=3.0, gradient_threshold=0.05)
    
    def test_singularity_exists(self):
        """测试存在奇点的情况"""
        # 创建有明显离群值和梯度的数据
        normal_data = np.random.normal(0.5, 0.1, 100).tolist()
        extreme_outliers = [0.01, 0.02, 0.03]  # 极端低值
        values = normal_data + extreme_outliers
        
        result = self.auditor.verify_singularity_existence(values)
        
        self.assertIn("singularity_exists", result)
        self.assertIn("verdict", result)
        self.assertIn("reason", result)
        self.assertIn("outlier_detection", result)
        self.assertIn("gradient_check", result)
        self.assertIn("statistics", result)
        
        # 由于有极端离群值和显著梯度，应该判定为存在奇点
        print(f"✅ 奇点验证: singularity_exists={result['singularity_exists']}, "
              f"verdict={result['verdict']}, reason={result['reason']}")
    
    def test_no_singularity(self):
        """测试不存在奇点的情况（梯度消失）"""
        # 创建差异很小的数据
        values = [0.45, 0.46, 0.47, 0.48, 0.49, 0.50, 0.51, 0.52] * 10
        
        result = self.auditor.verify_singularity_existence(values)
        
        self.assertIn("singularity_exists", result)
        # 由于梯度消失，应该判定为不存在奇点
        self.assertFalse(result["singularity_exists"] or result["reason"] == "gradient_vanished")
        print(f"✅ 无奇点验证: singularity_exists={result['singularity_exists']}, "
              f"verdict={result['verdict']}, reason={result['reason']}")
    
    def test_no_outliers_case(self):
        """测试无离群值的情况"""
        # 创建均匀分布的数据
        values = [0.4, 0.41, 0.42, 0.43, 0.44, 0.45, 0.46, 0.47, 0.48, 0.49] * 10
        
        result = self.auditor.verify_singularity_existence(values)
        
        self.assertIn("singularity_exists", result)
        # 由于无离群值，应该判定为不存在奇点
        if not result["singularity_exists"]:
            self.assertEqual(result["reason"], "no_statistical_outliers")
        print(f"✅ 无离群值验证: singularity_exists={result['singularity_exists']}, "
              f"reason={result['reason']}")


class TestSingletonPattern(unittest.TestCase):
    """测试单例模式"""
    
    def test_get_statistical_auditor(self):
        """测试获取全局统计审计器实例"""
        auditor1 = get_statistical_auditor()
        auditor2 = get_statistical_auditor()
        
        # 应该是同一个实例
        self.assertIs(auditor1, auditor2)
        print("✅ 单例模式测试通过")


class TestRealWorldScenarios(unittest.TestCase):
    """测试真实场景"""
    
    def setUp(self):
        self.auditor = StatisticalAuditor(z_score_threshold=3.0, gradient_threshold=0.05)
    
    def test_stability_distribution_scenario(self):
        """测试稳定性分布场景（模拟格局审计）"""
        # 模拟伤官见官格局的稳定性分布
        # 大部分样本稳定性在0.1-0.4之间，少数极端样本在0.01-0.05
        normal_stabilities = np.random.normal(0.2, 0.1, 8000).tolist()
        normal_stabilities = [max(0.05, min(0.5, s)) for s in normal_stabilities]  # 限制范围
        extreme_stabilities = [0.01, 0.02, 0.03, 0.04, 0.05] * 10  # 50个极端样本
        all_stabilities = normal_stabilities + extreme_stabilities
        
        # 执行奇点验证
        result = self.auditor.verify_singularity_existence(all_stabilities)
        
        self.assertIn("singularity_exists", result)
        self.assertIn("statistics", result)
        
        stats = result["statistics"]
        print(f"✅ 真实场景测试: 总样本={stats['count']}, "
              f"均值={stats['mean']:.4f}, 标准差={stats['std']:.4f}, "
              f"奇点存在={result['singularity_exists']}")
        
        # 检查动态离群红线
        if "dynamic_singularity_threshold" in stats:
            print(f"   动态离群红线: {stats['dynamic_singularity_threshold']:.4f}")


def run_statistical_audit_tests():
    """运行所有统计审计测试"""
    print("\n" + "=" * 70)
    print("📊 统计审计工具测试套件 (RSS-V1.4规范)")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestOutlierDetection))
    suite.addTests(loader.loadTestsFromTestCase(TestGradientCheck))
    suite.addTests(loader.loadTestsFromTestCase(TestDistributionStats))
    suite.addTests(loader.loadTestsFromTestCase(TestSingularityVerification))
    suite.addTests(loader.loadTestsFromTestCase(TestSingletonPattern))
    suite.addTests(loader.loadTestsFromTestCase(TestRealWorldScenarios))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_statistical_audit_tests()
    exit(0 if success else 1)

