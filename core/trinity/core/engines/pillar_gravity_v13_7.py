"""
[V13.7 物理化升级] MOD_11 宫位引力：动态权重
=============================================

核心物理问题：宫位权重如何随时间变化？

物理映射：
- 时变引力：宫位权重随时间（节气深度）动态变化
- 月令支配：月令权重最高，其他宫位权重相对较低

核心公式：
- 动态权重：W_month(t) = 0.40 + 0.15 * sin(π * t)
- 其他宫位：W_other(t) = W_base * (1 - α * W_month(t))

整合了 InfluenceBus 的时代背景修正。
"""

import numpy as np
import math
from typing import Dict, Any, Optional, List
from core.trinity.core.middleware.influence_bus import InfluenceBus


class PillarGravityEngineV13_7:
    """
    [V13.7 物理化升级] 宫位引力引擎：动态权重模型
    
    核心功能：
    1. 时变引力：宫位权重随时间（节气深度）动态变化
    2. 月令支配：月令权重最高，其他宫位权重相对较低
    3. 非线性偏移：模拟非线性能量偏移
    """
    
    # 基础权重（静态）
    BASE_WEIGHTS = {
        "year": 0.7,
        "month": 1.42,  # 最高（月令）
        "day": 1.35,
        "hour": 0.77
    }
    
    # 动态权重参数
    MONTH_BASE = 0.40  # 月令基础权重
    MONTH_AMPLITUDE = 0.15  # 月令振幅
    ALPHA_COUPLING = 0.3  # 耦合系数（其他宫位受月令影响）
    
    def __init__(self):
        """初始化宫位引力引擎"""
        pass
    
    def calculate_dynamic_weights(
        self,
        t: float,
        influence_bus: Optional[InfluenceBus] = None
    ) -> Dict[str, float]:
        """
        [V13.7] 计算动态权重（时变引力）
        
        公式：
        - 月令：W_month(t) = 0.40 + 0.15 * sin(π * t)
        - 其他：W_other(t) = W_base * (1 - α * W_month(t))
        
        Args:
            t: 时间参数（0-1，表示节气深度或归一化时间）
            influence_bus: InfluenceBus 实例（用于获取时代背景修正）
        
        Returns:
            动态权重字典
        """
        # 从 InfluenceBus 获取时代背景修正
        era_modifier = 1.0
        if influence_bus:
            for factor in influence_bus.active_factors:
                if factor.name == "EraBias/时代":
                    era_bonus = factor.metadata.get("era_bonus", 0.0)
                    era_modifier = 1.0 + era_bonus * 0.05  # 小幅修正
                    break
        
        # 计算月令动态权重：W_month(t) = 0.40 + 0.15 * sin(π * t)
        month_weight = self.MONTH_BASE + self.MONTH_AMPLITUDE * math.sin(math.pi * t)
        month_weight *= era_modifier  # 应用时代修正
        
        # 计算其他宫位权重：W_other(t) = W_base * (1 - α * W_month(t))
        # 归一化：确保总权重保持合理范围
        dynamic_weights = {}
        
        for pillar, base_weight in self.BASE_WEIGHTS.items():
            if pillar == "month":
                # 月令使用动态权重
                dynamic_weights[pillar] = month_weight
            else:
                # 其他宫位受月令影响
                # W_other(t) = W_base * (1 - α * (W_month(t) / W_month_base))
                month_ratio = month_weight / self.MONTH_BASE if self.MONTH_BASE > 0 else 1.0
                other_weight = base_weight * (1.0 - self.ALPHA_COUPLING * (month_ratio - 1.0))
                dynamic_weights[pillar] = max(0.1, other_weight)  # 确保最小值
        
        return dynamic_weights
    
    def calculate_energy_distribution(
        self,
        pillar_energies: Dict[str, float],
        t: float = 0.5,
        influence_bus: Optional[InfluenceBus] = None
    ) -> Dict[str, Any]:
        """
        [V13.7] 计算能量分布（基于动态权重）
        
        Args:
            pillar_energies: 宫位能量字典
            t: 时间参数（0-1）
            influence_bus: InfluenceBus 实例
        
        Returns:
            包含加权能量分布和动态权重的字典
        """
        # 计算动态权重
        dynamic_weights = self.calculate_dynamic_weights(t=t, influence_bus=influence_bus)
        
        # 计算加权能量
        weighted_energies = {}
        total_weighted_energy = 0.0
        
        for pillar, energy in pillar_energies.items():
            weight = dynamic_weights.get(pillar, 1.0)
            weighted_energy = energy * weight
            weighted_energies[pillar] = weighted_energy
            total_weighted_energy += weighted_energy
        
        # 计算能量占比
        energy_ratios = {}
        if total_weighted_energy > 0:
            for pillar, weighted_energy in weighted_energies.items():
                energy_ratios[pillar] = weighted_energy / total_weighted_energy
        else:
            for pillar in pillar_energies.keys():
                energy_ratios[pillar] = 0.0
        
        return {
            "Dynamic_Weights": {k: round(v, 4) for k, v in dynamic_weights.items()},
            "Weighted_Energies": {k: round(v, 2) for k, v in weighted_energies.items()},
            "Energy_Ratios": {k: round(v, 4) for k, v in energy_ratios.items()},
            "Total_Weighted_Energy": round(total_weighted_energy, 2),
            "Metrics": {
                "Month_Dominance": round(energy_ratios.get("month", 0.0), 4),
                "Time_Parameter": round(t, 4)
            }
        }
    
    def analyze_pillar_gravity(
        self,
        pillar_energies: Dict[str, float],
        t: float = 0.5,
        influence_bus: Optional[InfluenceBus] = None
    ) -> Dict[str, Any]:
        """
        [V13.7 物理化升级] 分析宫位引力（动态权重模型）
        
        核心功能：
        1. 时变引力：宫位权重随时间（节气深度）动态变化
        2. 月令支配：月令权重最高，其他宫位权重相对较低
        3. 非线性偏移：模拟非线性能量偏移
        
        Args:
            pillar_energies: 宫位能量字典
            t: 时间参数（0-1，表示节气深度）
            influence_bus: InfluenceBus 实例
        
        Returns:
            包含动态权重、能量分布、月令支配度的字典
        """
        # 计算能量分布
        distribution = self.calculate_energy_distribution(
            pillar_energies=pillar_energies,
            t=t,
            influence_bus=influence_bus
        )
        
        return {
            "Pillar_Gravity_Analysis": distribution,
            "Month_Dominance": distribution["Metrics"]["Month_Dominance"],
            "Time_Parameter": t
        }

