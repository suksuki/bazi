"""
[V13.7 物理化升级] MOD_18 全局干涉检测：交叉因子耦合
=====================================================

核心物理问题：模块间的"二阶干预"如何实现？

物理映射：
- 交叉干涉：当 MOD_04（刑害）产生极高 SAI 时，应自动增加 MOD_05（财富）的粘滞系数
- 应力反馈：应力导致财富流速减缓的交叉反馈

核心公式：
- 交叉干涉修正：ν_cross = ν_base * (1 + k_cross * SAI)
- 其中：k_cross 为交叉耦合系数，SAI 为结构异常指数

整合了 InfluenceBus 的全局状态注入机制。
"""

from typing import Dict, Any, Optional, List
from core.trinity.core.middleware.influence_bus import InfluenceBus


class GlobalInterferenceEngineV13_7:
    """
    [V13.7 物理化升级] 全局干涉引擎：交叉因子耦合
    
    核心功能：
    1. 交叉干涉检测：检测模块间的二阶干预
    2. 应力反馈：将 SAI 指数反馈给财富和情感引擎
    3. 全局状态汇总：汇总所有模块的物理指标
    """
    
    # 交叉耦合系数
    K_CROSS_WEALTH = 0.15  # 财富模块的交叉耦合系数
    K_CROSS_RELATIONSHIP = 0.12  # 情感模块的交叉耦合系数
    K_CROSS_IMPEDANCE = 0.10  # 阻抗模块的交叉耦合系数
    
    # SAI 阈值
    SAI_HIGH_THRESHOLD = 0.6  # 高 SAI 阈值
    SAI_CRITICAL_THRESHOLD = 0.8  # 临界 SAI 阈值
    
    def __init__(self):
        """初始化全局干涉引擎"""
        pass
    
    def calculate_cross_interference(
        self,
        sai_index: float,
        target_module: str,
        base_value: float,
        influence_bus: Optional[InfluenceBus] = None
    ) -> float:
        """
        [V13.7] 计算交叉干涉修正
        
        公式：ν_cross = ν_base * (1 + k_cross * SAI)
        
        Args:
            sai_index: 结构异常指数（SAI）
            target_module: 目标模块（如 "MOD_05_WEALTH", "MOD_06_RELATIONSHIP"）
            base_value: 基础值（如粘滞系数、阻抗等）
            influence_bus: InfluenceBus 实例
        
        Returns:
            修正后的值
        """
        # 根据目标模块选择交叉耦合系数
        if "WEALTH" in target_module or "MOD_05" in target_module:
            k_cross = self.K_CROSS_WEALTH
        elif "RELATIONSHIP" in target_module or "MOD_06" in target_module:
            k_cross = self.K_CROSS_RELATIONSHIP
        elif "IMPEDANCE" in target_module or "MOD_15" in target_module:
            k_cross = self.K_CROSS_IMPEDANCE
        else:
            k_cross = 0.1  # 默认值
        
        # 从 InfluenceBus 获取全局状态修正
        global_modifier = 1.0
        if influence_bus:
            for factor in influence_bus.active_factors:
                if factor.name == "EraBias/时代":
                    # 时代背景可能影响交叉干涉强度
                    era_bonus = factor.metadata.get("era_bonus", 0.0)
                    global_modifier = 1.0 + era_bonus * 0.05
                    break
        
        # 计算交叉干涉修正：ν_cross = ν_base * (1 + k_cross * SAI)
        cross_correction = 1.0 + k_cross * sai_index
        cross_correction *= global_modifier
        
        corrected_value = base_value * cross_correction
        
        return corrected_value
    
    def detect_global_interference(
        self,
        module_states: Dict[str, Dict[str, Any]],
        influence_bus: Optional[InfluenceBus] = None
    ) -> Dict[str, Any]:
        """
        [V13.7] 检测全局干涉
        
        Args:
            module_states: 模块状态字典（包含各模块的物理指标）
            influence_bus: InfluenceBus 实例
        
        Returns:
            包含交叉干涉修正和全局状态的字典
        """
        # 提取 SAI 指数（从 MOD_04 或其他模块）
        sai_index = 0.0
        if "MOD_04" in module_states:
            sai_index = module_states["MOD_04"].get("SAI", 0.0)
        elif "SAI" in module_states:
            sai_index = module_states["SAI"]
        
        # 计算交叉干涉修正
        cross_corrections = {}
        
        # MOD_05 财富流体：粘滞系数修正
        if "MOD_05" in module_states:
            base_viscosity = module_states["MOD_05"].get("Viscosity", 1.0)
            corrected_viscosity = self.calculate_cross_interference(
                sai_index=sai_index,
                target_module="MOD_05_WEALTH",
                base_value=base_viscosity,
                influence_bus=influence_bus
            )
            cross_corrections["MOD_05_Viscosity"] = corrected_viscosity
        
        # MOD_06 情感引力：轨道稳定性修正
        if "MOD_06" in module_states:
            base_stability = module_states["MOD_06"].get("Orbital_Stability", 1.0)
            # 高 SAI 降低轨道稳定性
            corrected_stability = base_stability / (1.0 + self.K_CROSS_RELATIONSHIP * sai_index)
            cross_corrections["MOD_06_Stability"] = corrected_stability
        
        # MOD_15 结构传导：阻抗修正
        if "MOD_15" in module_states:
            base_impedance = module_states["MOD_15"].get("Impedance", 1.0)
            corrected_impedance = self.calculate_cross_interference(
                sai_index=sai_index,
                target_module="MOD_15_STRUCTURAL_VIBRATION",
                base_value=base_impedance,
                influence_bus=influence_bus
            )
            cross_corrections["MOD_15_Impedance"] = corrected_impedance
        
        # 判定干涉等级
        interference_level = "NORMAL"
        if sai_index >= self.SAI_CRITICAL_THRESHOLD:
            interference_level = "CRITICAL"
        elif sai_index >= self.SAI_HIGH_THRESHOLD:
            interference_level = "HIGH"
        
        return {
            "SAI_Index": round(sai_index, 4),
            "Interference_Level": interference_level,
            "Cross_Corrections": {k: round(v, 4) for k, v in cross_corrections.items()},
            "Metrics": {
                "K_Cross_Wealth": self.K_CROSS_WEALTH,
                "K_Cross_Relationship": self.K_CROSS_RELATIONSHIP,
                "K_Cross_Impedance": self.K_CROSS_IMPEDANCE
            }
        }
    
    def generate_integrated_report(
        self,
        module_results: Dict[str, Dict[str, Any]],
        influence_bus: Optional[InfluenceBus] = None
    ) -> Dict[str, Any]:
        """
        [V13.7] 生成集成报告（全参数联动波动图）
        
        将财富雷诺数、情感轨道偏移、系统熵、复阻抗效率汇总，输出一张"全参数联动波动图"。
        
        Args:
            module_results: 各模块计算结果字典
            influence_bus: InfluenceBus 实例
        
        Returns:
            包含所有物理指标的集成报告
        """
        # 提取各模块的关键指标
        integrated_metrics = {}
        
        # MOD_05 财富流体
        if "MOD_05" in module_results:
            wealth_data = module_results["MOD_05"]
            integrated_metrics["Wealth"] = {
                "Reynolds": wealth_data.get("Reynolds", 0.0),
                "Viscosity": wealth_data.get("Viscosity", 1.0),
                "Permeability": wealth_data.get("Permeability", 0.0),
                "State": wealth_data.get("State", "UNKNOWN")
            }
        
        # MOD_06 情感引力
        if "MOD_06" in module_results:
            relationship_data = module_results["MOD_06"]
            integrated_metrics["Relationship"] = {
                "Binding_Energy": relationship_data.get("Binding_Energy", 0.0),
                "Orbital_Stability": relationship_data.get("Orbital_Stability", 0.0),
                "Phase_Coherence": relationship_data.get("Phase_Coherence", 0.0),
                "Perturbation_Delta_r": relationship_data.get("Metrics", {}).get("Perturbation_Delta_r", 0.0)
            }
        
        # MOD_02 极高位格局
        if "MOD_02" in module_results:
            super_data = module_results["MOD_02"]
            integrated_metrics["Super_Structure"] = {
                "Locking_Ratio": super_data.get("Metrics", {}).get("Locking_Ratio", 0.0),
                "Sync_State": super_data.get("Metrics", {}).get("Sync_State", 0.0),
                "Pattern_Type": super_data.get("Pattern_Type", "NORMAL")
            }
        
        # MOD_10 通根增益
        if "MOD_10" in module_results:
            resonance_data = module_results["MOD_10"]
            integrated_metrics["Resonance"] = {
                "Rooting_Gain": resonance_data.get("gain", 0.0),
                "Status": resonance_data.get("status", "UNKNOWN")
            }
        
        # MOD_15 结构传导
        if "MOD_15" in module_results:
            impedance_data = module_results["MOD_15"]
            integrated_metrics["Impedance"] = {
                "R": impedance_data.get("R", 0.0),
                "X": impedance_data.get("X", 0.0),
                "Z_Magnitude": impedance_data.get("Z_Magnitude", 0.0),
                "Efficiency": impedance_data.get("Efficiency", 0.0)
            }
        
        # MOD_17 星辰相干
        if "MOD_17" in module_results:
            stellar_data = module_results["MOD_17"]
            integrated_metrics["Stellar"] = {
                "Entropy_Damping": stellar_data.get("Metrics", {}).get("Entropy_Damping", 0.0),
                "SNR_Boost": stellar_data.get("Metrics", {}).get("SNR_Boost", 0.0)
            }
        
        # 检测全局干涉
        interference_result = self.detect_global_interference(
            module_states=module_results,
            influence_bus=influence_bus
        )
        
        # 汇总 InfluenceBus 参数
        influence_params = {}
        if influence_bus:
            for factor in influence_bus.active_factors:
                if factor.name == "LuckCycle/大运":
                    influence_params["Luck"] = {
                        "Damping": factor.metadata.get("damping", 1.0),
                        "Phase_Shift": factor.metadata.get("phase_shift", 0.0)
                    }
                elif factor.name == "AnnualPulse/流年":
                    influence_params["Annual"] = {
                        "Phase": factor.metadata.get("phase", 0.0),
                        "Frequency": factor.metadata.get("frequency", 1.0)
                    }
                elif factor.name == "GeoBias/地域":
                    influence_params["Geo"] = {
                        "Factor": factor.metadata.get("geo_factor", 1.0),
                        "Element": factor.metadata.get("geo_element", None)
                    }
                elif factor.name == "EraBias/时代":
                    influence_params["Era"] = {
                        "Bonus": factor.metadata.get("era_bonus", 0.0),
                        "Element": factor.metadata.get("era_element", None)
                    }
        
        return {
            "Integrated_Metrics": integrated_metrics,
            "Global_Interference": interference_result,
            "Influence_Parameters": influence_params,
            "Summary": {
                "Total_Modules": len(module_results),
                "Interference_Level": interference_result.get("Interference_Level", "NORMAL"),
                "SAI_Index": interference_result.get("SAI_Index", 0.0)
            }
        }

