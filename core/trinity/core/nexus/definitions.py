
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
    
    # 5. Global Weights
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
    
    # Branches: (Element, Angle, HiddenStems[(Stem, Weight)])
    # Combined Registry Hidden Stems
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

    # Remediation Particles (Prescriptions)
    REMEDY_PARTICLES = {
        "甲": {"type": "Medicine", "effect": "Resonance Boost"},
        "乙": {"type": "Herbal", "effect": "Sync Stabilization"},
        "丙": {"type": "Radiation", "effect": "Structural Excitation"},
        "丁": {"type": "Laser", "effect": "Precision Cut"},
        "戊": {"type": "Shield", "effect": "Entropy Damping"},
        "己": {"type": "Filter", "effect": "Impurity Capture"},
        "庚": {"type": "Sword", "effect": "Pattern Decoupling"},
        "辛": {"type": "Probe", "effect": "Connectivity Analysis"},
        "壬": {"type": "Coolant", "effect": "Thermal Decay"},
        "癸": {"type": "Solvent", "effect": "Crystal Dissolution"}
    }
    
    REMEDY_DESC = {
        "甲": "🌿 [甲] Medicine: Boosts coherent resonance.",
        "乙": "🍀 [乙] Herbal: Stabilizes sync fluctuations.",
        "丙": "🔥 [丙] Radiation: Excites structure nodes.",
        "丁": "🕯️ [丁] Laser: Precision structural adjustment.",
        "戊": "🏔️ [戊] Shield: Dampens erratic entropy.",
        "己": "⏳ [己] Filter: Captures field impurities.",
        "庚": "⚔️ [庚] Sword: Decouples rigid patterns.",
        "辛": "💎 [辛] Probe: Analyzes connectivity gaps.",
        "壬": "🌊 [壬] Coolant: Decays excessive heat/fire.",
        "癸": "💧 [癸] Solvent: Dissolves crystalized blocks."
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
        "OPPOSE": 0  # Phase 28: Highest priority for annihilation events
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

    # 3. Dynamic Q (Resonance Multiplier) & Phase Shift (Radians)
    DYNAMICS = {
        "SAN_HUI": {"q": 3.0, "phi": 0.0, "lock": True},
        "SAN_HE": {"q": 2.5, "phi": 0.0, "lock": True},
        "LIU_HE": {"q": 1.8, "phi": 0.15, "lock": True},
        "CLASH": {"q": 0.6, "phi": 2.827, "lock": False}, # ~162 deg (Clash)
        "RESONANCE": {"q": 1.2, "phi": 0.0, "lock": False},
        "OPPOSE": {"q": 0.05, "phi": 3.14159, "lock": False}
    }
