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

from v17_rebirth.backend.logic.climate_field_protocol import build_climate_field
from v17_rebirth.backend.logic.runtime_field_protocol import ROOT_SCOPE_WEIGHTS as _RUNTIME_ROOT_SCOPE_WEIGHTS
from v17_rebirth.backend.logic.L0_physics_fields.evolution_ledger import EvolutionLedger
from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_decomposition import (
    add_decomposition as _add_decomposition,
    finalize_decomposition as _finalize_decomposition,
)
from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_projection import (
    collect_visible_stems as _collect_visible_stems,
    cross_polarity_root_support as _cross_polarity_root_support,
    same_element_visible as _same_element_visible,
    visible_stem_scope_weights as _visible_stem_scope_weights,
)
from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_relation_runtime import (
    append_relation_trace as _append_relation_trace,
    detect_relation_runtime_hits as _detect_relation_runtime_hits,
)
from v17_rebirth.backend.logic.L1_atomic_ops.relation_runtime_collectors import (
    collect_structured_relation_family_deltas as _collect_structured_relation_family_deltas,
    collect_penalty_relation_deltas as _collect_penalty_relation_deltas,
    collect_control_relation_deltas as _collect_control_relation_deltas,
    collect_stem_fusion_relation_deltas as _collect_stem_fusion_relation_deltas,
)
from v17_rebirth.backend.logic.L1_atomic_ops.relation_geometry_pairs import (
    eval_anhe_hits,
    eval_liu_chong_hits,
    eval_liu_hai_hits,
    eval_liu_po_hits,
    eval_liuhe_hits,
    sanxing_detect_geometry,
)
from v17_rebirth.backend.logic.L1_atomic_ops.relation_geometry_structured import (
    eval_banhe_hits,
    eval_gonghe_hits,
    eval_sanhe_hits,
)
from v17_rebirth.backend.logic.L1_atomic_ops.stem_fusion_geometry import (
    branches_and_stems_from_runtime_pillars,
    detect_stem_fusion_cases,
)
from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_root_dynamics import (
    build_runtime_stems as _build_runtime_stems,
    finalize_root_dynamic_state as _finalize_root_dynamic_state,
)
from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_protocol_builders import (
    build_projection_bridge_protocol,
    build_relation_formation_summary,
    build_relation_dynamics_summary,
)
from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_static_basis import (
    accumulate_branch_energy as _accumulate_branch_energy,
    accumulate_stem_energy as _accumulate_stem_energy,
    branch_stage_for_daymaster as _branch_stage_for_daymaster,
    split_stage_component as _split_stage_component,
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
REL_ROOT_BONUS_GONGHE: float = 0.11
REL_ROOT_BONUS_LIUHE: float = 0.12
REL_ROOT_BONUS_ANHE: float = 0.08
REL_FAMILY_BASE_FACTOR_SANHUI: float = 2.4
REL_FAMILY_BASE_FACTOR_SANHE: float = 1.9
REL_FAMILY_BASE_FACTOR_BANHE_SHENGWANG: float = 1.45
REL_FAMILY_BASE_FACTOR_BANHE_MUWANG: float = 1.28
REL_FAMILY_BASE_FACTOR_GONGHE: float = 1.12
REL_FAMILY_BASE_FACTOR_LIUHE: float = 1.22
REL_FAMILY_BASE_FACTOR_ANHE: float = 1.05
REL_FAMILY_FULL_CLEAN_SANHUI: float = 10.0
REL_FAMILY_FULL_CLEAN_SANHE: float = 5.0
REL_FAMILY_FULL_CLEAN_BANHE_SHENGWANG: float = 2.45
REL_FAMILY_FULL_CLEAN_BANHE_MUWANG: float = 1.95
REL_FAMILY_FULL_CLEAN_GONGHE: float = 1.35
REL_FAMILY_FULL_CLEAN_LIUHE: float = 1.55
REL_FAMILY_FULL_CLEAN_ANHE: float = 1.10
REL_FAMILY_ROOT_UNIT: float = 0.078
REL_FAMILY_STRUCTURE_SCALE_SANHUI: float = 0.62
REL_FAMILY_STRUCTURE_SCALE_SANHE: float = 0.90
REL_DUPLICATE_BONUS_PIVOT: float = 0.30
REL_DUPLICATE_BONUS_TOMB: float = 0.18
REL_DUPLICATE_BONUS_STARTER: float = 0.10
REL_VISIBLE_STEM_RESONANCE_BANHE: float = 3.8
REL_VISIBLE_STEM_RESONANCE_SANHE: float = 2.15
REL_VISIBLE_STEM_RESONANCE_SANHUI: float = 2.0
REL_VISIBLE_STEM_RESONANCE_BANHE_SHENGWANG: float = 1.75
REL_VISIBLE_STEM_RESONANCE_BANHE_MUWANG: float = 1.45
REL_VISIBLE_STEM_RESONANCE_GONGHE: float = 1.05
REL_VISIBLE_STEM_RESONANCE_LIUHE: float = 1.8
REL_VISIBLE_STEM_RESONANCE_ANHE: float = 1.1
REL_VISIBLE_CROSS_POLARITY_FACTOR: float = 0.82
REL_SOURCE_ATTENUATION_SANHUI: float = 0.18
REL_SOURCE_ATTENUATION_SANHE: float = 0.38
REL_SOURCE_ATTENUATION_BANHE_SHENGWANG: float = 0.28
REL_SOURCE_ATTENUATION_BANHE_MUWANG: float = 0.24
REL_SOURCE_ATTENUATION_GONGHE: float = 0.16
REL_SOURCE_ATTENUATION_LIUHE: float = 0.20
REL_SOURCE_ATTENUATION_ANHE: float = 0.12
REL_SOURCE_RETENTION_MIN_SANHUI: float = 0.72
REL_SOURCE_RETENTION_MIN_SANHE: float = 0.48
REL_SOURCE_RETENTION_MIN_BANHE_SHENGWANG: float = 0.58
REL_SOURCE_RETENTION_MIN_BANHE_MUWANG: float = 0.62
REL_SOURCE_RETENTION_MIN_GONGHE: float = 0.70
REL_SOURCE_RETENTION_MIN_LIUHE: float = 0.66
REL_SOURCE_RETENTION_MIN_ANHE: float = 0.76
REL_SOURCE_KEEP_SAME_ELEMENT_SANHUI: float = 0.97
REL_SOURCE_KEEP_SAME_ELEMENT_SANHE: float = 0.92
REL_SOURCE_KEEP_SAME_ELEMENT_BANHE_SHENGWANG: float = 0.94
REL_SOURCE_KEEP_SAME_ELEMENT_BANHE_MUWANG: float = 0.95
REL_SOURCE_KEEP_SAME_ELEMENT_GONGHE: float = 0.97
REL_SOURCE_KEEP_SAME_ELEMENT_LIUHE: float = 0.96
REL_SOURCE_KEEP_SAME_ELEMENT_ANHE: float = 0.98
STEM_FUSION_SOURCE_ATTENUATION: float = 0.16
STEM_FUSION_SOURCE_RETENTION_MIN: float = 0.78
STEM_FUSION_VISIBLE_SUPPORT_MONTH: float = 1.00
STEM_FUSION_VISIBLE_SUPPORT_DAY: float = 0.82
STEM_FUSION_VISIBLE_SUPPORT_HOUR: float = 0.66
STEM_FUSION_VISIBLE_SUPPORT_YEAR: float = 0.52
STEM_FUSION_VISIBLE_SUPPORT_LUCK: float = 0.72
STEM_FUSION_VISIBLE_SUPPORT_FLOW: float = 0.48
STEM_FUSION_BRANCH_ROOT_MONTH: float = 1.00
STEM_FUSION_BRANCH_ROOT_DAY: float = 0.84
STEM_FUSION_BRANCH_ROOT_HOUR: float = 0.68
STEM_FUSION_BRANCH_ROOT_YEAR: float = 0.56
STEM_FUSION_BRANCH_ROOT_LUCK: float = 0.86
STEM_FUSION_BRANCH_ROOT_FLOW: float = 0.60
STEM_FUSION_SUPPORT_VISIBLE_WEIGHT: float = 0.62
STEM_FUSION_SUPPORT_BRANCH_WEIGHT: float = 0.38
STEM_FUSION_INTERFERENCE_BRANCH_WEIGHT: float = 0.72
STEM_FUSION_INTERFERENCE_STEM_WEIGHT: float = 0.45
STEM_FUSION_EFFECTIVE_THRESHOLD: float = 0.26
REL_ROOT_PENALTY_CHONG: float = 0.12
REL_ROOT_PENALTY_HAI: float = 0.08
REL_ROOT_PENALTY_PO: float = 0.06
REL_ROOT_PENALTY_XING: float = 0.07
REL_ROOT_CONTROL_BONUS: float = 0.05
REL_ROOT_CONTROL_PENALTY: float = 0.07

REL_VISIBLE_SCOPE_WEIGHTS: Dict[str, float] = {
    "year": 0.56,
    "month": 1.00,
    "day": 0.84,
    "hour": 0.68,
    "luck": 0.92,
    "flow": 0.38,
}

ROOT_SCOPE_WEIGHTS: Dict[str, float] = dict(_RUNTIME_ROOT_SCOPE_WEIGHTS)

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

_GONGHE_PAIR_TO_ELEMENT: Dict[frozenset[str], str] = {
    frozenset({"申", "辰"}): "水",
    frozenset({"亥", "未"}): "木",
    frozenset({"寅", "戌"}): "火",
    frozenset({"巳", "丑"}): "金",
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


def _relation_full_clean_factor(family_key: str) -> float:
    mapping = {
        "sanhui": ("REL_FAMILY_FULL_CLEAN_SANHUI", REL_FAMILY_FULL_CLEAN_SANHUI),
        "sanhe": ("REL_FAMILY_FULL_CLEAN_SANHE", REL_FAMILY_FULL_CLEAN_SANHE),
        "banhe_shengwang": ("REL_FAMILY_FULL_CLEAN_BANHE_SHENGWANG", REL_FAMILY_FULL_CLEAN_BANHE_SHENGWANG),
        "banhe_muwang": ("REL_FAMILY_FULL_CLEAN_BANHE_MUWANG", REL_FAMILY_FULL_CLEAN_BANHE_MUWANG),
        "gonghe": ("REL_FAMILY_FULL_CLEAN_GONGHE", REL_FAMILY_FULL_CLEAN_GONGHE),
        "liuhe": ("REL_FAMILY_FULL_CLEAN_LIUHE", REL_FAMILY_FULL_CLEAN_LIUHE),
        "anhe": ("REL_FAMILY_FULL_CLEAN_ANHE", REL_FAMILY_FULL_CLEAN_ANHE),
    }
    cfg_key, default = mapping.get(family_key, (f"REL_FAMILY_FULL_CLEAN_{family_key.upper()}", 1.0))
    return max(0.5, _get_l0_val(cfg_key, default))


def _relation_base_factor(family_key: str) -> float:
    mapping = {
        "sanhui": ("REL_FAMILY_BASE_FACTOR_SANHUI", REL_FAMILY_BASE_FACTOR_SANHUI),
        "sanhe": ("REL_FAMILY_BASE_FACTOR_SANHE", REL_FAMILY_BASE_FACTOR_SANHE),
        "banhe_shengwang": ("REL_FAMILY_BASE_FACTOR_BANHE_SHENGWANG", REL_FAMILY_BASE_FACTOR_BANHE_SHENGWANG),
        "banhe_muwang": ("REL_FAMILY_BASE_FACTOR_BANHE_MUWANG", REL_FAMILY_BASE_FACTOR_BANHE_MUWANG),
        "gonghe": ("REL_FAMILY_BASE_FACTOR_GONGHE", REL_FAMILY_BASE_FACTOR_GONGHE),
        "liuhe": ("REL_FAMILY_BASE_FACTOR_LIUHE", REL_FAMILY_BASE_FACTOR_LIUHE),
        "anhe": ("REL_FAMILY_BASE_FACTOR_ANHE", REL_FAMILY_BASE_FACTOR_ANHE),
    }
    cfg_key, default = mapping.get(family_key, (f"REL_FAMILY_BASE_FACTOR_{family_key.upper()}", 1.0))
    return max(1.0, _get_l0_val(cfg_key, default))


def _relation_effective_factor(family_key: str, visible_support_strength: float) -> float:
    base_factor = _relation_base_factor(family_key)
    max_factor = max(base_factor, _relation_full_clean_factor(family_key))
    support = max(0.0, min(1.0, float(visible_support_strength or 0.0)))
    return base_factor + (max_factor - base_factor) * support


def _relation_duplicate_role_bonus(role: str) -> float:
    normalized = str(role or "").strip().lower()
    if normalized == "pivot":
        return _get_l0_val("REL_DUPLICATE_BONUS_PIVOT", REL_DUPLICATE_BONUS_PIVOT)
    if normalized == "tomb":
        return _get_l0_val("REL_DUPLICATE_BONUS_TOMB", REL_DUPLICATE_BONUS_TOMB)
    return _get_l0_val("REL_DUPLICATE_BONUS_STARTER", REL_DUPLICATE_BONUS_STARTER)


def _relation_duplicate_bonus(
    branch_counts: Dict[str, Any],
    role_map: Dict[str, Any],
) -> Tuple[float, Dict[str, Dict[str, Any]]]:
    total = 0.0
    detail: Dict[str, Dict[str, Any]] = {}
    for branch, raw_count in (branch_counts or {}).items():
        extra_count = max(0, int(raw_count or 0) - 1)
        if extra_count <= 0:
            continue
        role = str((role_map or {}).get(branch) or "starter")
        per_bonus = _relation_duplicate_role_bonus(role)
        bonus = per_bonus * extra_count
        total += bonus
        detail[str(branch)] = {
            "role": role,
            "extra_count": extra_count,
            "bonus": round(bonus, 4),
        }
    return total, detail


def _relation_conflict_damping(
    *,
    members: List[str],
    family_key: str,
    conflicted_branches: set[str],
    conflict_events: Optional[List[set[str]]] = None,
) -> float:
    uniq = [m for m in set(members) if m]
    if not uniq:
        return 1.0
    member_set = set(uniq)
    if conflict_events:
        externally_conflicted: set[str] = set()
        for event in conflict_events:
            if not event:
                continue
            event_set = {str(item) for item in event if str(item).strip()}
            if not event_set:
                continue
            if event_set <= member_set:
                continue
            if event_set & member_set:
                externally_conflicted.update(event_set & member_set)
        conflict_ratio = len(externally_conflicted) / len(uniq)
    else:
        conflict_ratio = sum(1 for m in uniq if m in conflicted_branches) / len(uniq)
    penalty_map = {
        "sanhui": 0.78,
        "sanhe": 0.48,
        "banhe_shengwang": 0.44,
        "banhe_muwang": 0.52,
        "gonghe": 0.58,
        "liuhe": 0.46,
        "anhe": 0.38,
    }
    floor_map = {
        "sanhui": 0.22,
        "sanhe": 0.38,
        "banhe_shengwang": 0.42,
        "banhe_muwang": 0.34,
        "gonghe": 0.30,
        "liuhe": 0.42,
        "anhe": 0.52,
    }
    penalty = float(penalty_map.get(family_key, 0.42))
    floor = float(floor_map.get(family_key, 0.42))
    return max(floor, 1.0 - penalty * conflict_ratio)


def _relation_root_intensity(
    *,
    family_key: str,
    closeness: float,
    strength: float,
    completion: float = 1.0,
    duplicate_bonus: float = 0.0,
    conflict_damping: float = 1.0,
    family_factor: Optional[float] = None,
) -> float:
    family_factor = max(1.0, float(family_factor if family_factor is not None else _relation_full_clean_factor(family_key)))
    root_unit = _get_l0_val("REL_FAMILY_ROOT_UNIT", REL_FAMILY_ROOT_UNIT)
    normalized_strength = max(0.62, min(1.85, float(strength or 0.0)))
    normalized_completion = max(0.36, min(1.0, 0.24 + float(completion or 0.0) * 0.76))
    extra_branch_factor = 1.0 + max(0.0, float(duplicate_bonus or 0.0))
    return (
        root_unit
        * family_factor
        * max(0.62, float(closeness or 0.0))
        * normalized_strength
        * normalized_completion
        * extra_branch_factor
        * max(0.18, float(conflict_damping or 0.0))
    )


def _relation_visible_resonance_scale(family_key: str) -> Tuple[str, float]:
    mapping = {
        "sanhui": ("REL_VISIBLE_STEM_RESONANCE_SANHUI", REL_VISIBLE_STEM_RESONANCE_SANHUI),
        "sanhe": ("REL_VISIBLE_STEM_RESONANCE_SANHE", REL_VISIBLE_STEM_RESONANCE_SANHE),
        "banhe_shengwang": ("REL_VISIBLE_STEM_RESONANCE_BANHE_SHENGWANG", REL_VISIBLE_STEM_RESONANCE_BANHE_SHENGWANG),
        "banhe_muwang": ("REL_VISIBLE_STEM_RESONANCE_BANHE_MUWANG", REL_VISIBLE_STEM_RESONANCE_BANHE_MUWANG),
        "gonghe": ("REL_VISIBLE_STEM_RESONANCE_GONGHE", REL_VISIBLE_STEM_RESONANCE_GONGHE),
        "liuhe": ("REL_VISIBLE_STEM_RESONANCE_LIUHE", REL_VISIBLE_STEM_RESONANCE_LIUHE),
        "anhe": ("REL_VISIBLE_STEM_RESONANCE_ANHE", REL_VISIBLE_STEM_RESONANCE_ANHE),
    }
    cfg_key, default = mapping.get(family_key, (f"REL_VISIBLE_STEM_RESONANCE_{family_key.upper()}", 1.0))
    return cfg_key, max(0.0, _get_l0_val(cfg_key, default))


def _relation_family_label(family_key: str, relation_element: str = "") -> str:
    element = _ELEMENT_EN_TO_CN.get(str(relation_element or "").lower(), str(relation_element or ""))
    mapping = {
        "sanhui": f"三会{element}局" if element else "三会局",
        "sanhe": f"三合{element}局" if element else "三合局",
        "banhe_shengwang": f"生旺半合{element}势" if element else "生旺半合",
        "banhe_muwang": f"墓旺半合{element}势" if element else "墓旺半合",
        "gonghe": f"拱合{element}势" if element else "拱合",
        "liuhe": f"六合{element}势" if element else "六合",
        "anhe": "暗合",
    }
    return mapping.get(str(family_key or "").strip(), family_key or "关系局")


def _relation_trace_formation_ratio(trace: Dict[str, Any]) -> float:
    family_key = str(trace.get("family_key") or trace.get("kind") or "").strip()
    if not family_key:
        return 0.0
    clean_intensity = _relation_root_intensity(
        family_key=family_key,
        closeness=1.0,
        strength=1.0,
        completion=1.0,
        duplicate_bonus=0.0,
        conflict_damping=1.0,
    )
    if clean_intensity <= 0.0:
        return 0.0
    return max(0.0, min(1.0, float(trace.get("intensity") or 0.0) / clean_intensity))


def _relation_manifestation_mode(family_key: str, visible_support_strength: float) -> str:
    normalized = str(family_key or "").strip()
    if normalized == "anhe":
        return "暗化"
    return "明化" if float(visible_support_strength or 0.0) >= 0.18 else "暗化"


def _relation_source_loss_base(family_key: str) -> float:
    mapping = {
        "sanhui": ("REL_SOURCE_ATTENUATION_SANHUI", REL_SOURCE_ATTENUATION_SANHUI),
        "sanhe": ("REL_SOURCE_ATTENUATION_SANHE", REL_SOURCE_ATTENUATION_SANHE),
        "banhe_shengwang": ("REL_SOURCE_ATTENUATION_BANHE_SHENGWANG", REL_SOURCE_ATTENUATION_BANHE_SHENGWANG),
        "banhe_muwang": ("REL_SOURCE_ATTENUATION_BANHE_MUWANG", REL_SOURCE_ATTENUATION_BANHE_MUWANG),
        "gonghe": ("REL_SOURCE_ATTENUATION_GONGHE", REL_SOURCE_ATTENUATION_GONGHE),
        "liuhe": ("REL_SOURCE_ATTENUATION_LIUHE", REL_SOURCE_ATTENUATION_LIUHE),
        "anhe": ("REL_SOURCE_ATTENUATION_ANHE", REL_SOURCE_ATTENUATION_ANHE),
    }
    cfg_key, default = mapping.get(str(family_key or "").strip(), ("REL_SOURCE_ATTENUATION_SANHE", REL_SOURCE_ATTENUATION_SANHE))
    return max(0.0, _get_l0_val(cfg_key, default))


def _relation_source_min_retention(family_key: str) -> float:
    mapping = {
        "sanhui": ("REL_SOURCE_RETENTION_MIN_SANHUI", REL_SOURCE_RETENTION_MIN_SANHUI),
        "sanhe": ("REL_SOURCE_RETENTION_MIN_SANHE", REL_SOURCE_RETENTION_MIN_SANHE),
        "banhe_shengwang": ("REL_SOURCE_RETENTION_MIN_BANHE_SHENGWANG", REL_SOURCE_RETENTION_MIN_BANHE_SHENGWANG),
        "banhe_muwang": ("REL_SOURCE_RETENTION_MIN_BANHE_MUWANG", REL_SOURCE_RETENTION_MIN_BANHE_MUWANG),
        "gonghe": ("REL_SOURCE_RETENTION_MIN_GONGHE", REL_SOURCE_RETENTION_MIN_GONGHE),
        "liuhe": ("REL_SOURCE_RETENTION_MIN_LIUHE", REL_SOURCE_RETENTION_MIN_LIUHE),
        "anhe": ("REL_SOURCE_RETENTION_MIN_ANHE", REL_SOURCE_RETENTION_MIN_ANHE),
    }
    cfg_key, default = mapping.get(str(family_key or "").strip(), ("REL_SOURCE_RETENTION_MIN_SANHE", REL_SOURCE_RETENTION_MIN_SANHE))
    return max(0.0, min(1.0, _get_l0_val(cfg_key, default)))


def _relation_source_same_element_keep(family_key: str) -> float:
    mapping = {
        "sanhui": ("REL_SOURCE_KEEP_SAME_ELEMENT_SANHUI", REL_SOURCE_KEEP_SAME_ELEMENT_SANHUI),
        "sanhe": ("REL_SOURCE_KEEP_SAME_ELEMENT_SANHE", REL_SOURCE_KEEP_SAME_ELEMENT_SANHE),
        "banhe_shengwang": ("REL_SOURCE_KEEP_SAME_ELEMENT_BANHE_SHENGWANG", REL_SOURCE_KEEP_SAME_ELEMENT_BANHE_SHENGWANG),
        "banhe_muwang": ("REL_SOURCE_KEEP_SAME_ELEMENT_BANHE_MUWANG", REL_SOURCE_KEEP_SAME_ELEMENT_BANHE_MUWANG),
        "gonghe": ("REL_SOURCE_KEEP_SAME_ELEMENT_GONGHE", REL_SOURCE_KEEP_SAME_ELEMENT_GONGHE),
        "liuhe": ("REL_SOURCE_KEEP_SAME_ELEMENT_LIUHE", REL_SOURCE_KEEP_SAME_ELEMENT_LIUHE),
        "anhe": ("REL_SOURCE_KEEP_SAME_ELEMENT_ANHE", REL_SOURCE_KEEP_SAME_ELEMENT_ANHE),
    }
    cfg_key, default = mapping.get(str(family_key or "").strip(), ("REL_SOURCE_KEEP_SAME_ELEMENT_SANHE", REL_SOURCE_KEEP_SAME_ELEMENT_SANHE))
    return max(0.0, min(1.0, _get_l0_val(cfg_key, default)))


def _relation_source_role_factor(role: str) -> float:
    normalized = str(role or "").strip().lower()
    if normalized == "pivot":
        return 1.0
    if normalized == "tomb":
        return 0.78
    if normalized == "starter":
        return 0.64
    return 0.82


def _build_relation_source_retention_plan(
    *,
    branch_rows: List[Tuple[str, str]],
    relation_traces: List[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    branch_base_strengths: Dict[Tuple[str, str, str], float] = {}
    for scope, branch in branch_rows:
        scope_weight = float(ROOT_SCOPE_WEIGHTS.get(scope, 0.5))
        for hidden_stem, hidden_weight in BRANCH_HIDDEN.get(branch, []):
            branch_base_strengths[(scope, branch, hidden_stem)] = float(hidden_weight) * scope_weight

    retention_plan: Dict[Tuple[str, str, str], Dict[str, Any]] = {}
    summary_rows: List[Dict[str, Any]] = []
    valid_families = {"sanhui", "sanhe", "banhe_shengwang", "banhe_muwang", "gonghe", "liuhe", "anhe"}
    for trace in relation_traces:
        if not isinstance(trace, dict):
            continue
        family_key = str(trace.get("family_key") or trace.get("kind") or "").strip()
        if family_key not in valid_families:
            continue
        members = [str(x) for x in (trace.get("members") or []) if str(x).strip()]
        pillars = [str(x) for x in (trace.get("pillars") or []) if str(x).strip()]
        if not members or not pillars:
            continue
        rel_element = _ELEMENT_EN_TO_CN.get(
            str(trace.get("relation_element") or "").lower(),
            str(trace.get("relation_element") or ""),
        )
        details = trace.get("details") if isinstance(trace.get("details"), dict) else {}
        role_map = details.get("role_map") if isinstance(details.get("role_map"), dict) else {}
        visible_support_strength = max(0.0, min(1.0, float(details.get("visible_support_strength") or 0.0)))
        visibility_factor = 0.45 + visible_support_strength * 0.55
        conflict_damping = max(0.4, min(1.0, float(trace.get("conflict_damping") or 1.0)))
        base_loss = _relation_source_loss_base(family_key)
        formation_ratio = _relation_trace_formation_ratio(trace)
        source_base_total = 0.0
        source_retained_total = 0.0
        manifestation_mode = _relation_manifestation_mode(family_key, visible_support_strength)

        for scope, branch in zip(pillars, members):
            role = str(role_map.get(branch) or "peer")
            role_factor = _relation_source_role_factor(role)
            occurrence_loss = base_loss * formation_ratio * visibility_factor * conflict_damping * role_factor
            for hidden_stem, _hidden_weight in BRANCH_HIDDEN.get(branch, []):
                stem_el = STEM_ELEMENT.get(hidden_stem, "")
                is_source_component = not rel_element or stem_el != rel_element
                if is_source_component:
                    retention = max(_relation_source_min_retention(family_key), 1.0 - occurrence_loss)
                else:
                    retention = max(_relation_source_same_element_keep(family_key), 1.0 - occurrence_loss * 0.18)
                key = (scope, branch, hidden_stem)
                existing = retention_plan.get(key)
                if existing is None or float(retention) < float(existing.get("retention") or 1.0):
                    retention_plan[key] = {
                        "scope": scope,
                        "branch": branch,
                        "hidden_stem": hidden_stem,
                        "retention": round(float(retention), 4),
                        "family_key": family_key,
                        "manifestation_mode": manifestation_mode,
                    }
                if is_source_component:
                    base_strength = float(branch_base_strengths.get(key, 0.0))
                    source_base_total += base_strength
                    source_retained_total += base_strength * float(retention)

        source_retention_ratio = 1.0
        if source_base_total > 1e-9:
            source_retention_ratio = max(0.0, min(1.0, source_retained_total / source_base_total))
        summary_rows.append(
            {
                "family_key": family_key,
                "members": members,
                "source_retention_ratio": round(source_retention_ratio, 4),
                "source_release_ratio": round(max(0.0, 1.0 - source_retention_ratio), 4),
                "manifestation_mode": manifestation_mode,
            }
        )

    ordered_records = sorted(
        retention_plan.values(),
        key=lambda row: (
            str(row.get("scope") or ""),
            str(row.get("branch") or ""),
            str(row.get("hidden_stem") or ""),
        ),
    )
    return ordered_records, summary_rows


def _build_stem_fusion_source_retention_plan(
    *,
    stem_cases: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    records: Dict[Tuple[str, str], Dict[str, Any]] = {}
    base_loss = _get_l0_val("STEM_FUSION_SOURCE_ATTENUATION", STEM_FUSION_SOURCE_ATTENUATION)
    retention_floor = _get_l0_val("STEM_FUSION_SOURCE_RETENTION_MIN", STEM_FUSION_SOURCE_RETENTION_MIN)
    for case in stem_cases:
        if not isinstance(case, dict):
            continue
        mode = str(case.get("mode") or "").strip()
        if mode != "transformed":
            continue
        branch_ratio = max(
            0.0,
            min(1.0, float(case.get("branch_root_ratio") if case.get("branch_root_ratio") is not None else case.get("branch_hua_ratio") or 0.0)),
        )
        visible_support = max(0.0, min(1.0, float(case.get("visible_support_strength") or (1.0 if case.get("month_stem_supports") else 0.0))))
        support_score = max(
            0.0,
            min(
                1.0,
                float(
                    case.get("effective_support_score")
                    if case.get("effective_support_score") is not None
                    else case.get("support_score")
                    if case.get("support_score") is not None
                    else visible_support * 0.62 + branch_ratio * 0.38
                ),
            ),
        )
        interference_score = max(0.0, min(1.0, float(case.get("interference_score") or 0.0)))
        manifestation_mode = str(case.get("manifestation_mode") or ("明化" if case.get("month_stem_supports") else "暗化")).strip()
        pillars = [str(p) for p in (case.get("pillars") or []) if str(p).strip()]
        stems = [str(s) for s in (case.get("stems") or []) if str(s).strip()]
        if len(pillars) != len(stems) or not pillars:
            continue
        closeness = _pillars_group_closeness(pillars)
        efficiency = max(0.0, min(1.0, 0.18 + support_score * 0.68 - interference_score * 0.22))
        visibility_factor = 0.94 if manifestation_mode == "明化" else 0.68
        loss = base_loss * efficiency * max(0.62, closeness) * visibility_factor * max(0.72, 1.0 - interference_score * 0.32)
        retention = max(retention_floor, 1.0 - loss)
        for scope, stem in zip(pillars, stems):
            key = (scope, stem)
            existing = records.get(key)
            if existing is None or float(retention) < float(existing.get("retention") or 1.0):
                records[key] = {
                    "scope": scope,
                    "stem": stem,
                    "retention": round(float(retention), 4),
                    "kind": "stem_fusion_transform",
                    "manifestation_mode": manifestation_mode,
                    "hua_element": _ELEMENT_EN_TO_CN.get(
                        str(case.get("hua_element") or "").lower(),
                        str(case.get("hua_element") or ""),
                    ),
                }
    return sorted(records.values(), key=lambda row: (str(row.get("scope") or ""), str(row.get("stem") or "")))


def _build_relation_formation_summary(
    *,
    relation_traces: List[Dict[str, Any]],
    structural_bonuses: List[Dict[str, Any]],
    relation_visible_bonuses: List[Dict[str, Any]],
    relation_source_attenuations: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    return build_relation_formation_summary(
        relation_traces=relation_traces,
        structural_bonuses=structural_bonuses,
        relation_visible_bonuses=relation_visible_bonuses,
        relation_source_attenuations=relation_source_attenuations,
        relation_family_label=_relation_family_label,
        relation_base_factor=_relation_base_factor,
        relation_full_clean_factor=_relation_full_clean_factor,
        relation_root_intensity=_relation_root_intensity,
        relation_duplicate_role_bonus=_relation_duplicate_role_bonus,
    )


def _build_relation_dynamics_summary(
    *,
    relation_traces: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    return build_relation_dynamics_summary(
        relation_traces=relation_traces,
        relation_family_label=_relation_family_label,
        relation_trace_formation_ratio=_relation_trace_formation_ratio,
    )


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
    for starter, pivot, tomb, element in _SANHUI_GROUPS:
        group = {starter, pivot, tomb}
        if not group.issubset(present):
            continue
        matched = [(p, br) for p, br in branches.items() if br in group]
        pillars = [p for p, _ in matched]
        matched_branches = [br for _, br in matched]
        branch_counts: Dict[str, int] = {}
        for br in matched_branches:
            branch_counts[br] = branch_counts.get(br, 0) + 1
        unique_count = len(group)
        duplicate_count = max(0, len(matched_branches) - unique_count)
        completion = 1.0
        role_map = {starter: "starter", pivot: "pivot", tomb: "tomb"}
        duplicate_bonus, duplicate_roles = _relation_duplicate_bonus(branch_counts, role_map)
        strength = (
            0.52
            + completion * 0.54
            + duplicate_bonus
            + max(0.0, _pillars_group_closeness(pillars) - 0.8) * 0.25
        )
        hits.append(
            {
                "group": [starter, pivot, tomb],
                "ordered_group": [starter, pivot, tomb],
                "matched_branches": matched_branches,
                "pillars": pillars,
                "branch_counts": branch_counts,
                "duplicate_count": duplicate_count,
                "duplicate_bonus": round(duplicate_bonus, 4),
                "duplicate_roles": duplicate_roles,
                "completion": round(completion, 4),
                "strength": round(max(0.0, min(1.55, strength)), 4),
                "element": element,
                "pivot_branch": pivot,
                "tomb_branch": tomb,
                "role_map": role_map,
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
    rel_el = _ELEMENT_EN_TO_CN.get(str(relation_element or "").lower(), str(relation_element or ""))
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
    rel_el = _ELEMENT_EN_TO_CN.get(str(target_element or "").lower(), str(target_element or ""))
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
    branch_hidden_base_strengths: Dict[Tuple[str, str, str], float] = {}
    stems: Dict[str, str] = _build_runtime_stems(
        four_pillars,
        luck_pillar,
        flow_pillar,
        parse_gz=_parse_gz,
    )

    branch_scope_totals: Dict[str, float] = {}
    for scope_key, branch in branch_rows:
        scope = float(ROOT_SCOPE_WEIGHTS.get(scope_key, 0.5))
        branch_scope_totals[branch] = branch_scope_totals.get(branch, 0.0) + scope
        for hidden_stem, hidden_weight in BRANCH_HIDDEN.get(branch, []):
            strength = float(hidden_weight) * scope
            branch_hidden_base_strengths[(scope_key, branch, hidden_stem)] = strength
            rooted[hidden_stem] = rooted.get(hidden_stem, 0.0) + strength

    static_rooted = dict(rooted)
    relation_delta_raw: Dict[str, float] = {}
    relation_traces: List[Dict[str, Any]] = []
    stem_cases: List[Dict[str, Any]] = []

    if branches:
        relation_hit_bundle = _detect_relation_runtime_hits(
            branches,
            eval_sanhe_hits=eval_sanhe_hits,
            eval_sanhui_hits=_eval_sanhui_hits,
            eval_banhe_hits=eval_banhe_hits,
            eval_gonghe_hits=eval_gonghe_hits,
            eval_liuhe_hits=eval_liuhe_hits,
            eval_anhe_hits=eval_anhe_hits,
            eval_liu_chong_hits=eval_liu_chong_hits,
            eval_liu_hai_hits=eval_liu_hai_hits,
            eval_liu_po_hits=eval_liu_po_hits,
            sanxing_detect_geometry=sanxing_detect_geometry,
        )
        sanhe_hits = relation_hit_bundle["sanhe_hits"]
        sanhui_hits = relation_hit_bundle["sanhui_hits"]
        banhe_hits = relation_hit_bundle["banhe_hits"]
        gonghe_hits = relation_hit_bundle["gonghe_hits"]
        liuhe_hits = relation_hit_bundle["liuhe_hits"]
        anhe_hits = relation_hit_bundle["anhe_hits"]
        chong_hits = relation_hit_bundle["chong_hits"]
        hai_hits = relation_hit_bundle["hai_hits"]
        po_hits = relation_hit_bundle["po_hits"]
        xing_hits = relation_hit_bundle["xing_hits"]
        conflicted_branches = relation_hit_bundle["conflicted_branches"]
        conflict_events = relation_hit_bundle["conflict_events"]

        _collect_structured_relation_family_deltas(
            sanhe_hits=sanhe_hits,
            sanhui_hits=sanhui_hits,
            banhe_hits=banhe_hits,
            gonghe_hits=gonghe_hits,
            liuhe_hits=liuhe_hits,
            anhe_hits=anhe_hits,
            conflicted_branches=conflicted_branches,
            conflict_events=conflict_events,
            four_pillars=four_pillars,
            luck_pillar=luck_pillar,
            flow_pillar=flow_pillar,
            branch_scope_totals=branch_scope_totals,
            relation_delta_raw=relation_delta_raw,
            relation_traces=relation_traces,
            branch_hidden=BRANCH_HIDDEN,
            stem_element_map=STEM_ELEMENT,
            banhe_pair_to_element=_BANHE_PAIR_TO_ELEMENT,
            gonghe_pair_to_element=_GONGHE_PAIR_TO_ELEMENT,
            liuhe_pair_to_element=_LIUHE_PAIR_TO_ELEMENT,
            pillars_group_closeness=_pillars_group_closeness,
            relation_factor_bundle=_relation_factor_bundle,
            relation_conflict_damping=_relation_conflict_damping,
            relation_root_intensity=_relation_root_intensity,
            relation_duplicate_bonus=_relation_duplicate_bonus,
            relation_duplicate_role_bonus=_relation_duplicate_role_bonus,
            relation_apply_branch_delta=_relation_apply_branch_delta,
            relation_dominant_hidden_stem=_relation_dominant_hidden_stem,
            append_relation_trace=_append_relation_trace,
        )

        _collect_penalty_relation_deltas(
            chong_hits=chong_hits,
            hai_hits=hai_hits,
            po_hits=po_hits,
            xing_hits=xing_hits,
            branch_scope_totals=branch_scope_totals,
            relation_delta_raw=relation_delta_raw,
            relation_traces=relation_traces,
            pillars_group_closeness=_pillars_group_closeness,
            get_penalty_value=_get_l0_val,
            relation_apply_branch_delta=_relation_apply_branch_delta,
            append_relation_trace=_append_relation_trace,
            penalty_chong_default=REL_ROOT_PENALTY_CHONG,
            penalty_hai_default=REL_ROOT_PENALTY_HAI,
            penalty_po_default=REL_ROOT_PENALTY_PO,
            penalty_xing_default=REL_ROOT_PENALTY_XING,
        )

        _collect_control_relation_deltas(
            branches=branches,
            branch_element_map=BRANCH_ELEMENT,
            control_adj_scope_pairs=_CONTROL_ADJ_SCOPE_PAIRS,
            branch_scope_totals=branch_scope_totals,
            relation_delta_raw=relation_delta_raw,
            relation_traces=relation_traces,
            pillar_pair_closeness=_pillar_pair_closeness,
            controls_element=_controls_element,
            get_l0_val=_get_l0_val,
            relation_apply_branch_delta=_relation_apply_branch_delta,
            append_relation_trace=_append_relation_trace,
            control_bonus_default=REL_ROOT_CONTROL_BONUS,
            control_penalty_default=REL_ROOT_CONTROL_PENALTY,
        )

        # 天干五合“化学效率”量化：以 branch_hua_ratio 与月干支持作为效率源。
        stem_cases = _collect_stem_fusion_relation_deltas(
            stems=stems,
            branches=branches,
            static_rooted=static_rooted,
            relation_delta_raw=relation_delta_raw,
            relation_traces=relation_traces,
            detect_stem_fusion_cases=detect_stem_fusion_cases,
            pillars_group_closeness=_pillars_group_closeness,
            get_l0_val=_get_l0_val,
            relation_apply_stem_element_delta=_relation_apply_stem_element_delta,
            append_relation_trace=_append_relation_trace,
            element_en_to_cn=_ELEMENT_EN_TO_CN,
            stem_element_map=STEM_ELEMENT,
            bonus_anhe_default=REL_ROOT_BONUS_ANHE,
            penalty_po_default=REL_ROOT_PENALTY_PO,
        )

    return _finalize_root_dynamic_state(
        branch_rows=branch_rows,
        relation_traces=relation_traces,
        branch_hidden_base_strengths=branch_hidden_base_strengths,
        static_rooted=static_rooted,
        relation_delta_raw=relation_delta_raw,
        stem_cases=stem_cases,
        build_relation_source_retention_plan=_build_relation_source_retention_plan,
        build_stem_fusion_source_retention_plan=_build_stem_fusion_source_retention_plan,
    )


def _collect_root_strengths(four_pillars: Dict[str, str], luck_pillar: str, flow_pillar: str) -> Dict[str, float]:
    rooted, _meta = _collect_root_strengths_with_meta(four_pillars, luck_pillar, flow_pillar)
    return rooted


def _relation_branch_role(branch: str, pivot_branch: str, tomb_branch: str) -> str:
    if branch == pivot_branch:
        return "pivot"
    if branch == tomb_branch:
        return "tomb"
    return "starter"


def _relation_projection_weights(
    *,
    hit: Dict[str, Any],
    family_key: str,
    daymaster: str,
    four_pillars: Dict[str, str],
    luck_pillar: str,
    flow_pillar: str,
) -> Dict[str, float]:
    pivot_branch = str(hit.get("pivot_branch") or hit.get("mid_branch") or "")
    tomb_branch = str(hit.get("tomb_branch") or "")
    branches = [str(x) for x in (hit.get("matched_branches") or hit.get("group") or []) if str(x).strip()]
    if not branches:
        return {}
    main_hidden = BRANCH_HIDDEN.get(pivot_branch, [])
    if not main_hidden:
        return {}
    target_element = STEM_ELEMENT.get(main_hidden[0][0], "")
    if not target_element:
        return {}
    role_weights_by_family = {
        "sanhui": {"pivot": 1.36, "tomb": 0.90, "starter": 0.66},
        "sanhe": {"pivot": 1.25, "tomb": 0.92, "starter": 0.58},
    }
    role_weights = role_weights_by_family.get(family_key, role_weights_by_family["sanhe"])
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
        role = _relation_branch_role(branch, pivot_branch, tomb_branch)
        role_weight = float(role_weights.get(role, 0.6))
        pillar_weight = float(pillar_weights.get(pillar, 0.9))
        for hidden_stem, hidden_weight in BRANCH_HIDDEN.get(branch, []):
            if STEM_ELEMENT.get(hidden_stem) != target_element:
                continue
            god = ten_god_from_stems(daymaster, hidden_stem)
            weights[god] = weights.get(god, 0.0) + float(hidden_weight) * role_weight * pillar_weight

    for scope, stem in _visible_stem_scope_weights(
        four_pillars,
        luck_pillar,
        flow_pillar,
        parse_gz=_parse_gz,
    ):
        if STEM_ELEMENT.get(stem) != target_element:
            continue
        # 动态透干口径：月干最强，日干有效并参与计算，但仍不回流为静态显化。
        scope_weight = _relation_visible_scope_weight(scope)
        if scope_weight <= 0.0:
            continue
        god = ten_god_from_stems(daymaster, stem)
        weights[god] = weights.get(god, 0.0) + scope_weight

    total = sum(weights.values())
    if total <= 0:
        return {}
    return {god: weight / total for god, weight in weights.items() if weight > 0}


def _apply_relation_foundation_bonuses(
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
    sanhui_hits = _eval_sanhui_hits(branches) if branches else []
    conflicted_branches: set[str] = set()
    conflict_events: List[set[str]] = []
    for hit in eval_liu_chong_hits(branches) if branches else []:
        pair = {str(x) for x in (hit.get("pair") or []) if str(x).strip()}
        conflicted_branches.update(pair)
        if pair:
            conflict_events.append(pair)
    for hit in eval_liu_hai_hits(branches) if branches else []:
        pair = {str(x) for x in (hit.get("pair") or []) if str(x).strip()}
        conflicted_branches.update(pair)
        if pair:
            conflict_events.append(pair)
    for hit in eval_liu_po_hits(branches) if branches else []:
        pair = {str(x) for x in (hit.get("pair") or []) if str(x).strip()}
        conflicted_branches.update(pair)
        if pair:
            conflict_events.append(pair)
    for hit in sanxing_detect_geometry(branches) if branches else []:
        members = {str(x) for x in (hit.get("branches") or []) if str(x).strip()}
        conflicted_branches.update(members)
        if members:
            conflict_events.append(members)
    bonuses: List[Dict[str, Any]] = []
    relation_hits: List[Tuple[str, Dict[str, Any]]] = [("sanhe", hit) for hit in sanhe_hits] + [("sanhui", hit) for hit in sanhui_hits]
    if not relation_hits:
        return bonuses

    structure_scale_defaults = {
        "sanhe": REL_FAMILY_STRUCTURE_SCALE_SANHE,
        "sanhui": REL_FAMILY_STRUCTURE_SCALE_SANHUI,
    }
    for family_key, hit in relation_hits:
        strength = float(hit.get("strength") or 1.0)
        duplicate_bonus = max(0.0, float(hit.get("duplicate_bonus") or 0.0))
        completion = max(0.0, min(1.0, float(hit.get("completion") or 1.0)))
        pivot_factor = float(hit.get("pivot_factor") or 0.9)
        members = [str(x) for x in (hit.get("matched_branches") or hit.get("group") or []) if str(x).strip()]
        if family_key == "sanhui":
            relation_element = str(hit.get("element") or "")
            dominant_hidden_stem = _relation_dominant_hidden_stem(
                relation_element=relation_element,
                members=members,
                four_pillars=four_pillars,
                luck_pillar=luck_pillar,
                flow_pillar=flow_pillar,
            )
        else:
            pivot_branch = str(hit.get("pivot_branch") or hit.get("mid_branch") or "")
            dominant_hidden_stem = BRANCH_HIDDEN.get(pivot_branch, [("", 0.0)])[0][0] if pivot_branch else ""
            relation_element = STEM_ELEMENT.get(dominant_hidden_stem, "") if dominant_hidden_stem else ""
        factor_bundle = _relation_factor_bundle(
            family_key=family_key,
            relation_element=relation_element,
            members=members,
            dominant_hidden_stem=dominant_hidden_stem,
            four_pillars=four_pillars,
            luck_pillar=luck_pillar,
            flow_pillar=flow_pillar,
        )
        projection = _relation_projection_weights(
            hit=hit,
            family_key=family_key,
            daymaster=daymaster,
            four_pillars=four_pillars,
            luck_pillar=luck_pillar,
            flow_pillar=flow_pillar,
        )
        if not projection:
            continue
        pillars = [str(p) for p in (hit.get("pillars") or []) if str(p).strip()]
        closeness = _pillars_group_closeness(pillars)
        conflict_damping = _relation_conflict_damping(
            members=members,
            family_key=family_key,
            conflicted_branches=conflicted_branches,
            conflict_events=conflict_events,
        )
        direct_support_strength = max(projection.values()) if projection else 0.0
        family_factor = float(factor_bundle.get("effective_family_factor") or _relation_full_clean_factor(family_key))
        structure_scale = _get_l0_val(
            f"REL_FAMILY_STRUCTURE_SCALE_{family_key.upper()}",
            structure_scale_defaults.get(family_key, 0.0),
        )
        bonus_total = (
            _get_l0_val("BRANCH_BASE", 12.0)
            * max(0.0, family_factor - 1.0)
            * max(0.65, closeness)
            * max(0.68, strength)
            * max(0.24, completion)
            * (1.0 + duplicate_bonus)
            * max(0.18, conflict_damping)
            * max(0.0, structure_scale)
            * (1.0 + 0.18 * max(0.0, pivot_factor - 0.9))
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
                f"L0_{family_key.upper()}_FORMATION",
                f"{family_key}结构回灌·{''.join(hit.get('group') or [])}·share={share:.2f}·dup={duplicate_bonus:.2f}",
            )
        bonuses.append(
            {
                "kind": family_key,
                "group": list(hit.get("group") or []),
                "matched_branches": list(hit.get("matched_branches") or []),
                "mid_branch": str(hit.get("pivot_branch") or hit.get("mid_branch") or ""),
                "duplicate_count": max(0, int(hit.get("duplicate_count") or 0)),
                "duplicate_bonus": round(duplicate_bonus, 4),
                "pivot_factor": round(pivot_factor, 3),
                "strength": round(strength, 3),
                "completion": round(completion, 4),
                "closeness": round(closeness, 4),
                "conflict_damping": round(conflict_damping, 4),
                "family_factor": round(family_factor, 4),
                "visible_support_strength": float(factor_bundle.get("visible_support_strength") or 0.0),
                "dominant_hidden_stem": str(factor_bundle.get("dominant_hidden_stem") or ""),
                "bonus_total": round(bonus_total, 3),
                "projection": {god: round(float(share), 4) for god, share in projection.items()},
            }
        )
    return bonuses


def _relation_visible_scope_weight(scope: str) -> float:
    return float(REL_VISIBLE_SCOPE_WEIGHTS.get(scope, 0.0))


def _relation_visible_support_strength(
    *,
    relation_element: str,
    dominant_hidden_stem: str,
    four_pillars: Dict[str, str],
    luck_pillar: str,
    flow_pillar: str,
) -> float:
    rel_el = _ELEMENT_EN_TO_CN.get(str(relation_element or "").lower(), str(relation_element or ""))
    if not rel_el:
        return 0.0
    cross_factor = _get_l0_val("REL_VISIBLE_CROSS_POLARITY_FACTOR", REL_VISIBLE_CROSS_POLARITY_FACTOR)
    support = 0.0
    for scope, stem in _visible_stem_scope_weights(
        four_pillars,
        luck_pillar,
        flow_pillar,
        parse_gz=_parse_gz,
    ):
        if STEM_ELEMENT.get(stem, "") != rel_el:
            continue
        scope_weight = _relation_visible_scope_weight(scope)
        if scope_weight <= 0.0:
            continue
        polarity_factor = 1.0
        if dominant_hidden_stem and stem != dominant_hidden_stem:
            polarity_factor = cross_factor
        support += scope_weight * polarity_factor
    return max(0.0, min(1.0, support))


def _relation_factor_bundle(
    *,
    family_key: str,
    relation_element: str,
    members: List[str],
    dominant_hidden_stem: str,
    four_pillars: Dict[str, str],
    luck_pillar: str,
    flow_pillar: str,
) -> Dict[str, float | str]:
    visible_support_strength = _relation_visible_support_strength(
        relation_element=relation_element,
        dominant_hidden_stem=dominant_hidden_stem,
        four_pillars=four_pillars,
        luck_pillar=luck_pillar,
        flow_pillar=flow_pillar,
    )
    effective_family_factor = _relation_effective_factor(family_key, visible_support_strength)
    return {
        "dominant_hidden_stem": dominant_hidden_stem,
        "visible_support_strength": round(visible_support_strength, 4),
        "effective_family_factor": round(effective_family_factor, 4),
    }


def _relation_dominant_hidden_stem(
    *,
    relation_element: str,
    members: List[str],
    four_pillars: Dict[str, str],
    luck_pillar: str,
    flow_pillar: str,
) -> str:
    normalized_relation_element = _ELEMENT_EN_TO_CN.get(str(relation_element or "").lower(), str(relation_element or ""))
    if not normalized_relation_element or not members:
        return ""
    branch_rows = _runtime_branch_rows(four_pillars, luck_pillar, flow_pillar)
    member_set = {str(member) for member in members if str(member).strip()}
    hidden_totals: Dict[str, float] = {}
    for scope, branch in branch_rows:
        if branch not in member_set:
            continue
        scope_weight = float(ROOT_SCOPE_WEIGHTS.get(scope, 0.5))
        for hidden_stem, hidden_weight in BRANCH_HIDDEN.get(branch, []):
            if STEM_ELEMENT.get(hidden_stem, "") != normalized_relation_element:
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
    rel_el = _ELEMENT_EN_TO_CN.get(str(relation_element or "").lower(), str(relation_element or ""))
    if not rel_el:
        return {}
    cross_factor = _get_l0_val("REL_VISIBLE_CROSS_POLARITY_FACTOR", REL_VISIBLE_CROSS_POLARITY_FACTOR)
    weights: Dict[str, float] = {}
    for scope, stem in _visible_stem_scope_weights(
        four_pillars,
        luck_pillar,
        flow_pillar,
        parse_gz=_parse_gz,
    ):
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
    for trace in relation_traces:
        kind = str(trace.get("kind") or "")
        family_key = str(trace.get("family_key") or kind)
        relation_element = _ELEMENT_EN_TO_CN.get(
            str(trace.get("relation_element") or "").lower(),
            str(trace.get("relation_element") or ""),
        )
        intensity = float(trace.get("intensity") or 0.0)
        members = [str(x) for x in (trace.get("members") or []) if str(x).strip()]
        if not relation_element or intensity <= 0.0 or not members:
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
        _scale_key, scale = _relation_visible_resonance_scale(family_key)
        if scale <= 0.0:
            continue
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
                f"L0_REL_VISIBLE_{family_key.upper()}",
                f"{family_key}显神导流·{relation_element}→{god}·share={share:.2f}·dominant={dominant_hidden_stem or '—'}",
            )
        bonuses.append(
            {
                "kind": kind,
                "family_key": family_key,
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
    return build_projection_bridge_protocol(
        cross_polarity_root_support_factor=_get_l0_val(
            "CROSS_POLARITY_ROOT_SUPPORT_FACTOR",
            CROSS_POLARITY_ROOT_SUPPORT_FACTOR,
        ),
        exact_exposed_hidden_gain=_get_l0_val("EXPOSED_HIDDEN_GAIN", EXPOSED_HIDDEN_GAIN),
        rooted_gain_cap=_get_l0_val("ROOTED_GAIN", ROOTED_STEM_GAIN),
    )


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
    visible_stems = _collect_visible_stems(
        four_pillars,
        luck_pillar,
        flow_pillar,
        parse_gz=_parse_gz,
    )
    root_strengths, root_dynamic_meta = _collect_root_strengths_with_meta(four_pillars, luck_pillar, flow_pillar)
    branch_source_retention_map = {
        (str(row.get("scope") or ""), str(row.get("branch") or ""), str(row.get("hidden_stem") or "")): row
        for row in (root_dynamic_meta.get("branch_source_retention") or [])
        if isinstance(row, dict)
    }
    stem_source_retention_map = {
        (str(row.get("scope") or ""), str(row.get("stem") or "")): row
        for row in (root_dynamic_meta.get("stem_source_retention") or [])
        if isinstance(row, dict)
    }
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
                stem_scope=pillar_key,
                daymaster=daymaster,
                source_factor=stem_position_factor * s_comp,
                season_multiplier=1.0,
                root_strengths=root_strengths,
                stem_source_retention_map=stem_source_retention_map,
                acc=acc,
                decomposition=decomposition,
                pillar_label=p_label,
                proximity_factor=stem_position_factor,
                ledger=ledger,
                get_l0_val=_get_l0_val,
                stem_base=STEM_BASE,
                ten_god_from_stems=ten_god_from_stems,
                add_decomposition=_add_decomposition,
                cross_polarity_root_support=lambda s, rooted: _cross_polarity_root_support(
                    s,
                    rooted,
                    stem_element_map=STEM_ELEMENT,
                    stem_yin_map=STEM_YIN,
                    cross_polarity_root_support_factor=_get_l0_val("CROSS_POLARITY_ROOT_SUPPORT_FACTOR", 0.55),
                ),
                logger=_log,
            )
        # 地支能量（藏干逐一累加，各自带 Season Power）
        branch_source_factor = float(NATAL_BRANCH_POSITION_WEIGHTS.get(pillar_key, 0.8)) * b_comp
        _accumulate_branch_energy(
            branch=branch,
            branch_scope=pillar_key,
            daymaster=daymaster,
            source_factor=branch_source_factor,
            void_factor=pillar_void_factor,
            month_branch=month_branch,
            apply_month_order=(pillar_key == "month"),
            visible_stems=visible_stems,
            branch_source_retention_map=branch_source_retention_map,
            acc=acc,
            decomposition=decomposition,
            pillar_label=p_label,
            ledger=ledger,
            get_l0_val=_get_l0_val,
            branch_hidden=BRANCH_HIDDEN,
            branch_base=BRANCH_BASE,
            stem_element_map=STEM_ELEMENT,
            ten_god_from_stems=ten_god_from_stems,
            add_decomposition=_add_decomposition,
            same_element_visible=lambda hidden_stem, stems: _same_element_visible(
                hidden_stem,
                stems,
                stem_element_map=STEM_ELEMENT,
            ),
            season_multiplier_fn=_season_multiplier,
            branch_stage_for_daymaster_fn=lambda dm, br: _branch_stage_for_daymaster(
                dm,
                br,
                stem_element_map=STEM_ELEMENT,
                chang_sheng_table=CHANG_SHENG_TABLE,
                chang_sheng_stages=CHANG_SHENG_STAGES,
                chang_sheng_bonus_map=CHANG_SHENG_BONUS_MAP,
            ),
            split_stage_component_fn=_split_stage_component,
            logger=_log,
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
                stem_scope="luck" if sf_label == "运" else "flow",
                daymaster=daymaster,
                source_factor=source_factor,
                season_multiplier=1.0,
                root_strengths=root_strengths,
                stem_source_retention_map=stem_source_retention_map,
                acc=acc,
                decomposition=decomposition,
                pillar_label=sf_label,
                ledger=ledger,
                get_l0_val=_get_l0_val,
                stem_base=STEM_BASE,
                ten_god_from_stems=ten_god_from_stems,
                add_decomposition=_add_decomposition,
                cross_polarity_root_support=lambda s, rooted: _cross_polarity_root_support(
                    s,
                    rooted,
                    stem_element_map=STEM_ELEMENT,
                    stem_yin_map=STEM_YIN,
                    cross_polarity_root_support_factor=_get_l0_val("CROSS_POLARITY_ROOT_SUPPORT_FACTOR", 0.55),
                ),
                logger=_log,
            )
            _accumulate_branch_energy(
                branch=branch,
                branch_scope="luck" if sf_label == "运" else "flow",
                daymaster=daymaster,
                source_factor=source_factor,
                void_factor=1.0,
                month_branch=month_branch,
                apply_month_order=False,
                visible_stems=visible_stems,
                branch_source_retention_map=branch_source_retention_map,
                acc=acc,
                decomposition=decomposition,
                pillar_label=sf_label,
                ledger=ledger,
                get_l0_val=_get_l0_val,
                branch_hidden=BRANCH_HIDDEN,
                branch_base=BRANCH_BASE,
                stem_element_map=STEM_ELEMENT,
                ten_god_from_stems=ten_god_from_stems,
                add_decomposition=_add_decomposition,
                same_element_visible=lambda hidden_stem, stems: _same_element_visible(
                    hidden_stem,
                    stems,
                    stem_element_map=STEM_ELEMENT,
                ),
                season_multiplier_fn=_season_multiplier,
                branch_stage_for_daymaster_fn=lambda dm, br: _branch_stage_for_daymaster(
                    dm,
                    br,
                    stem_element_map=STEM_ELEMENT,
                    chang_sheng_table=CHANG_SHENG_TABLE,
                    chang_sheng_stages=CHANG_SHENG_STAGES,
                    chang_sheng_bonus_map=CHANG_SHENG_BONUS_MAP,
                ),
                split_stage_component_fn=_split_stage_component,
                logger=_log,
            )

    structural_bonuses = _apply_relation_foundation_bonuses(
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
    relation_formation_summary = _build_relation_formation_summary(
        relation_traces=list(root_dynamic_meta.get("traces") or []),
        structural_bonuses=structural_bonuses,
        relation_visible_bonuses=relation_visible_bonuses,
        relation_source_attenuations=list(root_dynamic_meta.get("source_attenuation_summary") or []),
    )
    relation_dynamics_summary = _build_relation_dynamics_summary(
        relation_traces=list(root_dynamic_meta.get("traces") or []),
    )
    climate_field = build_climate_field(
        four_pillars=four_pillars,
        luck_pillar=luck_pillar,
        flow_pillar=flow_pillar,
        daymaster=daymaster,
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
            "rel_visible_scope_weights": dict(REL_VISIBLE_SCOPE_WEIGHTS),
            "rooted_stem_gain": ROOTED_STEM_GAIN,
            "rel_family_base_factor_sanhui": _relation_base_factor("sanhui"),
            "rel_family_base_factor_sanhe": _relation_base_factor("sanhe"),
            "rel_family_base_factor_banhe_shengwang": _relation_base_factor("banhe_shengwang"),
            "rel_family_base_factor_banhe_muwang": _relation_base_factor("banhe_muwang"),
            "rel_family_base_factor_gonghe": _relation_base_factor("gonghe"),
            "rel_family_base_factor_liuhe": _relation_base_factor("liuhe"),
            "rel_family_base_factor_anhe": _relation_base_factor("anhe"),
            "rel_family_full_clean_sanhui": _relation_full_clean_factor("sanhui"),
            "rel_family_full_clean_sanhe": _relation_full_clean_factor("sanhe"),
            "rel_family_full_clean_banhe_shengwang": _relation_full_clean_factor("banhe_shengwang"),
            "rel_family_full_clean_banhe_muwang": _relation_full_clean_factor("banhe_muwang"),
            "rel_family_full_clean_gonghe": _relation_full_clean_factor("gonghe"),
            "rel_family_full_clean_liuhe": _relation_full_clean_factor("liuhe"),
            "rel_family_full_clean_anhe": _relation_full_clean_factor("anhe"),
            "rel_family_root_unit": _get_l0_val("REL_FAMILY_ROOT_UNIT", REL_FAMILY_ROOT_UNIT),
            "rel_root_bonus_sanhe": REL_ROOT_BONUS_SANHE,
            "rel_root_bonus_sanhui": REL_ROOT_BONUS_SANHUI,
            "rel_root_bonus_banhe": REL_ROOT_BONUS_BANHE,
            "rel_root_bonus_gonghe": REL_ROOT_BONUS_GONGHE,
            "rel_root_bonus_liuhe": REL_ROOT_BONUS_LIUHE,
            "rel_root_bonus_anhe": REL_ROOT_BONUS_ANHE,
            "rel_duplicate_bonus_pivot": _get_l0_val("REL_DUPLICATE_BONUS_PIVOT", REL_DUPLICATE_BONUS_PIVOT),
            "rel_duplicate_bonus_tomb": _get_l0_val("REL_DUPLICATE_BONUS_TOMB", REL_DUPLICATE_BONUS_TOMB),
            "rel_duplicate_bonus_starter": _get_l0_val("REL_DUPLICATE_BONUS_STARTER", REL_DUPLICATE_BONUS_STARTER),
            "rel_visible_stem_resonance_sanhe": _relation_visible_resonance_scale("sanhe")[1],
            "rel_visible_stem_resonance_banhe": REL_VISIBLE_STEM_RESONANCE_BANHE,
            "rel_visible_stem_resonance_sanhui": REL_VISIBLE_STEM_RESONANCE_SANHUI,
            "rel_visible_stem_resonance_banhe_shengwang": _relation_visible_resonance_scale("banhe_shengwang")[1],
            "rel_visible_stem_resonance_banhe_muwang": _relation_visible_resonance_scale("banhe_muwang")[1],
            "rel_visible_stem_resonance_gonghe": _relation_visible_resonance_scale("gonghe")[1],
            "rel_visible_stem_resonance_liuhe": REL_VISIBLE_STEM_RESONANCE_LIUHE,
            "rel_visible_stem_resonance_anhe": REL_VISIBLE_STEM_RESONANCE_ANHE,
            "rel_visible_cross_polarity_factor": REL_VISIBLE_CROSS_POLARITY_FACTOR,
            "rel_source_attenuation_sanhui": _relation_source_loss_base("sanhui"),
            "rel_source_attenuation_sanhe": _relation_source_loss_base("sanhe"),
            "rel_source_attenuation_banhe_shengwang": _relation_source_loss_base("banhe_shengwang"),
            "rel_source_attenuation_banhe_muwang": _relation_source_loss_base("banhe_muwang"),
            "rel_source_attenuation_gonghe": _relation_source_loss_base("gonghe"),
            "rel_source_attenuation_liuhe": _relation_source_loss_base("liuhe"),
            "rel_source_attenuation_anhe": _relation_source_loss_base("anhe"),
            "stem_fusion_source_attenuation": _get_l0_val("STEM_FUSION_SOURCE_ATTENUATION", STEM_FUSION_SOURCE_ATTENUATION),
            "stem_fusion_visible_support_month": _get_l0_val("STEM_FUSION_VISIBLE_SUPPORT_MONTH", STEM_FUSION_VISIBLE_SUPPORT_MONTH),
            "stem_fusion_visible_support_day": _get_l0_val("STEM_FUSION_VISIBLE_SUPPORT_DAY", STEM_FUSION_VISIBLE_SUPPORT_DAY),
            "stem_fusion_visible_support_hour": _get_l0_val("STEM_FUSION_VISIBLE_SUPPORT_HOUR", STEM_FUSION_VISIBLE_SUPPORT_HOUR),
            "stem_fusion_visible_support_year": _get_l0_val("STEM_FUSION_VISIBLE_SUPPORT_YEAR", STEM_FUSION_VISIBLE_SUPPORT_YEAR),
            "stem_fusion_visible_support_luck": _get_l0_val("STEM_FUSION_VISIBLE_SUPPORT_LUCK", STEM_FUSION_VISIBLE_SUPPORT_LUCK),
            "stem_fusion_visible_support_flow": _get_l0_val("STEM_FUSION_VISIBLE_SUPPORT_FLOW", STEM_FUSION_VISIBLE_SUPPORT_FLOW),
            "stem_fusion_branch_root_month": _get_l0_val("STEM_FUSION_BRANCH_ROOT_MONTH", STEM_FUSION_BRANCH_ROOT_MONTH),
            "stem_fusion_branch_root_day": _get_l0_val("STEM_FUSION_BRANCH_ROOT_DAY", STEM_FUSION_BRANCH_ROOT_DAY),
            "stem_fusion_branch_root_hour": _get_l0_val("STEM_FUSION_BRANCH_ROOT_HOUR", STEM_FUSION_BRANCH_ROOT_HOUR),
            "stem_fusion_branch_root_year": _get_l0_val("STEM_FUSION_BRANCH_ROOT_YEAR", STEM_FUSION_BRANCH_ROOT_YEAR),
            "stem_fusion_branch_root_luck": _get_l0_val("STEM_FUSION_BRANCH_ROOT_LUCK", STEM_FUSION_BRANCH_ROOT_LUCK),
            "stem_fusion_branch_root_flow": _get_l0_val("STEM_FUSION_BRANCH_ROOT_FLOW", STEM_FUSION_BRANCH_ROOT_FLOW),
            "stem_fusion_support_visible_weight": _get_l0_val("STEM_FUSION_SUPPORT_VISIBLE_WEIGHT", STEM_FUSION_SUPPORT_VISIBLE_WEIGHT),
            "stem_fusion_support_branch_weight": _get_l0_val("STEM_FUSION_SUPPORT_BRANCH_WEIGHT", STEM_FUSION_SUPPORT_BRANCH_WEIGHT),
            "stem_fusion_interference_branch_weight": _get_l0_val("STEM_FUSION_INTERFERENCE_BRANCH_WEIGHT", STEM_FUSION_INTERFERENCE_BRANCH_WEIGHT),
            "stem_fusion_interference_stem_weight": _get_l0_val("STEM_FUSION_INTERFERENCE_STEM_WEIGHT", STEM_FUSION_INTERFERENCE_STEM_WEIGHT),
            "stem_fusion_effective_threshold": _get_l0_val("STEM_FUSION_EFFECTIVE_THRESHOLD", STEM_FUSION_EFFECTIVE_THRESHOLD),
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
        "relation_formation_summary": relation_formation_summary,
        "relation_dynamics_summary": relation_dynamics_summary,
        "climate_field": climate_field,
        "climate_modifier_layer": dict(climate_field.get("climate_modifier_layer") or {}),
        "projection_bridge_protocol": _projection_bridge_protocol(),
        "ledger": ledger,
    }
