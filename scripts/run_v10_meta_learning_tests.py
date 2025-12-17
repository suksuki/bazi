#!/usr/bin/env python3
"""
运行 V10.0 元学习调优体系测试
=============================

运行所有单元测试、集成测试和回归测试

作者: Antigravity Team
版本: V10.0
日期: 2025-12-17
"""

import sys
import unittest
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_tests():
    """加载所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 单元测试
    unit_tests = [
        'tests.unit.test_bayesian_optimization',
        'tests.unit.test_contrastive_rlhf',
        'tests.unit.test_transformer_position_tuning',
        'tests.unit.test_gat_path_filter'
    ]
    
    for test_module in unit_tests:
        try:
            suite.addTests(loader.loadTestsFromName(test_module))
            print(f"✅ 加载测试模块: {test_module}")
        except Exception as e:
            print(f"❌ 加载测试模块失败: {test_module}, 错误: {e}")
    
    # 集成测试
    integration_tests = [
        'tests.integration.test_meta_learning_integration'
    ]
    
    for test_module in integration_tests:
        try:
            suite.addTests(loader.loadTestsFromName(test_module))
            print(f"✅ 加载集成测试模块: {test_module}")
        except Exception as e:
            print(f"❌ 加载集成测试模块失败: {test_module}, 错误: {e}")
    
    # 回归测试
    regression_tests = [
        'tests.test_jason_d_1999_regression'
    ]
    
    for test_module in regression_tests:
        try:
            suite.addTests(loader.loadTestsFromName(test_module))
            print(f"✅ 加载回归测试模块: {test_module}")
        except Exception as e:
            print(f"❌ 加载回归测试模块失败: {test_module}, 错误: {e}")
    
    return suite


def main():
    """主函数"""
    print("=" * 80)
    print("🧪 V10.0 元学习调优体系测试套件")
    print("=" * 80)
    print()
    
    # 加载测试
    suite = load_tests()
    
    print()
    print("=" * 80)
    print("开始运行测试...")
    print("=" * 80)
    print()
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 输出总结
    print()
    print("=" * 80)
    print("📊 测试结果总结")
    print("=" * 80)
    print(f"运行测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped)}")
    
    if result.failures:
        print()
        print("❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print()
        print("❌ 错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    # 返回退出码
    if result.wasSuccessful():
        print()
        print("✅ 所有测试通过！")
        return 0
    else:
        print()
        print("❌ 部分测试失败！")
        return 1


if __name__ == '__main__':
    sys.exit(main())

