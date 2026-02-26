#!/usr/bin/env python3
"""
FDS SOP V6.1：第六梯队（A-46～A-60）终极合拢 L1
================================================
- A-46 时墓格：日干见时支为墓，且时干透财。
- A-47 倒飞天：丙/丁日地支午多（火局虚冲子）。
- A-48 六甲趋乾：甲日地支亥多。
- A-49 六壬趋艮：壬日地支寅多。
- A-50 刑合格：地支见三刑且天干透官。
- A-51～A-60：杂气变格与神煞占位（L1 待补或极简）。
"""
from __future__ import annotations

from typing import Any, Dict, List

from pattern_scanner_v57 import _bazi_to_pillars
from pattern_scanner_v60 import DAY_TO_CAI_GUAN_PAIRS, DAY_TO_OFFICER_STEMS

# 日干 → 墓支（时墓格）
DAY_TO_TOMB_BRANCH = {
    "甲": "未", "乙": "戌", "丙": "戌", "丁": "丑", "戊": "戌",
    "己": "丑", "庚": "丑", "辛": "辰", "壬": "辰", "癸": "未",
}
# 三刑组（寅巳申、丑戌未、子卯）
SAN_XING_SETS = [
    {"寅", "巳", "申"},
    {"丑", "戌", "未"},
    {"子", "卯"},
]


def is_a46_shimu(day_master: str, hour_stem: str, hour_branch: str) -> bool:
    """A-46 时墓格：时支=日干墓，且时干透财。"""
    tomb = DAY_TO_TOMB_BRANCH.get((day_master or "").strip())
    if not tomb or (hour_branch or "").strip() != tomb:
        return False
    pair = DAY_TO_CAI_GUAN_PAIRS.get((day_master or "").strip())
    if not pair:
        return False
    cai_stems, _ = pair
    return (hour_stem or "").strip() in cai_stems


def is_a47_daofeitian(day_master: str, branches: List[str]) -> bool:
    """A-47 倒飞天禄马：丙/丁日地支午多（≥2），火局虚冲子。"""
    if (day_master or "").strip() not in ("丙", "丁"):
        return False
    wu_count = sum(1 for b in branches if b == "午")
    return wu_count >= 2


def is_a48_liujia_quqian(day_master: str, branches: List[str]) -> bool:
    """A-48 六甲趋乾：甲日地支亥多（≥3，满足丰度 <0.2% 熔断）。"""
    if (day_master or "").strip() != "甲":
        return False
    hai_count = sum(1 for b in branches if b == "亥")
    return hai_count >= 3


def is_a49_liuren_qugen(day_master: str, branches: List[str]) -> bool:
    """A-49 六壬趋艮：壬日地支寅多（≥2）。"""
    if (day_master or "").strip() != "壬":
        return False
    yin_count = sum(1 for b in branches if b == "寅")
    return yin_count >= 2


def is_a50_xinghe(day_master: str, branches: List[str], stems: List[str]) -> bool:
    """A-50 刑合格：地支见三刑（寅巳申/丑戌未/子卯）且天干透官。"""
    branch_set = set(b for b in branches if b)
    has_san_xing = any(sx <= branch_set for sx in SAN_XING_SETS)
    if not has_san_xing:
        return False
    officer = DAY_TO_OFFICER_STEMS.get((day_master or "").strip(), set())
    other_stems = [stems[i] for i in (0, 1, 3) if i < len(stems) and stems[i]]
    return any(s in officer for s in other_stems)


def l1_match_a46_through_a60(case: Dict[str, Any]) -> List[str]:
    """对单条 case 应用 A-46～A-60 的 L1，返回命中的 pattern_id 列表。"""
    out: List[str] = []
    stems, branches, day_master, _, _, _ = _bazi_to_pillars(case)
    if len(stems) < 4 or len(branches) < 4:
        return out
    hour_stem = stems[3] if len(stems) > 3 else ""
    hour_branch = branches[3] if len(branches) > 3 else ""

    if is_a46_shimu(day_master, hour_stem, hour_branch):
        out.append("A-46")
    if is_a47_daofeitian(day_master, branches):
        out.append("A-47")
    if is_a48_liujia_quqian(day_master, branches):
        out.append("A-48")
    if is_a49_liuren_qugen(day_master, branches):
        out.append("A-49")
    if is_a50_xinghe(day_master, branches, stems):
        out.append("A-50")
    # A-51～A-60：占位，L1 待审计师后续签发后补全
    return out
