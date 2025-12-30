"""
BAZI_FUNDAMENTAL 注册表加载与模块测试套件
==========================================
测试从注册表加载模块、LogicRegistry集成、quantum_lab支持等功能
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


class TestBaziFundamentalRegistry(unittest.TestCase):
    """测试 BAZI_FUNDAMENTAL 注册表加载"""
    
    def setUp(self):
        """初始化测试环境"""
        self.registry_path = Path(__file__).parent.parent / "core" / "subjects" / "bazi_fundamental" / "registry.json"
        self.loader = RegistryLoader(theme_id="BAZI_FUNDAMENTAL")
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
        self.assertEqual(metadata.get("id"), "BAZI_FUNDAMENTAL_REGISTRY")
        self.assertEqual(metadata.get("specification", {}).get("registry_standard"), "QGA-HR V2.0")
        
        print(f"✅ 注册表结构正确")
        print(f"   主题: {self.registry['theme'].get('name')}")
        print(f"   模块数: {len(self.registry.get('patterns', {}))}")
    
    def test_03_pattern_count(self):
        """测试模块数量"""
        patterns = self.registry.get("patterns", {})
        expected_count = 17  # MOD_00 到 MOD_18 (跳过 MOD_08, MOD_13)
        self.assertGreaterEqual(len(patterns), expected_count, f"模块数量不足，期望至少 {expected_count} 个")
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
    
    def test_05_semantic_seed(self):
        """测试语义种子结构"""
        patterns = self.registry.get("patterns", {})
        test_pattern = patterns.get("MOD_00_SUBSTRATE")
        self.assertIsNotNone(test_pattern, "MOD_00_SUBSTRATE 不存在")
        
        semantic_seed = test_pattern.get("semantic_seed", {})
        self.assertIn("description", semantic_seed)
        self.assertIn("physical_image", semantic_seed)
        self.assertIn("source", semantic_seed)
        
        print(f"✅ 语义种子结构正确")
    
    def test_06_physics_kernel(self):
        """测试物理内核结构"""
        patterns = self.registry.get("patterns", {})
        test_pattern = patterns.get("MOD_00_SUBSTRATE")
        
        physics_kernel = test_pattern.get("physics_kernel", {})
        self.assertIn("description", physics_kernel)
        self.assertIn("quantum_dispersion", physics_kernel)
        self.assertIn("causal_entropy", physics_kernel)
        
        print(f"✅ 物理内核结构正确")
    
    def test_07_algorithm_implementation(self):
        """测试算法实现路径"""
        patterns = self.registry.get("patterns", {})
        test_pattern = patterns.get("MOD_00_SUBSTRATE")
        
        algo_impl = test_pattern.get("algorithm_implementation", {})
        self.assertIn("paths", algo_impl, "缺少 paths 字段")
        self.assertIn("registry_loader", algo_impl, "缺少 registry_loader 字段")
        
        paths = algo_impl.get("paths", {})
        self.assertGreater(len(paths), 0, "paths 为空")
        
        print(f"✅ 算法实现路径正确（{len(paths)} 个路径）")
    
    def test_08_feature_anchors(self):
        """测试特征锚点结构"""
        patterns = self.registry.get("patterns", {})
        test_pattern = patterns.get("MOD_00_SUBSTRATE")
        
        feature_anchors = test_pattern.get("feature_anchors", {})
        self.assertIn("standard_centroid", feature_anchors)
        
        standard_centroid = feature_anchors.get("standard_centroid", {})
        self.assertIn("vector", standard_centroid)
        self.assertIn("match_threshold", standard_centroid)
        
        print(f"✅ 特征锚点结构正确")
    
    def test_09_get_pattern(self):
        """测试获取格局配置"""
        pattern = self.loader.get_pattern("MOD_00_SUBSTRATE")
        self.assertIsNotNone(pattern, "无法获取 MOD_00_SUBSTRATE")
        self.assertEqual(pattern.get("id"), "MOD_00_SUBSTRATE")
        
        print(f"✅ 成功获取格局配置: {pattern.get('name')}")
    
    def test_10_all_patterns_loadable(self):
        """测试所有模块都可加载"""
        patterns = self.registry.get("patterns", {})
        failed_patterns = []
        
        for pattern_id in patterns.keys():
            pattern = self.loader.get_pattern(pattern_id)
            if pattern is None:
                failed_patterns.append(pattern_id)
        
        self.assertEqual(len(failed_patterns), 0, f"以下模块无法加载: {failed_patterns}")
        print(f"✅ 所有 {len(patterns)} 个模块都可正常加载")


class TestLogicRegistryIntegration(unittest.TestCase):
    """测试 LogicRegistry 与注册表的集成"""
    
    def setUp(self):
        """初始化测试环境"""
        self.registry = LogicRegistry()
    
    def test_11_get_themes(self):
        """测试获取主题列表"""
        themes = self.registry.get_themes()
        self.assertIn("BAZI_FUNDAMENTAL", themes, "BAZI_FUNDAMENTAL 主题不存在")
        
        theme_data = themes["BAZI_FUNDAMENTAL"]
        self.assertIn("registry_path", theme_data, "主题缺少 registry_path")
        
        print(f"✅ 主题列表正确，包含 BAZI_FUNDAMENTAL")
    
    def test_12_get_active_modules_from_registry(self):
        """测试从注册表加载模块"""
        modules = self.registry.get_active_modules(theme_id="BAZI_FUNDAMENTAL")
        self.assertGreater(len(modules), 0, "未加载到任何模块")
        
        # 检查第一个模块
        first_module = modules[0]
        self.assertIn("id", first_module)
        self.assertIn("name", first_module)
        self.assertIn("pattern_data", first_module, "模块缺少 pattern_data")
        
        pattern_data = first_module.get("pattern_data", {})
        self.assertIn("semantic_seed", pattern_data)
        self.assertIn("physics_kernel", pattern_data)
        
        print(f"✅ 从注册表加载了 {len(modules)} 个模块")
        print(f"   第一个模块: {first_module.get('id')} - {first_module.get('name')}")
    
    def test_13_module_structure_completeness(self):
        """测试模块结构完整性（从 LogicRegistry）"""
        modules = self.registry.get_active_modules(theme_id="BAZI_FUNDAMENTAL")
        
        required_fields = ["id", "name", "description", "goal", "outcome", "pattern_data"]
        
        for module in modules:
            for field in required_fields:
                self.assertIn(field, module, f"{module.get('id')} 缺少字段: {field}")
        
        print(f"✅ 所有模块结构完整（检查了 {len(modules)} 个模块）")
    
    def test_14_module_ordering(self):
        """测试模块排序"""
        modules = self.registry.get_active_modules(theme_id="BAZI_FUNDAMENTAL")
        
        # 检查是否按ID排序
        module_ids = [m["id"] for m in modules]
        sorted_ids = sorted(module_ids)
        self.assertEqual(module_ids, sorted_ids, "模块未按ID排序")
        
        print(f"✅ 模块已正确排序")
    
    def test_15_theme_filtering(self):
        """测试主题过滤"""
        # 测试 BAZI_FUNDAMENTAL 主题
        modules_bf = self.registry.get_active_modules(theme_id="BAZI_FUNDAMENTAL")
        self.assertGreater(len(modules_bf), 0, "BAZI_FUNDAMENTAL 主题无模块")
        
        # 测试 HOLOGRAPHIC_PATTERN 主题
        modules_hp = self.registry.get_active_modules(theme_id="HOLOGRAPHIC_PATTERN")
        self.assertGreater(len(modules_hp), 0, "HOLOGRAPHIC_PATTERN 主题无模块")
        
        # 确保两个主题的模块不同
        bf_ids = {m["id"] for m in modules_bf}
        hp_ids = {m["id"] for m in modules_hp}
        self.assertNotEqual(bf_ids, hp_ids, "两个主题的模块不应该相同")
        
        print(f"✅ 主题过滤正确")
        print(f"   BAZI_FUNDAMENTAL: {len(modules_bf)} 个模块")
        print(f"   HOLOGRAPHIC_PATTERN: {len(modules_hp)} 个模块")


class TestRegistryLoaderThemeSupport(unittest.TestCase):
    """测试 RegistryLoader 的主题支持"""
    
    def test_16_theme_id_bazi_fundamental(self):
        """测试通过 theme_id 加载 BAZI_FUNDAMENTAL"""
        loader = RegistryLoader(theme_id="BAZI_FUNDAMENTAL")
        self.assertIsNotNone(loader.registry)
        self.assertEqual(loader.theme_id, "BAZI_FUNDAMENTAL")
        
        patterns = loader.registry.get("patterns", {})
        self.assertGreater(len(patterns), 0)
        
        print(f"✅ 通过 theme_id 成功加载 BAZI_FUNDAMENTAL ({len(patterns)} 个模块)")
    
    def test_17_theme_id_holographic_pattern(self):
        """测试通过 theme_id 加载 HOLOGRAPHIC_PATTERN"""
        loader = RegistryLoader(theme_id="HOLOGRAPHIC_PATTERN")
        self.assertIsNotNone(loader.registry)
        self.assertEqual(loader.theme_id, "HOLOGRAPHIC_PATTERN")
        
        patterns = loader.registry.get("patterns", {})
        self.assertGreater(len(patterns), 0)
        
        print(f"✅ 通过 theme_id 成功加载 HOLOGRAPHIC_PATTERN ({len(patterns)} 个模块)")
    
    def test_18_default_registry(self):
        """测试默认注册表（无 theme_id）"""
        loader = RegistryLoader()
        self.assertIsNotNone(loader.registry)
        
        patterns = loader.registry.get("patterns", {})
        self.assertGreater(len(patterns), 0)
        
        print(f"✅ 默认注册表加载成功 ({len(patterns)} 个模块)")


class TestPatternDataValidation(unittest.TestCase):
    """测试模块数据的验证"""
    
    def setUp(self):
        """初始化测试环境"""
        self.registry = LogicRegistry()
        self.modules = self.registry.get_active_modules(theme_id="BAZI_FUNDAMENTAL")
    
    def test_19_pattern_data_presence(self):
        """测试所有模块都有 pattern_data"""
        for module in self.modules:
            self.assertIn("pattern_data", module, f"{module.get('id')} 缺少 pattern_data")
        
        print(f"✅ 所有 {len(self.modules)} 个模块都包含 pattern_data")
    
    def test_20_semantic_seed_validation(self):
        """测试语义种子验证"""
        for module in self.modules:
            pattern_data = module.get("pattern_data", {})
            semantic_seed = pattern_data.get("semantic_seed", {})
            
            self.assertIn("description", semantic_seed, f"{module.get('id')} 语义种子缺少 description")
            self.assertIn("physical_image", semantic_seed, f"{module.get('id')} 语义种子缺少 physical_image")
        
        print(f"✅ 所有模块的语义种子结构正确")
    
    def test_21_algorithm_paths_validation(self):
        """测试算法路径验证"""
        for module in self.modules:
            pattern_data = module.get("pattern_data", {})
            algo_impl = pattern_data.get("algorithm_implementation", {})
            paths = algo_impl.get("paths", {})
            
            self.assertGreater(len(paths), 0, f"{module.get('id')} 算法路径为空")
            
            # 检查路径格式（应该包含点号分隔）
            for func_name, func_path in paths.items():
                self.assertIn(".", func_path, f"{module.get('id')} 路径格式错误: {func_path}")
        
        print(f"✅ 所有模块的算法路径格式正确")
    
    def test_22_feature_anchors_validation(self):
        """测试特征锚点验证"""
        for module in self.modules:
            pattern_data = module.get("pattern_data", {})
            feature_anchors = pattern_data.get("feature_anchors", {})
            
            self.assertIn("standard_centroid", feature_anchors, f"{module.get('id')} 缺少 standard_centroid")
            
            standard_centroid = feature_anchors.get("standard_centroid", {})
            self.assertIn("vector", standard_centroid, f"{module.get('id')} standard_centroid 缺少 vector")
        
        print(f"✅ 所有模块的特征锚点结构正确")


def run_tests():
    """运行所有测试"""
    print("\n" + "=" * 70)
    print("🧪 BAZI_FUNDAMENTAL 注册表测试套件")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestBaziFundamentalRegistry))
    suite.addTests(loader.loadTestsFromTestCase(TestLogicRegistryIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestRegistryLoaderThemeSupport))
    suite.addTests(loader.loadTestsFromTestCase(TestPatternDataValidation))
    
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

