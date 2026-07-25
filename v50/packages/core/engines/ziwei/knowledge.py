from __future__ import annotations

from core.contracts.base import Topic


TOPIC_PALACE_NAMES: dict[Topic, tuple[str, ...]] = {
    Topic.OVERVIEW: ("命宫", "身宫", "迁移宫", "福德宫"),
    Topic.STRUCTURE: ("命宫", "身宫", "迁移宫", "福德宫"),
    Topic.CAREER: ("官禄宫", "命宫", "迁移宫", "财帛宫"),
    Topic.WEALTH: ("财帛宫", "官禄宫", "田宅宫", "福德宫"),
    Topic.RELATIONSHIP: ("夫妻宫", "命宫", "福德宫"),
    Topic.HEALTH: ("疾厄宫", "福德宫", "命宫"),
    Topic.FAMILY: ("父母宫", "兄弟宫", "田宅宫", "子女宫"),
    Topic.TIMING: ("命宫", "迁移宫", "官禄宫", "财帛宫"),
    Topic.MIGRATION: ("迁移宫", "命宫", "官禄宫", "福德宫"),
    Topic.PORTRAIT: ("命宫", "身宫", "福德宫"),
    Topic.UNKNOWN: ("命宫",),
}

BRANCH_ORDER: tuple[str, ...] = ("寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑")

PALACE_SEQUENCE: tuple[str, ...] = (
    "命宫",
    "兄弟宫",
    "夫妻宫",
    "子女宫",
    "财帛宫",
    "疾厄宫",
    "迁移宫",
    "交友宫",
    "官禄宫",
    "田宅宫",
    "福德宫",
    "父母宫",
)

MAJOR_STARS_14: tuple[str, ...] = (
    "紫微",
    "天机",
    "太阳",
    "武曲",
    "天同",
    "廉贞",
    "天府",
    "太阴",
    "贪狼",
    "巨门",
    "天相",
    "天梁",
    "七杀",
    "破军",
)

BASIC_SUPPORT_STARS: tuple[str, ...] = ("左辅", "右弼", "文昌", "文曲")

BASIC_MALEFIC_STARS: tuple[str, ...] = ("擎羊", "陀罗", "火星", "铃星")

FOUR_TRANSFORMATION_BY_YEAR_STEM: dict[str, dict[str, str]] = {
    "甲": {"禄": "廉贞", "权": "破军", "科": "武曲", "忌": "太阳"},
    "乙": {"禄": "天机", "权": "天梁", "科": "紫微", "忌": "太阴"},
    "丙": {"禄": "天同", "权": "天机", "科": "文昌", "忌": "廉贞"},
    "丁": {"禄": "太阴", "权": "天同", "科": "天机", "忌": "巨门"},
    "戊": {"禄": "贪狼", "权": "太阴", "科": "右弼", "忌": "天机"},
    "己": {"禄": "武曲", "权": "贪狼", "科": "天梁", "忌": "文曲"},
    "庚": {"禄": "太阳", "权": "武曲", "科": "太阴", "忌": "天同"},
    "辛": {"禄": "巨门", "权": "太阳", "科": "文曲", "忌": "文昌"},
    "壬": {"禄": "天梁", "权": "紫微", "科": "左辅", "忌": "武曲"},
    "癸": {"禄": "破军", "权": "巨门", "科": "太阴", "忌": "贪狼"},
}


FOUR_TRANSFORMATION_MEANINGS: dict[str, str] = {
    "禄": "opportunity",
    "权": "activation",
    "科": "reputation",
    "忌": "pressure",
}


def canonical_palace_name(name: str) -> str:
    stripped = name.strip()
    if not stripped:
        return ""
    return stripped if stripped.endswith("宫") else f"{stripped}宫"
