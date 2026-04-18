"""
V17.30：十神绝对能量强度引擎（L0 层 — Mass Phase）。

彻底废弃任何「归一化到 100」思路，引擎输出纯物理绝对能量（单位：Qi）。
- 天干基础常数 STEM_BASE = 10.0
- 地支基础常数 BRANCH_BASE = 12.0（按藏干占比分配）
- 月令对五行能量的放大倍数（Season Power）逐柱应用
- 天干通根地支 → Energy *= 1.5
- 地支透出天干 → Energy *= 1.2
- 所在支空亡   → Energy *= 0.4

返回值 `ten_gods_absolute` / `total_energy_index` 均为绝对累加值，
典型范围 50.0 ～ 500.0+，量级与命局旺衰成正比。
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from v17_rebirth.backend.logic.L0_physics_fields.evolution_ledger import EvolutionLedger

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

# 当令五行的 Season Power 放大倍率
SEASON_POWER_SAME: float = 2.5      # 与月令五行相同 → 得令
SEASON_POWER_GENERATED: float = 1.8  # 月令五行所生 → 次旺
SEASON_POWER_CONTROLLED: float = 0.6 # 月令五行所克 → 受制
SEASON_POWER_DEFAULT: float = 1.0    # 其余（休囚一般）


def _season_multiplier(target_element: str, month_branch: str) -> float:
    """
    根据目标天干五行与月令地支五行的关系，返回 Season Power 倍率。
    """
    consts = _get_l0_consts()
    s_same = float(consts.get("SEASON_POWER_SAME", 2.5))
    s_gen = float(consts.get("SEASON_POWER_GENERATED", 1.8))
    s_ctrl = float(consts.get("SEASON_POWER_CONTROLLED", 0.6))
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
    # 月令所克：月令的+2位 = 被月令克
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
        return _get_l0_val("VOID_EFFICIENCY", 0.3)
    return 1.0


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
    rooted_stems: set[str],
    acc: Dict[str, float],
    pillar_label: str = "",
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
    rooted = stem in rooted_stems
    if rooted:
        energy *= _get_l0_val("ROOTED_GAIN", 1.5)
    god = ten_god_from_stems(daymaster, stem)
    # V17.99: 数值护栏 — 安全累加
    if math.isfinite(energy):
        acc[god] = acc.get(god, 0.0) + energy
    else:
        _log.warning(f"[V17-PHYSICS-NAN] Attempted to add NaN energy for {god} at {pillar_label}干")
    if ledger is not None:
        parts = [f"{stem}→{god}"]
        if rooted:
            parts.append("通根×1.5")
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
    season_multiplier_fn,
    visible_stems: List[str],
    acc: Dict[str, float],
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
    for hidden_stem, h_w in BRANCH_HIDDEN.get(branch, []):
        hidden_element = STEM_ELEMENT.get(hidden_stem, "")
        sm = season_multiplier_fn(hidden_element) if hidden_element else 1.0
        energy = _get_l0_val("BRANCH_BASE", 12.0) * h_w * source_factor * sm * void_factor
        exposed = hidden_stem in visible_stems
        if exposed:
            energy *= _get_l0_val("EXPOSED_HIDDEN_GAIN", 1.2)
        god = ten_god_from_stems(daymaster, hidden_stem)
        # V17.99: 数值护栏 — 安全累加
        if math.isfinite(energy):
            acc[god] = acc.get(god, 0.0) + energy
        else:
            _log.warning(f"[V17-PHYSICS-NAN] Attempted to add NaN energy for {god} at {pillar_label}支")
        if ledger is not None:
            parts = [f"{branch}藏{hidden_stem}→{god}"]
            if exposed:
                parts.append("透干×1.2")
            if void_factor < 1.0:
                parts.append(f"空亡×{void_factor:.1f}")
            if abs(sm - 1.0) > 0.01:
                parts.append(f"季×{sm:.1f}")
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
    visible_stems = _collect_visible_stems(four_pillars, luck_pillar, flow_pillar)
    rooted_stems = _collect_rooted_stems(four_pillars, luck_pillar, flow_pillar)
    xun_kong_map = _get_xun_kong_map(birth_time=birth_time, four_pillars=four_pillars)
    void_pillars: List[str] = []
    ledger = EvolutionLedger()

    # ── Step 2：提取月支 → 构造 Season Power 偏函数 ──
    _, month_branch = _parse_gz(str(four_pillars.get("month", "")).strip())

    def _season_mul(target_element: str) -> float:
        return _season_multiplier(target_element, month_branch)

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

        # 天干能量
        target_stem = daymaster if pillar_key == "day" else stem
        stem_element = STEM_ELEMENT.get(target_stem, "")
        stem_sm = _season_mul(stem_element) if stem_element else 1.0
        _accumulate_stem_energy(
            stem=target_stem,
            daymaster=daymaster,
            source_factor=1.0 * s_comp,
            season_multiplier=stem_sm,
            rooted_stems=rooted_stems,
            acc=acc,
            pillar_label=p_label,
            ledger=ledger,
        )
        # 地支能量（藏干逐一累加，各自带 Season Power）
        _accumulate_branch_energy(
            branch=branch,
            daymaster=daymaster,
            source_factor=1.0 * b_comp,
            void_factor=pillar_void_factor,
            season_multiplier_fn=_season_mul,
            visible_stems=visible_stems,
            acc=acc,
            pillar_label=p_label,
            ledger=ledger,
        )

    # ── Step 4：大运 / 流年（带衰减系数，但同样受 Season Power 影响）──
    luck_f = _get_l0_val("LUCK_PILLAR_FACTOR", 0.85)
    flow_f = _get_l0_val("FLOW_PILLAR_FACTOR", 0.65)
    for gz_val, source_factor, sf_label in (
        (luck_pillar, luck_f, "运"),
        (flow_pillar, flow_f, "流"),
    ):
        if gz_val and gz_val not in ("—", "-"):
            stem, branch = _parse_gz(gz_val)
            stem_element = STEM_ELEMENT.get(stem, "")
            stem_sm = _season_mul(stem_element) if stem_element else 1.0
            _accumulate_stem_energy(
                stem=stem,
                daymaster=daymaster,
                source_factor=source_factor,
                season_multiplier=stem_sm,
                rooted_stems=rooted_stems,
                acc=acc,
                pillar_label=sf_label,
                ledger=ledger,
            )
            _accumulate_branch_energy(
                branch=branch,
                daymaster=daymaster,
                source_factor=source_factor,
                void_factor=1.0,
                season_multiplier_fn=_season_mul,
                visible_stems=visible_stems,
                acc=acc,
                pillar_label=sf_label,
                ledger=ledger,
            )

    # ── Step 5：月令主气额外标记（不再做 *= 放大，Season Power 已在 Step 3/4 逐柱应用）──
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
        ledger.append_entry("正官", acc.get("正官", 0.0), "L0_GENDER", "男命正官性别微调+1.2")
        ledger.append_entry("七杀", acc.get("七杀", 0.0), "L0_GENDER", "男命七杀性别微调+0.8")
    else:
        acc["食神"] = acc.get("食神", 0.0) + 1.2
        acc["伤官"] = acc.get("伤官", 0.0) + 0.8
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
            "same": SEASON_POWER_SAME,
            "generated": SEASON_POWER_GENERATED,
            "controlled": SEASON_POWER_CONTROLLED,
        },
        "constants": {
            "stem_base": STEM_BASE,
            "branch_base": BRANCH_BASE,
            "rooted_stem_gain": ROOTED_STEM_GAIN,
            "exposed_hidden_gain": EXPOSED_HIDDEN_GAIN,
            "void_reduction_factor": VOID_REDUCTION_FACTOR,
        },
        "ledger": ledger,
    }
