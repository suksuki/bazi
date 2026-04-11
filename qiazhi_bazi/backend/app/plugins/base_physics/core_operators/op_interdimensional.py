"""干支维轴算子：同柱盖头截脚、跨柱传导 Conductivity、通根透干谐振（与 L1 对接）。

Conductivity 与 `INTERDIMENSIONAL_*` 门控仅依赖柱位几何（通根、冲刑激活、柱距、屏障等），
不按十神分支；凡经 `resolve_stem_branch_pair` 与 `StemBranchCouplingEngine` 参与传导的冲突边
（冲 / 害 / 合等）均走同一套标度。十神层面的「核心冲突」由 `junction` 与 `core_conflict_*` 算子簇处理。
"""
from __future__ import annotations

from typing import Any, Callable, Dict, List, Mapping, MutableMapping, Optional, Tuple

from app.skills.physics_rules import BRANCH_HIDDEN_STEMS, STEM_TO_ELEMENT

# 地支本气天干（用于透干判定）
BRANCH_MAIN_STEM: Dict[str, str] = {
    "子": "癸",
    "丑": "己",
    "寅": "甲",
    "卯": "乙",
    "辰": "戊",
    "巳": "丙",
    "午": "丁",
    "未": "己",
    "申": "庚",
    "酉": "辛",
    "戌": "戊",
    "亥": "壬",
}

PILLAR_KEYS = frozenset({"year", "month", "day", "hour"})
PILLAR_ORDER = ("year", "month", "day", "hour")

# 审计与 skill_manifest `operator_to_skill` 对齐
L1_OP_VERTICAL_CRUSH = "L1_OP_VERTICAL_CRUSH"

# 五行相克：ea 是否克 eb
_RESTRAINS: Dict[str, str] = {
    "wood": "earth",
    "earth": "water",
    "water": "fire",
    "fire": "metal",
    "metal": "wood",
}


def _pos_to_pillar(pos: str) -> str:
    s = str(pos)
    if s.endswith("_branch"):
        return s.replace("_branch", "")
    if s.endswith("_stem"):
        return s.replace("_stem", "")
    return s


def parse_position_slot(pos: str) -> Optional[Tuple[str, str]]:
    s = str(pos).strip()
    if s.endswith("_branch"):
        p = s.replace("_branch", "")
        return (p, "branch") if p in PILLAR_KEYS else None
    if s.endswith("_stem"):
        p = s.replace("_stem", "")
        return (p, "stem") if p in PILLAR_KEYS else None
    if s in PILLAR_KEYS:
        return (s, "stem")
    return None


def _stem_map(pillars: Mapping[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for key in PILLAR_KEYS:
        col = pillars.get(key)
        if not col:
            continue
        if isinstance(col, dict):
            st = col.get("stem")
        else:
            st = getattr(col, "stem", None)
        if st:
            out[key] = str(st)
    return out


def _branch_map(pillars: Mapping[str, Any]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for key in PILLAR_KEYS:
        col = pillars.get(key)
        if not col:
            continue
        if isinstance(col, dict):
            br = col.get("branch")
        else:
            br = getattr(col, "branch", None)
        if br:
            out[key] = str(br)
    return out


def element_restrains(stem_el: str, other_el: str) -> bool:
    if not stem_el or not other_el:
        return False
    return _RESTRAINS.get(stem_el) == other_el


def stem_element(stem: str) -> str:
    return str(STEM_TO_ELEMENT.get(str(stem), "") or "")


def branch_main_element(branch_char: str) -> str:
    main = BRANCH_MAIN_STEM.get(str(branch_char), "")
    return stem_element(main) if main else ""


def branch_pillar_in_clash_or_punish(*, branch_pillar: str, conflict_points: List[Any]) -> bool:
    """支所在柱是否出现在给定冲突点列表的 clash/punish 涉及柱位中。"""
    for pt in conflict_points:
        kind = getattr(pt, "kind", None) or (pt.get("kind") if isinstance(pt, dict) else None)
        if str(kind) not in ("clash", "punish"):
            continue
        positions = getattr(pt, "positions", None) or (pt.get("positions") if isinstance(pt, dict) else None) or []
        for raw in positions:
            if _pos_to_pillar(str(raw)) == branch_pillar:
                return True
    return False


class StemBranchCouplingEngine:
    """干支维轴：垂直盖头截脚、因果传导、通根透干谐振。"""

    def __init__(
        self,
        *,
        pillars: Mapping[str, Any],
        stems_by_pillar: Mapping[str, str],
        branches_by_pillar: Mapping[str, str],
        merged_config: Mapping[str, float],
    ) -> None:
        self.pillars = pillars
        self.stems = dict(stems_by_pillar)
        self.branches = dict(branches_by_pillar)
        self.cfg = dict(merged_config)

    def _pillar_index(self, pillar: str) -> int:
        try:
            return PILLAR_ORDER.index(str(pillar))
        except ValueError:
            return 0

    def pillar_distance(self, a: str, b: str) -> int:
        return abs(self._pillar_index(a) - self._pillar_index(b))

    def stem_has_root(self, stem: str) -> bool:
        """通根：天干字出现在任一支的藏干中。"""
        s = str(stem or "")
        if not s:
            return False
        for br in self.branches.values():
            hidden = BRANCH_HIDDEN_STEMS.get(str(br), {})
            if s in hidden:
                return True
        return False

    def main_qi_penetrates_stems(self, branch_char: str) -> bool:
        """透干：该支本气天干在四柱天干中出现。"""
        main = BRANCH_MAIN_STEM.get(str(branch_char), "")
        if not main:
            return False
        return any(v == main for v in self.stems.values())

    def causal_conductivity_base(
        self,
        stem_node: Mapping[str, Any],
        branch_node: Mapping[str, Any],
        activation_conflict_points: Optional[List[Any]] = None,
    ) -> float:
        """
        逻辑 B：同柱 1.0；跨柱通根 0.8；冲刑激活（他点）0.5；否则 0；再乘跨柱衰减与屏障。
        """
        sp = str(stem_node.get("pillar") or "")
        bp = str(branch_node.get("pillar") or "")
        if sp not in PILLAR_KEYS or bp not in PILLAR_KEYS:
            return 0.0
        if sp == bp:
            return 1.0
        stem = str(stem_node.get("stem") or "")
        act_pts = list(activation_conflict_points or [])
        if self.stem_has_root(stem):
            base = 0.8
        elif act_pts and branch_pillar_in_clash_or_punish(branch_pillar=bp, conflict_points=act_pts):
            base = 0.5
        else:
            base = 0.0
        if base <= 0.0:
            return 0.0
        dist = self.pillar_distance(sp, bp)
        decay = float(self.cfg.get("CONDUCTIVITY_DECAY_RATE", 0.7))
        decay = max(1e-6, min(1.0, decay))
        # 相邻柱 dist=1 不衰减；dist>=2 按 (dist-1) 次衰减
        factor = decay ** max(0, dist - 1)
        base *= factor
        barrier = float(self.cfg.get("INTERDIMENSIONAL_BARRIER_STRENGTH", 1.0))
        barrier = max(0.0, min(2.0, barrier))
        base *= max(0.0, 1.0 - barrier * 0.35 * (1.0 - min(1.0, base)))
        return max(0.0, min(1.0, base))

    def effective_conductivity(
        self,
        stem_node: Mapping[str, Any],
        branch_node: Mapping[str, Any],
        *,
        interdimensional_alpha: float,
        activation_conflict_points: Optional[List[Any]] = None,
    ) -> Tuple[float, float]:
        """返回 (physics_c, effective_after_blend)。

        `INTERDIMENSIONAL_SHIELD_ENABLE` 为全局开关：<0.5 时跳过几何屏蔽（恒 (1,1)）；
        否则先算物理传导再与人工 alpha 混合。不对十神或 Deity 标签做特判。
        """
        if float(self.cfg.get("INTERDIMENSIONAL_SHIELD_ENABLE", 1.0)) < 0.5:
            return 1.0, 1.0
        c_phys = self.causal_conductivity_base(
            stem_node, branch_node, activation_conflict_points=activation_conflict_points
        )
        eff = blend_conductivity(c_phys, interdimensional_alpha)
        return c_phys, eff

    def root_penetration_resonance_active(
        self,
        stem_node: Mapping[str, Any],
        branch_node: Mapping[str, Any],
    ) -> bool:
        """通根且支本气透出于天干 → 谐振通道。"""
        if float(self.cfg.get("STEM_BRANCH_ROOT_RESONANCE_ENABLE", 1.0)) < 0.5:
            return False
        st = str(stem_node.get("stem") or "")
        bp = str(branch_node.get("pillar") or "")
        br = str(branch_node.get("branch") or self.branches.get(bp, ""))
        if not st or not br:
            return False
        if not self.stem_has_root(st):
            return False
        return self.main_qi_penetrates_stems(br)

    def apply_resonance_abs_gain(self, delta: MutableMapping[str, Any]) -> None:
        mult = float(self.cfg.get("MANGPAI_ROOT_RESONANCE", 1.2))
        mult = max(0.0, min(3.0, mult))
        try:
            g = float(delta.get("abs_gain") or 0.0)
            delta["abs_gain"] = round(g * mult, 4)
        except (TypeError, ValueError):
            pass

    def vertical_crush_steps(self, pillar_raw: Callable[[str], float]) -> List[Dict[str, Any]]:
        """逻辑 A：同柱相克 → 盖头/截脚，对受克柱施加与 MANGPAI_ETA_DIMENSIONAL_CRUSH 成比例的 Abs 损耗。"""
        if float(self.cfg.get("STEM_BRANCH_VERTICAL_CRUSH_ENABLE", 1.0)) < 0.5:
            return []
        eta = float(self.cfg.get("MANGPAI_ETA_DIMENSIONAL_CRUSH", 0.6))
        eta = max(0.0, min(2.0, eta))
        out: List[Dict[str, Any]] = []
        for pname in PILLAR_ORDER:
            st = self.stems.get(pname, "")
            br = self.branches.get(pname, "")
            if not st or not br:
                continue
            se = stem_element(st)
            be = branch_main_element(br)
            if not se or not be:
                continue
            crush = element_restrains(se, be) or element_restrains(be, se)
            if not crush:
                continue
            raw_e = max(0.0, float(pillar_raw(pname)))
            loss = raw_e * eta * 0.12
            if loss <= 1e-9:
                continue
            out.append(
                {
                    "plugin": "interdimensional.vertical_crush",
                    "pillar": pname,
                    "stem": st,
                    "branch": br,
                    "l1_operator_id": L1_OP_VERTICAL_CRUSH,
                    "l1_operator_ids": [L1_OP_VERTICAL_CRUSH],
                    "delta": {
                        "effect": "vertical_crush",
                        "abs_loss": round(loss, 4),
                        "abs_gain": 0.0,
                        "vector": "dimensional_crush",
                    },
                }
            )
        return out


def blend_conductivity(physics_c: float, interdimensional_param: float) -> float:
    """人工灵敏度：param 0..2 → alpha∈[0,1] 插值到全传导。"""
    c = max(0.0, min(1.0, float(physics_c)))
    alpha = max(0.0, min(1.0, float(interdimensional_param) / 2.0))
    return max(0.0, min(1.0, c + (1.0 - c) * alpha))


def resolve_stem_branch_pair(
    pos_a: str,
    pos_b: str,
    *,
    pillars: Mapping[str, Any],
) -> Optional[Tuple[MutableMapping[str, Any], MutableMapping[str, Any]]]:
    ma = parse_position_slot(pos_a)
    mb = parse_position_slot(pos_b)
    if not ma or not mb:
        return None
    stems = _stem_map(pillars)
    branches = _branch_map(pillars)

    def stem_node(pillar: str) -> Dict[str, Any]:
        return {"pillar": pillar, "stem": stems.get(pillar, "")}

    def branch_node(pillar: str) -> Dict[str, Any]:
        return {"pillar": pillar, "branch": branches.get(pillar, "")}

    if ma[1] == "stem" and mb[1] == "branch":
        return stem_node(ma[0]), branch_node(mb[0])
    if ma[1] == "branch" and mb[1] == "stem":
        return stem_node(mb[0]), branch_node(ma[0])
    return None


def scale_delta_abs_loss(delta: MutableMapping[str, Any], factor: float) -> None:
    f = max(0.0, float(factor))
    if "abs_loss" in delta and delta["abs_loss"] is not None:
        try:
            delta["abs_loss"] = round(float(delta["abs_loss"]) * f, 4)
        except (TypeError, ValueError):
            pass
    if "impact_torque" in delta and delta["impact_torque"] is not None:
        try:
            delta["impact_torque"] = round(float(delta["impact_torque"]) * f, 4)
        except (TypeError, ValueError):
            pass


def scale_delta_abs_locked(delta: MutableMapping[str, Any], factor: float) -> None:
    f = max(0.0, float(factor))
    if "abs_locked" in delta and delta["abs_locked"] is not None:
        try:
            delta["abs_locked"] = round(float(delta["abs_locked"]) * f, 4)
        except (TypeError, ValueError):
            pass


def shield_log_line(stem_glyph: str, branch_glyph: str) -> str:
    sg = stem_glyph or "?"
    bg = branch_glyph or "?"
    return f"[CAUSAL_SHIELDED]: {sg} 与 {bg} 维度不连通，判定为无功干扰。"


def is_interaction_conductive(
    stem_node: Mapping[str, Any],
    branch_node: Mapping[str, Any],
    *,
    stems_by_pillar: Mapping[str, str],
    branches: Mapping[str, str],
    conflict_points: List[Any],
    activation_conflict_points: Optional[List[Any]] = None,
    **_ignored: Any,
) -> float:
    """
    兼容旧接口名：等价于 StemBranchCouplingEngine.causal_conductivity_base（忽略 conflict_points / activation 列表）。
    """
    pillars_stub: Dict[str, Any] = {}
    for pk in PILLAR_KEYS:
        st = stems_by_pillar.get(pk, "")
        br = branches.get(pk, "")
        if st or br:
            pillars_stub[pk] = {"stem": st, "branch": br}
    merged: Dict[str, float] = {
        "CONDUCTIVITY_DECAY_RATE": 0.7,
        "INTERDIMENSIONAL_BARRIER_STRENGTH": 1.0,
        "INTERDIMENSIONAL_SHIELD_ENABLE": 1.0,
    }
    eng = StemBranchCouplingEngine(
        pillars=pillars_stub,
        stems_by_pillar=stems_by_pillar,
        branches_by_pillar=branches,
        merged_config=merged,
    )
    return eng.causal_conductivity_base(
        stem_node, branch_node, activation_conflict_points=activation_conflict_points
    )


def compute_solid_ghost_ratio(
    *,
    steps: List[Dict[str, Any]],
    dimensional_shield_logs: List[str],
    ghost_damping: float,
) -> Dict[str, float]:
    """虚实比：有效传导均值经虚态阻尼，并受屏蔽条数拖累。"""
    mixed = [s for s in steps if "conductivity_effective" in s]
    if mixed:
        avg_eff = sum(float(s.get("conductivity_effective") or 0.0) for s in mixed) / len(mixed)
    else:
        avg_eff = 1.0
    damp = max(0.0, min(1.0, float(ghost_damping)))
    shield_n = len(dimensional_shield_logs or [])
    penalty = min(0.45, shield_n * 0.12)
    solid = avg_eff * (1.0 - damp * 0.5) * (1.0 - penalty)
    solid = max(0.0, min(1.0, solid))
    return {
        "solid_fraction": round(solid, 4),
        "ghost_fraction": round(1.0 - solid, 4),
        "avg_effective_conductivity": round(avg_eff, 4),
    }
