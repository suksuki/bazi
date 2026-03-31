"""
[V13.7 物理化升级] MOD_16 应期预测：概率波坍缩
=================================================

核心物理问题：如何预测未来事件的发生时间？

物理映射：
- 概率波坍缩：量子波函数在特定条件下坍缩为确定性事件
- 非线性累加：多个影响因子的非线性叠加

核心公式：
- 概率波坍缩：P(t) = |ψ(t)|² = A * exp(-(t - t_0)² / (2σ²))
- 非线性累加：E_total = Σ(E_i * w_i * f_nonlinear(E_i))

整合了 InfluenceBus 的大运、流年注入机制。
"""

import numpy as np
import math
from typing import Dict, Any, List, Optional, Tuple
from core.trinity.core.middleware.influence_bus import InfluenceBus


class TemporalPredictionEngineV13_7:
    """
    [V13.7 物理化升级] 应期预测引擎：概率波坍缩模型
    
    核心功能：
    1. 概率波坍缩：量子波函数在特定条件下坍缩为确定性事件
    2. 非线性累加：多个影响因子的非线性叠加
    3. 奇点探测：检测未来高风险/高收益时间点
    """
    
    # 概率波参数
    SIGMA_BASE = 1.0  # 基础标准差（年）
    AMPLITUDE_BASE = 1.0  # 基础振幅
    
    # 非线性累加参数
    NONLINEAR_THRESHOLD = 0.5  # 非线性阈值
    NONLINEAR_EXPONENT = 1.5  # 非线性指数
    
    def __init__(self):
        """初始化应期预测引擎"""
        pass
    
    def calculate_wavefunction_collapse(
        self,
        t: float,
        t_0: float,
        sigma: float = None,
        amplitude: float = None,
        influence_bus: Optional[InfluenceBus] = None
    ) -> float:
        """
        [V13.7] 计算概率波坍缩（高斯波包）
        
        公式：P(t) = |ψ(t)|² = A * exp(-(t - t_0)² / (2σ²))
        
        Args:
            t: 当前时间（年）
            t_0: 中心时间（年）
            sigma: 标准差（年），如果为 None 则使用默认值
            amplitude: 振幅，如果为 None 则使用默认值
            influence_bus: InfluenceBus 实例（用于获取环境修正）
        
        Returns:
            概率密度 P(t)
        """
        if sigma is None:
            sigma = self.SIGMA_BASE
        if amplitude is None:
            amplitude = self.AMPLITUDE_BASE
        
        # 从 InfluenceBus 获取环境修正
        if influence_bus:
            for factor in influence_bus.active_factors:
                if factor.name == "EraBias/时代":
                    # 时代背景可能影响概率波宽度
                    era_bonus = factor.metadata.get("era_bonus", 0.0)
                    sigma = sigma * (1.0 + era_bonus * 0.1)  # 小幅修正
                    break
        
        # 高斯波包：P(t) = A * exp(-(t - t_0)² / (2σ²))
        exponent = -((t - t_0) ** 2) / (2.0 * sigma ** 2)
        probability = amplitude * math.exp(exponent)
        
        return probability
    
    def calculate_nonlinear_accumulation(
        self,
        energy_components: Dict[str, float],
        weights: Optional[Dict[str, float]] = None,
        influence_bus: Optional[InfluenceBus] = None
    ) -> float:
        """
        [V13.7] 计算非线性累加
        
        公式：E_total = Σ(E_i * w_i * f_nonlinear(E_i))
        其中：f_nonlinear(E_i) = 1 + (E_i / threshold)^exponent
        
        Args:
            energy_components: 能量分量字典
            weights: 权重字典（如果为 None，则使用均匀权重）
            influence_bus: InfluenceBus 实例
        
        Returns:
            总能量 E_total
        """
        if not energy_components:
            return 0.0
        
        if weights is None:
            # 均匀权重
            n = len(energy_components)
            weights = {k: 1.0 / n for k in energy_components.keys()}
        
        # 从 InfluenceBus 获取大运修正
        luck_modifier = 1.0
        if influence_bus:
            for factor in influence_bus.active_factors:
                if factor.name == "LuckCycle/大运" or "Luck" in factor.name:
                    luck_damping = factor.metadata.get("damping", 1.0)
                    luck_modifier = luck_damping
                    break
        
        total_energy = 0.0
        
        for component, energy in energy_components.items():
            weight = weights.get(component, 0.0)
            
            # 非线性函数：f_nonlinear(E_i) = 1 + (E_i / threshold)^exponent
            if energy > self.NONLINEAR_THRESHOLD:
                nonlinear_factor = 1.0 + ((energy / self.NONLINEAR_THRESHOLD) ** self.NONLINEAR_EXPONENT)
            else:
                nonlinear_factor = 1.0
            
            # 累加：E_i * w_i * f_nonlinear(E_i)
            total_energy += energy * weight * nonlinear_factor
        
        # 应用大运修正
        total_energy *= luck_modifier
        
        return total_energy
    
    def detect_singularity_points(
        self,
        timeline: List[float],
        energy_timeline: List[float],
        threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        [V13.7] 探测奇点（高风险/高收益时间点）
        
        Args:
            timeline: 时间序列（年）
            energy_timeline: 能量序列
            threshold: 奇点阈值
        
        Returns:
            奇点列表（包含时间、能量、类型）
        """
        singularities = []
        
        for i, (t, energy) in enumerate(zip(timeline, energy_timeline)):
            if energy >= threshold:
                # 判断奇点类型
                if energy >= 0.8:
                    singularity_type = "HIGH_RISK"  # 高风险
                elif energy >= 0.6:
                    singularity_type = "MODERATE_RISK"  # 中等风险
                else:
                    singularity_type = "OPPORTUNITY"  # 机会点
                
                singularities.append({
                    "time": t,
                    "energy": energy,
                    "type": singularity_type,
                    "index": i
                })
        
        return singularities
    
    def predict_timeline(
        self,
        base_energy: float,
        timeline_years: List[int],
        influence_bus: Optional[InfluenceBus] = None,
        singularity_threshold: float = 0.6
    ) -> Dict[str, Any]:
        """
        [V13.7 物理化升级] 预测时间线（概率波坍缩 + 非线性累加）
        
        核心功能：
        1. 概率波坍缩：计算每个时间点的概率密度
        2. 非线性累加：累加多个影响因子的能量
        3. 奇点探测：检测高风险/高收益时间点
        
        Args:
            base_energy: 基础能量
            timeline_years: 时间线（年份列表）
            influence_bus: InfluenceBus 实例
            singularity_threshold: 奇点阈值
        
        Returns:
            包含预测时间线、奇点、概率分布的字典
        """
        # 1. 计算概率波坍缩
        # 假设中心时间点为时间线的中点
        t_0 = (timeline_years[0] + timeline_years[-1]) / 2.0
        
        probability_timeline = []
        energy_timeline = []
        
        for t in timeline_years:
            # 概率波坍缩
            probability = self.calculate_wavefunction_collapse(
                t=t,
                t_0=t_0,
                influence_bus=influence_bus
            )
            probability_timeline.append(probability)
            
            # 非线性累加（基于概率和基础能量）
            energy_components = {
                "base": base_energy,
                "probability": probability
            }
            total_energy = self.calculate_nonlinear_accumulation(
                energy_components=energy_components,
                influence_bus=influence_bus
            )
            energy_timeline.append(total_energy)
        
        # 2. 探测奇点
        singularities = self.detect_singularity_points(
            timeline=timeline_years,
            energy_timeline=energy_timeline,
            threshold=singularity_threshold
        )
        
        return {
            "Timeline": timeline_years,
            "Probability_Timeline": [round(p, 4) for p in probability_timeline],
            "Energy_Timeline": [round(e, 2) for e in energy_timeline],
            "Singularities": singularities,
            "Metrics": {
                "Base_Energy": round(base_energy, 2),
                "Center_Time": round(t_0, 2),
                "Max_Probability": round(max(probability_timeline), 4) if probability_timeline else 0.0,
                "Max_Energy": round(max(energy_timeline), 2) if energy_timeline else 0.0,
                "Singularity_Count": len(singularities)
            }
        }

