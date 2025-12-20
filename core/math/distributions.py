"""
[V13.0] 概率分布数学库 (Probabilistic Distributions)
===================================================

核心哲学：一切皆概率。
提供 ProbValue 类，用于处理带有不确定度（标准差）的能量值。
"""

import math
from typing import Union, Tuple
import numpy as np

class ProbValue:
    """
    概率值类 - 表示一个服从正态分布的能量值
    
    属性:
        mean: 均值 (μ)
        std: 标准差 (σ)
    """
    
    def __init__(self, mean: float, std_dev_percent: float = 0.1):
        """
        初始化概率值
        
        Args:
            mean: 均值 (μ)
            std_dev_percent: 标准差占均值的百分比（相对波动率）
        """
        self.mean = float(mean)
        # 标准差通常与均值成正比，但至少有一个最小值
        self.std = max(abs(self.mean * std_dev_percent), 0.1)  # 至少 0.1 的不确定度
    
    def prob_greater_than(self, other: 'ProbValue') -> float:
        """计算 P(Self > Other) 的概率（胜率）"""
        if not isinstance(other, ProbValue):
            other = ProbValue(other, std_dev_percent=0.1)
        
        diff_mean = self.mean - other.mean
        combined_var = self.std**2 + other.std**2
        
        if combined_var <= 0:
            return 1.0 if diff_mean > 0 else 0.0
        
        z = diff_mean / math.sqrt(combined_var)
        prob = 0.5 * (1 + math.erf(z / math.sqrt(2)))
        return prob
    
    def prob_less_than(self, other: 'ProbValue') -> float:
        """计算 P(Self < Other) 的概率"""
        if not isinstance(other, ProbValue):
            other = ProbValue(other, std_dev_percent=0.1)
        return 1.0 - self.prob_greater_than(other)
    
    def __mul__(self, factor: Union[float, 'ProbValue']) -> 'ProbValue':
        """乘法运算：能量乘以系数"""
        if isinstance(factor, ProbValue):
            new_mean = self.mean * factor.mean
            new_var = (self.mean**2 * factor.std**2) + (factor.mean**2 * self.std**2)
            new_std = math.sqrt(new_var)
            std_dev_percent = new_std / new_mean if new_mean != 0 else 0.1
            return ProbValue(new_mean, std_dev_percent)
        else:
            new_mean = self.mean * factor
            std_dev_percent = self.std / abs(self.mean) if self.mean != 0 else 0.1
            return ProbValue(new_mean, std_dev_percent)
    
    def __rmul__(self, factor: float) -> 'ProbValue':
        return self.__mul__(factor)
    
    def __add__(self, other: Union[float, 'ProbValue']) -> 'ProbValue':
        """加法运算"""
        if isinstance(other, ProbValue):
            new_mean = self.mean + other.mean
            new_var = self.std**2 + other.std**2
            new_std = math.sqrt(new_var)
            std_dev_percent = new_std / new_mean if new_mean != 0 else 0.1
            return ProbValue(new_mean, std_dev_percent)
        else:
            new_mean = self.mean + other
            std_dev_percent = self.std / new_mean if new_mean != 0 else 0.1
            return ProbValue(new_mean, std_dev_percent)
    
    def __radd__(self, other: float) -> 'ProbValue':
        return self.__add__(other)
    
    def __sub__(self, other: Union[float, 'ProbValue']) -> 'ProbValue':
        """减法运算：不仅均值减少，不确定性增加（熵增）"""
        if isinstance(other, ProbValue):
            new_mean = self.mean - other.mean
            new_var = self.std**2 + other.std**2
            new_std = math.sqrt(new_var)
            std_dev_percent = new_std / new_mean if new_mean != 0 else 0.1
            return ProbValue(new_mean, std_dev_percent)
        else:
            new_mean = self.mean - other
            std_dev_percent = self.std / new_mean if new_mean != 0 else 0.1
            return ProbValue(new_mean, std_dev_percent)
    
    def __truediv__(self, divisor: Union[float, 'ProbValue']) -> 'ProbValue':
        """除法运算"""
        if isinstance(divisor, ProbValue):
            new_mean = self.mean / divisor.mean if divisor.mean != 0 else self.mean
            new_var = (self.std / divisor.mean)**2 + (self.mean * divisor.std / divisor.mean**2)**2
            new_std = math.sqrt(new_var)
            std_dev_percent = new_std / new_mean if new_mean != 0 else 0.1
            return ProbValue(new_mean, std_dev_percent)
        else:
            new_mean = self.mean / divisor if divisor != 0 else self.mean
            std_dev_percent = self.std / self.mean if self.mean != 0 else 0.1
            return ProbValue(new_mean, std_dev_percent)
    
    def __float__(self) -> float:
        return self.mean
    
    def __str__(self) -> str:
        return f"ProbValue(μ={self.mean:.2f}, σ={self.std:.2f})"
    
    def __repr__(self) -> str:
        return self.__str__()

def prob_compare(val_a: Union[ProbValue, float], val_b: Union[ProbValue, float], 
                 threshold: float = 0.85) -> Tuple[bool, float]:
    """比较两个概率值"""
    if not isinstance(val_a, ProbValue):
        val_a = ProbValue(val_a, std_dev_percent=0.1)
    if not isinstance(val_b, ProbValue):
        val_b = ProbValue(val_b, std_dev_percent=0.1)
    
    prob = val_a.prob_greater_than(val_b)
    passed = prob >= threshold
    return (passed, prob)
