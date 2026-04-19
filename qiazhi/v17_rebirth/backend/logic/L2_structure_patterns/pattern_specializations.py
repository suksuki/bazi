from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    build_static_basis,
    choose_dominant_origin_type,
    collect_origin_types_from_rows,
    detect_interaction_layer,
    detect_relation_origin_type,
    relation_origin_multiplier,
)
from v17_rebirth.backend.logic.L1_atomic_ops.relation_cluster_projection import god_cluster_projection
from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import BRANCH_HIDDEN, _parse_gz, ten_god_from_stems
from v17_rebirth.backend.logic.plugin_discovery import deity_scores_from_tensor, rows_dict_to_v17_facts
from v17_rebirth.backend.logic.configs.manager import get_plugin_config
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec


PATTERN_DEFAULTS = {
    "classical.pattern.dynamic_scope.v1": {
        "SCOPE_MIX_LABEL_BOOST": 1.1,
        "SCOPE_MIN_WEIGHT": 0.06,
        "SCOPE_PRIORITY": 0.72,
        "SCOPE_MATCH_BASE": 0.62,
    },
    "classical.pattern.axis.v1": {
        "CANDIDATE_FOLLOWER_RATIO": 2.0,
        "CANDIDATE_FOLLOWER_SCORE": 35.0,
        "CANDIDATE_OFFICER_WEALTH": 25.0,
        "AXIS_MATCH_BASE": 0.42,
        "AXIS_TOP_SHARE_WEIGHT": 0.5,
        "AXIS_DOMINANT_WEIGHT": 0.25,
        "AXIS_DOMINANT_DIVISOR": 1.5,
        "AXIS_ORIGIN_SCALE_MIN": 0.92,
        "FORMATION_STRENGTH_RATIO": 2.0,
        "FINANCE_STRONG_MATCH_RATIO": 0.6,
    },
    "classical.pattern.congshi.v1": {
        "CONGSHI_RATIO_THRESHOLD": 2.0,
        "CONGSHI_SCORE_THRESHOLD": 35.0,
        "CONGSHI_RATIO_DIVISOR": 2.0,
        "CONGSHI_ORIGIN_SCALE_MIN": 0.92,
        "CONGSHI_STRONG_RATIO": 2.2,
    },
    "classical.pattern.jianlu_yuejie.v1": {
        "JIANLU_MATCH_BASE": 0.82,
        "JIANLU_ORIGIN_SCALE_MIN": 0.92,
    },
    "classical.pattern.finance_officer.v1": {
        "FINANCE_MIN_GOD_SUM": 25.0,
        "FINANCE_MATCH_MIN_ORIGIN_SCALE": 0.92,
    },
}


def _scope_weights_from_rows(rows: List[Dict[str, Any]], *, member_filter: List[str] | None = None) -> Dict[str, float]:
    filtered: List[Dict[str, Any]] = []
    need_members = {str(item).strip() for item in (member_filter or []) if str(item).strip()}
    for row in rows:
        if not isinstance(row, dict):
            continue
        if need_members:
            row_members = set()
            for key in ("pair", "group", "branches", "matched_branches", "branch"):
                value = row.get(key)
                if isinstance(value, (list, tuple, set)):
                    row_members.update({str(item).strip() for item in value if str(item).strip()})
                elif str(value or "").strip():
                    row_members.add(str(value).strip())
            if not (need_members & row_members):
                continue
        origin = str(row.get("origin_type") or "").strip()
        if not origin:
            origin = detect_relation_origin_type(row.get("pillars") if isinstance(row.get("pillars"), list) else [])
        if not origin:
            continue
        filtered.append({"origin_type": origin, "row": row})
    if not filtered:
        return {"natal": 1.0}
    scope_weights: Dict[str, float] = {
        "natal": 0.0,
        "luck_background": 0.0,
        "luck_only": 0.0,
        "flow_trigger": 0.0,
        "flow_only": 0.0,
        "runtime_pair": 0.0,
        "mixed": 0.0,
        "unknown": 0.0,
    }
    for payload in filtered:
        origin = str(payload["origin_type"]).strip().lower()
        row = payload["row"]
        strength = float(
            row.get("pivot_factor")
            if row.get("pivot_factor") is not None
            else row.get("strength")
            if row.get("strength") is not None
            else row.get("stress")
            if row.get("stress") is not None
            else 1.0
        )
        scope_weights[origin] = scope_weights.get(origin, 0.0) + max(0.2, strength) * relation_origin_multiplier(origin)
    total = sum(scope_weights.values()) or 1.0
    return {k: round(v / total, 4) for k, v in scope_weights.items() if v > 0.0}


def _classify_dynamic_scope(scope_weights: Dict[str, float]) -> str:
    present = {k for k, v in scope_weights.items() if v > 0.0 and k != "mixed"}
    if not present:
        return "natal"
    if "natal" in present and len(present) > 1:
        return "mixed"
    if "natal" in present and "flow_only" in present:
        return "flow_trigger"
    if {"luck_background", "luck_only"} & present and "natal" in present:
        return "luck_background"
    if "runtime_pair" in present and "luck_only" in present and "flow_only" in present:
        return "mixed"
    if "luck_only" in present and "flow_only" in present:
        return "runtime_pair"
    if "flow_only" in present:
        return "flow_only"
    if "luck_only" in present:
        return "luck_only"
    if "runtime_pair" in present:
        return "runtime_pair"
    if "luck_background" in present:
        return "luck_background"
    return "mixed" if len(present) > 1 else next(iter(present), "natal")


def _pattern_cfg(plugin_id: str, key: str, fallback: float) -> float:
    cfg = get_plugin_config(plugin_id)
    defaults = PATTERN_DEFAULTS.get(plugin_id, {})
    return float(cfg.get(key, defaults.get(key, fallback)))


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
    cfg = get_plugin_config("classical.pattern.axis.v1")
    follower_ratio_threshold = float(cfg.get("CANDIDATE_FOLLOWER_RATIO", 2.0))
    follower_score_threshold = float(cfg.get("CANDIDATE_FOLLOWER_SCORE", 35.0))
    officer_wealth_threshold = float(cfg.get("CANDIDATE_OFFICER_WEALTH", 25.0))

    top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_name, top_score = top[0]
    candidates.append(("主轴格", top_name, float(top_score)))

    month_god = _month_main_god(physics_tensor)
    if month_god in {"比肩", "劫财"}:
        candidates.append(("建禄/月劫", month_god, float(scores.get(month_god, 0.0))))

    if len(top) >= 2:
        top2_score = float(top[1][1])
        ratio = float(top_score) / max(top2_score, 1.0)
        if ratio >= follower_ratio_threshold and float(top_score) >= follower_score_threshold:
            candidates.append(("从势候选", top_name, round(ratio, 3)))

    officer = float(scores.get("正官", 0.0) + scores.get("七杀", 0.0))
    wealth = float(scores.get("正财", 0.0) + scores.get("偏财", 0.0))
    if officer >= officer_wealth_threshold and wealth >= officer_wealth_threshold:
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
    blocker_origin_types: List[str] = []
    blocker_origin_types.extend(collect_origin_types_from_rows(iv2.get("liu_chong") or [], member_key="pair"))
    blocker_origin_types.extend(collect_origin_types_from_rows(iv2.get("sanxing") or [], member_key="branches"))
    blocker_origin_types.extend(collect_origin_types_from_rows(iv2.get("liu_hai") or [], member_key="pair"))
    return {
        "scores": scores,
        "month_god": month_god,
        "top_name": top_name,
        "top_score": top_score,
        "dominant_ratio": round(ratio, 3),
        "blockers": blockers,
        "origin_type": choose_dominant_origin_type(blocker_origin_types) if blocker_origin_types else "natal",
    }


def _dynamic_scope_context(physics_tensor: Dict[str, Any], *, candidates: List[Tuple[str, str, float]]) -> Dict[str, Any]:
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    iv2 = meta.get("interaction_v2") if isinstance(meta.get("interaction_v2"), dict) else {}
    relation_rows: List[Dict[str, Any]] = []
    relation_rows.extend([row for row in iv2.get("liu_chong", []) if isinstance(row, dict)])
    relation_rows.extend([row for row in iv2.get("liu_hai", []) if isinstance(row, dict)])
    relation_rows.extend([row for row in iv2.get("liu_po", []) if isinstance(row, dict)])
    relation_rows.extend([row for row in iv2.get("liu_he", []) if isinstance(row, dict)])
    relation_rows.extend([row for row in iv2.get("san_he", []) if isinstance(row, dict)])
    relation_rows.extend([row for row in iv2.get("ban_he", []) if isinstance(row, dict)])
    relation_rows.extend([row for row in iv2.get("sanxing", []) if isinstance(row, dict)])

    scope_weights = _scope_weights_from_rows(relation_rows)
    dominant_scope = _classify_dynamic_scope(scope_weights)
    # 只保留高于阈值的来源权重，避免无意义的长尾噪声被误读为主导
    min_weight = float(_pattern_cfg("classical.pattern.dynamic_scope.v1", "SCOPE_MIN_WEIGHT", 0.06))
    compact_scope = {
        k: v
        for k, v in sorted(scope_weights.items(), key=lambda kv: kv[1], reverse=True)
        if v >= min_weight
    }

    scope_labels = {
        "natal": "原局主导",
        "luck_background": "原局+大运共振",
        "luck_only": "大运主导",
        "flow_trigger": "原局+流年触发",
        "flow_only": "流年触发",
        "runtime_pair": "大运+流年触发",
        "mixed": "原局/运/流混合",
        "unknown": "待确认",
    }
    target = str(candidates[0][1] if candidates else "")
    return {
        "scope": dominant_scope,
        "scope_label": scope_labels.get(dominant_scope, "动态判定"),
        "scope_weights": compact_scope,
        "target_god": target,
        "candidate_count": len(candidates),
        "candidates": [
            {"candidate": name, "target_god": str(target_god), "raw_score": round(float(score), 3)}
            for name, target_god, score in candidates
        ],
    }


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _pattern_origin_meta(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    context = _pattern_context(physics_tensor)
    origin_type = str(context.get("origin_type") or "natal")
    return {
        "origin_type": origin_type,
        "origin_multiplier": relation_origin_multiplier(origin_type),
    }


def _pattern_manifestation(blockers: List[str] | None, origin_type: str, *, target_is_strong: bool) -> str:
    if not blockers and target_is_strong:
        return "manifested"
    if blockers:
        return "supported" if len(blockers) <= 1 else "contested"
    if origin_type == "natal":
        return "supported"
    return "latent"


@dataclass
class PatternAxisPlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.axis.v1"
    causal_tier: int = 3
    registry_priority: float = 0.77

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        if not scores:
            return []
        origin_meta = _pattern_origin_meta(physics_tensor)
        context = _pattern_context(physics_tensor)
        base = _pattern_cfg(self.plugin_id, "AXIS_MATCH_BASE", 0.42)
        top_share_weight = _pattern_cfg(self.plugin_id, "AXIS_TOP_SHARE_WEIGHT", 0.5)
        dominant_weight = _pattern_cfg(self.plugin_id, "AXIS_DOMINANT_WEIGHT", 0.25)
        dominant_divisor = max(0.1, _pattern_cfg(self.plugin_id, "AXIS_DOMINANT_DIVISOR", 1.5))
        origin_scale = max(0.92, _pattern_cfg(self.plugin_id, "AXIS_ORIGIN_SCALE_MIN", 0.92))
        ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
        top = ordered[0]
        top_score = float(top[1])
        second_score = float(ordered[1][1]) if len(ordered) >= 2 else 0.0
        total_score = max(sum(float(v) for _k, v in ordered), 1.0)
        top_share = top_score / total_score
        dominant_ratio = top_score / max(second_score, 1.0) if top_score else 0.0
        fp = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
        day_gz = str(fp.get("day", "")).strip()
        daymaster = day_gz[0] if len(day_gz) >= 2 else "壬"
        projection = god_cluster_projection(
            physics_tensor=physics_tensor,
            base_god=top[0],
            day_master=daymaster,
            focus_branches=[str(str(fp.get("month", ""))[1:2] or "")],
        )
        axis_match_ratio = _clamp01(
            base
            + top_share_weight * top_share
            + dominant_weight * min(1.0, max(0.0, (dominant_ratio - 1.0) / dominant_divisor))
        ) * max(origin_scale, float(origin_meta["origin_multiplier"]))
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"格局轴线候选：{top[0]} 当前为最强主轴，可作为格局专题的第一观察面。",
                "priority": 0.77,
                "label": "格局轴线",
                "meta": {
                    "pattern_axis": top[0],
                    "target_god": top[0],
                    "axis_score": top_score,
                    "projection_share": round(float((projection or {}).get(top[0], 1.0)), 4),
                    "cluster_projection": projection,
                    "top_share": round(top_share, 3),
                    "dominant_ratio": round(dominant_ratio, 3),
                    "match_ratio": round(axis_match_ratio, 3),
                    "claim_type": "pattern_candidate",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "confidence": 0.77,
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=top[0],
                        relation_family="pattern_axis",
                        relation_members=[],
                    ),
                    "interaction_layer": detect_interaction_layer(
                        {"interaction_layer": "cross_layer"},
                        relation_family="pattern_axis",
                    ),
                    "manifestation_state": _pattern_manifestation(
                        blockers=context.get("blockers"),
                        origin_type=str(origin_meta.get("origin_type") or ""),
                        target_is_strong=True,
                    ),
                    **origin_meta,
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class PatternDynamicScopePlugin(V17PluginSpec):
    plugin_id: str = "classical.pattern.dynamic_scope.v1"
    causal_tier: int = 3
    registry_priority: float = 0.72

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        candidates = _pattern_candidates(physics_tensor)
        if not candidates:
            return []
        scope_meta = _dynamic_scope_context(physics_tensor, candidates=candidates)
        match_base = _pattern_cfg(self.plugin_id, "SCOPE_MATCH_BASE", 0.62)
        scope = str(scope_meta.get("scope") or "natal")
        scope_multipliers = {"natal": 1.0, "luck_background": 0.96, "luck_only": 0.89, "flow_trigger": 0.9, "flow_only": 0.84, "runtime_pair": 0.88, "mixed": 1.0}
        scope_boost = float(_pattern_cfg(self.plugin_id, "SCOPE_MIX_LABEL_BOOST", 1.1)) if scope == "mixed" else 1.0
        scope_weight_sum = sum(float(v) for v in scope_meta.get("scope_weights", {}).values())
        match_ratio = round(min(0.92, match_base * min(1.0, scope_weight_sum) * scope_boost * scope_multipliers.get(scope, 1.0)), 3)
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": (
                    f"动态格局来源：{scope_meta.get('scope_label') or ''}；"
                    f"候选{scope_meta.get('candidate_count', 0)}条，"
                    f"以{scope_meta.get('target_god') or '主轴神'}为核心观察。"
                ).strip(),
                "priority": 0.72,
                "label": "动态格局来源",
                "meta": {
                    "pattern_scope_mode": "natal_luck_flow_mix",
                    "scope_weights": scope_meta.get("scope_weights", {}),
                    "pattern_scope": scope,
                    "pattern_scope_label": scope_meta.get("scope_label"),
                    "pattern_dynamic_candidates": scope_meta.get("candidates", []),
                    "candidate_count": scope_meta.get("candidate_count", 0),
                    "observe_only": True,
                    "claim_type": "pattern_observation",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "match_ratio": match_ratio,
                    "pattern_mix_mode": "dynamic_scope",
                    "origin_type": scope,
                    "origin_multiplier": relation_origin_multiplier(scope),
                    **build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=scope_meta.get("target_god") or "",
                        relation_family="pattern_dynamic_scope",
                        relation_members=[],
                    ),
                    "interaction_layer": detect_interaction_layer(
                        {"interaction_layer": "cross_layer"},
                        relation_family="pattern_dynamic_scope",
                    ),
                    "manifestation_state": "supported",
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
        origin_meta = _pattern_origin_meta(physics_tensor)
        context = _pattern_context(physics_tensor)
        fp = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
        day_gz = str(fp.get("day", "")).strip()
        daymaster = day_gz[0] if len(day_gz) >= 2 else "壬"
        projection = god_cluster_projection(
            physics_tensor=physics_tensor,
            base_god=month_god,
            day_master=daymaster,
            focus_branches=[str(str(fp.get("month", ""))[1:2] or "")],
        )
        name = "建禄" if month_god == "比肩" else "月劫"
        match_base = _pattern_cfg(self.plugin_id, "JIANLU_MATCH_BASE", 0.82)
        origin_scale = max(_pattern_cfg(self.plugin_id, "JIANLU_ORIGIN_SCALE_MIN", 0.92), float(origin_meta["origin_multiplier"]))
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"格局候选：月令主气落在 {month_god}，本局存在「{name}」方向。",
                "priority": 0.75,
                "label": "格局候选",
                "meta": {
                    "pattern_candidate": name,
                    "target_god": month_god,
                    "month_main_god": month_god,
                    "projection_share": round(float((projection or {}).get(month_god, 1.0)), 4),
                    "cluster_projection": projection,
                    "match_ratio": round(_clamp01(match_base * max(origin_scale, float(origin_meta["origin_multiplier"]))), 3),
                    "claim_type": "pattern_candidate",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "confidence": 0.75,
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=month_god,
                        relation_family="pattern_jianlu_yuejie",
                        relation_members=[],
                    ),
                    "interaction_layer": detect_interaction_layer(
                        {"interaction_layer": "cross_layer"},
                        relation_family="pattern_jianlu_yuejie",
                    ),
                    "manifestation_state": _pattern_manifestation(
                        blockers=context.get("blockers"),
                        origin_type=str(origin_meta.get("origin_type") or ""),
                        target_is_strong=True,
                    ),
                    **origin_meta,
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
        origin_meta = _pattern_origin_meta(physics_tensor)
        context = _pattern_context(physics_tensor)
        top = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:2]
        if len(top) < 2:
            return []
        (g1, v1), (_g2, v2) = top
        fp = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
        day_gz = str(fp.get("day", "")).strip()
        daymaster = day_gz[0] if len(day_gz) >= 2 else "壬"
        projection = god_cluster_projection(
            physics_tensor=physics_tensor,
            base_god=g1,
            day_master=daymaster,
            focus_branches=[str(str(fp.get("month", ""))[1:2] or "")],
        )
        ratio = v1 / max(v2, 1.0)
        cfg = get_plugin_config(self.plugin_id)
        ratio_threshold = float(cfg.get("CONGSHI_RATIO_THRESHOLD", PATTERN_DEFAULTS[self.plugin_id]["CONGSHI_RATIO_THRESHOLD"]))
        score_threshold = float(cfg.get("CONGSHI_SCORE_THRESHOLD", PATTERN_DEFAULTS[self.plugin_id]["CONGSHI_SCORE_THRESHOLD"]))
        ratio_divisor = max(0.1, float(cfg.get("CONGSHI_RATIO_DIVISOR", PATTERN_DEFAULTS[self.plugin_id]["CONGSHI_RATIO_DIVISOR"])))
        origin_scale = max(
            float(cfg.get("CONGSHI_ORIGIN_SCALE_MIN", PATTERN_DEFAULTS[self.plugin_id]["CONGSHI_ORIGIN_SCALE_MIN"])),
            float(origin_meta["origin_multiplier"]),
        )
        strong_ratio = float(cfg.get("CONGSHI_STRONG_RATIO", PATTERN_DEFAULTS[self.plugin_id]["CONGSHI_STRONG_RATIO"]))
        if ratio < ratio_threshold or v1 < score_threshold:
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
                    "target_god": g1,
                    "projection_share": round(float((projection or {}).get(g1, 1.0)), 4),
                    "cluster_projection": projection,
                    "dominant_ratio": round(ratio, 3),
                    "match_ratio": round(_clamp01(_clamp01((ratio - 1.0) / ratio_divisor) * origin_scale), 3),
                    "claim_type": "pattern_candidate",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "confidence": 0.74,
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=g1,
                        relation_family="pattern_congshi",
                        relation_members=[],
                    ),
                    "interaction_layer": detect_interaction_layer(
                        {"interaction_layer": "cross_layer"},
                        relation_family="pattern_congshi",
                    ),
                    "manifestation_state": _pattern_manifestation(
                        blockers=context.get("blockers"),
                        origin_type=str(origin_meta.get("origin_type") or ""),
                        target_is_strong=ratio >= strong_ratio,
                    ),
                    **origin_meta,
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
        origin_meta = _pattern_origin_meta(physics_tensor)
        context = _pattern_context(physics_tensor)
        officer = float(scores.get("正官", 0.0) + scores.get("七杀", 0.0))
        wealth = float(scores.get("正财", 0.0) + scores.get("偏财", 0.0))
        min_total = _pattern_cfg(self.plugin_id, "FINANCE_MIN_GOD_SUM", 25.0)
        if officer < min_total or wealth < min_total:
            return []
        dominant_god = "正官" if float(scores.get("正官", 0.0)) >= float(scores.get("七杀", 0.0)) else "七杀"
        match_scale = max(
            _pattern_cfg(self.plugin_id, "FINANCE_MATCH_MIN_ORIGIN_SCALE", 0.92),
            float(origin_meta["origin_multiplier"]),
        )
        fp = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
        day_gz = str(fp.get("day", "")).strip()
        daymaster = day_gz[0] if len(day_gz) >= 2 else "壬"
        projection = god_cluster_projection(
            physics_tensor=physics_tensor,
            base_god=dominant_god,
            day_master=daymaster,
            focus_branches=[str(str(fp.get("month", ""))[1:2] or "")],
        )
        match_ratio = _clamp01((min(officer, wealth) / max(officer, wealth, 1.0)) * match_scale)
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": "格局候选：财官双线并举，可进入财官协同专题继续核验。",
                "priority": 0.73,
                "label": "财官协同",
                "meta": {
                    "pattern_candidate": "财官协同",
                    "target_god": dominant_god,
                    "officer_total": officer,
                    "wealth_total": wealth,
                    "projection_share": round(float((projection or {}).get(dominant_god, 1.0)), 4),
                    "cluster_projection": projection,
                    "match_ratio": round(match_ratio, 3),
                    "claim_type": "pattern_candidate",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "confidence": 0.73,
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=dominant_god,
                        relation_family="pattern_finance_officer",
                        relation_members=[],
                    ),
                    "interaction_layer": detect_interaction_layer(
                        {"interaction_layer": "cross_layer"},
                        relation_family="pattern_finance_officer",
                    ),
                    "manifestation_state": _pattern_manifestation(
                        blockers=context.get("blockers"),
                        origin_type=str(origin_meta.get("origin_type") or ""),
                        target_is_strong=match_ratio >= _pattern_cfg("classical.pattern.axis.v1", "FINANCE_STRONG_MATCH_RATIO", 0.6),
                    ),
                    **origin_meta,
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
        origin_meta = _pattern_origin_meta(physics_tensor)
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
                    "observe_only": True,
                    "claim_type": "pattern_observation",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=str(axis_names[0] if axis_names else ""),
                        relation_family="pattern_resolver",
                        relation_members=[],
                    ),
                    "interaction_layer": detect_interaction_layer(
                        {"interaction_layer": "cross_layer"},
                        relation_family="pattern_resolver",
                    ),
                    "manifestation_state": "supported",
                    **origin_meta,
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
        origin_meta = _pattern_origin_meta(physics_tensor)
        formation_ratio = _pattern_cfg("classical.pattern.axis.v1", "FORMATION_STRENGTH_RATIO", 2.0)
        month_god = str(context["month_god"] or "")
        top_name = str(context["top_name"] or "")
        top_ratio = float(context["dominant_ratio"] or 0.0)
        best_gate = "弱成立"
        best_reason = "候选已出现，但暂未形成稳定成格条件。"
        if month_god in {"比肩", "劫财"} and any(name == "建禄/月劫" for name, _axis, _score in candidates):
            best_gate = "月令成格"
            best_reason = "月令主气直接落在比劫轴，格局具备优先成形条件。"
        elif top_ratio >= formation_ratio and any(name == "从势候选" for name, _axis, _score in candidates):
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
                    "observe_only": True,
                    "claim_type": "pattern_observation",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=str(context.get("top_name") or month_god or ""),
                        relation_family="pattern_formation_gate",
                        relation_members=[],
                    ),
                    "interaction_layer": detect_interaction_layer(
                        {"interaction_layer": "cross_layer"},
                        relation_family="pattern_formation_gate",
                    ),
                    "manifestation_state": "supported" if len(candidates) >= 2 else "contested",
                    **origin_meta,
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
        origin_meta = _pattern_origin_meta(physics_tensor)
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"破格预警：当前格局候选受到 {' / '.join(blockers)} 干扰，后续专题应优先核验是否破格。",
                "priority": 0.79,
                "label": "破格预警",
                "meta": {
                    "pattern_break_risks": blockers,
                    "pattern_candidate_count": len(candidates),
                    "observe_only": True,
                    "claim_type": "pattern_observation",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=str(context.get("top_name") or ""),
                        relation_family="pattern_break_guard",
                        relation_members=[],
                    ),
                    "interaction_layer": detect_interaction_layer(
                        {"interaction_layer": "cross_layer"},
                        relation_family="pattern_break_guard",
                    ),
                    "manifestation_state": "supported" if blockers else "contested",
                    **origin_meta,
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGINS = [
    PatternAxisPlugin(),
    PatternDynamicScopePlugin(),
    JianLuYueJiePlugin(),
    CongShiPlugin(),
    FinanceOfficerPatternPlugin(),
    PatternResolverPlugin(),
    PatternFormationGatePlugin(),
    PatternBreakGuardPlugin(),
]
