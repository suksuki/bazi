"""
[V13.7 物理化升级] MOD_05 财富流体：纳维-斯托克斯方程重构
===========================================================

核心物理问题：大运不再是加减金钱，而是改变环境的"粘滞系数"。

物理映射：
- 大运好（粘滞系数低）→ 财富流体呈层流（高效）
- 大运坏（粘滞系数高）→ 财富流体呈湍流（耗散）

核心公式：
- 雷诺数：Re = (ρ * v * L) / ν_luck
- 粘滞系数：ν_luck = ν_base * (1 + k_luck * |Δφ_luck|)
- 渗透效率：η = f(Re) = 1 / (1 + exp(-(Re - Re_critical) / Re_width))

整合了 InfluenceBus 的大运注入机制。
"""

import numpy as np
import math
from typing import Optional, Any, Dict
from core.trinity.core.nexus.definitions import PhysicsConstants, BaziParticleNexus
from core.trinity.core.middleware.influence_bus import InfluenceBus, NonlinearType


class WealthFluidEngineV13_7:
    """
    [V13.7 物理化升级] 财富流体力学引擎：纳维-斯托克斯方程适配
    
    核心改进：
    1. 粘滞算子：基于 InfluenceBus 注入的 LuckFactor 计算环境粘滞系数
    2. 雷诺数重构：加入大运阻尼依赖 Re = (ρ * v * L) / ν_luck
    3. 渗透映射：根据 Re 数值判定财富的"渗透效率"
    """
    
    # 雷诺数临界值（流动状态判定）
    RE_LAMINAR_THRESHOLD = 2000.0  # 层流阈值
    RE_TRANSITION_THRESHOLD = 4000.0  # 过渡流阈值
    RE_STAGNANT_THRESHOLD = 100.0  # 停滞流阈值
    
    # 渗透效率参数
    RE_CRITICAL = 2000.0  # 临界雷诺数
    RE_WIDTH = 500.0  # 过渡宽度
    
    def __init__(self, dm_element: str):
        """
        初始化财富流体引擎
        
        Args:
            dm_element: 日主元素（如 "Earth"）
        """
        self.dm = dm_element
        # 识别关系（元素字符串）
        self.output = PhysicsConstants.GENERATION.get(dm_element)  # 食伤（输出）
        self.wealth = PhysicsConstants.CONTROL.get(dm_element)     # 财星
        self.rival = dm_element                                     # 比劫（竞争者）
        
        # 找到克制比劫的元素（官杀）
        self.control = next((k for k, v in PhysicsConstants.CONTROL.items() if v == self.rival), None)
    
    def calculate_viscosity_with_luck(
        self,
        e_rival: float,
        e_control: float,
        influence_bus: Optional[InfluenceBus] = None
    ) -> float:
        """
        [V13.7] 计算粘滞系数（包含大运阻尼修正）
        
        公式：ν_luck = ν_base * (1 + k_luck * |Δφ_luck|)
        
        Args:
            e_rival: 比劫能量（摩擦源）
            e_control: 官杀能量（润滑剂）
            influence_bus: InfluenceBus 实例（用于获取大运信息）
        
        Returns:
            粘滞系数 ν_luck
        """
        # 1. 计算基础粘滞系数（复用现有逻辑）
        # [Phase 35-B] 平方律摩擦（非线性阻力）
        friction_term = (e_rival ** 2) * 0.05
        filter_term = e_control * 2.0
        
        nu_base = 1.0 + friction_term - filter_term
        nu_base = max(1.0, nu_base)  # 粘滞系数不能 < 1.0（水的基准值）
        
        # 2. [V13.7] 大运阻尼修正
        # 从 InfluenceBus 获取大运信息
        luck_damping = 1.0  # 默认无阻尼
        luck_phase_shift = 0.0  # 默认无相位差
        
        if influence_bus:
            for factor in influence_bus.active_factors:
                # 检查是否为大运因子
                if factor.name == "LuckCycle/大运" or "Luck" in factor.name or "LuckCycle" in factor.name:
                    # 获取大运阻尼系数
                    luck_damping = factor.metadata.get("damping", 1.0)
                    # 获取相位差（如果有）
                    luck_phase_shift = factor.metadata.get("phase_shift", 0.0)
                    break
        
        # 3. [V13.7] 应用大运阻尼修正
        # 公式：ν_luck = ν_base * (1 + k_luck * |Δφ_luck|)
        # k_luck: 大运阻尼系数（默认 0.1）
        k_luck = 0.1
        phase_impact = abs(luck_phase_shift) * k_luck
        
        # 如果大运有利（damping < 1.0），降低粘滞系数
        # 如果大运不利（damping > 1.0），增加粘滞系数
        luck_modifier = luck_damping * (1.0 + phase_impact)
        
        nu_luck = nu_base * luck_modifier
        nu_luck = max(1.0, nu_luck)  # 确保最小值
        
        return nu_luck
    
    def calculate_reynolds_with_luck(
        self,
        e_wealth: float,
        e_output: float,
        nu_luck: float,
        length_scale: float = 10.0
    ) -> float:
        """
        [V13.7] 计算雷诺数（包含大运阻尼依赖）
        
        公式：Re = (ρ * v * L) / ν_luck
        
        Args:
            e_wealth: 财星能量（流体密度 ρ）
            e_output: 食伤能量（流速 v）
            nu_luck: 粘滞系数（包含大运修正）
            length_scale: 特征长度 L（系统尺度，默认 10.0）
        
        Returns:
            雷诺数 Re
        """
        # 如果没有财星，雷诺数为 0（无流体）
        if e_wealth < 0.1:
            return 0.0
        
        # 映射物理量
        density = e_wealth  # 流体密度
        velocity = e_output * 2.0  # 流速（食伤驱动）
        
        # [V13.7] 雷诺数计算：Re = (ρ * v * L) / ν_luck
        Re = (density * velocity * length_scale) / nu_luck
        
        return Re
    
    def calculate_permeability(self, Re: float) -> Dict[str, float]:
        """
        [V13.7] 计算渗透效率（根据雷诺数判定）
        
        公式：η = f(Re) = 1 / (1 + exp(-(Re - Re_critical) / Re_width))
        
        Args:
            Re: 雷诺数
        
        Returns:
            包含渗透效率和流动状态的字典
        """
        # 1. 判定流动状态
        if Re < self.RE_STAGNANT_THRESHOLD:
            state = "STAGNANT"  # 停滞流
        elif Re < self.RE_LAMINAR_THRESHOLD:
            state = "LAMINAR"  # 层流（稳定、高效）
        elif Re < self.RE_TRANSITION_THRESHOLD:
            state = "TRANSITION"  # 过渡流
        else:
            state = "TURBULENT"  # 湍流（不稳定、耗散）
        
        # 2. [V13.7] 计算渗透效率
        # 使用 Sigmoid 函数平滑过渡
        # η = 1 / (1 + exp(-(Re - Re_critical) / Re_width))
        if Re < 0.1:
            permeability = 0.0  # 无流动
        else:
            # Sigmoid 函数：在 Re_critical 附近平滑过渡
            exponent = -(Re - self.RE_CRITICAL) / self.RE_WIDTH
            permeability = 1.0 / (1.0 + math.exp(exponent))
            
            # 层流状态：渗透效率高（接近 1.0）
            # 湍流状态：渗透效率低（接近 0.0）
            if state == "LAMINAR":
                permeability = min(1.0, permeability * 1.2)  # 层流增强
            elif state == "TURBULENT":
                permeability = max(0.0, permeability * 0.8)  # 湍流衰减
        
        return {
            "permeability": permeability,
            "state": state,
            "reynolds": Re
        }
    
    def analyze_flow(
        self,
        waves: Dict[str, Any],
        influence_bus: Optional[InfluenceBus] = None
    ) -> Dict[str, Any]:
        """
        [V13.7 物理化升级] 分析财富流体动力学
        
        核心改进：
        1. 粘滞系数包含大运阻尼修正
        2. 雷诺数包含大运阻尼依赖
        3. 渗透效率基于雷诺数判定
        
        Args:
            waves: 元素能量字典（WaveState 对象）
            influence_bus: InfluenceBus 实例（用于获取大运信息）
        
        Returns:
            包含雷诺数、粘滞系数、流量、流动状态、渗透效率的字典
        """
        # 1. 获取能量振幅
        # 兼容 WaveState 对象或直接数值
        def get_amplitude(wave_obj):
            if wave_obj is None:
                return 0.0
            if hasattr(wave_obj, 'amplitude'):
                return wave_obj.amplitude
            if isinstance(wave_obj, (int, float)):
                return float(wave_obj)
            return 0.0
        
        e_dm = get_amplitude(waves.get(self.dm))
        e_output = get_amplitude(waves.get(self.output))  # 食伤（流量源）
        e_wealth = get_amplitude(waves.get(self.wealth))  # 财星（流体体积）
        e_rival = get_amplitude(waves.get(self.rival))    # 比劫（摩擦源）
        e_control = get_amplitude(waves.get(self.control))  # 官杀（润滑剂）
        
        # 2. [V13.7] 计算粘滞系数（包含大运阻尼修正）
        nu_luck = self.calculate_viscosity_with_luck(
            e_rival=e_rival,
            e_control=e_control,
            influence_bus=influence_bus
        )
        
        # 3. 计算流量 Q（食伤驱动）
        Q = e_output * 2.0
        
        # 4. [V13.7] 计算雷诺数（包含大运阻尼依赖）
        Re = self.calculate_reynolds_with_luck(
            e_wealth=e_wealth,
            e_output=e_output,
            nu_luck=nu_luck
        )
        
        # 5. [V13.7] 计算渗透效率
        permeability_result = self.calculate_permeability(Re)
        
        return {
            "Reynolds": round(Re, 2),
            "Viscosity": round(nu_luck, 2),
            "Flux": round(Q, 2),
            "State": permeability_result["state"],
            "Permeability": round(permeability_result["permeability"], 4),
            "Metrics": {
                "Wealth_Density": round(e_wealth, 2),
                "Output_Velocity": round(e_output * 2.0, 2),
                "Rival_Friction": round(e_rival, 2),
                "Control_Lubricant": round(e_control, 2),
                "Luck_Damping": round(nu_luck / max(1.0, 1.0 + (e_rival ** 2) * 0.05 - e_control * 2.0), 4) if e_rival > 0 or e_control > 0 else 1.0
            }
        }


# 导出函数别名（兼容现有代码）
def calculate_reynolds(e_wealth: float, e_output: float, nu: float, length_scale: float = 10.0) -> float:
    """
    [V13.7] 计算雷诺数的函数接口（兼容现有代码）
    
    注意：此函数不包含大运阻尼修正，建议使用 WealthFluidEngineV13_7.calculate_reynolds_with_luck()
    """
    if e_wealth < 0.1:
        return 0.0
    density = e_wealth
    velocity = e_output * 2.0
    Re = (density * velocity * length_scale) / nu
    return Re


def calculate_viscosity(e_rival: float, e_control: float) -> float:
    """
    [V13.7] 计算粘滞系数的函数接口（兼容现有代码）
    
    注意：此函数不包含大运阻尼修正，建议使用 WealthFluidEngineV13_7.calculate_viscosity_with_luck()
    """
    friction_term = (e_rival ** 2) * 0.05
    filter_term = e_control * 2.0
    nu = 1.0 + friction_term - filter_term
    return max(1.0, nu)

