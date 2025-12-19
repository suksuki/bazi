"""
V13.0 概率波函数数学库 (Probabilistic Wave Function Math Library)
================================================================

核心哲学：一切皆概率
- 不再使用确定性数值（Scalar）
- 使用概率分布（Distribution）
- 每个能量值都有均值(μ)和标准差(σ)

这是从"算术"到"统计学"的跨越。
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
    
    物理意义:
        - 均值代表能量的期望值
        - 标准差代表能量的不确定度/波动范围
        - 月令：σ 极小（权威，极稳）
        - 日支：σ 小（坐下，稳）
        - 时/年支：σ 大（远方，波动大）
        - 被克：σ 极大（受损，极其不稳定）
    """
    
    def __init__(self, mean: float, std_dev_percent: float = 0.1):
        """
        初始化概率值
        
        Args:
            mean: 均值 (μ)
            std_dev_percent: 标准差占均值的百分比（相对波动率）
                            例如 0.1 表示标准差 = 均值的 10%
        """
        self.mean = float(mean)
        # 标准差通常与均值成正比，但至少有一个最小值
        self.std = max(abs(self.mean * std_dev_percent), 0.1)  # 至少 0.1 的不确定度
    
    def prob_greater_than(self, other: 'ProbValue') -> float:
        """
        计算 P(Self > Other) 的概率（胜率）
        
        使用 Z-score 和误差函数计算两个正态分布的差值分布
        
        Args:
            other: 另一个概率值
            
        Returns:
            P(Self > Other) 的概率，范围 [0, 1]
        """
        if not isinstance(other, ProbValue):
            # 如果 other 是普通数值，转换为 ProbValue
            other = ProbValue(other, std_dev_percent=0.1)
        
        # 计算差值分布的均值和方差
        diff_mean = self.mean - other.mean
        combined_var = self.std**2 + other.std**2
        
        if combined_var <= 0:
            # 如果方差为 0，直接比较均值
            return 1.0 if diff_mean > 0 else 0.0
        
        # 计算 Z-score
        z = diff_mean / math.sqrt(combined_var)
        
        # 使用误差函数近似累积分布函数 (CDF)
        # P(X > 0) = 0.5 * (1 + erf(z / sqrt(2)))
        prob = 0.5 * (1 + math.erf(z / math.sqrt(2)))
        
        return prob
    
    def prob_less_than(self, other: 'ProbValue') -> float:
        """
        计算 P(Self < Other) 的概率
        
        Args:
            other: 另一个概率值
            
        Returns:
            P(Self < Other) 的概率
        """
        if not isinstance(other, ProbValue):
            other = ProbValue(other, std_dev_percent=0.1)
        
        return 1.0 - self.prob_greater_than(other)
    
    def __mul__(self, factor: Union[float, 'ProbValue']) -> 'ProbValue':
        """
        乘法运算：能量乘以系数
        
        乘法会放大均值，也会放大波动（保持相对波动率不变）
        
        Args:
            factor: 乘数（可以是数值或 ProbValue）
            
        Returns:
            新的 ProbValue
        """
        if isinstance(factor, ProbValue):
            # 两个概率值相乘（更复杂的情况）
            new_mean = self.mean * factor.mean
            # 方差传播：Var(X*Y) ≈ (E[X]^2 * Var[Y]) + (E[Y]^2 * Var[X])
            new_var = (self.mean**2 * factor.std**2) + (factor.mean**2 * self.std**2)
            new_std = math.sqrt(new_var)
            # 计算相对波动率
            std_dev_percent = new_std / new_mean if new_mean != 0 else 0.1
            return ProbValue(new_mean, std_dev_percent)
        else:
            # 乘以常数
            new_mean = self.mean * factor
            # 保持相对波动率不变
            std_dev_percent = self.std / self.mean if self.mean != 0 else 0.1
            return ProbValue(new_mean, std_dev_percent)
    
    def __rmul__(self, factor: float) -> 'ProbValue':
        """右乘法（支持 factor * prob_value）"""
        return self.__mul__(factor)
    
    def __add__(self, other: Union[float, 'ProbValue']) -> 'ProbValue':
        """
        加法运算：两个能量相加
        
        Args:
            other: 加数（可以是数值或 ProbValue）
            
        Returns:
            新的 ProbValue
        """
        if isinstance(other, ProbValue):
            # 两个概率值相加
            new_mean = self.mean + other.mean
            # 方差相加：Var(X+Y) = Var(X) + Var(Y)
            new_var = self.std**2 + other.std**2
            new_std = math.sqrt(new_var)
            # 计算相对波动率
            std_dev_percent = new_std / new_mean if new_mean != 0 else 0.1
            return ProbValue(new_mean, std_dev_percent)
        else:
            # 加上常数（只改变均值，不确定度不变）
            new_mean = self.mean + other
            std_dev_percent = self.std / self.mean if self.mean != 0 else 0.1
            return ProbValue(new_mean, std_dev_percent)
    
    def __radd__(self, other: float) -> 'ProbValue':
        """右加法（支持 other + prob_value）"""
        return self.__add__(other)
    
    def __sub__(self, other: Union[float, 'ProbValue']) -> 'ProbValue':
        """
        减法运算（能量扣除）
        
        [V13.6] 遵循高斯误差传播定律：
        - 均值相减：μ_new = μ_self - μ_other
        - 方差相加：σ²_new = σ²_self + σ²_other（因为不确定性永远增加）
        
        物理含义：
        - 当能量被扣除时（如被克、被冲），不仅能量减少，不确定性也增加
        - 这是"熵增"的体现：系统状态变得更加不稳定
        
        Args:
            other: 减数（可以是数值或 ProbValue）
            
        Returns:
            新的 ProbValue
        """
        if isinstance(other, ProbValue):
            new_mean = self.mean - other.mean
            # [V13.6] 方差相加：Var(X-Y) = Var(X) + Var(Y)（注意这里是加号！）
            # 因为不确定性永远增加，即使是在减法运算中
            new_var = self.std**2 + other.std**2
            new_std = math.sqrt(new_var)
            std_dev_percent = new_std / new_mean if new_mean != 0 else 0.1
            return ProbValue(new_mean, std_dev_percent)
        else:
            # 减去常数：均值减少，但标准差保持不变（相对波动率增加）
            new_mean = self.mean - other
            std_dev_percent = self.std / new_mean if new_mean != 0 else 0.1
            return ProbValue(new_mean, std_dev_percent)
    
    def __truediv__(self, divisor: Union[float, 'ProbValue']) -> 'ProbValue':
        """
        除法运算
        
        Args:
            divisor: 除数（可以是数值或 ProbValue）
            
        Returns:
            新的 ProbValue
        """
        if isinstance(divisor, ProbValue):
            # 两个概率值相除
            new_mean = self.mean / divisor.mean if divisor.mean != 0 else self.mean
            # 使用误差传播公式
            new_var = (self.std / divisor.mean)**2 + (self.mean * divisor.std / divisor.mean**2)**2
            new_std = math.sqrt(new_var)
            std_dev_percent = new_std / new_mean if new_mean != 0 else 0.1
            return ProbValue(new_mean, std_dev_percent)
        else:
            new_mean = self.mean / divisor if divisor != 0 else self.mean
            std_dev_percent = self.std / self.mean if self.mean != 0 else 0.1
            return ProbValue(new_mean, std_dev_percent)
    
    def __float__(self) -> float:
        """转换为浮点数（返回均值）"""
        return self.mean
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"ProbValue(μ={self.mean:.2f}, σ={self.std:.2f}, σ%={self.std/self.mean*100:.1f}%)"
    
    def __repr__(self) -> str:
        """详细表示"""
        return self.__str__()
    
    def get_confidence_interval(self, confidence: float = 0.95) -> Tuple[float, float]:
        """
        获取置信区间
        
        Args:
            confidence: 置信水平（默认 0.95，即 95% 置信区间）
            
        Returns:
            (下限, 上限)
        """
        # 使用标准正态分布的 z-score
        z_score = {
            0.90: 1.645,
            0.95: 1.96,
            0.99: 2.576
        }.get(confidence, 1.96)
        
        lower = self.mean - z_score * self.std
        upper = self.mean + z_score * self.std
        
        return (lower, upper)
    
    def sample(self, n: int = 1) -> np.ndarray:
        """
        从分布中采样
        
        Args:
            n: 采样数量
            
        Returns:
            采样值数组
        """
        return np.random.normal(self.mean, self.std, n)


def prob_compare(val_a: Union[ProbValue, float], val_b: Union[ProbValue, float], 
                 threshold: float = 0.85) -> Tuple[bool, float]:
    """
    比较两个概率值，判断 A > B 的概率是否超过阈值
    
    Args:
        val_a: 第一个值（可以是 ProbValue 或 float）
        val_b: 第二个值（可以是 ProbValue 或 float）
        threshold: 概率阈值（默认 0.85，即 85% 置信度）
        
    Returns:
        (是否通过, 实际概率)
    """
    if not isinstance(val_a, ProbValue):
        val_a = ProbValue(val_a, std_dev_percent=0.1)
    if not isinstance(val_b, ProbValue):
        val_b = ProbValue(val_b, std_dev_percent=0.1)
    
    prob = val_a.prob_greater_than(val_b)
    passed = prob >= threshold
    
    return (passed, prob)

