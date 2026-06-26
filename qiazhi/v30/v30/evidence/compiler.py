from __future__ import annotations

from typing import Any

from v30.contracts import ChartContext, FeatureEvidence, TenGodEnergyModel
from v30.rules import build_rule_evidence


FEATURE_COMPILER_VERSION = "v30.feature_compiler.v1"
SEASON_ELEMENT_BY_BRANCH = {
    "寅": "wood",
    "卯": "wood",
    "辰": "wood",
    "巳": "fire",
    "午": "fire",
    "未": "fire",
    "申": "metal",
    "酉": "metal",
    "戌": "metal",
    "亥": "water",
    "子": "water",
    "丑": "water",
}
TEN_GOD_FAMILY = {
    "食神": "output",
    "伤官": "output",
    "正财": "wealth",
    "偏财": "wealth",
    "正官": "authority",
    "七杀": "authority",
    "正印": "resource",
    "偏印": "resource",
    "比肩": "self",
    "劫财": "self",
}
BRANCH_CONFLICT_RELATIONS = {"clash", "harm", "break", "punishment"}
BRANCH_ALIGNMENT_RELATIONS = {"harmony", "three_harmony", "three_meeting"}


def compile_feature_evidence(
    context: ChartContext,
    rule_policy: dict[str, object] | None = None,
    ten_god_energy_model: TenGodEnergyModel | None = None,
    supplemental_evidence: list[FeatureEvidence] | None = None,
) -> list[FeatureEvidence]:
    rows: list[FeatureEvidence] = []
    rows.extend(_day_master_evidence(context))
    rows.extend(_ten_god_evidence(context))
    rows.extend(_element_evidence(context))
    rows.extend(_strength_pattern_evidence(context))
    rows.extend(_source_backed_m3_feature_evidence(context))
    rows.extend(_branch_relation_evidence(context))
    rows.extend(_domain_rule_evidence(context))
    rows.extend(_time_context_evidence(context))
    rows.extend(_useful_god_gate_evidence(context))
    rows.extend(_ten_god_energy_evidence(context, ten_god_energy_model))
    rows.extend(supplemental_evidence or [])
    rows.extend(build_rule_evidence(rows, rule_policy))
    return _dedupe(rows)


def _day_master_evidence(context: ChartContext) -> list[FeatureEvidence]:
    return [
        FeatureEvidence(
            evidence_id=f"{context.context_id}:feature:day_master",
            domain="chart",
            kind="fact",
            label=f"day_master:{context.day_master}",
            source=context.context_id,
            confidence=1.0,
            supports=["chart_context_bound"],
            boundary="deterministic_chart_fact_not_interpretation",
        ),
        FeatureEvidence(
            evidence_id=f"{context.context_id}:feature:day_master_element",
            domain="element",
            kind="fact",
            label=f"day_master_element:{context.day_master_element}",
            source=context.context_id,
            confidence=1.0,
            supports=["element_context_bound"],
            boundary="deterministic_chart_fact_not_interpretation",
        ),
    ]


def _ten_god_evidence(context: ChartContext) -> list[FeatureEvidence]:
    rows: list[FeatureEvidence] = []
    visible = _list(context.natal_pillars.get("visible_ten_gods"))
    hidden = _list(context.natal_pillars.get("hidden_ten_gods"))
    visible_labels = sorted({str(row.get("label", "")) for row in visible if row.get("label")})
    hidden_labels = sorted({str(row.get("label", "")) for row in hidden if row.get("label")})
    if visible_labels:
        visible_families = sorted({_ten_god_family(label) for label in visible_labels if _ten_god_family(label)})
        rows.append(
            FeatureEvidence(
                evidence_id=f"{context.context_id}:feature:ten_god_visible",
                domain="ten_god",
                kind="visibility",
                label="visible_ten_gods:" + ",".join(visible_labels),
                source=context.context_id,
                confidence=min(1.0, 0.5 + len(visible_labels) * 0.08),
                supports=[
                    "ten_god_visibility",
                    *[f"ten_god_family:{family}" for family in visible_families],
                ],
                boundary="metadata_signal_not_user_verdict",
            )
        )
    if hidden_labels:
        hidden_families = sorted({_ten_god_family(label) for label in hidden_labels if _ten_god_family(label)})
        rows.append(
            FeatureEvidence(
                evidence_id=f"{context.context_id}:feature:ten_god_hidden",
                domain="ten_god",
                kind="hidden_stem",
                label="hidden_ten_gods:" + ",".join(hidden_labels),
                source=context.context_id,
                confidence=min(1.0, 0.42 + len(hidden_labels) * 0.05),
                supports=[
                    "hidden_stem_context",
                    *[f"hidden_ten_god_family:{family}" for family in hidden_families],
                ],
                boundary="hidden_stem_signal_requires_structure_review",
            )
        )
    return rows


def _element_evidence(context: ChartContext) -> list[FeatureEvidence]:
    distribution = _dict(context.natal_pillars.get("element_distribution"))
    if not distribution:
        return []
    strongest = _extreme_elements(distribution, max)
    weakest = _extreme_elements(distribution, min)
    spread = round(max(distribution.values()) - min(distribution.values()), 3)
    return [
        FeatureEvidence(
            evidence_id=f"{context.context_id}:feature:element_distribution",
            domain="element",
            kind="distribution",
            label=f"elements:strongest={','.join(strongest)};weakest={','.join(weakest)};spread={spread}",
            source=context.context_id,
            confidence=round(min(1.0, 0.45 + min(0.25, spread * 0.05)), 3),
            supports=["element_balance_review"],
            boundary="distribution_signal_not_strength_verdict",
        )
    ]


def _strength_pattern_evidence(context: ChartContext) -> list[FeatureEvidence]:
    distribution = _dict(context.natal_pillars.get("element_distribution"))
    pillars = _dict_any(context.natal_pillars.get("pillars"))
    month = pillars.get("month", {})
    month_branch = str(month.get("branch", "")) if isinstance(month, dict) else ""
    season_element = SEASON_ELEMENT_BY_BRANCH.get(month_branch, "")
    day_element = context.day_master_element
    if not distribution or not day_element:
        return []
    total = sum(distribution.values()) or 1.0
    day_share = round(distribution.get(day_element, 0.0) / total, 3)
    strongest = _extreme_elements(distribution, max)
    weakest = _extreme_elements(distribution, min)
    supports = [
        "strength_review_candidate",
        "structure_pattern_candidate",
        f"day_master_element_share:{_share_bucket(day_share)}",
        *[f"dominant_element:{element}" for element in strongest],
        *[f"thin_element:{element}" for element in weakest],
    ]
    if season_element:
        supports.append(f"season_element:{season_element}")
        if season_element == day_element:
            supports.append("seasonal_support:day_master")
        elif season_element in _pressure_elements(day_element):
            supports.append("seasonal_pressure:day_master")
        else:
            supports.append("seasonal_indirect_context:day_master")
    useful_families = _candidate_useful_families(day_element, strongest, weakest, season_element)
    supports.extend(f"useful_god_candidate_family:{family}" for family in useful_families)
    return [
        FeatureEvidence(
            evidence_id=f"{context.context_id}:feature:strength_pattern_review",
            domain="structure_pattern",
            kind="strength_pattern_review",
            label=(
                f"strength_pattern:day_element={day_element};share={day_share};"
                f"season={season_element or 'unknown'};strongest={','.join(strongest)};weakest={','.join(weakest)}"
            ),
            source=context.context_id,
            confidence=round(min(1.0, 0.48 + abs(day_share - 0.2)), 3),
            supports=supports,
            weakens=["fixed_strength_verdict", "fixed_geju_verdict", "fixed_useful_god_verdict"],
            boundary="strength_and_pattern_review_candidate_not_final_verdict",
        )
    ]


def _source_backed_m3_feature_evidence(context: ChartContext) -> list[FeatureEvidence]:
    distribution = _dict(context.natal_pillars.get("element_distribution"))
    pillars = _dict_any(context.natal_pillars.get("pillars"))
    month = pillars.get("month", {})
    month_branch = str(month.get("branch", "")) if isinstance(month, dict) else ""
    season_element = SEASON_ELEMENT_BY_BRANCH.get(month_branch, "")
    rows: list[FeatureEvidence] = []
    if season_element:
        rows.append(
            FeatureEvidence(
                evidence_id=f"{context.context_id}:feature:month_command_review",
                domain="structure_pattern",
                kind="month_command",
                label=f"month_command:branch={month_branch};season_element={season_element}",
                source=context.context_id,
                confidence=0.78,
                supports=[
                    "month_command_review",
                    "structure_pattern_candidate",
                    f"season_element:{season_element}",
                ],
                weakens=["fixed_geju_verdict", "fixed_strength_verdict"],
                boundary="month_command_supports_pattern_review_not_fixed_geju",
            )
        )
        rows.append(
            FeatureEvidence(
                evidence_id=f"{context.context_id}:feature:wang_xiang_state",
                domain="element",
                kind="seasonal_state",
                label=f"wang_xiang_xiu_qiu_si:season={season_element};day_element={context.day_master_element}",
                source=context.context_id,
                confidence=0.74,
                supports=[
                    "wang_xiang_xiu_qiu_si_review",
                    f"seasonal_state:{_seasonal_state(context.day_master_element, season_element)}",
                ],
                weakens=["fixed_strength_verdict"],
                boundary="wang_xiang_state_is_strength_input_not_verdict",
            )
        )
    if distribution:
        strongest = _extreme_elements(distribution, max)
        weakest = _extreme_elements(distribution, min)
        spread = _element_spread(distribution)
        supports = ["element_flow_transform_review"]
        if season_element in {"fire", "water"} or {"fire", "water"} & set(strongest + weakest):
            supports.extend(["climate_regulation_review", "tiaohou_candidate_path"])
        if spread >= 0.28:
            supports.extend(["bingyao_blockage_review", "bingyao_remedy_candidate_path"])
        if len({*strongest, *weakest}) >= 2:
            supports.extend(["tongguan_candidate_path", "zhihua_candidate_path"])
        rows.append(
            FeatureEvidence(
                evidence_id=f"{context.context_id}:feature:m3_source_review",
                domain="structure_dynamic",
                kind="source_backed_review",
                label=(
                    f"m3_source_review:season={season_element or 'unknown'};"
                    f"strongest={','.join(strongest)};weakest={','.join(weakest)};spread={spread}"
                ),
                source=context.context_id,
                confidence=round(min(1.0, 0.58 + spread * 0.3), 3),
                supports=supports,
                weakens=["single_factor_reading", "fixed_useful_god_verdict"],
                boundary="source_backed_m3_review_produces_candidates_not_verdicts",
            )
        )
    visible = _list(context.natal_pillars.get("visible_ten_gods"))
    hidden = _list(context.natal_pillars.get("hidden_ten_gods"))
    if visible or hidden:
        rows.append(
            FeatureEvidence(
                evidence_id=f"{context.context_id}:feature:ten_god_role_set",
                domain="ten_god",
                kind="role_set",
                label=f"ten_god_role_set:visible={len(visible)};hidden={len(hidden)}",
                source=context.context_id,
                confidence=0.72,
                supports=["ten_god_role_set_review"],
                weakens=["single_factor_reading"],
                boundary="ten_god_roles_require_visible_hidden_position_review",
            )
        )
    return rows


def _branch_relation_evidence(context: ChartContext) -> list[FeatureEvidence]:
    relations = _list(context.natal_pillars.get("relation_hits"))
    if not relations:
        return []
    relation_types = sorted({str(row.get("relation_type", "")) for row in relations if row.get("relation_type")})
    conflict_types = sorted(set(relation_types) & BRANCH_CONFLICT_RELATIONS)
    alignment_types = sorted(set(relation_types) & BRANCH_ALIGNMENT_RELATIONS)
    return [
        FeatureEvidence(
            evidence_id=f"{context.context_id}:feature:branch_relations",
            domain="branch_relation",
            kind="relation",
            label="branch_relations:" + ",".join(relation_types),
            source=context.context_id,
            confidence=min(1.0, 0.45 + len(relation_types) * 0.08),
            supports=[
                "structure_dynamic_review",
                *[f"branch_relation:{relation_type}" for relation_type in relation_types],
                *[f"branch_conflict_family:{relation_type}" for relation_type in conflict_types],
                *[f"branch_alignment_family:{relation_type}" for relation_type in alignment_types],
                "branch_relation_arbitration_review",
            ],
            weakens=["single_factor_reading"],
            boundary="branch_relations_require_layer_review",
        )
    ]


def _domain_rule_evidence(context: ChartContext) -> list[FeatureEvidence]:
    visible = _list(context.natal_pillars.get("visible_ten_gods"))
    hidden = _list(context.natal_pillars.get("hidden_ten_gods"))
    labels = {
        str(row.get("label", ""))
        for row in [*visible, *hidden]
        if row.get("label")
    }
    families = {_ten_god_family(label) for label in labels if _ten_god_family(label)}
    relations = _list(context.natal_pillars.get("relation_hits"))
    relation_types = {str(row.get("relation_type", "")) for row in relations if row.get("relation_type")}
    distribution = _dict(context.natal_pillars.get("element_distribution"))
    supports = ["domain_rule_review_candidate"]
    if "wealth" in families:
        supports.append("domain_rule_family:wealth_pressure")
    if {"wealth", "self"} <= families:
        supports.append("domain_rule_family:wealth_competition")
    if {"wealth", "output"} <= families:
        supports.append("domain_rule_family:wealth_output_generation_path")
    if {"wealth", "authority"} <= families:
        supports.append("domain_rule_family:wealth_authority_bridge_path")
    if "authority" in families:
        supports.append("domain_rule_family:career_authority_path")
        supports.append("domain_rule_family:career_authority_pressure_path")
    if {"authority", "resource"} <= families:
        supports.append("domain_rule_family:career_resource_resolution")
        supports.append("domain_rule_family:career_resource_resolution_path")
        supports.append("domain_rule_family:tongguan_resource_mediator_path")
    if relation_types & (BRANCH_CONFLICT_RELATIONS | BRANCH_ALIGNMENT_RELATIONS):
        supports.append("domain_rule_family:relationship_relation_path")
        supports.append("palace_position_review")
    if relation_types & BRANCH_CONFLICT_RELATIONS:
        supports.append("domain_rule_family:relationship_conflict_path")
    if relation_types & BRANCH_ALIGNMENT_RELATIONS:
        supports.append("domain_rule_family:relationship_alignment_review_path")
    if families & {"wealth", "authority"}:
        supports.append("domain_rule_family:relationship_authority_or_wealth_marker_path")
    if _element_spread(distribution) >= 0.35 or any(value <= 0.08 for value in distribution.values()):
        supports.append("domain_rule_family:health_element_imbalance_review")
    if any(value >= 0.34 for value in distribution.values()):
        supports.append("domain_rule_family:health_element_excess_review")
    if any(value <= 0.08 for value in distribution.values()):
        supports.append("domain_rule_family:health_element_thin_review")
    if relation_types & BRANCH_CONFLICT_RELATIONS:
        supports.append("domain_rule_family:health_conflict_pressure_review")
    if families:
        supports.append("domain_rule_family:useful_god_candidate_path")
    if {"output", "wealth"} <= families:
        supports.append("domain_rule_family:tongguan_output_wealth_bridge_path")
    if {"output", "authority"} <= families:
        supports.append("domain_rule_family:zhihua_output_controls_authority_path")
    if {"wealth", "authority", "resource"} <= families:
        supports.append("domain_rule_family:zhihua_wealth_authority_resource_path")
    if len(supports) == 1:
        return []
    return [
        FeatureEvidence(
            evidence_id=f"{context.context_id}:feature:domain_rule_review",
            domain="domain_rule",
            kind="domain_path_review",
            label="domain_rule_review:" + ",".join(sorted(supports[1:])),
            source=context.context_id,
            confidence=round(min(1.0, 0.46 + 0.05 * (len(supports) - 1)), 3),
            supports=supports,
            weakens=[
                "fixed_wealth_outcome_claim",
                "fixed_career_outcome_claim",
                "fixed_relationship_outcome_claim",
                "fixed_health_outcome_claim",
            ],
            boundary="domain_rule_review_candidate_not_life_outcome_verdict",
        )
    ]


def _time_context_evidence(context: ChartContext) -> list[FeatureEvidence]:
    status = str(context.time_layers.get("status", "not_provided"))
    if status != "ready":
        return [
            FeatureEvidence(
                evidence_id=f"{context.context_id}:feature:time_missing",
                domain="time_context",
                kind="missing_requirement",
                label="time_context:not_provided",
                source=context.context_id,
                confidence=1.0,
                weakens=["timing_claim", "special_year_claim"],
                boundary="no_timing_prediction_without_explicit_time_layer",
            )
        ]
    layers = _list(context.time_layers.get("layers"))
    layer_keys = [str(row.get("layer_key", "")) for row in layers if row.get("layer_key")]
    return [
        FeatureEvidence(
            evidence_id=f"{context.context_id}:feature:time_layers",
            domain="time_context",
            kind="explicit_layer",
            label="time_layers:" + ",".join(layer_keys),
            source=context.context_id,
            confidence=1.0,
            supports=["time_activation_review"],
            boundary="time_layer_is_context_not_fixed_event",
        )
    ]


def _useful_god_gate_evidence(context: ChartContext) -> list[FeatureEvidence]:
    return [
        FeatureEvidence(
            evidence_id=f"{context.context_id}:feature:useful_god_gate",
            domain="useful_god",
            kind="evidence_gate",
            label="useful_god_requires_evidence_path_review",
            source=context.context_id,
            confidence=0.42,
            supports=["useful_god_candidate_question"],
            weakens=["fixed_useful_god_verdict"],
            boundary="candidate_paths_only_no_fixed_favorable_unfavorable_verdict",
        )
    ]


def _ten_god_energy_evidence(
    context: ChartContext,
    model: TenGodEnergyModel | None,
) -> list[FeatureEvidence]:
    if model is None or model.status != "ready":
        return []
    scores = model.scores
    if not scores:
        return []
    dominant = sorted(model.dominant_ten_gods)
    volatile = sorted(model.high_volatility_ten_gods)
    low_stability = sorted(model.low_stability_ten_gods)
    supports = [
        "ten_god_energy_model_ready",
        *[f"ten_god_energy:{label}:{_score_bucket(score.energy)}" for label, score in scores.items()],
        *[f"ten_god_stability:{label}:{_score_bucket(score.stability)}" for label, score in scores.items()],
        *[f"ten_god_volatility:{label}:{_score_bucket(score.volatility)}" for label, score in scores.items()],
        *[f"ten_god_family_energy:{score.family}:{_score_bucket(score.energy)}" for score in scores.values()],
    ]
    return [
        FeatureEvidence(
            evidence_id=f"{context.context_id}:feature:ten_god_energy_model",
            domain="ten_god_energy",
            kind="energy_vector",
            label=(
                "ten_god_energy:"
                f"dominant={','.join(dominant) or 'none'};"
                f"volatile={','.join(volatile) or 'none'};"
                f"low_stability={','.join(low_stability) or 'none'}"
            ),
            source=model.context_id,
            confidence=round(
                min(1.0, sum(score.confidence for score in scores.values()) / max(1, len(scores))),
                3,
            ),
            supports=supports,
            weakens=["single_factor_reading", "fixed_strength_verdict"],
            boundary="ten_god_energy_model_signal_not_chart_fact",
        )
    ]


def _dedupe(rows: list[FeatureEvidence]) -> list[FeatureEvidence]:
    out: dict[str, FeatureEvidence] = {}
    for row in rows:
        current = out.get(row.evidence_id)
        if current is None or row.confidence > current.confidence:
            out[row.evidence_id] = row
    return list(out.values())


def _list(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    return []


def _dict(value: Any) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, float] = {}
    for key, item in value.items():
        try:
            out[str(key)] = float(item)
        except (TypeError, ValueError):
            continue
    return out


def _dict_any(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _extreme_elements(distribution: dict[str, float], fn: Any) -> list[str]:
    if not distribution:
        return []
    value = fn(distribution.values())
    return [key for key, item in distribution.items() if item == value]


def _element_spread(distribution: dict[str, float]) -> float:
    if not distribution:
        return 0.0
    return round(max(distribution.values()) - min(distribution.values()), 3)


def _ten_god_family(label: str) -> str:
    return TEN_GOD_FAMILY.get(label, "")


def _share_bucket(value: float) -> str:
    if value >= 0.34:
        return "high"
    if value <= 0.12:
        return "low"
    return "balanced"


def _score_bucket(value: float) -> str:
    if value >= 0.64:
        return "high"
    if value <= 0.38:
        return "low"
    return "medium"


def _pressure_elements(day_element: str) -> set[str]:
    if not day_element:
        return set()
    controls_day = {element for element, target in {"wood": "earth", "fire": "metal", "earth": "water", "metal": "wood", "water": "fire"}.items() if target == day_element}
    drained_by_day = {"wood": "fire", "fire": "earth", "earth": "metal", "metal": "water", "water": "wood"}.get(day_element, "")
    return {row for row in {*controls_day, drained_by_day} if row}


def _candidate_useful_families(
    day_element: str,
    strongest: list[str],
    weakest: list[str],
    season_element: str,
) -> list[str]:
    rows: set[str] = set()
    if day_element in strongest or season_element == day_element:
        rows.update({"output", "wealth", "authority"})
    if day_element in weakest or season_element in _pressure_elements(day_element):
        rows.update({"resource", "self"})
    if not rows:
        rows.add("balance_review")
    return sorted(rows)


def _seasonal_state(day_element: str, season_element: str) -> str:
    if not day_element or not season_element:
        return "unknown"
    if day_element == season_element:
        return "wang"
    if {"wood": "fire", "fire": "earth", "earth": "metal", "metal": "water", "water": "wood"}.get(day_element) == season_element:
        return "xiu"
    if {"wood": "water", "fire": "wood", "earth": "fire", "metal": "earth", "water": "metal"}.get(day_element) == season_element:
        return "xiang"
    if {"wood": "earth", "fire": "metal", "earth": "water", "metal": "wood", "water": "fire"}.get(day_element) == season_element:
        return "qiu"
    return "si"
