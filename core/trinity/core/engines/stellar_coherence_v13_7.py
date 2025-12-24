"""
[V13.7 物理化升级] MOD_17 星辰相干：神煞场强修正
=================================================

核心物理问题：神煞不再是标签，而是信噪比（SNR）和熵（Entropy）的修正算子。

物理映射：
- 天乙贵人：熵衰减 10%（entropy_damping = 0.1）
- 文昌：信噪比提升 15%（SNR_boost = 0.15）
- 桃花：量子引力增强（relationship_binding_boost）
- 驿马：动能冲量（kinetic_impulse）

核心公式：
- 熵修正：S_new = S_old * (1 - entropy_damping)
- 信噪比修正：SNR_new = SNR_old * (1 + SNR_boost)
"""

from typing import Dict, Any, Optional, List
from core.trinity.core.middleware.influence_bus import InfluenceBus
from core.trinity.core.nexus.definitions import BaziParticleNexus


class StellarCoherenceEngineV13_7:
    """
    [V13.7 物理化升级] 星辰相干引擎：神煞场强修正
    
    核心功能：
    1. 天乙贵人：熵衰减 10%
    2. 文昌：信噪比提升 15%
    3. 桃花：量子引力增强
    4. 驿马：动能冲量
    """
    
    # 天乙贵人映射（年干/日干 → 天乙贵人地支）
    TIAN_YI_MAP = {
        '甲': '丑', '乙': '子', '丙': '亥', '丁': '酉',
        '戊': '未', '己': '申', '庚': '午', '辛': '巳',
        '壬': '卯', '癸': '寅'
    }
    
    # 文昌映射（年干/日干 → 文昌地支）
    WEN_CHANG_MAP = {
        '甲': '巳', '乙': '午', '丙': '申', '丁': '酉',
        '戊': '申', '己': '酉', '庚': '亥', '辛': '子',
        '壬': '寅', '癸': '卯'
    }
    
    # 桃花映射（年支/日支 → 桃花地支）
    PEACH_BLOSSOM_MAP = {
        frozenset(['寅', '午', '戌']): '卯',
        frozenset(['申', '子', '辰']): '酉',
        frozenset(['巳', '酉', '丑']): '午',
        frozenset(['亥', '卯', '未']): '子'
    }
    
    # 驿马映射（年支/日支 → 驿马地支）
    POST_HORSE_MAP = {
        frozenset(['寅', '午', '戌']): '申',
        frozenset(['申', '子', '辰']): '寅',
        frozenset(['巳', '酉', '丑']): '亥',
        frozenset(['亥', '卯', '未']): '巳'
    }
    
    # 场强修正系数
    TIAN_YI_ENTROPY_DAMPING = 0.1  # 天乙贵人：熵衰减 10%
    WEN_CHANG_SNR_BOOST = 0.15     # 文昌：信噪比提升 15%
    PEACH_BLOSSOM_BINDING_BOOST = 0.2  # 桃花：绑定能提升 20%
    POST_HORSE_KINETIC_IMPULSE = 0.25  # 驿马：动能冲量 25%
    
    def __init__(self):
        """初始化星辰相干引擎"""
        pass
    
    def detect_stellar_nodes(
        self,
        pillars: List[str]
    ) -> Dict[str, List[str]]:
        """
        [V13.7] 检测神煞节点
        
        Args:
            pillars: 四柱列表
        
        Returns:
            包含各种神煞节点的字典
        """
        if len(pillars) < 4:
            return {
                "tian_yi": [],
                "wen_chang": [],
                "peach_blossom": [],
                "post_horse": []
            }
        
        year_pillar = pillars[0]
        day_pillar = pillars[2]
        
        year_stem = year_pillar[0] if len(year_pillar) > 0 else ""
        day_stem = day_pillar[0] if len(day_pillar) > 0 else ""
        year_branch = year_pillar[1] if len(year_pillar) > 1 else ""
        day_branch = day_pillar[1] if len(day_pillar) > 1 else ""
        
        all_branches = [p[1] for p in pillars if len(p) > 1]
        
        # 检测天乙贵人
        tian_yi_nodes = []
        for stem in [year_stem, day_stem]:
            if stem in self.TIAN_YI_MAP:
                tian_yi_branch = self.TIAN_YI_MAP[stem]
                if tian_yi_branch in all_branches:
                    tian_yi_nodes.append(tian_yi_branch)
        
        # 检测文昌
        wen_chang_nodes = []
        for stem in [year_stem, day_stem]:
            if stem in self.WEN_CHANG_MAP:
                wen_chang_branch = self.WEN_CHANG_MAP[stem]
                if wen_chang_branch in all_branches:
                    wen_chang_nodes.append(wen_chang_branch)
        
        # 检测桃花
        peach_blossom_nodes = []
        for branch in [year_branch, day_branch]:
            for triad, peach in self.PEACH_BLOSSOM_MAP.items():
                if branch in triad:
                    if peach in all_branches:
                        peach_blossom_nodes.append(peach)
                    break
        
        # 检测驿马
        post_horse_nodes = []
        for branch in [year_branch, day_branch]:
            for triad, horse in self.POST_HORSE_MAP.items():
                if branch in triad:
                    if horse in all_branches:
                        post_horse_nodes.append(horse)
                    break
        
        return {
            "tian_yi": list(set(tian_yi_nodes)),
            "wen_chang": list(set(wen_chang_nodes)),
            "peach_blossom": list(set(peach_blossom_nodes)),
            "post_horse": list(set(post_horse_nodes))
        }
    
    def calculate_entropy_damping(
        self,
        stellar_nodes: Dict[str, List[str]],
        base_entropy: float
    ) -> float:
        """
        [V13.7] 计算熵衰减（天乙贵人）
        
        公式：S_new = S_old * (1 - entropy_damping)
        
        Args:
            stellar_nodes: 神煞节点字典
            base_entropy: 基础熵值
        
        Returns:
            修正后的熵值
        """
        tian_yi_count = len(stellar_nodes.get("tian_yi", []))
        if tian_yi_count == 0:
            return base_entropy
        
        # 每个天乙贵人衰减 10%
        total_damping = self.TIAN_YI_ENTROPY_DAMPING * tian_yi_count
        # 限制最大衰减为 50%
        total_damping = min(total_damping, 0.5)
        
        entropy_damped = base_entropy * (1.0 - total_damping)
        return entropy_damped
    
    def calculate_snr_boost(
        self,
        stellar_nodes: Dict[str, List[str]],
        base_snr: float
    ) -> float:
        """
        [V13.7] 计算信噪比提升（文昌）
        
        公式：SNR_new = SNR_old * (1 + SNR_boost)
        
        Args:
            stellar_nodes: 神煞节点字典
            base_snr: 基础信噪比
        
        Returns:
            修正后的信噪比
        """
        wen_chang_count = len(stellar_nodes.get("wen_chang", []))
        if wen_chang_count == 0:
            return base_snr
        
        # 每个文昌提升 15%
        total_boost = self.WEN_CHANG_SNR_BOOST * wen_chang_count
        # 限制最大提升为 100%
        total_boost = min(total_boost, 1.0)
        
        snr_boosted = base_snr * (1.0 + total_boost)
        return snr_boosted
    
    def calculate_quantum_attraction(
        self,
        stellar_nodes: Dict[str, List[str]],
        base_binding_energy: float
    ) -> float:
        """
        [V13.7] 计算量子引力（桃花）
        
        公式：E_new = E_old * (1 + binding_boost)
        
        Args:
            stellar_nodes: 神煞节点字典
            base_binding_energy: 基础绑定能
        
        Returns:
            修正后的绑定能
        """
        peach_count = len(stellar_nodes.get("peach_blossom", []))
        if peach_count == 0:
            return base_binding_energy
        
        # 每个桃花提升 20%
        total_boost = self.PEACH_BLOSSOM_BINDING_BOOST * peach_count
        # 限制最大提升为 100%
        total_boost = min(total_boost, 1.0)
        
        binding_boosted = base_binding_energy * (1.0 + total_boost)
        return binding_boosted
    
    def calculate_kinetic_impulse(
        self,
        stellar_nodes: Dict[str, List[str]],
        base_velocity: float
    ) -> float:
        """
        [V13.7] 计算动能冲量（驿马）
        
        公式：v_new = v_old * (1 + kinetic_impulse)
        
        Args:
            stellar_nodes: 神煞节点字典
            base_velocity: 基础速度
        
        Returns:
            修正后的速度
        """
        post_horse_count = len(stellar_nodes.get("post_horse", []))
        if post_horse_count == 0:
            return base_velocity
        
        # 每个驿马提升 25%
        total_impulse = self.POST_HORSE_KINETIC_IMPULSE * post_horse_count
        # 限制最大提升为 100%
        total_impulse = min(total_impulse, 1.0)
        
        velocity_boosted = base_velocity * (1.0 + total_impulse)
        return velocity_boosted
    
    def analyze_stellar_coherence(
        self,
        pillars: List[str],
        base_entropy: float = 1.0,
        base_snr: float = 1.0,
        base_binding_energy: float = 1.0,
        base_velocity: float = 1.0,
        influence_bus: Optional[InfluenceBus] = None
    ) -> Dict[str, Any]:
        """
        [V13.7 物理化升级] 分析星辰相干（神煞场强修正）
        
        核心功能：
        1. 天乙贵人：熵衰减 10%
        2. 文昌：信噪比提升 15%
        3. 桃花：量子引力增强
        4. 驿马：动能冲量
        
        Args:
            pillars: 四柱列表
            base_entropy: 基础熵值
            base_snr: 基础信噪比
            base_binding_energy: 基础绑定能
            base_velocity: 基础速度
            influence_bus: InfluenceBus 实例
        
        Returns:
            包含神煞修正信息的字典
        """
        # 1. 检测神煞节点
        stellar_nodes = self.detect_stellar_nodes(pillars)
        
        # 2. 计算熵衰减（天乙贵人）
        entropy_damped = self.calculate_entropy_damping(
            stellar_nodes=stellar_nodes,
            base_entropy=base_entropy
        )
        
        # 3. 计算信噪比提升（文昌）
        snr_boosted = self.calculate_snr_boost(
            stellar_nodes=stellar_nodes,
            base_snr=base_snr
        )
        
        # 4. 计算量子引力（桃花）
        binding_boosted = self.calculate_quantum_attraction(
            stellar_nodes=stellar_nodes,
            base_binding_energy=base_binding_energy
        )
        
        # 5. 计算动能冲量（驿马）
        velocity_boosted = self.calculate_kinetic_impulse(
            stellar_nodes=stellar_nodes,
            base_velocity=base_velocity
        )
        
        return {
            "Stellar_Nodes": stellar_nodes,
            "Metrics": {
                "Base_Entropy": round(base_entropy, 4),
                "Damped_Entropy": round(entropy_damped, 4),
                "Entropy_Damping": round((base_entropy - entropy_damped) / base_entropy if base_entropy > 0 else 0.0, 4),
                "Base_SNR": round(base_snr, 4),
                "Boosted_SNR": round(snr_boosted, 4),
                "SNR_Boost": round((snr_boosted - base_snr) / base_snr if base_snr > 0 else 0.0, 4),
                "Base_Binding_Energy": round(base_binding_energy, 4),
                "Boosted_Binding_Energy": round(binding_boosted, 4),
                "Binding_Boost": round((binding_boosted - base_binding_energy) / base_binding_energy if base_binding_energy > 0 else 0.0, 4),
                "Base_Velocity": round(base_velocity, 4),
                "Boosted_Velocity": round(velocity_boosted, 4),
                "Kinetic_Impulse": round((velocity_boosted - base_velocity) / base_velocity if base_velocity > 0 else 0.0, 4)
            }
        }

