"""
V17.30：十神绝对能量强度引擎（L0 层 — Mass Phase）。

彻底废弃任何「归一化到 100」思路，引擎输出纯物理绝对能量（单位：Qi）。
- 天干基础常数 STEM_BASE = 10.0
- 地支基础常数 BRANCH_BASE = 12.0（按藏干占比分配）
- 月令只放大月支自身的藏干能量；透干/通根联动交给根气机制处理
- 天干通根地支 → Energy *= 1.5
- 地支透出天干 → Energy *= 1.2
- 所在支空亡   → Energy *= 0.4

术语口径：
- 通根只定义为「天干 <- 地支藏干」的支撑关系，主体始终是天干。
- 透干只定义为「地支藏干 -> 天干显影」的显化关系，主体始终是地支内层。
- 地支之间不谈“根气”，天干之间不谈“透干”。
- 通根/透干可视为相对概念，但实现必须基于冻结盘面做单次耦合，禁止递归迭代放大。

返回值 `ten_gods_absolute` / `total_energy_index` 均为绝对累加值，
典型范围 50.0 ～ 500.0+，量级与命局旺衰成正比。
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from v17_rebirth.backend.logic.L0_physics_fields.evolution_ledger import EvolutionLedger
from v17_rebirth.backend.logic.L1_atomic_ops.branch_stem_geometry import (
    branches_and_stems_from_runtime_pillars,
    eval_anhe_hits,
    eval_banhe_hits,
    eval_liu_chong_hits,
    eval_liu_hai_hits,
    eval_liu_po_hits,
    eval_liuhe_hits,
    eval_sanhe_hits,
    detect_stem_fusion_cases,
    sanxing_detect_geometry,
)

_log = logging.getLogger(__name__)


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

# ── 地支藏干表（主气 / 中气 / 余气；纯气支仅保留单一本气）────────────────────

BRANCH_HIDDEN: Dict[str, List[Tuple[str, float]]] = {
    "子": [("癸", 1.00)],
    "丑": [("己", 0.60), ("癸", 0.20), ("辛", 0.20)],
    "寅": [("甲", 0.70), ("丙", 0.20), ("戊", 0.10)],
    "卯": [("乙", 1.00)],
    "辰": [("戊", 0.60), ("乙", 0.20), ("癸", 0.20)],
    "巳": [("丙", 0.70), ("庚", 0.20), ("戊", 0.10)],
    "午": [("丁", 0.70), ("己", 0.30)],
    "未": [("己", 0.60), ("丁", 0.20), ("乙", 0.20)],
    "申": [("庚", 0.70), ("壬", 0.20), ("戊", 0.10)],
    "酉": [("辛", 1.00)],
    "戌": [("戊", 0.60), ("辛", 0.20), ("丁", 0.20)],
    "亥": [("壬", 0.70), ("甲", 0.30)],
}

# ── V17.30 物理常数 ────────────────────────────────────────────────────────────

# --- V17 Core Configuration Hook ---
def _get_l0_consts() -> Dict[str, Any]:
    from v17_rebirth.backend.logic.configs.manager import get_v17_constants
    return get_v17_constants().get("L0_FOUNDATION", {})

def _get_l0_val(key: str, default: float) -> float:
    return float(_get_l0_consts().get(key, default))

def _get_guardrail_consts() -> Dict[str, Any]:
    from v17_rebirth.backend.logic.configs.manager import get_v17_constants
    return get_v17_constants().get("PHYSICS_GUARDRAILS", {})

def _get_guardrail_val(key: str, default: float) -> float:
    return float(_get_guardrail_consts().get(key, default))

# ── V17.30 物理常数 (动态延迟加载占位) ────────────────────────────────────────────
STEM_BASE: float = 10.0
BRANCH_BASE: float = 12.0
ROOTED_STEM_GAIN: float = 1.5
EXPOSED_HIDDEN_GAIN: float = 1.2
GAI_TOU_FACTOR: float = 0.85
JIE_JIAO_FACTOR: float = 0.75
VOID_REDUCTION_FACTOR: float = 0.3
LUCK_PILLAR_FACTOR: float = 0.85
FLOW_PILLAR_FACTOR: float = 0.65
ENERGY_MIN: float = 0.1
ENERGY_MAX: float = 1000.0
GLOBAL_DAMPING: float = 0.95
FLOATING_PEER_FACTOR: float = 0.72
UNEXPOSED_MAIN_HIDDEN_FACTOR: float = 0.58
UNEXPOSED_AUX_HIDDEN_FACTOR: float = 0.42
CROSS_POLARITY_ROOT_SUPPORT_FACTOR: float = 0.55
REL_ROOT_BONUS_SANHE: float = 0.22
REL_ROOT_BONUS_SANHUI: float = 0.18
REL_ROOT_BONUS_BANHE: float = 0.16
REL_ROOT_BONUS_LIUHE: float = 0.12
REL_ROOT_BONUS_ANHE: float = 0.08
REL_VISIBLE_STEM_RESONANCE_BANHE: float = 3.8
REL_VISIBLE_STEM_RESONANCE_SANHUI: float = 2.0
REL_VISIBLE_STEM_RESONANCE_LIUHE: float = 1.8
REL_VISIBLE_STEM_RESONANCE_ANHE: float = 1.1
REL_VISIBLE_CROSS_POLARITY_FACTOR: float = 0.82
REL_ROOT_PENALTY_CHONG: float = 0.12
REL_ROOT_PENALTY_HAI: float = 0.08
REL_ROOT_PENALTY_PO: float = 0.06
REL_ROOT_PENALTY_XING: float = 0.07
REL_ROOT_CONTROL_BONUS: float = 0.05
REL_ROOT_CONTROL_PENALTY: float = 0.07

ROOT_SCOPE_WEIGHTS: Dict[str, float] = {
    "year": 0.48,
    "month": 1.0,
    "day": 0.68,
    "hour": 0.82,
    "luck": 0.92,
    "flow": 0.42,
}

# 旧名兼容（供外部 import 使用）
STEM_BASE_ENERGY: float = STEM_BASE
BRANCH_BASE_ENERGY: float = BRANCH_BASE
MONTH_COMMAND_AMPLIFIER: float = 1.0  # 已废弃：旧的一次性乘法放大系数不再使用


# ── 月令令五行 Season Power（月支主气五行 → 当令倍率）──────────────────────

# 月支五行对照表
BRANCH_ELEMENT: Dict[str, str] = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木",
    "辰": "土", "巳": "火", "午": "火", "未": "土",
    "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

NATAL_BRANCH_POSITION_WEIGHTS: Dict[str, float] = {
    "year": 0.72,
    "month": 1.0,
    "day": 0.92,
    "hour": 0.85,
}

# 天干贴身显化权重：
# 只描述“明透离日主有多近、做功有多直接”，不等同于根气。
# 日干本身为十神参照轴，不参与十神计分，因此不在此表里使用。
NATAL_STEM_POSITION_WEIGHTS: Dict[str, float] = {
    "year": 0.72,
    "month": 1.0,
    "hour": 0.85,
}

CHANG_SHENG_STAGES: List[str] = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]

CHANG_SHENG_TABLE: Dict[str, List[str]] = {
    "木": ["亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌"],
    "火": ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"],
    "土": ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"],
    "金": ["巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰"],
    "水": ["申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未"],
}

CHANG_SHENG_BONUS_MAP: Dict[str, float] = {
    "长生": 0.10,
    "沐浴": 0.02,
    "冠带": 0.12,
    "临官": 0.24,
    "帝旺": 0.30,
    "衰": 0.0,
    "病": 0.0,
    "死": 0.0,
    "墓": 0.06,
    "绝": 0.0,
    "胎": 0.03,
    "养": 0.05,
}

# 当令五行的 Season Power 放大倍率
SEASON_POWER_SAME: float = 2.5      # 与月令五行相同 → 得令
SEASON_POWER_GENERATED: float = 1.8  # 月令五行所生 → 次旺
SEASON_POWER_CONTROLLED: float = 1.0 # L0 静态层不再直接压低被克元素，克制交给动态层
SEASON_POWER_DEFAULT: float = 1.0    # 其余（休囚一般）


def _season_multiplier(target_element: str, month_branch: str) -> float:
    """
    根据目标五行与月令地支五行的关系，返回月支内部使用的 Season Power 倍率。
    注意：该倍率只允许作用于「月支自身」的藏干，不能广播到全盘同元素。
    """
    consts = _get_l0_consts()
    s_same = float(consts.get("SEASON_POWER_SAME", 2.5))
    s_gen = float(consts.get("SEASON_POWER_GENERATED", 1.8))
    s_ctrl = max(1.0, float(consts.get("SEASON_POWER_CONTROLLED", 1.0)))
    s_def = 1.0

    month_el = BRANCH_ELEMENT.get(month_branch, "")
    if not month_el or not target_element:
        return s_def
    if target_element == month_el:
        return s_same
    m_idx = ELEMENT_CYCLE.index(month_el) if month_el in ELEMENT_CYCLE else -1
    t_idx = ELEMENT_CYCLE.index(target_element) if target_element in ELEMENT_CYCLE else -1
    if m_idx < 0 or t_idx < 0:
        return s_def
    # 月令所生：月令的下一位 = 被月令生
    if t_idx == (m_idx + 1) % 5:
        return s_gen
    # 月令所克：在 L0 静态层不直接压低本体，只保留“非加成”；
    # 真正的克制、做功、流动，交由 L1/L2 动态层处理。
    if t_idx == (m_idx + 2) % 5:
        return s_ctrl
    return s_def


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


_BANHE_PAIR_TO_ELEMENT: Dict[frozenset[str], str] = {
    frozenset({"申", "子"}): "水",
    frozenset({"子", "辰"}): "水",
    frozenset({"亥", "卯"}): "木",
    frozenset({"卯", "未"}): "木",
    frozenset({"寅", "午"}): "火",
    frozenset({"午", "戌"}): "火",
    frozenset({"巳", "酉"}): "金",
    frozenset({"酉", "丑"}): "金",
}

_SANHUI_GROUPS: Tuple[Tuple[str, str, str, str], ...] = (
    ("寅", "卯", "辰", "木"),
    ("巳", "午", "未", "火"),
    ("申", "酉", "戌", "金"),
    ("亥", "子", "丑", "水"),
)

_LIUHE_PAIR_TO_ELEMENT: Dict[frozenset[str], str] = {
    frozenset({"子", "丑"}): "土",
    frozenset({"寅", "亥"}): "木",
    frozenset({"卯", "戌"}): "火",
    frozenset({"辰", "酉"}): "金",
    frozenset({"巳", "申"}): "水",
    frozenset({"午", "未"}): "土",
}

_ELEMENT_EN_TO_CN: Dict[str, str] = {
    "wood": "木",
    "fire": "火",
    "earth": "土",
    "metal": "金",
    "water": "水",
}

_PAIR_CLOSENESS: Dict[frozenset[str], float] = {
    frozenset({"month", "day"}): 1.18,
    frozenset({"day", "hour"}): 1.02,
    frozenset({"year", "month"}): 0.96,
    frozenset({"month", "luck"}): 1.12,
    frozenset({"luck", "flow"}): 0.84,
    frozenset({"day", "flow"}): 0.72,
    frozenset({"month", "flow"}): 0.79,
    frozenset({"year", "day"}): 0.74,
    frozenset({"hour", "luck"}): 0.77,
}

_CONTROL_ADJ_SCOPE_PAIRS: Tuple[Tuple[str, str], ...] = (
    ("year", "month"),
    ("month", "day"),
    ("day", "hour"),
    ("month", "luck"),
    ("luck", "flow"),
    ("day", "flow"),
)


def _runtime_branch_rows(four_pillars: Dict[str, str], luck_pillar: str, flow_pillar: str) -> List[Tuple[str, str]]:
    rows: List[Tuple[str, str]] = []
    for key in ("year", "month", "day", "hour"):
        _, branch = _parse_gz(str(four_pillars.get(key, "")).strip())
        if branch:
            rows.append((key, branch))
    for key, gz in (("luck", luck_pillar), ("flow", flow_pillar)):
        _, branch = _parse_gz(str(gz or "").strip())
        if branch:
            rows.append((key, branch))
    return rows


def _pillar_pair_closeness(pillar_a: str, pillar_b: str) -> float:
    if not pillar_a or not pillar_b:
        return 0.72
    if pillar_a == pillar_b:
        return 1.0
    key = frozenset({pillar_a, pillar_b})
    if key in _PAIR_CLOSENESS:
        return float(_PAIR_CLOSENESS[key])
    sa = float(ROOT_SCOPE_WEIGHTS.get(pillar_a, 0.6))
    sb = float(ROOT_SCOPE_WEIGHTS.get(pillar_b, 0.6))
    return max(0.62, min(1.0, (sa + sb) * 0.58))


def _pillars_group_closeness(pillars: List[str]) -> float:
    uniq = [p for p in pillars if p]
    if len(uniq) < 2:
        return 0.78
    vals: List[float] = []
    for i in range(len(uniq)):
        for j in range(i + 1, len(uniq)):
            vals.append(_pillar_pair_closeness(uniq[i], uniq[j]))
    if not vals:
        return 0.78
    return max(0.68, min(1.2, sum(vals) / len(vals)))


def _controls_element(src_el: str, dst_el: str) -> bool:
    if src_el not in ELEMENT_CYCLE or dst_el not in ELEMENT_CYCLE:
        return False
    idx = ELEMENT_CYCLE.index(src_el)
    return ELEMENT_CYCLE[(idx + 2) % len(ELEMENT_CYCLE)] == dst_el


def _eval_sanhui_hits(branches: Dict[str, str]) -> List[Dict[str, Any]]:
    present = {str(v) for v in branches.values() if str(v).strip()}
    hits: List[Dict[str, Any]] = []
    if not present:
        return hits
    for b1, b2, b3, element in _SANHUI_GROUPS:
        group = {b1, b2, b3}
        shared = sorted(group.intersection(present))
        if len(shared) < 2:
            continue
        matched = [(p, br) for p, br in branches.items() if br in group]
        pillars = [p for p, _ in matched]
        matched_branches = [br for _, br in matched]
        branch_counts: Dict[str, int] = {}
        for br in matched_branches:
            branch_counts[br] = branch_counts.get(br, 0) + 1
        unique_count = len(set(shared))
        duplicate_count = max(0, len(matched_branches) - unique_count)
        completion = unique_count / 3.0
        strength = (
            0.54
            + completion * 0.46
            + duplicate_count * 0.12
            + max(0.0, _pillars_group_closeness(pillars) - 0.8) * 0.25
        )
        hits.append(
            {
                "group": [b1, b2, b3],
                "matched_branches": matched_branches,
                "pillars": pillars,
                "branch_counts": branch_counts,
                "duplicate_count": duplicate_count,
                "completion": round(completion, 4),
                "strength": round(max(0.0, min(1.55, strength)), 4),
                "element": element,
            }
        )
    return hits


def _relation_apply_branch_delta(
    *,
    branch: str,
    branch_scope_totals: Dict[str, float],
    relation_element: str,
    magnitude: float,
    out: Dict[str, float],
) -> None:
    scope = max(0.0, float(branch_scope_totals.get(branch, 0.0)))
    if scope <= 0.0 or abs(magnitude) <= 1e-9:
        return
    rel_el = str(relation_element or "")
    for hidden_stem, hidden_weight in BRANCH_HIDDEN.get(branch, []):
        stem_el = STEM_ELEMENT.get(hidden_stem, "")
        focus = 1.0
        if rel_el:
            if stem_el == rel_el:
                focus = 1.35
            else:
                focus = 0.55
        delta = float(hidden_weight) * scope * float(magnitude) * focus
        out[hidden_stem] = out.get(hidden_stem, 0.0) + delta


def _relation_apply_stem_element_delta(
    *,
    target_element: str,
    magnitude: float,
    rooted_static: Dict[str, float],
    out: Dict[str, float],
) -> None:
    rel_el = str(target_element or "")
    if not rel_el or abs(magnitude) <= 1e-9:
        return
    for stem, base_strength in rooted_static.items():
        if STEM_ELEMENT.get(stem, "") != rel_el:
            continue
        # 天干五合的“化学效率”只做温和折算，避免替代静态根气主干。
        stem_delta = float(magnitude) * (0.65 + min(1.0, max(0.0, float(base_strength))) * 0.35)
        out[stem] = out.get(stem, 0.0) + stem_delta


def _collect_root_strengths_with_meta(
    four_pillars: Dict[str, str],
    luck_pillar: str,
    flow_pillar: str,
) -> Tuple[Dict[str, float], Dict[str, Any]]:
    """
    根气分为两部分：
    1) 静态根气：藏干×柱位作用域；
    2) 动态根气：刑冲克害合 + 天干五合效率，对静态根气做温和修正。
    """
    rooted: Dict[str, float] = {}
    branch_rows = _runtime_branch_rows(four_pillars, luck_pillar, flow_pillar)
    branches: Dict[str, str] = {scope: branch for scope, branch in branch_rows}
    stems: Dict[str, str] = {}
    for key in ("year", "month", "day", "hour"):
        stem, _ = _parse_gz(str(four_pillars.get(key, "")).strip())
        if stem:
            stems[key] = stem
    for key, gz in (("luck", luck_pillar), ("flow", flow_pillar)):
        stem, _ = _parse_gz(str(gz or "").strip())
        if stem:
            stems[key] = stem

    branch_scope_totals: Dict[str, float] = {}
    for scope_key, branch in branch_rows:
        scope = float(ROOT_SCOPE_WEIGHTS.get(scope_key, 0.5))
        branch_scope_totals[branch] = branch_scope_totals.get(branch, 0.0) + scope
        for hidden_stem, hidden_weight in BRANCH_HIDDEN.get(branch, []):
            rooted[hidden_stem] = rooted.get(hidden_stem, 0.0) + float(hidden_weight) * scope

    static_rooted = dict(rooted)
    relation_delta_raw: Dict[str, float] = {}
    relation_traces: List[Dict[str, Any]] = []

    def _trace(kind: str, members: List[str], pillars: List[str], intensity: float, relation_element: str = "") -> None:
        relation_traces.append(
            {
                "kind": kind,
                "members": [str(x) for x in members if str(x).strip()],
                "pillars": [str(x) for x in pillars if str(x).strip()],
                "intensity": round(float(intensity), 4),
                "relation_element": str(relation_element or ""),
            }
        )

    if branches:
        sanhe_hits = eval_sanhe_hits(branches)
        sanhui_hits = _eval_sanhui_hits(branches)
        banhe_hits = eval_banhe_hits(branches)
        liuhe_hits = eval_liuhe_hits(branches)
        anhe_hits = eval_anhe_hits(branches)
        chong_hits = eval_liu_chong_hits(branches)
        hai_hits = eval_liu_hai_hits(branches)
        po_hits = eval_liu_po_hits(branches)
        xing_hits = sanxing_detect_geometry(branches)
        conflicted_branches: set[str] = set()
        for hit in chong_hits:
            conflicted_branches.update([str(x) for x in (hit.get("pair") or []) if str(x).strip()])
        for hit in hai_hits:
            conflicted_branches.update([str(x) for x in (hit.get("pair") or []) if str(x).strip()])
        for hit in po_hits:
            conflicted_branches.update([str(x) for x in (hit.get("pair") or []) if str(x).strip()])
        for hit in xing_hits:
            conflicted_branches.update([str(x) for x in (hit.get("branches") or []) if str(x).strip()])

        def _conflict_damping(members: List[str]) -> float:
            uniq = [m for m in set(members) if m]
            if not uniq:
                return 1.0
            conflict_ratio = sum(1 for m in uniq if m in conflicted_branches) / len(uniq)
            return max(0.52, 1.0 - 0.34 * conflict_ratio)

        for hit in sanhe_hits:
            members = [str(b) for b in (hit.get("matched_branches") or hit.get("group") or []) if str(b).strip()]
            if not members:
                continue
            pillars = [str(p) for p in (hit.get("pillars") or []) if str(p).strip()]
            closeness = _pillars_group_closeness(pillars)
            strength = float(hit.get("strength") or 1.0)
            base = _get_l0_val("REL_ROOT_BONUS_SANHE", REL_ROOT_BONUS_SANHE)
            intensity = base * closeness * max(0.75, strength) * _conflict_damping(members)
            mid_branch = str(hit.get("mid_branch") or "")
            rel_element = ""
            if mid_branch and BRANCH_HIDDEN.get(mid_branch):
                rel_element = STEM_ELEMENT.get(BRANCH_HIDDEN[mid_branch][0][0], "")
            counts = hit.get("branch_counts") or {}
            for branch in set(members):
                dup_factor = 1.0 + 0.16 * max(0, int((counts.get(branch) or 1) - 1))
                _relation_apply_branch_delta(
                    branch=branch,
                    branch_scope_totals=branch_scope_totals,
                    relation_element=rel_element,
                    magnitude=intensity * dup_factor,
                    out=relation_delta_raw,
                )
            _trace("sanhe", members, pillars, intensity, rel_element)

        for hit in sanhui_hits:
            members = [str(b) for b in (hit.get("matched_branches") or hit.get("group") or []) if str(b).strip()]
            if not members:
                continue
            pillars = [str(p) for p in (hit.get("pillars") or []) if str(p).strip()]
            closeness = _pillars_group_closeness(pillars)
            completion = max(0.0, min(1.0, float(hit.get("completion") or 0.0)))
            strength = max(0.0, float(hit.get("strength") or 0.0))
            duplicate_count = max(0, int(hit.get("duplicate_count") or 0))
            side_branch_bonus = 1.0 + 0.1 * duplicate_count
            base = _get_l0_val("REL_ROOT_BONUS_SANHUI", REL_ROOT_BONUS_SANHUI)
            intensity = (
                base
                * closeness
                * max(0.7, completion + 0.22)
                * max(0.72, min(1.35, strength))
                * side_branch_bonus
                * _conflict_damping(members)
            )
            rel_element = str(hit.get("element") or "")
            counts = hit.get("branch_counts") or {}
            for branch in set(members):
                dup_factor = 1.0 + 0.12 * max(0, int((counts.get(branch) or 1) - 1))
                _relation_apply_branch_delta(
                    branch=branch,
                    branch_scope_totals=branch_scope_totals,
                    relation_element=rel_element,
                    magnitude=intensity * dup_factor,
                    out=relation_delta_raw,
                )
            _trace("sanhui", members, pillars, intensity, rel_element)

        for hit in banhe_hits:
            pair = [str(x) for x in (hit.get("pair") or []) if str(x).strip()]
            if len(pair) != 2:
                continue
            pillars = [str(p) for p in (hit.get("pillars") or []) if str(p).strip()]
            closeness = _pillars_group_closeness(pillars)
            base = _get_l0_val("REL_ROOT_BONUS_BANHE", REL_ROOT_BONUS_BANHE)
            rel_element = _BANHE_PAIR_TO_ELEMENT.get(frozenset(pair), "")
            intensity = base * closeness * _conflict_damping(pair)
            for branch in pair:
                _relation_apply_branch_delta(
                    branch=branch,
                    branch_scope_totals=branch_scope_totals,
                    relation_element=rel_element,
                    magnitude=intensity,
                    out=relation_delta_raw,
                )
            _trace("banhe", pair, pillars, intensity, rel_element)

        for hit in liuhe_hits:
            pair = [str(x) for x in (hit.get("pair") or []) if str(x).strip()]
            if len(pair) != 2:
                continue
            pillars = [str(p) for p in (hit.get("pillars") or []) if str(p).strip()]
            closeness = _pillars_group_closeness(pillars)
            base = _get_l0_val("REL_ROOT_BONUS_LIUHE", REL_ROOT_BONUS_LIUHE)
            rel_element = _LIUHE_PAIR_TO_ELEMENT.get(frozenset(pair), "")
            intensity = base * closeness * _conflict_damping(pair)
            for branch in pair:
                _relation_apply_branch_delta(
                    branch=branch,
                    branch_scope_totals=branch_scope_totals,
                    relation_element=rel_element,
                    magnitude=intensity,
                    out=relation_delta_raw,
                )
            _trace("liuhe", pair, pillars, intensity, rel_element)

        for hit in anhe_hits:
            pair = [str(x) for x in (hit.get("pair") or []) if str(x).strip()]
            if len(pair) != 2:
                continue
            pillars = [str(p) for p in (hit.get("pillars") or []) if str(p).strip()]
            closeness = _pillars_group_closeness(pillars)
            base = _get_l0_val("REL_ROOT_BONUS_ANHE", REL_ROOT_BONUS_ANHE)
            intensity = base * closeness * _conflict_damping(pair)
            for branch in pair:
                _relation_apply_branch_delta(
                    branch=branch,
                    branch_scope_totals=branch_scope_totals,
                    relation_element="",
                    magnitude=intensity,
                    out=relation_delta_raw,
                )
            _trace("anhe", pair, pillars, intensity, "")

        for kind, hits, cfg_key, dft in (
            ("chong", chong_hits, "REL_ROOT_PENALTY_CHONG", REL_ROOT_PENALTY_CHONG),
            ("hai", hai_hits, "REL_ROOT_PENALTY_HAI", REL_ROOT_PENALTY_HAI),
            ("po", po_hits, "REL_ROOT_PENALTY_PO", REL_ROOT_PENALTY_PO),
        ):
            for hit in hits:
                pair = [str(x) for x in (hit.get("pair") or []) if str(x).strip()]
                if len(pair) != 2:
                    continue
                pillars = [str(p) for p in (hit.get("pillars") or []) if str(p).strip()]
                closeness = _pillars_group_closeness(pillars)
                intensity = -_get_l0_val(cfg_key, dft) * closeness
                for branch in pair:
                    _relation_apply_branch_delta(
                        branch=branch,
                        branch_scope_totals=branch_scope_totals,
                        relation_element="",
                        magnitude=intensity,
                        out=relation_delta_raw,
                    )
                _trace(kind, pair, pillars, intensity, "")

        for hit in xing_hits:
            members = [str(b) for b in (hit.get("branches") or []) if str(b).strip()]
            if len(members) < 2:
                continue
            pillars = [str(p) for p in (hit.get("edge") or []) if str(p).strip()]
            closeness = _pillars_group_closeness(pillars)
            intensity = -_get_l0_val("REL_ROOT_PENALTY_XING", REL_ROOT_PENALTY_XING) * closeness
            for branch in members:
                _relation_apply_branch_delta(
                    branch=branch,
                    branch_scope_totals=branch_scope_totals,
                    relation_element="",
                    magnitude=intensity,
                    out=relation_delta_raw,
                )
            _trace("xing", members, pillars, intensity, "")

        for p1, p2 in _CONTROL_ADJ_SCOPE_PAIRS:
            b1 = str(branches.get(p1) or "")
            b2 = str(branches.get(p2) or "")
            if not b1 or not b2:
                continue
            e1 = BRANCH_ELEMENT.get(b1, "")
            e2 = BRANCH_ELEMENT.get(b2, "")
            if not e1 or not e2 or e1 == e2:
                continue
            closeness = _pillar_pair_closeness(p1, p2)
            bonus = _get_l0_val("REL_ROOT_CONTROL_BONUS", REL_ROOT_CONTROL_BONUS) * closeness
            penalty = _get_l0_val("REL_ROOT_CONTROL_PENALTY", REL_ROOT_CONTROL_PENALTY) * closeness
            if _controls_element(e1, e2):
                _relation_apply_branch_delta(
                    branch=b1,
                    branch_scope_totals=branch_scope_totals,
                    relation_element=e1,
                    magnitude=bonus,
                    out=relation_delta_raw,
                )
                _relation_apply_branch_delta(
                    branch=b2,
                    branch_scope_totals=branch_scope_totals,
                    relation_element=e2,
                    magnitude=-penalty,
                    out=relation_delta_raw,
                )
                _trace("ke", [b1, b2], [p1, p2], bonus - penalty, f"{e1}克{e2}")
            elif _controls_element(e2, e1):
                _relation_apply_branch_delta(
                    branch=b2,
                    branch_scope_totals=branch_scope_totals,
                    relation_element=e2,
                    magnitude=bonus,
                    out=relation_delta_raw,
                )
                _relation_apply_branch_delta(
                    branch=b1,
                    branch_scope_totals=branch_scope_totals,
                    relation_element=e1,
                    magnitude=-penalty,
                    out=relation_delta_raw,
                )
                _trace("ke", [b2, b1], [p2, p1], bonus - penalty, f"{e2}克{e1}")

        # 天干五合“化学效率”量化：以 branch_hua_ratio 与月干支持作为效率源。
        stem_cases = detect_stem_fusion_cases(stems, branches) if stems else []
        for case in stem_cases:
            mode = str(case.get("mode") or "")
            hua_el_en = str(case.get("hua_element") or "")
            rel_element = _ELEMENT_EN_TO_CN.get(hua_el_en.lower(), "")
            branch_ratio = max(0.0, min(1.0, float(case.get("branch_hua_ratio") or 0.0)))
            month_supports = bool(case.get("month_stem_supports"))
            efficiency = max(0.0, min(1.0, 0.22 + branch_ratio * 0.58 + (0.2 if month_supports else 0.0)))
            pillars = [str(p) for p in (case.get("pillars") or []) if str(p).strip()]
            closeness = _pillars_group_closeness(pillars)
            stems_pair = [str(s) for s in (case.get("stems") or []) if str(s).strip()]
            if mode == "transformed" and rel_element:
                intensity = _get_l0_val("REL_ROOT_BONUS_ANHE", REL_ROOT_BONUS_ANHE) * efficiency * closeness
                _relation_apply_stem_element_delta(
                    target_element=rel_element,
                    magnitude=intensity,
                    rooted_static=static_rooted,
                    out=relation_delta_raw,
                )
                _trace("stem_fusion_transform", stems_pair, pillars, intensity, rel_element)
            elif mode == "stuck":
                intensity = -_get_l0_val("REL_ROOT_PENALTY_PO", REL_ROOT_PENALTY_PO) * efficiency * closeness
                for stem in stems_pair:
                    stem_el = STEM_ELEMENT.get(stem, "")
                    if not stem_el:
                        continue
                    _relation_apply_stem_element_delta(
                        target_element=stem_el,
                        magnitude=intensity * 0.6,
                        rooted_static=static_rooted,
                        out=relation_delta_raw,
                    )
                _trace("stem_fusion_stuck", stems_pair, pillars, intensity, "")

    relation_delta_applied: Dict[str, float] = {}
    for stem, raw_delta in relation_delta_raw.items():
        base = max(0.0, float(static_rooted.get(stem, 0.0)))
        cap_plus = max(0.2, base * 0.55)
        cap_minus = max(0.16, base * 0.45)
        applied = max(-cap_minus, min(cap_plus, float(raw_delta)))
        if abs(applied) <= 1e-9:
            continue
        relation_delta_applied[stem] = applied
        rooted[stem] = max(0.0, rooted.get(stem, 0.0) + applied)

    relation_counts: Dict[str, int] = {}
    for trace in relation_traces:
        kind = str(trace.get("kind") or "")
        relation_counts[kind] = relation_counts.get(kind, 0) + 1

    return rooted, {
        "hits": relation_counts,
        "dynamic_raw": {stem: round(v, 4) for stem, v in sorted(relation_delta_raw.items()) if abs(v) > 1e-9},
        "dynamic_applied": {stem: round(v, 4) for stem, v in sorted(relation_delta_applied.items()) if abs(v) > 1e-9},
        "traces": relation_traces[:48],
    }


def _collect_root_strengths(four_pillars: Dict[str, str], luck_pillar: str, flow_pillar: str) -> Dict[str, float]:
    rooted, _meta = _collect_root_strengths_with_meta(four_pillars, luck_pillar, flow_pillar)
    return rooted


def _cross_polarity_root_support(stem: str, root_strengths: Dict[str, float]) -> float:
    """
    同五行可通根，但若阴阳不匹配，只按折损后的根气计算。
    例如壬水可以从子中癸水通根，但力度弱于癸水对癸水的本根。
    """
    stem_element = STEM_ELEMENT.get(stem, "")
    stem_yin = STEM_YIN.get(stem)
    if not stem_element or stem_yin is None:
        return 0.0
    support = 0.0
    factor = _get_l0_val("CROSS_POLARITY_ROOT_SUPPORT_FACTOR", 0.55)
    for root_stem, strength in root_strengths.items():
        if root_stem == stem:
            continue
        if STEM_ELEMENT.get(root_stem, "") != stem_element:
            continue
        if STEM_YIN.get(root_stem) == stem_yin:
            support += max(0.0, float(strength or 0.0))
        else:
            support += max(0.0, float(strength or 0.0)) * factor
    return support


def _visible_stem_scope_weights(four_pillars: Dict[str, str], luck_pillar: str, flow_pillar: str) -> List[Tuple[str, str]]:
    rows: List[Tuple[str, str]] = []
    for key in ("year", "month", "day", "hour"):
        stem, _ = _parse_gz(str(four_pillars.get(key, "")).strip())
        if stem:
            rows.append((key, stem))
    for scope, gz in (("luck", luck_pillar), ("flow", flow_pillar)):
        stem, _ = _parse_gz(gz)
        if stem:
            rows.append((scope, stem))
    return rows


def _same_element_visible(hidden_stem: str, visible_stems: List[str]) -> bool:
    hidden_element = STEM_ELEMENT.get(hidden_stem, "")
    if not hidden_element:
        return False
    return any(STEM_ELEMENT.get(stem, "") == hidden_element for stem in visible_stems)


def _branch_stage_for_daymaster(daymaster: str, branch: str) -> Tuple[str, float]:
    dm_element = STEM_ELEMENT.get(daymaster, "")
    if not dm_element or not branch:
        return "", 0.0
    table = CHANG_SHENG_TABLE.get(dm_element, [])
    if branch not in table:
        return "", 0.0
    stage = CHANG_SHENG_STAGES[table.index(branch)]
    return stage, float(CHANG_SHENG_BONUS_MAP.get(stage, 0.0))


def _split_stage_component(stage_name: str, stage_component: float) -> Dict[str, float]:
    if stage_component <= 0.0:
        return {
            "momentum_stage_lu": 0.0,
            "momentum_stage_blade": 0.0,
            "momentum_stage_general": 0.0,
        }
    if stage_name == "临官":
        return {
            "momentum_stage_lu": stage_component,
            "momentum_stage_blade": 0.0,
            "momentum_stage_general": 0.0,
        }
    if stage_name == "帝旺":
        return {
            "momentum_stage_lu": 0.0,
            "momentum_stage_blade": stage_component,
            "momentum_stage_general": 0.0,
        }
    return {
        "momentum_stage_lu": 0.0,
        "momentum_stage_blade": 0.0,
        "momentum_stage_general": stage_component,
    }


def _sanhe_branch_role(branch: str, mid_branch: str) -> str:
    if branch == mid_branch:
        return "pivot"
    if branch in {"辰", "戌", "丑", "未"}:
        return "tomb"
    return "starter"


def _sanhe_projection_weights(
    *,
    hit: Dict[str, Any],
    daymaster: str,
    four_pillars: Dict[str, str],
    luck_pillar: str,
    flow_pillar: str,
) -> Dict[str, float]:
    mid_branch = str(hit.get("mid_branch") or "")
    branches = [str(x) for x in (hit.get("matched_branches") or hit.get("group") or []) if str(x).strip()]
    if not branches:
        return {}
    main_hidden = BRANCH_HIDDEN.get(mid_branch, [])
    if not main_hidden:
        return {}
    target_element = STEM_ELEMENT.get(main_hidden[0][0], "")
    if not target_element:
        return {}
    role_weights = {
        "pivot": 1.25,
        "tomb": 0.92,
        "starter": 0.58,
    }
    pillar_weights = {
        "year": 0.88,
        "month": 1.18,
        "day": 0.95,
        "hour": 1.02,
        "luck": 1.16,
        "flow": 0.72,
    }
    branch_occurrences = list(
        zip(
            [str(p) for p in (hit.get("pillars") or []) if str(p).strip()],
            branches,
        )
    )
    weights: Dict[str, float] = {}
    for pillar, branch in branch_occurrences:
        role = _sanhe_branch_role(branch, mid_branch)
        role_weight = float(role_weights.get(role, 0.6))
        pillar_weight = float(pillar_weights.get(pillar, 0.9))
        for hidden_stem, hidden_weight in BRANCH_HIDDEN.get(branch, []):
            if STEM_ELEMENT.get(hidden_stem) != target_element:
                continue
            god = ten_god_from_stems(daymaster, hidden_stem)
            weights[god] = weights.get(god, 0.0) + float(hidden_weight) * role_weight * pillar_weight

    visible_scope_weights = {
        "year": 0.55,
        "month": 0.72,
        "day": 0.45,
        "hour": 0.58,
        # 运上透神对成局后主神定向更强，流年只作引动。
        "luck": 1.35,
        "flow": 0.38,
    }
    for scope, stem in _visible_stem_scope_weights(four_pillars, luck_pillar, flow_pillar):
        if STEM_ELEMENT.get(stem) != target_element:
            continue
        god = ten_god_from_stems(daymaster, stem)
        weights[god] = weights.get(god, 0.0) + float(visible_scope_weights.get(scope, 0.55))

    total = sum(weights.values())
    if total <= 0:
        return {}
    return {god: weight / total for god, weight in weights.items() if weight > 0}


def _apply_sanhe_foundation_bonus(
    *,
    acc: Dict[str, float],
    decomposition: Dict[str, Dict[str, float]],
    daymaster: str,
    four_pillars: Dict[str, str],
    luck_pillar: str,
    flow_pillar: str,
    ledger: EvolutionLedger,
) -> List[Dict[str, Any]]:
    branches, _ = branches_and_stems_from_runtime_pillars(
        four_pillars,
        luck_pillar=luck_pillar,
        flow_pillar=flow_pillar,
    )
    sanhe_hits = eval_sanhe_hits(branches) if branches else []
    bonuses: List[Dict[str, Any]] = []
    if not sanhe_hits:
        return bonuses

    for hit in sanhe_hits:
        strength = float(hit.get("strength") or 1.0)
        duplicate_count = max(0, int(hit.get("duplicate_count") or 0))
        pivot_factor = float(hit.get("pivot_factor") or 0.9)
        projection = _sanhe_projection_weights(
            hit=hit,
            daymaster=daymaster,
            four_pillars=four_pillars,
            luck_pillar=luck_pillar,
            flow_pillar=flow_pillar,
        )
        if not projection:
            continue
        direct_support_strength = max(projection.values()) if projection else 0.0
        bonus_total = (
            _get_l0_val("BRANCH_BASE", 12.0)
            * strength
            * (1.0 + 0.24 * duplicate_count)
            * (1.0 + 0.22 * max(0.0, pivot_factor - 0.9))
            * (1.0 + 0.45 * direct_support_strength)
        )
        bonus_total = max(0.0, bonus_total)
        for god, share in projection.items():
            delta = bonus_total * float(share)
            if not math.isfinite(delta) or delta <= 0.0:
                continue
            acc[god] = acc.get(god, 0.0) + delta
            _add_decomposition(decomposition, god, momentum_structure=delta)
            ledger.append_entry(
                god,
                acc[god],
                "L0_SANHE_FORMATION",
                f"三合成局基础回灌·{''.join(hit.get('group') or [])}·share={share:.2f}·dup={duplicate_count}",
            )
        bonuses.append(
            {
                "group": list(hit.get("group") or []),
                "matched_branches": list(hit.get("matched_branches") or []),
                "mid_branch": str(hit.get("mid_branch") or ""),
                "duplicate_count": duplicate_count,
                "pivot_factor": round(pivot_factor, 3),
                "strength": round(strength, 3),
                "bonus_total": round(bonus_total, 3),
                "projection": {god: round(float(share), 4) for god, share in projection.items()},
            }
        )
    return bonuses


def _relation_visible_scope_weight(scope: str) -> float:
    if scope in NATAL_STEM_POSITION_WEIGHTS:
        return float(NATAL_STEM_POSITION_WEIGHTS.get(scope, 0.72))
    if scope == "luck":
        return float(_get_l0_val("LUCK_PILLAR_FACTOR", 0.85))
    if scope == "flow":
        return float(_get_l0_val("FLOW_PILLAR_FACTOR", 0.65))
    return 0.0


def _relation_dominant_hidden_stem(
    *,
    relation_element: str,
    members: List[str],
    four_pillars: Dict[str, str],
    luck_pillar: str,
    flow_pillar: str,
) -> str:
    if not relation_element or not members:
        return ""
    branch_rows = _runtime_branch_rows(four_pillars, luck_pillar, flow_pillar)
    member_set = {str(member) for member in members if str(member).strip()}
    hidden_totals: Dict[str, float] = {}
    for scope, branch in branch_rows:
        if branch not in member_set:
            continue
        scope_weight = float(ROOT_SCOPE_WEIGHTS.get(scope, 0.5))
        for hidden_stem, hidden_weight in BRANCH_HIDDEN.get(branch, []):
            if STEM_ELEMENT.get(hidden_stem, "") != relation_element:
                continue
            hidden_totals[hidden_stem] = hidden_totals.get(hidden_stem, 0.0) + float(hidden_weight) * scope_weight
    if not hidden_totals:
        return ""
    return max(hidden_totals.items(), key=lambda item: (item[1], item[0]))[0]


def _relation_visible_projection_weights(
    *,
    relation_element: str,
    dominant_hidden_stem: str,
    daymaster: str,
    four_pillars: Dict[str, str],
    luck_pillar: str,
    flow_pillar: str,
) -> Dict[str, float]:
    rel_el = str(relation_element or "")
    if not rel_el:
        return {}
    cross_factor = _get_l0_val("REL_VISIBLE_CROSS_POLARITY_FACTOR", REL_VISIBLE_CROSS_POLARITY_FACTOR)
    weights: Dict[str, float] = {}
    for scope, stem in _visible_stem_scope_weights(four_pillars, luck_pillar, flow_pillar):
        if STEM_ELEMENT.get(stem, "") != rel_el:
            continue
        scope_weight = _relation_visible_scope_weight(scope)
        if scope_weight <= 0.0:
            continue
        polarity_factor = 1.0
        if dominant_hidden_stem and stem != dominant_hidden_stem:
            polarity_factor = cross_factor
        god = ten_god_from_stems(daymaster, stem)
        weights[god] = weights.get(god, 0.0) + scope_weight * polarity_factor
    total = sum(weights.values())
    if total <= 0.0:
        return {}
    return {god: weight / total for god, weight in weights.items() if weight > 0.0}


def _apply_relation_visible_resonance_bonuses(
    *,
    acc: Dict[str, float],
    decomposition: Dict[str, Dict[str, float]],
    daymaster: str,
    four_pillars: Dict[str, str],
    luck_pillar: str,
    flow_pillar: str,
    relation_traces: List[Dict[str, Any]],
    ledger: EvolutionLedger,
) -> List[Dict[str, Any]]:
    bonuses: List[Dict[str, Any]] = []
    scale_defaults = {
        "banhe": REL_VISIBLE_STEM_RESONANCE_BANHE,
        "sanhui": REL_VISIBLE_STEM_RESONANCE_SANHUI,
        "liuhe": REL_VISIBLE_STEM_RESONANCE_LIUHE,
        "anhe": REL_VISIBLE_STEM_RESONANCE_ANHE,
    }
    scale_keys = {
        "banhe": "REL_VISIBLE_STEM_RESONANCE_BANHE",
        "sanhui": "REL_VISIBLE_STEM_RESONANCE_SANHUI",
        "liuhe": "REL_VISIBLE_STEM_RESONANCE_LIUHE",
        "anhe": "REL_VISIBLE_STEM_RESONANCE_ANHE",
    }
    for trace in relation_traces:
        kind = str(trace.get("kind") or "")
        relation_element = str(trace.get("relation_element") or "")
        intensity = float(trace.get("intensity") or 0.0)
        members = [str(x) for x in (trace.get("members") or []) if str(x).strip()]
        if kind not in scale_defaults or not relation_element or intensity <= 0.0 or not members:
            continue
        dominant_hidden_stem = _relation_dominant_hidden_stem(
            relation_element=relation_element,
            members=members,
            four_pillars=four_pillars,
            luck_pillar=luck_pillar,
            flow_pillar=flow_pillar,
        )
        projection = _relation_visible_projection_weights(
            relation_element=relation_element,
            dominant_hidden_stem=dominant_hidden_stem,
            daymaster=daymaster,
            four_pillars=four_pillars,
            luck_pillar=luck_pillar,
            flow_pillar=flow_pillar,
        )
        if not projection:
            continue
        scale = _get_l0_val(scale_keys[kind], scale_defaults[kind])
        bonus_total = max(0.0, _get_l0_val("BRANCH_BASE", 12.0) * intensity * max(0.0, scale))
        if bonus_total <= 0.0:
            continue
        for god, share in projection.items():
            delta = bonus_total * float(share)
            if not math.isfinite(delta) or delta <= 0.0:
                continue
            acc[god] = acc.get(god, 0.0) + delta
            _add_decomposition(decomposition, god, momentum_structure=delta)
            ledger.append_entry(
                god,
                acc[god],
                f"L0_REL_VISIBLE_{kind.upper()}",
                f"{kind}显神导流·{relation_element}→{god}·share={share:.2f}·dominant={dominant_hidden_stem or '—'}",
            )
        bonuses.append(
            {
                "kind": kind,
                "relation_element": relation_element,
                "members": members,
                "dominant_hidden_stem": dominant_hidden_stem,
                "bonus_total": round(bonus_total, 3),
                "projection": {god: round(float(share), 4) for god, share in projection.items()},
            }
        )
    return bonuses


def _void_factor(branch: str, void_branches: str) -> float:
    if branch and void_branches and branch in void_branches:
        return _get_l0_val("VOID_EFFICIENCY", 0.3)
    return 1.0


def _projection_bridge_protocol() -> Dict[str, Any]:
    return {
        "tonggen_direction": "stem<-branch_hidden",
        "tougan_direction": "branch_hidden->visible_stem",
        "same_element_first": True,
        "polarity_second": True,
        "exact_root_support_factor": 1.0,
        "cross_polarity_root_support_factor": _get_l0_val(
            "CROSS_POLARITY_ROOT_SUPPORT_FACTOR",
            CROSS_POLARITY_ROOT_SUPPORT_FACTOR,
        ),
        "exact_exposed_hidden_gain": _get_l0_val("EXPOSED_HIDDEN_GAIN", EXPOSED_HIDDEN_GAIN),
        "same_element_visible_relief": 1.0,
        "rooted_gain_cap": _get_l0_val("ROOTED_GAIN", ROOTED_STEM_GAIN),
        "single_pass_coupling": True,
        "recursive_feedback": False,
        "protocol": "frozen_evidence_single_pass",
    }


def _ensure_decomposition_bucket(
    decomposition: Dict[str, Dict[str, float]],
    god: str,
) -> Dict[str, float]:
    row = decomposition.get(god)
    if isinstance(row, dict):
        return row
    row = {
        "manifest": 0.0,
        "root": 0.0,
        "momentum": 0.0,
        "momentum_month_order": 0.0,
        "momentum_stage": 0.0,
        "momentum_stage_lu": 0.0,
        "momentum_stage_blade": 0.0,
        "momentum_stage_general": 0.0,
        "momentum_structure": 0.0,
        "momentum_auxiliary": 0.0,
        "hidden": 0.0,
        "total": 0.0,
    }
    decomposition[god] = row
    return row


def _add_decomposition(
    decomposition: Dict[str, Dict[str, float]],
    god: str,
    *,
    manifest: float = 0.0,
    root: float = 0.0,
    momentum: float = 0.0,
    momentum_month_order: float = 0.0,
    momentum_stage: float = 0.0,
    momentum_stage_lu: float = 0.0,
    momentum_stage_blade: float = 0.0,
    momentum_stage_general: float = 0.0,
    momentum_structure: float = 0.0,
    momentum_auxiliary: float = 0.0,
    hidden: float = 0.0,
) -> None:
    row = _ensure_decomposition_bucket(decomposition, god)
    month_order = max(0.0, float(momentum_month_order or 0.0))
    stage_lu = max(0.0, float(momentum_stage_lu or 0.0))
    stage_blade = max(0.0, float(momentum_stage_blade or 0.0))
    stage_general = max(0.0, float(momentum_stage_general or 0.0))
    stage = max(0.0, float(momentum_stage or 0.0)) + stage_lu + stage_blade + stage_general
    structure = max(0.0, float(momentum_structure or 0.0))
    auxiliary = max(0.0, float(momentum_auxiliary or 0.0))
    total_momentum = max(0.0, float(momentum or 0.0)) + month_order + stage + structure + auxiliary
    row["manifest"] += max(0.0, float(manifest or 0.0))
    row["root"] += max(0.0, float(root or 0.0))
    row["momentum"] += total_momentum
    row["momentum_month_order"] += month_order
    row["momentum_stage"] += stage
    row["momentum_stage_lu"] += stage_lu
    row["momentum_stage_blade"] += stage_blade
    row["momentum_stage_general"] += stage_general
    row["momentum_structure"] += structure
    row["momentum_auxiliary"] += auxiliary
    row["hidden"] += max(0.0, float(hidden or 0.0))
    row["total"] = row["manifest"] + row["root"] + row["momentum"] + row["hidden"]


def _finalize_decomposition(
    decomposition: Dict[str, Dict[str, float]],
    *,
    damping: float,
    energy_min: float,
    energy_max: float,
) -> Dict[str, Dict[str, float]]:
    out: Dict[str, Dict[str, float]] = {}
    for god, raw in decomposition.items():
        if not isinstance(raw, dict):
            continue
        manifest = max(0.0, float(raw.get("manifest") or 0.0)) * damping
        root = max(0.0, float(raw.get("root") or 0.0)) * damping
        momentum_month_order = max(0.0, float(raw.get("momentum_month_order") or 0.0)) * damping
        momentum_stage_lu = max(0.0, float(raw.get("momentum_stage_lu") or 0.0)) * damping
        momentum_stage_blade = max(0.0, float(raw.get("momentum_stage_blade") or 0.0)) * damping
        momentum_stage_general = max(0.0, float(raw.get("momentum_stage_general") or 0.0)) * damping
        momentum_stage = (
            max(0.0, float(raw.get("momentum_stage") or 0.0))
            - max(0.0, float(raw.get("momentum_stage_lu") or 0.0))
            - max(0.0, float(raw.get("momentum_stage_blade") or 0.0))
            - max(0.0, float(raw.get("momentum_stage_general") or 0.0))
        )
        momentum_stage = max(0.0, momentum_stage) * damping + momentum_stage_lu + momentum_stage_blade + momentum_stage_general
        momentum_structure = max(0.0, float(raw.get("momentum_structure") or 0.0)) * damping
        momentum_auxiliary = max(0.0, float(raw.get("momentum_auxiliary") or 0.0)) * damping
        momentum_base = max(0.0, float(raw.get("momentum") or 0.0)) - (
            max(0.0, float(raw.get("momentum_month_order") or 0.0))
            + max(0.0, float(raw.get("momentum_stage") or 0.0))
            + max(0.0, float(raw.get("momentum_structure") or 0.0))
            + max(0.0, float(raw.get("momentum_auxiliary") or 0.0))
        )
        momentum_other = max(0.0, momentum_base) * damping
        momentum = momentum_month_order + momentum_stage + momentum_structure + momentum_auxiliary + momentum_other
        hidden = max(0.0, float(raw.get("hidden") or 0.0)) * damping
        total_raw = manifest + root + momentum + hidden
        total = max(energy_min, min(energy_max, total_raw))
        if total_raw > 0.0 and total != total_raw:
            scale = total / total_raw
            manifest *= scale
            root *= scale
            momentum_month_order *= scale
            momentum_stage *= scale
            momentum_stage_lu *= scale
            momentum_stage_blade *= scale
            momentum_stage_general *= scale
            momentum_structure *= scale
            momentum_auxiliary *= scale
            momentum_other *= scale
            momentum *= scale
            hidden *= scale
        manifest_r = round(manifest, 2)
        root_r = round(root, 2)
        momentum_r = round(momentum, 2)
        hidden_r = round(hidden, 2)
        out[god] = {
            "manifest": manifest_r,
            "root": root_r,
            "momentum": momentum_r,
            "momentum_month_order": round(momentum_month_order, 2),
            "momentum_stage": round(momentum_stage, 2),
            "momentum_stage_lu": round(momentum_stage_lu, 2),
            "momentum_stage_blade": round(momentum_stage_blade, 2),
            "momentum_stage_general": round(momentum_stage_general, 2),
            "momentum_structure": round(momentum_structure, 2),
            "momentum_auxiliary": round(momentum_auxiliary, 2),
            "momentum_other": round(momentum_other, 2),
            "hidden": hidden_r,
            "total": round(manifest_r + root_r + momentum_r + hidden_r, 2),
        }
    return out


def _vertical_compression(stem: str, branch: str) -> Tuple[float, float]:
    """计算同柱盖头截脚因子：返回 (stem_factor, branch_factor)"""
    s_el = STEM_ELEMENT.get(stem, "")
    b_el = BRANCH_ELEMENT.get(branch, "")
    if not s_el or not b_el:
        return 1.0, 1.0
    
    # 五行索引：木0, 火1, 土2, 金3, 水4
    s_idx = ELEMENT_CYCLE.index(s_el)
    b_idx = ELEMENT_CYCLE.index(b_el)
    
    # 盖头：干克支 (s_idx 克 b_idx) -> b_idx == (s_idx + 2) % 5
    if b_idx == (s_idx + 2) % 5:
        return 1.0, _get_l0_val("GAI_TOU_FACTOR", 0.85)
    
    # 截脚：支克干 (b_idx 克 s_idx) -> s_idx == (b_idx + 2) % 5
    if s_idx == (b_idx + 2) % 5:
        return _get_l0_val("JIE_JIAO_FACTOR", 0.75), 1.0
        
    return 1.0, 1.0


def _accumulate_stem_energy(
    *,
    stem: str,
    daymaster: str,
    source_factor: float,
    season_multiplier: float,
    root_strengths: Dict[str, float],
    acc: Dict[str, float],
    decomposition: Dict[str, Dict[str, float]],
    pillar_label: str = "",
    proximity_factor: Optional[float] = None,
    ledger: Optional[EvolutionLedger] = None,
) -> None:
    """
    V17.30 能量累加器（天干）：
      Energy = STEM_BASE * source_factor * season_multiplier
      如果天干通根地支 → Energy *= 1.5
    """
    if not stem:
        return
    energy = _get_l0_val("STEM_BASE", 10.0) * source_factor * season_multiplier
    manifest_energy = energy
    exact_root_strength = max(0.0, float(root_strengths.get(stem, 0.0) or 0.0))
    cross_polarity_support = _cross_polarity_root_support(stem, root_strengths)
    root_strength = exact_root_strength + cross_polarity_support
    root_bonus = 0.0
    if root_strength > 0.0:
        rooted_gain = 1.0 + (_get_l0_val("ROOTED_GAIN", 1.5) - 1.0) * min(1.0, root_strength)
        root_bonus = manifest_energy * (rooted_gain - 1.0)
        energy = manifest_energy + root_bonus
    god = ten_god_from_stems(daymaster, stem)
    # 无根明透的比劫容易虚浮。除日主本干外，对无根比肩/劫财做一次温和衰减。
    if pillar_label != "日" and god in {"比肩", "劫财"} and root_strength < 0.35:
        floating_floor = _get_l0_val("FLOATING_PEER_FACTOR", 0.72)
        floating_ratio = max(0.0, min(1.0, root_strength / 0.35))
        peer_factor = floating_floor + (1.0 - floating_floor) * floating_ratio
        energy *= peer_factor
        manifest_energy *= peer_factor
        root_bonus *= peer_factor
    # V17.99: 数值护栏 — 安全累加
    if math.isfinite(energy):
        acc[god] = acc.get(god, 0.0) + energy
        _add_decomposition(decomposition, god, manifest=manifest_energy, root=root_bonus)
    else:
        _log.warning(f"[V17-PHYSICS-NAN] Attempted to add NaN energy for {god} at {pillar_label}干")
    if ledger is not None:
        parts = [f"{stem}→{god}"]
        if proximity_factor is not None:
            parts.append(f"贴身×{proximity_factor:.2f}")
        if exact_root_strength > 0.0:
            parts.append(f"本根×{min(1.0, exact_root_strength):.2f}")
        if cross_polarity_support > 0.0:
            parts.append(f"异阴阳根×{min(1.0, cross_polarity_support):.2f}")
        if pillar_label != "日" and god in {"比肩", "劫财"} and root_strength < 0.35:
            floating_floor = _get_l0_val("FLOATING_PEER_FACTOR", 0.72)
            floating_ratio = max(0.0, min(1.0, root_strength / 0.35))
            peer_factor = floating_floor + (1.0 - floating_floor) * floating_ratio
            parts.append(f"浮木×{peer_factor:.2f}")
        if abs(season_multiplier - 1.0) > 0.01:
            parts.append(f"季×{season_multiplier:.1f}")
        reason = f"{pillar_label}干 {'·'.join(parts)}"
        ledger.append_entry(god, acc[god], f"L0_STEM_{pillar_label}", reason)


def _accumulate_branch_energy(
    *,
    branch: str,
    daymaster: str,
    source_factor: float,
    void_factor: float,
    month_branch: str,
    apply_month_order: bool,
    visible_stems: List[str],
    acc: Dict[str, float],
    decomposition: Dict[str, Dict[str, float]],
    pillar_label: str = "",
    ledger: Optional[EvolutionLedger] = None,
) -> None:
    """
    V17.30 能量累加器（地支）：
      Energy = BRANCH_BASE * hidden_weight * source_factor * season_multiplier * void_factor
      如果地支透出天干 → Energy *= 1.2
    """
    if not branch:
        return
    stage_name, stage_bonus_ratio = _branch_stage_for_daymaster(daymaster, branch)
    for hidden_stem, h_w in BRANCH_HIDDEN.get(branch, []):
        hidden_element = STEM_ELEMENT.get(hidden_stem, "")
        sm = 1.0
        if apply_month_order and branch == month_branch and hidden_element:
            sm = _season_multiplier(hidden_element, month_branch)
        raw_base_energy = _get_l0_val("BRANCH_BASE", 12.0) * h_w * source_factor * void_factor
        exposed = hidden_stem in visible_stems
        same_element_visible = _same_element_visible(hidden_stem, visible_stems)
        support_factor = 1.0
        if exposed:
            support_factor = _get_l0_val("EXPOSED_HIDDEN_GAIN", 1.2)
        elif not same_element_visible:
            support_factor = _get_l0_val(
                "UNEXPOSED_MAIN_HIDDEN_FACTOR" if float(h_w) >= 0.6 else "UNEXPOSED_AUX_HIDDEN_FACTOR",
                0.58 if float(h_w) >= 0.6 else 0.42,
            )
        energy = raw_base_energy * sm * support_factor
        god = ten_god_from_stems(daymaster, hidden_stem)
        base_component = raw_base_energy * support_factor
        momentum_component = raw_base_energy * max(0.0, sm - 1.0) * support_factor
        stage_component = 0.0
        if hidden_element and hidden_element == STEM_ELEMENT.get(daymaster, "") and stage_bonus_ratio > 0.0:
            stage_component = raw_base_energy * stage_bonus_ratio * support_factor
            energy += stage_component
        stage_breakdown = _split_stage_component(stage_name, stage_component)
        # V17.99: 数值护栏 — 安全累加
        if math.isfinite(energy):
            acc[god] = acc.get(god, 0.0) + energy
            if exposed or same_element_visible:
                _add_decomposition(
                    decomposition,
                    god,
                    root=base_component,
                    momentum_month_order=momentum_component,
                    momentum_stage=stage_component,
                    momentum_stage_lu=stage_breakdown["momentum_stage_lu"],
                    momentum_stage_blade=stage_breakdown["momentum_stage_blade"],
                    momentum_stage_general=stage_breakdown["momentum_stage_general"],
                )
            else:
                _add_decomposition(
                    decomposition,
                    god,
                    hidden=base_component,
                    momentum_month_order=momentum_component,
                    momentum_stage=stage_component,
                    momentum_stage_lu=stage_breakdown["momentum_stage_lu"],
                    momentum_stage_blade=stage_breakdown["momentum_stage_blade"],
                    momentum_stage_general=stage_breakdown["momentum_stage_general"],
                )
        else:
            _log.warning(f"[V17-PHYSICS-NAN] Attempted to add NaN energy for {god} at {pillar_label}支")
        if ledger is not None:
            parts = [f"{branch}藏{hidden_stem}→{god}"]
            if exposed:
                parts.append("透干×1.2")
            elif not same_element_visible:
                latent_factor = _get_l0_val(
                    "UNEXPOSED_MAIN_HIDDEN_FACTOR" if float(h_w) >= 0.6 else "UNEXPOSED_AUX_HIDDEN_FACTOR",
                    0.58 if float(h_w) >= 0.6 else 0.42,
                )
                parts.append(f"潜藏×{latent_factor:.2f}")
            if void_factor < 1.0:
                parts.append(f"空亡×{void_factor:.1f}")
            if abs(sm - 1.0) > 0.01:
                parts.append(f"季×{sm:.1f}")
            if stage_component > 0.0 and stage_name:
                parts.append(f"{stage_name}势×{stage_bonus_ratio:.2f}")
            reason = f"{pillar_label}支 {'·'.join(parts)}"
            ledger.append_entry(god, acc[god], f"L0_BRANCH_{pillar_label}", reason)


def calc_deity_scores(
    *,
    four_pillars: Dict[str, str],
    luck_pillar: str = "—",
    flow_pillar: str = "—",
    gender: str = "female",
    birth_time: Optional[Any] = None,
) -> Tuple[Dict[str, float], List[str], float, Dict[str, Any]]:
    """
    V17.30 Mass Phase：计算十神绝对能量分值。

    参数：
        four_pillars: {"year": "甲子", "month": "乙丑", "day": "丙寅", "hour": "丁卯"}
        luck_pillar:  大运干支字符串（"—" 或空字符串表示缺失）
        flow_pillar:  流年干支字符串
        gender:       "male" | "female"
        birth_time:   出生时间（用于旬空计算）

    返回：
        (absolute_scores, top4_ten_gods, total_energy_index, energy_meta)

    absolute_scores:    各十神绝对能量值 dict（单位：Qi），不做归一化
    total_energy_index: 所有十神绝对能量的总和（预期范围：50.0 - 500.0+）
    """
    day_gz = str(four_pillars.get("day", "")).strip()
    daymaster, _ = _parse_gz(day_gz)
    if not daymaster:
        default: Dict[str, float] = {
            "比肩": STEM_BASE, "食神": STEM_BASE, "正官": STEM_BASE, "正财": STEM_BASE, "正印": STEM_BASE
        }
        return default, list(default)[:4], round(sum(default.values()), 2), {"month_command_god": "", "void_pillars": []}

    # ── Step 1：准备全局辅助数据 ──
    acc: Dict[str, float] = {}
    decomposition: Dict[str, Dict[str, float]] = {}
    visible_stems = _collect_visible_stems(four_pillars, luck_pillar, flow_pillar)
    root_strengths, root_dynamic_meta = _collect_root_strengths_with_meta(four_pillars, luck_pillar, flow_pillar)
    xun_kong_map = _get_xun_kong_map(birth_time=birth_time, four_pillars=four_pillars)
    void_pillars: List[str] = []
    ledger = EvolutionLedger()

    # ── Step 2：提取月支。月令只作用月支自身，不再对全盘同元素广播。 ──
    _, month_branch = _parse_gz(str(four_pillars.get("month", "")).strip())

    # ── Step 3：遍历四柱累加 ──
    pillar_cn = {"year": "年", "month": "月", "day": "日", "hour": "时"}
    for pillar_key in ("year", "month", "day", "hour"):
        gz = str(four_pillars.get(pillar_key, "")).strip()
        if not gz:
            continue
        stem, branch = _parse_gz(gz)
        pillar_void_factor = _void_factor(branch, xun_kong_map.get(pillar_key, ""))
        
        # V17.70：计算垂直压制因子
        s_comp, b_comp = _vertical_compression(stem, branch)
        
        if pillar_void_factor < 1.0:
            void_pillars.append(pillar_key)
        p_label = pillar_cn.get(pillar_key, pillar_key)

        # 天干能量：
        # 日干是十神参照轴，不应再作为“比肩/劫财显化”重复计入。
        if pillar_key != "day":
            stem_position_factor = float(NATAL_STEM_POSITION_WEIGHTS.get(pillar_key, 0.8))
            _accumulate_stem_energy(
                stem=stem,
                daymaster=daymaster,
                source_factor=stem_position_factor * s_comp,
                season_multiplier=1.0,
                root_strengths=root_strengths,
                acc=acc,
                decomposition=decomposition,
                pillar_label=p_label,
                proximity_factor=stem_position_factor,
                ledger=ledger,
            )
        # 地支能量（藏干逐一累加，各自带 Season Power）
        branch_source_factor = float(NATAL_BRANCH_POSITION_WEIGHTS.get(pillar_key, 0.8)) * b_comp
        _accumulate_branch_energy(
            branch=branch,
            daymaster=daymaster,
            source_factor=branch_source_factor,
            void_factor=pillar_void_factor,
            month_branch=month_branch,
            apply_month_order=(pillar_key == "month"),
            visible_stems=visible_stems,
            acc=acc,
            decomposition=decomposition,
            pillar_label=p_label,
            ledger=ledger,
        )

    # ── Step 4：大运 / 流年（带衰减系数；月令不再直接广播到外柱）──
    luck_f = _get_l0_val("LUCK_PILLAR_FACTOR", 0.85)
    flow_f = _get_l0_val("FLOW_PILLAR_FACTOR", 0.65)
    for gz_val, source_factor, sf_label in (
        (luck_pillar, luck_f, "运"),
        (flow_pillar, flow_f, "流"),
    ):
        if gz_val and gz_val not in ("—", "-"):
            stem, branch = _parse_gz(gz_val)
            _accumulate_stem_energy(
                stem=stem,
                daymaster=daymaster,
                source_factor=source_factor,
                season_multiplier=1.0,
                root_strengths=root_strengths,
                acc=acc,
                decomposition=decomposition,
                pillar_label=sf_label,
                ledger=ledger,
            )
            _accumulate_branch_energy(
                branch=branch,
                daymaster=daymaster,
                source_factor=source_factor,
                void_factor=1.0,
                month_branch=month_branch,
                apply_month_order=False,
                visible_stems=visible_stems,
                acc=acc,
                decomposition=decomposition,
                pillar_label=sf_label,
                ledger=ledger,
            )

    structural_bonuses = _apply_sanhe_foundation_bonus(
        acc=acc,
        decomposition=decomposition,
        daymaster=daymaster,
        four_pillars=four_pillars,
        luck_pillar=luck_pillar,
        flow_pillar=flow_pillar,
        ledger=ledger,
    )
    relation_visible_bonuses = _apply_relation_visible_resonance_bonuses(
        acc=acc,
        decomposition=decomposition,
        daymaster=daymaster,
        four_pillars=four_pillars,
        luck_pillar=luck_pillar,
        flow_pillar=flow_pillar,
        relation_traces=list(root_dynamic_meta.get("traces") or []),
        ledger=ledger,
    )

    # ── Step 5：月令主气额外标记（实际加持已只作用在月支自身）──
    month_stem, _ = _parse_gz(str(four_pillars.get("month", "")).strip())
    month_command_god = ""
    month_hidden = BRANCH_HIDDEN.get(month_branch, [])
    if month_hidden:
        month_main_stem = month_hidden[0][0]
        month_command_god = ten_god_from_stems(daymaster, month_main_stem)
    elif month_stem:
        month_command_god = ten_god_from_stems(daymaster, month_stem)

    # ── Step 6：性别微调（不影响量级，仅作定性偏移）──
    if gender == "male":
        acc["正官"] = acc.get("正官", 0.0) + 1.2
        acc["七杀"] = acc.get("七杀", 0.0) + 0.8
        _add_decomposition(decomposition, "正官", momentum_auxiliary=1.2)
        _add_decomposition(decomposition, "七杀", momentum_auxiliary=0.8)
        ledger.append_entry("正官", acc.get("正官", 0.0), "L0_GENDER", "男命正官性别微调+1.2")
        ledger.append_entry("七杀", acc.get("七杀", 0.0), "L0_GENDER", "男命七杀性别微调+0.8")
    else:
        acc["食神"] = acc.get("食神", 0.0) + 1.2
        acc["伤官"] = acc.get("伤官", 0.0) + 0.8
        _add_decomposition(decomposition, "食神", momentum_auxiliary=1.2)
        _add_decomposition(decomposition, "伤官", momentum_auxiliary=0.8)
        ledger.append_entry("食神", acc.get("食神", 0.0), "L0_GENDER", "女命食神性别微调+1.2")
        ledger.append_entry("伤官", acc.get("伤官", 0.0), "L0_GENDER", "女命伤官性别微调+0.8")

    # ── Step 7：全局阻尼与排序输出 ──
    if not acc:
        return {"比肩": STEM_BASE}, ["比肩"], STEM_BASE, {"month_command_god": "", "void_pillars": void_pillars}
    
    # V17.98+：从统一的双层配置架构（全局法典）读取安全阻尼策略
    import json
    from v17_rebirth.paths import V17_REBIRTH_ROOT
    cfg_path = V17_REBIRTH_ROOT / "backend" / "logic" / "configs" / "v17_core_constants.json"
    damping_enabled = True
    system_friction = GLOBAL_DAMPING
    if cfg_path.exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:

                v17_cfg = json.load(f).get("constants", {})
                sd = v17_cfg.get("PHYSICS_DAMPING", {})
                damping_enabled = sd.get("SAFETY_CAP_ENABLED", True)
                system_friction = sd.get("SYSTEM_FRICTION", GLOBAL_DAMPING)
        except: pass

    # 应用全局惯性阻尼（针对高能系统）
    total_raw = sum(acc.values())
    damping = system_friction if damping_enabled and total_raw > 340.0 else 1.0

    
    # V17.99: 物理稳态钳制 (Numerical Guardrails Enforcement)
    # 强制将所有十神能量压制在宏观物理允许的区间 [MIN, MAX]
    e_min = _get_guardrail_val("ENERGY_MIN", 0.1)
    e_max = _get_guardrail_val("ENERGY_MAX", 1000.0)
    decomposition_final = _finalize_decomposition(
        decomposition,
        damping=damping,
        energy_min=e_min,
        energy_max=e_max,
    )

    scored = {}
    for k, v in acc.items():
        v_final = v * damping
        # 强制钳制
        v_clamped = max(e_min, min(e_max, v_final))
        if math.isfinite(v_clamped):
            scored[k] = round(v_clamped, 2)
            
    # 按强度排序
    sorted_scored = {
        k: v for k, v in sorted(scored.items(), key=lambda kv: (-kv[1], kv[0]))
    }

    total_energy_index = round(sum(sorted_scored.values()), 2)
    ten_gods = list(sorted_scored)[:4]
    return sorted_scored, ten_gods, total_energy_index, {
        "month_command_god": month_command_god,
        "void_pillars": void_pillars,
        "void_branches": {k: v for k, v in xun_kong_map.items() if v},
        "season_power": {
            "month_branch": month_branch,
            "month_element": BRANCH_ELEMENT.get(month_branch, ""),
            "scope": "month_branch_only",
            "same": SEASON_POWER_SAME,
            "generated": SEASON_POWER_GENERATED,
            "controlled": SEASON_POWER_CONTROLLED,
        },
        "ten_gods_decomposition_l0": decomposition_final,
        "constants": {
            "stem_base": STEM_BASE,
            "branch_base": BRANCH_BASE,
            "natal_stem_position_weights": dict(NATAL_STEM_POSITION_WEIGHTS),
            "natal_branch_position_weights": dict(NATAL_BRANCH_POSITION_WEIGHTS),
            "rooted_stem_gain": ROOTED_STEM_GAIN,
            "rel_root_bonus_sanhe": REL_ROOT_BONUS_SANHE,
            "rel_root_bonus_sanhui": REL_ROOT_BONUS_SANHUI,
            "rel_root_bonus_banhe": REL_ROOT_BONUS_BANHE,
            "rel_root_bonus_liuhe": REL_ROOT_BONUS_LIUHE,
            "rel_root_bonus_anhe": REL_ROOT_BONUS_ANHE,
            "rel_visible_stem_resonance_banhe": REL_VISIBLE_STEM_RESONANCE_BANHE,
            "rel_visible_stem_resonance_sanhui": REL_VISIBLE_STEM_RESONANCE_SANHUI,
            "rel_visible_stem_resonance_liuhe": REL_VISIBLE_STEM_RESONANCE_LIUHE,
            "rel_visible_stem_resonance_anhe": REL_VISIBLE_STEM_RESONANCE_ANHE,
            "rel_visible_cross_polarity_factor": REL_VISIBLE_CROSS_POLARITY_FACTOR,
            "rel_root_penalty_chong": REL_ROOT_PENALTY_CHONG,
            "rel_root_penalty_hai": REL_ROOT_PENALTY_HAI,
            "rel_root_penalty_po": REL_ROOT_PENALTY_PO,
            "rel_root_penalty_xing": REL_ROOT_PENALTY_XING,
            "rel_root_control_bonus": REL_ROOT_CONTROL_BONUS,
            "rel_root_control_penalty": REL_ROOT_CONTROL_PENALTY,
            "exposed_hidden_gain": EXPOSED_HIDDEN_GAIN,
            "unexposed_main_hidden_factor": UNEXPOSED_MAIN_HIDDEN_FACTOR,
            "unexposed_aux_hidden_factor": UNEXPOSED_AUX_HIDDEN_FACTOR,
            "cross_polarity_root_support_factor": CROSS_POLARITY_ROOT_SUPPORT_FACTOR,
            "void_reduction_factor": VOID_REDUCTION_FACTOR,
        },
        "root_dynamic_relations": root_dynamic_meta,
        "structural_bonuses": structural_bonuses,
        "relation_visible_bonuses": relation_visible_bonuses,
        "projection_bridge_protocol": _projection_bridge_protocol(),
        "ledger": ledger,
    }
