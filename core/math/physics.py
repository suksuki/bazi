"""
八字物理层 (Bazi Physics Math)
==============================

提供专属于八字命理物理引擎的数学公式。
"""

import math
import numpy as np
from .kernels import expit

def calculate_control_damage(attacker_energy: float, defender_energy: float, base_impact: float = 0.8) -> float:
    """
    [V9.7 FINAL] Sigmoid 伤害模型。
    使用 Sigmoid 函数计算攻防差导致的最终能量折损，并有 50% 的硬钳位保护。
    """
    if attacker_energy <= 0 or defender_energy <= 0:
        return 0.0

    k_smoothness = 5.0 
    diff = attacker_energy - defender_energy
    
    # Sigmoid 激活
    activation = expit(diff / k_smoothness)
    
    raw_damage = defender_energy * base_impact * activation
    max_allowed = defender_energy * 0.5
    
    return min(raw_damage, max_allowed)
    return min(raw_damage, max_allowed)

def calculate_impedance_mismatch(attacker_energy: float, defender_energy: float, 
                               threshold: float = 4.0, base_recoil: float = 0.3, 
                               inverse_recoil_multiplier: float = 2.0) -> tuple[float, float, bool]:
    """
    [V12.3] 阻抗失配计算 (Impedance Mismatch Calculation).
    判断是否触发"反克" (Inverse Control)。
    
    Args:
        attacker_energy: 攻击方能量
        defender_energy: 防守方能量
        threshold: 反克阈值 (Impedance Threshold), 默认 4.0
        base_recoil: 基础反冲系数
        inverse_recoil_multiplier: 反克触发时的反冲倍率
        
    Returns:
        (damage_modifier, effective_recoil_factor, is_inverse)
        - damage_modifier: 伤害修正系数 (正常=1.0, 反克=0.1)
        - effective_recoil_factor: 最终反冲系数
        - is_inverse: 是否触发反克
    """
    if attacker_energy <= 0.1: return 0.0, 0.0, False
    
    # 防止除以零
    ratio = defender_energy / attacker_energy if attacker_energy > 0.1 else 999.0
    
    if ratio > threshold:
        # 触发反克 (Inverse Control)
        # 伤害修正 -> 0.05 (蚍蜉撼树) - Matches verification script
        damage_mod = 0.05
        
        # 反冲系数 -> base * multiplier * log10(ratio) (反噬随差距指数级增加)
        # 模拟全反射叠加
        log_factor = math.log10(ratio) if ratio > 1.0 else 1.0
        recoil_factor = base_recoil * inverse_recoil_multiplier * log_factor
        
        return damage_mod, recoil_factor, True
    else:
        # 正常克制
        return 1.0, base_recoil, False

def calculate_shielding_effect(damage_raw: float, target_element: str, era_element: str, 
                             shield_factor: float = 0.5) -> float:
    """
    [V12.3] 环境屏蔽效应 (Environmental Shielding).
    如果环境属性与受冲属性一致，则提供护盾。
    
    Args:
        damage_raw: 原始伤害
        target_element: 受冲节点属性
        era_element: 时代/地理属性
        shield_factor: 屏蔽系数 (0.5 means 50 reduction)
        
    Returns:
        float: 实际生效伤害 (Effective Damage)
    """
    if target_element == era_element:
        # 法拉第笼效应
        return damage_raw * (1.0 - shield_factor)
    return damage_raw

def calculate_generation(mother_energy: float, efficiency: float, threshold: float = 10.0) -> float:
    """
    [V9.4] 阈值生发模型 (Activation Energy)。
    只有当母体能量超过阈值时，才能产生后续生发，模拟“水多木漂”或“湿木不燃”的物理边界。
    """
    effective_source = mother_energy - threshold
    if effective_source <= 0:
        return 0.0
    return effective_source * efficiency

def quantum_tunneling_probability(barrier_height: float, particle_energy: float, barrier_width: float = 1.0) -> float:
    """量子隧穿概率（模拟墓库开启）"""
    if particle_energy >= barrier_height:
        return 1.0
    energy_deficit = barrier_height - particle_energy
    if energy_deficit <= 0: return 1.0
    return np.exp(-2.0 * np.sqrt(energy_deficit) * barrier_width)

def phase_transition_energy(strength_normalized: float, base_energy: float = 100.0, phase_point: float = 0.5) -> float:
    """相变能量模型 ( Landau 简化版)"""
    if strength_normalized > phase_point:
        excess = strength_normalized - phase_point
        return base_energy * (1.0 + excess ** 2 * 0.5)
    else:
        deficit = phase_point - strength_normalized
        return base_energy * (1.0 - deficit * 0.5)
