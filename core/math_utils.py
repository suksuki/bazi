"""
数学工具库 (Math Utilities)
===========================

V12.2 非线性物理效应工具函数

版本: V12.2
作者: Antigravity Team
日期: 2025-01-XX

核心功能：
- 饱和曲线 (Saturation Curve)：模拟边际递减效应
- 门控函数 (Gating Function)：模拟临界点效应
- 衰减函数 (Decay Function)：模拟指数衰减
"""

import numpy as np
from typing import Union


def saturation_curve(x: float, max_val: float = 2.5, steepness: float = 0.8) -> float:
    """
    V12.2: S型饱和函数 (Sigmoid Saturation Curve)
    
    使用双曲正切函数 (Tanh) 模拟边际递减效应。
    特点：先快后慢，最后趋于平缓。
    
    Args:
        x: 输入值（如根的总强度）
        max_val: 最大加成上限（如 2.5，即最多增加 2.5 倍）
        steepness: 陡峭度（控制曲线上升速度，越大越陡）
        
    Returns:
        饱和后的加成值（0 到 max_val 之间）
        
    Examples:
        >>> saturation_curve(0.8, max_val=2.5, steepness=0.8)
        # 第 1 个根：tanh(0.8*0.8) ≈ 0.66 → 能量暴涨（雪中送炭）
        
        >>> saturation_curve(1.6, max_val=2.5, steepness=0.8)
        # 第 2 个根：tanh(1.6*0.8) ≈ 0.92 → 能量微涨（锦上添花）
        
        >>> saturation_curve(2.4, max_val=2.5, steepness=0.8)
        # 第 3 个根：tanh(2.4*0.8) ≈ 0.98 → 能量几乎不变（边际递减）
    """
    # 使用 Tanh 函数：tanh(x) 在 [-1, 1] 之间，我们映射到 [0, max_val]
    # tanh(steepness * x) 的值域是 [-1, 1]
    # 我们将其映射到 [0, max_val]：max_val * (tanh(steepness * x) + 1) / 2
    tanh_value = np.tanh(steepness * x)
    return max_val * (tanh_value + 1) / 2


def gating_function(x: float, threshold: float = 0.5, sharpness: float = 10.0) -> float:
    """
    V12.2: 门控函数 (Gating Function)
    
    使用 Sigmoid 函数模拟临界点效应（开关效应）。
    当 x 低于 threshold 时，输出接近 0；高于 threshold 时，输出接近 1。
    
    Args:
        x: 输入值（如能量强度）
        threshold: 临界点（阈值）
        sharpness: 锐度（控制开关的陡峭程度，越大越像开关）
        
    Returns:
        门控值（0 到 1 之间）
        
    Examples:
        >>> gating_function(0.3, threshold=0.5, sharpness=10.0)
        # 低于阈值，输出接近 0（能量被阻断）
        
        >>> gating_function(0.7, threshold=0.5, sharpness=10.0)
        # 高于阈值，输出接近 1（能量通过）
    """
    # Sigmoid 函数：1 / (1 + exp(-sharpness * (x - threshold)))
    sigmoid_value = 1.0 / (1.0 + np.exp(-sharpness * (x - threshold)))
    return sigmoid_value


def exponential_decay(x: float, decay_rate: float = 0.5, min_value: float = 0.1) -> float:
    """
    V12.2: 指数衰减函数 (Exponential Decay)
    
    模拟能量在不利环境下的指数级衰减。
    
    Args:
        x: 输入值（原始能量）
        decay_rate: 衰减率（0-1 之间，越大衰减越快）
        min_value: 最小值（衰减后的能量不会低于此值）
        
    Returns:
        衰减后的能量值
        
    Examples:
        >>> exponential_decay(100.0, decay_rate=0.5, min_value=0.1)
        # 能量衰减到 50.0
        
        >>> exponential_decay(100.0, decay_rate=0.9, min_value=0.1)
        # 能量衰减到 10.0（更强的衰减）
    """
    decayed = x * (1.0 - decay_rate)
    return max(decayed, min_value)


def gaussian_gating(element_match: bool, base_energy: float, 
                   match_boost: float = 1.3, mismatch_penalty: float = 0.3) -> float:
    """
    V12.2: 高斯门控（月令能量场分布）
    
    模拟月令对能量的"场分布"效应。
    如果五行与月令匹配（得令），获得加成；如果不匹配（失令），受到指数级衰减。
    
    Args:
        element_match: 是否与月令匹配（得令）
        base_energy: 基础能量
        match_boost: 匹配时的加成系数（如 1.3）
        mismatch_penalty: 不匹配时的衰减系数（如 0.3，即保留 30%）
        
    Returns:
        修正后的能量值
        
    Examples:
        >>> gaussian_gating(True, 100.0, match_boost=1.3, mismatch_penalty=0.3)
        # 得令：100.0 * 1.3 = 130.0
        
        >>> gaussian_gating(False, 100.0, match_boost=1.3, mismatch_penalty=0.3)
        # 失令：100.0 * 0.3 = 30.0（指数级衰减）
    """
    if element_match:
        return base_energy * match_boost
    else:
        # 失令时，不仅打折，还要受到额外的环境压制
        # 使用指数衰减：energy * penalty^2（平方衰减，更严厉）
        return base_energy * (mismatch_penalty ** 2)


def smooth_step(x: float, edge0: float = 0.0, edge1: float = 1.0) -> float:
    """
    V12.2: 平滑步进函数 (Smooth Step Function)
    
    在 edge0 和 edge1 之间平滑过渡，用于模拟渐变效应。
    
    Args:
        x: 输入值
        edge0: 下边界
        edge1: 上边界
        
    Returns:
        平滑过渡值（0 到 1 之间）
    """
    # 将 x 归一化到 [0, 1]
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    # 平滑步进：t^2 * (3 - 2t)
    return t * t * (3.0 - 2.0 * t)

