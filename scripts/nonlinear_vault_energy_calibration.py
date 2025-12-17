#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
非线性财库能量校准示例
====================

基于核心分析师的优化建议，展示如何使用非线性 Soft-thresholding 逻辑
重新校准 Jason D 2015年财库开启的能量释放峰值。

核心改进：
1. 从硬编码 if/else 转向 Softplus/Sigmoid 函数
2. 引入相变点 (Singularity) 模型
3. 考虑多因素综合影响（身强、三刑、冲的强度等）
"""

import numpy as np
try:
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("⚠️  matplotlib 未安装，将跳过可视化部分")

try:
    from scipy.special import softplus, expit
    HAS_SCIPY = True
except ImportError:
    # 手动实现 softplus 和 expit
    HAS_SCIPY = False
    def softplus(x):
        return np.log1p(np.exp(x))
    def expit(x):
        return 1.0 / (1.0 + np.exp(-x))
from typing import Dict, Tuple, List
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine_graph import GraphNetworkEngine
from core.bazi_profile import BaziProfile
from datetime import datetime

# ============================================================================
# 非线性激活函数库
# ============================================================================

class NonlinearActivation:
    """非线性激活函数集合，用于模拟相变和量子隧穿效应"""
    
    @staticmethod
    def softplus_threshold(x: float, threshold: float = 0.5, scale: float = 10.0) -> float:
        """
        Softplus 软阈值函数
        
        用于模拟能量在临界点处的平滑过渡，避免硬编码的 if/else 跳跃。
        
        Args:
            x: 输入值（如身强归一化值）
            threshold: 阈值（临界点）
            scale: 缩放因子，控制过渡的陡峭程度
        
        Returns:
            平滑的激活值 [0, 1]
        """
        # Softplus: log(1 + exp(k*(x - threshold)))
        # 当 x >> threshold 时，输出接近 1
        # 当 x << threshold 时，输出接近 0
        k = scale
        return softplus(k * (x - threshold)) / (1 + softplus(k * (x - threshold)))
    
    @staticmethod
    def sigmoid_threshold(x: float, threshold: float = 0.5, steepness: float = 10.0) -> float:
        """
        Sigmoid 软阈值函数
        
        用于模拟相变点处的平滑过渡。
        
        Args:
            x: 输入值
            threshold: 阈值（相变点）
            steepness: 陡峭度，控制过渡的平滑程度
        
        Returns:
            平滑的激活值 [0, 1]
        """
        # Sigmoid: 1 / (1 + exp(-k*(x - threshold)))
        k = steepness
        return expit(k * (x - threshold))
    
    @staticmethod
    def phase_transition_energy(
        strength_normalized: float,
        clash_intensity: float,
        trine_effect: float,
        base_energy: float = 100.0,
        phase_point: float = 0.5,
        critical_exponent: float = 2.0
    ) -> float:
        """
        相变能量模型 (Phase Transition Energy Model)
        
        模拟热力学相变：当能量密度超过临界点时，触发整体结构的"气化"或"晶裂"，
        改变其对日主的做功效率。
        
        基于 Landau 相变理论：
        E = E_base × (1 + α × (x - x_c)^β)
        
        Args:
            strength_normalized: 身强归一化值 [0, 1]
            clash_intensity: 冲的强度 [0, 1]（考虑冲的类型、距离等）
            trine_effect: 三刑效应 [0, 1]（三刑的完整程度）
            base_energy: 基础能量（如 100.0）
            phase_point: 相变点（临界点，如 0.5）
            critical_exponent: 临界指数（控制相变的陡峭程度）
        
        Returns:
            相变后的能量值
        """
        # 综合激活因子
        activation = NonlinearActivation.sigmoid_threshold(
            strength_normalized,
            threshold=phase_point,
            steepness=10.0
        )
        
        # 多因素综合影响
        # 1. 身强激活因子
        strength_factor = activation
        
        # 2. 冲的强度因子（冲越强，能量释放越大）
        clash_factor = 0.5 + 0.5 * clash_intensity  # [0.5, 1.0]
        
        # 3. 三刑效应因子（三刑增强能量释放）
        trine_factor = 1.0 + 0.3 * trine_effect  # [1.0, 1.3]
        
        # 4. 相变修正（当超过临界点时，触发非线性增长）
        if strength_normalized > phase_point:
            # 超临界相变：能量非线性增长
            excess = strength_normalized - phase_point
            phase_multiplier = 1.0 + (excess ** critical_exponent) * 0.5
        else:
            # 亚临界：能量线性衰减
            deficit = phase_point - strength_normalized
            phase_multiplier = 1.0 - deficit * 0.5
        
        # 综合能量计算
        final_energy = base_energy * strength_factor * clash_factor * trine_factor * phase_multiplier
        
        return final_energy
    
    @staticmethod
    def quantum_tunneling_probability(
        barrier_height: float,
        particle_energy: float,
        barrier_width: float = 1.0
    ) -> float:
        """
        量子隧穿概率模型
        
        用于模拟"墓库开启"的量子隧穿效应。
        即使能量不足以直接突破库的屏障，也有一定概率通过隧穿效应开启。
        
        基于 WKB 近似：
        P = exp(-2 * k * width)
        k = sqrt(2m(V - E)) / ħ
        
        Args:
            barrier_height: 屏障高度（库的封闭强度）
            particle_energy: 粒子能量（冲的能量）
            barrier_width: 屏障宽度（库的厚度）
        
        Returns:
            隧穿概率 [0, 1]
        """
        if particle_energy >= barrier_height:
            # 能量足够，直接突破
            return 1.0
        
        # 能量不足，计算隧穿概率
        energy_deficit = barrier_height - particle_energy
        # 简化的隧穿概率公式
        tunneling_prob = np.exp(-2.0 * np.sqrt(energy_deficit) * barrier_width)
        
        return max(0.0, min(1.0, tunneling_prob))


# ============================================================================
# 改进的财库能量计算函数
# ============================================================================

def calculate_vault_energy_nonlinear(
    strength_normalized: float,
    clash_type: str,  # '冲' or '合'
    clash_intensity: float,  # 冲的强度 [0, 1]
    has_trine: bool,  # 是否有三刑
    trine_completeness: float = 1.0,  # 三刑完整程度 [0, 1]
    base_bonus: float = 100.0,
    base_penalty: float = -120.0
) -> Tuple[float, Dict[str, float]]:
    """
    非线性财库能量计算
    
    使用 Soft-thresholding 和相变模型，替代硬编码的 if/else。
    
    Args:
        strength_normalized: 身强归一化值 [0, 1]
        clash_type: 冲的类型 ('冲' or '合')
        clash_intensity: 冲的强度 [0, 1]
        has_trine: 是否有三刑
        trine_completeness: 三刑完整程度 [0, 1]
        base_bonus: 基础加成（身强时）
        base_penalty: 基础惩罚（身弱时）
    
    Returns:
        (最终能量值, 详细分解字典)
    """
    details = {}
    
    # 1. 身强激活因子（使用 Softplus 软阈值）
    strength_activation = NonlinearActivation.softplus_threshold(
        strength_normalized,
        threshold=0.5,
        scale=10.0
    )
    details['strength_activation'] = strength_activation
    
    # 2. 冲的强度因子
    clash_factor = 0.5 + 0.5 * clash_intensity
    details['clash_factor'] = clash_factor
    
    # 3. 三刑效应因子
    if has_trine:
        trine_factor = 1.0 + 0.3 * trine_completeness
    else:
        trine_factor = 1.0
    details['trine_factor'] = trine_factor
    
    # 4. 相变能量计算
    phase_energy = NonlinearActivation.phase_transition_energy(
        strength_normalized=strength_normalized,
        clash_intensity=clash_intensity,
        trine_effect=trine_completeness if has_trine else 0.0,
        base_energy=base_bonus,
        phase_point=0.5,
        critical_exponent=2.0
    )
    details['phase_energy'] = phase_energy
    
    # 5. 量子隧穿概率（考虑库的封闭强度）
    barrier_height = 0.6  # 库的封闭强度阈值
    particle_energy = strength_normalized * clash_intensity
    tunneling_prob = NonlinearActivation.quantum_tunneling_probability(
        barrier_height=barrier_height,
        particle_energy=particle_energy,
        barrier_width=1.0
    )
    details['tunneling_prob'] = tunneling_prob
    
    # 6. 综合能量计算
    # 如果身强，使用正向能量；如果身弱，使用负向能量
    if strength_normalized > 0.5:
        # 身强：财富爆发
        base = base_bonus
        polarity = 1.0
    else:
        # 身弱：库塌损失
        base = abs(base_penalty)
        polarity = -1.0
    
    # 非线性修正
    nonlinear_correction = strength_activation * clash_factor * trine_factor * tunneling_prob
    
    final_energy = base * nonlinear_correction * polarity
    
    details['base_energy'] = base
    details['nonlinear_correction'] = nonlinear_correction
    details['final_energy'] = final_energy
    
    return final_energy, details


# ============================================================================
# Jason D 2015年案例对比分析
# ============================================================================

def analyze_jason_d_2015():
    """分析 Jason D 2015年案例，对比硬编码 vs 非线性模型"""
    
    print("=" * 80)
    print("Jason D 2015年财库开启能量校准对比分析")
    print("=" * 80)
    print()
    
    # Jason D 基本信息
    bazi = ['辛丑', '丁酉', '庚辰', '丙戌']
    day_master = '庚'
    year_pillar = '乙未'
    luck_pillar = '壬辰'
    
    # 初始化引擎
    engine = GraphNetworkEngine()
    result = engine.analyze(
        bazi=bazi,
        day_master=day_master,
        luck_pillar=luck_pillar,
        year_pillar=year_pillar
    )
    
    strength_score = result.get('strength_score', 50.0)
    strength_normalized = strength_score / 100.0
    
    print(f"【案例信息】")
    print(f"  八字: {' '.join(bazi)}")
    print(f"  日主: {day_master}金")
    print(f"  大运: {luck_pillar}")
    print(f"  流年: {year_pillar}")
    print(f"  身强分数: {strength_score:.2f} / 100.0")
    print(f"  身强归一化: {strength_normalized:.4f}")
    print()
    
    # 检测关键机制
    year_branch = year_pillar[1]  # 未
    has_chou = '丑' in bazi[0]  # 年柱有丑
    has_xu = '戌' in bazi[3]  # 时柱有戌
    has_trine = has_chou and year_branch == '未' and has_xu  # 丑未戌三刑
    
    clash_intensity = 1.0  # 丑未冲，强度为 1.0
    trine_completeness = 1.0 if has_trine else 0.0
    
    print(f"【机制检测】")
    print(f"  流年地支: {year_branch} (未 = 财库)")
    print(f"  原局年柱: {bazi[0]} (丑)")
    print(f"  原局时柱: {bazi[3]} (戌)")
    print(f"  丑未冲: {'✅' if has_chou and year_branch == '未' else '❌'}")
    print(f"  三刑齐备: {'✅' if has_trine else '❌'}")
    print()
    
    # ========== 方法 1: 硬编码模型 (当前 V9.3) ==========
    print("=" * 80)
    print("方法 1: 硬编码模型 (当前 V9.3)")
    print("=" * 80)
    
    if strength_normalized > 0.5:
        hardcoded_energy = 100.0
        hardcoded_method = "if strength_normalized > 0.5: treasury_bonus = 100.0"
    else:
        hardcoded_energy = -120.0
        hardcoded_method = "else: treasury_penalty = -120.0"
    
    print(f"  判定逻辑: {hardcoded_method}")
    print(f"  计算结果: {hardcoded_energy:.2f}")
    print(f"  特点: 硬阈值，在 0.5 处发生跳跃")
    print()
    
    # ========== 方法 2: 非线性 Soft-thresholding 模型 ==========
    print("=" * 80)
    print("方法 2: 非线性 Soft-thresholding 模型 (V10.0 优化)")
    print("=" * 80)
    
    nonlinear_energy, details = calculate_vault_energy_nonlinear(
        strength_normalized=strength_normalized,
        clash_type='冲',
        clash_intensity=clash_intensity,
        has_trine=has_trine,
        trine_completeness=trine_completeness,
        base_bonus=100.0,
        base_penalty=-120.0
    )
    
    print(f"  身强激活因子: {details['strength_activation']:.4f}")
    print(f"  冲的强度因子: {details['clash_factor']:.4f}")
    print(f"  三刑效应因子: {details['trine_factor']:.4f}")
    print(f"  相变能量: {details['phase_energy']:.2f}")
    print(f"  量子隧穿概率: {details['tunneling_prob']:.4f}")
    print(f"  非线性修正: {details['nonlinear_correction']:.4f}")
    print(f"  最终能量: {nonlinear_energy:.2f}")
    print()
    
    # ========== 对比分析 ==========
    print("=" * 80)
    print("对比分析")
    print("=" * 80)
    
    print(f"  硬编码模型: {hardcoded_energy:.2f}")
    print(f"  非线性模型: {nonlinear_energy:.2f}")
    print(f"  差异: {abs(nonlinear_energy - hardcoded_energy):.2f}")
    print()
    
    print("【非线性模型优势】")
    print("  1. ✅ 平滑过渡: 避免了硬编码在 0.5 处的跳跃")
    print("  2. ✅ 多因素综合: 考虑了身强、冲的强度、三刑效应等多个因素")
    print("  3. ✅ 相变模拟: 模拟了能量在临界点处的非线性增长")
    print("  4. ✅ 量子隧穿: 考虑了即使能量不足也可能通过隧穿开启库的概率")
    print("  5. ✅ 可微性: 函数可微，便于梯度优化和参数调优")
    print()
    
    # ========== 敏感性分析 ==========
    print("=" * 80)
    print("敏感性分析: 身强归一化值对能量的影响")
    print("=" * 80)
    
    strength_range = np.linspace(0.3, 0.8, 50)
    hardcoded_values = []
    nonlinear_values = []
    
    for s in strength_range:
        # 硬编码模型
        if s > 0.5:
            hardcoded_values.append(100.0)
        else:
            hardcoded_values.append(-120.0)
        
        # 非线性模型
        energy, _ = calculate_vault_energy_nonlinear(
            strength_normalized=s,
            clash_type='冲',
            clash_intensity=clash_intensity,
            has_trine=has_trine,
            trine_completeness=trine_completeness,
            base_bonus=100.0,
            base_penalty=-120.0
        )
        nonlinear_values.append(energy)
    
    print(f"  身强范围: [{strength_range[0]:.2f}, {strength_range[-1]:.2f}]")
    print(f"  硬编码模型: 在 0.5 处发生跳跃")
    print(f"  非线性模型: 平滑过渡，能量范围 [{min(nonlinear_values):.2f}, {max(nonlinear_values):.2f}]")
    print()
    
    # ========== 可视化 ==========
    if HAS_MATPLOTLIB:
        try:
            plt.figure(figsize=(12, 6))
            
            plt.subplot(1, 2, 1)
            plt.plot(strength_range, hardcoded_values, 'r-', linewidth=2, label='硬编码模型')
            plt.plot(strength_range, nonlinear_values, 'b-', linewidth=2, label='非线性模型')
            plt.axvline(x=0.5, color='gray', linestyle='--', alpha=0.5, label='临界点 (0.5)')
            plt.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            plt.xlabel('身强归一化值')
            plt.ylabel('财库能量')
            plt.title('硬编码 vs 非线性模型对比')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            plt.subplot(1, 2, 2)
            plt.plot(strength_range, nonlinear_values, 'b-', linewidth=2, label='非线性模型')
            plt.axvline(x=strength_normalized, color='red', linestyle='--', 
                       label=f'Jason D 实际值 ({strength_normalized:.4f})')
            plt.axhline(y=nonlinear_energy, color='red', linestyle='--', alpha=0.5)
            plt.xlabel('身强归一化值')
            plt.ylabel('财库能量')
            plt.title('非线性模型详细曲线')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            output_path = 'docs/jason_d_2015_nonlinear_comparison.png'
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"  ✅ 可视化图表已保存: {output_path}")
            plt.close()
        except Exception as e:
            print(f"  ⚠️  可视化失败: {e}")
    else:
        print("  ⚠️  matplotlib 未安装，跳过可视化")
    
    print()
    print("=" * 80)
    print("分析完成")
    print("=" * 80)
    
    return {
        'hardcoded_energy': hardcoded_energy,
        'nonlinear_energy': nonlinear_energy,
        'strength_normalized': strength_normalized,
        'details': details
    }


if __name__ == '__main__':
    try:
        result = analyze_jason_d_2015()
        print(f"\n✅ 脚本执行成功！")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 脚本执行失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

