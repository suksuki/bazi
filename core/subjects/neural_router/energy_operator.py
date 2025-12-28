"""
[QGA V25.0] 能量叠加算子模块 (Energy Operator)
RSS-V1.2规范：显性化实现能量叠加公式

能量叠加公式：
E_total = [ (E_base ⊗ ω_luck) ⊕ ΔE_year ] × (1 ± δ_geo)

符号定义：
- ⊗ (非线性耦合)：大运场能与原局能量的非线性穿透（张量积）
- ⊕ (瞬时叠加)：流年脉冲能量与[原局+大运]耦合场后的矢量叠加（直和）
- δ_geo (修正因子)：地理修正算子，基准值为[原局+大运+流年]的结果，限制在±15%以内
"""

import logging
from typing import Dict, Any, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class EnergyOperator:
    """
    能量叠加算子（RSS-V1.1规范）
    
    显性化实现能量叠加公式，确保物理逻辑可追溯
    """
    
    def __init__(self):
        self.geo_correction_limit = 0.15  # RSS-V1.2规范：地理修正限制在±15%以内
        logger.info("✅ 能量叠加算子初始化完成（RSS-V1.2规范）")
    
    def tensor_product(self, 
                      base_energy: Dict[str, float],
                      luck_weight: float = 1.0) -> Dict[str, float]:
        """
        张量积运算（⊗）：大运场能与原局能量的非线性穿透
        
        RSS-V1.2规范：
        - ⊗ (非线性耦合)：表示大运场能与原局能量的非线性穿透（张量积）
        - 决定底层能级的整体位移
        
        Args:
            base_energy: 原局能量场（E_base）
            luck_weight: 大运权重（ω_luck），默认1.0（最高优先级基准场修正）
        
        Returns:
            耦合后的能量场（E_base ⊗ ω_luck）
        """
        # 非线性耦合：每个元素场乘以luck_weight，但保持相对比例
        coupled_energy = {}
        total_base = sum(base_energy.values()) if base_energy else 1.0
        
        for element, value in base_energy.items():
            # 非线性穿透：不仅放大数值，还考虑场强分布
            coupled_value = value * luck_weight * (1 + value / max(total_base, 0.1))
            coupled_energy[element] = coupled_value
        
        return coupled_energy
    
    def direct_sum(self,
                  coupled_energy: Dict[str, float],
                  year_pulse: Dict[str, float]) -> Dict[str, float]:
        """
        直和运算（⊕）：流年脉冲能量与[原局+大运]耦合场后的矢量叠加
        
        RSS-V1.2规范：
        - ⊕ (瞬时叠加)：表示流年脉冲能量与[原局+大运]耦合场后的矢量叠加（直和）
        - 负责触发奇点
        
        Args:
            coupled_energy: 耦合后的能量场（E_base ⊗ ω_luck）
            year_pulse: 流年脉冲能量（ΔE_year）
        
        Returns:
            叠加后的能量场（(E_base ⊗ ω_luck) ⊕ ΔE_year）
        """
        # 矢量叠加：直接相加，但考虑方向性
        summed_energy = {}
        
        # 先复制耦合能量
        for element, value in coupled_energy.items():
            summed_energy[element] = value
        
        # 叠加流年脉冲（矢量叠加）
        for element, pulse_value in year_pulse.items():
            if element in summed_energy:
                # 矢量叠加：直接相加（考虑正负方向）
                summed_energy[element] += pulse_value
            else:
                summed_energy[element] = pulse_value
        
        return summed_energy
    
    def geo_correction(self,
                      total_energy: Dict[str, float],
                      geo_damping: float = 0.0) -> Dict[str, float]:
        """
        地理修正算子（δ_geo）：介质阻尼修正
        
        RSS-V1.2规范：
        - δ_geo (修正因子)：地理修正算子
        - 基准值为[原局+大运+流年]的结果
        - 限制在±15%以内
        
        Args:
            total_energy: 叠加后的能量场（(E_base ⊗ ω_luck) ⊕ ΔE_year）
            geo_damping: 地理阻尼系数（-0.15 到 +0.15）
        
        Returns:
            修正后的能量场 E_total = [ (E_base ⊗ ω_luck) ⊕ ΔE_year ] × (1 ± δ_geo)
        """
        # 限制地理修正系数在±15%以内
        geo_damping = max(-self.geo_correction_limit, 
                         min(self.geo_correction_limit, geo_damping))
        
        # 应用修正：E_total = E × (1 ± δ_geo)
        corrected_energy = {}
        for element, value in total_energy.items():
            corrected_energy[element] = value * (1.0 + geo_damping)
        
        logger.debug(f"📊 地理修正: damping={geo_damping:.3f} (限制在±{self.geo_correction_limit*100:.0f}%以内)")
        
        return corrected_energy
    
    def compute_total_energy(self,
                            base_energy: Dict[str, float],
                            luck_weight: float = 1.0,
                            year_pulse: Optional[Dict[str, float]] = None,
                            geo_damping: float = 0.0) -> Dict[str, float]:
        """
        计算总能量（完整公式）
        
        RSS-V1.1规范能量叠加公式：
        E_total = [ (E_base ⊗ ω_luck) ⊕ ΔE_year ] × (1 ± δ_geo)
        
        Args:
            base_energy: 原局能量场（E_base）
            luck_weight: 大运权重（ω_luck），默认1.0
            year_pulse: 流年脉冲能量（ΔE_year），可选
            geo_damping: 地理阻尼系数（δ_geo），默认0.0
        
        Returns:
            总能量场（E_total）
        """
        # Step 1: 张量积运算（⊗）
        coupled_energy = self.tensor_product(base_energy, luck_weight)
        
        # Step 2: 直和运算（⊕）
        if year_pulse:
            total_before_geo = self.direct_sum(coupled_energy, year_pulse)
        else:
            total_before_geo = coupled_energy
        
        # Step 3: 地理修正（× (1 ± δ_geo)）
        total_energy = self.geo_correction(total_before_geo, geo_damping)
        
        logger.debug(f"✅ 能量叠加完成: base={sum(base_energy.values()):.3f}, "
                    f"coupled={sum(coupled_energy.values()):.3f}, "
                    f"total={sum(total_energy.values()):.3f}")
        
        return total_energy
    
    def calculate_geo_damping_from_info(self, geo_info: str) -> float:
        """
        从地理信息计算阻尼系数
        
        RSS-V1.2规范：地理修正限制在±15%以内
        
        Args:
            geo_info: 地理信息（如"南方"、"北方"、"中央"等）
        
        Returns:
            地理阻尼系数（-0.15 到 +0.15）
        """
        # 简化的地理阻尼映射（可根据实际需求扩展）
        geo_damping_map = {
            '南方': 0.10,  # 火地，增强火元素
            '北方': -0.10,  # 水地，增强水元素
            '东方': 0.05,  # 木地，增强木元素
            '西方': -0.05,  # 金地，增强金元素
            '中央': 0.0,  # 中性
            '东南': 0.08,
            '西南': 0.03,
            '东北': -0.03,
            '西北': -0.08
        }
        
        damping = geo_damping_map.get(geo_info, 0.0)
        
        # 确保在±15%限制内
        damping = max(-self.geo_correction_limit, 
                     min(self.geo_correction_limit, damping))
        
        return damping

