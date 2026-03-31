"""
数学内核层 (Math Kernels)
==========================

提供基础的非线性激活函数。
"""

import numpy as np

def expit(x: float) -> float:
    """Sigmoid 函数: 1 / (1 + exp(-x))"""
    if x > 20: return 1.0
    if x < -20: return 0.0
    return 1.0 / (1.0 + np.exp(-x))

def softplus(x: float) -> float:
    """Softplus 函数: log(1 + exp(x))"""
    if x > 20: return x
    return np.log1p(np.exp(x))

def gating_function(x: float, threshold: float = 0.5, sharpness: float = 10.0) -> float:
    """门控函数 (Sigmoid 变体)"""
    return expit(sharpness * (x - threshold))

def sigmoid_threshold(x: float, threshold: float = 0.5, steepness: float = 10.0) -> float:
    """Sigmoid 阈值激活"""
    return expit(steepness * (x - threshold))

def softplus_threshold(x: float, threshold: float = 0.5, scale: float = 10.0) -> float:
    """Softplus 阈值激活"""
    numerator = softplus(scale * (x - threshold))
    denominator = 1 + softplus(scale * (x - threshold))
    return numerator / denominator if denominator > 0 else 0.0
