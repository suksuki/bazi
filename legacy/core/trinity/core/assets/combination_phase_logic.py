"""
[V13.7 整合升级] Antigravity Combination Phase Logic (Phase B-09)
==================================================================
Core physics logic for determining Stem Combination Phase Transitions.

整合了阿伦尼乌斯公式修正（地理能垒），实现真正的物理动力学模型。
"""

import math
from typing import List, Dict, Any, Optional

class CombinationPhaseEngine:
    """
    [V13.7] 合化相位判定引擎：整合了阿伦尼乌斯公式修正
    
    核心公式：P_transform = A * exp(-E_a / (k_B * T_geo))
    - E_a: 活化能垒（受地理环境影响）
    - T_geo: 地理温度（从InfluenceBus获取）
    - k_B: 玻尔兹曼常数（归一化为1.0）
    """
    
    # Critical Phase Change Threshold
    THRESHOLD = 0.65

    @staticmethod
    def check_combination_phase(
        stems: List[str], 
        month_energy: float,
        geo_temperature: float = 1.0,
        target_element: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        [V13.7 整合升级] 判定干合是否成功化气（整合阿伦尼乌斯公式修正）
        
        Args:
            stems: List of combining stems (e.g., ['丁', '壬'])
            month_energy: The normalized energy coefficient of the target element in the month (0.0 - 1.0+)
            geo_temperature: 地理温度（从InfluenceBus获取，默认1.0）
            target_element: 化气目标元素（用于判断是否需要地理能垒修正）
            
        Returns:
            Dict: Status, Message, Power Ratio, and Geo Correction Info.
        """
        # [V13.7] 地理能垒修正（阿伦尼乌斯公式）
        threshold_effective = CombinationPhaseEngine.THRESHOLD
        geo_correction_info = {}
        
        if target_element and target_element.lower() == 'fire' and geo_temperature > 1.0:
            # 火区环境：降低化火能垒
            E_a_base = 1.0  # 基础活化能垒
            E_a = E_a_base / geo_temperature
            
            # 阿伦尼乌斯公式：P = A * exp(-E_a / T)
            k_B = 1.0  # 玻尔兹曼常数（归一化）
            T_geo = max(0.1, geo_temperature)  # 避免除零
            transform_probability = math.exp(-E_a / (k_B * T_geo))
            
            # 修正阈值：地理环境有利时，有效阈值降低（更容易合化）
            threshold_effective = CombinationPhaseEngine.THRESHOLD / max(0.1, transform_probability)
            
            geo_correction_info = {
                "applied": True,
                "E_a": E_a,
                "T_geo": geo_temperature,
                "transform_probability": transform_probability,
                "threshold_effective": threshold_effective
            }
        else:
            geo_correction_info = {"applied": False}
        
        # Threshold Logic (使用修正后的阈值)
        if month_energy >= threshold_effective:
            result = {
                "status": "PHASE_TRANSITION", 
                "msg": "合化成功 (Transformation Success)", 
                "power_ratio": 1.0,
                "dynamic_gain": "SUPERCONDUCTING",
                "geo_correction": geo_correction_info
            }
            if geo_correction_info.get("applied"):
                result["msg"] += f" [地理能垒修正: E_a={geo_correction_info['E_a']:.3f}, T_geo={geo_correction_info['T_geo']:.2f}]"
            return result
        else:
            return {
                "status": "ENTANGLEMENT", 
                "msg": "合而不化 (Entanglement/Bound)", 
                "power_ratio": 0.3, # Residual binding interference
                "dynamic_gain": "INTERFERENCE",
                "geo_correction": geo_correction_info
            }

# Export functional alias
check_combination_phase = CombinationPhaseEngine.check_combination_phase
