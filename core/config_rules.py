"""
[Antigravity V6.0] 核心算法参数配置表 (Tuned Edition)
====================================================
基于 Steve Jobs (2011) 和 Jack Ma (2014) 真实案例调优。
作为"算法宪法"，本文件是所有子引擎的单一真理源 (Single Source of Truth)。

使用方法:
    from core.config_rules import SCORE_SKULL_CRASH, ENERGY_THRESHOLD_STRONG
"""

# =========================================
# 1. 能量阈值 (Energy Thresholds)
# =========================================
ENERGY_THRESHOLD_STRONG = 3.5  # 身旺线 (触发 🏆)
ENERGY_THRESHOLD_WEAK = 2.0    # 身弱线 (触发 ⚠️)
MONTH_WEIGHT_MULTIPLIER = 2.0  # 月令权重


# =========================================
# 2. 评分权重 (Scoring Weights)
# =========================================

# [Skull Layer] 乔布斯去世案例调优
# 触发丑未戌三刑时的强制熔断分
SCORE_SKULL_CRASH = -50.0

# [Treasury Layer] 马云 IPO 案例调优
# 身强冲开财库 (暴富)
SCORE_TREASURY_BONUS = 20.0

# [Safety Valve] 伦理风控调优
# 身弱冲开财库 (由吉转凶)
SCORE_TREASURY_PENALTY = -20.0

# 普通杂气库开启
SCORE_GENERAL_OPEN = 5.0

# [Base Layer] 基础交互
SCORE_INTERACTION_BONUS = 5.0    # 干支相生
SCORE_INTERACTION_PENALTY = -5.0 # 盖头截脚


# =========================================
# 3. 结构定义
# =========================================
EARTH_PUNISHMENT_SET = {'丑', '未', '戌'}

WEALTH_MAP = {
    'Wood': 'Earth',
    'Fire': 'Metal',
    'Earth': 'Water',
    'Metal': 'Wood',
    'Water': 'Fire'
}

TOMB_ELEMENTS = {
    '辰': 'Water',
    '戌': 'Fire',
    '丑': 'Metal',
    '未': 'Wood'
}


# =========================================
# 4. 默认配置字典 (供 QuantumEngine 使用)
# =========================================
DEFAULT_CONFIG = {
    # Energy Thresholds
    'energy_threshold_strong': ENERGY_THRESHOLD_STRONG,
    'energy_threshold_weak': ENERGY_THRESHOLD_WEAK,
    'month_weight_multiplier': MONTH_WEIGHT_MULTIPLIER,
    
    # Scoring Weights
    'score_skull_crash': SCORE_SKULL_CRASH,
    'score_treasury_bonus': SCORE_TREASURY_BONUS,
    'score_treasury_penalty': SCORE_TREASURY_PENALTY,
    'score_general_open': SCORE_GENERAL_OPEN,
    'score_interaction_bonus': SCORE_INTERACTION_BONUS,
    'score_interaction_penalty': SCORE_INTERACTION_PENALTY,
    
    # Structural Definitions
    'earth_punishment_set': EARTH_PUNISHMENT_SET,
    'wealth_map': WEALTH_MAP,
    'tomb_elements': TOMB_ELEMENTS,
}
