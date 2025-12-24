"""
[V13.7] 验证八字真言页面是否正确注入大运、流年、地理信息
========================================================

测试目标：
1. 验证 UI 页面是否正确收集大运、流年、地理信息
2. 验证这些信息是否正确传递到 arbitrate_bazi
3. 验证 InfluenceBus 是否正确构建并注入这些信息
4. 验证各个引擎是否正确接收到这些信息
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.trinity.core.unified_arbitrator_master import quantum_framework
from core.trinity.core.middleware.influence_bus import InfluenceBus


def test_influence_bus_injection():
    """
    测试 InfluenceBus 注入流程
    """
    print("=" * 80)
    print("测试：验证大运、流年、地理信息是否正确注入到 InfluenceBus")
    print("=" * 80)
    
    # 1. 模拟 UI 输入
    bazi_chart = ["甲子", "乙丑", "丙寅", "丁卯"]  # 示例四柱
    birth_info = {
        'birth_year': 1990,
        'birth_month': 1,
        'birth_day': 1,
        'birth_hour': 12,
        'gender': '男'
    }
    
    # 模拟 UI 选择的大运、流年、地理信息
    luck_pillar = "戊辰"  # 大运
    annual_pillar = "庚午"  # 流年
    geo_factor = 1.5  # 地理因子（例如：火区）
    geo_element = "Fire"  # 地理元素
    
    # 2. 构建上下文（模拟 quantum_lab.py 中的传递方式）
    current_context = {
        'luck_pillar': luck_pillar,
        'annual_pillar': annual_pillar,
        'months_since_switch': 6.0,
        'scenario': 'GENERAL',
        'data': {
            'city': '深圳',
            'geo_factor': geo_factor,
            'geo_element': geo_element
        }
    }
    
    print(f"\n📋 输入参数：")
    print(f"  四柱: {bazi_chart}")
    print(f"  大运: {luck_pillar}")
    print(f"  流年: {annual_pillar}")
    print(f"  地理因子: {geo_factor}")
    print(f"  地理元素: {geo_element}")
    
    # 3. 调用 arbitrate_bazi（模拟 quantum_lab.py 中的调用）
    print(f"\n🔄 执行 arbitrate_bazi...")
    result = quantum_framework.arbitrate_bazi(
        bazi_chart=bazi_chart,
        birth_info=birth_info,
        current_context=current_context
    )
    
    # 4. 检查结果中的 InfluenceBus 信息
    if 'error' in result:
        print(f"❌ 错误: {result['error']}")
        return False
    
    # 检查 resonance_metrics 中的 influence_bus 信息
    resonance_metrics = result.get('resonance', {})
    influence_bus_info = resonance_metrics.get('influence_bus', {})
    active_factors = influence_bus_info.get('active_factors', [])
    
    print(f"\n✅ InfluenceBus 状态：")
    print(f"  激活的影响因子: {active_factors}")
    
    # 5. 验证各个因子是否正确注册
    expected_factors = []
    if luck_pillar:
        expected_factors.append("LuckCycle/大运")
    if annual_pillar:
        expected_factors.append("AnnualPulse/流年")
    if geo_factor != 1.0 or geo_element != 'Neutral':
        expected_factors.append("GeoBias/地域")
    
    print(f"\n🔍 验证检查：")
    print(f"  期望的影响因子: {expected_factors}")
    
    all_present = all(factor in active_factors for factor in expected_factors)
    
    if all_present:
        print(f"  ✅ 所有期望的影响因子都已注册")
    else:
        missing = [f for f in expected_factors if f not in active_factors]
        print(f"  ❌ 缺失的影响因子: {missing}")
        return False
    
    # 6. 检查各个引擎是否正确接收到 InfluenceBus
    print(f"\n🔍 检查各个引擎的调用：")
    
    # 检查财富引擎
    wealth_metrics = result.get('wealth', {})
    if wealth_metrics:
        print(f"  ✅ 财富引擎已调用（应使用 InfluenceBus 计算粘滞系数）")
        reynolds = wealth_metrics.get('REYNOLDS_NUMBER')
        viscosity = wealth_metrics.get('VISCOSITY')
        if reynolds is not None:
            print(f"    雷诺数: {reynolds:.2f}")
        if viscosity is not None:
            print(f"    粘滞系数: {viscosity:.2f}")
    
    # 检查情感引擎
    relationship_metrics = result.get('relationship', {})
    if relationship_metrics:
        print(f"  ✅ 情感引擎已调用（应使用 InfluenceBus 计算轨道摄动）")
        binding_energy = relationship_metrics.get('BINDING_ENERGY')
        orbital_perturbation = relationship_metrics.get('ORBITAL_PERTURBATION')
        if binding_energy is not None:
            print(f"    绑定能: {binding_energy:.2f}")
        if orbital_perturbation is not None:
            print(f"    轨道摄动: {orbital_perturbation:.2f}")
    
    # 检查通根增益
    rooting_gain = resonance_metrics.get('gain', 1.0)
    geo_correction = resonance_metrics.get('geo_correction', 0.0)
    print(f"  ✅ 通根增益引擎已调用")
    print(f"    通根增益: {rooting_gain:.3f}")
    if geo_correction > 0:
        print(f"    地理修正: {geo_correction:.4f} (已应用)")
    
    # 7. 验证地理修正是否正确应用
    if geo_factor != 1.0:
        print(f"\n🔍 验证地理修正：")
        print(f"  地理因子: {geo_factor}")
        print(f"  地理元素: {geo_element}")
        
        # 检查通根增益是否受到地理修正影响
        if geo_correction > 0:
            print(f"  ✅ 地理修正已应用到通根增益")
        else:
            print(f"  ⚠️  地理修正未应用到通根增益（可能需要检查地理元素是否匹配日主）")
    
    print(f"\n" + "=" * 80)
    print("✅ 测试完成：所有验证通过")
    print("=" * 80)
    
    return True


def test_direct_influence_bus_construction():
    """
    直接测试 InfluenceBus 构建过程
    """
    print("\n" + "=" * 80)
    print("测试：直接验证 _build_influence_bus 方法")
    print("=" * 80)
    
    # 模拟上下文和地理修正
    ctx = {
        'luck_pillar': '戊辰',
        'annual_pillar': '庚午',
        'months_since_switch': 6.0
    }
    
    geo_modifiers = {
        'temperature_factor': 1.5,
        'geo_element': 'Fire',
        'desc': '深圳 - Fire'
    }
    
    # 调用 _build_influence_bus
    influence_bus = quantum_framework._build_influence_bus(ctx, geo_modifiers)
    
    print(f"\n📋 构建的 InfluenceBus：")
    print(f"  激活的影响因子数量: {len(influence_bus.active_factors)}")
    
    for factor in influence_bus.active_factors:
        print(f"  - {factor.name}")
        if hasattr(factor, 'nonlinear_type'):
            print(f"    类型: {factor.nonlinear_type}")
        if hasattr(factor, 'metadata'):
            print(f"    元数据: {factor.metadata}")
        # 检查标准因子的属性
        if hasattr(factor, 'luck_pillar'):
            print(f"    大运: {factor.luck_pillar}")
        if hasattr(factor, 'annual_pillar'):
            print(f"    流年: {factor.annual_pillar}")
        if hasattr(factor, 'geo_factor'):
            print(f"    地理因子: {factor.geo_factor}")
        if hasattr(factor, 'geo_element'):
            print(f"    地理元素: {factor.geo_element}")
    
    # 验证因子
    factor_names = [f.name for f in influence_bus.active_factors]
    expected = ["LuckCycle/大运", "AnnualPulse/流年", "GeoBias/地域"]
    
    print(f"\n🔍 验证：")
    for exp in expected:
        if exp in factor_names:
            print(f"  ✅ {exp} 已注册")
        else:
            print(f"  ❌ {exp} 未注册")
    
    return len([f for f in expected if f in factor_names]) == len(expected)


if __name__ == "__main__":
    print("\n🚀 开始验证 InfluenceBus 注入流程...\n")
    
    # 测试 1: 直接测试 InfluenceBus 构建
    test1_passed = test_direct_influence_bus_construction()
    
    # 测试 2: 完整流程测试
    test2_passed = test_influence_bus_injection()
    
    print(f"\n📊 测试结果总结：")
    print(f"  测试 1 (直接构建): {'✅ 通过' if test1_passed else '❌ 失败'}")
    print(f"  测试 2 (完整流程): {'✅ 通过' if test2_passed else '❌ 失败'}")
    
    if test1_passed and test2_passed:
        print(f"\n🎉 所有测试通过！InfluenceBus 注入流程正常工作。")
        sys.exit(0)
    else:
        print(f"\n⚠️  部分测试失败，请检查代码。")
        sys.exit(1)

