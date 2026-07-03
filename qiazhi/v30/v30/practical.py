from __future__ import annotations

from typing import Any

from v30.contracts import ChartContext, FeatureEvidence, PracticalReadingContext, RankedDecision, StructureState


PRACTICAL_READING_VERSION = "v30.practical_reading.v1"
ELEMENT_CONTROLS = {
    "wood": "earth",
    "fire": "metal",
    "earth": "water",
    "metal": "wood",
    "water": "fire",
}
ELEMENT_CONTROLLED_BY = {controlled: controller for controller, controlled in ELEMENT_CONTROLS.items()}
ELEMENT_GENERATES = {
    "wood": "fire",
    "fire": "earth",
    "earth": "metal",
    "metal": "water",
    "water": "wood",
}
ELEMENT_GENERATED_BY = {generated: generator for generator, generated in ELEMENT_GENERATES.items()}

DOMAIN_PROFILES = {
    "career": {
        "label": "事业",
        "active": "事业线索已进入当前主线，可以先看职责压力、协作关系和阶段性机会。",
        "review": "事业判断还需要结合用户当前岗位、压力来源或关键年份，避免只按单一格局下结论。",
        "action": "确认当前最想看的事业问题：方向选择、升迁压力、合作冲突或转型时机。",
    },
    "wealth": {
        "label": "财务",
        "active": "财务线索已进入当前主线，可以先看收入结构、资源投入和风险承受方式。",
        "review": "财务判断还需要结合实际收入模式、投资压力或关键年份，避免把财星直接等同于结果。",
        "action": "确认当前最想看的财务问题：收入增长、投资风险、现金流或合作分账。",
    },
    "relationship": {
        "label": "关系",
        "active": "关系线索已进入当前主线，可以先看沟通张力、承诺方式和外部压力。",
        "review": "关系判断还需要结合实际关系状态与近年事件，避免把合冲直接说成确定事件。",
        "action": "确认当前最想看的关系问题：亲密关系、合作关系、家庭压力或沟通模式。",
    },
    "health": {
        "label": "身心",
        "active": "身心线索已进入当前主线，可以先看压力承载、作息消耗和需要复核的风险区。",
        "review": "身心判断只做压力与作息层面的提醒，需要用户反馈和专业判断共同校准。",
        "action": "确认当前最想看的身心问题：压力来源、作息消耗、恢复节奏或需规避的触发点。",
    },
}


def build_ranked_decisions(
    context: ChartContext,
    evidence: list[FeatureEvidence],
    structure: StructureState,
    model_signal_summary: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    model_signal_summary = model_signal_summary if isinstance(model_signal_summary, dict) else {}
    strength = _strength_decision(context, evidence, model_signal_summary)
    pattern = _structure_pattern_decision(context, evidence, structure, model_signal_summary)
    useful = _useful_god_decision(context, evidence, structure, model_signal_summary)
    return {
        "strength": strength.model_dump(mode="json"),
        "structure_pattern": pattern.model_dump(mode="json"),
        "useful_god": useful.model_dump(mode="json"),
    }


def build_practical_reading_context(
    context: ChartContext,
    structure: StructureState,
    ranked_decisions: dict[str, dict[str, Any]],
    ten_god_energy_summary: dict[str, Any] | None = None,
) -> PracticalReadingContext:
    time_layers = context.time_layers
    six = time_layers.get("six_pillar_context", {}) if isinstance(time_layers, dict) else {}
    time_ready = isinstance(six, dict) and six.get("status") == "ready"
    timing = {
        "status": "ready" if time_ready else "natal_only",
        "luck_pillar": six.get("luck_pillar", "") if isinstance(six, dict) else "",
        "flow_year_pillar": six.get("flow_year_pillar", "") if isinstance(six, dict) else "",
        "flow_month_pillar": six.get("flow_month_pillar", "") if isinstance(six, dict) else "",
        "boundary": "timing_context_not_fixed_event_prediction",
    }
    energy = ten_god_energy_summary if isinstance(ten_god_energy_summary, dict) else {}
    domains = {
        "career": _domain_reading("career", context, structure, timing, ranked_decisions, energy),
        "wealth": _domain_reading("wealth", context, structure, timing, ranked_decisions, energy),
        "relationship": _domain_reading("relationship", context, structure, timing, ranked_decisions, energy),
        "health": _domain_reading("health", context, structure, timing, ranked_decisions, energy),
        "timing": _timing_reading(context, structure, timing, ranked_decisions, energy),
    }
    gaps = [
        {
            "domain": domain,
            "gap": str(payload.get("question_gap")),
            "priority_score": float(payload.get("priority_score", 0.0)),
            "action_prompt": str(payload.get("action_prompt", "")),
        }
        for domain, payload in domains.items()
        if payload.get("question_gap")
    ]
    gaps = sorted(gaps, key=lambda row: (-float(row.get("priority_score", 0.0)), str(row.get("domain"))))
    return PracticalReadingContext(
        status="ready" if time_ready else "natal_only",
        role_modes=["guest", "user", "practitioner"],
        domain_readings=domains,
        timing_summary=timing,
        question_gaps=gaps,
        boundaries=[
            "practical_reading_uses_evidence_and_time_context_not_fortune_fact",
            "feedback_can_calibrate_reading_not_mutate_chart_facts",
            *[str(row.get("boundary")) for row in ranked_decisions.values() if row.get("boundary")],
        ],
    )


def build_agent_question_flow(
    practical_reading: PracticalReadingContext,
    context: ChartContext,
) -> dict[str, Any]:
    time_status = str(context.time_layers.get("status", "not_provided"))
    stages = [
        {"stage": "chart_confirmation", "status": "ready", "question_focus": "confirm_birth_input"},
        {
            "stage": "time_context_confirmation",
            "status": "ready" if time_status == "ready" else "pending",
            "question_focus": "confirm_luck_flow_context",
        },
        {"stage": "event_year_discovery", "status": "active", "question_focus": "discover_special_event_year"},
        {
            "stage": "domain_gap_followup",
            "status": "active" if practical_reading.question_gaps else "ready",
            "question_focus": "clarify_practical_domain_gap",
        },
        {"stage": "final_reading_clarification", "status": "pending", "question_focus": "confirm_reading_priority"},
    ]
    return {
        "version": "v30.agent_question_flow.v1",
        "stages": stages,
        "next_stage": next((row["stage"] for row in stages if row["status"] in {"pending", "active"}), "final_reading_clarification"),
        "boundaries": [
            "agent_questions_calibrate_context_not_chart_facts",
            "question_flow_is_role_projected_presentation_state",
        ],
    }


def _strength_decision(
    context: ChartContext,
    evidence: list[FeatureEvidence],
    model_signal_summary: dict[str, Any],
) -> RankedDecision:
    row = next((item for item in evidence if item.domain == "structure_pattern"), None)
    supports = row.supports if row else []
    basis = _calculation_basis(context, supports, model_signal_summary)
    scores = _strength_candidate_scores(basis)
    basis = _with_score_diagnostics(basis, scores)
    primary = _top_candidate(scores)
    alternatives = _alternatives(scores, primary, fallback=["balanced"])
    model_signal = _decision_model_signal("strength", model_signal_summary)
    confidence = _candidate_confidence(scores, base=row.confidence if row else 0.35)
    if model_signal:
        confidence = min(0.86, confidence + 0.04)
    return RankedDecision(
        decision_id=f"{context.context_id}:decision:strength",
        domain="strength",
        status="ranked_candidate",
        primary_candidate=primary,
        alternatives=alternatives + ["needs_time_layer_review"],
        candidate_scores=scores,
        scoring_basis=basis,
        confidence=confidence,
        supporting_evidence=([row.evidence_id] if row else []) + _model_signal_evidence(model_signal),
        weakening_evidence=(row.weakens if row else ["fixed_strength_verdict"]) + _model_signal_weakening(model_signal),
        unresolved_requirements=[] if context.time_layers.get("status") == "ready" else ["luck_or_flow_context"],
        model_signal_summary=model_signal,
        boundary="strength_decision_ranked_candidate_not_final_verdict",
    )


def _structure_pattern_decision(
    context: ChartContext,
    evidence: list[FeatureEvidence],
    structure: StructureState,
    model_signal_summary: dict[str, Any],
) -> RankedDecision:
    rows = [row for row in evidence if row.domain in {"structure_pattern", "branch_relation", "domain_rule"}]
    supports = [support for row in rows for support in row.supports]
    basis = _calculation_basis(context, supports, model_signal_summary, structure=structure)
    scores = _structure_candidate_scores(basis, structure)
    basis = _with_score_diagnostics(basis, scores)
    primary = _top_candidate(scores)
    model_signal = _decision_model_signal("structure_pattern", model_signal_summary)
    return RankedDecision(
        decision_id=f"{context.context_id}:decision:structure_pattern",
        domain="structure_pattern",
        status="ranked_candidate",
        primary_candidate=primary,
        alternatives=_alternatives(scores, primary, fallback=[":".join(chain) for chain in structure.candidate_chains[:3]]),
        candidate_scores=scores,
        scoring_basis=basis,
        confidence=min(0.88, _candidate_confidence(scores, base=structure.confidence) + (0.03 if model_signal else 0.0)),
        supporting_evidence=[row.evidence_id for row in rows] + _model_signal_evidence(model_signal),
        weakening_evidence=["single_factor_reading", "fixed_geju_verdict"] + _model_signal_weakening(model_signal),
        unresolved_requirements=[] if structure.path_scores.get("dynamic_path_count", 0.0) else ["dynamic_path_review"],
        model_signal_summary=model_signal,
        boundary="structure_pattern_ranked_candidate_not_fixed_geju",
    )


def _useful_god_decision(
    context: ChartContext,
    evidence: list[FeatureEvidence],
    structure: StructureState,
    model_signal_summary: dict[str, Any],
) -> RankedDecision:
    useful_rows = [row for row in evidence if row.domain in {"useful_god", "structure_pattern", "domain_rule"}]
    supports = [support for row in useful_rows for support in row.supports]
    families = sorted({
        support.removeprefix("useful_god_candidate_family:")
        for row in useful_rows
        for support in row.supports
        if support.startswith("useful_god_candidate_family:")
    })
    if not families:
        families = ["resource_or_balance_review"]
    model_signal = _decision_model_signal("useful_god", model_signal_summary)
    basis = _calculation_basis(context, supports, model_signal_summary, structure=structure)
    scores = _useful_god_candidate_scores(basis, families)
    basis = _with_score_diagnostics(basis, scores)
    primary = _top_candidate(scores)
    unresolved = [] if context.time_layers.get("status") == "ready" else ["luck_or_flow_context"]
    if model_signal.get("requires_review") and "model_signal_volatility_review" not in unresolved:
        unresolved.append("model_signal_volatility_review")
    return RankedDecision(
        decision_id=f"{context.context_id}:decision:useful_god",
        domain="useful_god",
        status="ranked_candidate",
        primary_candidate=primary,
        alternatives=_alternatives(scores, primary, fallback=families[1:] + ["requires_practitioner_review"]),
        candidate_scores=scores,
        scoring_basis=basis,
        confidence=min(0.82, _candidate_confidence(scores, base=0.48) + structure.path_scores.get("dynamic_useful_god_candidate_path_count", 0.0) * 0.04 + (0.03 if model_signal else 0.0)),
        supporting_evidence=[row.evidence_id for row in useful_rows] + _model_signal_evidence(model_signal),
        weakening_evidence=["fixed_useful_god_verdict"] + _model_signal_weakening(model_signal),
        unresolved_requirements=unresolved,
        model_signal_summary=model_signal,
        boundary="useful_god_ranked_candidate_not_fixed_favorable_verdict",
    )


def _calculation_basis(
    context: ChartContext,
    supports: list[str],
    model_signal_summary: dict[str, Any],
    *,
    structure: StructureState | None = None,
) -> dict[str, Any]:
    distribution = context.natal_pillars.get("element_distribution", {})
    if not isinstance(distribution, dict):
        distribution = {}
    distribution = {str(key): float(value) for key, value in distribution.items() if isinstance(value, (int, float))}
    total = sum(distribution.values()) or 1.0
    day_element = context.day_master_element
    day_share = round(distribution.get(day_element, 0.0) / total, 3) if day_element else 0.0
    strongest_share = round(max(distribution.values()) / total, 3) if distribution else 0.0
    weakest_share = round(min(distribution.values()) / total, 3) if distribution else 0.0
    element_imbalance_ratio = round(strongest_share - weakest_share, 3)
    strongest = _extreme_elements(distribution, max)
    weakest = _extreme_elements(distribution, min)
    season_element = _support_value(supports, "season_element:")
    energy_bands = model_signal_summary.get("energy_bands", []) if isinstance(model_signal_summary, dict) else []
    if not isinstance(energy_bands, list):
        energy_bands = []
    interface_contract = model_signal_summary.get("interface_contract", {}) if isinstance(model_signal_summary, dict) else {}
    if not isinstance(interface_contract, dict):
        interface_contract = {}
    calibration_profile = model_signal_summary.get("calibration_profile", {}) if isinstance(model_signal_summary, dict) else {}
    if not isinstance(calibration_profile, dict):
        calibration_profile = {}
    ranked_adjustments = calibration_profile.get("ranked_decision_adjustments", {})
    if not isinstance(ranked_adjustments, dict):
        ranked_adjustments = {}
    base_summary = context.natal_pillars.get("base_fact_summary", {})
    base_summary = base_summary if isinstance(base_summary, dict) else {}
    root_summary = base_summary.get("root_fact_summary", {})
    root_summary = root_summary if isinstance(root_summary, dict) else {}
    dominant_ten_gods = model_signal_summary.get("dominant_ten_gods", []) if isinstance(model_signal_summary, dict) else []
    if not isinstance(dominant_ten_gods, list):
        dominant_ten_gods = []
    stability_alerts = model_signal_summary.get("stability_alerts", []) if isinstance(model_signal_summary, dict) else []
    volatility_alerts = model_signal_summary.get("volatility_alerts", []) if isinstance(model_signal_summary, dict) else []
    dynamic_path_count = float(structure.path_scores.get("dynamic_path_count", 0.0)) if structure else 0.0
    branch_conflict_path_count = float(structure.path_scores.get("dynamic_branch_conflict_edge_count", 0.0)) if structure else 0.0
    tongguan_path_count = float(structure.path_scores.get("dynamic_tongguan_path_count", 0.0)) if structure else 0.0
    zhihua_path_count = float(structure.path_scores.get("dynamic_zhihua_path_count", 0.0)) if structure else 0.0
    climate_boundary_signal = "fire" in weakest or "water" in weakest
    follow_structure_boundary_signal = (
        (day_share <= 0.18 and strongest_share >= 0.34)
        or (day_share >= 0.58 and element_imbalance_ratio >= 0.28)
    )
    disputed_structure_signal = branch_conflict_path_count >= 14.0 and (
        len(volatility_alerts) >= 4 or tongguan_path_count + zhihua_path_count >= 11.0
    )
    return {
        "version": "v30.ranked_decision_scoring_basis.v1",
        "day_master": context.day_master,
        "day_master_element": day_element,
        "day_element_share": day_share,
        "strongest_element_share": strongest_share,
        "weakest_element_share": weakest_share,
        "element_imbalance_ratio": element_imbalance_ratio,
        "season_element": season_element,
        "seasonal_support": "seasonal_support:day_master" in supports,
        "seasonal_pressure": "seasonal_pressure:day_master" in supports,
        "strongest_elements": strongest,
        "weakest_elements": weakest,
        "element_distribution": distribution,
        "ten_god_dominant": [str(row) for row in dominant_ten_gods],
        "ten_god_energy_bands": [
            {
                "label": str(row.get("label") or ""),
                "family": str(row.get("family") or ""),
                "energy_band": str(row.get("energy_band") or ""),
                "stability_band": str(row.get("stability_band") or ""),
                "volatility_band": str(row.get("volatility_band") or ""),
            }
            for row in energy_bands
            if isinstance(row, dict)
        ],
        "model_signal_interface_version": str(interface_contract.get("version") or ""),
        "model_signal_allowed_consumers": [
            str(row) for row in interface_contract.get("consumers", [])
        ] if isinstance(interface_contract.get("consumers", []), list) else [],
        "model_signal_forbidden_fields": [
            str(row) for row in interface_contract.get("forbidden_fields", [])
        ] if isinstance(interface_contract.get("forbidden_fields", []), list) else [],
        "model_signal_calibration_profile_version": str(calibration_profile.get("version") or ""),
        "model_signal_calibration_family_coverage": [
            str(row) for row in calibration_profile.get("family_coverage", [])
        ] if isinstance(calibration_profile.get("family_coverage", []), list) else [],
        "model_signal_calibration_flags": [
            str(row) for row in calibration_profile.get("calibration_flags", [])
        ] if isinstance(calibration_profile.get("calibration_flags", []), list) else [],
        "model_signal_ranked_adjustment_version": str(ranked_adjustments.get("version") or ""),
        "model_signal_ranked_adjustment_flags": [
            str(row) for row in ranked_adjustments.get("review_flags", [])
        ] if isinstance(ranked_adjustments.get("review_flags", []), list) else [],
        "model_signal_score_bias": ranked_adjustments.get("score_bias", {})
        if isinstance(ranked_adjustments.get("score_bias"), dict) else {},
        "root_fact_summary_version": str(root_summary.get("version") or ""),
        "day_master_root_count": int(root_summary.get("day_master_root_count", 0) or 0),
        "same_element_root_count": int(root_summary.get("same_element_root_count", 0) or 0),
        "root_vault_boundary": str(root_summary.get("boundary") or ""),
        "stability_alert_count": len(stability_alerts) if isinstance(stability_alerts, list) else 0,
        "volatility_alert_count": len(volatility_alerts) if isinstance(volatility_alerts, list) else 0,
        "time_context_status": str(context.time_layers.get("status") or "pending"),
        "dynamic_path_count": dynamic_path_count,
        "branch_conflict_path_count": branch_conflict_path_count,
        "tongguan_path_count": tongguan_path_count,
        "zhihua_path_count": zhihua_path_count,
        "follow_structure_boundary_signal": follow_structure_boundary_signal,
        "special_structure_boundary_signal": follow_structure_boundary_signal or day_share <= 0.22 or day_share >= 0.55,
        "regulation_climate_boundary_signal": climate_boundary_signal,
        "disputed_structure_signal": disputed_structure_signal,
        "boundary": "ranked_decision_scoring_basis_uses_chart_facts_and_model_signals_not_fixed_verdict",
    }


def _strength_candidate_scores(basis: dict[str, Any]) -> dict[str, float]:
    day_share = float(basis.get("day_element_share", 0.0))
    support_score = day_share
    if basis.get("seasonal_support"):
        support_score += 0.18
    if basis.get("seasonal_pressure"):
        support_score -= 0.14
    for row in basis.get("ten_god_energy_bands", []):
        if not isinstance(row, dict):
            continue
        if row.get("family") in {"self", "resource"} and row.get("energy_band") == "high":
            support_score += 0.08
        if row.get("family") in {"wealth", "authority", "output"} and row.get("energy_band") == "high":
            support_score -= 0.04
    support_score = max(0.0, min(1.0, support_score))
    score_bias = basis.get("model_signal_score_bias", {})
    score_bias = score_bias if isinstance(score_bias, dict) else {}
    review_penalty = float(score_bias.get("strength_review_penalty", 0.0) or 0.0)
    scores = {
        "strong": _score_from_distance(support_score, 0.68) - review_penalty,
        "slightly_strong": _score_from_distance(support_score, 0.55),
        "balanced": _score_from_distance(support_score, 0.42) + review_penalty,
        "slightly_weak": _score_from_distance(support_score, 0.30),
        "weak": _score_from_distance(support_score, 0.18) - review_penalty,
    }
    return _normalize_scores(scores)


def _structure_candidate_scores(basis: dict[str, Any], structure: StructureState) -> dict[str, float]:
    distribution = basis.get("element_distribution", {})
    spread = max(distribution.values()) - min(distribution.values()) if isinstance(distribution, dict) and distribution else 0.0
    day_share = float(basis.get("day_element_share", 0.0))
    conflict = float(basis.get("branch_conflict_path_count", 0.0))
    dynamic = float(basis.get("dynamic_path_count", 0.0))
    scores = {
        "ordinary_structure_review": 0.52 + min(0.16, dynamic * 0.02),
        "dynamic_structure_review": 0.44 + min(0.18, conflict * 0.06),
        "follow_structure_boundary_review": 0.22 + (0.24 if basis.get("follow_structure_boundary_signal") else 0.0) + min(0.1, float(basis.get("element_imbalance_ratio", 0.0)) * 0.24),
        "special_structure_boundary_review": 0.24 + (0.22 if basis.get("special_structure_boundary_signal") else 0.0) + min(0.12, spread * 0.03),
        "regulation_climate_boundary_review": 0.28 + (0.18 if basis.get("regulation_climate_boundary_signal") else 0.0),
        "disputed_structure_review": 0.26 + (0.2 if basis.get("disputed_structure_signal") else 0.0) + min(0.1, conflict * 0.005),
        "mediation_path_review": 0.24 + min(0.22, (float(basis.get("tongguan_path_count", 0.0)) + float(basis.get("zhihua_path_count", 0.0))) * 0.06),
    }
    score_bias = basis.get("model_signal_score_bias", {})
    score_bias = score_bias if isinstance(score_bias, dict) else {}
    scores["dynamic_structure_review"] += float(score_bias.get("dynamic_structure_bonus", 0.0) or 0.0)
    scores["disputed_structure_review"] += float(score_bias.get("dynamic_structure_bonus", 0.0) or 0.0) * 0.6
    if structure.state == "partial_missing_time":
        scores["ordinary_structure_review"] -= 0.06
        scores["dynamic_structure_review"] += 0.04
    return _normalize_scores(scores)


def _useful_god_candidate_scores(basis: dict[str, Any], families: list[str]) -> dict[str, float]:
    strength = _top_candidate(_strength_candidate_scores(basis))
    day_element = str(basis.get("day_master_element") or "")
    weak_elements = set(basis.get("weakest_elements", []))
    strong_elements = set(basis.get("strongest_elements", []))
    scores: dict[str, float] = {
        "balance_review": 0.44,
        "resource_or_self_support_review": 0.34,
        "output_or_wealth_release_review": 0.34,
        "authority_regulation_review": 0.28,
        "climate_regulation_review": 0.28,
    }
    if strength in {"weak", "slightly_weak"}:
        scores["resource_or_self_support_review"] += 0.24
    if strength in {"strong", "slightly_strong"}:
        scores["output_or_wealth_release_review"] += 0.2
        scores["authority_regulation_review"] += 0.1
    if strength == "balanced":
        scores["balance_review"] += 0.16
    if day_element and ELEMENT_GENERATED_BY.get(day_element) in weak_elements:
        scores["resource_or_self_support_review"] += 0.08
    if day_element and ELEMENT_GENERATES.get(day_element) in weak_elements:
        scores["output_or_wealth_release_review"] += 0.08
    if day_element and ELEMENT_CONTROLS.get(day_element) in strong_elements:
        scores["output_or_wealth_release_review"] += 0.05
    if day_element and ELEMENT_CONTROLLED_BY.get(day_element) in strong_elements:
        scores["authority_regulation_review"] += 0.08
    if "fire" in weak_elements or "water" in weak_elements:
        scores["climate_regulation_review"] += 0.12
    score_bias = basis.get("model_signal_score_bias", {})
    score_bias = score_bias if isinstance(score_bias, dict) else {}
    non_unique_bonus = float(score_bias.get("useful_god_non_unique_bonus", 0.0) or 0.0)
    scores["balance_review"] += non_unique_bonus
    scores["climate_regulation_review"] += non_unique_bonus * 0.5
    for family in families:
        if family in {"resource", "self"}:
            scores["resource_or_self_support_review"] += 0.04
        elif family in {"output", "wealth"}:
            scores["output_or_wealth_release_review"] += 0.04
        elif family == "authority":
            scores["authority_regulation_review"] += 0.04
        else:
            scores["balance_review"] += 0.02
    return _normalize_scores(scores)


def _score_from_distance(value: float, target: float) -> float:
    return round(max(0.0, 1.0 - abs(value - target) * 2.8), 3)


def _normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    return {
        key: round(max(0.0, min(0.99, value)), 3)
        for key, value in sorted(scores.items(), key=lambda row: (-row[1], row[0]))
    }


def _with_score_diagnostics(basis: dict[str, Any], scores: dict[str, float]) -> dict[str, Any]:
    rows = sorted(scores.items(), key=lambda row: (-row[1], row[0]))
    top_score = rows[0][1] if rows else 0.0
    runner_up_score = rows[1][1] if len(rows) > 1 else 0.0
    gap = round(top_score - runner_up_score, 3)
    enriched = dict(basis)
    enriched.update({
        "score_top_candidate": rows[0][0] if rows else "",
        "score_runner_up_candidate": rows[1][0] if len(rows) > 1 else "",
        "score_top_gap": gap,
        "close_candidate_count": sum(1 for _, score in rows if top_score - score <= 0.12),
        "non_unique_candidate_signal": bool(rows and gap <= 0.12),
    })
    return enriched


def _top_candidate(scores: dict[str, float]) -> str:
    if not scores:
        return "candidate_review_required"
    return max(scores.items(), key=lambda row: (row[1], row[0]))[0]


def _alternatives(scores: dict[str, float], primary: str, *, fallback: list[str]) -> list[str]:
    rows = [key for key in scores if key != primary][:3]
    for item in fallback:
        if item and item != primary and item not in rows:
            rows.append(item)
        if len(rows) >= 4:
            break
    return rows


def _candidate_confidence(scores: dict[str, float], *, base: float) -> float:
    if not scores:
        return round(max(0.0, min(0.78, base)), 3)
    values = sorted(scores.values(), reverse=True)
    separation = values[0] - values[1] if len(values) > 1 else values[0]
    return round(max(0.0, min(0.86, base * 0.65 + values[0] * 0.22 + separation * 0.25)), 3)


def _extreme_elements(distribution: dict[str, float], fn: Any) -> list[str]:
    if not distribution:
        return []
    target = fn(distribution.values())
    return sorted(element for element, value in distribution.items() if value == target)


def _support_value(supports: list[str], prefix: str) -> str:
    for support in supports:
        if support.startswith(prefix):
            return support.removeprefix(prefix)
    return ""


def _decision_model_signal(domain: str, summary: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(summary, dict):
        return {}
    consumers = summary.get("ranked_decision_inputs", {})
    if not isinstance(consumers, dict):
        consumers = {}
    payload = consumers.get(domain, {})
    if not isinstance(payload, dict):
        payload = {}
    if not payload:
        return {}
    interface_contract = summary.get("interface_contract", {})
    interface_contract = interface_contract if isinstance(interface_contract, dict) else {}
    calibration_profile = summary.get("calibration_profile", {})
    calibration_profile = calibration_profile if isinstance(calibration_profile, dict) else {}
    return {
        "version": "v30.model_signal_decision_input.v1",
        "summary_id": str(summary.get("summary_id", "")),
        "domain": domain,
        "energy_bands": payload.get("energy_bands", []),
        "stability_notes": payload.get("stability_notes", []),
        "volatility_notes": payload.get("volatility_notes", []),
        "interface_contract_version": str(interface_contract.get("version") or ""),
        "calibration_profile_version": str(calibration_profile.get("version") or ""),
        "requires_review": bool(payload.get("requires_review", False)),
        "boundary": "ranked_decision_consumes_model_signal_summary_not_raw_score",
    }


def _model_signal_evidence(model_signal: dict[str, Any]) -> list[str]:
    if not model_signal:
        return []
    summary_id = str(model_signal.get("summary_id", ""))
    if not summary_id:
        return ["model_signal_summary"]
    return [summary_id]


def _model_signal_weakening(model_signal: dict[str, Any]) -> list[str]:
    if not model_signal or not model_signal.get("requires_review"):
        return []
    return ["model_signal_volatility_requires_review"]


def _domain_reading(
    domain: str,
    context: ChartContext,
    structure: StructureState,
    timing: dict[str, Any],
    ranked_decisions: dict[str, dict[str, Any]],
    ten_god_energy_summary: dict[str, Any],
) -> dict[str, Any]:
    score_key = {
        "career": "dynamic_career_path_count",
        "wealth": "dynamic_wealth_path_count",
        "relationship": "dynamic_relationship_path_count",
        "health": "dynamic_health_review_path_count",
    }[domain]
    active_score = float(structure.path_scores.get(score_key, 0.0))
    active = active_score > 0
    timing_ready = timing.get("status") == "ready"
    profile = DOMAIN_PROFILES[domain]
    decision = ranked_decisions.get("structure_pattern", {})
    useful = ranked_decisions.get("useful_god", {})
    strength = ranked_decisions.get("strength", {})
    state = "active" if active else "needs_context"
    priority_score = _domain_priority_score(active_score, timing_ready, structure)
    decision_links = _ranked_decision_links(ranked_decisions)
    calculation_basis = _practical_calculation_basis(context, structure, timing, score_key, active_score)
    model_signal_context = _practical_model_signal_context(ten_god_energy_summary)
    return {
        "version": "v30.practical_domain_reading.v2",
        "domain": domain,
        "label": profile["label"],
        "state": state,
        "summary": profile["active"] if active else profile["review"],
        "customer_takeaway": _customer_takeaway(domain, active=active, timing_ready=timing_ready),
        "basis": [score_key, _public_structure_label(structure.semantic_label)],
        "depends_on_modules": ["M1/M2_chart_facts", "M3_evidence_rule_structure", "M4_model_signal", "M5_ranked_decisions"],
        "calculation_basis": calculation_basis,
        "decision_context": {
            "strength_candidate": _public_candidate_label(strength.get("primary_candidate", "")),
            "structure_candidate": _public_candidate_label(decision.get("primary_candidate", _public_structure_label(structure.semantic_label))),
            "useful_god_candidate": _public_candidate_label(useful.get("primary_candidate", "")),
            "confidence_band": _confidence_band(float(decision.get("confidence", structure.confidence))),
        },
        "ranked_decision_links": decision_links,
        "model_signal_context": model_signal_context,
        "domain_insights": _domain_insights(domain, calculation_basis, decision_links, model_signal_context, timing_ready=timing_ready),
        "action_steps": _domain_action_steps(domain, timing_ready=timing_ready),
        "calibration_prompts": _domain_calibration_prompts(domain, timing_ready=timing_ready),
        "module_trace": _practical_module_trace(calculation_basis, decision_links, model_signal_context),
        "evidence_ids": _domain_evidence_ids(structure, decision_links),
        "explanation_units": _domain_explanation_units(domain, calculation_basis, decision_links, model_signal_context),
        "risk": "需要结合大运/流年触发条件，不作单点断语。",
        "boundary_conditions": _domain_boundary_conditions(domain, timing_ready=timing_ready),
        "blocked_claims": _domain_blocked_claims(domain),
        "action_prompt": profile["action"],
        "priority_score": priority_score,
        "timing_trigger": {
            "luck_pillar": timing.get("luck_pillar", ""),
            "flow_year_pillar": timing.get("flow_year_pillar", ""),
            "status": timing.get("status", ""),
        },
        "question_gap": "" if active and timing_ready else f"clarify_{domain}_priority_or_event_year",
        "quality_contract": _reading_quality_contract(domain),
        "reading_boundary": "practical_domain_reading_is_evidence_bound_review_not_life_outcome_verdict",
    }


def _timing_reading(
    context: ChartContext,
    structure: StructureState,
    timing: dict[str, Any],
    ranked_decisions: dict[str, dict[str, Any]],
    ten_god_energy_summary: dict[str, Any],
) -> dict[str, Any]:
    timing_ready = timing.get("status") == "ready"
    calculation_basis = _practical_calculation_basis(
        context,
        structure,
        timing,
        "six_pillar_context",
        1.0 if timing_ready else 0.0,
    )
    decision_links = _ranked_decision_links(ranked_decisions)
    model_signal_context = _practical_model_signal_context(ten_god_energy_summary)
    return {
        "version": "v30.practical_domain_reading.v2",
        "domain": "timing",
        "label": "时机",
        "state": "active" if timing_ready else "needs_context",
        "summary": "当前已接入大运/流年上下文，可把阅读限定在阶段趋势与触发条件。" if timing_ready else "当前只做原局分析，时运判断需要大运/流年上下文。",
        "customer_takeaway": "时机内容只能作为阶段性复核线索，不是确定事件预测。",
        "basis": ["six_pillar_context", _public_structure_label(structure.semantic_label)],
        "depends_on_modules": ["M1/M2_chart_facts", "M3_evidence_rule_structure", "M4_model_signal", "M5_ranked_decisions"],
        "calculation_basis": calculation_basis,
        "decision_context": {
            "strength_candidate": _public_candidate_label(ranked_decisions.get("strength", {}).get("primary_candidate", "")),
            "structure_candidate": _public_candidate_label(ranked_decisions.get("structure_pattern", {}).get("primary_candidate", "")),
            "useful_god_candidate": _public_candidate_label(ranked_decisions.get("useful_god", {}).get("primary_candidate", "")),
            "confidence_band": _confidence_band(float(ranked_decisions.get("structure_pattern", {}).get("confidence", structure.confidence))),
        },
        "ranked_decision_links": decision_links,
        "model_signal_context": model_signal_context,
        "domain_insights": _domain_insights("timing", calculation_basis, decision_links, model_signal_context, timing_ready=timing_ready),
        "action_steps": _domain_action_steps("timing", timing_ready=timing_ready),
        "calibration_prompts": _domain_calibration_prompts("timing", timing_ready=timing_ready),
        "module_trace": _practical_module_trace(calculation_basis, decision_links, model_signal_context),
        "evidence_ids": _domain_evidence_ids(structure, decision_links),
        "explanation_units": _domain_explanation_units("timing", calculation_basis, decision_links, model_signal_context),
        "risk": "不能把流年触发说成确定事件。",
        "boundary_conditions": _domain_boundary_conditions("timing", timing_ready=timing_ready),
        "blocked_claims": _domain_blocked_claims("timing"),
        "action_prompt": "补充当前大运、流年关注点或近期关键年份。",
        "priority_score": 0.72 if not timing_ready else 0.48,
        "timing_trigger": {
            "luck_pillar": timing.get("luck_pillar", ""),
            "flow_year_pillar": timing.get("flow_year_pillar", ""),
            "flow_month_pillar": timing.get("flow_month_pillar", ""),
            "status": timing.get("status", ""),
        },
        "question_gap": "" if timing_ready else "confirm_luck_flow_context",
        "quality_contract": _reading_quality_contract("timing"),
        "reading_boundary": "timing_reading_is_stage_review_not_fixed_event_prediction",
    }


def _domain_priority_score(active_score: float, timing_ready: bool, structure: StructureState) -> float:
    score = 0.34 + min(0.28, active_score * 0.06)
    if not timing_ready:
        score += 0.16
    score += min(0.12, float(structure.path_scores.get("domain_rule_depth_path_count", 0.0)) * 0.02)
    return round(min(0.95, score), 3)


def _ranked_decision_links(ranked_decisions: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for domain in ("strength", "structure_pattern", "useful_god"):
        decision = ranked_decisions.get(domain, {})
        if not isinstance(decision, dict):
            continue
        out[domain] = {
            "decision_id": str(decision.get("decision_id", "")),
            "primary_candidate": _public_candidate_label(decision.get("primary_candidate", "")),
            "confidence_band": _confidence_band(float(decision.get("confidence", 0.0) or 0.0)),
            "supporting_evidence": _string_list(decision.get("supporting_evidence", []))[:8],
            "weakening_evidence": _string_list(decision.get("weakening_evidence", []))[:8],
            "unresolved_requirements": _string_list(decision.get("unresolved_requirements", [])),
            "boundary": str(decision.get("boundary", "")),
        }
    return out


def _practical_calculation_basis(
    context: ChartContext,
    structure: StructureState,
    timing: dict[str, Any],
    path_score_key: str,
    path_score_value: float,
) -> dict[str, Any]:
    base_summary = context.natal_pillars.get("base_fact_summary", {})
    base_summary = base_summary if isinstance(base_summary, dict) else {}
    root_summary = base_summary.get("root_fact_summary", {})
    root_summary = root_summary if isinstance(root_summary, dict) else {}
    element_distribution = context.natal_pillars.get("element_distribution", {})
    if not isinstance(element_distribution, dict):
        element_distribution = {}
    return {
        "version": "v30.practical_domain_calculation_basis.v1",
        "day_master": context.day_master,
        "day_master_element": context.day_master_element,
        "element_distribution_keys": sorted(str(key) for key in element_distribution),
        "root_fact_summary_version": str(root_summary.get("version") or ""),
        "root_vault_boundary": str(root_summary.get("boundary") or ""),
        "structure_state": structure.state,
        "structure_label": _public_structure_label(structure.semantic_label),
        "path_score_key": path_score_key,
        "path_score_value": round(float(path_score_value), 3),
        "timing_status": str(timing.get("status", "")),
        "luck_pillar": str(timing.get("luck_pillar", "")),
        "flow_year_pillar": str(timing.get("flow_year_pillar", "")),
        "flow_month_pillar": str(timing.get("flow_month_pillar", "")),
        "boundary": "practical_basis_uses_existing_chart_facts_and_ranked_candidates_not_new_facts",
    }


def _practical_model_signal_context(ten_god_energy_summary: dict[str, Any]) -> dict[str, Any]:
    top_energy = ten_god_energy_summary.get("top_energy", []) if isinstance(ten_god_energy_summary, dict) else []
    if not isinstance(top_energy, list):
        top_energy = []
    return {
        "version": "v30.practical_model_signal_context.v1",
        "status": str(ten_god_energy_summary.get("status") or "pending"),
        "dominant_ten_gods": _string_list(ten_god_energy_summary.get("dominant_ten_gods", [])),
        "top_energy_bands": [
            {
                "label": str(row.get("label", "")),
                "family": str(row.get("family", "")),
                "energy_band": _value_band(float(row.get("energy", 0.0) or 0.0)),
                "stability_band": _value_band(float(row.get("stability", 0.0) or 0.0)),
                "volatility_band": _value_band(float(row.get("volatility", 0.0) or 0.0)),
            }
            for row in top_energy
            if isinstance(row, dict)
        ],
        "high_volatility_ten_gods": _string_list(ten_god_energy_summary.get("high_volatility_ten_gods", [])),
        "low_stability_ten_gods": _string_list(ten_god_energy_summary.get("low_stability_ten_gods", [])),
        "forbidden_fields": ["raw_weight", "raw_score", "energy", "stability", "volatility"],
        "boundary": "practical_reading_consumes_model_signal_bands_not_raw_scores",
    }


def _domain_evidence_ids(structure: StructureState, decision_links: dict[str, dict[str, Any]]) -> list[str]:
    rows = [str(row) for row in structure.evidence_ids if row]
    for decision in decision_links.values():
        rows.extend(_string_list(decision.get("supporting_evidence", [])))
    out: list[str] = []
    for row in rows:
        if row and row not in out:
            out.append(row)
    return out[:12]


def _domain_explanation_units(
    domain: str,
    calculation_basis: dict[str, Any],
    decision_links: dict[str, dict[str, Any]],
    model_signal_context: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "unit": "chart_fact_basis",
            "text": f"{domain} reading starts from day master, element distribution, root/vault presence, and timing status.",
            "source": calculation_basis.get("version"),
            "boundary": calculation_basis.get("boundary"),
        },
        {
            "unit": "ranked_candidate_basis",
            "text": "Strength, structure, and useful-god remain ranked candidates with counter-evidence and unresolved requirements.",
            "source": sorted(decision_links),
            "boundary": "ranked_candidates_support_reading_not_fixed_verdict",
        },
        {
            "unit": "model_signal_basis",
            "text": "Ten-god model signals can change emphasis and review priority only through bands and alerts.",
            "source": model_signal_context.get("version"),
            "boundary": model_signal_context.get("boundary"),
        },
    ]


def _domain_insights(
    domain: str,
    calculation_basis: dict[str, Any],
    decision_links: dict[str, dict[str, Any]],
    model_signal_context: dict[str, Any],
    *,
    timing_ready: bool,
) -> list[dict[str, Any]]:
    structure_candidate = str(
        (decision_links.get("structure_pattern", {}) if isinstance(decision_links.get("structure_pattern"), dict) else {}).get("primary_candidate", "")
    )
    useful_candidate = str(
        (decision_links.get("useful_god", {}) if isinstance(decision_links.get("useful_god"), dict) else {}).get("primary_candidate", "")
    )
    high_volatility = _string_list(model_signal_context.get("high_volatility_ten_gods", []))
    low_stability = _string_list(model_signal_context.get("low_stability_ten_gods", []))
    base = {
        "career": {
            "opportunity": "职责、协作与阶段性压力可以作为事业判断的主要入口。",
            "pressure": "避免把官杀、结构压力或流年触发直接说成升迁或失业。",
            "adjustment": "先校准岗位环境、上级压力、合作关系和近两年关键变化。",
        },
        "wealth": {
            "opportunity": "收入结构、资源投入和合作分账可以作为财务判断的主要入口。",
            "pressure": "避免把财星强弱直接说成收入金额、投资结果或必然破财。",
            "adjustment": "先校准现金流模式、风险承受、投入周期和合作账务边界。",
        },
        "relationship": {
            "opportunity": "沟通方式、承诺压力和关系中的外部牵引是当前关系判断入口。",
            "pressure": "避免把合冲刑害或配偶星信号直接说成结婚、分手或第三方事件。",
            "adjustment": "先校准关系状态、沟通矛盾、家庭压力和关键年份反馈。",
        },
        "health": {
            "opportunity": "压力承载、作息节律和恢复方式是身心判断入口。",
            "pressure": "避免输出疾病诊断、医学预测或确定风险事件。",
            "adjustment": "先校准睡眠、压力来源、作息变化和已知专业检查结论。",
        },
        "timing": {
            "opportunity": "大运、流年、流月只用于阶段复核和触发条件排序。",
            "pressure": "避免把单一年份或单一柱位说成确定事件。",
            "adjustment": "先校准用户关注年份、近期事件和当前阶段目标。",
        },
    }[domain]
    return [
        {
            "insight_type": "opportunity_path",
            "text": base["opportunity"],
            "basis": [
                str(calculation_basis.get("path_score_key", "")),
                structure_candidate,
                useful_candidate,
            ],
            "boundary": "domain_opportunity_is_candidate_path_not_fixed_outcome",
        },
        {
            "insight_type": "pressure_or_risk_path",
            "text": base["pressure"],
            "basis": high_volatility[:4] + low_stability[:4],
            "boundary": "domain_pressure_is_review_signal_not_prediction",
        },
        {
            "insight_type": "calibration_path",
            "text": base["adjustment"],
            "basis": [
                "timing_ready" if timing_ready else "timing_context_needed",
                str(model_signal_context.get("status", "")),
            ],
            "boundary": "domain_calibration_uses_feedback_without_mutating_chart_facts",
        },
    ]


def _domain_action_steps(domain: str, *, timing_ready: bool) -> list[dict[str, Any]]:
    rows = {
        "career": [
            ("clarify_current_role", "确认当前岗位、职责边界和最主要压力来源。"),
            ("map_collaboration_pressure", "把上级、同事、合作方压力分开看。"),
            ("review_recent_years", "列出近两年明显转折年份用于校准时机。"),
        ],
        "wealth": [
            ("clarify_income_model", "确认收入来自工资、经营、投资还是合作分账。"),
            ("map_risk_exposure", "区分现金流压力、投入周期和杠杆风险。"),
            ("review_recent_years", "列出近两年财务波动年份用于校准。"),
        ],
        "relationship": [
            ("clarify_relationship_state", "确认当前关系状态和主要矛盾类型。"),
            ("map_external_pressure", "区分沟通、家庭、距离、承诺或合作压力。"),
            ("review_recent_years", "列出近两年关系变化年份用于校准。"),
        ],
        "health": [
            ("clarify_stress_pattern", "确认压力来源、睡眠作息和恢复方式。"),
            ("separate_medical_boundary", "已有医学问题以专业诊断为准，命理只做压力复核。"),
            ("review_recent_years", "列出近两年身心状态变化年份用于校准。"),
        ],
        "timing": [
            ("clarify_target_year", "确认用户关注的年份或阶段。"),
            ("separate_stage_and_event", "先看阶段趋势，再看可能触发条件，不做定事。"),
            ("review_recent_years", "用已发生年份校准大运/流年的解释边界。"),
        ],
    }[domain]
    if not timing_ready:
        rows.append(("confirm_luck_flow_context", "补充出生时辰或关键年份后再展开时机判断。"))
    return [
        {
            "step_id": step_id,
            "text": text,
            "boundary": "action_step_guides_user_feedback_not_chart_fact",
        }
        for step_id, text in rows
    ]


def _domain_calibration_prompts(domain: str, *, timing_ready: bool) -> list[dict[str, Any]]:
    prompts = {
        "career": ["最近两年事业上最明显的压力或机会是哪一年？", "当前更关心方向选择、升迁压力、合作冲突还是转型？"],
        "wealth": ["最近两年财务波动最明显的是哪一年？", "当前更关心收入、投资、现金流还是合作分账？"],
        "relationship": ["最近两年关系变化最明显的是哪一年？", "当前更关心亲密关系、家庭压力、合作关系还是沟通模式？"],
        "health": ["最近两年压力或作息变化最明显的是哪一年？", "当前更关心压力来源、睡眠、恢复节奏还是触发点？"],
        "timing": ["当前最想复核哪一年或哪个阶段？", "这个阶段已经发生的明显事件或状态是什么？"],
    }[domain]
    if not timing_ready:
        prompts.append("如果时辰不确定，可以先提供几个关键年份作为校准线索。")
    return [
        {
            "prompt": prompt,
            "trains": ["domain_priority", "timing_calibration", "expression_fit"],
            "boundary": "calibration_prompt_collects_feedback_not_new_chart_fact",
        }
        for prompt in prompts
    ]


def _practical_module_trace(
    calculation_basis: dict[str, Any],
    decision_links: dict[str, dict[str, Any]],
    model_signal_context: dict[str, Any],
) -> dict[str, Any]:
    return {
        "version": "v30.m6_practical_module_trace.v1",
        "uses_m1_m2_facts": calculation_basis.get("version") == "v30.practical_domain_calculation_basis.v1",
        "uses_m3_structure_evidence": bool(calculation_basis.get("structure_state")),
        "uses_m4_model_signal": model_signal_context.get("version") == "v30.practical_model_signal_context.v1",
        "uses_m5_ranked_decisions": {"strength", "structure_pattern", "useful_god"} <= set(decision_links),
        "raw_model_score_visible": False,
        "chart_fact_mutation_allowed": False,
        "boundary": "m6_trace_proves_practical_reading_consumes_core_modules_without_mutating_them",
    }


def _domain_boundary_conditions(domain: str, *, timing_ready: bool) -> list[str]:
    rows = [
        "must_reference_existing_chart_facts",
        "must_reference_ranked_decision_boundary",
        "must_not_mutate_birth_chart_or_luck_flow_facts",
        "must_not_expose_raw_model_scores",
    ]
    if not timing_ready:
        rows.append("timing_claim_blocked_until_luck_flow_context_ready")
    if domain == "health":
        rows.append("health_output_is_stress_and_routine_review_not_medical_advice")
    return rows


def _domain_blocked_claims(domain: str) -> list[str]:
    blocked = {
        "career": ["fixed_job_title_prediction", "certain_promotion_or_job_loss_year"],
        "wealth": ["certain_income_amount", "guaranteed_investment_gain_or_loss"],
        "relationship": ["certain_marriage_or_breakup_event", "single_branch_relation_event_claim"],
        "health": ["medical_diagnosis", "disease_prediction"],
        "timing": ["fixed_event_prediction", "single_flow_year_certain_outcome"],
    }
    return blocked[domain]


def _value_band(value: float) -> str:
    if value >= 0.68:
        return "high"
    if value >= 0.38:
        return "medium"
    return "low"


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(row) for row in value if row]


def _public_structure_label(value: str) -> str:
    raw = str(value or "").strip()
    lowered = raw.lower()
    traits: list[str] = []
    if any(token in lowered for token in ("branch", "dynamic")):
        traits.append("地支动态")
    if any(token in lowered for token in ("strength", "pattern")):
        traits.append("旺衰候选")
    if "ten-god" in lowered or "ten_god" in lowered:
        traits.append("十神评分")
    if "counter" in lowered:
        traits.append("反证")
    if any(token in lowered for token in ("path", "mechanism")):
        traits.append("路径评分")
    if "time layer missing" in lowered:
        traits.append("时运待补")
    if any(token in lowered for token in ("evidence", "chart", "knowledge/rule/portrait", "rule evidence")):
        traits.insert(0, "证据约束")
    rows: list[str] = []
    for trait in traits:
        if trait and trait not in rows:
            rows.append(trait)
    if rows:
        priority = ["证据约束", "反证", "地支动态", "旺衰候选", "路径评分", "十神评分", "时运待补"]
        rows = [row for row in priority if row in rows][:4]
        detail = "、".join(row for row in rows if row != "证据约束")
        return f"证据约束型结构（含{detail}）" if detail else "证据约束型结构"
    return raw[:80] or "结构待复核"


def _public_candidate_label(value: Any) -> str:
    raw = str(value or "").strip()
    labels = {
        "strong": "日主偏旺候选",
        "slightly_strong": "日主略偏旺候选",
        "balanced": "平衡取向",
        "slightly_weak": "日主略偏弱候选",
        "weak": "日主偏弱候选",
        "dynamic_structure_review": "动态结构复核",
        "ordinary_structure_review": "常规格局复核",
        "special_structure_boundary_review": "特殊格局边界复核",
        "mediation_path_review": "通关承接路径",
        "resource_or_self_support_review": "印比扶助方向",
        "output_or_wealth_release_review": "食伤生财或财星释放方向",
        "authority_regulation_review": "官杀约束承接方向",
        "climate_regulation_review": "调候平衡方向",
        "balance_review": "平衡调候方向",
        "needs_time_layer_review": "需要时运复核",
    }
    if raw in labels:
        return labels[raw]
    if "evidence-bound" in raw.lower():
        return _public_structure_label(raw)
    return raw.replace("_", " ") or "候选待复核"


def _customer_takeaway(domain: str, *, active: bool, timing_ready: bool) -> str:
    profile = DOMAIN_PROFILES[domain]
    if active and timing_ready:
        return f"{profile['label']}可以进入具体问题，但仍按候选路径表达，不做确定断语。"
    if active:
        return f"{profile['label']}已有可读线索，下一步需要关键年份或当前处境来校准。"
    return f"{profile['label']}目前适合先问用户优先级，再决定是否展开。"


def _confidence_band(confidence: float) -> str:
    if confidence >= 0.72:
        return "high_review_confidence"
    if confidence >= 0.5:
        return "medium_review_confidence"
    return "low_review_confidence"


def _reading_quality_contract(domain: str) -> dict[str, object]:
    return {
        "version": "v30.practical_reading_quality.v1",
        "domain": domain,
        "requires": [
            "human_readable_summary",
            "customer_takeaway",
            "action_prompt",
            "boundary_language",
        ],
        "trains": ["domain_ranking", "expression_strategy", "question_strategy"],
        "boundary": "practical_reading_quality_trains_expression_not_chart_facts",
    }
