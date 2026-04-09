"""Static physics rules and pure helper functions."""
from __future__ import annotations

from typing import Dict, Tuple

DEFAULT_POSITION_WEIGHTS: Dict[str, float] = {
    "year": 0.20,
    "month": 0.45,
    "day": 0.25,
    "hour": 0.10,
}

DEFAULT_INTERACTION_PARAMS: Dict[str, float] = {
    "root_decay_lambda": 0.7,
    "through_stem_boost": 1.05,
    "conflict_penalty_gamma": 0.12,
    "EFF_PROMOTING": 1.2,
    "EFF_PROMOTING_SAME": 1.2,
    "EFF_PROMOTING_DIFF": 1.2,
    "EFF_EXHAUSTING": 0.8,
    "EFF_EXHAUSTING_SAME": 0.8,
    "EFF_EXHAUSTING_DIFF": 0.8,
    "EFF_RESTRAINING": 0.6,
    "EFF_RESTRAINING_SAME": 0.6,
    "EFF_RESTRAINING_DIFF": 0.6,
    "EFF_CONSUMING": 0.9,
    "EFF_CONSUMING_SAME": 0.9,
    "EFF_CONSUMING_DIFF": 0.9,
    "CF_FLOATING_DECAY": 0.1,
    "A_PROTRUSION": 1.0,
    "L1_PUNISH_FRICTION_SANXING": 0.22,
    "L1_PUNISH_FRICTION_ZIXING": 0.18,
    "L1_CLASH_INTENSITY": 1.0,
    "L1_COMBINE_LOCK_RATIO": 0.3,
    "L1_PIERCE_RATIO": 0.45,
    # 1.0：三合聚合节点在 L1 显式 φ=0；若岁运扫描中出现冲及合局支，读参数关闭钳制
    "L1_SANHE_PHI_CLAMP": 1.0,
    "L1_SANHE_PHI_UNLOCK_ON_CLASH": 1.0,
    "ENTROPY_W_TORQUE": 0.4,
    "ENTROPY_W_CLAMP": 0.3,
    "ENTROPY_W_CLASH": 0.3,
    "ENTROPY_TORQUE_REF": 180.0,
    "ENTROPY_CLASH_REF": 160.0,
}

WEIGHT_LUCK = 0.4
WEIGHT_YEAR = 0.2

SOLAR_TERMS = [
    "立春", "雨水", "惊蛰", "春分", "清明", "谷雨",
    "立夏", "小满", "芒种", "夏至", "小暑", "大暑",
    "立秋", "处暑", "白露", "秋分", "寒露", "霜降",
    "立冬", "小雪", "大雪", "冬至", "小寒", "大寒",
]

DEFAULT_SEASONAL_BASE: Dict[str, Dict[str, float]] = {
    "default": {"wood": 1.0, "fire": 1.0, "earth": 1.0, "metal": 1.0, "water": 1.0},
    "spring": {"wood": 1.2, "fire": 1.05, "earth": 0.95, "metal": 0.85, "water": 0.95},
    "summer": {"wood": 1.0, "fire": 1.2, "earth": 1.05, "metal": 0.85, "water": 0.85},
    "autumn": {"wood": 0.85, "fire": 0.9, "earth": 1.0, "metal": 1.2, "water": 1.05},
    "winter": {"wood": 0.9, "fire": 0.8, "earth": 0.95, "metal": 1.05, "water": 1.2},
}

TERM_TO_SEASON = {
    **{k: "spring" for k in SOLAR_TERMS[0:6]},
    **{k: "summer" for k in SOLAR_TERMS[6:12]},
    **{k: "autumn" for k in SOLAR_TERMS[12:18]},
    **{k: "winter" for k in SOLAR_TERMS[18:24]},
}

STEM_TO_ELEMENT = {
    "甲": "wood", "乙": "wood",
    "丙": "fire", "丁": "fire",
    "戊": "earth", "己": "earth",
    "庚": "metal", "辛": "metal",
    "壬": "water", "癸": "water",
}

# 日干之墓支（L1 墓库插件定位用，结构规则非可调系数）
STEM_TOMB_BRANCH: Dict[str, str] = {
    "甲": "未",
    "乙": "未",
    "丙": "戌",
    "丁": "戌",
    "戊": "戌",
    "己": "戌",
    "庚": "丑",
    "辛": "丑",
    "壬": "辰",
    "癸": "辰",
}

# 三合局（全支齐现时标记 AGGREGATED + composite 场强）
SANHE_GROUPS: Tuple[frozenset[str], ...] = (
    frozenset({"寅", "午", "戌"}),
    frozenset({"申", "子", "辰"}),
    frozenset({"亥", "卯", "未"}),
    frozenset({"巳", "酉", "丑"}),
)

# 三刑边（任两支同现于盘中则施加扭力边）
SANXING_EDGES: tuple[tuple[str, str], ...] = (
    ("寅", "巳"),
    ("巳", "申"),
    ("寅", "申"),
    ("丑", "戌"),
    ("戌", "未"),
    ("丑", "未"),
    ("子", "卯"),
)

SELF_PUNISH_BRANCHES: frozenset[str] = frozenset({"辰", "午", "酉", "亥"})

STEM_YIN_YANG = {
    "甲": "yang",
    "乙": "yin",
    "丙": "yang",
    "丁": "yin",
    "戊": "yang",
    "己": "yin",
    "庚": "yang",
    "辛": "yin",
    "壬": "yang",
    "癸": "yin",
}

BRANCH_HIDDEN_STEMS: Dict[str, Dict[str, float]] = {
    "子": {"癸": 100.0},
    "丑": {"己": 60.0, "癸": 30.0, "辛": 10.0},
    "寅": {"甲": 60.0, "丙": 30.0, "戊": 10.0},
    "卯": {"乙": 100.0},
    "辰": {"戊": 60.0, "乙": 20.0, "癸": 20.0},
    "巳": {"丙": 60.0, "戊": 20.0, "庚": 20.0},
    "午": {"丁": 80.0, "己": 20.0},
    "未": {"己": 60.0, "丁": 20.0, "乙": 20.0},
    "申": {"庚": 60.0, "壬": 30.0, "戊": 10.0},
    "酉": {"辛": 100.0},
    "戌": {"戊": 60.0, "辛": 20.0, "丁": 20.0},
    "亥": {"壬": 60.0, "甲": 20.0, "戊": 20.0},
}

TEN_DEITIES = [
    "比肩",
    "劫财",
    "食神",
    "伤官",
    "正财",
    "偏财",
    "正官",
    "七杀",
    "正印",
    "偏印",
]

MONTH_BRANCH_TO_SEASON = {
    "寅": "spring",
    "卯": "spring",
    "辰": "spring",
    "巳": "summer",
    "午": "summer",
    "未": "summer",
    "申": "autumn",
    "酉": "autumn",
    "戌": "autumn",
    "亥": "winter",
    "子": "winter",
    "丑": "winter",
}

ROOT_MAP: Dict[str, set[str]] = {
    "甲": {"寅", "卯", "辰", "未", "亥"},
    "乙": {"寅", "卯", "辰", "未"},
    "丙": {"巳", "午", "寅", "未"},
    "丁": {"巳", "午", "未", "戌"},
    "戊": {"辰", "戌", "丑", "未", "巳", "午"},
    "己": {"辰", "戌", "丑", "未", "午"},
    "庚": {"申", "酉", "戌", "丑"},
    "辛": {"申", "酉", "戌", "丑"},
    "壬": {"亥", "子", "申", "辰"},
    "癸": {"亥", "子", "丑", "辰"},
}

ELEMENT_GENERATES = {
    "wood": "fire",
    "fire": "earth",
    "earth": "metal",
    "metal": "water",
    "water": "wood",
}

ELEMENT_CONTROLS = {
    "wood": "earth",
    "fire": "metal",
    "earth": "water",
    "metal": "wood",
    "water": "fire",
}


def stem_polarity(stem: str) -> str:
    return STEM_YIN_YANG.get(stem, "yang")


def deity_from_self_and_target_stem(*, day_stem: str, target_stem: str) -> str:
    self_element = STEM_TO_ELEMENT.get(day_stem, "earth")
    target_element = STEM_TO_ELEMENT.get(target_stem, "earth")
    day_polarity = stem_polarity(day_stem)
    target_polarity = stem_polarity(target_stem)

    if target_element == self_element:
        return "比肩" if target_polarity == day_polarity else "劫财"
    if ELEMENT_GENERATES.get(self_element) == target_element:
        return "食神" if target_polarity == day_polarity else "伤官"
    if ELEMENT_CONTROLS.get(self_element) == target_element:
        return "偏财" if target_polarity == day_polarity else "正财"
    if ELEMENT_CONTROLS.get(target_element) == self_element:
        return "七杀" if target_polarity == day_polarity else "正官"
    if ELEMENT_GENERATES.get(target_element) == self_element:
        return "偏印" if target_polarity == day_polarity else "正印"
    return "比肩"


def controlled_by(element: str) -> str:
    for source, target in ELEMENT_CONTROLS.items():
        if target == element:
            return source
    return "earth"


def generated_by(element: str) -> str:
    for source, target in ELEMENT_GENERATES.items():
        if target == element:
            return source
    return "earth"


def deity_element_map(self_element: str) -> Dict[str, str]:
    output = ELEMENT_GENERATES[self_element]
    wealth = ELEMENT_CONTROLS[self_element]
    power = controlled_by(self_element)
    support = generated_by(self_element)
    return {
        "比劫": self_element,
        "食伤": output,
        "财星": wealth,
        "官杀": power,
        "印星": support,
    }
