"""
[V13.7 物理化升级] MOD_06 情感引力：谐振子摄动模型
===================================================

核心物理问题：流年冲击如何影响情感绑定轨道？

物理映射：
- 流年冲击定义为周期性外力 F(t)
- 情感绑定轨道在流年"冲、刑"脉冲下的位移偏离量

核心公式：
- 轨道摄动：Δr = A * sin(ωt + φ) * e^(-γt)
- 其中：A 为振幅，ω 为频率，φ 为相位，γ 为衰减系数

整合了 InfluenceBus 的流年注入机制。
"""

import numpy as np
import math
from typing import Dict, Any, List, Optional
from core.trinity.core.nexus.definitions import PhysicsConstants, BaziParticleNexus, ArbitrationNexus
from core.trinity.core.middleware.influence_bus import InfluenceBus


class RelationshipGravityEngineV13_7:
    """
    [V13.7 物理化升级] 情感引力场引擎：谐振子摄动模型
    
    核心改进：
    1. 流年冲击：周期性外力 F(t) = A * sin(ωt + φ)
    2. 轨道摄动：Δr = A * sin(ωt + φ) * e^(-γt)
    3. 衰减模型：流年冲击的破坏力随节气进度衰减
    """
    
    # 引力常数（类比）
    G = 6.674
    
    # 谐振子参数
    OMEGA_BASE = 1.0  # 基础频率（归一化）
    GAMMA_DECAY = 0.1  # 衰减系数（流年冲击衰减率）
    
    # 桃花映射
    PEACH_BLOSSOM_MAP = {
        frozenset(['寅', '午', '戌']): '卯',
        frozenset(['申', '子', '辰']): '酉',
        frozenset(['巳', '酉', '丑']): '午',
        frozenset(['亥', '卯', '未']): '子'
    }
    
    def __init__(self, dm_stem: str, gender: str = "男"):
        """
        初始化情感引力引擎
        
        Args:
            dm_stem: 日主天干
            gender: 性别（'男' 或 '女'）
        """
        self.dm_stem = dm_stem
        self.gender = gender
        
        # 获取日主元素
        dm_info = BaziParticleNexus.STEMS.get(dm_stem, ("Unknown", "Unknown", 0))
        self.dm_element = dm_info[0]
        
        # 确定配偶星元素
        if gender == "男":
            self.spouse_star_element = PhysicsConstants.CONTROL.get(self.dm_element)  # 财星
        else:
            self.spouse_star_element = next(
                (k for k, v in PhysicsConstants.CONTROL.items() if v == self.dm_element),
                None
            )
    
    def calculate_annual_orbital_perturbation(
        self,
        annual_pillar: Optional[str],
        spouse_palace: str,
        base_r: float,
        influence_bus: Optional[InfluenceBus] = None
    ) -> Dict[str, float]:
        """
        [V13.7] 计算流年轨道摄动（谐振子模型）
        
        公式：Δr = A * sin(ωt + φ) * e^(-γt)
        
        Args:
            annual_pillar: 流年干支
            spouse_palace: 配偶宫（日支）
            base_r: 基础轨道距离
            influence_bus: InfluenceBus 实例（用于获取流年相位信息）
        
        Returns:
            包含摄动位移、相位、频率的字典
        """
        if not annual_pillar or len(annual_pillar) < 2:
            return {
                "delta_r": 0.0,
                "phase": 0.0,
                "frequency": 0.0,
                "amplitude": 0.0,
                "decay_factor": 1.0
            }
        
        annual_branch = annual_pillar[1]
        annual_stem = annual_pillar[0]
        
        # 1. 检测流年与配偶宫的相互作用
        amplitude = 0.0
        phase = 0.0
        is_clash = False
        is_join = False
        
        # 检查冲（六冲）
        clash_target = ArbitrationNexus.CLASH_MAP.get(annual_branch)
        if clash_target == spouse_palace:
            amplitude = 50.0  # 冲的振幅（轨道扩张）
            phase = math.pi  # 180度相位（相消）
            is_clash = True
        elif ArbitrationNexus.CLASH_MAP.get(spouse_palace) == annual_branch:
            amplitude = 50.0
            phase = math.pi
            is_clash = True
        
        # 检查合（六合）
        for pair, _ in ArbitrationNexus.LIU_HE.items():
            if annual_branch in pair and spouse_palace in pair:
                amplitude = -30.0  # 合的振幅（轨道收缩，负值）
                phase = 0.0  # 0度相位（相长）
                is_join = True
                break
        
        # 检查刑（三刑）
        penalty_info = BaziParticleNexus.PENALTY_GROUPS.get(annual_branch)
        if penalty_info and spouse_palace in penalty_info.get('components', []):
            if not is_clash:  # 如果已经有冲，不再叠加刑
                amplitude = 25.0
                phase = math.pi / 2  # 90度相位
        elif penalty_info:
            # 检查反向刑
            for comp in penalty_info.get('components', []):
                if comp == spouse_palace:
                    if not is_clash:
                        amplitude = 25.0
                        phase = math.pi / 2
                    break
        
        # 2. [V13.7] 从 InfluenceBus 获取流年相位信息
        annual_phase = 0.0
        annual_frequency = self.OMEGA_BASE
        
        if influence_bus:
            for factor in influence_bus.active_factors:
                if factor.name == "AnnualPulse/流年" or "Annual" in factor.name:
                    # 获取相位信息（如果可用）
                    annual_phase = factor.metadata.get("phase", 0.0)
                    annual_frequency = factor.metadata.get("frequency", self.OMEGA_BASE)
                    break
        
        # 3. [V13.7] 计算谐振子摄动
        # 公式：Δr = A * sin(ωt + φ) * e^(-γt)
        # 其中：t 为时间（归一化为 0-1，表示流年进度）
        # 假设流年进度为 0.5（年中），可以根据实际需求调整
        t = 0.5  # 流年进度（0-1）
        
        # 合成相位：流年相位 + 相互作用相位
        total_phase = annual_phase + phase
        
        # 衰减因子：e^(-γt)
        decay_factor = math.exp(-self.GAMMA_DECAY * t)
        
        # 摄动位移：Δr = A * sin(ωt + φ) * e^(-γt)
        delta_r = amplitude * math.sin(annual_frequency * t + total_phase) * decay_factor
        
        return {
            "delta_r": delta_r,
            "phase": total_phase,
            "frequency": annual_frequency,
            "amplitude": amplitude,
            "decay_factor": decay_factor,
            "is_clash": is_clash,
            "is_join": is_join
        }
    
    def calculate_binding_energy(
        self,
        m_dm: float,
        m_spouse: float,
        r: float,
        geo_factor: float = 1.0
    ) -> float:
        """
        [V13.7] 计算引力绑定能（复用现有逻辑）
        
        公式：E = -G * M_dm * M_spouse / (2 * r)
        
        Args:
            m_dm: 日主质量（能量）
            m_spouse: 配偶星质量（能量）
            r: 轨道距离
            geo_factor: 地理修正系数
        
        Returns:
            绑定能 E（负值表示绑定）
        """
        G_effective = self.G * geo_factor
        binding_energy = -G_effective * m_dm * m_spouse / (2.0 * r)
        return binding_energy
    
    def calculate_orbital_stability(
        self,
        binding_energy: float,
        perturbation_energy: float
    ) -> float:
        """
        [V13.7] 计算轨道稳定性（复用现有逻辑）
        
        公式：σ = |E_bind| / E_perturb
        
        Args:
            binding_energy: 绑定能
            perturbation_energy: 摄动能
        
        Returns:
            轨道稳定性 σ
        """
        if perturbation_energy < 0.1:
            return 999.0  # 无摄动，极高稳定性
        return abs(binding_energy) / perturbation_energy
    
    def analyze_relationship(
        self,
        waves: Dict[str, Any],
        pillars: List[str],
        influence_bus: Optional[InfluenceBus] = None
    ) -> Dict[str, Any]:
        """
        [V13.7 物理化升级] 分析情感引力动力学（整合谐振子摄动模型）
        
        核心改进：
        1. 流年冲击：周期性外力 F(t)
        2. 轨道摄动：Δr = A * sin(ωt + φ) * e^(-γt)
        3. 衰减模型：流年冲击的破坏力随节气进度衰减
        
        Args:
            waves: 元素能量字典
            pillars: 四柱列表
            influence_bus: InfluenceBus 实例
        
        Returns:
            包含绑定能、轨道稳定性、相位相干性、摄动信息的字典
        """
        # 1. 提取流年和大运信息
        annual_pillar = None
        luck_pillar = None
        geo_factor = 1.0
        
        if influence_bus:
            for factor in influence_bus.active_factors:
                if factor.name == "AnnualPulse/流年" or "Annual" in factor.name:
                    annual_pillar = factor.metadata.get("annual_pillar")
                if factor.name == "LuckCycle/大运" or "Luck" in factor.name:
                    luck_pillar = factor.metadata.get("luck_pillar")
                if factor.name == "GeoBias/地域":
                    geo_factor = factor.metadata.get("geo_factor", 1.0)
        
        # 2. 提取日支（配偶宫）
        day_pillar = pillars[2] if len(pillars) > 2 else ""
        spouse_palace = day_pillar[1] if len(day_pillar) > 1 else ""
        
        # 3. 获取能量质量
        def get_amplitude(wave_obj):
            if wave_obj is None:
                return 1.0
            if hasattr(wave_obj, 'amplitude'):
                return wave_obj.amplitude
            if isinstance(wave_obj, (int, float)):
                return float(wave_obj)
            return 1.0
        
        m_dm = get_amplitude(waves.get(self.dm_element))
        m_spouse = get_amplitude(waves.get(self.spouse_star_element))
        
        # 4. 应用大运修正（复用现有逻辑）
        luck_modifier = 1.0
        if luck_pillar and len(luck_pillar) > 1:
            luck_branch = luck_pillar[1]
            luck_element = BaziParticleNexus.BRANCHES.get(luck_branch, ("Unknown",))[0]
            if luck_element == self.spouse_star_element:
                luck_modifier = 1.3
            elif PhysicsConstants.CONTROL.get(luck_element) == self.spouse_star_element:
                luck_modifier = 0.7
            if ArbitrationNexus.CLASH_MAP.get(luck_branch) == spouse_palace:
                luck_modifier *= 0.6
        m_spouse *= luck_modifier
        
        # 5. 计算基础轨道距离
        spouse_palace_element = BaziParticleNexus.BRANCHES.get(spouse_palace, ("Unknown",))[0]
        if spouse_palace_element == self.spouse_star_element:
            base_r = 1.0  # 紧轨道
        elif self._elements_compatible(spouse_palace_element, self.spouse_star_element):
            base_r = 2.0  # 兼容轨道
        else:
            base_r = 5.0  # 远轨道
        
        # 6. [V13.7] 计算流年轨道摄动（谐振子模型）
        perturbation_result = self.calculate_annual_orbital_perturbation(
            annual_pillar=annual_pillar,
            spouse_palace=spouse_palace,
            base_r=base_r,
            influence_bus=influence_bus
        )
        
        # 7. 应用摄动修正到轨道距离
        delta_r = perturbation_result["delta_r"]
        r_perturbed = base_r + delta_r
        r_perturbed = max(0.1, r_perturbed)  # 确保最小值
        
        # 8. 计算绑定能
        binding_energy = self.calculate_binding_energy(
            m_dm=m_dm,
            m_spouse=m_spouse,
            r=r_perturbed,
            geo_factor=geo_factor
        )
        
        # 9. 计算摄动能（用于稳定性计算）
        perturbation_energy = abs(delta_r) * 10.0  # 摄动能与位移成正比
        
        # 10. 计算轨道稳定性
        orbital_stability = self.calculate_orbital_stability(
            binding_energy=binding_energy,
            perturbation_energy=perturbation_energy
        )
        
        # 11. 计算相位相干性（复用现有逻辑）
        dm_phase = getattr(waves.get(self.dm_element), 'phase', 0.0) if hasattr(waves.get(self.dm_element), 'phase') else 0.0
        spouse_phase = getattr(waves.get(self.spouse_star_element), 'phase', 0.0) if hasattr(waves.get(self.spouse_star_element), 'phase') else 0.0
        delta_phi = abs(dm_phase - spouse_phase)
        phase_coherence = math.cos(delta_phi / 2.0) ** 2
        
        # 12. 计算桃花波函数（复用现有逻辑）
        peach_amplitude = self._calculate_peach_blossom(pillars)
        
        # 13. 判定关系状态
        state = self._determine_state(r_perturbed, orbital_stability, phase_coherence)
        
        return {
            "Binding_Energy": round(binding_energy, 2),
            "Orbital_Stability": round(orbital_stability, 2),
            "Phase_Coherence": round(phase_coherence, 4),
            "Peach_Blossom_Amplitude": round(peach_amplitude, 2),
            "State": state,
            "Metrics": {
                "DM_Mass": round(m_dm, 2),
                "Spouse_Mass": round(m_spouse, 2),
                "Base_Orbital_Distance": round(base_r, 2),
                "Perturbed_Orbital_Distance": round(r_perturbed, 2),
                "Perturbation_Delta_r": round(delta_r, 2),
                "Perturbation_Phase": round(perturbation_result["phase"], 4),
                "Perturbation_Frequency": round(perturbation_result["frequency"], 4),
                "Perturbation_Amplitude": round(perturbation_result["amplitude"], 2),
                "Decay_Factor": round(perturbation_result["decay_factor"], 4),
                "Spouse_Star": self.spouse_star_element,
                "Spouse_Palace": spouse_palace,
                "Luck_Modifier": round(luck_modifier, 2),
                "Geo_Factor": geo_factor
            }
        }
    
    def _elements_compatible(self, elem1: str, elem2: str) -> bool:
        """检查两个元素是否生成关系"""
        if not elem1 or not elem2:
            return False
        return PhysicsConstants.GENERATION.get(elem1) == elem2 or \
               PhysicsConstants.GENERATION.get(elem2) == elem1
    
    def _calculate_peach_blossom(self, pillars: List[str]) -> float:
        """计算桃花波函数振幅（复用现有逻辑）"""
        if len(pillars) < 3:
            return 0.0
        
        year_branch = pillars[0][1] if len(pillars[0]) > 1 else ""
        day_branch = pillars[2][1] if len(pillars[2]) > 1 else ""
        all_branches = set(p[1] for p in pillars if len(p) > 1)
        
        amplitude = 0.0
        
        for triad, peach in self.PEACH_BLOSSOM_MAP.items():
            if year_branch in triad:
                if peach in all_branches:
                    amplitude += 30.0
                break
        
        for triad, peach in self.PEACH_BLOSSOM_MAP.items():
            if day_branch in triad:
                if peach in all_branches:
                    amplitude += 20.0
                break
        
        return amplitude
    
    def _determine_state(self, r: float, orbital_stability: float, phase_coherence: float) -> str:
        """判定关系状态（复用现有逻辑）"""
        if phase_coherence < 0.1:
            if orbital_stability > 1.0:
                return "PERTURBED"
            else:
                return "UNBOUND"
        elif r >= 6.0:
            return "UNBOUND"
        elif r >= 4.0:
            return "PERTURBED"
        elif r >= 2.5:
            if orbital_stability > 1.5:
                return "BOUND"
            else:
                return "PERTURBED"
        elif orbital_stability > 2.0 and phase_coherence > 0.7:
            return "ENTANGLED"
        elif orbital_stability > 1.0:
            return "BOUND"
        elif orbital_stability > 0.5:
            return "PERTURBED"
        else:
            return "UNBOUND"


# 导出函数别名（兼容现有代码）
def calculate_binding_energy(m_dm: float, m_spouse: float, r: float, G: float = 6.674, geo_factor: float = 1.0) -> float:
    """计算绑定能的函数接口（兼容现有代码）"""
    G_effective = G * geo_factor
    return -G_effective * m_dm * m_spouse / (2.0 * r)

