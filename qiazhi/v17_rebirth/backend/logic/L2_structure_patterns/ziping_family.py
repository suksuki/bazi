from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    build_static_basis,
    detect_interaction_layer,
    infer_manifestation_state,
    relation_origin_multiplier,
)
from v17_rebirth.backend.logic.L2_structure_patterns.climate_theme_core import resolve_climate_theme
from v17_rebirth.backend.logic.L2_structure_patterns.pattern_specializations import (
    _pattern_candidates as _pattern_candidates_from_specializations,
)
from v17_rebirth.backend.logic.core_engine.effect_resolver import pick_god_candidates
from v17_rebirth.backend.logic.core_engine.god_ring_resolver_core import resolve_god_ring_core
from v17_rebirth.backend.logic.L1_atomic_ops.relation_cluster_projection import god_cluster_projection
from v17_rebirth.backend.logic.L2_structure_patterns.blind_school_core import (
    build_blind_bias_protocol,
    normalize_blind_theme_meta,
)
from v17_rebirth.backend.logic.plugin_discovery import deity_scores_from_tensor, rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec
from v17_rebirth.backend.logic.configs.manager import get_plugin_config
from v17_rebirth.backend.services.authority_layer_protocol import (
    build_authority_layer_protocol,
    clamp_soft_bias_map,
    preserve_hard_top,
)
from v17_rebirth.backend.services.authority_judgement_protocol import (
    build_judgement_bias_protocol,
    build_stage_bias_protocol,
)


def _energy_meta(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    raw = physics_tensor.get("energy_meta")
    return raw if isinstance(raw, dict) else {}


def _ten_gods_decomposition(physics_tensor: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    top_level = physics_tensor.get("ten_gods_decomposition_l0")
    if isinstance(top_level, dict):
        return top_level  # type: ignore[return-value]
    meta = _energy_meta(physics_tensor)
    nested = meta.get("ten_gods_decomposition_l0")
    return nested if isinstance(nested, dict) else {}


def _collect_stage_bias(physics_tensor: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    decomposition = _ten_gods_decomposition(physics_tensor)
    out: Dict[str, Dict[str, float]] = {}
    for god, raw in decomposition.items():
        if not god or not isinstance(raw, dict):
            continue
        lu = float(raw.get("momentum_stage_lu") or 0.0)
        blade = float(raw.get("momentum_stage_blade") or 0.0)
        general = float(raw.get("momentum_stage_general") or 0.0)
        stage_total = float(raw.get("momentum_stage") or 0.0)
        if max(lu, blade, general, stage_total) <= 0.0:
            continue
        use_boost = lu * 0.14 + general * 0.08 + blade * 0.04
        taboo_boost = blade * 0.16 + max(0.0, general - lu * 0.12) * 0.04
        stability_boost = lu * 0.1 + general * 0.05 + blade * 0.02
        volatility = blade * 0.18 + max(0.0, general - lu * 0.18) * 0.05
        out[str(god).strip()] = {
            "lu": round(lu, 4),
            "blade": round(blade, 4),
            "general": round(general, 4),
            "stage": round(stage_total, 4),
            "use_boost": round(use_boost, 4),
            "taboo_boost": round(taboo_boost, 4),
            "stability_boost": round(stability_boost, 4),
            "volatility_boost": round(volatility, 4),
        }
    return out


def _blind_theme(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    return normalize_blind_theme_meta(meta.get("blind_theme"))


def _blind_bias_protocol(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    theme = _blind_theme(physics_tensor)
    return build_blind_bias_protocol(theme)


def _climate_modifier_layer(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    energy_meta = _energy_meta(physics_tensor)
    raw = energy_meta.get("climate_modifier_layer")
    return raw if isinstance(raw, dict) else {}


def _top_two(scores: Dict[str, float]) -> List[tuple[str, float]]:
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)[:2]


def _dominant_ratio(scores: Dict[str, float]) -> float:
    top2 = _top_two(scores)
    if len(top2) < 2:
        return 1.0
    return float(top2[0][1]) / max(float(top2[1][1]), 1.0)


def _extract_tongguan_gods(paths: List[Dict[str, Any]]) -> List[str]:
    candidates: Dict[str, float] = {}
    for raw in paths:
        if not isinstance(raw, dict):
            continue
        path_type = str(raw.get("path_type") or "").strip().lower()
        path_family = str(raw.get("path_family") or "").strip().lower()
        path_role = str(raw.get("path_role") or "").strip().lower()
        if not (path_type.startswith("tongguan") or path_family == "bridge" or path_role == "bridge"):
            continue
        god = str(raw.get("target_god") or "").strip()
        if not god:
            continue
        raw_effect = raw.get("net_effect")
        try:
            net_effect = abs(float(raw_effect))
        except Exception:
            net_effect = 0.0
        if net_effect <= 0.0:
            continue
        if god not in candidates or net_effect > candidates[god]:
            candidates[god] = net_effect
    if not candidates:
        return []
    ordered = sorted(candidates.items(), key=lambda item: item[1], reverse=True)
    return [god for god, _ in ordered[:4]]


def _projection_meta(physics_tensor: Dict[str, Any], base_god: str) -> Dict[str, Any]:
    four = physics_tensor.get("four_pillars") if isinstance(physics_tensor.get("four_pillars"), dict) else {}
    day_gz = str(four.get("day", "")).strip()
    month_gz = str(four.get("month", "")).strip()
    daymaster = day_gz[0] if len(day_gz) >= 2 else "壬"
    month_branch = month_gz[1] if len(month_gz) >= 2 else ""
    projection = god_cluster_projection(
        physics_tensor=physics_tensor,
        base_god=base_god,
        day_master=daymaster,
        focus_branches=[month_branch] if month_branch else [],
    )
    return {
        "target_god": base_god,
        "projection_share": round(float((projection or {}).get(base_god, 1.0)), 4),
        "cluster_projection": projection,
    }


def _axis_members(axis: str) -> List[str]:
    axis_map = {
        "财官": ["正财", "偏财", "正官", "七杀"],
        "印官": ["正印", "偏印", "正官", "七杀"],
        "印比": ["正印", "偏印", "比肩", "劫财"],
    }
    return list(axis_map.get(str(axis or "").strip(), []))


def _dominant_axis(scores: Dict[str, float]) -> tuple[str, str, str]:
    top = _top_two(scores)
    dominant = top[0][0] if top else ""
    if dominant in {"比肩", "劫财", "正印", "偏印"}:
        return dominant, "财官", "印比"
    if dominant in {"食神", "伤官", "正财", "偏财"}:
        return dominant, "印官", "食伤财"
    return dominant, "印比", "官杀"


def _decision_rows(physics_tensor: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for key in ("auto_resolutions", "manual_decisions", "pending_decisions"):
        for row in physics_tensor.get(key, []) if isinstance(physics_tensor.get(key), list) else []:
            if not isinstance(row, dict):
                continue
            rid = str(row.get("id") or "").strip()
            fingerprint = rid or f"{row.get('plugin_id')}::{row.get('target_god')}::{row.get('label')}"
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            rows.append(row)
    return rows


def _ziping_family_profile(scores: Dict[str, float], *, family: str) -> Dict[str, Any]:
    top_two = _top_two(scores)
    top_ratio = float(top_two[0][1] / max(top_two[1][1], 1.0)) if len(top_two) >= 2 else 1.0
    rows: List[Dict[str, Any]] = []
    if family == "ziping_balance":
        rows.append({"strength_ratio": top_ratio, "pillars": ["natal"]})
    if family == "ziping_month_command":
        rows.append({"pillars": ["natal", "flow"]})
    if family == "ziping_yongshen":
        rows.append({"pillars": ["natal"]})
    return {
        "rows": rows,
        "relation_family": family,
    }


def _ziping_interaction_meta(
    *,
    family: str,
    scores: Dict[str, float],
    top_god: str,
    interaction_layer: str = "branch",
) -> Dict[str, Any]:
    profile = _ziping_family_profile(scores=scores, family=family)
    top_two = _top_two(scores)
    ratio = float(top_two[0][1] / max(top_two[1][1], 1.0)) if len(top_two) >= 2 else 1.0
    return {
        "interaction_layer": detect_interaction_layer(
            {"interaction_layer": interaction_layer},
            relation_family=family,
            member_key="branches",
        ),
        "manifestation_state": infer_manifestation_state(
            rows=profile["rows"],
            relation_family=profile["relation_family"],
            member_set=[],
            origin_types=["natal"],
        ),
        "origin_type": "natal",
        "origin_multiplier": relation_origin_multiplier("natal"),
        "top_ratio": round(ratio, 3),
        "ziping_focus_god": top_god,
    }


ZIPING_DEFAULTS = {
    "classical.ziping.month_command.v1": {
        "MATCH_RATIO_TOP": 0.88,
        "MATCH_RATIO_OTHER": 0.72,
    },
    "classical.ziping.balance.v1": {
        "BALANCE_STRONG_RATIO": 1.8,
        "BALANCE_MODERATE_RATIO": 1.3,
        "MATCH_RATIO_MIN": 0.45,
        "MATCH_RATIO_GAIN": 0.22,
        "MATCH_RATIO_MAX": 0.9,
    },
    "classical.ziping.yongshen.v1": {
        "MATCH_RATIO_BASE": 0.58,
        "MATCH_RATIO_GAIN": 0.14,
        "MATCH_RATIO_MAX": 0.84,
    },
    "classical.ziping.climate_bridge.v1": {
        "MATCH_RATIO_MIN": 0.56,
        "MATCH_RATIO_MAX": 0.88,
    },
    "classical.ziping.pattern_bridge.v1": {
        "MATCH_RATIO_BASE": 0.58,
        "MATCH_RATIO_MAX": 0.86,
    },
    "classical.ziping.summary.v1": {
        "MATCH_RATIO_BASE": 0.62,
        "MATCH_RATIO_MAX": 0.9,
    },
    "classical.ziping.god_ring_resolver.v1": {
        "WORK_RATIO_WEIGHT": 1.25,
        "MONTH_COMMAND_BONUS": 0.22,
        "AXIS_BONUS": 0.18,
        "DOMINANT_TABOO_BONUS": 0.16,
        "MATCH_RATIO_BASE": 0.62,
        "MATCH_RATIO_CAP": 0.9,
    },
}


def _ziping_cfg(plugin_id: str, key: str, fallback: float) -> float:
    cfg = get_plugin_config(plugin_id)
    defaults = ZIPING_DEFAULTS.get(plugin_id, {})
    return float(cfg.get(key, defaults.get(key, fallback)))


def _climate_analysis(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    return resolve_climate_theme(physics_tensor)


def _climate_theme(physics_tensor: Dict[str, Any]) -> Dict[str, Any]:
    analysis = _climate_analysis(physics_tensor)
    theme = analysis.get("climate_theme")
    return theme if isinstance(theme, dict) else {}


def _pattern_candidates_summary(physics_tensor: Dict[str, Any]) -> List[Dict[str, Any]]:
    ranked: Dict[str, Dict[str, Any]] = {}
    for name, axis, score in _pattern_candidates_from_specializations(physics_tensor):
        pattern_name = str(name or "").strip()
        pattern_axis = str(axis or "").strip()
        numeric_score = float(score or 0.0)
        if not pattern_name:
            continue
        current = ranked.get(pattern_name)
        if current is None or numeric_score > float(current.get("score") or 0.0):
            ranked[pattern_name] = {
                "name": pattern_name,
                "axis": pattern_axis,
                "score": round(numeric_score, 4),
            }
    return sorted(ranked.values(), key=lambda row: float(row.get("score") or 0.0), reverse=True)


def _ziping_common_meta(
    *,
    physics_tensor: Dict[str, Any],
    scores: Dict[str, float],
    target_god: str,
    relation_family: str,
    relation_members: List[str],
    interaction_layer: str,
    match_ratio: float,
    extra_meta: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    interaction_meta = _ziping_interaction_meta(
        family=relation_family,
        scores=scores,
        top_god=target_god,
        interaction_layer=interaction_layer,
    )
    payload: Dict[str, Any] = {
        "match_ratio": round(match_ratio, 3),
        "observe_only": True,
        "claim_type": "pattern_observation",
        "entity_scope": "pattern",
        "exclusivity_key": "ziping_family",
        "source_event": "ziping_family",
        "target_god": target_god,
        "static_basis": build_static_basis(
            physics_tensor=physics_tensor,
            target_god=target_god,
            relation_family=relation_family,
            relation_members=relation_members,
        ),
        **{k: v for k, v in interaction_meta.items() if k not in {"top_ratio"}},
    }
    if target_god:
        payload.update(_projection_meta(physics_tensor, target_god))
    if isinstance(extra_meta, dict):
        payload.update(extra_meta)
    return payload


@dataclass
class ZiPingMonthCommandPlugin(V17PluginSpec):
    plugin_id: str = "classical.ziping.month_command.v1"
    causal_tier: int = 3
    registry_priority: float = 0.83

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        meta = _energy_meta(physics_tensor)
        god = str(meta.get("month_command_god") or "").strip()
        season = meta.get("season_power") if isinstance(meta.get("season_power"), dict) else {}
        branch = str(season.get("month_branch") or "").strip()
        if not god:
            return []
        scores = deity_scores_from_tensor(physics_tensor)
        top2 = _top_two(scores)
        top_god = top2[0][0] if top2 else ""
        match_ratio_top = _ziping_cfg(self.plugin_id, "MATCH_RATIO_TOP", 0.88)
        match_ratio_other = _ziping_cfg(self.plugin_id, "MATCH_RATIO_OTHER", 0.72)
        match_ratio = match_ratio_top if top_god == god else match_ratio_other
        interaction_meta = _ziping_interaction_meta(
            family="ziping_month_command",
            scores=scores,
            top_god=top_god,
            interaction_layer="branch",
        )
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"子平月令法：月支{branch or '未知'}主气落在 {god}，本局应先以月令定旺衰、再论其余结构。",
                "priority": 0.83,
                "label": "月令定盘",
                "meta": {
                    "month_command_god": god,
                    "month_branch": branch,
                    "match_ratio": match_ratio,
                    "observe_only": True,
                    "claim_type": "pattern_observation",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    **_projection_meta(physics_tensor, god),
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=god,
                        relation_family="ziping_month_command",
                        relation_members=[branch] if branch else [],
                    ),
                    **{k: v for k, v in interaction_meta.items() if k not in {"top_ratio"}},
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class ZiPingBalancePlugin(V17PluginSpec):
    plugin_id: str = "classical.ziping.balance.v1"
    causal_tier: int = 3
    registry_priority: float = 0.82

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        top2 = _top_two(scores)
        if len(top2) < 2:
            return []
        (g1, v1), (_g2, v2) = top2
        ratio = v1 / max(v2, 1.0)
        strong_ratio = _ziping_cfg(self.plugin_id, "BALANCE_STRONG_RATIO", 1.8)
        moderate_ratio = _ziping_cfg(self.plugin_id, "BALANCE_MODERATE_RATIO", 1.3)
        match_ratio_min = _ziping_cfg(self.plugin_id, "MATCH_RATIO_MIN", 0.45)
        match_ratio_gain = _ziping_cfg(self.plugin_id, "MATCH_RATIO_GAIN", 0.22)
        match_ratio_max = _ziping_cfg(self.plugin_id, "MATCH_RATIO_MAX", 0.9)
        if ratio >= strong_ratio:
            state = "偏枯偏势"
        elif ratio >= moderate_ratio:
            state = "偏旺有主轴"
        else:
            state = "相对均衡"
        match_ratio = min(
            match_ratio_max,
            max(
                match_ratio_min,
                0.48 + match_ratio_gain * min(1.0, max(0.0, ratio - 1.0)),
            ),
        )
        interaction_meta = _ziping_interaction_meta(
            family="ziping_balance",
            scores=scores,
            top_god=g1,
            interaction_layer="branch",
        )
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"子平旺衰平衡：当前呈「{state}」态，{g1} 为主导神。",
                "priority": 0.82,
                "label": "旺衰平衡",
                "meta": {
                    "balance_state": state,
                    "dominant_god": g1,
                    "dominant_ratio": round(ratio, 3),
                    "match_ratio": round(match_ratio, 3),
                    "observe_only": True,
                    "claim_type": "pattern_observation",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    **_projection_meta(physics_tensor, g1),
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=g1,
                        relation_family="ziping_balance",
                        relation_members=[],
                    ),
                    **{k: v for k, v in interaction_meta.items() if k not in {"top_ratio"}},
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class ZiPingYongShenPlugin(V17PluginSpec):
    plugin_id: str = "classical.ziping.yongshen.v1"
    causal_tier: int = 3
    registry_priority: float = 0.8

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        top = _top_two(scores)
        if not top:
            return []
        god = top[0][0]
        ratio = _dominant_ratio(scores)
        if god in {"比肩", "劫财", "正印", "偏印"}:
            yong = "财官"
            reason = "比印偏重，宜以财官疏导与收束。"
        elif god in {"食神", "伤官", "正财", "偏财"}:
            yong = "印官"
            reason = "食伤财势外放，宜以印官节制并收口。"
        else:
            yong = "印比"
            reason = "官杀承压偏重，宜以印比承载与护身。"
        base = _ziping_cfg(self.plugin_id, "MATCH_RATIO_BASE", 0.58)
        gain = _ziping_cfg(self.plugin_id, "MATCH_RATIO_GAIN", 0.14)
        cap = _ziping_cfg(self.plugin_id, "MATCH_RATIO_MAX", 0.84)
        interaction_meta = _ziping_interaction_meta(
            family="ziping_yongshen",
            scores=scores,
            top_god=god,
            interaction_layer="branch",
        )
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"子平用神建议：本局可优先观察「{yong}」线。{reason}",
                "priority": 0.8,
                "label": "用神先看",
                "meta": {
                    "yongshen_axis": yong,
                    "dominant_god": god,
                    "match_ratio": round(
                        min(cap, max(base, base + gain * min(1.0, max(0.0, ratio - 1.0)))),
                        3,
                    ),
                    "observe_only": True,
                    "claim_type": "pattern_observation",
                    "entity_scope": "pattern",
                    "exclusivity_key": "pattern_family",
                    "source_event": "pattern_family",
                    **_projection_meta(physics_tensor, god),
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=god,
                        relation_family="ziping_yongshen",
                        relation_members=[],
                    ),
                    **{k: v for k, v in interaction_meta.items() if k not in {"top_ratio"}},
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class ZiPingClimateBridgePlugin(V17PluginSpec):
    plugin_id: str = "classical.ziping.climate_bridge.v1"
    causal_tier: int = 3
    registry_priority: float = 0.79

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        if not scores:
            return []
        theme = _climate_theme(physics_tensor)
        if not theme:
            return []
        favored = [str(item).strip() for item in theme.get("favored_gods") or [] if str(item).strip()]
        strained = [str(item).strip() for item in theme.get("strained_gods") or [] if str(item).strip()]
        target_god = favored[0] if favored else str(_energy_meta(physics_tensor).get("month_command_god") or "").strip()
        if not target_god:
            target_god = _top_two(scores)[0][0]
        digest = str(theme.get("prompt_digest") or "").strip()
        parts: List[str] = [f"当前调候呈「{str(theme.get('state') or '未定')}」"]
        if favored:
            parts.append("更顺势 " + "/".join(favored[:3]))
        if strained:
            parts.append("更承压 " + "/".join(strained[:3]))
        if digest:
            parts.append(digest)
        match_ratio = min(
            _ziping_cfg(self.plugin_id, "MATCH_RATIO_MAX", 0.88),
            max(
                _ziping_cfg(self.plugin_id, "MATCH_RATIO_MIN", 0.56),
                float(theme.get("confidence") or 0.0),
            ),
        )
        relation_members = [str(theme.get("state") or "").strip()] + favored[:2] + strained[:2]
        relation_members = [item for item in relation_members if item]
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": "子平调候桥：" + "；".join(parts) + "。",
                "priority": 0.79,
                "label": "调候归口",
                "meta": _ziping_common_meta(
                    physics_tensor=physics_tensor,
                    scores=scores,
                    target_god=target_god,
                    relation_family="ziping_climate_bridge",
                    relation_members=relation_members,
                    interaction_layer="cross_layer",
                    match_ratio=match_ratio,
                    extra_meta={
                        "ziping_axis": "climate",
                        "climate_theme": theme,
                        "climate_state": str(theme.get("state") or "").strip(),
                        "climate_prompt_digest": digest,
                        "favored_gods": favored,
                        "strained_gods": strained,
                    },
                ),
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class ZiPingPatternBridgePlugin(V17PluginSpec):
    plugin_id: str = "classical.ziping.pattern_bridge.v1"
    causal_tier: int = 3
    registry_priority: float = 0.78

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        if not scores:
            return []
        candidates = _pattern_candidates_summary(physics_tensor)
        if not candidates:
            return []
        leading = candidates[0]
        target_god = str(leading.get("axis") or "").strip() or _top_two(scores)[0][0]
        candidate_names = [str(row.get("name") or "").strip() for row in candidates[:4] if str(row.get("name") or "").strip()]
        leading_score = float(leading.get("score") or 0.0)
        total_score = max(sum(float(row.get("score") or 0.0) for row in candidates[:4]), 1.0)
        match_ratio = min(
            _ziping_cfg(self.plugin_id, "MATCH_RATIO_MAX", 0.86),
            max(
                _ziping_cfg(self.plugin_id, "MATCH_RATIO_BASE", 0.58),
                0.52 + min(0.3, leading_score / total_score * 0.26),
            ),
        )
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": (
                    f"子平格局桥：当前格局轴优先落在「{str(leading.get('name') or '未定')}」"
                    f"（主轴 {str(leading.get('axis') or '未定')}），并存候选 {len(candidates)} 条。"
                ),
                "priority": 0.78,
                "label": "格局归口",
                "meta": _ziping_common_meta(
                    physics_tensor=physics_tensor,
                    scores=scores,
                    target_god=target_god,
                    relation_family="ziping_pattern_bridge",
                    relation_members=candidate_names,
                    interaction_layer="cross_layer",
                    match_ratio=match_ratio,
                    extra_meta={
                        "ziping_axis": "pattern",
                        "leading_pattern_candidate": str(leading.get("name") or "").strip(),
                        "leading_pattern_axis": str(leading.get("axis") or "").strip(),
                        "leading_pattern_score": round(leading_score, 4),
                        "pattern_candidate_count": len(candidates),
                        "pattern_candidates": candidate_names,
                        "pattern_candidates_scored": candidates[:6],
                    },
                ),
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class ZiPingGodRingResolverPlugin(V17PluginSpec):
    plugin_id: str = "classical.ziping.god_ring_resolver.v1"
    causal_tier: int = 3
    registry_priority: float = 0.72

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        if not scores:
            return []

        dominant_god, use_axis, taboo_axis = _dominant_axis(scores)
        month_command_god = str(_energy_meta(physics_tensor).get("month_command_god") or "").strip()
        match_ratio_base = _ziping_cfg(self.plugin_id, "MATCH_RATIO_BASE", 0.62)
        match_ratio_cap = _ziping_cfg(self.plugin_id, "MATCH_RATIO_CAP", 0.9)
        axis_bonus = _ziping_cfg(self.plugin_id, "AXIS_BONUS", 0.18)
        month_command_bonus = _ziping_cfg(self.plugin_id, "MONTH_COMMAND_BONUS", 0.22)
        dominant_taboo_bonus = _ziping_cfg(self.plugin_id, "DOMINANT_TABOO_BONUS", 0.16)
        work_ratio_weight = _ziping_cfg(self.plugin_id, "WORK_RATIO_WEIGHT", 1.25)
        decision_rows = _decision_rows(physics_tensor)
        core_result = resolve_god_ring_core(
            four_pillars=physics_tensor.get("four_pillars", {}) if isinstance(physics_tensor.get("four_pillars"), dict) else {},
            luck_pillar=str(physics_tensor.get("luck_pillar") or "").strip(),
            flow_pillar=str(physics_tensor.get("flow_pillar") or "").strip(),
            deity_scores=scores,
            decision_rows=decision_rows,
        )
        effect_scores = core_result.get("effect_scores") if isinstance(core_result.get("effect_scores"), dict) else {}
        stage_bias = _collect_stage_bias(physics_tensor)
        for god, bias in stage_bias.items():
            row = effect_scores.get(god)
            if not isinstance(row, dict):
                continue
            row["stage_use_boost"] = round(float(bias.get("use_boost") or 0.0), 4)
            row["stage_taboo_boost"] = round(float(bias.get("taboo_boost") or 0.0), 4)
            row["stage_stability_boost"] = round(float(bias.get("stability_boost") or 0.0), 4)
            row["stage_volatility_boost"] = round(float(bias.get("volatility_boost") or 0.0), 4)
            row["stability_score"] = round(float(row.get("stability_score") or 0.0) + float(bias.get("stability_boost") or 0.0), 4)
            row["benefit_score"] = round(float(row.get("benefit_score") or 0.0) + float(bias.get("use_boost") or 0.0), 4)
            row["harm_score"] = round(float(row.get("harm_score") or 0.0) + float(bias.get("taboo_boost") or 0.0), 4)
            row["net_utility"] = round(
                float(row.get("net_utility") or 0.0)
                + float(bias.get("use_boost") or 0.0) * 0.78
                - float(bias.get("taboo_boost") or 0.0) * 0.72,
                4,
            )
            row["resolved_utility"] = round(
                float(row.get("resolved_utility") or 0.0)
                + float(bias.get("use_boost") or 0.0) * 0.72
                - float(bias.get("volatility_boost") or 0.0) * 0.48,
                4,
            )
        positive_work: Dict[str, float] = {
            god: float((row if isinstance(row, dict) else {}).get("benefit_score") or 0.0)
            for god, row in effect_scores.items()
        }
        negative_work: Dict[str, float] = {
            god: float((row if isinstance(row, dict) else {}).get("harm_score") or 0.0)
            for god, row in effect_scores.items()
        }
        stage_protocol = build_stage_bias_protocol(stage_bias)
        judgement_protocol = build_judgement_bias_protocol(decision_rows)
        judgement_bias = {
            "use_bias": dict(judgement_protocol.get("use_bias") or {}),
            "taboo_bias": dict(judgement_protocol.get("taboo_bias") or {}),
            "entries": list(judgement_protocol.get("entries") or []),
        }
        climate_modifier = _climate_modifier_layer(physics_tensor)
        climate_efficiency = (
            climate_modifier.get("ten_god_efficiency")
            if isinstance(climate_modifier.get("ten_god_efficiency"), dict)
            else {}
        )
        climate_stability = (
            climate_modifier.get("ten_god_stability")
            if isinstance(climate_modifier.get("ten_god_stability"), dict)
            else {}
        )
        climate_priority = (
            climate_modifier.get("yongshen_priority_delta")
            if isinstance(climate_modifier.get("yongshen_priority_delta"), dict)
            else {}
        )
        for god, row in effect_scores.items():
            if not isinstance(row, dict):
                continue
            row["climate_efficiency_delta"] = round(float(climate_efficiency.get(god, 0.0) or 0.0), 4)
            row["climate_stability_delta"] = round(float(climate_stability.get(god, 0.0) or 0.0), 4)
            row["climate_priority_delta"] = round(float(climate_priority.get(god, 0.0) or 0.0), 4)
        climate_candidates = pick_god_candidates(effect_scores)
        blind_theme = _blind_theme(physics_tensor)
        blind_protocol = _blind_bias_protocol(physics_tensor)
        core_use_scores = {
            str(item.get("god") or "").strip(): float(item.get("score") or 0.0)
            for item in (climate_candidates.get("use_candidates") or [])
            if isinstance(item, dict) and str(item.get("god") or "").strip()
        }
        core_taboo_scores = {
            str(item.get("god") or "").strip(): float(item.get("score") or 0.0)
            for item in (climate_candidates.get("taboo_candidates") or [])
            if isinstance(item, dict) and str(item.get("god") or "").strip()
        }
        hard_use_scores: Dict[str, float] = {}
        hard_taboo_scores: Dict[str, float] = {}
        for god, row in effect_scores.items():
            if not isinstance(row, dict):
                continue
            hard_use_scores[god] = round(
                core_use_scores.get(god, 0.0)
                + max(0.0, float(row.get("resolved_utility") or 0.0))
                + max(0.0, float(row.get("stability_score") or 0.0)) * 0.42
                + max(0.0, float(row.get("climate_efficiency_delta") or 0.0)) * 0.44
                + max(0.0, float(row.get("climate_stability_delta") or 0.0)) * 0.38
                + max(0.0, float(row.get("climate_priority_delta") or 0.0)) * 0.76
                + stage_bias.get(god, {}).get("use_boost", 0.0) * 0.64
                + stage_bias.get(god, {}).get("stability_boost", 0.0) * 0.28,
                4,
            )
            hard_taboo_scores[god] = round(
                core_taboo_scores.get(god, 0.0)
                + max(0.0, float(row.get("harm_score") or 0.0))
                + max(0.0, -float(row.get("climate_efficiency_delta") or 0.0)) * 0.42
                + max(0.0, -float(row.get("climate_stability_delta") or 0.0)) * 0.46
                + max(0.0, -float(row.get("climate_priority_delta") or 0.0)) * 0.74
                + stage_bias.get(god, {}).get("taboo_boost", 0.0) * 0.72
                + stage_bias.get(god, {}).get("volatility_boost", 0.0) * 0.36,
                4,
            )
        blind_bias = {
            "use_bias": clamp_soft_bias_map(
                hard_scores=hard_use_scores,
                bias_map=blind_protocol.get("use_bias") if isinstance(blind_protocol.get("use_bias"), dict) else {},
            ),
            "taboo_bias": clamp_soft_bias_map(
                hard_scores=hard_taboo_scores,
                bias_map=blind_protocol.get("taboo_bias") if isinstance(blind_protocol.get("taboo_bias"), dict) else {},
            ),
        }
        rank_positive_work = dict(positive_work)
        rank_negative_work = dict(negative_work)
        for god, value in judgement_bias["use_bias"].items():
            rank_positive_work[god] = rank_positive_work.get(god, 0.0) + float(value or 0.0)
        for god, value in judgement_bias["taboo_bias"].items():
            rank_negative_work[god] = rank_negative_work.get(god, 0.0) + float(value or 0.0)
        for god, value in blind_bias["use_bias"].items():
            rank_positive_work[god] = rank_positive_work.get(god, 0.0) + float(value or 0.0) * 0.72
        for god, value in blind_bias["taboo_bias"].items():
            rank_negative_work[god] = rank_negative_work.get(god, 0.0) + float(value or 0.0) * 0.72

        use_members = set(_axis_members(use_axis))
        taboo_members = set(_axis_members(taboo_axis))
        use_gods = [
            str(item.get("god") or "").strip()
            for item in (climate_candidates.get("use_candidates") or [])
            if isinstance(item, dict) and str(item.get("god") or "").strip()
        ][:2]
        taboo_gods = [
            str(item.get("god") or "").strip()
            for item in (climate_candidates.get("taboo_candidates") or [])
            if isinstance(item, dict) and str(item.get("god") or "").strip()
        ]
        taboo_gods = [god for god in taboo_gods if god not in use_gods][:2] or taboo_gods[:2]

        has_judgement_bias = bool(judgement_bias["use_bias"] or judgement_bias["taboo_bias"])
        has_blind_bias = bool(blind_bias["use_bias"] or blind_bias["taboo_bias"])
        if has_judgement_bias:
            ranked_use = sorted(
                scores.items(),
                key=lambda item: (
                    core_use_scores.get(item[0], 0.0) * 1.1
                    + (rank_positive_work.get(item[0], 0.0) - rank_negative_work.get(item[0], 0.0)) * work_ratio_weight
                    + judgement_bias["use_bias"].get(item[0], 0.0) * 1.35
                    - judgement_bias["taboo_bias"].get(item[0], 0.0) * 0.85
                    + blind_bias["use_bias"].get(item[0], 0.0) * 0.72
                    - blind_bias["taboo_bias"].get(item[0], 0.0) * 0.42
                    + stage_bias.get(item[0], {}).get("use_boost", 0.0) * 0.92
                    + stage_bias.get(item[0], {}).get("stability_boost", 0.0) * 0.48
                    - stage_bias.get(item[0], {}).get("volatility_boost", 0.0) * 0.16
                    + float(effect_scores.get(item[0], {}).get("climate_efficiency_delta") or 0.0) * 0.54
                    + float(effect_scores.get(item[0], {}).get("climate_stability_delta") or 0.0) * 0.44
                    + float(effect_scores.get(item[0], {}).get("climate_priority_delta") or 0.0) * 0.72
                    + (axis_bonus if item[0] in use_members else 0.0)
                    + (month_command_bonus if month_command_god and item[0] == month_command_god else 0.0)
                ),
                reverse=True,
            )
            use_gods = [god for god, _value in ranked_use[:2]]

            ranked_taboo = sorted(
                scores.items(),
                key=lambda item: (
                    core_taboo_scores.get(item[0], 0.0) * 1.1
                    + rank_negative_work.get(item[0], 0.0) * work_ratio_weight
                    + judgement_bias["taboo_bias"].get(item[0], 0.0) * 1.35
                    - judgement_bias["use_bias"].get(item[0], 0.0) * 0.72
                    + blind_bias["taboo_bias"].get(item[0], 0.0) * 0.72
                    - blind_bias["use_bias"].get(item[0], 0.0) * 0.36
                    + stage_bias.get(item[0], {}).get("taboo_boost", 0.0) * 0.9
                    + stage_bias.get(item[0], {}).get("volatility_boost", 0.0) * 0.42
                    - stage_bias.get(item[0], {}).get("stability_boost", 0.0) * 0.2
                    + max(0.0, -float(effect_scores.get(item[0], {}).get("climate_efficiency_delta") or 0.0)) * 0.52
                    + max(0.0, -float(effect_scores.get(item[0], {}).get("climate_stability_delta") or 0.0)) * 0.44
                    + max(0.0, -float(effect_scores.get(item[0], {}).get("climate_priority_delta") or 0.0)) * 0.74
                    + (dominant_taboo_bonus if item[0] == dominant_god else 0.0)
                    + (axis_bonus if item[0] in taboo_members else 0.0)
                ),
                reverse=True,
            )
            taboo_gods = [god for god, _value in ranked_taboo if god not in use_gods][:2] or [god for god, _value in ranked_taboo[:2]]
        elif has_blind_bias:
            ranked_use = sorted(
                scores.items(),
                key=lambda item: (
                    core_use_scores.get(item[0], 0.0)
                    + (rank_positive_work.get(item[0], 0.0) - rank_negative_work.get(item[0], 0.0)) * (work_ratio_weight * 0.9)
                    + blind_bias["use_bias"].get(item[0], 0.0) * 0.92
                    - blind_bias["taboo_bias"].get(item[0], 0.0) * 0.38
                    + stage_bias.get(item[0], {}).get("use_boost", 0.0) * 0.82
                    + float(effect_scores.get(item[0], {}).get("climate_efficiency_delta") or 0.0) * 0.42
                    + float(effect_scores.get(item[0], {}).get("climate_stability_delta") or 0.0) * 0.34
                    + float(effect_scores.get(item[0], {}).get("climate_priority_delta") or 0.0) * 0.58
                    + (axis_bonus if item[0] in use_members else 0.0)
                ),
                reverse=True,
            )
            use_gods = [god for god, _value in ranked_use[:2]]
            ranked_taboo = sorted(
                scores.items(),
                key=lambda item: (
                    core_taboo_scores.get(item[0], 0.0)
                    + rank_negative_work.get(item[0], 0.0) * (work_ratio_weight * 0.9)
                    + blind_bias["taboo_bias"].get(item[0], 0.0) * 0.92
                    - blind_bias["use_bias"].get(item[0], 0.0) * 0.34
                    + stage_bias.get(item[0], {}).get("taboo_boost", 0.0) * 0.78
                    + max(0.0, -float(effect_scores.get(item[0], {}).get("climate_efficiency_delta") or 0.0)) * 0.46
                    + max(0.0, -float(effect_scores.get(item[0], {}).get("climate_stability_delta") or 0.0)) * 0.38
                    + max(0.0, -float(effect_scores.get(item[0], {}).get("climate_priority_delta") or 0.0)) * 0.62
                    + (axis_bonus if item[0] in taboo_members else 0.0)
                ),
                reverse=True,
            )
            taboo_gods = [god for god, _value in ranked_taboo if god not in use_gods][:2] or [god for god, _value in ranked_taboo[:2]]

        if not use_gods:
            ranked_use = sorted(
                scores.items(),
                key=lambda item: (
                    (rank_positive_work.get(item[0], 0.0) - rank_negative_work.get(item[0], 0.0)) * work_ratio_weight
                    + blind_bias["use_bias"].get(item[0], 0.0) * 0.8
                    - blind_bias["taboo_bias"].get(item[0], 0.0) * 0.32
                    + stage_bias.get(item[0], {}).get("use_boost", 0.0) * 0.92
                    + stage_bias.get(item[0], {}).get("stability_boost", 0.0) * 0.48
                    - stage_bias.get(item[0], {}).get("volatility_boost", 0.0) * 0.16
                    + float(effect_scores.get(item[0], {}).get("climate_efficiency_delta") or 0.0) * 0.48
                    + float(effect_scores.get(item[0], {}).get("climate_stability_delta") or 0.0) * 0.38
                    + float(effect_scores.get(item[0], {}).get("climate_priority_delta") or 0.0) * 0.64
                    + (axis_bonus if item[0] in use_members else 0.0)
                    + (month_command_bonus if month_command_god and item[0] == month_command_god else 0.0)
                    - rank_negative_work.get(item[0], 0.0) * 0.8
                ),
                reverse=True,
            )
            use_gods = [god for god, _value in ranked_use[:2]]
        if not taboo_gods:
            ranked_taboo = sorted(
                scores.items(),
                key=lambda item: (
                    (rank_negative_work.get(item[0], 0.0) * work_ratio_weight)
                    + blind_bias["taboo_bias"].get(item[0], 0.0) * 0.8
                    - blind_bias["use_bias"].get(item[0], 0.0) * 0.32
                    + stage_bias.get(item[0], {}).get("taboo_boost", 0.0) * 0.9
                    + stage_bias.get(item[0], {}).get("volatility_boost", 0.0) * 0.42
                    - stage_bias.get(item[0], {}).get("stability_boost", 0.0) * 0.2
                    + max(0.0, -float(effect_scores.get(item[0], {}).get("climate_efficiency_delta") or 0.0)) * 0.48
                    + max(0.0, -float(effect_scores.get(item[0], {}).get("climate_stability_delta") or 0.0)) * 0.42
                    + max(0.0, -float(effect_scores.get(item[0], {}).get("climate_priority_delta") or 0.0)) * 0.66
                    + (dominant_taboo_bonus if item[0] == dominant_god else 0.0)
                    + (axis_bonus if item[0] in taboo_members else 0.0)
                ),
                reverse=True,
            )
            taboo_gods = [god for god, _value in ranked_taboo if god not in use_gods][:2] or [god for god, _value in ranked_taboo[:2]]

        core_confidence = float(core_result.get("confidence") or 0.0)
        confidence = min(match_ratio_cap, max(match_ratio_base, core_confidence))
        for god, row in effect_scores.items():
            if not isinstance(row, dict):
                continue
            row["blind_use_bias"] = round(float(blind_bias["use_bias"].get(god, 0.0) or 0.0), 4)
            row["blind_taboo_bias"] = round(float(blind_bias["taboo_bias"].get(god, 0.0) or 0.0), 4)
        structure_sources = [
            str(entry.get("plugin_id") or "").strip()
            for entry in judgement_bias["entries"]
            if isinstance(entry, dict) and str(entry.get("plugin_id") or "").strip()
        ]
        if climate_modifier:
            structure_sources.append("climate_modifier_layer")
        soft_sources = ["blind_theme"] if (blind_bias["use_bias"] or blind_bias["taboo_bias"]) else []
        authority_layer_protocol = build_authority_layer_protocol(
            hard_constraint_source=[self.plugin_id, "stage_bias_protocol"],
            structure_enhancement_source=structure_sources,
            soft_bias_source=soft_sources,
        )
        if soft_sources:
            use_gods = preserve_hard_top(
                hard_scores=hard_use_scores,
                ranked_gods=use_gods,
                override_forbidden=bool(authority_layer_protocol.get("override_forbidden")),
            )
            taboo_gods = preserve_hard_top(
                hard_scores=hard_taboo_scores,
                ranked_gods=taboo_gods,
                override_forbidden=bool(authority_layer_protocol.get("override_forbidden")),
            )
        taboo_gods = [god for god in taboo_gods if god not in use_gods][:2] or taboo_gods[:2]
        authority = {
            "use_gods": use_gods,
            "taboo_gods": taboo_gods,
            "source": self.plugin_id,
            "mode": str(core_result.get("mode") or "six_pillar_spacetime_core"),
            "confidence": round(confidence, 3),
            "dominant_god": dominant_god,
            "use_axis": use_axis,
            "taboo_axis": taboo_axis,
            "month_command_god": month_command_god,
            "core_graph_meta": dict(core_result.get("graph_meta") or {}),
            "core_path_count": int(core_result.get("path_count") or 0),
            "core_flux_meta": dict(core_result.get("flux_meta") or {}),
            "core_use_candidates": list(climate_candidates.get("use_candidates") or []),
            "core_taboo_candidates": list(climate_candidates.get("taboo_candidates") or []),
            "dual_role_candidates": list(core_result.get("dual_role_candidates") or []),
            "tongguan_gods": _extract_tongguan_gods(list(core_result.get("paths") or [])),
            "effect_scores": effect_scores,
            "judgement_bias": {
                "use_bias": {k: round(v, 3) for k, v in judgement_bias["use_bias"].items() if v > 0},
                "taboo_bias": {k: round(v, 3) for k, v in judgement_bias["taboo_bias"].items() if v > 0},
            },
            "judgement_bias_entries": list(judgement_bias.get("entries") or [])[:12],
            "judgement_bias_protocol": judgement_protocol,
            "blind_theme": blind_theme,
            "blind_bias": {
                "use_bias": {k: round(v, 3) for k, v in blind_bias["use_bias"].items() if v > 0},
                "taboo_bias": {k: round(v, 3) for k, v in blind_bias["taboo_bias"].items() if v > 0},
            },
            "blind_bias_protocol": blind_protocol,
            "authority_layer_protocol": authority_layer_protocol,
            "climate_modifier_layer": climate_modifier,
            "stage_bias": stage_bias,
            "stage_bias_protocol": stage_protocol,
        }
        primary_god = use_gods[0] if use_gods else dominant_god
        interaction_meta = _ziping_interaction_meta(
            family="ziping_yongshen",
            scores=scores,
            top_god=primary_god,
            interaction_layer="cross_layer",
        )
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": f"体用裁决：当前更宜以「{' / '.join(use_gods) or '未定'}」为用，以「{' / '.join(taboo_gods) or '未定'}」为忌；判断基于原局强弱、月令落点与运流做功方向。",
                "priority": 0.84,
                "label": "体用裁决",
                "meta": {
                    "target_god": primary_god,
                    "match_ratio": round(confidence, 3),
                    "observe_only": True,
                    "claim_type": "pattern_observation",
                    "entity_scope": "pattern",
                    "exclusivity_key": "god_ring_authority",
                    "source_event": "god_ring_authority",
                    "god_ring_authority": authority,
                    "positive_work": {k: round(v, 3) for k, v in positive_work.items() if v > 0},
                    "negative_work": {k: round(v, 3) for k, v in negative_work.items() if v > 0},
                    "core_paths_preview": list(core_result.get("paths") or [])[:6],
                    **_projection_meta(physics_tensor, primary_god),
                    "static_basis": build_static_basis(
                        physics_tensor=physics_tensor,
                        target_god=primary_god,
                        relation_family="ziping_god_ring_resolver",
                        relation_members=list(use_members),
                    ),
                    **{k: v for k, v in interaction_meta.items() if k not in {"top_ratio"}},
                },
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


@dataclass
class ZiPingSummaryPlugin(V17PluginSpec):
    plugin_id: str = "classical.ziping.summary.v1"
    causal_tier: int = 3
    registry_priority: float = 0.71

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        scores = deity_scores_from_tensor(physics_tensor)
        if not scores:
            return []

        month_command_god = str(_energy_meta(physics_tensor).get("month_command_god") or "").strip()
        top2 = _top_two(scores)
        dominant_god = top2[0][0] if top2 else ""
        ratio = _dominant_ratio(scores)
        strong_ratio = _ziping_cfg("classical.ziping.balance.v1", "BALANCE_STRONG_RATIO", 1.8)
        moderate_ratio = _ziping_cfg("classical.ziping.balance.v1", "BALANCE_MODERATE_RATIO", 1.3)
        if ratio >= strong_ratio:
            balance_state = "偏枯偏势"
        elif ratio >= moderate_ratio:
            balance_state = "偏旺有主轴"
        else:
            balance_state = "相对均衡"

        _dominant, use_axis, taboo_axis = _dominant_axis(scores)
        climate_theme = _climate_theme(physics_tensor)
        climate_state = str(climate_theme.get("state") or "").strip()
        pattern_candidates = _pattern_candidates_summary(physics_tensor)
        leading_pattern = str(pattern_candidates[0].get("name") or "").strip() if pattern_candidates else ""

        authority_facts = ZiPingGodRingResolverPlugin().collect_v17_facts(physics_tensor)
        authority_meta = authority_facts[0].meta if authority_facts else {}
        authority = authority_meta.get("god_ring_authority") if isinstance(authority_meta, dict) else {}
        if not isinstance(authority, dict):
            authority = {}
        use_gods = [str(item).strip() for item in authority.get("use_gods") or [] if str(item).strip()]
        taboo_gods = [str(item).strip() for item in authority.get("taboo_gods") or [] if str(item).strip()]
        confidence = float(authority.get("confidence") or 0.0)
        match_ratio = min(
            _ziping_cfg(self.plugin_id, "MATCH_RATIO_MAX", 0.9),
            max(
                _ziping_cfg(self.plugin_id, "MATCH_RATIO_BASE", 0.62),
                confidence or (
                    0.58
                    + (0.06 if climate_theme else 0.0)
                    + (0.06 if pattern_candidates else 0.0)
                    + min(0.12, max(0.0, ratio - 1.0) * 0.12)
                ),
            ),
        )
        target_god = use_gods[0] if use_gods else (month_command_god or dominant_god)
        summary_parts = [
            f"月令先看「{month_command_god or dominant_god or '未定'}」",
            f"旺衰为「{balance_state}」",
        ]
        if climate_state:
            summary_parts.append(f"调候呈「{climate_state}」")
        if leading_pattern:
            summary_parts.append(f"格局候选偏向「{leading_pattern}」")
        summary_parts.append(
            f"当前宜用「{' / '.join(use_gods) if use_gods else use_axis}」，"
            f"宜忌「{' / '.join(taboo_gods) if taboo_gods else taboo_axis}」"
        )
        relation_members = [month_command_god, climate_state, leading_pattern]
        relation_members = [item for item in relation_members if item]
        rows = [
            {
                "plugin": self.plugin_id,
                "fact": "子平总括：" + "；".join(summary_parts) + "。",
                "priority": 0.71,
                "label": "子平总括",
                "meta": _ziping_common_meta(
                    physics_tensor=physics_tensor,
                    scores=scores,
                    target_god=target_god,
                    relation_family="ziping_summary",
                    relation_members=relation_members,
                    interaction_layer="cross_layer",
                    match_ratio=match_ratio,
                    extra_meta={
                        "ziping_axis": "summary",
                        "ziping_summary": {
                            "month_command_god": month_command_god,
                            "balance_state": balance_state,
                            "climate_state": climate_state,
                            "leading_pattern_candidate": leading_pattern,
                            "use_axis": use_axis,
                            "taboo_axis": taboo_axis,
                            "use_gods": use_gods,
                            "taboo_gods": taboo_gods,
                        },
                        "god_ring_authority": authority,
                        "climate_theme": climate_theme,
                        "pattern_candidates": [str(row.get("name") or "").strip() for row in pattern_candidates[:4]],
                    },
                ),
            }
        ]
        return rows_dict_to_v17_facts(rows, causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGINS = [
    ZiPingMonthCommandPlugin(),
    ZiPingBalancePlugin(),
    ZiPingYongShenPlugin(),
    ZiPingClimateBridgePlugin(),
    ZiPingPatternBridgePlugin(),
    ZiPingGodRingResolverPlugin(),
    ZiPingSummaryPlugin(),
]
