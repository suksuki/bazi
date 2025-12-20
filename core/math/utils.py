"""
数学工具层 (Math Utilities)
==========================

提供通用的数学辅助函数，如饱和曲线、衰减函数等。
"""

import numpy as np

def saturation_curve(x: float, max_val: float = 2.5, steepness: float = 0.8) -> float:
    """S型饱和函数 (模拟边际递减效应)"""
    return max_val * np.tanh(steepness * x)

def exponential_decay(x: float, decay_rate: float = 0.5, min_value: float = 0.1) -> float:
    """指数衰减函数"""
    return max(x * (1.0 - decay_rate), min_value)

def smooth_step(x: float, edge0: float = 0.0, edge1: float = 1.0) -> float:
    """平滑步进函数"""
    t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)

def gaussian_gating(element_match: bool, base_energy: float, 
                   match_boost: float = 1.3, mismatch_penalty: float = 0.3) -> float:
    """高斯门控模型"""
    if element_match:
        return base_energy * match_boost
    return base_energy * (mismatch_penalty ** 2)
