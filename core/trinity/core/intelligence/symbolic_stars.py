
"""
Phase B: Symbolic Stars Engine (Shen Sha as Physics)
====================================================
Translates traditional 'Symbolic Stars' into physical field modifiers.
- Tian Yi (天乙): Entropy Damper (S-Damping)
- Wen Chang (文昌): SNR Booster (Signal Clarity)
- Lu (禄): Energy Anchor (Base Score Boost)
- Yang Ren (羊刃): Criticality Trigger (Phase Transition)
"""

from typing import List, Dict, Set, Any

class SymbolicStarsEngine:
    
    # Mapping definitions
    TIAN_YI_MAP = {
        '甲': ['丑', '未'], '戊': ['丑', '未'], '庚': ['丑', '未'],
        '乙': ['子', '申'], '己': ['子', '申'],
        '丙': ['亥', '酉'], '丁': ['亥', '酉'],
        '壬': ['卯', '巳'], '癸': ['卯', '巳'],
        '辛': ['午', '寅']
    }
    
    WEN_CHANG_MAP = {
        '甲': '巳', '乙': '午', '丙': '申', '丁': '酉', '戊': '申', '己': '酉',
        '庚': '亥', '辛': '子', '壬': '寅', '癸': '卯'
    }
    
    LU_MAP = {
        '甲': '寅', '乙': '卯', '丙': '巳', '丁': '午', '戊': '巳', '己': '午',
        '庚': '申', '辛': '酉', '壬': '亥', '癸': '子'
    }
    
    YANG_REN_MAP = {
        '甲': '卯', '丙': '午', '戊': '午', '庚': '酉', '壬': '子',
        '乙': '辰', '丁': '未', '己': '未', '辛': '戌', '癸': '丑'
    }

    @classmethod
    def analyze_stars(cls, day_master: str, branches: List[str]) -> Dict[str, Any]:
        """
        Identifies active symbolic stars and identifies their physical modifiers.
        """
        stats = {
            'tian_yi_count': 0,
            'wen_chang_count': 0,
            'lu_count': 0,
            'yang_ren_count': 0,
            'active_stars': []
        }
        
        # 1. Tian Yi (Stabilizer)
        t_targets = cls.TIAN_YI_MAP.get(day_master, [])
        for b in branches:
            if b in t_targets:
                stats['tian_yi_count'] += 1
                stats['active_stars'].append({'name': '天乙贵人', 'effect': 'ENTROPY_DAMPING', 'node': b})
                
        # 2. Wen Chang (Clarity)
        w_target = cls.WEN_CHANG_MAP.get(day_master)
        for b in branches:
            if b == w_target:
                stats['wen_chang_count'] += 1
                stats['active_stars'].append({'name': '文昌贵人', 'effect': 'SNR_BOOST', 'node': b})
                
        # 3. Lu (Anchor)
        l_target = cls.LU_MAP.get(day_master)
        for b in branches:
            if b == l_target:
                stats['lu_count'] += 1
                stats['active_stars'].append({'name': '禄神', 'effect': 'ENERGY_ANCHOR', 'node': b})
                
        # 4. Yang Ren (Criticality)
        y_target = cls.YANG_REN_MAP.get(day_master)
        for b in branches:
            if b == y_target:
                stats['yang_ren_count'] += 1
                stats['active_stars'].append({'name': '羊刃', 'effect': 'PHASE_TRANSITION_POTENTIAL', 'node': b})
                
        return stats

    @staticmethod
    def get_physical_modifiers(star_stats: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculates the aggregate physical multipliers based on active stars.
        """
        # S-Damping: Each Tian Yi reduces entropy by 10%
        entropy_damping = 0.9 ** star_stats['tian_yi_count']
        
        # SNR Booster: Each Wen Chang improves SNR by 15%
        snr_boost = 1.0 + (0.15 * star_stats['wen_chang_count'])
        
        # Lu Gain: 1.25x per Lu node
        lu_gain = 1.25 if star_stats['lu_count'] > 0 else 1.0
        
        return {
            'entropy_damping': round(entropy_damping, 3),
            'snr_boost': round(snr_boost, 3),
            'lu_gain': lu_gain
        }
