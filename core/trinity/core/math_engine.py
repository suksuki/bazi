"""
Quantum Trinity: Math Engine (V1.0)
=====================================
Unified mathematical primitives for the Antigravity Graph Engine.
Consolidates probability distributions, non-linear kernels, and utilities.
"""

import math
from typing import Union, Tuple, Any
import numpy as np

class ProbValue:
    """
    概率值类 - 表示一个服从正态分布的能量值 (Everything is a wave).
    """
    def __init__(self, mean: float, std_dev_percent: float = 0.1):
        self.mean = float(mean)
        self.std = max(abs(self.mean * std_dev_percent), 0.1)
    
    def prob_greater_than(self, other: Any) -> float:
        if not isinstance(other, ProbValue):
            other = ProbValue(float(other), std_dev_percent=0.1)
        
        diff_mean = self.mean - other.mean
        combined_var = self.std**2 + other.std**2
        
        if combined_var <= 0:
            return 1.0 if diff_mean > 0 else 0.0
        
        z = diff_mean / math.sqrt(combined_var)
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))
    
    def prob_less_than(self, other: Any) -> float:
        return 1.0 - self.prob_greater_than(other)
    
    def __mul__(self, factor: Union[float, 'ProbValue']) -> 'ProbValue':
        if isinstance(factor, ProbValue):
            new_mean = self.mean * factor.mean
            new_var = (self.mean**2 * factor.std**2) + (factor.mean**2 * self.std**2)
            return ProbValue(new_mean, math.sqrt(new_var) / new_mean if new_mean != 0 else 0.1)
        new_mean = self.mean * factor
        return ProbValue(new_mean, self.std / abs(self.mean) if self.mean != 0 else 0.1)
    
    def __rmul__(self, factor: float) -> 'ProbValue':
        return self.__mul__(factor)
    
    def __add__(self, other: Union[float, 'ProbValue']) -> 'ProbValue':
        if isinstance(other, ProbValue):
            new_mean = self.mean + other.mean
            new_std = math.sqrt(self.std**2 + other.std**2)
            return ProbValue(new_mean, new_std / new_mean if new_mean != 0 else 0.1)
        new_mean = self.mean + other
        return ProbValue(new_mean, self.std / new_mean if new_mean != 0 else 0.1)
    
    def __radd__(self, other: float) -> 'ProbValue':
        return self.__add__(other)
    
    def __sub__(self, other: Union[float, 'ProbValue']) -> 'ProbValue':
        if isinstance(other, ProbValue):
            new_mean = self.mean - other.mean
            new_std = math.sqrt(self.std**2 + other.std**2)
            return ProbValue(new_mean, new_std / new_mean if new_mean != 0 else 0.1)
        new_mean = self.mean - other
        return ProbValue(new_mean, self.std / new_mean if new_mean != 0 else 0.1)
    
    def __truediv__(self, divisor: Union[float, 'ProbValue']) -> 'ProbValue':
        if isinstance(divisor, ProbValue):
            if divisor.mean == 0: return self
            new_mean = self.mean / divisor.mean
            new_var = (self.std / divisor.mean)**2 + (self.mean * divisor.std / divisor.mean**2)**2
            return ProbValue(new_mean, math.sqrt(new_var) / new_mean if new_mean != 0 else 0.1)
        if divisor == 0: return self
        return ProbValue(self.mean / divisor, self.std / self.mean if self.mean != 0 else 0.1)

    def transmit(self, damping_factor: float, noise_floor: float = 0.5) -> 'ProbValue':
        """波的传输 (Transmission): 振幅衰减，熵增加"""
        attenuation = math.exp(-damping_factor)
        new_mean = self.mean * attenuation
        new_std = math.sqrt((self.std * attenuation)**2 + noise_floor**2)
        res = ProbValue(new_mean, new_std / new_mean if new_mean != 0 else 0.1)
        res.std = new_std
        return res

    def react(self, damage_dealt: float, recoil_factor: float) -> 'ProbValue':
        """波的反作用 (Reaction): 能量减损，不稳定性剧增"""
        recoil = damage_dealt * recoil_factor
        new_mean = max(0.0, self.mean - recoil)
        new_std = math.sqrt(self.std**2 + (recoil * 0.5)**2)
        res = ProbValue(new_mean, new_std / new_mean if new_mean != 0 else 0.1)
        res.std = new_std
        return res

    def __float__(self) -> float: return self.mean
    def __str__(self) -> str: return f"Prob(μ={self.mean:.2f}, σ={self.std:.2f})"
    def __repr__(self) -> str: return self.__str__()

# Kernels
def expit(x: float) -> float:
    if x > 20: return 1.0
    if x < -20: return 0.0
    return 1.0 / (1.0 + np.exp(-x))

def softplus(x: float) -> float:
    if x > 20: return x
    return np.log1p(np.exp(x))

def gating(x: float, threshold: float = 0.5, sharpness: float = 10.0) -> float:
    return expit(sharpness * (x - threshold))

# Utilities
def saturate(x: float, max_val: float = 2.5, steepness: float = 0.8) -> float:
    return max_val * np.tanh(steepness * x)

def decay(x: float, rate: float = 0.5, floor: float = 0.1) -> float:
    return max(x * (1.0 - rate), floor)

def prob_compare(a: Any, b: Any, threshold: float = 0.85) -> Tuple[bool, float]:
    v_a = a if isinstance(a, ProbValue) else ProbValue(float(a))
    v_b = b if isinstance(b, ProbValue) else ProbValue(float(b))
    p = v_a.prob_greater_than(v_b)
    return p >= threshold, p
