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
