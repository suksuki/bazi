from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.L1_atomic_ops.plugin_condition_protocol import (
    build_static_basis,
    detect_interaction_layer,
    infer_manifestation_state,
    relation_origin_multiplier,
)
from v17_rebirth.backend.logic.core_engine.god_ring_resolver_core import resolve_god_ring_core
from v17_rebirth.backend.logic.L1_atomic_ops.relation_cluster_projection import god_cluster_projection
from v17_rebirth.backend.logic.plugin_discovery import deity_scores_from_tensor, rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec
from v17_rebirth.backend.logic.configs.manager import get_plugin_config
from v17_rebirth.backend.services.plugin_display import plugin_source_label


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


def _collect_god_ring_bias(decision_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    use_bias: Dict[str, float] = {}
    taboo_bias: Dict[str, float] = {}
    entries: List[Dict[str, Any]] = []
    for row in decision_rows:
        if not isinstance(row, dict):
            continue
        impact = row.get("physical_impact") if isinstance(row.get("physical_impact"), dict) else {}
        bias = impact.get("god_ring_bias") if isinstance(impact.get("god_ring_bias"), dict) else {}
        use_entry: Dict[str, float] = {}
        taboo_entry: Dict[str, float] = {}
        for god, raw in (bias.get("use_bias") or {}).items() if isinstance(bias.get("use_bias"), dict) else []:
            name = str(god or "").strip()
            if not name:
                continue
            try:
                value = float(raw or 0.0)
            except (TypeError, ValueError):
                value = 0.0
            if value > 0.0:
                use_bias[name] = use_bias.get(name, 0.0) + value
                use_entry[name] = round(use_entry.get(name, 0.0) + value, 3)
        for god, raw in (bias.get("taboo_bias") or {}).items() if isinstance(bias.get("taboo_bias"), dict) else []:
            name = str(god or "").strip()
            if not name:
                continue
            try:
                value = float(raw or 0.0)
            except (TypeError, ValueError):
                value = 0.0
            if value > 0.0:
                taboo_bias[name] = taboo_bias.get(name, 0.0) + value
                taboo_entry[name] = round(taboo_entry.get(name, 0.0) + value, 3)
        if use_entry or taboo_entry:
            source = str(row.get("plugin_id") or row.get("source") or "").strip()
            entries.append(
                {
                    "decision_id": str(row.get("id") or "").strip(),
                    "plugin_id": source,
                    "source_label": plugin_source_label(source, fallback=row.get("label") or row.get("title") or ""),
                    "decision_label": str(row.get("label") or row.get("title") or "").strip(),
                    "reason": str(bias.get("reason") or row.get("title") or row.get("label") or "").strip(),
                    "target_god": str(row.get("target_god") or impact.get("target_god") or "").strip(),
                    "use_bias": use_entry,
                    "taboo_bias": taboo_entry,
                }
            )
    entries.sort(
        key=lambda item: (
            sum(float(v or 0.0) for v in (item.get("use_bias") or {}).values())
            + sum(float(v or 0.0) for v in (item.get("taboo_bias") or {}).values())
        ),
        reverse=True,
    )
    return {"use_bias": use_bias, "taboo_bias": taboo_bias, "entries": entries}


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
        judgement_bias = _collect_god_ring_bias(decision_rows)
        rank_positive_work = dict(positive_work)
        rank_negative_work = dict(negative_work)
        for god, value in judgement_bias["use_bias"].items():
            rank_positive_work[god] = rank_positive_work.get(god, 0.0) + float(value or 0.0)
        for god, value in judgement_bias["taboo_bias"].items():
            rank_negative_work[god] = rank_negative_work.get(god, 0.0) + float(value or 0.0)
        core_use_scores = {
            str(item.get("god") or "").strip(): float(item.get("score") or 0.0)
            for item in (core_result.get("use_candidates") or [])
            if isinstance(item, dict) and str(item.get("god") or "").strip()
        }
        core_taboo_scores = {
            str(item.get("god") or "").strip(): float(item.get("score") or 0.0)
            for item in (core_result.get("taboo_candidates") or [])
            if isinstance(item, dict) and str(item.get("god") or "").strip()
        }

        use_members = set(_axis_members(use_axis))
        taboo_members = set(_axis_members(taboo_axis))
        use_gods = [
            str(item.get("god") or "").strip()
            for item in (core_result.get("use_candidates") or [])
            if isinstance(item, dict) and str(item.get("god") or "").strip()
        ][:2]
        taboo_gods = [
            str(item.get("god") or "").strip()
            for item in (core_result.get("taboo_candidates") or [])
            if isinstance(item, dict) and str(item.get("god") or "").strip()
        ]
        taboo_gods = [god for god in taboo_gods if god not in use_gods][:2] or taboo_gods[:2]

        has_judgement_bias = bool(judgement_bias["use_bias"] or judgement_bias["taboo_bias"])
        if has_judgement_bias:
            ranked_use = sorted(
                scores.items(),
                key=lambda item: (
                    core_use_scores.get(item[0], 0.0) * 1.1
                    + (rank_positive_work.get(item[0], 0.0) - rank_negative_work.get(item[0], 0.0)) * work_ratio_weight
                    + judgement_bias["use_bias"].get(item[0], 0.0) * 1.35
                    - judgement_bias["taboo_bias"].get(item[0], 0.0) * 0.85
                    + stage_bias.get(item[0], {}).get("use_boost", 0.0) * 0.92
                    + stage_bias.get(item[0], {}).get("stability_boost", 0.0) * 0.48
                    - stage_bias.get(item[0], {}).get("volatility_boost", 0.0) * 0.16
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
                    + stage_bias.get(item[0], {}).get("taboo_boost", 0.0) * 0.9
                    + stage_bias.get(item[0], {}).get("volatility_boost", 0.0) * 0.42
                    - stage_bias.get(item[0], {}).get("stability_boost", 0.0) * 0.2
                    + (dominant_taboo_bonus if item[0] == dominant_god else 0.0)
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
                    + stage_bias.get(item[0], {}).get("use_boost", 0.0) * 0.92
                    + stage_bias.get(item[0], {}).get("stability_boost", 0.0) * 0.48
                    - stage_bias.get(item[0], {}).get("volatility_boost", 0.0) * 0.16
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
                    + stage_bias.get(item[0], {}).get("taboo_boost", 0.0) * 0.9
                    + stage_bias.get(item[0], {}).get("volatility_boost", 0.0) * 0.42
                    - stage_bias.get(item[0], {}).get("stability_boost", 0.0) * 0.2
                    + (dominant_taboo_bonus if item[0] == dominant_god else 0.0)
                    + (axis_bonus if item[0] in taboo_members else 0.0)
                ),
                reverse=True,
            )
            taboo_gods = [god for god, _value in ranked_taboo if god not in use_gods][:2] or [god for god, _value in ranked_taboo[:2]]

        core_confidence = float(core_result.get("confidence") or 0.0)
        confidence = min(match_ratio_cap, max(match_ratio_base, core_confidence))
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
            "core_use_candidates": list(core_result.get("use_candidates") or []),
            "core_taboo_candidates": list(core_result.get("taboo_candidates") or []),
            "dual_role_candidates": list(core_result.get("dual_role_candidates") or []),
            "tongguan_gods": _extract_tongguan_gods(list(core_result.get("paths") or [])),
            "effect_scores": effect_scores,
            "judgement_bias": {
                "use_bias": {k: round(v, 3) for k, v in judgement_bias["use_bias"].items() if v > 0},
                "taboo_bias": {k: round(v, 3) for k, v in judgement_bias["taboo_bias"].items() if v > 0},
            },
            "judgement_bias_entries": list(judgement_bias.get("entries") or [])[:12],
            "stage_bias": stage_bias,
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


PLUGINS = [
    ZiPingMonthCommandPlugin(),
    ZiPingBalancePlugin(),
    ZiPingYongShenPlugin(),
    ZiPingGodRingResolverPlugin(),
]
