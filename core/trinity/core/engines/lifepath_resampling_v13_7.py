"""
[V13.7 物理化升级] MOD_07 个人生命轨道仪：高频采样修正
=====================================================

核心物理问题：流年脉冲如何平滑化？

物理映射：
- 高频采样：将流年（Annual）的冲击平滑化
- 惯性衰减：引入 MOD_12 的衰减常数 tau
- 动态弥散：使用正弦弥散算法

核心公式：
- 动态弥散：E(t) = E_base * (1 + A * sin(ωt + φ))
- 惯性衰减：W(t) = exp(-t / tau)

整合了 InfluenceBus 的流年注入机制和 MOD_12 的惯性衰减。
"""

import numpy as np
import math
from typing import Dict, Any, Optional, List, Tuple
from core.trinity.core.middleware.influence_bus import InfluenceBus
from core.trinity.core.engines.spacetime_inertia_v13_7 import SpacetimeInertiaEngineV13_7


class LifepathResamplingEngineV13_7:
    """
    [V13.7 物理化升级] 个人生命轨道仪引擎：高频采样修正
    
    核心功能：
    1. 高频采样：将流年（Annual）的冲击平滑化
    2. 惯性衰减：引入 MOD_12 的衰减常数 tau
    3. 动态弥散：使用正弦弥散算法
    """
    
    # 采样频率（月/次）
    SAMPLING_FREQUENCY = 12.0  # 每月采样一次
    
    # 动态弥散参数
    DISPERSION_AMPLITUDE = 0.15  # 弥散振幅
    DISPERSION_FREQUENCY = 1.0  # 弥散频率（1/年）
    
    def __init__(self, tau: float = 3.0):
        """
        初始化生命轨道仪引擎
        
        Args:
            tau: 惯性常数（月），默认 3.0
        """
        self.inertia_engine = SpacetimeInertiaEngineV13_7(tau=tau)
    
    def calculate_dynamic_dispersion(
        self,
        t: float,
        base_energy: float,
        influence_bus: Optional[InfluenceBus] = None
    ) -> float:
        """
        [V13.7] 计算动态弥散（正弦弥散算法）
        
        公式：E(t) = E_base * (1 + A * sin(ωt + φ))
        
        Args:
            t: 时间（年）
            base_energy: 基础能量
            influence_bus: InfluenceBus 实例（用于获取流年相位）
        
        Returns:
            弥散后的能量
        """
        # 从 InfluenceBus 获取流年相位
        phase = 0.0
        frequency = self.DISPERSION_FREQUENCY
        
        if influence_bus:
            for factor in influence_bus.active_factors:
                if factor.name == "AnnualPulse/流年" or "Annual" in factor.name:
                    phase = factor.metadata.get("phase", 0.0)
                    frequency = factor.metadata.get("frequency", self.DISPERSION_FREQUENCY)
                    break
        
        # 动态弥散：E(t) = E_base * (1 + A * sin(ωt + φ))
        dispersion_term = 1.0 + self.DISPERSION_AMPLITUDE * math.sin(frequency * t + phase)
        dispersed_energy = base_energy * dispersion_term
        
        return dispersed_energy
    
    def resample_timeline(
        self,
        base_timeline: List[int],
        base_energy: float,
        influence_bus: Optional[InfluenceBus] = None,
        sampling_rate: float = None
    ) -> Dict[str, Any]:
        """
        [V13.7] 重新采样时间线（高频采样）
        
        将流年（Annual）的冲击平滑化，引入 MOD_12 的衰减常数 tau。
        确保能量变化不是"瞬断"的，而是有物理惯性的过渡。
        
        Args:
            base_timeline: 基础时间线（年份列表）
            base_energy: 基础能量
            influence_bus: InfluenceBus 实例
            sampling_rate: 采样率（月/次），如果为 None 则使用默认值
        
        Returns:
            包含重采样时间线、能量序列、平滑能量的字典
        """
        if sampling_rate is None:
            sampling_rate = self.SAMPLING_FREQUENCY
        
        # 生成高频采样时间线（按月）
        resampled_timeline = []
        resampled_energy = []
        
        for year in base_timeline:
            # 每年采样 12 次（每月一次）
            for month in range(12):
                t_year = year + month / 12.0
                t_months = (year - base_timeline[0]) * 12 + month
                
                # 计算动态弥散
                dispersed_energy = self.calculate_dynamic_dispersion(
                    t=t_year,
                    base_energy=base_energy,
                    influence_bus=influence_bus
                )
                
                resampled_timeline.append(t_months)
                resampled_energy.append(dispersed_energy)
        
        # 应用惯性平滑
        smoothed_energy = self.inertia_engine.apply_inertia_smoothing(
            energy_timeline=resampled_energy,
            time_months=resampled_timeline,
            influence_bus=influence_bus
        )
        
        return {
            "Resampled_Timeline_Months": resampled_timeline,
            "Resampled_Energy": [round(e, 2) for e in resampled_energy],
            "Smoothed_Energy": [round(e, 2) for e in smoothed_energy],
            "Metrics": {
                "Sampling_Rate": sampling_rate,
                "Total_Samples": len(resampled_timeline),
                "Original_Years": len(base_timeline),
                "Energy_Range": [round(min(resampled_energy), 2), round(max(resampled_energy), 2)] if resampled_energy else [0.0, 0.0]
            }
        }
    
    def detect_risk_nodes(
        self,
        energy_timeline: List[float],
        sai_threshold: float = 0.6,
        entropy_threshold: float = 1.5,
        ic_threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        [V13.7] 探测风险节点
        
        触发条件：SAI > 0.6, Entropy > 1.5, 或 IC > 0.6
        
        Args:
            energy_timeline: 能量时间序列
            sai_threshold: SAI 阈值
            entropy_threshold: 熵阈值
            ic_threshold: IC 阈值
        
        Returns:
            风险节点列表
        """
        risk_nodes = []
        
        for i, energy in enumerate(energy_timeline):
            # 简化的风险判定（基于能量异常）
            # 实际应用中，SAI、Entropy、IC 应从其他模块获取
            is_risk = False
            risk_reason = []
            
            # 能量异常检测（简化版）
            if i > 0 and i < len(energy_timeline) - 1:
                energy_change = abs(energy - energy_timeline[i-1])
                if energy_change > sai_threshold:
                    is_risk = True
                    risk_reason.append("High_Energy_Change")
            
            if is_risk:
                risk_nodes.append({
                    "Index": i,
                    "Energy": round(energy, 2),
                    "Risk_Reasons": risk_reason
                })
        
        return risk_nodes
    
    def analyze_lifepath(
        self,
        base_timeline: List[int],
        base_energy: float,
        influence_bus: Optional[InfluenceBus] = None
    ) -> Dict[str, Any]:
        """
        [V13.7 物理化升级] 分析个人生命轨道（高频采样修正）
        
        核心功能：
        1. 高频采样：将流年（Annual）的冲击平滑化
        2. 惯性衰减：引入 MOD_12 的衰减常数 tau
        3. 动态弥散：使用正弦弥散算法
        4. 风险节点探测：检测高风险时间点
        
        Args:
            base_timeline: 基础时间线（年份列表）
            base_energy: 基础能量
            influence_bus: InfluenceBus 实例
        
        Returns:
            包含重采样时间线、能量序列、平滑能量、风险节点的字典
        """
        # 重新采样时间线
        resample_result = self.resample_timeline(
            base_timeline=base_timeline,
            base_energy=base_energy,
            influence_bus=influence_bus
        )
        
        # 探测风险节点
        risk_nodes = self.detect_risk_nodes(
            energy_timeline=resample_result["Resampled_Energy"]
        )
        
        return {
            "Lifepath_Analysis": resample_result,
            "Risk_Nodes": risk_nodes,
            "Metrics": {
                "Total_Risk_Nodes": len(risk_nodes),
                "Sampling_Rate": resample_result["Metrics"]["Sampling_Rate"],
                "Total_Samples": resample_result["Metrics"]["Total_Samples"]
            }
        }

