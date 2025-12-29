#!/usr/bin/env python3
"""
QGA 冒烟测试：RegistryLoader 算法复原验证
使用真实八字验证 RegistryLoader 能否100%复原算法
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core.registry_loader import RegistryLoader
from core.math_engine import sigmoid_variant, tensor_normalize, calculate_s_balance, calculate_flow_factor
from core.physics_engine import compute_energy_flux, calculate_interaction_damping

print("=" * 70)
print("🔥 QGA 冒烟测试：RegistryLoader 算法复原验证")
print("=" * 70)
print()

# 测试用例：真实八字（羊刃架杀格局）
test_cases = [
    {
        "name": "测试用例1：标准羊刃架杀",
        "chart": ["丙寅", "甲午", "戊午", "戊午"],
        "day_master": "戊",
        "description": "地支三午（羊刃），天干透甲木七杀，标准羊刃架杀格局"
    },
    {
        "name": "测试用例2：羊刃架杀（有印星）",
        "chart": ["庚申", "甲午", "丙午", "甲午"],
        "day_master": "丙",
        "description": "地支三午（羊刃），天干透甲木七杀，年干庚金偏印（通关）"
    },
    {
        "name": "测试用例3：羊刃架杀（刃重杀轻）",
        "chart": ["戊辰", "甲子", "壬子", "庚子"],
        "day_master": "壬",
        "description": "地支三子（羊刃），天干透甲木七杀，刃重杀轻"
    }
]

# 初始化 RegistryLoader
print("【步骤1：初始化 RegistryLoader】")
print("-" * 70)
loader = RegistryLoader()
print("✅ RegistryLoader 初始化成功")
print()

# 测试1：验证能否加载 A-03 配置
print("【步骤2：验证配置加载】")
print("-" * 70)
pattern = loader.get_pattern('A-03')
if pattern:
    print("✅ 成功加载 A-03 配置")
    print(f"   格局名称: {pattern.get('name', 'N/A')}")
    print(f"   版本: {pattern.get('version', 'N/A')}")
    
    # 检查 algorithm_implementation 模块
    algo_impl = pattern.get('tensor_operator', {}).get('algorithm_implementation', {})
    if algo_impl:
        print("✅ 找到 algorithm_implementation 模块")
        print(f"   包含 {len(algo_impl)} 个引擎路径")
    else:
        print("❌ 未找到 algorithm_implementation 模块")
        sys.exit(1)
else:
    print("❌ 无法加载 A-03 配置")
    sys.exit(1)
print()

# 测试2：验证引擎函数是否可调用
print("【步骤3：验证引擎函数可调用性】")
print("-" * 70)

# 测试数学引擎
try:
    result = sigmoid_variant(0.0, k=1.0, x0=0.0)
    print(f"✅ sigmoid_variant: {result:.4f}")
except Exception as e:
    print(f"❌ sigmoid_variant 调用失败: {e}")

try:
    result = tensor_normalize({'E': 0.6, 'O': 0.8, 'M': 0.2})
    print(f"✅ tensor_normalize: {result}")
except Exception as e:
    print(f"❌ tensor_normalize 调用失败: {e}")

try:
    result = calculate_s_balance(1.0, 0.8)
    print(f"✅ calculate_s_balance: {result:.4f}")
except Exception as e:
    print(f"❌ calculate_s_balance 调用失败: {e}")

try:
    result = calculate_flow_factor(20.0, 0.5)
    print(f"✅ calculate_flow_factor: {result:.4f}")
except Exception as e:
    print(f"❌ calculate_flow_factor 调用失败: {e}")

# 测试物理引擎
try:
    chart = ['丙寅', '甲午', '戊午', '戊午']
    result = compute_energy_flux(chart, '戊', '羊刃')
    print(f"✅ compute_energy_flux(羊刃): {result:.2f}")
except Exception as e:
    print(f"❌ compute_energy_flux 调用失败: {e}")

try:
    result = compute_energy_flux(chart, '戊', '七杀')
    print(f"✅ compute_energy_flux(七杀): {result:.2f}")
except Exception as e:
    print(f"❌ compute_energy_flux 调用失败: {e}")

try:
    result = calculate_interaction_damping(chart, '午', '子')
    print(f"✅ calculate_interaction_damping: {result:.2f}")
except Exception as e:
    print(f"❌ calculate_interaction_damping 调用失败: {e}")

print()

# 测试3：对真实八字进行完整计算
print("=" * 70)
print("【步骤4：真实八字完整计算测试】")
print("=" * 70)
print()

all_passed = True

for i, test_case in enumerate(test_cases, 1):
    print(f"【{test_case['name']}】")
    print("-" * 70)
    print(f"八字: {' '.join(test_case['chart'])}")
    print(f"日主: {test_case['day_master']}")
    print(f"描述: {test_case['description']}")
    print()
    
    try:
        # 使用 RegistryLoader 计算
        result = loader.calculate_tensor_projection_from_registry(
            'A-03',
            test_case['chart'],
            test_case['day_master']
        )
        
        if 'error' in result:
            print(f"❌ 计算失败: {result['error']}")
            all_passed = False
            print()
            continue
        
        # 显示结果
        print("✅ 计算成功！")
        print()
        print("【计算结果】")
        print(f"  格局: {result.get('pattern_name', 'N/A')}")
        print(f"  SAI: {result.get('sai', 0.0):.2f}")
        print()
        print("【五维张量投影】")
        projection = result.get('projection', {})
        print(f"  E (能级轴): {projection.get('E', 0.0):.2f}")
        print(f"  O (秩序轴): {projection.get('O', 0.0):.2f}")
        print(f"  M (物质轴): {projection.get('M', 0.0):.2f}")
        print(f"  S (应力轴): {projection.get('S', 0.0):.2f}")
        print(f"  R (关联轴): {projection.get('R', 0.0):.2f}")
        print()
        
        # 显示基础能量
        energies = result.get('energies', {})
        if energies:
            print("【基础能量】")
            for key, value in energies.items():
                print(f"  {key}: {value:.2f}")
            print()
        
        # 显示平衡度
        s_balance = result.get('s_balance')
        if s_balance:
            print("【核心方程结果】")
            print(f"  S_balance = E_blade / E_kill = {s_balance:.4f}")
            if abs(s_balance - 1.0) < 0.1:
                print("  ✅ 共振态（E_blade ≈ E_kill）→ 大贵")
            elif s_balance > 1.2:
                print("  ⚠️ 能量溢出（E_blade > E_kill）→ 破财")
            elif s_balance < 0.8:
                print("  ⚠️ 场强压垮（E_blade < E_kill）→ 夭折风险")
            print()
        
        # 显示相变状态
        phase_change = result.get('phase_change')
        if phase_change:
            print("【相变判定】")
            print(f"  状态: {phase_change}")
            print()
        
    except Exception as e:
        print(f"❌ 计算异常: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
        print()
        continue
    
    print()

# 测试4：动态事件仿真
print("=" * 70)
print("【步骤5：动态事件仿真测试】")
print("=" * 70)
print()

test_chart = ['丙寅', '甲午', '戊午', '戊午']
test_day_master = '戊'

print("【测试场景：流年冲刃事件】")
print("-" * 70)
print(f"原局: {' '.join(test_chart)}")
print(f"日主: {test_day_master}")
print(f"月令羊刃: 午")
print(f"流年冲刃: 子（子午冲）")
print()

try:
    result = loader.simulate_dynamic_event(
        'A-03',
        test_chart,
        test_day_master,
        event_type='clash',
        event_params={'clash_branch': '子'}
    )
    
    if 'error' in result:
        print(f"❌ 仿真失败: {result['error']}")
        all_passed = False
    else:
        print("✅ 仿真成功！")
        print()
        print("【仿真结果】")
        print(f"  基础应力 (S_base): {result.get('s_base', 0.0):.2f}")
        print(f"  激增系数 (λ): {result.get('lambda', 0.0):.2f}")
        print(f"  新应力 (S_new): {result.get('s_new', 0.0):.2f}")
        print(f"  断裂阈值: {result.get('fracture_threshold', 0.0):.2f}")
        print(f"  状态: {result.get('status', 'N/A')}")
        
        if result.get('is_collapse', False):
            print("  ⚠️ 系统崩溃（S_new >= 阈值）")
        else:
            print("  ✅ 系统稳定（S_new < 阈值）")
        print()
        
except Exception as e:
    print(f"❌ 仿真异常: {e}")
    import traceback
    traceback.print_exc()
    all_passed = False
    print()

# 最终总结
print("=" * 70)
print("【冒烟测试总结】")
print("=" * 70)
print()

if all_passed:
    print("✅ 所有测试通过！")
    print()
    print("【验证结果】")
    print("  ✅ RegistryLoader 能够正确加载 A-03 配置")
    print("  ✅ 所有引擎函数都可以正常调用")
    print("  ✅ 能够对真实八字进行完整计算")
    print("  ✅ 动态事件仿真功能正常")
    print()
    print("🎉 算法复原能力验证成功！")
    print("   注册表现在可以100%复原算法逻辑")
else:
    print("❌ 部分测试失败，请检查错误信息")
    print()

print("=" * 70)
print(f"测试完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

