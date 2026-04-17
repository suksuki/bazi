"""
V17.27：十神绝对能量强度引擎（L0 层）。

废弃旧式「最强值拉到固定上限」的归一化思路，改为物理常数驱动：
- 天干基础常数 = 10.0
- 地支基础常数 = 12.0（按藏干占比分配）
- 月令主气对同属性十神做绝对放大
- 通根 / 透干按结构关系加成
- 空亡按绝对能量折减
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


# ── 天干基础表 ─────────────────────────────────────────────────────────────────

STEM_ELEMENT: Dict[str, str] = {
    "甲": "木", "乙": "木",
    "丙": "火", "丁": "火",
    "戊": "土", "己": "土",
    "庚": "金", "辛": "金",
    "壬": "水", "癸": "水",
}

# True = 阴干（乙丁己辛癸），False = 阳干
STEM_YIN: Dict[str, bool] = {
    "甲": False, "乙": True,
    "丙": False, "丁": True,
    "戊": False, "己": True,
    "庚": False, "辛": True,
    "壬": False, "癸": True,
}

# 五行相生循环（木→火→土→金→水→木）
ELEMENT_CYCLE: List[str] = ["木", "火", "土", "金", "水"]

# ── 地支藏干表（主气 + 余气权重之和 = 1.0）──────────────────────────────────

BRANCH_HIDDEN: Dict[str, List[Tuple[str, float]]] = {
    "子": [("壬", 0.70), ("癸", 0.30)],
    "丑": [("己", 0.60), ("癸", 0.20), ("辛", 0.20)],
    "寅": [("甲", 0.70), ("丙", 0.20), ("戊", 0.10)],
    "卯": [("乙", 0.90), ("甲", 0.10)],
    "辰": [("戊", 0.60), ("乙", 0.20), ("癸", 0.20)],
    "巳": [("丙", 0.70), ("庚", 0.20), ("戊", 0.10)],
    "午": [("丁", 0.70), ("己", 0.30)],
    "未": [("己", 0.60), ("丁", 0.20), ("乙", 0.20)],
    "申": [("庚", 0.70), ("壬", 0.20), ("戊", 0.10)],
    "酉": [("辛", 0.90), ("庚", 0.10)],
    "戌": [("戊", 0.60), ("辛", 0.20), ("丁", 0.20)],
    "亥": [("壬", 0.70), ("甲", 0.30)],
}

STEM_BASE_ENERGY: float = 10.0
BRANCH_BASE_ENERGY: float = 12.0
MONTH_COMMAND_AMPLIFIER: float = 4.0
ROOTED_STEM_GAIN: float = 1.5
EXPOSED_HIDDEN_GAIN: float = 1.2
VOID_REDUCTION_FACTOR: float = 0.4
LUCK_PILLAR_FACTOR: float = 0.85
FLOW_PILLAR_FACTOR: float = 0.65
ENERGY_MIN: float = 0.01


def ten_god_from_stems(daymaster: str, target: str) -> str:
    """根据日主天干与目标天干推算十神名称。"""
    dm_el = STEM_ELEMENT.get(daymaster, "")
    tg_el = STEM_ELEMENT.get(target, "")
    if not dm_el or not tg_el:
        return "比肩"
    dm_yin = STEM_YIN.get(daymaster, False)
    tg_yin = STEM_YIN.get(target, False)
    dm_idx = ELEMENT_CYCLE.index(dm_el)
    produces = ELEMENT_CYCLE[(dm_idx + 1) % 5]    # 日主所生（食伤）
    produced_by = ELEMENT_CYCLE[(dm_idx - 1) % 5] # 生日主（印枭）
    controls = ELEMENT_CYCLE[(dm_idx + 2) % 5]    # 日主所克（财）
    controlled_by = ELEMENT_CYCLE[(dm_idx - 2) % 5] # 克日主（官杀）

    if tg_el == dm_el:
        return "劫财" if tg_yin != dm_yin else "比肩"
    if tg_el == produces:
        return "伤官" if tg_yin != dm_yin else "食神"
    if tg_el == produced_by:
        return "偏印" if tg_yin == dm_yin else "正印"
    if tg_el == controls:
        return "偏财" if tg_yin == dm_yin else "正财"
    if tg_el == controlled_by:
        return "七杀" if tg_yin == dm_yin else "正官"
    return "比肩"  # fallback


def _parse_gz(gz: str) -> Tuple[str, str]:
    """解析干支字符串，返回 (天干, 地支)；不足 2 字时返回 ('', '')。"""
    s = str(gz or "").strip()
    if len(s) < 2:
        return "", ""
    return s[0], s[1]


def _get_xun_kong_map(
    *,
    birth_time: Optional[Any],
    four_pillars: Dict[str, str],
) -> Dict[str, str]:
    """
    优先从 lunar_python 读取四柱旬空；失败时退化为空。
    仅四柱支持空亡折减，大运/流年暂不纳入。
    """
    if birth_time is None:
        return {}
    try:
        from lunar_python import Lunar

        lunar = Lunar.fromDate(birth_time)
        ec = lunar.getEightChar()
        return {
            "year": str(ec.getYearXunKong() or "").strip(),
            "month": str(ec.getMonthXunKong() or "").strip(),
            "day": str(ec.getDayXunKong() or "").strip(),
            "hour": str(ec.getTimeXunKong() or "").strip(),
        }
    except Exception:
        _ = four_pillars
        return {}


def _collect_visible_stems(four_pillars: Dict[str, str], luck_pillar: str, flow_pillar: str) -> List[str]:
    stems: List[str] = []
    for key in ("year", "month", "day", "hour"):
        stem, _ = _parse_gz(str(four_pillars.get(key, "")).strip())
        if stem:
            stems.append(stem)
    for gz in (luck_pillar, flow_pillar):
        stem, _ = _parse_gz(gz)
        if stem:
            stems.append(stem)
    return stems


def _collect_rooted_stems(four_pillars: Dict[str, str], luck_pillar: str, flow_pillar: str) -> set[str]:
    rooted: set[str] = set()
    for key in ("year", "month", "day", "hour"):
        _, branch = _parse_gz(str(four_pillars.get(key, "")).strip())
        for hidden_stem, _h_w in BRANCH_HIDDEN.get(branch, []):
            rooted.add(hidden_stem)
    for gz in (luck_pillar, flow_pillar):
        _, branch = _parse_gz(gz)
        for hidden_stem, _h_w in BRANCH_HIDDEN.get(branch, []):
            rooted.add(hidden_stem)
    return rooted


def _void_factor(branch: str, void_branches: str) -> float:
    if branch and void_branches and branch in void_branches:
        return VOID_REDUCTION_FACTOR
    return 1.0


def _accumulate_stem_energy(
    *,
    stem: str,
    daymaster: str,
    source_factor: float,
    rooted_stems: set[str],
    acc: Dict[str, float],
) -> None:
    if not stem:
        return
    energy = STEM_BASE_ENERGY * source_factor
    if stem in rooted_stems:
        energy *= ROOTED_STEM_GAIN
    god = ten_god_from_stems(daymaster, stem)
    acc[god] = acc.get(god, 0.0) + energy


def _accumulate_branch_energy(
    *,
    branch: str,
    daymaster: str,
    source_factor: float,
    void_factor: float,
    visible_stems: List[str],
    acc: Dict[str, float],
) -> None:
    if not branch:
        return
    for hidden_stem, h_w in BRANCH_HIDDEN.get(branch, []):
        energy = BRANCH_BASE_ENERGY * h_w * source_factor * void_factor
        if hidden_stem in visible_stems:
            energy *= EXPOSED_HIDDEN_GAIN
        god = ten_god_from_stems(daymaster, hidden_stem)
        acc[god] = acc.get(god, 0.0) + energy


def calc_deity_scores(
    *,
    four_pillars: Dict[str, str],
    luck_pillar: str = "—",
    flow_pillar: str = "—",
    gender: str = "female",
    birth_time: Optional[Any] = None,
) -> Tuple[Dict[str, float], List[str], float, Dict[str, Any]]:
    """
    计算十神分值。

    参数：
        four_pillars: {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"}
        luck_pillar:  大运干支字符串（"—" 或空字符串表示缺失）
        flow_pillar:  流年干支字符串
        gender:       "male" | "female"

    返回：
        (absolute_scores, top4_ten_gods, total_energy_index, energy_meta)
    """
    day_gz = str(four_pillars.get("day", "")).strip()
    daymaster, _ = _parse_gz(day_gz)
    if not daymaster:
        default: Dict[str, float] = {
            "比肩": 10.0, "食神": 10.0, "正官": 10.0, "正财": 10.0, "正印": 10.0
        }
        return default, list(default)[:4], round(sum(default.values()), 2), {"month_command_god": "", "void_pillars": []}

    acc: Dict[str, float] = {}
    visible_stems = _collect_visible_stems(four_pillars, luck_pillar, flow_pillar)
    rooted_stems = _collect_rooted_stems(four_pillars, luck_pillar, flow_pillar)
    xun_kong_map = _get_xun_kong_map(birth_time=birth_time, four_pillars=four_pillars)
    void_pillars: List[str] = []

    for pillar_key in ("year", "month", "day", "hour"):
        gz = str(four_pillars.get(pillar_key, "")).strip()
        if not gz:
            continue
        stem, branch = _parse_gz(gz)
        pillar_void_factor = _void_factor(branch, xun_kong_map.get(pillar_key, ""))
        if pillar_void_factor < 1.0:
            void_pillars.append(pillar_key)
        if pillar_key == "day":
            _accumulate_stem_energy(
                stem=daymaster,
                daymaster=daymaster,
                source_factor=1.0,
                rooted_stems=rooted_stems,
                acc=acc,
            )
        else:
            _accumulate_stem_energy(
                stem=stem,
                daymaster=daymaster,
                source_factor=1.0,
                rooted_stems=rooted_stems,
                acc=acc,
            )
        _accumulate_branch_energy(
            branch=branch,
            daymaster=daymaster,
            source_factor=1.0,
            void_factor=pillar_void_factor,
            visible_stems=visible_stems,
            acc=acc,
        )

    for gz_val, source_factor in ((luck_pillar, LUCK_PILLAR_FACTOR), (flow_pillar, FLOW_PILLAR_FACTOR)):
        if gz_val and gz_val not in ("—", "-"):
            stem, branch = _parse_gz(gz_val)
            _accumulate_stem_energy(
                stem=stem,
                daymaster=daymaster,
                source_factor=source_factor,
                rooted_stems=rooted_stems,
                acc=acc,
            )
            _accumulate_branch_energy(
                branch=branch,
                daymaster=daymaster,
                source_factor=source_factor,
                void_factor=1.0,
                visible_stems=visible_stems,
                acc=acc,
            )

    month_stem, month_branch = _parse_gz(str(four_pillars.get("month", "")).strip())
    month_command_god = ""
    month_hidden = BRANCH_HIDDEN.get(month_branch, [])
    if month_hidden:
        month_main_stem = month_hidden[0][0]
        month_command_god = ten_god_from_stems(daymaster, month_main_stem)
        if month_command_god:
            acc[month_command_god] = acc.get(month_command_god, 0.0) * MONTH_COMMAND_AMPLIFIER
    elif month_stem:
        month_command_god = ten_god_from_stems(daymaster, month_stem)
        if month_command_god:
            acc[month_command_god] = acc.get(month_command_god, 0.0) * MONTH_COMMAND_AMPLIFIER

    if gender == "male":
        acc["正官"] = acc.get("正官", 0.0) + 1.2
        acc["七杀"] = acc.get("七杀", 0.0) + 0.8
    else:
        acc["食神"] = acc.get("食神", 0.0) + 1.2
        acc["伤官"] = acc.get("伤官", 0.0) + 0.8

    if not acc:
        return {"比肩": STEM_BASE_ENERGY}, ["比肩"], STEM_BASE_ENERGY, {"month_command_god": "", "void_pillars": void_pillars}
    scored = {
        k: round(v, 2)
        for k, v in sorted(acc.items(), key=lambda kv: (-kv[1], kv[0]))
        if v >= ENERGY_MIN
    }
    total_energy_index = round(sum(scored.values()), 2)
    ten_gods = list(scored)[:4]
    return scored, ten_gods, total_energy_index, {
        "month_command_god": month_command_god,
        "void_pillars": void_pillars,
        "void_branches": {k: v for k, v in xun_kong_map.items() if v},
        "constants": {
            "stem_base_energy": STEM_BASE_ENERGY,
            "branch_base_energy": BRANCH_BASE_ENERGY,
            "month_command_amplifier": MONTH_COMMAND_AMPLIFIER,
            "rooted_stem_gain": ROOTED_STEM_GAIN,
            "exposed_hidden_gain": EXPOSED_HIDDEN_GAIN,
            "void_reduction_factor": VOID_REDUCTION_FACTOR,
        },
    }
