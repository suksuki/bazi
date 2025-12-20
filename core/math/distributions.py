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
    
    def __lt__(self, other: Union[float, 'ProbValue']) -> bool:
        val = other.mean if isinstance(other, ProbValue) else other
        return self.mean < val

    def __le__(self, other: Union[float, 'ProbValue']) -> bool:
        val = other.mean if isinstance(other, ProbValue) else other
        return self.mean <= val

    def __gt__(self, other: Union[float, 'ProbValue']) -> bool:
        val = other.mean if isinstance(other, ProbValue) else other
        return self.mean > val

    def __ge__(self, other: Union[float, 'ProbValue']) -> bool:
        val = other.mean if isinstance(other, ProbValue) else other
        return self.mean >= val

    def __float__(self) -> float:
        return self.mean
    
    def transmit(self, damping_factor: float, noise_floor: float = 0.5) -> 'ProbValue':
        """
        [V12.2] 波的传输 (Transmission): 振幅衰减，熵增加
        
        Args:
            damping_factor: 阻尼系数 (e^-damping)
            noise_floor: 本底噪音 (高斯白噪声)
        
        物理含义:
            信号穿过介质，能量按指数衰减，但携带的信息熵（不确定度）增加。
            衰减后的方差 = (原方差 * 衰减系数)^2 + 噪音^2
        """
        # 1. 振幅衰减 (非线性)
        attenuation = math.exp(-damping_factor)
        new_mean = self.mean * attenuation
        
        # 2. 方差演化 (熵增)
        # 信号变弱，但必须引入额外的传输噪音（不可逆的热力学过程）
        # new_std = sqrt((old_std * att)^2 + noise^2)
        new_std = math.sqrt((self.std * attenuation)**2 + noise_floor**2)
        
        # 重新计算相对波动率用于初始化
        std_percent = new_std / new_mean if new_mean != 0 else 0.1
        
        # 直接使用 calculated std 初始化，覆盖默认的 std_percent 计算
        new_prob = ProbValue(new_mean, std_percent)
        new_prob.std = new_std  # 强制覆盖，确保精确物理值
        return new_prob

    def react(self, damage_dealt: float, recoil_factor: float) -> 'ProbValue':
        """
        [V12.2] 波的反作用 (Reaction): 能量减损，不稳定性剧增
        
        Args:
            damage_dealt: 造成的伤害量 (Scalar or Mean)
            recoil_factor: 后坐力系数 (beta)
            
        物理含义:
            牛顿第三定律的反作用力。
            攻击造成反噬，导致自身能量减少，且波函数剧烈震荡（方差增加）。
        """
        recoil_energy = damage_dealt * recoil_factor
        
        # 能量减少
        new_mean = self.mean - recoil_energy
        if new_mean < 0: new_mean = 0.0 # 能量不能为负
        
        # 方差剧增: 战斗导致波形崩塌/混乱
        # 假设反作用力带来了巨大的扰动 (Instability)
        added_instability = recoil_energy * 0.5 
        new_std = math.sqrt(self.std**2 + added_instability**2)
        
        std_percent = new_std / new_mean if new_mean != 0 else 0.1
        new_prob = ProbValue(new_mean, std_percent)
        new_prob.std = new_std
        return new_prob

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
