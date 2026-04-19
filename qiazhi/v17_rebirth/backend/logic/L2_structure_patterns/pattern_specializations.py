from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import BRANCH_HIDDEN, _parse_gz, ten_god_from_stems
from v17_rebirth.backend.logic.plugin_discovery import deity_scores_from_tensor, rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec


def _month_main_god(physics_tensor: Dict[str, Any]) -> str:
    four = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    day_gz = str(four.get("day", "")).strip()
    month_gz = str(four.get("month", "")).strip()
    if len(day_gz) < 2 or len(month_gz) < 2:
        return ""
    daymaster = day_gz[0]
    month_branch = month_gz[1]
    hidden = BRANCH_HIDDEN.get(month_branch, [])
    if not hidden:
        return ""
    return ten_god_from_stems(daymaster, hidden[0][0])


def _pattern_candidates(physics_tensor: Dict[str, Any]) -> List[Tuple[str, str, float]]:
    scores = deity_scores_from_tensor(physics_tensor)
    candidates: List[Tuple[str, str, float]] = []
    if not scores:
        return candidates

    top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_name, top_score = top[0]
    candidates.append(("主轴格", top_name, float(top_score)))

    month_god = _month_main_god(physics_tensor)
    if month_god in {"比肩", "劫财"}:
        candidates.append(("建禄/月劫", month_god, float(scores.get(month_god, 0.0))))

    if len(top) >= 2:
        top2_score = float(top[1][1])
        ratio = float(top_score) / max(top2_score, 1.0)
        if ratio >= 2.0 and float(top_score) >= 35.0:
            candidates.append(("从势候选", top_name, round(ratio, 3)))

    officer = float(scores.get("正官", 0.0) + scores.get("七杀", 0.0))
    wealth = float(scores.get("正财", 0.0) + scores.get("偏财", 0.0))
    if officer >= 25.0 and wealth >= 25.0:
        candidates.append(("财官协同", "财官", min(officer, wealth)))

    return candidates


def _pattern_context(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    scores = deity_scores_from_tensor(physics_tensor)
    month_god = _month_main_god(physics_tensor)
    top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True) if scores else []
    top_name = top[0][0] if top else ""
    top_score = float(top[0][1]) if top else 0.0
    second_score = float(top[1][1]) if len(top) >= 2 else 0.0
    ratio = top_score / max(second_score, 1.0) if top_score else 0.0
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    iv2 = meta.get("interaction_v2") if isinstance(meta.get("interaction_v2"), dict) else {}
    blockers: List[str] = []
    if iv2.get("liu_chong"):
        blockers.append("liu_chong")
    if iv2.get("sanxing"):
        blockers.append("sanxing")
    if iv2.get("liu_hai"):
        blockers.append("liu_hai")
    return {
        "scores": scores,
        "month_god": month_god,
        "top_name": top_name,
        "top_score": top_score,
        "dominant_ratio": round(ratio, 3),
        "blockers": blockers,
    }


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass
class PatternAxisPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.axis.v1"
    causal_tier: int = 3
    registry_priority: float = 0.77

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        if not scores:
            return []
        top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[0]
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"格局轴线候选：{top[0]} 当前为最强主轴，可作为格局专题的第一观察面。",
                "priority": 0.77,
                "label": "格局轴线",
                "meta": {
                    "pattern_axis": top[0],
                    "axis_score": float(top[1]),
                    "match_ratio": round(_clamp01(float(top[1]) / max(sum(float(v) for v in scores.values()), 1.0) * 3.0), 3),
                    "claim_type": "pattern_candidate",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "confidence": 0.77,
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class JianLuYueJiePlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.jianlu_yuejie.v1"
    causal_tier: int = 3
    registry_priority: float = 0.75

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        month_god = _month_main_god(physics_tensor)
        if month_god not in {"比肩", "劫财"}:
            return []
        name = "建禄" if month_god == "比肩" else "月劫"
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"格局候选：月令主气落在 {month_god}，本局存在「{name}」方向。",
                "priority": 0.75,
                "label": "格局候选",
                "meta": {
                    "pattern_candidate": name,
                    "month_main_god": month_god,
                    "match_ratio": 0.82,
                    "claim_type": "pattern_candidate",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "confidence": 0.75,
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class CongShiPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.congshi.v1"
    causal_tier: int = 3
    registry_priority: float = 0.74

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:2]
        if len(top) < 2:
            return []
        (g1, v1), (_g2, v2) = top
        ratio = v1 / max(v2, 1.0)
        if ratio < 2.0 or v1 < 35.0:
            return []
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"格局候选：{g1} 一枝独强，存在「从势 / 从强」候选，需要专题条件进一步核验。",
                "priority": 0.74,
                "label": "从势候选",
                "meta": {
                    "pattern_candidate": "从势候选",
                    "dominant_god": g1,
                    "dominant_ratio": round(ratio, 3),
                    "match_ratio": round(_clamp01((ratio - 1.0) / 2.0), 3),
                    "claim_type": "pattern_candidate",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "confidence": 0.74,
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class FinanceOfficerPatternPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.finance_officer.v1"
    causal_tier: int = 3
    registry_priority: float = 0.73

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        officer = float(scores.get("正官", 0.0) + scores.get("七杀", 0.0))
        wealth = float(scores.get("正财", 0.0) + scores.get("偏财", 0.0))
        if officer < 25.0 or wealth < 25.0:
            return []
        match_ratio = _clamp01(min(officer, wealth) / max(officer, wealth, 1.0))
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": "格局候选：财官双线并举，可进入财官协同专题继续核验。",
                "priority": 0.73,
                "label": "财官协同",
                "meta": {
                    "pattern_candidate": "财官协同",
                    "officer_total": officer,
                    "wealth_total": wealth,
                    "match_ratio": round(match_ratio, 3),
                    "claim_type": "pattern_candidate",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "confidence": 0.73,
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class PatternResolverPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.resolver.v1"
    causal_tier: int = 3
    registry_priority: float = 0.81

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        candidates = _pattern_candidates(physics_tensor)
        if len(candidates) < 2:
            return []
        candidate_names = [name for name, _axis, _score in candidates]
        axis_names = [axis for _name, axis, _score in candidates]
        unique_names = sorted(set(candidate_names))
        if len(unique_names) == 1:
            return []
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"格局冲突审计：当前并存 {len(unique_names)} 条候选路径（{' / '.join(unique_names)}），需要以月令与主轴统一裁决。",
                "priority": 0.81,
                "label": "格局冲突裁决",
                "meta": {
                    "pattern_candidate_count": len(unique_names),
                    "pattern_candidates": unique_names,
                    "pattern_axes": sorted(set(axis_names)),
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class PatternFormationGatePlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.formation_gate.v1"
    causal_tier: int = 3
    registry_priority: float = 0.8

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        context = _pattern_context(physics_tensor)
        candidates = _pattern_candidates(physics_tensor)
        if not candidates:
            return []
        month_god = str(context["month_god"] or "")
        top_name = str(context["top_name"] or "")
        top_ratio = float(context["dominant_ratio"] or 0.0)
        best_gate = "弱成立"
        best_reason = "候选已出现，但暂未形成稳定成格条件。"
        if month_god in {"比肩", "劫财"} and any(name == "建禄/月劫" for name, _axis, _score in candidates):
            best_gate = "月令成格"
            best_reason = "月令主气直接落在比劫轴，格局具备优先成形条件。"
        elif top_ratio >= 2.0 and any(name == "从势候选" for name, _axis, _score in candidates):
            best_gate = "强轴成格"
            best_reason = f"{top_name} 一枝独强，主轴比值已达 {top_ratio:.2f}。"
        elif any(name == "财官协同" for name, _axis, _score in candidates):
            best_gate = "双线成格"
            best_reason = "财官双线并举，具备协同成格的结构基础。"
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"成格条件审计：当前属于「{best_gate}」。{best_reason}",
                "priority": 0.8,
                "label": "成格条件",
                "meta": {
                    "pattern_gate": best_gate,
                    "pattern_gate_reason": best_reason,
                    "dominant_ratio": top_ratio,
                    "month_main_god": month_god,
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class PatternBreakGuardPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.break_guard.v1"
    causal_tier: int = 3
    registry_priority: float = 0.79

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        context = _pattern_context(physics_tensor)
        candidates = _pattern_candidates(physics_tensor)
        blockers = list(context.get("blockers") or [])
        if not candidates or not blockers:
            return []
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"破格预警：当前格局候选受到 {' / '.join(blockers)} 干扰，后续专题应优先核验是否破格。",
                "priority": 0.79,
                "label": "破格预警",
                "meta": {
                    "pattern_break_risks": blockers,
                    "pattern_candidate_count": len(candidates),
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGINS = [
    PatternAxisPlugin(),
    JianLuYueJiePlugin(),
    CongShiPlugin(),
    FinanceOfficerPatternPlugin(),
    PatternResolverPlugin(),
    PatternFormationGatePlugin(),
    PatternBreakGuardPlugin(),
]
