from __future__ import annotations

STEMS = ("甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸")
BRANCHES = ("子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥")

ELEMENT_BY_STEM = {
    "甲": "wood",
    "乙": "wood",
    "丙": "fire",
    "丁": "fire",
    "戊": "earth",
    "己": "earth",
    "庚": "metal",
    "辛": "metal",
    "壬": "water",
    "癸": "water",
}

YIN_YANG_BY_STEM = {
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

HIDDEN_STEMS = {
    "子": (("癸", 1.0),),
    "丑": (("己", 0.6), ("癸", 0.25), ("辛", 0.15)),
    "寅": (("甲", 0.6), ("丙", 0.25), ("戊", 0.15)),
    "卯": (("乙", 1.0),),
    "辰": (("戊", 0.6), ("乙", 0.25), ("癸", 0.15)),
    "巳": (("丙", 0.6), ("戊", 0.25), ("庚", 0.15)),
    "午": (("丁", 0.7), ("己", 0.3)),
    "未": (("己", 0.6), ("丁", 0.25), ("乙", 0.15)),
    "申": (("庚", 0.6), ("壬", 0.25), ("戊", 0.15)),
    "酉": (("辛", 1.0),),
    "戌": (("戊", 0.6), ("辛", 0.25), ("丁", 0.15)),
    "亥": (("壬", 0.7), ("甲", 0.3)),
}

GENERATES = {
    "wood": "fire",
    "fire": "earth",
    "earth": "metal",
    "metal": "water",
    "water": "wood",
}

CONTROLS = {
    "wood": "earth",
    "earth": "water",
    "water": "fire",
    "fire": "metal",
    "metal": "wood",
}

BRANCH_CLASH = {("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"), ("辰", "戌"), ("巳", "亥")}
BRANCH_HARM = {("子", "未"), ("丑", "午"), ("寅", "巳"), ("卯", "辰"), ("申", "亥"), ("酉", "戌")}
BRANCH_BREAK = {("子", "酉"), ("丑", "辰"), ("寅", "亥"), ("卯", "午"), ("巳", "申"), ("未", "戌")}
BRANCH_HARMONY = {("子", "丑"), ("寅", "亥"), ("卯", "戌"), ("辰", "酉"), ("巳", "申"), ("午", "未")}
BRANCH_PUNISHMENT = {("子", "卯"), ("寅", "巳"), ("巳", "申"), ("丑", "戌"), ("戌", "未")}

THREE_HARMONY = {
    "water": {"申", "子", "辰"},
    "wood": {"亥", "卯", "未"},
    "fire": {"寅", "午", "戌"},
    "metal": {"巳", "酉", "丑"},
}

THREE_MEETING = {
    "wood": {"寅", "卯", "辰"},
    "fire": {"巳", "午", "未"},
    "metal": {"申", "酉", "戌"},
    "water": {"亥", "子", "丑"},
}

VAULT_BRANCHES = {"辰", "戌", "丑", "未"}
ELEMENTS = ("wood", "fire", "earth", "metal", "water")


def element_of_stem(stem: str) -> str:
    return ELEMENT_BY_STEM.get(stem, "")


def pair_key(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted((left, right), key=BRANCHES.index))  # type: ignore[return-value]
