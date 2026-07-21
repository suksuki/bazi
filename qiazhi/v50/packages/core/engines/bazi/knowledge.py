from __future__ import annotations


STEM_ELEMENTS = {
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

STEM_POLARITY = {
    "甲": "yang",
    "丙": "yang",
    "戊": "yang",
    "庚": "yang",
    "壬": "yang",
    "乙": "yin",
    "丁": "yin",
    "己": "yin",
    "辛": "yin",
    "癸": "yin",
}

BRANCH_ELEMENTS = {
    "子": "water",
    "丑": "earth",
    "寅": "wood",
    "卯": "wood",
    "辰": "earth",
    "巳": "fire",
    "午": "fire",
    "未": "earth",
    "申": "metal",
    "酉": "metal",
    "戌": "earth",
    "亥": "water",
}

BRANCH_POLARITY = {
    "子": "yang",
    "丑": "yin",
    "寅": "yang",
    "卯": "yin",
    "辰": "yang",
    "巳": "yin",
    "午": "yang",
    "未": "yin",
    "申": "yang",
    "酉": "yin",
    "戌": "yang",
    "亥": "yin",
}

HIDDEN_STEMS = {
    "子": ["癸"],
    "丑": ["己", "癸", "辛"],
    "寅": ["甲", "丙", "戊"],
    "卯": ["乙"],
    "辰": ["戊", "乙", "癸"],
    "巳": ["丙", "戊", "庚"],
    "午": ["丁", "己"],
    "未": ["己", "丁", "乙"],
    "申": ["庚", "壬", "戊"],
    "酉": ["辛"],
    "戌": ["戊", "辛", "丁"],
    "亥": ["壬", "甲"],
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

SIX_CLASH = {
    frozenset(("子", "午")),
    frozenset(("丑", "未")),
    frozenset(("寅", "申")),
    frozenset(("卯", "酉")),
    frozenset(("辰", "戌")),
    frozenset(("巳", "亥")),
}

SIX_HARMONY = {
    frozenset(("子", "丑")),
    frozenset(("寅", "亥")),
    frozenset(("卯", "戌")),
    frozenset(("辰", "酉")),
    frozenset(("巳", "申")),
    frozenset(("午", "未")),
}

TRIPLE_HARMONY = {
    frozenset(("申", "子", "辰")): ("shen_zi_chen_water", "water", "子"),
    frozenset(("亥", "卯", "未")): ("hai_mao_wei_wood", "wood", "卯"),
    frozenset(("寅", "午", "戌")): ("yin_wu_xu_fire", "fire", "午"),
    frozenset(("巳", "酉", "丑")): ("si_you_chou_metal", "metal", "酉"),
}

HALF_TRIPLE_HARMONY = {
    frozenset(("申", "子")): ("shen_zi_half_water", "water", "子"),
    frozenset(("子", "辰")): ("zi_chen_half_water", "water", "子"),
    frozenset(("亥", "卯")): ("hai_mao_half_wood", "wood", "卯"),
    frozenset(("卯", "未")): ("mao_wei_half_wood", "wood", "卯"),
    frozenset(("寅", "午")): ("yin_wu_half_fire", "fire", "午"),
    frozenset(("午", "戌")): ("wu_xu_half_fire", "fire", "午"),
    frozenset(("巳", "酉")): ("si_you_half_metal", "metal", "酉"),
    frozenset(("酉", "丑")): ("you_chou_half_metal", "metal", "酉"),
}
