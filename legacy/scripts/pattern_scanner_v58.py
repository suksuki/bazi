#!/usr/bin/env python3
"""
FDS SOP V5.8：第三梯队奇格异局 L1 物理过滤器（A-31～A-35）
================================================================
- A-31 六阴朝阳：辛日 + 戊子时，月令不通火气（地支无巳午，天干无丙丁）。
- A-32 六乙鼠贵：乙日 + 丙子时，忌见午冲、未合（地支无午、无未）。
- A-33 井栏叉：庚申/庚子/庚辰日，地支申子辰全。
- A-34 飞天禄马：庚/壬日 + 地支子字 ≥2（3 个权重更高，518k 放宽至 2）。
- A-35 从杀格：日主无根（无印、无比劫、无库根）+ 满局官杀。
"""
from __future__ import annotations

from typing import Any, Dict, List, Tuple

# 复用 v57 的支柱解析与十神求和
from pattern_scanner_v57 import (
    _bazi_to_pillars,
    _ten_gods_sum,
    _has_root,
    LU_DI_ZHI,
    REN_DI_ZHI,
)
ZHI_WUXING = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火", "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}
GAN_WUXING = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土", "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}


def is_a31_liuyin_chaoyang(stems: List[str], branches: List[str], day_master: str, hour_pillar: str) -> bool:
    """A-31 六阴朝阳：辛日 + 戊子时；月令不通火气（地支无巳午，天干无丙丁）。"""
    if (day_master or "").strip() != "辛":
        return False
    if (hour_pillar or "").strip() != "戊子":
        return False
    all_stems = [s for s in stems if s]
    all_branches = [b for b in branches if b]
    if "丙" in all_stems or "丁" in all_stems:
        return False
    if "巳" in all_branches or "午" in all_branches:
        return False
    return True


def is_a32_liuyi_shugui(day_master: str, hour_pillar: str, branches: List[str]) -> bool:
    """A-32 六乙鼠贵：乙日 + 丙子时；忌见午冲、未合（地支无午、无未）。"""
    if (day_master or "").strip() != "乙":
        return False
    if (hour_pillar or "").strip() != "丙子":
        return False
    all_branches = [b for b in branches if b]
    if "午" in all_branches or "未" in all_branches:
        return False
    return True


def is_a33_jinglancha(day_pillar: str, branches: List[str]) -> bool:
    """A-33 井栏叉：庚申/庚子/庚辰日，地支申子辰全。"""
    valid_day = (day_pillar or "").strip() in {"庚申", "庚子", "庚辰"}
    if not valid_day:
        return False
    s = set(b for b in branches if b)
    return {"申", "子", "辰"} <= s


def is_a34_feitian_luma(day_master: str, branches: List[str], *, min_zi: int = 3) -> bool:
    """A-34 飞天禄马：庚/壬日 + 地支子字 ≥ min_zi（默认 3 以满足奇格丰度 ≤0.5%；2 为放宽定义）。"""
    if (day_master or "").strip() not in ("庚", "壬"):
        return False
    zi_count = sum(1 for b in branches if b == "子")
    return zi_count >= min_zi


def is_a35_cong_sha(case: Dict[str, Any], day_master: str, branches: List[str]) -> bool:
    """A-35 从杀格：日主无根（无印、无比劫、无库根）+ 满局官杀。"""
    if _has_root(day_master, branches):
        return False
    yin_bi = _ten_gods_sum(case, ["ZC", "PC", "ZB", "PB"])
    guan_sha = _ten_gods_sum(case, ["ZG", "PG"])
    cai_shang = _ten_gods_sum(case, ["ZR", "PR", "ZS", "PS"])
    if yin_bi >= 0.5:
        return False
    if guan_sha < 1.5:
        return False
    return guan_sha >= 1.5 * max(cai_shang, 0.1)


def l1_match_a31_through_a35(case: Dict[str, Any]) -> List[str]:
    """对单条 case 应用 A-31～A-35 的 L1 过滤器，返回命中的 pattern_id 列表。"""
    out: List[str] = []
    stems, branches, day_master, month_branch, day_pillar, hour_pillar = _bazi_to_pillars(case)
    if len(stems) < 4 or len(branches) < 4:
        return out

    if is_a31_liuyin_chaoyang(stems, branches, day_master, hour_pillar):
        out.append("A-31")
    if is_a32_liuyi_shugui(day_master, hour_pillar, branches):
        out.append("A-32")
    if is_a33_jinglancha(day_pillar, branches):
        out.append("A-33")
    if is_a34_feitian_luma(day_master, branches):
        out.append("A-34")
    if is_a35_cong_sha(case, day_master, branches):
        out.append("A-35")

    return out
