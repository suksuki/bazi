#!/usr/bin/env python3
"""
QGA 全面自动化测试套件
包含：
1. 全息格局系统测试
2. RegistryLoader 算法复原测试
3. 核心引擎测试
4. UI 功能测试
"""

import sys
import os
import json
import traceback
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# 测试结果统计
test_results = {
    'total': 0,
    'passed': 0,
    'failed': 0,
    'errors': []
}

def print_header(title):
    """打印测试标题"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def run_test(test_name, test_func):
    """运行单个测试"""
    test_results['total'] += 1
    print(f"\n[{test_results['total']}] {test_name}...", end=" ")
    try:
        result = test_func()
        if result:
            print("✅ PASS")
            test_results['passed'] += 1
            return True
        else:
            print("❌ FAIL")
            test_results['failed'] += 1
            return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        test_results['failed'] += 1
        test_results['errors'].append({
            'test': test_name,
            'error': str(e),
            'traceback': traceback.format_exc()
        })
        return False

# ==================== 测试1: RegistryLoader 算法复原 ====================
def test_registry_loader():
    """测试 RegistryLoader 能否正确加载和计算"""
    from core.registry_loader import RegistryLoader
    
    loader = RegistryLoader()
    
    # 测试加载 A-03 配置
    pattern_id = 'A-03'
    chart = ['甲子', '丁卯', '甲寅', '庚午']
    day_master = '甲'
    
    result = loader.calculate_tensor_projection_from_registry(
        pattern_id=pattern_id,
        chart=chart,
        day_master=day_master
    )
    
    if 'error' in result:
        raise Exception(f"计算失败: {result['error']}")
    
    # 验证结果结构
    assert 'sai' in result, "缺少SAI值"
    assert 'projection' in result, "缺少投影值"
    assert 'weights' in result, "缺少权重值"
    
    return True

# ==================== 测试2: 核心数学引擎 ====================
def test_math_engine():
    """测试数学引擎函数"""
    from core.math_engine import (
        sigmoid_variant,
        tensor_normalize,
        calculate_s_balance,
        calculate_flow_factor
    )
    import numpy as np
    
    # 测试 sigmoid_variant
    x = 0.5
    k = 1.5
    x0 = 0.0
    result = sigmoid_variant(x, k, x0)
    assert isinstance(result, (float, np.floating)), "sigmoid_variant 应返回数值"
    assert 0 <= result <= 1, "sigmoid_variant 结果应在 [0, 1] 范围内"
    
    # 测试 tensor_normalize
    vector = {'E': 0.3, 'O': 0.4, 'M': 0.1, 'S': 0.15, 'R': 0.05}
    normalized = tensor_normalize(vector)
    total = sum(normalized.values())
    assert abs(total - 1.0) < 0.001, f"归一化后总和应为1.0，实际为{total}"
    
    # 测试 calculate_s_balance
    blade_energy = 1.0
    kill_energy = 0.8
    balance = calculate_s_balance(blade_energy, kill_energy)
    assert isinstance(balance, (float, np.floating)), "calculate_s_balance 应返回数值"
    
    # 测试 calculate_flow_factor
    s_base = 0.5
    e_seal = 0.3
    flow = calculate_flow_factor(s_base, e_seal)
    assert isinstance(flow, (float, np.floating)), "calculate_flow_factor 应返回数值"
    assert flow > 0, "flow_factor 应大于0"
    
    return True

# ==================== 测试3: 核心物理引擎 ====================
def test_physics_engine():
    """测试物理引擎函数"""
    from core.physics_engine import (
        compute_energy_flux,
        calculate_interaction_damping
    )
    
    # 测试 compute_energy_flux
    chart = ['甲子', '丁卯', '甲寅', '庚午']
    day_master = '甲'
    
    # 测试计算七杀能量
    kill_energy = compute_energy_flux(chart, day_master, '七杀')
    assert isinstance(kill_energy, (float, int)), "compute_energy_flux 应返回数值"
    assert kill_energy >= 0, "能量值应大于等于0"
    
    # 测试计算羊刃能量
    blade_energy = compute_energy_flux(chart, day_master, '羊刃')
    assert isinstance(blade_energy, (float, int)), "compute_energy_flux 应返回数值"
    assert blade_energy >= 0, "能量值应大于等于0"
    
    # 测试 calculate_interaction_damping
    chart = ['甲子', '丁卯', '甲寅', '庚午']
    month_branch = '卯'  # 月令
    clash_branch = '酉'  # 冲刃地支
    damping = calculate_interaction_damping(chart, month_branch, clash_branch)
    assert isinstance(damping, (float, int)), "calculate_interaction_damping 应返回数值"
    assert damping > 0, "阻尼系数应大于0"
    
    return True

# ==================== 测试4: 全息格局控制器 ====================
def test_holographic_pattern_controller():
    """测试全息格局控制器"""
    from controllers.holographic_pattern_controller import HolographicPatternController
    
    controller = HolographicPatternController()
    
    # 测试获取所有格局
    patterns = controller.get_all_patterns()
    assert isinstance(patterns, list), "get_all_patterns 应返回列表"
    assert len(patterns) > 0, "应至少有一个格局"
    
    # 测试获取格局层级
    hierarchy = controller.get_pattern_hierarchy()
    assert isinstance(hierarchy, dict), "get_pattern_hierarchy 应返回字典"
    
    # 测试计算张量投影
    chart = ['甲子', '丁卯', '甲寅', '庚午']
    day_master = '甲'
    result = controller.calculate_tensor_projection(
        pattern_id='A-03',
        chart=chart,
        day_master=day_master
    )
    
    if 'error' in result:
        raise Exception(f"计算失败: {result['error']}")
    
    assert 'sai' in result, "结果应包含SAI值"
    assert 'projection' in result, "结果应包含投影值"
    
    return True

# ==================== 测试5: 注册表完整性 ====================
def test_registry_integrity():
    """测试注册表完整性"""
    registry_path = project_root / "core" / "subjects" / "holographic_pattern" / "registry.json"
    
    assert registry_path.exists(), f"注册表文件不存在: {registry_path}"
    
    with open(registry_path, 'r', encoding='utf-8') as f:
        registry = json.load(f)
    
    # 验证基本结构
    assert 'metadata' in registry, "注册表应包含 metadata"
    assert 'patterns' in registry, "注册表应包含 patterns"
    
    # 验证 A-03 格局
    assert 'A-03' in registry['patterns'], "注册表应包含 A-03 格局"
    pattern = registry['patterns']['A-03']
    
    # 验证必要字段
    required_fields = [
        'semantic_seed',
        'tensor_operator',
        'kinetic_evolution',
        'audit_trail'
    ]
    for field in required_fields:
        assert field in pattern, f"A-03 格局应包含 {field} 字段"
    
    # 验证算法实现路径
    tensor_operator = pattern.get('tensor_operator', {})
    algo_impl = tensor_operator.get('algorithm_implementation', {})
    
    if algo_impl:
        # 验证关键函数路径是否存在（通过导入验证）
        import importlib
        
        # 检查必要的函数路径
        required_functions = [
            'energy_calculation',
            'activation_function',
            'core_equation'
        ]
        
        for func_name in required_functions:
            if func_name in algo_impl:
                func_info = algo_impl[func_name]
                func_path = func_info.get('function')
                if func_path:
                    # 验证路径格式：module.function
                    parts = func_path.split('.')
                    assert len(parts) >= 2, f"路径格式错误: {func_path}"
                    
                    # 尝试导入模块
                    module_path = '.'.join(parts[:-1])
                    func_name_in_module = parts[-1]
                    
                    try:
                        module = importlib.import_module(module_path)
                        func = getattr(module, func_name_in_module, None)
                        assert func is not None, f"模块 {module_path} 中找不到函数 {func_name_in_module}"
                        assert callable(func), f"{func_path} 不是可调用函数"
                    except ImportError as e:
                        raise Exception(f"无法导入模块 {module_path}: {e}")
    
    return True

# ==================== 测试6: UI 页面导入测试 ====================
def test_ui_page_imports():
    """测试 UI 页面能否正常导入"""
    try:
        from ui.pages.holographic_pattern import render
        assert callable(render), "render 应该是可调用函数"
        return True
    except Exception as e:
        raise Exception(f"UI 页面导入失败: {str(e)}")

# ==================== 主测试函数 ====================
def main():
    print_header("QGA 全面自动化测试套件")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"项目根目录: {project_root}")
    
    # 运行所有测试
    tests = [
        ("RegistryLoader 算法复原", test_registry_loader),
        ("核心数学引擎", test_math_engine),
        ("核心物理引擎", test_physics_engine),
        ("全息格局控制器", test_holographic_pattern_controller),
        ("注册表完整性", test_registry_integrity),
        ("UI 页面导入", test_ui_page_imports),
    ]
    
    for test_name, test_func in tests:
        run_test(test_name, test_func)
    
    # 打印测试总结
    print_header("测试总结")
    print(f"总测试数: {test_results['total']}")
    print(f"通过: {test_results['passed']} ✅")
    print(f"失败: {test_results['failed']} ❌")
    print(f"通过率: {(test_results['passed'] / test_results['total'] * 100):.1f}%")
    
    if test_results['errors']:
        print("\n【错误详情】")
        print("-" * 70)
        for i, error in enumerate(test_results['errors'], 1):
            print(f"\n{i}. {error['test']}")
            print(f"   错误: {error['error']}")
            if len(error['traceback']) < 500:  # 只显示简短的错误信息
                print(f"   详情: {error['traceback'][:200]}...")
    
    # 保存测试报告
    report_path = project_root / "data" / "test_reports" / f"comprehensive_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total': test_results['total'],
            'passed': test_results['passed'],
            'failed': test_results['failed'],
            'pass_rate': test_results['passed'] / test_results['total'] * 100 if test_results['total'] > 0 else 0
        },
        'errors': test_results['errors']
    }
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 测试报告已保存: {report_path}")
    
    # 返回退出码
    return 0 if test_results['failed'] == 0 else 1

if __name__ == '__main__':
    sys.exit(main())

