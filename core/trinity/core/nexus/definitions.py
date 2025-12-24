
"""
Quantum Trinity V2.0: Nexus Definitions
=======================================
Single Source of Truth for Bazi Physics Constants and Rules.
"""

import numpy as np
from typing import Dict, List, Tuple, Set

class PhysicsConstants:
    # 1. Five Elements & Phases (Phasor Angles)
    ELEMENT_PHASES = {
        "Wood": 0.0,
        "Fire": 1.2566,  # 2π/5
        "Earth": 2.5133, # 4π/5
        "Metal": 3.7699, # 6π/5
        "Water": 5.0265  # 8π/5
    }
    
    # 2. Cycles (State Transitions)
    GENERATION = {"Wood": "Fire", "Fire": "Earth", "Earth": "Metal", "Metal": "Water", "Water": "Wood"}
    CONTROL = {"Wood": "Earth", "Earth": "Water", "Water": "Fire", "Fire": "Metal", "Metal": "Wood"}
    
    # 3. Structural Thresholds
    LOCKING_RATIO_CRITICAL = 2.0
    SYNC_THRESHOLD_COHERENT = 0.85
    SNR_THRESHOLD_BEATING = 0.4
    BRITTLENESS_COEFF = 0.85
    CRITICAL_IMPEDANCE_RATIO = 4.2 # Z_ratio for Total Internal Reflection
    
    # 4. Phase 28: Oppose Dynamics (Shang Guan vs Zheng Guan)
    ANNIHILATION_THRESHOLD = 0.12  # Below this sync, system enters annihilation
    RADIATION_SENSITIVITY = 1.8   # Multiplier for Shang Guan penetration
    EXPOSED_BOOST_COEFF = 2.5     # Power boost when透干
    ORDER_COLLAPSE_LIMIT = 0.15     # Critical order parameter for structural failure
    
    # 6. Seasonal Multipliers (Wang Shuai Xiu Qiu Si)
    # Rows: Spring, Summer, Autumn, Winter, Earth-Month (End of seasons)
    SEASONAL_MATRIX = {
        '寅': {'Wood': 1.5, 'Fire': 1.2, 'Earth': 0.5, 'Metal': 0.4, 'Water': 0.8},
        '卯': {'Wood': 1.8, 'Fire': 1.2, 'Earth': 0.4, 'Metal': 0.3, 'Water': 0.7},
        '辰': {'Wood': 1.1, 'Fire': 0.8, 'Earth': 1.5, 'Metal': 1.1, 'Water': 1.0},
        '巳': {'Wood': 0.8, 'Fire': 1.5, 'Earth': 1.2, 'Metal': 0.5, 'Water': 0.4},
        '午': {'Wood': 0.7, 'Fire': 1.8, 'Earth': 1.2, 'Metal': 0.4, 'Water': 0.3},
        '未': {'Wood': 1.0, 'Fire': 1.1, 'Earth': 1.5, 'Metal': 0.8, 'Water': 0.6},
        '申': {'Wood': 0.4, 'Fire': 0.5, 'Earth': 0.8, 'Metal': 1.5, 'Water': 1.2},
        '酉': {'Wood': 0.3, 'Fire': 0.4, 'Earth': 0.7, 'Metal': 1.8, 'Water': 1.2},
        '戌': {'Wood': 0.6, 'Fire': 1.0, 'Earth': 1.5, 'Metal': 1.1, 'Water': 0.8},
        '亥': {'Wood': 1.2, 'Fire': 0.4, 'Earth': 0.4, 'Metal': 0.8, 'Water': 1.5},
        '子': {'Wood': 1.2, 'Fire': 0.3, 'Earth': 0.3, 'Metal': 0.7, 'Water': 1.8},
        '丑': {'Wood': 0.8, 'Fire': 0.6, 'Earth': 1.5, 'Metal': 1.0, 'Water': 1.1},
    }

    PILLAR_WEIGHTS = {'year': 0.5, 'month': 3.0, 'day': 1.0, 'hour': 0.8, 'luck': 1.2, 'annual': 1.5}
    BASE_SCORE = 5.0  

class BaziParticleNexus:
    # Stems: (Element, Polarity, HetuNumber)
    STEMS = {
        "甲": ("Wood", "Yang", 1), "乙": ("Wood", "Yin", 2),
        "丙": ("Fire", "Yang", 3), "丁": ("Fire", "Yin", 4),
        "戊": ("Earth", "Yang", 5), "己": ("Earth", "Yin", 6),
        "庚": ("Metal", "Yang", 7), "辛": ("Metal", "Yin", 8),
        "壬": ("Water", "Yang", 9), "癸": ("Water", "Yin", 10)
    }
    
    STEM_SHI_SHEN = ["比肩", "劫财", "食神", "伤官", "偏财", "正财", "七杀", "正官", "偏印", "正印"]

    @classmethod
    def get_shi_shen(cls, stem: str, dm_stem: str) -> str:
        """
        Calculates the Ten God (Shi Shen) label for a target stem relative to a Day Master.
        """
        if stem not in cls.STEMS or dm_stem not in cls.STEMS:
            return "Unknown"
        
        from .definitions import PhysicsConstants
        target_elem, target_pol, _ = cls.STEMS[stem]
        dm_elem, dm_pol, _ = cls.STEMS[dm_stem]
        
        if target_elem == dm_elem:
            return "比肩" if target_pol == dm_pol else "劫财"
        if PhysicsConstants.GENERATION[dm_elem] == target_elem:
            return "食神" if target_pol == dm_pol else "伤官"
        if PhysicsConstants.GENERATION[target_elem] == dm_elem:
            return "偏印" if target_pol == dm_pol else "正印"
        if PhysicsConstants.CONTROL[dm_elem] == target_elem:
            return "偏财" if target_pol == dm_pol else "正财"
        if PhysicsConstants.CONTROL[target_elem] == dm_elem:
            return "七杀" if target_pol == dm_pol else "正官"
        return "未知"
    @classmethod
    def get_branch_weights(cls, branch: str) -> List[Tuple[str, int]]:
        """
        Returns the hidden stems and their weights for a given branch.
        """
        if branch not in cls.BRANCHES:
            return []
        return cls.BRANCHES[branch][2] # Index 2 is hidden stems list
    # Combined Registry Hidden Stems - STATIC WEIGHTS (legacy)
    BRANCHES = {
        "子": ("Water", 0, [('癸', 10)]),
        "丑": ("Earth", 30, [('己', 5), ('癸', 3), ('辛', 2)]),
        "寅": ("Wood", 60, [('甲', 5), ('丙', 3), ('戊', 2)]),
        "卯": ("Wood", 90, [('乙', 10)]),
        "辰": ("Earth", 120, [('戊', 5), ('乙', 3), ('癸', 2)]),
        "巳": ("Fire", 150, [('丙', 5), ('戊', 3), ('庚', 2)]),
        "午": ("Fire", 180, [('丁', 7), ('己', 3)]),
        "未": ("Earth", 210, [('己', 5), ('丁', 3), ('乙', 2)]),
        "申": ("Metal", 240, [('庚', 5), ('壬', 3), ('戊', 2)]),
        "酉": ("Metal", 270, [('辛', 10)]),
        "戌": ("Earth", 300, [('戊', 5), ('辛', 3), ('丁', 2)]),
        "亥": ("Water", 330, [('壬', 7), ('甲', 3)])
    }
    
    # [Phase B] Dynamic weight accessor
    @classmethod
    def get_branch_weights(cls, branch: str, phase_progress: float = None, 
                           dispersion_engine=None) -> list:
        """
        Get hidden stem weights for a branch - static or dynamic.
        
        Args:
            branch: The branch character (e.g., '丑')
            phase_progress: Solar term progress (0.0-1.0), None for static
            dispersion_engine: QuantumDispersionEngine instance for dynamic mode
        
        Returns:
            list: [(stem, weight), ...] 
        """
        if phase_progress is not None and dispersion_engine is not None:
            # Dynamic mode: use quantum dispersion
            dynamic_weights = dispersion_engine.get_dynamic_weights(branch, phase_progress)
            return [(stem, weight) for stem, weight in dynamic_weights.items()]
        
        # Static mode: fallback to traditional weights
        branch_data = cls.BRANCHES.get(branch)
        if branch_data:
            return branch_data[2]
        return []

    # Phase 32: Structural Interactions (Harm/Penalty)
    # 6 Harms (Liu Hai) - Phase Jitter Sources
    HARM_MAPPING = {
        '子': '未', '未': '子', # Rat - Goat
        '丑': '午', '午': '丑', # Ox - Horse
        '寅': '巳', '巳': '寅', # Tiger - Snake
        '卯': '辰', '辰': '卯', # Rabbit - Dragon
        '申': '亥', '亥': '申', # Monkey - Pig
        '酉': '戌', '戌': '酉'  # Rooster - Dog
    }

    # Penalties (San Xing) - Shear Stress Sources
    # Format: Trigger Branch -> Components required for full activation
    PENALTY_GROUPS = {
        '寅': {'components': ['巳', '申'], 'type': '无恩之刑'},
        '巳': {'components': ['寅', '申'], 'type': '无恩之刑'},
        '申': {'components': ['寅', '巳'], 'type': '无恩之刑'},
        
        '丑': {'components': ['未', '戌'], 'type': '恃势之刑'},
        '未': {'components': ['丑', '戌'], 'type': '恃势之刑'},
        '戌': {'components': ['丑', '未'], 'type': '恃势之刑'},
        
        '子': {'components': ['卯'], 'type': '无礼之刑'},
        '卯': {'components': ['子'], 'type': '无礼之刑'},
        
        '辰': {'components': ['辰'], 'type': '自刑'},
        '午': {'components': ['午'], 'type': '自刑'},
        '酉': {'components': ['酉'], 'type': '自刑'},
        '亥': {'components': ['亥'], 'type': '自刑'}
    }


    # Remediation Particles (Prescriptions)
    REMEDY_PARTICLES = {
        "甲": {"type": "能量药剂", "effect": "共振增强"},
        "乙": {"type": "草本修复", "effect": "相位稳定"},
        "丙": {"type": "光子脉冲", "effect": "结构激发"},
        "丁": {"type": "激光引导", "effect": "精准手术"},
        "戊": {"type": "重力护盾", "effect": "因果熵阻尼"},
        "己": {"type": "量子过滤器", "effect": "杂质俘获"},
        "庚": {"type": "星际切片", "effect": "模式解耦"},
        "辛": {"type": "微观探针", "effect": "连通性分析"},
        "壬": {"type": "冷却介质", "effect": "热寂衰减"},
        "癸": {"type": "通用溶剂", "effect": "晶格溶解"}
    }
    
    REMEDY_DESC = {
        "甲": "🌿 [甲] 能量药剂: 增强系统共振相干性。",
        "乙": "🍀 [乙] 草本修复: 稳定相位波动与抖动。",
        "丙": "🔥 [丙] 光子脉冲: 激发结构弱节点能量。",
        "丁": "🕯️ [丁] 激光引导: 精准调整结构缺陷。",
        "戊": "🏔️ [戊] 重力护盾: 压制异常的因果熵增。",
        "己": "⏳ [己] 量子过滤器: 捕捉场中的能量杂质。",
        "庚": "⚔️ [庚] 星际切片: 解除僵化的规则模式。",
        "辛": "💎 [辛] 微观探针: 分析能量连通性盲点。",
        "壬": "🌊 [壬] 冷却介质: 降低场强度过高的节点。",
        "癸": "💧 [癸] 通用溶剂: 溶解因果晶格中的阻塞。"
    }

class ArbitrationNexus:
    """Standardized Bazi interaction rules and their physical Q values."""
    
    # 1. Priority Table (Lower Number = Higher Priority)
    PRIORITY = {
        "SAN_HUI": 1,
        "SAN_HE": 2,
        "LIU_HE": 3,
        "CLASH": 4,
        "HARMONY": 5, # Semi-combines
        "HARM": 6,
        "PUNISHMENT": 7,
        "RESONANCE": 8,
        "OPPOSE": 0,  # Phase 28: Highest priority for annihilation events
        "CAPTURE": 2, # Shishen vs Qisha (Force Neutralization)
        "CUTTING": 1, # Xiao Shen Duo Shi (System Critical)
        "CONTAMINATION": 3 # Cai Xing Huai Yin (Medium Priority)
    }

    # 2. Static Interaction Maps
    SAN_HUI = {
        frozenset({'寅', '卯', '辰'}): 'Wood',
        frozenset({'巳', '午', '未'}): 'Fire',
        frozenset({'申', '酉', '戌'}): 'Metal',
        frozenset({'亥', '子', '丑'}): 'Water',
    }

    SAN_HE = {
        frozenset({'申', '子', '辰'}): 'Water',
        frozenset({'亥', '卯', '未'}): 'Wood',
        frozenset({'寅', '午', '戌'}): 'Fire',
        frozenset({'巳', '酉', '丑'}): 'Metal',
    }

    LIU_HE = {
        frozenset({'子', '丑'}): 'Earth', frozenset({'寅', '亥'}): 'Wood',
        frozenset({'卯', '戌'}): 'Fire', frozenset({'辰', '酉'}): 'Metal',
        frozenset({'巳', '申'}): 'Water', frozenset({'午', '未'}): 'Earth',
    }

    CLASH_MAP = {
        '子': '午', '午': '子', '丑': '未', '未': '丑', '寅': '申', '申': '寅', 
        '卯': '酉', '酉': '卯', '辰': '戌', '戌': '辰', '巳': '亥', '亥': '巳'
    }

    PUNISHMENT_THREE = [
        frozenset(['寅', '巳', '申']),
        frozenset(['丑', '戌', '未'])
    ]
    
    SELF_PUNISHMENT = {'辰', '午', '酉', '亥'}

    HARM_MAP = {
        '子': '未', '未': '子', '丑': '午', '午': '丑', '寅': '巳', '巳': '寅',
        '卯': '辰', '辰': '卯', '申': '亥', '亥': '申', '酉': '戌', '戌': '酉'
    }

    # 3. Dynamic Q (Resonance Multiplier) & Phase Shift (Radians)
    DYNAMICS = {
        "SAN_HUI": {"q": 3.0, "phi": 0.0, "lock": True},
        "SAN_HE": {"q": 2.5, "phi": 0.0, "lock": True},
        "LIU_HE": {"q": 1.8, "phi": 0.15, "lock": True},
        "CLASH": {"q": 0.6, "phi": 2.827, "lock": False}, # ~162 deg (Clash)
        "RESONANCE": {"q": 1.2, "phi": 0.0, "lock": False},
        "OPPOSE": {"q": 0.05, "phi": 3.14159, "lock": False},
        "CAPTURE": {"q": 1.5, "phi": 0.5, "lock": True},
        "CUTTING": {"q": 0.3, "phi": 2.2, "lock": False},
        "CONTAMINATION": {"q": 0.7, "phi": 1.2, "lock": False},
        "HARM": {"q": 0.4, "phi": 2.5, "lock": False},
        "PUNISHMENT": {"q": 0.35, "phi": 2.7, "lock": False}
    }
