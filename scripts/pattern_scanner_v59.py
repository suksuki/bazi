#!/usr/bin/env python3
"""
FDS SOP V5.9：第四梯队杂气与进阶从格 L1（A-36～A-40）
========================================================
- A-36 从儿格（进阶）：Gate1 伤食>60%，Gate2 见财，Gate3 印/官杀≤ignore_threshold。
- A-37 从气格：日主无根，某单一五行极旺（非官杀/财/食主导）。
- A-38 弃命从财格：满局财星，日主无根，无比劫夺财。
- A-39 从官格：满局正官，无食伤克制，日主无根。
- A-40 从旺进阶：满局印比，不见财官伤，气势极纯。
"""
from __future__ import annotations

from typing import Any, Dict, List

from pattern_scanner_v57 import (
    _bazi_to_pillars,
    _ten_gods_sum,
    _has_root,
    _wuxing_counts,
)

# 伤食占比临界（Gate 1）
CONG_ER_SHANG_RATIO_MIN = 0.6
# 从气格：单一五行占比下限（8 柱中该五行占比）
CONG_QI_WUXING_RATIO_MIN = 0.6
# 从财/从官/从旺：主导十神占比下限
CONG_MAIN_RATIO_MIN = 0.55


def _get_ignore_threshold() -> float:
    """从 config.physics.ignore_threshold 读取；缺省 0.5。"""
    try:
        from core.config import config
        return getattr(config.physics, "ignore_threshold", 0.5)
    except Exception:
        return 0.5


def is_cong_er_advanced(case: Dict[str, Any]) -> bool:
    """
    A-36 从儿格进阶 L1：三重门。
    Gate 1: 伤食能量占比 > 60%。
    Gate 2: 必须见财星（吾儿又见儿）。
    Gate 3: 印星、官杀 ≤ ignore_threshold（清纯度）。
    """
    tg = case.get("ten_gods") or {}
    shang_shi = _ten_gods_sum(case, ["ZS", "PS"])
    cai = _ten_gods_sum(case, ["ZR", "PR"])
    guan = _ten_gods_sum(case, ["ZG", "PG"])
    yin = _ten_gods_sum(case, ["ZC", "PC"])
    total = 0.0
    for v in (tg or {}).values():
        if isinstance(v, (int, float)):
            total += float(v)
        elif isinstance(v, dict):
            total += float(v.get("mean", v.get("strength", 0)))
    if total <= 0:
        return False
    # Gate 1: 伤食占比 > 60%
    if shang_shi / total <= CONG_ER_SHANG_RATIO_MIN:
        return False
    # Gate 2: 见财星
    if cai <= 0:
        return False
    # Gate 3: 印、官杀可忽略
    ignore = _get_ignore_threshold()
    if yin > ignore or guan > ignore:
        return False
    return True


def is_cong_qi(case: Dict[str, Any], day_master: str, stems: List[str], branches: List[str]) -> bool:
    """
    A-37 从气格：日主无根，某单一五行极旺（非官杀/财/食主导）。
    单一五行在干支中占比 ≥ 60%，且日主无根；排除“官杀/财/食”为唯一极旺者时的歧义，此处简化为：该五行计数最多且占比≥60%。
    """
    if _has_root(day_master, branches):
        return False
    counts = _wuxing_counts(stems, branches)
    total = sum(counts.values())
    if total < 4:
        return False
    for wuxing, c in counts.items():
        if c / total >= CONG_QI_WUXING_RATIO_MIN:
            return True
    return False


def is_cong_cai(case: Dict[str, Any], day_master: str, branches: List[str]) -> bool:
    """A-38 弃命从财格：满局财星，日主无根，无比劫夺财。"""
    if _has_root(day_master, branches):
        return False
    cai = _ten_gods_sum(case, ["ZR", "PR"])
    yin_bi = _ten_gods_sum(case, ["ZC", "PC", "ZB", "PB"])
    total = _ten_gods_sum(case, ["ZG", "PG", "ZR", "PR", "ZS", "PS", "ZC", "PC", "ZB", "PB"])
    if total <= 0:
        return False
    if cai / total < CONG_MAIN_RATIO_MIN:
        return False
    if yin_bi > _get_ignore_threshold():
        return False
    return True


def is_cong_guan(case: Dict[str, Any], day_master: str, branches: List[str]) -> bool:
    """A-39 从官格：满局正官，无食伤克制，日主无根。"""
    if _has_root(day_master, branches):
        return False
    guan = _ten_gods_sum(case, ["ZG", "PG"])
    shang = _ten_gods_sum(case, ["ZS", "PS"])
    total = _ten_gods_sum(case, ["ZG", "PG", "ZR", "PR", "ZS", "PS", "ZC", "PC", "ZB", "PB"])
    if total <= 0:
        return False
    if guan / total < CONG_MAIN_RATIO_MIN:
        return False
    if shang > _get_ignore_threshold():
        return False
    return True


def is_cong_wang_advanced(case: Dict[str, Any], day_master: str, branches: List[str]) -> bool:
    """A-40 从旺进阶：满局印比，不见财官伤，气势极纯。"""
    yin_bi = _ten_gods_sum(case, ["ZC", "PC", "ZB", "PB"])
    cai_guan_shang = _ten_gods_sum(case, ["ZR", "PR", "ZG", "PG", "ZS", "PS"])
    total = _ten_gods_sum(case, ["ZG", "PG", "ZR", "PR", "ZS", "PS", "ZC", "PC", "ZB", "PB"])
    if total <= 0:
        return False
    if yin_bi / total < CONG_MAIN_RATIO_MIN:
        return False
    if cai_guan_shang > _get_ignore_threshold():
        return False
    return True


def l1_match_a36_through_a40(case: Dict[str, Any]) -> List[str]:
    """对单条 case 应用 A-36～A-40 的 L1，返回命中的 pattern_id 列表。"""
    out: List[str] = []
    stems, branches, day_master, _, _, _ = _bazi_to_pillars(case)
    if len(stems) < 4 or len(branches) < 4:
        return out

    if is_cong_er_advanced(case):
        out.append("A-36")
    if is_cong_qi(case, day_master, stems, branches):
        out.append("A-37")
    if is_cong_cai(case, day_master, branches):
        out.append("A-38")
    if is_cong_guan(case, day_master, branches):
        out.append("A-39")
    if is_cong_wang_advanced(case, day_master, branches):
        out.append("A-40")

    return out
