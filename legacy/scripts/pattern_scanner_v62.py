#!/usr/bin/env python3
"""
FDS SOP V6.2：A-51～A-60 简易 L1 补齐（神煞变格）
==================================================
- A-51 文昌/学堂：日干文昌贵人地支在四柱出现。
- A-52 桃花/将星：桃花地支在四柱出现且子午卯酉≥2。
- A-53 学堂格：月支或年支为日干文昌或禄。
- A-54 驿马格：驿马地支在四柱出现。
- A-55 天乙格：天乙贵人地支在四柱出现。
- A-56 金舆格：日干金舆地支在时支或日支（占位）。
- A-57 将星格：将星地支在四柱出现。
- A-58～A-60：杂气/占位（简单结构判定）。
"""
from __future__ import annotations

from typing import Any, Dict, List

from pattern_scanner_v61 import (
    _bazi_to_pillars,
    is_a46_shimu,
    is_a47_daofeitian,
    is_a48_liujia_quqian,
    is_a49_liuren_qugen,
    is_a50_xinghe,
)

# 文昌：日干 → 文昌地支（与 symbolic_stars 一致）
WEN_CHANG = {
    "甲": "巳", "乙": "午", "丙": "申", "丁": "酉", "戊": "申", "己": "酉",
    "庚": "亥", "辛": "子", "壬": "寅", "癸": "卯",
}
# 禄：日干 → 禄支
LU = {
    "甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳", "己": "午",
    "庚": "申", "辛": "酉", "壬": "亥", "癸": "子",
}
# 桃花：年支/日支 → 桃花地支
TAOHUA = {
    "寅": "卯", "午": "卯", "戌": "卯", "申": "酉", "子": "酉", "辰": "酉",
    "巳": "午", "酉": "午", "丑": "午", "亥": "子", "卯": "子", "未": "子",
}
# 将星：寅午戌→午，申子辰→子，巳酉丑→酉，亥卯未→卯
JIANG_XING = {
    "寅": "午", "午": "午", "戌": "午", "申": "子", "子": "子", "辰": "子",
    "巳": "酉", "酉": "酉", "丑": "酉", "亥": "卯", "卯": "卯", "未": "卯",
}
# 驿马：寅午戌→申，申子辰→寅，巳酉丑→亥，亥卯未→巳
YI_MA = {
    "寅": "申", "午": "申", "戌": "申", "申": "寅", "子": "寅", "辰": "寅",
    "巳": "亥", "酉": "亥", "丑": "亥", "亥": "巳", "卯": "巳", "未": "巳",
}
# 天乙贵人：日干 → 地支列表
TIAN_YI = {
    "甲": ["丑", "未"], "戊": ["丑", "未"], "庚": ["丑", "未"],
    "乙": ["子", "申"], "己": ["子", "申"],
    "丙": ["亥", "酉"], "丁": ["亥", "酉"],
    "壬": ["卯", "巳"], "癸": ["卯", "巳"],
    "辛": ["午", "寅"],
}
# 金舆：甲龙乙蛇丙戊羊... 简化为日干→单支占位
JIN_YU = {
    "甲": "辰", "乙": "巳", "丙": "未", "丁": "申", "戊": "未",
    "己": "申", "庚": "戌", "辛": "亥", "壬": "丑", "癸": "寅",
}
ZI_WU_MAO_YOU = {"子", "午", "卯", "酉"}


def _is_a51_wenchang_xuetang(day_master: str, branches: List[str]) -> bool:
    """A-51 文昌/学堂：日干文昌贵人地支在四柱出现。"""
    wc = WEN_CHANG.get((day_master or "").strip())
    if not wc:
        return False
    return wc in (branches or [])


def _is_a52_taohua_jiangxing(branches: List[str], year_branch: str, day_branch: str) -> bool:
    """A-52 桃花/将星：桃花地支在四柱出现且子午卯酉≥2。"""
    for trigger in [year_branch, day_branch]:
        if not trigger:
            continue
        pb = TAOHUA.get(trigger)
        if pb and pb in (branches or []):
            zi_count = sum(1 for b in branches if b in ZI_WU_MAO_YOU)
            if zi_count >= 2:
                return True
    return False


def _is_a53_xuetang(day_master: str, branches: List[str]) -> bool:
    """A-53 学堂格：月支或年支为日干文昌或禄。"""
    dm = (day_master or "").strip()
    wc, lu = WEN_CHANG.get(dm), LU.get(dm)
    if not wc and not lu:
        return False
    # 年支 index 0，月支 index 1
    for i in (0, 1):
        if i < len(branches) and branches[i] in (wc, lu):
            return True
    return False


def _is_a54_yima(branches: List[str], year_branch: str, day_branch: str) -> bool:
    """A-54 驿马格：驿马地支在四柱出现。"""
    for trigger in [year_branch, day_branch]:
        if not trigger:
            continue
        ym = YI_MA.get(trigger)
        if ym and ym in (branches or []):
            return True
    return False


def _is_a55_tianyi(day_master: str, branches: List[str]) -> bool:
    """A-55 天乙格：天乙贵人地支在四柱出现。"""
    targets = TIAN_YI.get((day_master or "").strip(), [])
    return any(b in targets for b in (branches or []))


def _is_a56_jinyu(day_master: str, branches: List[str]) -> bool:
    """A-56 金舆格：日干金舆地支在时支或日支。"""
    jy = JIN_YU.get((day_master or "").strip())
    if not jy:
        return False
    # 日支 index 2，时支 index 3
    for i in (2, 3):
        if i < len(branches) and branches[i] == jy:
            return True
    return False


def _is_a57_jiangxing(branches: List[str], year_branch: str, day_branch: str) -> bool:
    """A-57 将星格：将星地支在四柱出现。"""
    for trigger in [year_branch, day_branch]:
        if not trigger:
            continue
        jx = JIANG_XING.get(trigger)
        if jx and jx in (branches or []):
            return True
    return False


def _is_a58_placeholder(day_master: str, stems: List[str], branches: List[str]) -> bool:
    """A-58 占位：禄在时支且时干为日干同类。"""
    lu_zhi = LU.get((day_master or "").strip())
    if not lu_zhi or len(branches) < 4:
        return False
    return (branches[3] == lu_zhi) and (stems[3] == day_master.strip())


def _is_a59_placeholder(stems: List[str], branches: List[str]) -> bool:
    """A-59 占位：四柱天干恰好两种且各出现两次（两神成象极简）。"""
    if len(stems) < 4:
        return False
    from collections import Counter
    c = Counter(s for s in stems if s)
    if len(c) != 2:
        return False
    return all(n == 2 for n in c.values())


def _is_a60_placeholder(branches: List[str]) -> bool:
    """A-60 占位：四柱地支恰好两种且各出现两次（双支成象）。"""
    if len(branches) < 4:
        return False
    from collections import Counter
    c = Counter(b for b in branches if b)
    if len(c) != 2:
        return False
    return all(n == 2 for n in c.values())


def l1_match_a46_through_a60(case: Dict[str, Any]) -> List[str]:
    """对单条 case 应用 A-46～A-60 的 L1（含 V6.2 补齐的 A-51～A-60），返回命中的 pattern_id 列表。"""
    out: List[str] = []
    stems, branches, day_master, _, _, _ = _bazi_to_pillars(case)
    if len(stems) < 4 or len(branches) < 4:
        return out
    hour_stem = stems[3] if len(stems) > 3 else ""
    hour_branch = branches[3] if len(branches) > 3 else ""
    year_branch = branches[0] if branches else ""
    day_branch = branches[2] if len(branches) > 2 else ""

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
    if _is_a51_wenchang_xuetang(day_master, branches):
        out.append("A-51")
    if _is_a52_taohua_jiangxing(branches, year_branch, day_branch):
        out.append("A-52")
    if _is_a53_xuetang(day_master, branches):
        out.append("A-53")
    if _is_a54_yima(branches, year_branch, day_branch):
        out.append("A-54")
    if _is_a55_tianyi(day_master, branches):
        out.append("A-55")
    if _is_a56_jinyu(day_master, branches):
        out.append("A-56")
    if _is_a57_jiangxing(branches, year_branch, day_branch):
        out.append("A-57")
    if _is_a58_placeholder(day_master, stems, branches):
        out.append("A-58")
    if _is_a59_placeholder(stems, branches):
        out.append("A-59")
    if _is_a60_placeholder(branches):
        out.append("A-60")
    return out
