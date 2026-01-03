#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FDS SOP V3.0 集成测试套件
=======================
全面自动化测试，验证架构归一化和A01格局完整流程

测试范围：
1. Manifest加载和验证
2. SOP执行流程
3. QGA信封格式验证
4. 子格局分类验证
5. UI注册验证
"""

import json
import os
import sys
from pathlib import Path
import numpy as np

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 测试配置
TEST_CONFIG = {
    "manifest_path": "config/patterns/manifest_A01.json",
    "registry_path": "registry/holographic_pattern/A-01.json",
    "data_path": "data/holographic_universe_518k.jsonl",
    "expected_abundance_min": 20.0,  # 期望丰度下限
    "expected_abundance_max": 25.0,  # 期望丰度上限
}

class TestFDSSOPV3:
    """FDS SOP V3.0 集成测试类"""
    
    def __init__(self):
        self.project_root = project_root
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def assert_test(self, condition, test_name, error_msg=""):
        """断言测试"""
        if condition:
            self.passed += 1
            self.tests.append(("✅ PASS", test_name))
            print(f"  ✅ PASS: {test_name}")
            return True
        else:
            self.failed += 1
            self.tests.append(("❌ FAIL", test_name, error_msg))
            print(f"  ❌ FAIL: {test_name}")
            if error_msg:
                print(f"     错误: {error_msg}")
            return False
    
    def test_01_manifest_exists(self):
        """测试1: Manifest文件存在性"""
        print("\n[测试1] Manifest文件存在性验证")
        manifest_path = self.project_root / TEST_CONFIG["manifest_path"]
        exists = manifest_path.exists()
        self.assert_test(exists, "Manifest文件存在", f"文件不存在: {manifest_path}")
        return exists
    
    def test_02_manifest_schema(self):
        """测试2: Manifest Schema验证"""
        print("\n[测试2] Manifest Schema验证")
        manifest_path = self.project_root / TEST_CONFIG["manifest_path"]
        
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest = json.load(f)
            
            # 必需字段检查
            required_fields = ['pattern_id', 'version', 'meta_info', 'classical_logic_rules', 'tensor_mapping_matrix']
            all_present = all(field in manifest for field in required_fields)
            
            self.assert_test(all_present, "Manifest包含必需字段", 
                           f"缺少字段: {set(required_fields) - set(manifest.keys())}")
            
            # 版本检查
            version = manifest.get('version')
            self.assert_test(version == "3.6", f"版本为3.6", f"当前版本: {version}")
            
            # 子格局检查
            has_sub_patterns = 'sub_pattern_definitions' in manifest
            if has_sub_patterns:
                subs = manifest['sub_pattern_definitions']
                self.assert_test(len(subs) == 2, "包含2个子格局定义", f"实际数量: {len(subs)}")
            
            return all_present and version == "3.6"
        except Exception as e:
            self.assert_test(False, "Manifest JSON解析", str(e))
            return False
    
    def test_03_registry_exists(self):
        """测试3: Registry文件存在性"""
        print("\n[测试3] Registry文件存在性验证")
        registry_path = self.project_root / TEST_CONFIG["registry_path"]
        exists = registry_path.exists()
        self.assert_test(exists, "Registry文件存在", f"文件不存在: {registry_path}")
        return exists
    
    def test_04_qga_envelope(self):
        """测试4: QGA信封格式验证"""
        print("\n[测试4] QGA信封格式验证")
        registry_path = self.project_root / TEST_CONFIG["registry_path"]
        
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 根字段检查
            has_topic = data.get('topic') == 'holographic_pattern'
            has_schema = 'schema_version' in data
            has_data = 'data' in data
            
            self.assert_test(has_topic, "topic字段正确", f"topic: {data.get('topic')}")
            self.assert_test(has_schema, "schema_version字段存在")
            self.assert_test(has_data, "data字段存在")
            
            return has_topic and has_schema and has_data
        except Exception as e:
            self.assert_test(False, "Registry JSON解析", str(e))
            return False
    
    def test_05_benchmarks_physical(self):
        """测试5: Benchmarks物理真实性验证"""
        print("\n[测试5] Benchmarks物理真实性验证")
        registry_path = self.project_root / TEST_CONFIG["registry_path"]
        
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            benchmarks = data['data'].get('benchmarks', [])
            self.assert_test(len(benchmarks) > 0, "Benchmarks非空", f"数量: {len(benchmarks)}")
            
            if benchmarks:
                first_tensor = benchmarks[0].get('t', [])
                is_non_zero = not all(v == 0 for v in first_tensor)
                self.assert_test(is_non_zero, "Tensor向量非零（真实物理值）", 
                               f"Tensor: {first_tensor}")
                
                # 验证维度
                has_5d = len(first_tensor) == 5
                self.assert_test(has_5d, "Tensor为5维", f"维度: {len(first_tensor)}")
            
            return len(benchmarks) > 0
        except Exception as e:
            self.assert_test(False, "Benchmarks验证", str(e))
            return False
    
    def test_06_sub_pattern_stats(self):
        """测试6: 子格局统计验证"""
        print("\n[测试6] 子格局统计验证")
        registry_path = self.project_root / TEST_CONFIG["registry_path"]
        
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            stats = data['data'].get('population_stats', {})
            sub_patterns = stats.get('sub_patterns', {})
            
            self.assert_test(len(sub_patterns) == 2, "包含2个子格局统计", 
                           f"数量: {len(sub_patterns)}")
            
            # 检查子格局ID
            expected_ids = {'A-01-S1', 'A-01-S2'}
            actual_ids = set(sub_patterns.keys())
            ids_match = expected_ids == actual_ids
            self.assert_test(ids_match, "子格局ID正确", 
                           f"期望: {expected_ids}, 实际: {actual_ids}")
            
            return len(sub_patterns) == 2 and ids_match
        except Exception as e:
            self.assert_test(False, "子格局统计验证", str(e))
            return False
    
    def test_07_ui_registration(self):
        """测试7: UI注册验证"""
        print("\n[测试7] UI注册验证（Controller加载测试）")
        
        try:
            from controllers.quantum_framework_registry_controller import QuantumFrameworkRegistryController
            
            controller = QuantumFrameworkRegistryController()
            subjects = controller.get_all_subjects(force_reload=True)
            holographic = next((s for s in subjects if s['name'] == 'holographic_pattern'), None)
            
            self.assert_test(holographic is not None, "holographic_pattern主题存在")
            
            if holographic:
                count = holographic.get('topics_count', 0)
                self.assert_test(count == 1, "专题数量为1", f"实际数量: {count}")
                
                topics = holographic.get('topics', {})
                has_a01 = 'A-01' in topics
                self.assert_test(has_a01, "A-01格局已注册")
            
            return holographic is not None
        except Exception as e:
            self.assert_test(False, "UI注册验证", str(e))
            return False
    
    def test_08_abundance_range(self):
        """测试8: 丰度范围验证"""
        print("\n[测试8] 丰度范围验证")
        registry_path = self.project_root / TEST_CONFIG["registry_path"]
        
        try:
            with open(registry_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            abundance = data['data']['population_stats'].get('base_abundance', 0)
            in_range = TEST_CONFIG["expected_abundance_min"] <= abundance <= TEST_CONFIG["expected_abundance_max"]
            
            self.assert_test(in_range, 
                           f"丰度在合理范围 ({TEST_CONFIG['expected_abundance_min']}-{TEST_CONFIG['expected_abundance_max']}%)",
                           f"实际丰度: {abundance}%")
            
            return in_range
        except Exception as e:
            self.assert_test(False, "丰度范围验证", str(e))
            return False
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("FDS SOP V3.0 集成测试套件")
        print("=" * 60)
        
        # 运行所有测试
        self.test_01_manifest_exists()
        self.test_02_manifest_schema()
        self.test_03_registry_exists()
        self.test_04_qga_envelope()
        self.test_05_benchmarks_physical()
        self.test_06_sub_pattern_stats()
        self.test_07_ui_registration()
        self.test_08_abundance_range()
        
        # 生成报告
        self.print_report()
    
    def print_report(self):
        """打印测试报告"""
        print("\n" + "=" * 60)
        print("测试报告")
        print("=" * 60)
        print(f"总测试数: {self.passed + self.failed}")
        print(f"通过: {self.passed}")
        print(f"失败: {self.failed}")
        print(f"通过率: {self.passed / (self.passed + self.failed) * 100:.1f}%")
        
        if self.failed > 0:
            print("\n失败的测试:")
            for test in self.tests:
                if test[0] == "❌ FAIL":
                    print(f"  {test[0]} {test[1]}")
                    if len(test) > 2:
                        print(f"      {test[2]}")
        
        print("\n" + "=" * 60)
        if self.failed == 0:
            print("✅ 所有测试通过！")
        else:
            print(f"❌ {self.failed} 个测试失败")
        print("=" * 60)
        
        return self.failed == 0


if __name__ == "__main__":
    tester = TestFDSSOPV3()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)

