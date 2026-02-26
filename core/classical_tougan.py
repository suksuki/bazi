# core/classical_tougan.py
"""
第 048 号纠偏：古典格局「提纲 + 透干」L1 硬约束
================================================
《子平真诠》《三命通会》《渊海子平》成格逻辑：月令所藏不透出天干则力量潜伏，不能轻易论格。
本模块提供：月令本气、透干判定、十二长生（禄刃），供 build_a01_full_index 与 fds_pattern_scanner 使用。
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional, Set

STEMS = "甲乙丙丁戊己庚辛壬癸"
BRANCHES = "子丑寅卯辰巳午未申酉戌亥"

# 十神名 -> manifest 代码 (与 registry manifest ten_gods 顺序一致)
TEN_GOD_TO_CODE = {
    "zheng_guan": "ZG",
    "qi_sha": "PG",
    "zheng_cai": "ZR",
    "pian_cai": "PR",
    "shi_shen": "ZS",
    "shang_guan": "PS",
    "zheng_yin": "ZC",
    "pian_yin": "PC",
    "bi_jian": "ZB",
    "jie_cai": "PB",
}


def _get_month_main_stem(branch: str) -> Optional[str]:
    """月支本气天干（提纲）。辰戌丑未取墓库主气。"""
    from core.constants import HIDDEN_STEMS_MAP
    if not branch or branch not in HIDDEN_STEMS_MAP:
        return None
    entry = HIDDEN_STEMS_MAP[branch]
    if isinstance(entry, dict) and "main" in entry:
        return entry["main"]
    return None


def get_ten_god_code(dm_stem: str, target_stem: str) -> str:
    """日干对某天干的十神，返回 manifest 用代码 ZG/PG/..."""
    if dm_stem not in STEMS or target_stem not in STEMS:
        return ""
    dm_idx = STEMS.index(dm_stem)
    target_idx = STEMS.index(target_stem)
    dm_pol = dm_idx % 2
    target_pol = target_idx % 2
    same_pol = (dm_pol == target_pol)
    rel = ((target_idx // 2) - (dm_idx // 2)) % 5
    mapping = {
        (0, True): "ZB",
        (0, False): "PB",
        (1, True): "ZS",
        (1, False): "PS",
        (2, True): "PR",
        (2, False): "ZR",
        (3, True): "PG",
        (3, False): "ZG",
        (4, True): "PC",
        (4, False): "ZC",
    }
    return mapping.get((rel, same_pol), "")


# 十二长生表（与 engine_graph.constants 一致，避免导入链拉取 lunar_python）
_TWELVE_LIFE_STAGES = {
    ("甲", "亥"): "长生", ("甲", "子"): "沐浴", ("甲", "丑"): "冠带", ("甲", "寅"): "临官",
    ("甲", "卯"): "帝旺", ("甲", "辰"): "衰", ("甲", "巳"): "病", ("甲", "午"): "死",
    ("甲", "未"): "墓", ("甲", "申"): "绝", ("甲", "酉"): "胎", ("甲", "戌"): "养",
    ("乙", "午"): "长生", ("乙", "巳"): "沐浴", ("乙", "辰"): "冠带", ("乙", "卯"): "临官",
    ("乙", "寅"): "帝旺", ("乙", "丑"): "衰", ("乙", "子"): "病", ("乙", "亥"): "死",
    ("乙", "戌"): "墓", ("乙", "酉"): "绝", ("乙", "申"): "胎", ("乙", "未"): "养",
    ("丙", "寅"): "长生", ("丙", "卯"): "沐浴", ("丙", "辰"): "冠带", ("丙", "巳"): "临官",
    ("丙", "午"): "帝旺", ("丙", "未"): "衰", ("丙", "申"): "病", ("丙", "酉"): "死",
    ("丙", "戌"): "墓", ("丙", "亥"): "绝", ("丙", "子"): "胎", ("丙", "丑"): "养",
    ("丁", "酉"): "长生", ("丁", "申"): "沐浴", ("丁", "未"): "冠带", ("丁", "午"): "临官",
    ("丁", "巳"): "帝旺", ("丁", "辰"): "衰", ("丁", "卯"): "病", ("丁", "寅"): "死",
    ("丁", "丑"): "墓", ("丁", "子"): "绝", ("丁", "亥"): "胎", ("丁", "戌"): "养",
    ("戊", "寅"): "长生", ("戊", "卯"): "沐浴", ("戊", "辰"): "冠带", ("戊", "巳"): "临官",
    ("戊", "午"): "帝旺", ("戊", "未"): "衰", ("戊", "申"): "病", ("戊", "酉"): "死",
    ("戊", "戌"): "墓", ("戊", "亥"): "绝", ("戊", "子"): "胎", ("戊", "丑"): "养",
    ("己", "酉"): "长生", ("己", "申"): "沐浴", ("己", "未"): "冠带", ("己", "午"): "临官",
    ("己", "巳"): "帝旺", ("己", "辰"): "衰", ("己", "卯"): "病", ("己", "寅"): "死",
    ("己", "丑"): "墓", ("己", "子"): "绝", ("己", "亥"): "胎", ("己", "戌"): "养",
    ("庚", "巳"): "长生", ("庚", "午"): "沐浴", ("庚", "未"): "冠带", ("庚", "申"): "临官",
    ("庚", "酉"): "帝旺", ("庚", "戌"): "衰", ("庚", "亥"): "病", ("庚", "子"): "死",
    ("庚", "丑"): "墓", ("庚", "寅"): "绝", ("庚", "卯"): "胎", ("庚", "辰"): "养",
    ("辛", "子"): "长生", ("辛", "亥"): "沐浴", ("辛", "戌"): "冠带", ("辛", "酉"): "临官",
    ("辛", "申"): "帝旺", ("辛", "未"): "衰", ("辛", "午"): "病", ("辛", "巳"): "死",
    ("辛", "辰"): "墓", ("辛", "卯"): "绝", ("辛", "寅"): "胎", ("辛", "丑"): "养",
    ("壬", "申"): "长生", ("壬", "酉"): "沐浴", ("壬", "戌"): "冠带", ("壬", "亥"): "临官",
    ("壬", "子"): "帝旺", ("壬", "丑"): "衰", ("壬", "寅"): "病", ("壬", "卯"): "死",
    ("壬", "辰"): "墓", ("壬", "巳"): "绝", ("壬", "午"): "胎", ("壬", "未"): "养",
    ("癸", "卯"): "长生", ("癸", "寅"): "沐浴", ("癸", "丑"): "冠带", ("癸", "子"): "临官",
    ("癸", "亥"): "帝旺", ("癸", "戌"): "衰", ("癸", "酉"): "病", ("癸", "申"): "死",
    ("癸", "未"): "墓", ("癸", "午"): "绝", ("癸", "巳"): "胎", ("癸", "辰"): "养",
}


def get_twelve_stage(day_master_stem: str, branch: str) -> str:
    """日干在月支的十二长生状态。"""
    key = (day_master_stem, branch)
    return _TWELVE_LIFE_STAGES.get(key, "")


def _bazi_to_stems_branches(bazi: Dict[str, Any]) -> tuple:
    """从 case['bazi'] 提取四柱天干、地支、日干。支持 year/month/day/hour 为 "甲子" 或 {"gan":"甲","zhi":"子"}。"""
    stems: List[str] = []
    branches: List[str] = []
    for pillar_name in ("year", "month", "day", "hour"):
        p = bazi.get(pillar_name)
        if not p:
            stems.append("")
            branches.append("")
            continue
        if isinstance(p, str) and len(p) >= 2:
            stems.append(p[0])
            branches.append(p[1])
        elif isinstance(p, dict):
            stems.append(p.get("gan") or p.get("stem") or "")
            branches.append(p.get("zhi") or p.get("branch") or "")
        else:
            stems.append("")
            branches.append("")
    day_master = stems[2] if len(stems) > 2 else ""
    return stems, branches, day_master


def enrich_case_with_classical_l1(case: Dict[str, Any]) -> Dict[str, Any]:
    """
    为 case 注入 048 古典 L1 字段，供 JsonLogic / is_classical_pattern_achieved 使用。
    注入字段：month_main_god, stems_revealed, month_stage（仅当有 bazi 时）。
    """
    case = dict(case)
    bazi = case.get("bazi")
    if not bazi or not isinstance(bazi, dict):
        case.setdefault("month_main_god", "")
        case.setdefault("stems_revealed", [])
        case.setdefault("month_stage", "")
        return case
    stems, branches, day_master = _bazi_to_stems_branches(bazi)
    month_branch = branches[1] if len(branches) > 1 else ""
    month_main_stem = _get_month_main_stem(month_branch)
    month_main_god = get_ten_god_code(day_master, month_main_stem) if month_main_stem and day_master else ""
    stems_revealed = []
    for s in stems:
        if s and day_master:
            code = get_ten_god_code(day_master, s)
            if code and code not in stems_revealed:
                stems_revealed.append(code)
    month_stage = get_twelve_stage(day_master, month_branch) if day_master and month_branch else ""
    case["month_main_god"] = month_main_god
    case["stems_revealed"] = stems_revealed
    case["month_stage"] = month_stage
    return case


def is_classical_pattern_achieved(case: Dict[str, Any], pattern_id: str) -> bool:
    """
    第 048 号判准：提纲（月令为该十神）+ 透干（该十神在天干中出现）。
    A-09/A-10 使用十二长生（临官/帝旺）。无 bazi 时回退为 False（不通过古典硬约束）。
    """
    pattern_id = (pattern_id or "").strip().upper()
    bazi = case.get("bazi")
    if not bazi or not isinstance(bazi, dict):
        return False
    stems, branches, day_master = _bazi_to_stems_branches(bazi)
    month_branch = branches[1] if len(branches) > 1 else ""
    month_main_stem = _get_month_main_stem(month_branch)
    month_main_god = get_ten_god_code(day_master, month_main_stem) if month_main_stem and day_master else ""
    stems_revealed_set: Set[str] = set()
    for s in stems:
        if s and day_master:
            code = get_ten_god_code(day_master, s)
            if code:
                stems_revealed_set.add(code)
    month_stage = get_twelve_stage(day_master, month_branch) if day_master and month_branch else ""

    # 禄刃：以地支位能为纲
    if pattern_id == "A-09":
        return month_stage == "临官"
    if pattern_id == "A-10":
        # 阳刃：月支为日干帝旺，通常指五阳干
        yang_stems = {"甲", "丙", "戊", "庚", "壬"}
        return month_stage == "帝旺" and day_master in yang_stems

    # 官杀印食伤财：提纲 + 透干
    required_god = {
        "A-01": "ZG",
        "A-02": "PG",
        "A-05": "PC",
        "A-06": "ZS",
        "A-07": "PS",
        "A-08": "ZC",
        "A-03": None,  # 财格单独处理
        "A-04": None,
    }.get(pattern_id)
    if required_god:
        if month_main_god != required_god:
            return False
        if required_god not in stems_revealed_set:
            return False
        if pattern_id == "A-05":
            # 枭神格：且命局见食神（形成夺之势）
            tg = case.get("ten_gods") or {}
            if (tg.get("ZS", 0) or 0) < 0.5:
                return False
        if pattern_id == "A-06":
            # 食神格：未见枭神过度
            tg = case.get("ten_gods") or {}
            if (tg.get("PC", 0) or 0) >= (tg.get("ZS", 0) or 0):
                return False
        return True

    # A-03 / A-04 财格：月令财星司权（正财/偏财）+ 透干 + 身财两停 M>1.2
    if pattern_id == "A-03":
        if month_main_god != "PR" or "PR" not in stems_revealed_set:
            return False
        tg = case.get("ten_gods") or {}
        m_axis = (tg.get("ZR", 0) or 0) + (tg.get("PR", 0) or 0)
        return m_axis > 1.2
    if pattern_id == "A-04":
        if month_main_god != "ZR" or "ZR" not in stems_revealed_set:
            return False
        tg = case.get("ten_gods") or {}
        m_axis = (tg.get("ZR", 0) or 0) + (tg.get("PR", 0) or 0)
        return m_axis > 1.2

    # A-11 / A-12 / A-13 极端格：不在此做透干硬约束，由 manifest pipeline 负责
    return True
