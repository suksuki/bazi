"""
[V13.7 物理化升级] MOD_14 多维时空场耦合模型
===========================================

核心物理问题：原生概率波函数（Base Wave）与大运（Background）、流年（Impulse）、地域（GEO Bias）的相干叠加。

物理映射：
- Base Wave: 原局概率波函数
- Background: 大运背景辐射（静态势场）
- Impulse: 流年脉冲（动能冲量）
- GEO Bias: 地域偏置（介质阻尼系数）

核心公式：
- 相干叠加：ψ_total = ψ_base + ψ_background + ψ_impulse + ψ_geo
- 干涉指数：I = |ψ_total|² / |ψ_base|²
- 相位相干：η = |⟨ψ_base|ψ_total⟩|² / (|ψ_base|² * |ψ_total|²)
"""

import numpy as np
import math
from typing import Dict, Any, List, Optional
from core.trinity.core.middleware.influence_bus import InfluenceBus, PhysicsTensor


class SpacetimeInterferenceEngineV13_7:
    """
    [V13.7 物理化升级] 多维时空场耦合引擎：相干叠加模型
    
    核心功能：
    1. 原生概率波函数（Base Wave）提取
    2. 大运背景辐射（Background）叠加
    3. 流年脉冲（Impulse）叠加
    4. 地域偏置（GEO Bias）修正
    5. 相干叠加计算和干涉指数生成
    """
    
    # 基础参数
    BASE_AMPLITUDE = 1.0  # 基础振幅
    BASE_PHASE = 0.0      # 基础相位
    BASE_FREQUENCY = 1.0  # 基础频率
    
    # 权重系数（根据实证校准）
    WEIGHT_BACKGROUND = 0.3  # 大运背景权重
    WEIGHT_IMPULSE = 0.2     # 流年脉冲权重
    WEIGHT_GEO = 0.1         # 地域偏置权重
    
    def __init__(self):
        """初始化多维时空场耦合引擎"""
        pass
    
    def extract_base_wave(
        self,
        waves: Dict[str, Any],
        day_master_element: str
    ) -> PhysicsTensor:
        """
        [V13.7] 提取原生概率波函数（Base Wave）
        
        从原局能量分布中提取日主的概率波函数。
        
        Args:
            waves: 元素能量字典
            day_master_element: 日主元素
        
        Returns:
            Base Wave 的 PhysicsTensor
        """
        # 获取日主能量
        dm_wave = waves.get(day_master_element)
        if dm_wave is None:
            return PhysicsTensor(
                amplitude=self.BASE_AMPLITUDE,
                phase=self.BASE_PHASE,
                frequency=self.BASE_FREQUENCY
            )
        
        # 提取振幅和相位
        amplitude = getattr(dm_wave, 'amplitude', self.BASE_AMPLITUDE)
        phase = getattr(dm_wave, 'phase', self.BASE_PHASE)
        
        # 计算频率（基于能量强度）
        frequency = amplitude / 10.0  # 归一化频率
        
        return PhysicsTensor(
            amplitude=amplitude,
            phase=phase,
            frequency=frequency
        )
    
    def extract_background_field(
        self,
        influence_bus: Optional[InfluenceBus] = None
    ) -> PhysicsTensor:
        """
        [V13.7] 提取大运背景辐射（Background Field）
        
        从 InfluenceBus 中提取大运信息，构建静态势场。
        
        Args:
            influence_bus: InfluenceBus 实例
        
        Returns:
            Background Field 的 PhysicsTensor
        """
        if not influence_bus:
            return PhysicsTensor(
                amplitude=0.0,
                phase=0.0,
                frequency=0.0
            )
        
        # 从 InfluenceBus 提取大运信息
        background_amplitude = 0.0
        background_phase = 0.0
        
        for factor in influence_bus.active_factors:
            if factor.name == "LuckCycle/大运" or "Luck" in factor.name or "LuckCycle" in factor.name:
                # 尝试从 InfluenceBus 的期望向量中提取
                if hasattr(influence_bus, '_active_verdict'):
                    verdict = influence_bus._active_verdict
                    if isinstance(verdict, dict):
                        expectation = verdict.get('expectation')
                        if expectation and hasattr(expectation, 'tensors'):
                            # 计算总振幅（所有元素的期望值）
                            total_amplitude = 0.0
                            for elem, tensor in expectation.tensors.items():
                                if isinstance(tensor, PhysicsTensor):
                                    total_amplitude += tensor.amplitude
                            
                            if total_amplitude > 0:
                                background_amplitude = total_amplitude * self.WEIGHT_BACKGROUND
                                background_phase = math.pi / 4.0  # 45度相位差
                                break
                
                # 使用元数据中的阻尼系数（备用方案）
                damping = factor.metadata.get("damping", 1.0)
                background_amplitude = (1.0 - damping) * self.WEIGHT_BACKGROUND
                background_phase = 0.0
                break
        
        return PhysicsTensor(
            amplitude=background_amplitude,
            phase=background_phase,
            frequency=0.1  # 大运频率低（静态场）
        )
    
    def extract_impulse_wave(
        self,
        influence_bus: Optional[InfluenceBus] = None
    ) -> PhysicsTensor:
        """
        [V13.7] 提取流年脉冲（Impulse Wave）
        
        从 InfluenceBus 中提取流年信息，构建动能冲量。
        
        Args:
            influence_bus: InfluenceBus 实例
        
        Returns:
            Impulse Wave 的 PhysicsTensor
        """
        if not influence_bus:
            return PhysicsTensor(
                amplitude=0.0,
                phase=0.0,
                frequency=0.0
            )
        
        # 从 InfluenceBus 提取流年信息
        impulse_amplitude = 0.0
        impulse_phase = 0.0
        impulse_frequency = 1.0  # 流年频率高（动态脉冲）
        
        for factor in influence_bus.active_factors:
            if factor.name == "AnnualPulse/流年" or "Annual" in factor.name or "AnnualPulse" in factor.name:
                # 尝试从 InfluenceBus 的期望向量中提取
                if hasattr(influence_bus, '_active_verdict'):
                    verdict = influence_bus._active_verdict
                    if isinstance(verdict, dict):
                        expectation = verdict.get('expectation')
                        if expectation and hasattr(expectation, 'tensors'):
                            # 计算总振幅
                            total_amplitude = 0.0
                            for elem, tensor in expectation.tensors.items():
                                if isinstance(tensor, PhysicsTensor):
                                    total_amplitude += tensor.amplitude
                            
                            if total_amplitude > 0:
                                impulse_amplitude = total_amplitude * self.WEIGHT_IMPULSE
                                impulse_phase = math.pi / 2.0  # 90度相位差
                                impulse_frequency = 2.0  # 流年频率高
                                break
                
                # 使用元数据中的冲量（备用方案）
                impulse = factor.metadata.get("impulse", 0.0)
                impulse_amplitude = abs(impulse) * self.WEIGHT_IMPULSE
                impulse_phase = math.pi if impulse < 0 else 0.0
                break
        
        return PhysicsTensor(
            amplitude=impulse_amplitude,
            phase=impulse_phase,
            frequency=impulse_frequency
        )
    
    def extract_geo_bias(
        self,
        influence_bus: Optional[InfluenceBus] = None
    ) -> PhysicsTensor:
        """
        [V13.7] 提取地域偏置（GEO Bias）
        
        从 InfluenceBus 中提取地理信息，构建介质阻尼系数。
        
        Args:
            influence_bus: InfluenceBus 实例
        
        Returns:
            GEO Bias 的 PhysicsTensor
        """
        if not influence_bus:
            return PhysicsTensor(
                amplitude=0.0,
                phase=0.0,
                frequency=0.0
            )
        
        # 从 InfluenceBus 提取地理信息
        geo_amplitude = 0.0
        geo_phase = 0.0
        
        for factor in influence_bus.active_factors:
            if factor.name == "GeoBias/地域":
                geo_factor = factor.metadata.get("geo_factor", 1.0)
                geo_element = factor.metadata.get("geo_element")
                
                # 地理偏置影响振幅（介质阻尼）
                # geo_factor > 1.0 表示增强，< 1.0 表示衰减
                geo_amplitude = (geo_factor - 1.0) * self.WEIGHT_GEO
                # 地理偏置相位通常为0（静态修正）
                geo_phase = 0.0
                break
        
        return PhysicsTensor(
            amplitude=geo_amplitude,
            phase=geo_phase,
            frequency=0.0  # 地理偏置频率为0（静态）
        )
    
    def calculate_coherent_superposition(
        self,
        base_wave: PhysicsTensor,
        background: PhysicsTensor,
        impulse: PhysicsTensor,
        geo_bias: PhysicsTensor
    ) -> PhysicsTensor:
        """
        [V13.7] 计算相干叠加
        
        公式：ψ_total = ψ_base + ψ_background + ψ_impulse + ψ_geo
        
        使用复数表示：A * e^(i*φ) = A * (cos(φ) + i*sin(φ))
        
        Args:
            base_wave: 原生概率波函数
            background: 大运背景辐射
            impulse: 流年脉冲
            geo_bias: 地域偏置
        
        Returns:
            总概率波函数的 PhysicsTensor
        """
        # 将各个分量转换为复数
        def tensor_to_complex(tensor: PhysicsTensor) -> complex:
            """将 PhysicsTensor 转换为复数"""
            return tensor.amplitude * (math.cos(tensor.phase) + 1j * math.sin(tensor.phase))
        
        # 计算总波函数（复数叠加）
        base_complex = tensor_to_complex(base_wave)
        background_complex = tensor_to_complex(background)
        impulse_complex = tensor_to_complex(impulse)
        geo_complex = tensor_to_complex(geo_bias)
        
        total_complex = base_complex + background_complex + impulse_complex + geo_complex
        
        # 提取总振幅和相位
        total_amplitude = abs(total_complex)
        total_phase = math.atan2(total_complex.imag, total_complex.real)
        
        # 计算总频率（加权平均）
        total_frequency = (
            base_wave.frequency * base_wave.amplitude +
            background.frequency * background.amplitude +
            impulse.frequency * impulse.amplitude +
            geo_bias.frequency * geo_bias.amplitude
        ) / max(total_amplitude, 0.1)
        
        return PhysicsTensor(
            amplitude=total_amplitude,
            phase=total_phase,
            frequency=total_frequency
        )
    
    def calculate_interference_index(
        self,
        base_wave: PhysicsTensor,
        total_wave: PhysicsTensor
    ) -> float:
        """
        [V13.7] 计算干涉指数
        
        公式：I = |ψ_total|² / |ψ_base|²
        
        Args:
            base_wave: 原生概率波函数
            total_wave: 总概率波函数
        
        Returns:
            干涉指数 I
        """
        base_intensity = base_wave.amplitude ** 2
        total_intensity = total_wave.amplitude ** 2
        
        if base_intensity < 0.01:
            return 1.0  # 避免除零
        
        interference_index = total_intensity / base_intensity
        return interference_index
    
    def calculate_phase_coherence(
        self,
        base_wave: PhysicsTensor,
        total_wave: PhysicsTensor
    ) -> float:
        """
        [V13.7] 计算相位相干度
        
        公式：η = |⟨ψ_base|ψ_total⟩|² / (|ψ_base|² * |ψ_total|²)
        
        简化：η = cos²(Δφ)，其中 Δφ 是相位差
        
        Args:
            base_wave: 原生概率波函数
            total_wave: 总概率波函数
        
        Returns:
            相位相干度 η (0-1)
        """
        delta_phi = abs(total_wave.phase - base_wave.phase)
        phase_coherence = math.cos(delta_phi / 2.0) ** 2
        return max(0.0, min(1.0, phase_coherence))
    
    def calculate_geo_coupling_efficiency(
        self,
        geo_bias: PhysicsTensor,
        total_wave: PhysicsTensor
    ) -> float:
        """
        [V13.7] 计算地理耦合效率
        
        公式：K_geo = 1 + ε_geo * |A_geo| / |A_total|
        
        Args:
            geo_bias: 地域偏置
            total_wave: 总概率波函数
        
        Returns:
            地理耦合效率 K_geo
        """
        if total_wave.amplitude < 0.01:
            return 1.0
        
        geo_ratio = abs(geo_bias.amplitude) / total_wave.amplitude
        epsilon_geo = 0.1  # 地理耦合系数
        
        coupling_efficiency = 1.0 + epsilon_geo * geo_ratio
        return coupling_efficiency
    
    def analyze_spacetime_interference(
        self,
        waves: Dict[str, Any],
        day_master_element: str,
        influence_bus: Optional[InfluenceBus] = None
    ) -> Dict[str, Any]:
        """
        [V13.7 物理化升级] 分析多维时空场耦合
        
        核心功能：
        1. 提取原生概率波函数（Base Wave）
        2. 提取大运背景辐射（Background）
        3. 提取流年脉冲（Impulse）
        4. 提取地域偏置（GEO Bias）
        5. 计算相干叠加和干涉指数
        
        Args:
            waves: 元素能量字典
            day_master_element: 日主元素
            influence_bus: InfluenceBus 实例
        
        Returns:
            包含干涉指数、相位相干度、地理耦合效率的字典
        """
        # 1. 提取各个分量
        base_wave = self.extract_base_wave(waves, day_master_element)
        background = self.extract_background_field(influence_bus)
        impulse = self.extract_impulse_wave(influence_bus)
        geo_bias = self.extract_geo_bias(influence_bus)
        
        # 2. 计算相干叠加
        total_wave = self.calculate_coherent_superposition(
            base_wave, background, impulse, geo_bias
        )
        
        # 3. 计算干涉指数
        interference_index = self.calculate_interference_index(base_wave, total_wave)
        
        # 4. 计算相位相干度
        phase_coherence = self.calculate_phase_coherence(base_wave, total_wave)
        
        # 5. 计算地理耦合效率
        geo_coupling_efficiency = self.calculate_geo_coupling_efficiency(geo_bias, total_wave)
        
        return {
            "spacetime_interference_index": round(interference_index, 4),
            "geo_coupling_efficiency": round(geo_coupling_efficiency, 4),
            "phase_coherence": round(phase_coherence, 4),
            "base_wave": {
                "amplitude": round(base_wave.amplitude, 4),
                "phase": round(base_wave.phase, 4),
                "frequency": round(base_wave.frequency, 4)
            },
            "total_wave": {
                "amplitude": round(total_wave.amplitude, 4),
                "phase": round(total_wave.phase, 4),
                "frequency": round(total_wave.frequency, 4)
            },
            "components": {
                "background": {
                    "amplitude": round(background.amplitude, 4),
                    "phase": round(background.phase, 4)
                },
                "impulse": {
                    "amplitude": round(impulse.amplitude, 4),
                    "phase": round(impulse.phase, 4)
                },
                "geo_bias": {
                    "amplitude": round(geo_bias.amplitude, 4),
                    "phase": round(geo_bias.phase, 4)
                }
            }
        }

