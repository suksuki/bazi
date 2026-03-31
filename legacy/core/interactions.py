
# Interaction Definitions for Bazi Stems and Branches
# Supports identifying He (Combine), Chong (Clash), Xing (Punishment), Hai (Harm)

STEM_COMBINATIONS = {
    "甲": "己", "己": "甲",
    "乙": "庚", "庚": "乙",
    "丙": "辛", "辛": "丙",
    "丁": "壬", "壬": "丁",
    "戊": "癸", "癸": "戊"
}

EARTHLY_BRANCHES = {
    "子": {"element": "water"}, "丑": {"element": "earth"},
    "寅": {"element": "wood"}, "卯": {"element": "wood"},
    "辰": {"element": "earth"}, "巳": {"element": "fire"},
    "午": {"element": "fire"}, "未": {"element": "earth"},
    "申": {"element": "metal"}, "酉": {"element": "metal"},
    "戌": {"element": "earth"}, "亥": {"element": "water"}
}

STEM_CLASHES = {
    "甲": "庚", "庚": "甲",
    "乙": "辛", "辛": "乙",
    "丙": "壬", "壬": "丙",
    "丁": "癸", "癸": "丁"
}

BRANCH_SIX_COMBINES = {
    "子": "丑", "丑": "子",
    "寅": "亥", "亥": "寅",
    "卯": "戌", "戌": "卯",
    "辰": "酉", "酉": "辰",
    "巳": "申", "申": "巳",
    "午": "未", "未": "午"
}

BRANCH_CLASHES = {
    "子": "午", "午": "子",
    "丑": "未", "未": "丑",
    "寅": "申", "申": "寅",
    "卯": "酉", "酉": "卯",
    "辰": "戌", "戌": "辰",
    "巳": "亥", "亥": "巳"
}

BRANCH_HARMS = {
    "子": "未", "未": "子",
    "丑": "午", "午": "丑",
    "寅": "巳", "巳": "寅",
    "卯": "辰", "辰": "卯",
    "申": "亥", "亥": "申",
    "酉": "戌", "戌": "酉"
}

# Punishments are complex; strictly listing pairs that trigger it
BRANCH_PUNISHMENTS = {
    "子": ["卯"], "卯": ["子"], # Rude
    "寅": ["巳", "申"], "巳": ["寅", "申"], "申": ["寅", "巳"], # Fiery Penalty
    "丑": ["未", "戌"], "未": ["丑", "戌"], "戌": ["丑", "未"], # Bullying Penalty
    "辰": ["辰"], "午": ["午"], "酉": ["酉"], "亥": ["亥"] # Self Penalty
}

def get_stem_interaction(s1, s2):
    """Returns 'Combine', 'Clash', or None (ignoring generic Ke)."""
    if STEM_COMBINATIONS.get(s1) == s2:
        return "合 (Combine)"
    if STEM_CLASHES.get(s1) == s2:
        return "冲 (Clash)"
    return None

def get_branch_interaction(b1, b2):
    """Returns highest priority interaction: Combine > Clash > Punishment > Harm."""
    # Priority is often debated, but usually Clash/Combine are most significant modifiers.
    
    interactions = []
    
    if BRANCH_SIX_COMBINES.get(b1) == b2:
        interactions.append("六合 (Combine)")
        
    if BRANCH_CLASHES.get(b1) == b2:
        interactions.append("冲 (Clash)")
        
    if b2 in BRANCH_PUNISHMENTS.get(b1, []):
        interactions.append("刑 (Punish)")
        
    if BRANCH_HARMS.get(b1) == b2:
        interactions.append("害 (Harm)")
        
    return " ".join(interactions) if interactions else None
