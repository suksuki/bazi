"""
[V13.7 物理化升级] MOD_12 时空场惯性：衰减常数应用
=================================================

核心物理问题：流年切换如何具有物理惯性？

物理映射：
- 指数衰减：W_prev = exp(-t/tau)
- 惯性常数：tau = 3.0 个月（默认值）
- 平滑过渡：确保能量变化不是"瞬断"的，而是有物理惯性的过渡

核心公式：
- 衰减权重：W(t) = exp(-t / tau)
- 其中：t 为时间（月），tau 为惯性常数

整合了 InfluenceBus 的大运、流年注入机制。
"""

import numpy as np
import math
from typing import Dict, Any, Optional, List
from core.trinity.core.middleware.influence_bus import InfluenceBus


class SpacetimeInertiaEngineV13_7:
    """
    [V13.7 物理化升级] 时空场惯性引擎：衰减常数应用
    
    核心功能：
    1. 指数衰减：W_prev = exp(-t/tau)
    2. 惯性常数：tau = 3.0 个月（默认值）
    3. 平滑过渡：确保能量变化不是"瞬断"的，而是有物理惯性的过渡
    """
    
    # 惯性常数（默认值：3.0 个月）
    TAU_DEFAULT = 3.0  # 月
    
    def __init__(self, tau: float = None):
        """
        初始化时空场惯性引擎
        
        Args:
            tau: 惯性常数（月），如果为 None 则使用默认值
        """
        self.tau = tau if tau is not None else self.TAU_DEFAULT
    
    def calculate_inertia_weights(
        self,
        time_months: List[float],
        previous_energy: float = 1.0,
        influence_bus: Optional[InfluenceBus] = None
    ) -> List[float]:
        """
        [V13.7] 计算惯性权重（指数衰减）
        
        公式：W(t) = exp(-t / tau)
        
        Args:
            time_months: 时间序列（月）
            previous_energy: 前一时刻的能量
            influence_bus: InfluenceBus 实例（用于获取大运修正）
        
        Returns:
            惯性权重列表
        """
        # 从 InfluenceBus 获取大运修正（可能影响惯性常数）
        tau_effective = self.tau
        if influence_bus:
            for factor in influence_bus.active_factors:
                if factor.name == "LuckCycle/大运" or "Luck" in factor.name:
                    # 大运可能影响惯性常数
                    luck_damping = factor.metadata.get("damping", 1.0)
                    # 好运（damping < 1.0）降低惯性（更快响应）
                    # 坏运（damping > 1.0）增加惯性（更慢响应）
                    tau_effective = self.tau * luck_damping
                    break
        
        # 计算惯性权重：W(t) = exp(-t / tau)
        inertia_weights = []
        for t in time_months:
            weight = math.exp(-t / tau_effective)
            inertia_weights.append(weight)
        
        return inertia_weights
    
    def apply_inertia_smoothing(
        self,
        energy_timeline: List[float],
        time_months: List[float],
        influence_bus: Optional[InfluenceBus] = None
    ) -> List[float]:
        """
        [V13.7] 应用惯性平滑（流年切换平滑化）
        
        将流年（Annual）的冲击平滑化，引入衰减常数 tau。
        确保能量变化不是"瞬断"的，而是有物理惯性的过渡。
        
        Args:
            energy_timeline: 能量时间序列
            time_months: 时间序列（月）
            influence_bus: InfluenceBus 实例
        
        Returns:
            平滑后的能量时间序列
        """
        if len(energy_timeline) != len(time_months):
            return energy_timeline
        
        # 计算惯性权重
        inertia_weights = self.calculate_inertia_weights(
            time_months=time_months,
            influence_bus=influence_bus
        )
        
        # 应用惯性平滑
        smoothed_energy = []
        previous_energy = energy_timeline[0] if energy_timeline else 0.0
        
        for i, (current_energy, weight) in enumerate(zip(energy_timeline, inertia_weights)):
            # 平滑公式：E_smooth = E_prev * weight + E_current * (1 - weight)
            smoothed = previous_energy * weight + current_energy * (1.0 - weight)
            smoothed_energy.append(smoothed)
            previous_energy = smoothed
        
        return smoothed_energy
    
    def calculate_viscosity_index(
        self,
        energy_timeline: List[float],
        time_months: List[float],
        influence_bus: Optional[InfluenceBus] = None
    ) -> float:
        """
        [V13.7] 计算粘滞指数（场混合状态）
        
        公式：Viscosity_Index = 1 - (min_energy / max_energy)
        
        Args:
            energy_timeline: 能量时间序列
            time_months: 时间序列（月）
            influence_bus: InfluenceBus 实例
        
        Returns:
            粘滞指数（0.0=纯态, 1.0=最大混合）
        """
        if not energy_timeline:
            return 0.0
        
        min_energy = min(energy_timeline)
        max_energy = max(energy_timeline)
        
        if max_energy < 0.1:
            return 0.0
        
        # 粘滞指数：Viscosity_Index = 1 - (min_energy / max_energy)
        viscosity_index = 1.0 - (min_energy / max_energy)
        
        return viscosity_index
    
    def analyze_spacetime_inertia(
        self,
        energy_timeline: List[float],
        time_months: List[float],
        influence_bus: Optional[InfluenceBus] = None
    ) -> Dict[str, Any]:
        """
        [V13.7 物理化升级] 分析时空场惯性
        
        核心功能：
        1. 指数衰减：W_prev = exp(-t/tau)
        2. 惯性常数：tau = 3.0 个月（默认值）
        3. 平滑过渡：确保能量变化不是"瞬断"的，而是有物理惯性的过渡
        
        Args:
            energy_timeline: 能量时间序列
            time_months: 时间序列（月）
            influence_bus: InfluenceBus 实例
        
        Returns:
            包含惯性权重、平滑能量、粘滞指数的字典
        """
        # 计算惯性权重
        inertia_weights = self.calculate_inertia_weights(
            time_months=time_months,
            influence_bus=influence_bus
        )
        
        # 应用惯性平滑
        smoothed_energy = self.apply_inertia_smoothing(
            energy_timeline=energy_timeline,
            time_months=time_months,
            influence_bus=influence_bus
        )
        
        # 计算粘滞指数
        viscosity_index = self.calculate_viscosity_index(
            energy_timeline=energy_timeline,
            time_months=time_months,
            influence_bus=influence_bus
        )
        
        return {
            "Inertia_Weights": [round(w, 4) for w in inertia_weights],
            "Smoothed_Energy": [round(e, 2) for e in smoothed_energy],
            "Viscosity_Index": round(viscosity_index, 4),
            "Metrics": {
                "Tau": round(self.tau, 2),
                "Original_Energy_Range": [round(min(energy_timeline), 2), round(max(energy_timeline), 2)] if energy_timeline else [0.0, 0.0],
                "Smoothed_Energy_Range": [round(min(smoothed_energy), 2), round(max(smoothed_energy), 2)] if smoothed_energy else [0.0, 0.0]
            }
        }

