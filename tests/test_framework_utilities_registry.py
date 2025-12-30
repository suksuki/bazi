"""
FRAMEWORK_UTILITIES 注册表加载与模块测试套件
==========================================
测试从注册表加载模块、LogicRegistry集成等功能
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import unittest
import json
from typing import Dict, Any, List

from core.registry_loader import RegistryLoader
from core.logic_registry import LogicRegistry


class TestFrameworkUtilitiesRegistry(unittest.TestCase):
    """测试 FRAMEWORK_UTILITIES 注册表加载"""
    
    def setUp(self):
        """初始化测试环境"""
        self.registry_path = Path(__file__).parent.parent / "core" / "subjects" / "framework_utilities" / "registry.json"
        self.loader = RegistryLoader(theme_id="FRAMEWORK_UTILITIES")
        self.registry = self.loader.registry
    
    def test_01_registry_file_exists(self):
        """测试注册表文件存在"""
        self.assertTrue(self.registry_path.exists(), f"注册表文件不存在: {self.registry_path}")
        print(f"✅ 注册表文件存在: {self.registry_path}")
    
    def test_02_registry_structure(self):
        """测试注册表结构"""
        self.assertIsNotNone(self.registry, "注册表未加载")
        self.assertIn("metadata", self.registry, "缺少 metadata")
        self.assertIn("theme", self.registry, "缺少 theme")
        self.assertIn("patterns", self.registry, "缺少 patterns")
        
        metadata = self.registry["metadata"]
        self.assertEqual(metadata.get("id"), "FRAMEWORK_UTILITIES_REGISTRY")
        self.assertEqual(metadata.get("specification", {}).get("registry_standard"), "QGA-HR V2.0")
        
        print(f"✅ 注册表结构正确")
        print(f"   主题: {self.registry['theme'].get('name')}")
        print(f"   模块数: {len(self.registry.get('patterns', {}))}")
    
    def test_03_pattern_count(self):
        """测试模块数量"""
        patterns = self.registry.get("patterns", {})
        expected_count = 4  # MOD_19, MOD_20, MOD_21, MOD_22
        self.assertEqual(len(patterns), expected_count, f"模块数量不正确，期望 {expected_count} 个，实际 {len(patterns)} 个")
        print(f"✅ 模块数量: {len(patterns)}")
    
    def test_04_pattern_structure(self):
        """测试模块结构完整性"""
        patterns = self.registry.get("patterns", {})
        required_fields = [
            "id", "name", "name_cn", "name_en", "category", "subject_id",
            "icon", "version", "active", "created_at", "description",
            "semantic_seed", "physics_kernel", "feature_anchors",
            "dynamic_states", "tensor_operator", "algorithm_implementation",
            "kinetic_evolution", "audit_trail"
        ]
        
        for pattern_id, pattern_data in patterns.items():
            for field in required_fields:
                self.assertIn(field, pattern_data, f"{pattern_id} 缺少字段: {field}")
        
        print(f"✅ 所有模块结构完整（检查了 {len(patterns)} 个模块）")
    
    def test_05_algorithm_implementation(self):
        """测试算法实现路径"""
        patterns = self.registry.get("patterns", {})
        test_pattern = patterns.get("MOD_19_BAZI_UTILITIES")
        self.assertIsNotNone(test_pattern, "MOD_19_BAZI_UTILITIES 不存在")
        
        algo_impl = test_pattern.get("algorithm_implementation", {})
        self.assertIn("paths", algo_impl, "缺少 paths 字段")
        self.assertIn("registry_loader", algo_impl, "缺少 registry_loader 字段")
        
        paths = algo_impl.get("paths", {})
        self.assertGreater(len(paths), 0, "paths 为空")
        
        print(f"✅ 算法实现路径正确（{len(paths)} 个路径）")
    
    def test_06_get_pattern(self):
        """测试获取格局配置"""
        pattern = self.loader.get_pattern("MOD_19_BAZI_UTILITIES")
        self.assertIsNotNone(pattern, "无法获取 MOD_19_BAZI_UTILITIES")
        self.assertEqual(pattern.get("id"), "MOD_19_BAZI_UTILITIES")
        
        print(f"✅ 成功获取格局配置: {pattern.get('name')}")


class TestLogicRegistryFrameworkUtilities(unittest.TestCase):
    """测试 LogicRegistry 与 FRAMEWORK_UTILITIES 的集成"""
    
    def setUp(self):
        """初始化测试环境"""
        self.registry = LogicRegistry()
    
    def test_07_get_themes(self):
        """测试获取主题列表"""
        themes = self.registry.get_themes()
        self.assertIn("FRAMEWORK_UTILITIES", themes, "FRAMEWORK_UTILITIES 主题不存在")
        
        theme_data = themes["FRAMEWORK_UTILITIES"]
        self.assertIn("registry_path", theme_data, "主题缺少 registry_path")
        
        print(f"✅ 主题列表正确，包含 FRAMEWORK_UTILITIES")
    
    def test_08_get_active_modules_from_registry(self):
        """测试从注册表加载模块"""
        modules = self.registry.get_active_modules(theme_id="FRAMEWORK_UTILITIES")
        self.assertGreater(len(modules), 0, "未加载到任何模块")
        
        # 检查第一个模块
        first_module = modules[0]
        self.assertIn("id", first_module)
        self.assertIn("name", first_module)
        self.assertIn("pattern_data", first_module, "模块缺少 pattern_data")
        
        pattern_data = first_module.get("pattern_data", {})
        self.assertIn("semantic_seed", pattern_data)
        self.assertIn("algorithm_implementation", pattern_data)
        
        print(f"✅ 从注册表加载了 {len(modules)} 个模块")
        print(f"   第一个模块: {first_module.get('id')} - {first_module.get('name')}")
    
    def test_09_module_ordering(self):
        """测试模块排序"""
        modules = self.registry.get_active_modules(theme_id="FRAMEWORK_UTILITIES")
        
        # 检查是否按ID排序
        module_ids = [m["id"] for m in modules]
        sorted_ids = sorted(module_ids)
        self.assertEqual(module_ids, sorted_ids, "模块未按ID排序")
        
        print(f"✅ 模块已正确排序")


class TestRegistryLoaderFrameworkUtilities(unittest.TestCase):
    """测试 RegistryLoader 的 FRAMEWORK_UTILITIES 支持"""
    
    def test_10_theme_id_framework_utilities(self):
        """测试通过 theme_id 加载 FRAMEWORK_UTILITIES"""
        loader = RegistryLoader(theme_id="FRAMEWORK_UTILITIES")
        self.assertIsNotNone(loader.registry)
        self.assertEqual(loader.theme_id, "FRAMEWORK_UTILITIES")
        
        patterns = loader.registry.get("patterns", {})
        self.assertGreater(len(patterns), 0)
        
        print(f"✅ 通过 theme_id 成功加载 FRAMEWORK_UTILITIES ({len(patterns)} 个模块)")


def run_tests():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("🧪 FRAMEWORK_UTILITIES 注册表测试套件")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestFrameworkUtilitiesRegistry))
    suite.addTests(loader.loadTestsFromTestCase(TestLogicRegistryFrameworkUtilities))
    suite.addTests(loader.loadTestsFromTestCase(TestRegistryLoaderFrameworkUtilities))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印摘要
    print("\n" + "=" * 70)
    print("📊 测试摘要")
    print("=" * 70)
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 失败的测试:")
        for test, traceback in result.failures:
            print(f"  - {test}")
    
    if result.errors:
        print("\n❌ 错误的测试:")
        for test, traceback in result.errors:
            print(f"  - {test}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)

