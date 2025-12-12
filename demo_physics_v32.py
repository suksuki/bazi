#!/usr/bin/env python3
"""
V32.0 Physics Kernel Demo
演示第一性原理物理模型的使用
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.physics_kernel import PhysicsParameters, ParticleDefinitions, GeometricInteraction
from core.dynamics_engine import (
    DynamicsEngine, SpacetimeEngine, SpatialCorrection,
    ProbabilityEngine, ParameterOptimizer
)
import numpy as np


def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def demo_particle_definitions():
    """演示粒子定义"""
    print_section("Definition 1 & 2: Particle Phases")
    
    # 天干波形态
    print("天干 - 波形态 (Stems - Waveforms):")
    for stem in ['甲', '丙', '戊', '庚', '壬']:
        props = ParticleDefinitions.get_stem_properties(stem)
        print(f"  {stem}: {props['waveform']} - {props['description']}")
        print(f"      Element: {props['element']}, Spin: {props['spin']:+d}, Hetu: {props['hetu_number']}")
    
    print("\n地支 - 场域环境 (Branches - Field Environments):")
    for branch in ['子', '寅', '辰', '午', '申', '戌']:
        props = ParticleDefinitions.get_branch_properties(branch)
        print(f"  {branch}: {props['environment']} ({props['description']})")
        print(f"      Phase Angle: {props['phase_angle']}°, Season: {props['season']}")


def demo_geometric_interaction():
    """演示几何交互"""
    print_section("Definition 4: Geometric Interaction")
    
    params = PhysicsParameters()
    geo = GeometricInteraction(params)
    
    # 测试地支交互
    test_pairs = [
        ('子', '午'),  # 180° - Chong
        ('寅', '午'),  # 120° - SanHe
        ('子', '丑'),  # 30° - No major interaction
        ('卯', '酉'),  # 180° - Chong
    ]
    
    print("地支几何交互:")
    for b1, b2 in test_pairs:
        angle = geo.calculate_angular_difference(b1, b2)
        interaction = geo.identify_interaction(b1, b2)
        
        if interaction:
            print(f"  {b1} ↔ {b2}: {angle}° → {interaction['type']}")
            print(f"      {interaction['description']}, Strength: {interaction['strength']}")
        else:
            print(f"  {b1} ↔ {b2}: {angle}° → No major interaction")
    
    # 测试天干河图共振
    print("\n天干河图共振:")
    hetu_pairs = [
        ('甲', '己'),  # 1-6
        ('丙', '辛'),  # 3-8
        ('戊', '癸'),  # 5-10
    ]
    
    for s1, s2 in hetu_pairs:
        resonance = geo.check_hetu_resonance(s1, s2)
        if resonance:
            print(f"  {resonance['description']}")


def demo_dynamics():
    """演示动力学计算"""
    print_section("Definition 5: Dynamics & Work")
    
    params = PhysicsParameters()
    dyn = DynamicsEngine(params)
    
    # 通根计算
    print("通根 (Rooting) 计算:")
    test_cases = [
        ('甲', '寅', 0),  # 甲在寅，同柱
        ('甲', '卯', 1),  # 甲在卯，相邻
        ('丙', '巳', 0),  # 丙在巳，同柱
    ]
    
    for stem, branch, dist in test_cases:
        strength = dyn.calculate_rooting_strength(stem, branch, dist)
        print(f"  {stem} → {branch} (距离={dist}): 通根力 = {strength:.3f}")
    
    # 能量流计算
    print("\n能量流 (Energy Flow) 计算:")
    flow_cases = [
        ('Wood', 'Fire', 1, 100),   # 木生火
        ('Water', 'Fire', 1, 100),  # 水克火
        ('Metal', 'Metal', 0, 100), # 金金共振
    ]
    
    for src, tgt, dist, energy in flow_cases:
        flow = dyn.calculate_energy_flow(src, tgt, dist, energy)
        print(f"  {src} → {tgt} (距离={dist}):")
        print(f"      类型: {flow['flow_type']}, 效率: {flow['efficiency']:.2f}")
        print(f"      传递能量: {flow['transferred_energy']:.1f} eV")


def demo_spacetime():
    """演示时空系统"""
    print_section("Definition 6: Spacetime System")
    
    params = PhysicsParameters()
    st = SpacetimeEngine(params)
    
    # 原始状态
    original_state = {
        'chart': '甲寅年 丙午月 戊辰日 壬子时',
        'energy': 100
    }
    
    # 应用大运
    print("应用大运 (Da Yun - Static Background):")
    state_with_dy = st.apply_dayun_field(original_state, '甲', '寅')
    print(f"  大运: {state_with_dy['dayun_field']['stem']}{state_with_dy['dayun_field']['branch']}")
    print(f"  场强: {state_with_dy['dayun_field']['field_strength']}")
    print(f"  常数重写系数: {state_with_dy['dayun_field']['constant_rewrite_factor']}")
    
    # 应用流年
    print("\n应用流年 (Liu Nian - Dynamic Trigger):")
    final_state = st.apply_liunian_trigger(state_with_dy, '丙', '午')
    print(f"  流年: {final_state['liunian_trigger']['stem']}{final_state['liunian_trigger']['branch']}")
    print(f"  冲击强度: {final_state['liunian_trigger']['impact_strength']}")
    print(f"  触发阈值: {final_state['liunian_trigger']['trigger_threshold']}")


def demo_spatial_correction():
    """演示空间修正"""
    print_section("Definition 7: Spatial Correction (K_geo)")
    
    params = PhysicsParameters()
    spatial = SpatialCorrection(params)
    
    # 测试不同地理位置
    locations = [
        ("北京", 39.9, 116.4, "inland"),
        ("上海", 31.2, 121.5, "coastal"),
        ("拉萨", 29.7, 91.1, "mountain"),
    ]
    
    print("地理位置修正:")
    for city, lat, lon, terrain in locations:
        lat_mod = spatial.calculate_latitude_modifier(lat)
        terrain_mod = spatial.get_terrain_modifier(terrain)
        
        print(f"  {city} (纬度{lat}°, {terrain}):")
        print(f"      温度系数: {lat_mod:.3f}")
        print(f"      湿度系数: {terrain_mod:.3f}")


def demo_probability():
    """演示概率计算"""
    print_section("Definition 8: Probability Calculation")
    
    params = PhysicsParameters()
    prob = ProbabilityEngine(params)
    
    # 创建波函数
    print("量子波函数 (Wave Function):")
    wf = prob.create_wavefunction(mean=70, uncertainty=15)
    print(f"  均值: {wf['mean']}")
    print(f"  不确定性: {wf['std']}")
    
    # 计算概率
    print("\n概率计算:")
    thresholds = [50, 70, 90]
    for threshold in thresholds:
        p = prob.calculate_probability(wf, threshold)
        classification = prob.classify_outcome(p)
        print(f"  P(X > {threshold}) = {p:.2%} - {classification}")
    
    # 生成样本
    print("\n样本分布:")
    samples = prob.generate_distribution_samples(wf, n_samples=1000)
    print(f"  样本数: {len(samples)}")
    print(f"  样本均值: {np.mean(samples):.1f}")
    print(f"  样本标准差: {np.std(samples):.1f}")
    print(f"  样本范围: [{np.min(samples):.1f}, {np.max(samples):.1f}]")


def demo_parameter_optimization():
    """演示参数优化"""
    print_section("Definition 9: Evolution Mechanism")
    
    params = PhysicsParameters()
    optimizer = ParameterOptimizer(params)
    
    # 模拟验证
    print("参数优化演示:")
    
    # 假设的预测和真实值
    test_cases = [
        (75, 80),
        (65, 70),
        (85, 82),
    ]
    
    validations = []
    for pred, real in test_cases:
        val = optimizer.validate_against_real_case(pred, real)
        validations.append(val)
        print(f"  预测: {val['predicted']}, 实际: {val['real']}")
        print(f"      误差: {val['error']:.1f}, 准确率: {val['accuracy']:.2%}")
    
    # 建议参数调整
    print("\n参数调整建议:")
    param_name = 'sheng_transfer_efficiency'
    current_value = getattr(params, param_name)
    suggested_value = optimizer.suggest_parameter_adjustment(param_name, validations)
    
    print(f"  参数: {param_name}")
    print(f"  当前值: {current_value}")
    print(f"  建议值: {suggested_value:.3f}")
    print(f"  调整量: {suggested_value - current_value:+.3f}")


def demo_parameter_persistence():
    """演示参数持久化"""
    print_section("Parameter Persistence")
    
    # 创建参数
    params = PhysicsParameters()
    
    # 修改一些参数
    params.update_parameter('sheng_transfer_efficiency', 0.75)
    params.update_parameter('dayun_field_strength', 1.2)
    
    # 保存到文件
    output_path = 'config/physics_params_demo.json'
    params.save_to_file(output_path)
    print(f"参数已保存到: {output_path}")
    
    # 重新加载
    params2 = PhysicsParameters(output_path)
    print(f"\n重新加载的参数:")
    print(f"  sheng_transfer_efficiency: {params2.sheng_transfer_efficiency}")
    print(f"  dayun_field_strength: {params2.dayun_field_strength}")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     Antigravity Physics Kernel V32.0 Demo                       ║
║     First Principles Model - Complete Demonstration             ║
║                                                                  ║
║     "NO HARD-CODED PARAMETERS"                                  ║
║     All values are tunable via data regression                  ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # 运行所有演示
    demo_particle_definitions()
    demo_geometric_interaction()
    demo_dynamics()
    demo_spacetime()
    demo_spatial_correction()
    demo_probability()
    demo_parameter_optimization()
    demo_parameter_persistence()
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║     Demo Complete! 演示完成！                                     ║
║                                                                  ║
║     查看完整文档: docs/PHYSICS_KERNEL_V32.md                      ║
║                                                                  ║
║     ⚠️  CRITICAL: 所有参数都是初始估计值                           ║
║     必须通过真实案例进行数据回归和优化！                            ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
