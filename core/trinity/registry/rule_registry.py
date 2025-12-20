"""
Quantum Trinity: Rule Registry (V1.0)
======================================
Centralized management for Bazi rules, scoring constants, and mappings.
Unifies config_rules.py.
"""

from typing import Dict, Set, List

class RuleRegistry:
    """
    Single Source of Truth for Bazi interaction rules and scoring constants.
    """
    # Rule Categories
    CAT_A_SEASONAL = 'A' # Seasonal Potential (Wang/Shuai)
    CAT_B_INTERACTION = 'B' # Geometric Interactions (Hui/He/Chong)
    CAT_C_SPECIAL = 'C' # Special Patterns (Transformation)
    CAT_D_STRUCTURAL = 'D' # Structural (Vaults/Hidden)

    # Energy Thresholds (Legacy scores, preserved for compatibility)
    ENERGY_THRESHOLD_STRONG = 3.5
    ENERGY_THRESHOLD_WEAK = 2.0
    
    # Scoring Constants
    SCORE_SKULL_CRASH = -50.0
    SCORE_TREASURY_BONUS = 20.0
    SCORE_TREASURY_PENALTY = -20.0
    SCORE_GENERAL_OPEN = 5.0
    
    SCORE_SANHE_BONUS = 15.0
    SCORE_LIUHE_BONUS = 5.0
    SCORE_CLASH_PENALTY = -5.0
    
    # Structural Sets
    EARTH_PUNISHMENT_SET: Set[str] = {'丑', '未', '戌'}
    
    # Mappings
    WEALTH_MAP: Dict[str, str] = {
        'Wood': 'Earth', 'Fire': 'Metal', 'Earth': 'Water',
        'Metal': 'Wood', 'Water': 'Fire'
    }
    
    TOMB_ELEMENTS: Dict[str, str] = {
        '辰': 'Water', '戌': 'Fire', '丑': 'Metal', '未': 'Wood'
    }

    STEM_ELEMENTS: Dict[str, str] = {
        '甲': 'Wood', '乙': 'Wood', '丙': 'Fire', '丁': 'Fire', '戊': 'Earth',
        '己': 'Earth', '庚': 'Metal', '辛': 'Metal', '壬': 'Water', '癸': 'Water'
    }

    HIDDEN_STEM_ELEMENTS: Dict[str, List[str]] = {
        '子': ['Water'], '丑': ['Earth', 'Metal', 'Water'], '寅': ['Wood', 'Fire', 'Earth'],
        '卯': ['Wood'], '辰': ['Earth', 'Water', 'Wood'], '巳': ['Fire', 'Earth', 'Metal'],
        '午': ['Fire', 'Earth'], '未': ['Earth', 'Wood', 'Fire'], '申': ['Metal', 'Water', 'Earth'],
        '酉': ['Metal'], '戌': ['Earth', 'Fire', 'Metal'], '亥': ['Water', 'Wood']
    }

    SEASONAL_ELEMENTS: Dict[str, str] = {
        '寅': 'Wood', '卯': 'Wood', '辰': 'Wood',
        '巳': 'Fire', '午': 'Fire', '未': 'Fire',
        '申': 'Metal', '酉': 'Metal', '戌': 'Metal',
        '亥': 'Water', '子': 'Water', '丑': 'Water'
    }

    # --- Interaction Rules (Moved from LogicMatrix) ---
    SAN_HUI: Dict[frozenset, str] = {
        frozenset({'寅', '卯', '辰'}): 'Wood',
        frozenset({'巳', '午', '未'}): 'Fire',
        frozenset({'申', '酉', '戌'}): 'Metal',
        frozenset({'亥', '子', '丑'}): 'Water',
    }

    SAN_HE: Dict[frozenset, str] = {
        frozenset({'申', '子', '辰'}): 'Water',
        frozenset({'亥', '卯', '未'}): 'Wood',
        frozenset({'寅', '午', '戌'}): 'Fire',
        frozenset({'巳', '酉', '丑'}): 'Metal',
    }

    LIU_HE: Dict[frozenset, str] = {
        frozenset({'子', '丑'}): 'Earth', frozenset({'寅', '亥'}): 'Wood',
        frozenset({'卯', '戌'}): 'Fire', frozenset({'辰', '酉'}): 'Metal',
        frozenset({'巳', '申'}): 'Water', frozenset({'午', '未'}): 'Earth',
    }
    
    CLASH_MAP: Dict[str, str] = {
        '子': '午', '午': '子', '丑': '未', '未': '丑', '寅': '申', '申': '寅', 
        '卯': '酉', '酉': '卯', '辰': '戌', '戌': '辰', '巳': '亥', '亥': '巳'
    }

    @classmethod
    def get_rule_config(cls) -> Dict:
        """Return all rules as a configuration dictionary."""
        return {
            'energy_threshold_strong': cls.ENERGY_THRESHOLD_STRONG,
            'energy_threshold_weak': cls.ENERGY_THRESHOLD_WEAK,
            'score_skull_crash': cls.SCORE_SKULL_CRASH,
            'score_treasury_bonus': cls.SCORE_TREASURY_BONUS,
            'score_sanhe_bonus': cls.SCORE_SANHE_BONUS,
            'earth_punishment_set': cls.EARTH_PUNISHMENT_SET,
            'wealth_map': cls.WEALTH_MAP,
            'tomb_elements': cls.TOMB_ELEMENTS
        }
