"""
[V13.7 物理化升级] MOD_02 极高位格局：相干态判别
=================================================

核心物理问题：系统是否进入超导（从格）或相干消减（化气失败）状态？

物理映射：
- 从格：locking_ratio > 2.0 且 mode == 'COHERENT' → 超导状态
- 假从：mode == 'BEATING' → 干涉包络
- 湮灭：sync_state < 0.12 → 全反射状态

核心公式：
- 从格判定：locking_ratio > 2.0
- 同步状态：sync_state = coherence_factor * energy_concentration
"""

from typing import Dict, Any, Optional, List
from core.trinity.core.middleware.influence_bus import InfluenceBus


class SuperStructureResonanceEngineV13_7:
    """
    [V13.7 物理化升级] 极高位格局共振引擎：相干态判别
    
    核心功能：
    1. 从格判定：locking_ratio > 2.0 且 mode == 'COHERENT'
    2. 假从判定：mode == 'BEATING'
    3. 湮灭判定：sync_state < 0.12
    """
    
    # 从格阈值
    LOCKING_RATIO_THRESHOLD = 2.0
    
    # 湮灭阈值
    ANNIHILATION_THRESHOLD = 0.12
    
    # 相干态阈值
    COHERENT_THRESHOLD = 0.7
    
    def __init__(self):
        """初始化极高位格局共振引擎"""
        pass
    
    def calculate_locking_ratio(
        self,
        energy_distribution: Dict[str, float],
        dominant_element: str
    ) -> float:
        """
        [V13.7] 计算锁定比例（从格判定）
        
        锁定比例 = 主导元素能量 / 其他元素能量总和
        
        Args:
            energy_distribution: 元素能量分布
            dominant_element: 主导元素
        
        Returns:
            锁定比例
        """
        if not energy_distribution or dominant_element not in energy_distribution:
            return 0.0
        
        dominant_energy = energy_distribution[dominant_element]
        other_energy_sum = sum(
            energy for element, energy in energy_distribution.items()
            if element != dominant_element
        )
        
        if other_energy_sum < 0.1:
            return 999.0  # 完全主导
        
        return dominant_energy / other_energy_sum
    
    def calculate_sync_state(
        self,
        energy_distribution: Dict[str, float],
        coherence_factor: float = 1.0
    ) -> float:
        """
        [V13.7] 计算同步状态（湮灭判定）
        
        同步状态 = coherence_factor * energy_concentration
        
        Args:
            energy_distribution: 元素能量分布
            coherence_factor: 相干因子（0-1）
        
        Returns:
            同步状态值（0-1）
        """
        if not energy_distribution:
            return 0.0
        
        total_energy = sum(energy_distribution.values())
        if total_energy < 0.1:
            return 0.0
        
        # 计算能量集中度（最大元素能量占比）
        max_energy = max(energy_distribution.values())
        energy_concentration = max_energy / total_energy
        
        # 同步状态 = 相干因子 * 能量集中度
        sync_state = coherence_factor * energy_concentration
        
        return sync_state
    
    def determine_resonance_mode(
        self,
        energy_distribution: Dict[str, float],
        locking_ratio: float,
        sync_state: float
    ) -> str:
        """
        [V13.7] 判定共振模式
        
        模式类型：
        - COHERENT: 相干态（从格）
        - BEATING: 拍频态（假从）
        - ANNIHILATION: 湮灭态
        - NORMAL: 正常态
        
        Args:
            energy_distribution: 元素能量分布
            locking_ratio: 锁定比例
            sync_state: 同步状态
        
        Returns:
            共振模式字符串
        """
        # 湮灭判定：sync_state < 0.12
        if sync_state < self.ANNIHILATION_THRESHOLD:
            return "ANNIHILATION"
        
        # 从格判定：locking_ratio > 2.0 且 sync_state > 0.7
        if locking_ratio > self.LOCKING_RATIO_THRESHOLD and sync_state > self.COHERENT_THRESHOLD:
            return "COHERENT"
        
        # 假从判定：locking_ratio > 1.5 但 sync_state < 0.7（拍频）
        if locking_ratio > 1.5 and sync_state < self.COHERENT_THRESHOLD:
            return "BEATING"
        
        # 正常态
        return "NORMAL"
    
    def analyze_super_structure(
        self,
        energy_distribution: Dict[str, float],
        dominant_element: Optional[str] = None,
        influence_bus: Optional[InfluenceBus] = None
    ) -> Dict[str, Any]:
        """
        [V13.7 物理化升级] 分析极高位格局（相干态判别）
        
        核心功能：
        1. 从格判定：locking_ratio > 2.0 且 mode == 'COHERENT'
        2. 假从判定：mode == 'BEATING'
        3. 湮灭判定：sync_state < 0.12
        
        Args:
            energy_distribution: 元素能量分布
            dominant_element: 主导元素（如果为 None，自动检测）
            influence_bus: InfluenceBus 实例（用于获取环境修正）
        
        Returns:
            包含格局类型、共振增益、能量趋势的字典
        """
        # 1. 自动检测主导元素（如果未提供）
        if not dominant_element:
            if energy_distribution:
                dominant_element = max(energy_distribution.items(), key=lambda x: x[1])[0]
            else:
                dominant_element = "Unknown"
        
        # 2. 从 InfluenceBus 获取相干因子修正
        coherence_factor = 1.0
        if influence_bus:
            for factor in influence_bus.active_factors:
                if factor.name == "EraBias/时代":
                    # 时代背景可能影响相干性
                    era_bonus = factor.metadata.get("era_bonus", 0.0)
                    coherence_factor = 1.0 + era_bonus * 0.1  # 小幅修正
                    break
        
        # 3. 计算锁定比例
        locking_ratio = self.calculate_locking_ratio(
            energy_distribution=energy_distribution,
            dominant_element=dominant_element
        )
        
        # 4. 计算同步状态
        sync_state = self.calculate_sync_state(
            energy_distribution=energy_distribution,
            coherence_factor=coherence_factor
        )
        
        # 5. 判定共振模式
        mode = self.determine_resonance_mode(
            energy_distribution=energy_distribution,
            locking_ratio=locking_ratio,
            sync_state=sync_state
        )
        
        # 6. 判定格局类型
        pattern_type = "正常格局"
        effect = "正常状态"
        resonance_gain = 1.0
        
        if mode == "COHERENT":
            pattern_type = "从旺/从强"
            effect = "超导状态"
            resonance_gain = 1.5  # 从格增益
        elif mode == "BEATING":
            pattern_type = "假从/拍频"
            effect = "干涉包络"
            resonance_gain = 1.2  # 假从增益（较低）
        elif mode == "ANNIHILATION":
            pattern_type = "系统湮灭"
            effect = "全反射状态"
            resonance_gain = 0.5  # 湮灭衰减
        
        # 7. 计算能量趋势
        total_energy = sum(energy_distribution.values())
        energy_trend = {
            element: energy / total_energy if total_energy > 0 else 0.0
            for element, energy in energy_distribution.items()
        }
        
        return {
            "Pattern_Type": pattern_type,
            "Resonance_Mode": mode,
            "Resonance_Gain": round(resonance_gain, 2),
            "Effect": effect,
            "Metrics": {
                "Locking_Ratio": round(locking_ratio, 2),
                "Sync_State": round(sync_state, 4),
                "Coherence_Factor": round(coherence_factor, 4),
                "Dominant_Element": dominant_element,
                "Energy_Trend": {k: round(v, 4) for k, v in energy_trend.items()}
            }
        }

