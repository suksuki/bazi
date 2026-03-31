#!/usr/bin/env python3
"""
FDS SOP V5.7：A-14～A-30 L1 物理过滤器
========================================
海选必须先过底层干支的「硬核物理约束」，再计 5D。
- A-14～A-18 化气；A-19 魁罡；A-20 金神。
- A-21～A-23 从强/从弱/从儿（十神比例+根气）；A-24～A-28 专旺（三合三会+月令）；A-29 天地元气；A-30 两神成象。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

# 天干五合 → 化神五行（与 phase1_initialization 一致）
STEM_TRANSFORM = {
    ("甲", "己"): "土", ("己", "甲"): "土",
    ("乙", "庚"): "金", ("庚", "乙"): "金",
    ("丙", "辛"): "水", ("辛", "丙"): "水",
    ("丁", "壬"): "木", ("壬", "丁"): "木",
    ("戊", "癸"): "火", ("癸", "戊"): "火",
}
# 月令地支主气 → 五行（本气天干→五行）
GAN_WUXING = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土", "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
# 化神五行 → 月令须属（支持引化的地支主气五行）
HUA_MONTH_WUXING = {
    "金": ["金", "土"],
    "木": ["木", "水"],
    "水": ["水", "金"],
    "火": ["火", "木"],
    "土": ["土", "火"],
}
# 化神五行 → 克神（强克化神则抑制）
HUA_KE_BY = {"金": "火", "木": "金", "水": "土", "火": "水", "土": "木"}

KUI_GANG_DAY_PILLARS = {"壬辰", "庚戌", "庚辰", "戊戌"}
GOLD_GOD_HOUR_PILLARS = {"癸酉", "己巳", "乙丑"}
FIRE_MONTH_BRANCHES = {"巳", "午"}


def _bazi_to_pillars(case: Dict[str, Any]) -> Tuple[List[str], List[str], str, str, str, str]:
    """从 case['bazi'] 提取 (stems, branches, day_master, month_branch, day_pillar, hour_pillar)。"""
    bazi = case.get("bazi")
    if not bazi or not isinstance(bazi, dict):
        return [], [], "", "", "", ""
    stems, branches = [], []
    for name in ("year", "month", "day", "hour"):
        p = bazi.get(name)
        if isinstance(p, str) and len(p) >= 2:
            stems.append(p[0])
            branches.append(p[1])
        elif isinstance(p, dict):
            stems.append((p.get("gan") or p.get("stem") or ""))
            branches.append((p.get("zhi") or p.get("branch") or ""))
        else:
            stems.append("")
            branches.append("")
    day_master = stems[2] if len(stems) > 2 else ""
    month_branch = branches[1] if len(branches) > 1 else ""
    day_pillar = (stems[2] + branches[2]) if len(stems) > 2 and len(branches) > 2 else ""
    hour_pillar = (stems[3] + branches[3]) if len(stems) > 3 and len(branches) > 3 else ""
    return stems, branches, day_master, month_branch, day_pillar, hour_pillar


def _month_main_stem(branch: str) -> Optional[str]:
    """月支本气天干。"""
    try:
        from core.constants import HIDDEN_STEMS_MAP
        entry = HIDDEN_STEMS_MAP.get(branch)
        if isinstance(entry, dict) and "main" in entry:
            return entry["main"]
    except Exception:
        pass
    return None


def is_transformed(
    branch_month: str,
    stem_day: str,
    stem_neighbor_list: List[str],
    *,
    allow_ke_suppress: bool = True,
    all_branches: Optional[List[str]] = None,
) -> Optional[str]:
    """
    化气五格 L1：日干与月干或时干相合，且月令主气为化神五行。
    allow_ke_suppress：若 True，原局地支主气见强克化神则判不通过。
    返回化神五行（土/金/水/木/火）或 None。
    """
    if not stem_day or not branch_month:
        return None
    month_main = _month_main_stem(branch_month)
    month_wuxing = GAN_WUXING.get(month_main, "") if month_main else ""
    # 日干与邻干（月干、时干）是否成五合
    for other in stem_neighbor_list:
        if not other:
            continue
        pair = (stem_day, other)
        if pair not in STEM_TRANSFORM:
            continue
        hua_wuxing = STEM_TRANSFORM[pair]
        allowed = HUA_MONTH_WUXING.get(hua_wuxing, [])
        if month_wuxing not in allowed:
            continue
        if allow_ke_suppress and all_branches:
            ke_wuxing = HUA_KE_BY.get(hua_wuxing)
            if ke_wuxing:
                for zb in all_branches:
                    m = _month_main_stem(zb)
                    if m and GAN_WUXING.get(m) == ke_wuxing:
                        return None
        return hua_wuxing
    return None


def is_kui_gang(pillar_day: str) -> bool:
    """魁罡格 L1：日柱必须为 壬辰、庚戌、庚辰、戊戌。"""
    return (pillar_day or "").strip() in KUI_GANG_DAY_PILLARS


def is_gold_god(pillar_hour: str, branch_month: str) -> bool:
    """金神格 L1：时柱为 癸酉、己巳、乙丑，且月令为火（巳午）。"""
    return (
        (pillar_hour or "").strip() in GOLD_GOD_HOUR_PILLARS
        and (branch_month or "").strip() in FIRE_MONTH_BRANCHES
    )


def which_pattern_a14_a18(
    branch_month: str,
    stem_day: str,
    stem_month: str,
    stem_hour: str,
    all_branches: Optional[List[str]] = None,
) -> Optional[str]:
    """返回 A-14～A-18 中命中的化气格 ID，否则 None。"""
    neighbors = [stem_month, stem_hour]
    hua = is_transformed(
        branch_month, stem_day, neighbors,
        allow_ke_suppress=True,
        all_branches=all_branches,
    )
    if not hua:
        return None
    mapping = {"金": "A-14", "木": "A-15", "水": "A-16", "火": "A-17", "土": "A-18"}
    return mapping.get(hua)


def l1_match_a14_through_a20(case: Dict[str, Any]) -> List[str]:
    """
    对单条 case 应用 A-14～A-20 的 L1 过滤器，返回命中的 pattern_id 列表（可多格同中，如魁罡+化气不互斥）。
    """
    out: List[str] = []
    stems, branches, day_master, month_branch, day_pillar, hour_pillar = _bazi_to_pillars(case)
    if not day_master and not day_pillar:
        return out

    # A-19 魁罡
    if is_kui_gang(day_pillar):
        out.append("A-19")

    # A-20 金神
    if is_gold_god(hour_pillar, month_branch):
        out.append("A-20")

    # A-14～A-18 化气
    stem_month = stems[1] if len(stems) > 1 else ""
    stem_hour = stems[3] if len(stems) > 3 else ""
    pid = which_pattern_a14_a18(month_branch, day_master, stem_month, stem_hour, branches)
    if pid:
        out.append(pid)

    return out


# ---------- 第二梯队 A-21～A-30：从格与专旺 ----------
ZHI_WUXING = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火", "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}
# 三合局 (三支齐全即成局)
SAN_HE = {"金": {"巳", "酉", "丑"}, "水": {"申", "子", "辰"}, "木": {"亥", "卯", "未"}, "火": {"寅", "午", "戌"}}
# 三会局
SAN_HUI = {"金": {"申", "酉", "戌"}, "水": {"亥", "子", "丑"}, "木": {"寅", "卯", "辰"}, "火": {"巳", "午", "未"}}
MONTH_BRANCH_TO_WUXING = {"寅": "木", "卯": "木", "辰": "土", "巳": "火", "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水", "子": "水", "丑": "土"}
# 日干禄刃地支（有根则非从弱）
LU_DI_ZHI = {"甲": "寅", "乙": "卯", "丙": "巳", "丁": "午", "戊": "巳", "己": "午", "庚": "申", "辛": "酉", "壬": "亥", "癸": "子"}
REN_DI_ZHI = {"甲": "卯", "乙": "寅", "丙": "午", "丁": "巳", "戊": "午", "己": "巳", "庚": "酉", "辛": "申", "壬": "子", "癸": "亥"}


def _ten_gods_sum(case: Dict[str, Any], codes: List[str]) -> float:
    """求 case['ten_gods'] 中 codes 对应键的数值和（支持标量或 {mean/strength}）。"""
    tg = case.get("ten_gods") or {}
    s = 0.0
    for c in codes:
        v = tg.get(c)
        if v is None:
            continue
        if isinstance(v, (int, float)):
            s += float(v)
        elif isinstance(v, dict):
            s += float(v.get("mean", v.get("strength", 0)))
    return s


def _has_root(day_master: str, branches: List[str]) -> bool:
    """日主在四支中是否有禄或刃。"""
    if not day_master or not branches:
        return False
    lu = LU_DI_ZHI.get(day_master)
    ren = REN_DI_ZHI.get(day_master)
    return (lu and lu in branches) or (ren and ren in branches)


def _branch_set_has_ju(branches: List[str], wuxing: str) -> bool:
    """四支是否成该五行的三合或三会局（三支齐全）。土：辰戌丑未至少三支。"""
    s = set(b for b in branches if b)
    if len(s) < 3:
        return False
    if wuxing == "土":
        tu_zhi = {"辰", "戌", "丑", "未"}
        return len(tu_zhi & s) >= 3
    he = SAN_HE.get(wuxing)
    hui = SAN_HUI.get(wuxing)
    if he and he <= s:
        return True
    if hui and hui <= s:
        return True
    return False


def _wuxing_counts(stems: List[str], branches: List[str]) -> Dict[str, int]:
    """四柱干支中各五行出现次数。"""
    counts = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
    for g in stems:
        if g and GAN_WUXING.get(g):
            counts[GAN_WUXING[g]] = counts.get(GAN_WUXING[g], 0) + 1
    for z in branches:
        if z and ZHI_WUXING.get(z):
            counts[ZHI_WUXING[z]] = counts.get(ZHI_WUXING[z], 0) + 1
    return counts


def is_cong_qiang(case: Dict[str, Any]) -> bool:
    """从强格 L1：满局印比，无/极微官杀财星。"""
    yin_bi = _ten_gods_sum(case, ["ZC", "PC", "ZB", "PB"])
    guan_cai = _ten_gods_sum(case, ["ZG", "PG", "ZR", "PR"])
    if yin_bi <= 0:
        return False
    return guan_cai < 0.5 and yin_bi > 2.0 * max(guan_cai, 0.1)


def is_cong_ruo(case: Dict[str, Any], day_master: str, branches: List[str]) -> bool:
    """从弱格 L1：满局财官伤，日主极弱且地支无根。"""
    if _has_root(day_master, branches):
        return False
    cai_guan_shang = _ten_gods_sum(case, ["ZR", "PR", "ZG", "PG", "ZS", "PS"])
    yin_bi = _ten_gods_sum(case, ["ZC", "PC", "ZB", "PB"])
    if cai_guan_shang <= 0:
        return False
    return yin_bi < 1.0 and cai_guan_shang > 2.0


def is_cong_er(case: Dict[str, Any]) -> bool:
    """从儿格 L1：伤食极旺且见财，不见官印。"""
    shang_cai = _ten_gods_sum(case, ["ZS", "PS", "ZR", "PR"])
    guan_yin = _ten_gods_sum(case, ["ZG", "PG", "ZC", "PC"])
    if shang_cai <= 0:
        return False
    return guan_yin < 0.5 and shang_cai > 2.0


def is_special_wang(branches: List[str], month_branch: str, wuxing: str) -> bool:
    """专旺格 L1：地支成该五行三合/三会局，且月令属该五行。"""
    if not month_branch or MONTH_BRANCH_TO_WUXING.get(month_branch) != wuxing:
        return False
    return _branch_set_has_ju(branches, wuxing)


def is_tian_di_yuan_qi(stems: List[str], branches: List[str]) -> bool:
    """天地元气格 L1（宽松）：四柱天干一气或地支一气。"""
    if len(stems) >= 4 and len(set(stems)) == 1 and stems[0]:
        return True
    if len(branches) >= 4 and len(set(branches)) == 1 and branches[0]:
        return True
    return False


def is_tian_di_yuan_qi_strict(stems: List[str], branches: List[str]) -> bool:
    """天地元气格 L1（严格）：天干四字完全相同且地支四字完全相同（天地同流）。"""
    if len(stems) < 4 or len(branches) < 4:
        return False
    if not stems[0] or not branches[0]:
        return False
    return len(set(stems)) == 1 and len(set(branches)) == 1


def is_liang_shen_cheng_xiang(stems: List[str], branches: List[str]) -> bool:
    """两神成象格 L1：全局仅两种五行且力量对等（允许 4:6 内）。"""
    counts = _wuxing_counts(stems, branches)
    non_zero = [(k, v) for k, v in counts.items() if v > 0]
    if len(non_zero) != 2:
        return False
    a, b = non_zero[0][1], non_zero[1][1]
    total = a + b
    if total < 4:
        return False
    return 0.35 <= a / total <= 0.65


def l1_match_a21_through_a30(case: Dict[str, Any], *, strict_a29: bool = False) -> List[str]:
    """对单条 case 应用 A-21～A-30 的 L1 过滤器，返回命中的 pattern_id 列表。
    strict_a29=True 时 A-29 采用「天地同流」严格判定（四干同且四支同）。"""
    out: List[str] = []
    stems, branches, day_master, month_branch, _, _ = _bazi_to_pillars(case)
    if len(stems) < 4 or len(branches) < 4:
        return out

    if is_cong_qiang(case):
        out.append("A-21")
    if is_cong_ruo(case, day_master, branches):
        out.append("A-22")
    if is_cong_er(case):
        out.append("A-23")
    if is_special_wang(branches, month_branch, "金"):
        out.append("A-24")
    if is_special_wang(branches, month_branch, "水"):
        out.append("A-25")
    if is_special_wang(branches, month_branch, "火"):
        out.append("A-26")
    if is_special_wang(branches, month_branch, "木"):
        out.append("A-27")
    if is_special_wang(branches, month_branch, "土"):
        out.append("A-28")
    if strict_a29:
        if is_tian_di_yuan_qi_strict(stems, branches):
            out.append("A-29")
    else:
        if is_tian_di_yuan_qi(stems, branches):
            out.append("A-29")
    if is_liang_shen_cheng_xiang(stems, branches):
        out.append("A-30")

    return out


def l1_match_all_v57(case: Dict[str, Any], tier: int = 1) -> List[str]:
    """tier=1 仅 A-14～A-20，tier=2 仅 A-21～A-30，tier=0 或 3 为全部。"""
    if tier == 1:
        return l1_match_a14_through_a20(case)
    if tier == 2:
        return l1_match_a21_through_a30(case)
    return l1_match_a14_through_a20(case) + l1_match_a21_through_a30(case)
