#!/usr/bin/env python3
"""
FDS SOP V6.0：第五梯队（A-41～A-50）L1 物理过滤器
==================================================
- A-41 壬骑龙背：壬辰日，支多辰/寅，忌见戌冲。
- A-42 归禄格：日禄归时，时柱不见官杀。
- A-43 拱禄格：日时虚拱禄位（丁巳丙午、戊辰己巳等）。
- A-44 杂气财官：辰戌丑未月令，天干透财官。
- A-45 胞胎格：庚寅、甲申等日生于绝地。
"""
from __future__ import annotations

from typing import Any, Dict, List

from pattern_scanner_v57 import _bazi_to_pillars, LU_DI_ZHI

# 日干 → 官杀天干（正官、七杀）
DAY_TO_OFFICER_STEMS = {
    "甲": {"庚", "辛"}, "乙": {"辛", "庚"}, "丙": {"壬", "癸"}, "丁": {"癸", "壬"},
    "戊": {"甲", "乙"}, "己": {"乙", "甲"}, "庚": {"丙", "丁"}, "辛": {"丁", "丙"},
    "壬": {"戊", "己"}, "癸": {"己", "戊"},
}
# 拱禄常见：日柱-时柱 虚拱禄。丁巳日丙午时（拱午禄）、戊辰日己巳时（拱巳禄）、癸亥日壬子时（拱子禄）等
GONG_LU_PILLARS = {
    ("丁", "巳", "丙", "午"), ("戊", "辰", "己", "巳"), ("癸", "亥", "壬", "子"),
    ("戊", "午", "己", "巳"), ("丙", "午", "丁", "巳"),
}
# 胞胎格：日柱在绝地。庚寅（庚绝寅）、甲申（甲绝申）、辛卯、乙酉、壬巳、丙亥、癸午、丁子等
JUE_DI_DAY_PILLARS = {"庚寅", "甲申", "辛卯", "乙酉", "壬巳", "丙亥", "癸午", "丁子", "戊寅", "己酉"}


def is_a41_renqi_longbei(day_pillar: str, branches: List[str]) -> bool:
    """A-41 壬骑龙背：壬辰日，地支多见辰、寅（≥3 以满足奇格 <0.1%），忌见戌冲。"""
    if (day_pillar or "").strip() != "壬辰":
        return False
    all_branches = [b for b in branches if b]
    if "戌" in all_branches:
        return False
    chen = sum(1 for b in all_branches if b == "辰")
    yin = sum(1 for b in all_branches if b == "寅")
    return (chen + yin) >= 3


def is_a42_guilu(day_master: str, hour_stem: str, hour_branch: str) -> bool:
    """A-42 归禄格：日禄归时（时支=日干禄），时柱不见官杀（时干非日干官杀）。"""
    lu = LU_DI_ZHI.get((day_master or "").strip())
    if not lu or (hour_branch or "").strip() != lu:
        return False
    officer = DAY_TO_OFFICER_STEMS.get((day_master or "").strip(), set())
    if (hour_stem or "").strip() in officer:
        return False
    return True


def is_a43_gonglu(day_master: str, day_branch: str, hour_stem: str, hour_branch: str) -> bool:
    """A-43 拱禄格：日时干支虚拱禄位。"""
    key = (day_master or "", day_branch or "", hour_stem or "", hour_branch or "")
    return key in GONG_LU_PILLARS


# 日干 → (财干集合, 官干集合)，杂气财官须财官双透
DAY_TO_CAI_GUAN_PAIRS = {
    "甲": ({"戊", "己"}, {"庚", "辛"}), "乙": ({"戊", "己"}, {"辛", "庚"}),
    "丙": ({"庚", "辛"}, {"壬", "癸"}), "丁": ({"庚", "辛"}, {"癸", "壬"}),
    "戊": ({"壬", "癸"}, {"甲", "乙"}), "己": ({"壬", "癸"}, {"乙", "甲"}),
    "庚": ({"甲", "乙"}, {"丙", "丁"}), "辛": ({"甲", "乙"}, {"丁", "丙"}),
    "壬": ({"丙", "丁"}, {"戊", "己"}), "癸": ({"丙", "丁"}, {"己", "戊"}),
}


def is_a44_zaqi_caiguan(month_branch: str, stems: List[str], day_master: str) -> bool:
    """A-44 杂气财官：辰戌丑未月令，月干透财或透官，且年/时干另一柱透官或透财（财官双透，<5% 熔断）。"""
    if (month_branch or "").strip() not in ("辰", "戌", "丑", "未"):
        return False
    pair = DAY_TO_CAI_GUAN_PAIRS.get((day_master or "").strip())
    if not pair:
        return False
    cai_stems, guan_stems = pair
    month_stem = stems[1] if len(stems) > 1 else ""
    year_stem = stems[0] if len(stems) > 0 else ""
    hour_stem = stems[3] if len(stems) > 3 else ""
    if not month_stem:
        return False
    other = [s for s in (year_stem, hour_stem) if s]
    if month_stem in cai_stems:
        return any(s in guan_stems for s in other)
    if month_stem in guan_stems:
        return any(s in cai_stems for s in other)
    return False


def is_a45_baotai(day_pillar: str) -> bool:
    """A-45 胞胎格：庚寅、甲申等日，生于绝地。"""
    return (day_pillar or "").strip() in JUE_DI_DAY_PILLARS


def l1_match_a41_through_a50(case: Dict[str, Any]) -> List[str]:
    """对单条 case 应用 A-41～A-50 的 L1，返回命中的 pattern_id 列表。"""
    out: List[str] = []
    stems, branches, day_master, month_branch, day_pillar, hour_pillar = _bazi_to_pillars(case)
    if len(stems) < 4 or len(branches) < 4:
        return out
    hour_stem = stems[3] if len(stems) > 3 else ""
    hour_branch = branches[3] if len(branches) > 3 else ""
    day_branch = branches[2] if len(branches) > 2 else ""

    if is_a41_renqi_longbei(day_pillar, branches):
        out.append("A-41")
    if is_a42_guilu(day_master, hour_stem, hour_branch):
        out.append("A-42")
    if is_a43_gonglu(day_master, day_branch, hour_stem, hour_branch):
        out.append("A-43")
    if is_a44_zaqi_caiguan(month_branch, stems, day_master):
        out.append("A-44")
    if is_a45_baotai(day_pillar):
        out.append("A-45")

    return out
