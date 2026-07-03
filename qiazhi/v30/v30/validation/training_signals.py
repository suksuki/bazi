from __future__ import annotations

from pydantic import Field

from v30.contracts import V30Model
from v30.validation.production_replay_metadata import summarize_production_replay_metadata
from v30.validation.synthetic_case import SyntheticValidationSuiteResult


class SyntheticTrainingSignal(V30Model):
    signal_id: str
    domain: str
    signal_type: str
    strength: float
    source_case_ids: list[str] = Field(default_factory=list)
    payload: dict[str, object] = Field(default_factory=dict)


def extract_training_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    signals: list[SyntheticTrainingSignal] = []
    signals.extend(_krp_coverage_signals(result))
    signals.extend(_m3_core_spine_signals(result))
    signals.extend(_per_unit_parameter_tuning_signals(result))
    signals.extend(_birth_chart_conversion_boundary_signals(result))
    signals.extend(_m1_m2_base_fact_contract_signals(result))
    signals.extend(_luck_cycle_alignment_signals(result))
    signals.extend(_flow_timing_activation_signals(result))
    signals.extend(_six_pillar_context_signals(result))
    signals.extend(_ten_god_energy_fusion_signals(result))
    signals.extend(_ranked_decision_signals(result))
    signals.extend(_ranked_decision_fusion_signals(result))
    signals.extend(_practical_reading_quality_signals(result))
    signals.extend(_agent_question_flow_signals(result))
    signals.extend(_high_value_question_quality_signals(result))
    signals.extend(_question_model_signal_personalization_signals(result))
    signals.extend(_real_case_feedback_alignment_signals(result))
    signals.extend(_real_case_calibration_pack_signals(result))
    signals.extend(_m5_weight_replay_signals(result))
    signals.extend(_macro_dimension_signals(result))
    signals.extend(_portrait_projection_signals(result))
    signals.extend(_portrait_projection_view_signals(result))
    signals.extend(_role_locale_client_projection_signals(result))
    signals.extend(_api_projection_contract_signals(result))
    signals.extend(_question_graph_signals(result))
    signals.extend(_question_dialogue_outcome_signals(result))
    signals.extend(_interaction_state_machine_signals(result))
    signals.extend(_interaction_loop_quality_signals(result))
    signals.extend(_interaction_brain_structured_constraint_signals(result))
    signals.extend(_adaptive_question_replay_signals(result))
    signals.extend(_central_brain_route_signals(result))
    signals.extend(_central_brain_judge_quality_signals(result))
    signals.extend(_central_brain_synthesis_blueprint_quality_signals(result))
    signals.extend(_expression_quality_signals(result))
    signals.extend(_llm_output_contract_signals(result))
    signals.extend(_bazi_llm_output_acceptance_signals(result))
    signals.extend(_structure_dynamic_signals(result))
    signals.extend(_hidden_factor_event_alignment_signals(result))
    signals.extend(_latent_bazi_attribute_alignment_signals(result))
    signals.extend(_failure_signals(result))
    return signals


def _krp_coverage_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    unit_ids: set[str] = set()
    source_cases: list[str] = []
    for row in result.results:
        observed_units = row.observed.get("krp_library_unit_ids", [])
        if not isinstance(observed_units, list):
            continue
        unit_ids.update(str(unit_id) for unit_id in observed_units)
        if observed_units:
            source_cases.append(row.case_id)
    if not unit_ids:
        return []
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.krp_unit_coverage",
            domain="knowledge_rule_portrait",
            signal_type="coverage",
            strength=round(min(1.0, len(unit_ids) / 35), 3),
            source_case_ids=source_cases,
            payload={"unit_count": len(unit_ids), "unit_ids": sorted(unit_ids)},
        )
    ]


def _m3_core_spine_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    source_family_ids: set[str] = set()
    reference_asset_ids: set[str] = set()
    krp_domains: set[str] = set()
    rule_states: dict[str, int] = {}
    dynamic_cases = 0
    completion_rows: list[dict[str, object]] = []
    source_cases: list[str] = []
    for row in result.results:
        summary = row.observed.get("krp_library_summary", {})
        if isinstance(summary, dict):
            source_family_ids.update(str(item) for item in summary.get("source_family_ids", []) if item)
            reference_asset_ids.update(str(item) for item in summary.get("reference_asset_ids", []) if item)
            by_domain = summary.get("by_domain", {})
            if isinstance(by_domain, dict):
                krp_domains.update(str(domain) for domain in by_domain if domain)
        states = row.observed.get("rule_states_by_kind", {})
        if isinstance(states, dict):
            for state_values in states.values():
                values = state_values if isinstance(state_values, list) else [state_values]
                for state in values:
                    state_key = str(state)
                    if state_key:
                        rule_states[state_key] = rule_states.get(state_key, 0) + 1
        path_scores = row.observed.get("structure_path_scores", {})
        if isinstance(path_scores, dict) and path_scores.get("dynamic_path_count"):
            dynamic_cases += 1
        completion = row.observed.get("m3_completion_summary", {})
        if isinstance(completion, dict) and completion:
            completion_rows.append(completion)
        if summary or states or path_scores or completion:
            source_cases.append(row.case_id)
    if not source_cases:
        return []
    completion_ready_count = sum(
        1 for row in completion_rows
        if row.get("version") == "v30.m3_completion_summary.v1"
        and row.get("status") == "ready"
        and row.get("m4_model_signal_support") is True
        and int(row.get("m5_ranked_decision_support_count", 0) or 0) >= 2
        and int(row.get("m6_practical_reading_support_count", 0) or 0) >= 5
        and row.get("acts_as_conclusion_engine") is False
        and row.get("chart_fact_mutation_allowed") is False
    )
    average_completion_coverage = (
        sum(float(row.get("completion_coverage", 0.0) or 0.0) for row in completion_rows) / len(completion_rows)
        if completion_rows else 0.0
    )
    strength = round(min(
        1.0,
        len(source_family_ids) / 6 * 0.25
        + len(krp_domains) / 12 * 0.2
        + dynamic_cases / max(1, result.case_count) * 0.2
        + len(rule_states) / 4 * 0.15
        + completion_ready_count / max(1, len(completion_rows) or 1) * 0.2,
    ), 3)
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.m3_core_spine_coverage",
            domain="m3_core_spine",
            signal_type="source_rule_feature_dynamic_coverage",
            strength=strength,
            source_case_ids=source_cases,
            payload={
                "source_family_ids": sorted(source_family_ids),
                "source_family_count": len(source_family_ids),
                "reference_asset_ids": sorted(reference_asset_ids),
                "reference_asset_count": len(reference_asset_ids),
                "krp_domains": sorted(krp_domains),
                "krp_domain_count": len(krp_domains),
                "rule_state_counts": dict(sorted(rule_states.items())),
                "dynamic_case_count": dynamic_cases,
                "completion_summary_version": "v30.m3_completion_summary.v1",
                "completion_summary_count": len(completion_rows),
                "completion_ready_count": completion_ready_count,
                "average_completion_coverage": round(average_completion_coverage, 3),
                "m4_support_ready_count": sum(1 for row in completion_rows if row.get("m4_model_signal_support") is True),
                "m5_support_ready_count": sum(1 for row in completion_rows if int(row.get("m5_ranked_decision_support_count", 0) or 0) >= 2),
                "m6_support_ready_count": sum(1 for row in completion_rows if int(row.get("m6_practical_reading_support_count", 0) or 0) >= 5),
                "conclusion_engine_count": sum(1 for row in completion_rows if row.get("acts_as_conclusion_engine") is True),
                "chart_fact_mutation_allowed_count": sum(1 for row in completion_rows if row.get("chart_fact_mutation_allowed") is True),
                "boundary": "m3_core_spine_trains_source_rule_path_weights_not_chart_facts",
            },
        )
    ]


def _birth_chart_conversion_boundary_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    observations: list[dict[str, object]] = []
    source_cases: list[str] = []
    for row in result.results:
        observed = row.observed.get("birth_chart_conversion_boundary", {})
        if not isinstance(observed, dict) or not observed:
            continue
        observations.append(observed)
        source_cases.append(row.case_id)
    if not observations:
        return []
    statuses = sorted({str(row.get("status")) for row in observations if row.get("status")})
    boundary_flags = sorted({
        str(flag)
        for row in observations
        for flag in (row.get("boundary_flags") if isinstance(row.get("boundary_flags"), list) else [])
    })
    missing_requirements = sorted({
        str(item)
        for row in observations
        for item in (row.get("missing_requirements") if isinstance(row.get("missing_requirements"), list) else [])
    })
    ready_count = sum(1 for row in observations if row.get("status") == "ready")
    blocked_count = sum(1 for row in observations if row.get("status") in {"pending", "unsupported", "blocked"})
    no_fake_fact_count = sum(1 for row in observations if not row.get("has_pillars") and row.get("status") != "ready")
    coverage = min(1.0, len(boundary_flags) / 5)
    strength = round(min(1.0, coverage * 0.45 + ready_count / max(1, len(observations)) * 0.25 + no_fake_fact_count / max(1, blocked_count or 1) * 0.3), 3)
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.birth_chart_conversion_boundary",
            domain="core_calculation",
            signal_type="conversion_boundary_coverage",
            strength=strength,
            source_case_ids=source_cases,
            payload={
                "case_count": len(observations),
                "ready_count": ready_count,
                "blocked_count": blocked_count,
                "no_fake_fact_count": no_fake_fact_count,
                "statuses": statuses,
                "boundary_flags": boundary_flags,
                "missing_requirements": missing_requirements,
                "boundary": "birth_chart_conversion_signal_validates_deterministic_conversion_not_chart_fact",
            },
        )
    ]


def _m1_m2_base_fact_contract_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    rows = [row for row in _observed_dicts(result, "m1_m2_base_fact_contract") if row]
    if not rows:
        return []
    ready_rows = [row for row in rows if row.get("status") == "ready"]
    deterministic_count = sum(1 for row in ready_rows if row.get("deterministic") is True)
    non_deterministic_count = sum(int(row.get("non_deterministic_source_count", 0) or 0) for row in rows)
    summary_keys = sorted({
        str(key)
        for row in rows
        for key in (row.get("summary_keys", []) if isinstance(row.get("summary_keys"), list) else [])
        if key
    })
    relation_families = sorted({
        str(family)
        for row in rows
        for family in (row.get("relation_families", []) if isinstance(row.get("relation_families"), list) else [])
        if family
    })
    categories = {
        "solar": any(row.get("calendar_type") == "solar" for row in rows),
        "lunar": any(row.get("calendar_type") == "lunar" and not row.get("lunar_is_leap_month") for row in rows),
        "leap_month_lunar": any(row.get("lunar_is_leap_month") for row in rows),
        "true_solar": any(row.get("use_true_solar_time") for row in rows),
        "unknown_gender": any(row.get("gender_status") == "unknown" for row in rows),
    }
    hidden_ready_count = sum(1 for row in ready_rows if int(row.get("hidden_ten_god_count", 0) or 0) > 0)
    explanation_ready_count = sum(
        1 for row in ready_rows
        if row.get("explanation_boundary") == "base_fact_explanations_are_deterministic_context_not_ranked_decisions"
    )
    root_fact_ready_count = sum(
        1 for row in ready_rows
        if isinstance(row.get("root_fact_summary"), dict)
        and row.get("root_fact_summary", {}).get("boundary") == "root_vault_summary_records_presence_without_strength_or_useful_god_verdict"
    )
    completion_ready_count = sum(
        1 for row in ready_rows
        if row.get("completion_summary_version") == "v30.m1_m2_completion_summary.v1"
        and row.get("completion_status") == "ready"
        and float(row.get("completion_required_key_coverage", 0.0) or 0.0) == 1.0
        and float(row.get("completion_explanation_coverage", 0.0) or 0.0) == 1.0
        and row.get("completion_downstream_consumption_ready") is True
        and row.get("completion_chart_fact_mutation_allowed") is False
    )
    downstream_ready_count = sum(
        1 for row in ready_rows
        if int(row.get("completion_m5_uses_root_fact_summary_count", 0) or 0) >= 3
        and int(row.get("completion_m6_uses_m1_m2_fact_count", 0) or 0) >= 5
    )
    required_keys = {
        "visible_ten_god_counts",
        "hidden_ten_god_counts",
        "hidden_stem_summary",
        "relation_type_counts",
        "relation_families",
        "element_distribution",
        "root_fact_summary",
    }
    key_coverage = len(required_keys & set(summary_keys)) / len(required_keys)
    strength = round(min(
        1.0,
        key_coverage * 0.35
        + deterministic_count / max(1, len(ready_rows)) * 0.25
        + hidden_ready_count / max(1, len(ready_rows)) * 0.2
        + explanation_ready_count / max(1, len(ready_rows)) * 0.1
        + root_fact_ready_count / max(1, len(ready_rows)) * 0.05
        + completion_ready_count / max(1, len(ready_rows)) * 0.05
        + downstream_ready_count / max(1, len(ready_rows)) * 0.05
        - min(0.25, non_deterministic_count * 0.05),
    ), 3)
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.m1_m2_base_fact_contract",
            domain="core_calculation",
            signal_type="deterministic_base_fact_contract_coverage",
            strength=max(0.0, strength),
            source_case_ids=[
                row.case_id for row in result.results
                if isinstance(row.observed.get("m1_m2_base_fact_contract"), dict)
                and row.observed.get("m1_m2_base_fact_contract")
            ],
            payload={
                "case_count": len(rows),
                "ready_count": len(ready_rows),
                "deterministic_count": deterministic_count,
                "non_deterministic_source_count": non_deterministic_count,
                "hidden_ready_count": hidden_ready_count,
                "explanation_ready_count": explanation_ready_count,
                "root_fact_ready_count": root_fact_ready_count,
                "completion_summary_version": "v30.m1_m2_completion_summary.v1",
                "completion_ready_count": completion_ready_count,
                "downstream_consumption_ready_count": downstream_ready_count,
                "summary_keys": summary_keys,
                "required_key_coverage": round(key_coverage, 3),
                "relation_families": relation_families,
                "categories": categories,
                "boundary": "m1_m2_base_fact_contract_trains_validation_coverage_not_chart_facts",
            },
        )
    ]


def _luck_cycle_alignment_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    rows = _observed_dicts(result, "luck_cycle_context")
    rows = [row for row in rows if row]
    if not rows:
        return []
    ready = [row for row in rows if row.get("status") == "ready"]
    return [_coverage_signal(
        "v30.training_signal.luck_cycle_alignment",
        "time_context",
        "luck_cycle_coverage",
        result,
        rows,
        {"ready_count": len(ready), "current_luck_pillars": sorted({str(row.get("current_luck_pillar")) for row in ready if row.get("current_luck_pillar")})},
    )]


def _flow_timing_activation_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    rows = [row for row in _observed_dicts(result, "flow_context") if row]
    if not rows:
        return []
    ready = [row for row in rows if row.get("status") == "ready"]
    return [_coverage_signal(
        "v30.training_signal.flow_timing_activation",
        "time_context",
        "flow_context_coverage",
        result,
        rows,
        {"ready_count": len(ready), "flow_year_pillars": sorted({str(row.get("flow_year_pillar")) for row in ready if row.get("flow_year_pillar")})},
    )]


def _six_pillar_context_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    rows = [row for row in _observed_dicts(result, "six_pillar_context") if row]
    if not rows:
        return []
    ready = [row for row in rows if row.get("status") == "ready"]
    pillar_counts = [len(row.get("pillars", [])) for row in ready if isinstance(row.get("pillars"), list)]
    return [_coverage_signal(
        "v30.training_signal.six_pillar_context_coverage",
        "six_pillar_context",
        "six_pillar_coverage",
        result,
        rows,
        {"ready_count": len(ready), "average_pillar_count": round(sum(pillar_counts) / max(1, len(pillar_counts)), 3)},
    )]


def _ranked_decision_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    rows = [row for row in _observed_dicts(result, "ranked_decisions") if row]
    if not rows:
        return []
    domains = sorted({domain for row in rows for domain in row if domain})
    return [_coverage_signal(
        "v30.training_signal.strength_structure_decision",
        "ranked_decision",
        "ranked_decision_coverage",
        result,
        rows,
        {"decision_domains": domains, "decision_domain_count": len(domains)},
    )]


def _ten_god_energy_fusion_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    rows = [row for row in _observed_dicts(result, "model_signal_summary") if row]
    if not rows:
        return []
    ready_count = sum(1 for row in rows if row.get("status") == "ready")
    raw_hidden_count = sum(1 for row in rows if row.get("raw_score_visible") is False)
    ranked_domains = sorted({
        str(domain)
        for row in rows
        for domain in (
            row.get("ranked_decision_inputs", {})
            if isinstance(row.get("ranked_decision_inputs"), dict) else {}
        )
    })
    volatility_count = sum(
        len(row.get("volatility_alerts", []))
        for row in rows
        if isinstance(row.get("volatility_alerts"), list)
    )
    stability_count = sum(
        len(row.get("stability_alerts", []))
        for row in rows
        if isinstance(row.get("stability_alerts"), list)
    )
    family_counts: dict[str, int] = {}
    energy_band_counts: dict[str, int] = {}
    stability_band_counts: dict[str, int] = {}
    volatility_band_counts: dict[str, int] = {}
    calibration_flag_counts: dict[str, int] = {}
    ranked_adjustment_count = 0
    for row in rows:
        profile = row.get("calibration_profile", {})
        profile = profile if isinstance(profile, dict) else {}
        for flag in profile.get("calibration_flags", []) if isinstance(profile.get("calibration_flags", []), list) else []:
            flag = str(flag)
            if flag:
                calibration_flag_counts[flag] = calibration_flag_counts.get(flag, 0) + 1
        adjustments = profile.get("ranked_decision_adjustments", {})
        if isinstance(adjustments, dict) and adjustments.get("version") == "v30.model_signal_ranked_decision_adjustments.v1":
            ranked_adjustment_count += 1
        bands = row.get("energy_bands", [])
        if not isinstance(bands, list):
            continue
        for band in bands:
            if not isinstance(band, dict):
                continue
            family = str(band.get("family") or "")
            if family:
                family_counts[family] = family_counts.get(family, 0) + 1
            for target, key in (
                (energy_band_counts, "energy_band"),
                (stability_band_counts, "stability_band"),
                (volatility_band_counts, "volatility_band"),
            ):
                value = str(band.get(key) or "")
                if value:
                    target[value] = target.get(value, 0) + 1
    calibration_rows = [
        row.observed.get("ten_god_energy_calibration", {})
        for row in result.results
        if isinstance(row.observed.get("ten_god_energy_calibration", {}), dict)
        and row.observed.get("ten_god_energy_calibration", {})
    ]
    replay_rows = [
        row.observed.get("m4_ten_god_real_case_replay", {})
        for row in result.results
        if isinstance(row.observed.get("m4_ten_god_real_case_replay", {}), dict)
        and row.observed.get("m4_ten_god_real_case_replay", {})
    ]
    calibration_family_coverage = sorted({
        str(family)
        for row in calibration_rows
        for family in (row.get("families", []) if isinstance(row.get("families"), list) else [])
        if family
    })
    replay_family_coverage = sorted({
        str(family)
        for row in replay_rows
        for family in (row.get("family_coverage", []) if isinstance(row.get("family_coverage"), list) else [])
        if family
    })
    replay_interface_ready_count = sum(
        1 for row in replay_rows
        if row.get("status") == "ready"
        and row.get("raw_score_visible") is False
        and not row.get("forbidden_field_leaks")
        and int(row.get("ranked_decision_domain_count", 0) or 0) >= 3
    )
    strength = round(min(
        1.0,
        ready_count / max(1, len(rows)) * 0.3
        + raw_hidden_count / max(1, len(rows)) * 0.25
        + len(ranked_domains) / 3 * 0.25
        + replay_interface_ready_count / max(1, len(replay_rows) or 1) * 0.2,
    ), 3)
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.ten_god_energy_fusion",
            domain="model_signal",
            signal_type="ten_god_energy_fusion_coverage",
            strength=strength,
            source_case_ids=[
                row.case_id for row in result.results
                if isinstance(row.observed.get("model_signal_summary"), dict)
                and row.observed.get("model_signal_summary")
            ],
            payload={
                "observed_count": len(rows),
                "ready_count": ready_count,
                "raw_score_hidden_count": raw_hidden_count,
                "ranked_decision_domains": ranked_domains,
                "volatility_alert_count": volatility_count,
                "stability_alert_count": stability_count,
                "family_counts": family_counts,
                "energy_band_counts": energy_band_counts,
                "stability_band_counts": stability_band_counts,
                "volatility_band_counts": volatility_band_counts,
                "calibration_flag_counts": calibration_flag_counts,
                "ranked_adjustment_count": ranked_adjustment_count,
                "calibration_case_count": len(calibration_rows),
                "calibration_family_coverage": calibration_family_coverage,
                "real_case_replay_count": len(replay_rows),
                "real_case_replay_interface_ready_count": replay_interface_ready_count,
                "real_case_replay_family_coverage": replay_family_coverage,
                "boundary": "ten_god_energy_fusion_trains_model_weights_not_chart_facts",
            },
        )
    ]


def _ranked_decision_fusion_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    rows = [row for row in _observed_dicts(result, "ranked_decisions") if row]
    if not rows:
        return []
    fused_domains = sorted({
        str(domain)
        for row in rows
        for domain, payload in row.items()
        if isinstance(payload, dict) and isinstance(payload.get("model_signal_summary"), dict) and payload.get("model_signal_summary")
    })
    unresolved_model_reviews = sum(
        1
        for row in rows
        for payload in row.values()
        if isinstance(payload, dict)
        and "model_signal_volatility_review" in (
            payload.get("unresolved_requirements", [])
            if isinstance(payload.get("unresolved_requirements"), list) else []
        )
    )
    supporting_model_signal_count = sum(
        1
        for row in rows
        for payload in row.values()
        if isinstance(payload, dict)
        and any(
            str(item).endswith(":model-signal-summary")
            for item in (
                payload.get("supporting_evidence", [])
                if isinstance(payload.get("supporting_evidence"), list) else []
            )
        )
    )
    candidate_score_domain_count = sum(
        1
        for row in rows
        for payload in row.values()
        if isinstance(payload, dict)
        and isinstance(payload.get("candidate_scores"), dict)
        and payload.get("candidate_scores")
    )
    non_unique_candidate_count = sum(
        1
        for row in rows
        for payload in row.values()
        if isinstance(payload, dict)
        and isinstance(payload.get("scoring_basis"), dict)
        and payload.get("scoring_basis", {}).get("non_unique_candidate_signal")
    )
    if not fused_domains:
        return []
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.ranked_decision_fusion",
            domain="ranked_decision",
            signal_type="model_signal_ranked_decision_fusion",
            strength=round(min(1.0, len(fused_domains) / 3 * 0.75 + supporting_model_signal_count / max(1, len(rows) * 3) * 0.25), 3),
            source_case_ids=[
                row.case_id for row in result.results
                if isinstance(row.observed.get("ranked_decisions"), dict)
                and row.observed.get("ranked_decisions")
            ],
            payload={
                "fused_domains": fused_domains,
                "fused_domain_count": len(fused_domains),
                "supporting_model_signal_count": supporting_model_signal_count,
                "candidate_score_domain_count": candidate_score_domain_count,
                "non_unique_candidate_count": non_unique_candidate_count,
                "unresolved_model_signal_review_count": unresolved_model_reviews,
                "boundary": "ranked_decision_fusion_trains_candidate_scoring_not_fixed_verdicts",
            },
        )
    ]


def _practical_reading_quality_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    rows = [row for row in _observed_dicts(result, "practical_reading_context") if row]
    if not rows:
        return []
    domain_payloads = [
        payload
        for row in rows
        for payload in (
            row.get("domain_readings", {}).values()
            if isinstance(row.get("domain_readings"), dict) else []
        )
        if isinstance(payload, dict)
    ]
    domains = sorted({
        domain
        for row in rows
        for domain in (row.get("domain_readings", {}) if isinstance(row.get("domain_readings"), dict) else {})
    })
    readable_summary_count = sum(1 for payload in domain_payloads if str(payload.get("summary", "")))
    takeaway_count = sum(1 for payload in domain_payloads if str(payload.get("customer_takeaway", "")))
    action_prompt_count = sum(1 for payload in domain_payloads if str(payload.get("action_prompt", "")))
    quality_contract_count = sum(1 for payload in domain_payloads if isinstance(payload.get("quality_contract"), dict))
    calculation_basis_count = sum(1 for payload in domain_payloads if isinstance(payload.get("calculation_basis"), dict))
    ranked_link_count = sum(1 for payload in domain_payloads if isinstance(payload.get("ranked_decision_links"), dict))
    model_signal_context_count = sum(1 for payload in domain_payloads if isinstance(payload.get("model_signal_context"), dict))
    evidence_bound_count = sum(1 for payload in domain_payloads if payload.get("evidence_ids"))
    blocked_claim_count = sum(1 for payload in domain_payloads if payload.get("blocked_claims"))
    domain_insight_count = sum(
        len(payload.get("domain_insights", []))
        for payload in domain_payloads
        if isinstance(payload.get("domain_insights", []), list)
    )
    action_step_count = sum(
        len(payload.get("action_steps", []))
        for payload in domain_payloads
        if isinstance(payload.get("action_steps", []), list)
    )
    calibration_prompt_count = sum(
        len(payload.get("calibration_prompts", []))
        for payload in domain_payloads
        if isinstance(payload.get("calibration_prompts", []), list)
    )
    module_trace_count = sum(
        1 for payload in domain_payloads
        if isinstance(payload.get("module_trace"), dict)
        and payload.get("module_trace", {}).get("version") == "v30.m6_practical_module_trace.v1"
    )
    explanation_unit_count = sum(
        len(payload.get("explanation_units", []))
        for payload in domain_payloads
        if isinstance(payload.get("explanation_units", []), list)
    )
    priority_scores = [
        float(payload.get("priority_score", 0.0))
        for payload in domain_payloads
        if payload.get("priority_score") is not None
    ]
    state_counts = {
        state: sum(1 for payload in domain_payloads if str(payload.get("state", "")) == state)
        for state in sorted({str(payload.get("state", "")) for payload in domain_payloads if payload.get("state")})
    }
    return [_coverage_signal(
        "v30.training_signal.practical_reading_quality",
        "practical_reading",
        "reading_domain_coverage",
        result,
        rows,
        {
            "reading_domains": domains,
            "reading_domain_count": len(domains),
            "domain_payload_count": len(domain_payloads),
            "readable_summary_count": readable_summary_count,
            "customer_takeaway_count": takeaway_count,
            "action_prompt_count": action_prompt_count,
            "quality_contract_count": quality_contract_count,
            "calculation_basis_count": calculation_basis_count,
            "ranked_decision_link_count": ranked_link_count,
            "model_signal_context_count": model_signal_context_count,
            "evidence_bound_count": evidence_bound_count,
            "blocked_claim_count": blocked_claim_count,
            "domain_insight_count": domain_insight_count,
            "action_step_count": action_step_count,
            "calibration_prompt_count": calibration_prompt_count,
            "module_trace_count": module_trace_count,
            "explanation_unit_count": explanation_unit_count,
            "state_counts": state_counts,
            "average_priority_score": round(sum(priority_scores) / max(1, len(priority_scores)), 3),
            "boundary": "practical_reading_quality_trains_expression_and_domain_priority_not_chart_facts",
        },
    )]


def _agent_question_flow_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    rows = [row for row in _observed_dicts(result, "agent_question_flow") if row]
    if not rows:
        return []
    stages = sorted({
        str(stage.get("stage"))
        for row in rows
        for stage in (row.get("stages", []) if isinstance(row.get("stages"), list) else [])
        if isinstance(stage, dict) and stage.get("stage")
    })
    return [_coverage_signal(
        "v30.training_signal.agent_question_flow_quality",
        "question_intelligence",
        "agent_flow_coverage",
        result,
        rows,
        {"stage_count": len(stages), "stages": stages},
    )]


def _high_value_question_quality_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    rows = [row for row in _observed_dicts(result, "high_value_question_quality") if row]
    if not rows:
        return []
    question_count = sum(int(row.get("question_count", 0)) for row in rows)
    contract_count = sum(int(row.get("questions_with_quality_contract", 0)) for row in rows)
    gains = [
        float(row.get("average_expected_information_gain", 0.0))
        for row in rows
        if row.get("average_expected_information_gain") is not None
    ]
    primary_gains = sorted({
        str(gain)
        for row in rows
        for gain in (row.get("primary_gains", []) if isinstance(row.get("primary_gains"), list) else [])
        if str(gain)
    })
    average_gain = round(sum(gains) / len(gains), 3) if gains else 0.0
    coverage = round(contract_count / question_count, 3) if question_count else 0.0
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.high_value_question_quality",
            domain="question_intelligence",
            signal_type="question_quality_policy_candidate_source",
            strength=round(min(1.0, (coverage + average_gain) / 2), 3),
            source_case_ids=[
                row.case_id for row in result.results
                if isinstance(row.observed.get("high_value_question_quality"), dict)
            ],
            payload={
                "question_count": question_count,
                "quality_contract_coverage": coverage,
                "average_expected_information_gain": average_gain,
                "primary_gains": primary_gains,
                "boundary": "high_value_question_quality_trains_question_strategy_not_chart_facts",
            },
        )
    ]


def _question_model_signal_personalization_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    rows = [row for row in _observed_dicts(result, "high_value_question_quality") if row]
    focused_rows = [
        row for row in rows
        if int(row.get("model_signal_focus_reason_count", 0) or 0) > 0
    ]
    if not focused_rows:
        return []
    focus_reason_count = sum(int(row.get("model_signal_focus_reason_count", 0) or 0) for row in focused_rows)
    focus_pairs = sorted({
        str(pair)
        for row in focused_rows
        for pair in (row.get("model_signal_focus_pairs", []) if isinstance(row.get("model_signal_focus_pairs"), list) else [])
        if str(pair)
    })
    focus_topics = sorted({
        str(topic)
        for row in focused_rows
        for topic in (row.get("model_signal_focus_topics", []) if isinstance(row.get("model_signal_focus_topics"), list) else [])
        if str(topic)
    })
    top_focused_count = sum(1 for row in focused_rows if row.get("top_question_model_signal_focused") is True)
    coverage = round(len(focused_rows) / max(1, len(rows)), 3)
    top_coverage = round(top_focused_count / max(1, len(focused_rows)), 3)
    strength = round(min(1.0, coverage * 0.55 + top_coverage * 0.25 + min(1.0, len(focus_topics) / 4) * 0.2), 3)
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.question_model_signal_personalization",
            domain="question_intelligence",
            signal_type="model_signal_question_policy_candidate_source",
            strength=strength,
            source_case_ids=[
                row.case_id for row in result.results
                if isinstance(row.observed.get("high_value_question_quality"), dict)
                and int(row.observed["high_value_question_quality"].get("model_signal_focus_reason_count", 0) or 0) > 0
            ],
            payload={
                "observed_count": len(rows),
                "model_signal_focused_count": len(focused_rows),
                "model_signal_focus_reason_count": focus_reason_count,
                "model_signal_focus_pairs": focus_pairs,
                "model_signal_focus_topics": focus_topics,
                "top_question_model_signal_focused_count": top_focused_count,
                "coverage": coverage,
                "top_question_coverage": top_coverage,
                "can_tune_question_strategy": True,
                "can_tune_chart_facts": False,
                "chart_fact_mutation_allowed_count": 0,
                "boundary": "question_model_signal_personalization_trains_question_strategy_not_chart_facts",
            },
        )
    ]


def _real_case_feedback_alignment_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    rows = [
        row.observed.get("real_case_fixture", {})
        for row in result.results
        if isinstance(row.observed.get("real_case_fixture", {}), dict)
        and row.observed.get("real_case_fixture", {})
    ]
    if not rows:
        return []
    ready_count = sum(1 for row in rows if row.get("status") == "ready")
    blocked_count = sum(1 for row in rows if row.get("status") in {"pending", "unsupported", "blocked"})
    no_fake_fact_count = sum(1 for row in rows if row.get("status") != "ready" and not row.get("has_pillars"))
    six_ready_count = sum(1 for row in rows if row.get("six_pillar_status") == "ready")
    practical_ready_count = sum(1 for row in rows if row.get("practical_reading_status") in {"ready", "natal_only"})
    agent_flow_count = sum(1 for row in rows if row.get("agent_question_stage"))
    projection_count = sum(1 for row in rows if row.get("projection_matrix_ready"))
    coverage = (
        ready_count / max(1, len(rows)) * 0.25
        + no_fake_fact_count / max(1, blocked_count or 1) * 0.2
        + six_ready_count / max(1, ready_count or 1) * 0.2
        + practical_ready_count / max(1, ready_count or 1) * 0.2
        + projection_count / max(1, len(rows)) * 0.15
    )
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.real_case_feedback_alignment",
            domain="real_case_validation",
            signal_type="canonical_real_case_coverage",
            strength=round(min(1.0, coverage), 3),
            source_case_ids=[str(row.get("case_id")) for row in rows if row.get("case_id")],
            payload={
                "case_count": len(rows),
                "ready_count": ready_count,
                "blocked_count": blocked_count,
                "no_fake_fact_count": no_fake_fact_count,
                "six_ready_count": six_ready_count,
                "practical_ready_count": practical_ready_count,
                "agent_flow_count": agent_flow_count,
                "projection_matrix_count": projection_count,
                "boundaries": sorted({str(row.get("boundary")) for row in rows if row.get("boundary")}),
                "boundary": "real_case_feedback_alignment_trains_quality_policy_not_chart_facts",
            },
        )
    ]


def _real_case_calibration_pack_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    rows = [
        row.observed.get("real_case_fixture", {})
        for row in result.results
        if isinstance(row.observed.get("real_case_fixture", {}), dict)
        and row.observed.get("real_case_fixture", {})
    ]
    if not rows:
        return []
    metadata_rows = [
        row.observed.get("production_replay_metadata", {})
        for row in result.results
        if isinstance(row.observed.get("production_replay_metadata", {}), dict)
        and row.observed.get("production_replay_metadata", {})
    ]
    metadata_summary = summarize_production_replay_metadata(metadata_rows)
    calendar_types = sorted({str(row.get("calendar_type")) for row in rows if row.get("calendar_type")})
    boundary_flags = sorted({
        str(flag)
        for row in rows
        for flag in (row.get("boundary_flags", []) if isinstance(row.get("boundary_flags"), list) else [])
    })
    ready_rows = [row for row in rows if row.get("status") == "ready"]
    pending_or_blocked_rows = [
        row for row in rows if row.get("status") in {"pending", "unsupported", "blocked"}
    ]
    categories = {
        "solar": any(row.get("calendar_type") == "solar" for row in rows),
        "lunar": any(row.get("calendar_type") == "lunar" and not row.get("lunar_is_leap_month") for row in rows),
        "leap_month_lunar": any(row.get("lunar_is_leap_month") for row in rows),
        "true_solar": any(row.get("use_true_solar_time") for row in rows),
        "unknown_hour": any(row.get("unknown_hour") for row in rows),
        "unknown_gender": any(row.get("gender_status") == "unknown" for row in rows),
    }
    no_fake_fact_count = sum(1 for row in pending_or_blocked_rows if not row.get("has_pillars"))
    model_signal_ready_count = sum(1 for row in ready_rows if row.get("model_signal_ready"))
    ranked_ready_count = sum(1 for row in ready_rows if int(row.get("ranked_decision_count", 0) or 0) >= 3)
    ranked_score_floor_ready_count = sum(
        1 for row in ready_rows
        if any(
            float(scores.get("follow_structure_boundary_review", 0.0) or 0.0) >= 0.55
            or float(scores.get("disputed_structure_review", 0.0) or 0.0) >= 0.52
            or float(scores.get("regulation_climate_boundary_review", 0.0) or 0.0) >= 0.45
            for scores in (
                row.get("ranked_candidate_scores", {}).values()
                if isinstance(row.get("ranked_candidate_scores"), dict) else []
            )
            if isinstance(scores, dict)
        )
    )
    ranked_basis_signal_counts = {
        "follow_structure_boundary": sum(
            1 for row in ready_rows
            if any(
                isinstance(signals, dict) and signals.get("follow_structure_boundary_signal")
                for signals in (
                    row.get("ranked_scoring_basis_signals", {}).values()
                    if isinstance(row.get("ranked_scoring_basis_signals"), dict) else []
                )
            )
        ),
        "disputed_structure": sum(
            1 for row in ready_rows
            if any(
                isinstance(signals, dict) and signals.get("disputed_structure_signal")
                for signals in (
                    row.get("ranked_scoring_basis_signals", {}).values()
                    if isinstance(row.get("ranked_scoring_basis_signals"), dict) else []
                )
            )
        ),
        "non_unique_candidate": sum(
            1 for row in ready_rows
            if any(
                isinstance(signals, dict) and signals.get("non_unique_candidate_signal")
                for signals in (
                    row.get("ranked_scoring_basis_signals", {}).values()
                    if isinstance(row.get("ranked_scoring_basis_signals"), dict) else []
                )
            )
        ),
    }
    six_ready_count = sum(1 for row in ready_rows if row.get("six_pillar_status") == "ready")
    practical_ready_count = sum(
        1 for row in rows if row.get("practical_reading_status") in {"ready", "natal_only"}
    )
    practical_contract_rows = [
        contract
        for row in rows
        for contract in (
            row.get("practical_domain_contracts", {}).values()
            if isinstance(row.get("practical_domain_contracts", {}), dict) else []
        )
        if isinstance(contract, dict)
    ]
    drift_summaries = [
        row.get("calibration_drift_summary", {})
        for row in rows
        if isinstance(row.get("calibration_drift_summary", {}), dict)
        and row.get("calibration_drift_summary", {})
    ]
    drift_flag_counts: dict[str, int] = {}
    module_adjustment_counts: dict[str, int] = {}
    module_readiness_counts: dict[str, int] = {}
    for summary in drift_summaries:
        for flag in summary.get("drift_flags", []) if isinstance(summary.get("drift_flags", []), list) else []:
            flag = str(flag)
            if flag:
                drift_flag_counts[flag] = drift_flag_counts.get(flag, 0) + 1
        for module_id in (
            summary.get("module_adjustment_targets", [])
            if isinstance(summary.get("module_adjustment_targets", []), list) else []
        ):
            module_id = str(module_id)
            if module_id:
                module_adjustment_counts[module_id] = module_adjustment_counts.get(module_id, 0) + 1
        readiness = summary.get("module_readiness", {})
        if isinstance(readiness, dict):
            for module_id, is_ready in readiness.items():
                if is_ready:
                    module_id = str(module_id)
                    module_readiness_counts[module_id] = module_readiness_counts.get(module_id, 0) + 1
    m6_contract_ready_count = sum(
        1 for row in ready_rows
        if int(row.get("practical_domain_count", 0) or 0) >= 5
        and all(
            isinstance(contract, dict)
            and contract.get("version") == "v30.practical_domain_reading.v2"
            and contract.get("calculation_basis_version") == "v30.practical_domain_calculation_basis.v1"
            and contract.get("model_signal_context_version") == "v30.practical_model_signal_context.v1"
            and int(contract.get("ranked_decision_link_count", 0) or 0) >= 3
            and int(contract.get("evidence_id_count", 0) or 0) >= 1
            and int(contract.get("explanation_unit_count", 0) or 0) >= 3
            and int(contract.get("blocked_claim_count", 0) or 0) >= 1
            and not bool(contract.get("raw_score_leak"))
            for contract in (
                row.get("practical_domain_contracts", {}).values()
                if isinstance(row.get("practical_domain_contracts", {}), dict) else []
            )
        )
    )
    category_score = sum(1 for active in categories.values() if active) / max(1, len(categories))
    runtime_score = (
        model_signal_ready_count / max(1, len(ready_rows)) * 0.25
        + ranked_ready_count / max(1, len(ready_rows)) * 0.25
        + six_ready_count / max(1, len(ready_rows)) * 0.2
        + practical_ready_count / max(1, len(rows)) * 0.15
        + no_fake_fact_count / max(1, len(pending_or_blocked_rows) or 1) * 0.15
    )
    strength = round(min(1.0, category_score * 0.45 + runtime_score * 0.55), 3)
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.real_case_calibration_pack",
            domain="real_case_validation",
            signal_type="canonical_fixture_calibration_coverage",
            strength=strength,
            source_case_ids=[str(row.get("case_id")) for row in rows if row.get("case_id")],
            payload={
                "case_count": len(rows),
                "categories": categories,
                "calendar_types": calendar_types,
                "boundary_flags": boundary_flags,
                "ready_count": len(ready_rows),
                "pending_or_blocked_count": len(pending_or_blocked_rows),
                "no_fake_fact_count": no_fake_fact_count,
                "model_signal_ready_count": model_signal_ready_count,
                "ranked_decision_ready_count": ranked_ready_count,
                "ranked_score_floor_ready_count": ranked_score_floor_ready_count,
                "ranked_basis_signal_counts": ranked_basis_signal_counts,
                "six_pillar_ready_count": six_ready_count,
                "practical_ready_or_natal_only_count": practical_ready_count,
                "m6_practical_contract_ready_count": m6_contract_ready_count,
                "m6_practical_domain_contract_count": len(practical_contract_rows),
                "m6_practical_raw_score_leak_count": sum(1 for row in practical_contract_rows if row.get("raw_score_leak")),
                "m7_calibration_drift_summary_version": "v30.real_case_calibration_drift_summary.v1",
                "m7_calibration_drift_summary_count": len(drift_summaries),
                "m7_calibration_stable_count": sum(
                    1 for row in drift_summaries if row.get("calibration_status") == "stable"
                ),
                "m7_calibration_needs_module_review_count": sum(
                    1 for row in drift_summaries if row.get("calibration_status") == "needs_module_review"
                ),
                "m7_drift_flag_counts": drift_flag_counts,
                "m7_module_adjustment_counts": module_adjustment_counts,
                "m7_module_readiness_counts": module_readiness_counts,
                "production_replay_metadata": metadata_summary,
                "production_replay_metadata_version": metadata_summary["version"],
                "production_replay_metadata_count": metadata_summary["row_count"],
                "production_replay_metadata_privacy_guard_pass_count": metadata_summary["privacy_guard_pass_count"],
                "production_replay_metadata_ready_count": metadata_summary["ready_count"],
                "production_replay_metadata_pending_count": metadata_summary["pending_count"],
                "production_replay_metadata_blocked_count": metadata_summary["blocked_count"],
                "production_replay_metadata_calendar_types": metadata_summary["calendar_types"],
                "production_replay_metadata_true_solar_count": metadata_summary["true_solar_count"],
                "production_replay_metadata_unknown_hour_count": metadata_summary["unknown_hour_count"],
                "production_replay_metadata_unknown_gender_count": metadata_summary["unknown_gender_count"],
                "production_replay_metadata_projection_leak_pass_count": metadata_summary["projection_leak_scan_pass_count"],
                "production_replay_metadata_boundary": metadata_summary["boundary"],
                "boundary": "real_case_calibration_pack_trains_validation_policy_not_chart_facts",
            },
        )
    ]


def _m5_weight_replay_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    rows = [row for row in _observed_dicts(result, "ranked_decisions") if row]
    if not rows:
        return []
    primary_counts: dict[str, dict[str, int]] = {}
    score_totals: dict[str, dict[str, float]] = {}
    score_counts: dict[str, dict[str, int]] = {}
    basis_signal_counts = {
        "follow_structure_boundary": 0,
        "special_structure_boundary": 0,
        "regulation_climate_boundary": 0,
        "disputed_structure": 0,
        "non_unique_candidate": 0,
    }
    useful_god_rows: list[dict[str, object]] = []
    for row in rows:
        for domain, payload in row.items():
            if not isinstance(payload, dict):
                continue
            primary = str(payload.get("primary_candidate") or "")
            if primary:
                primary_counts.setdefault(str(domain), {})[primary] = primary_counts.setdefault(str(domain), {}).get(primary, 0) + 1
            scores = payload.get("candidate_scores", {})
            if isinstance(scores, dict):
                for candidate_id, score in scores.items():
                    if not isinstance(score, (int, float)):
                        continue
                    score_totals.setdefault(str(domain), {})[str(candidate_id)] = (
                        score_totals.setdefault(str(domain), {}).get(str(candidate_id), 0.0) + float(score)
                    )
                    score_counts.setdefault(str(domain), {})[str(candidate_id)] = (
                        score_counts.setdefault(str(domain), {}).get(str(candidate_id), 0) + 1
                    )
            basis = payload.get("scoring_basis", {})
            if isinstance(basis, dict):
                if basis.get("follow_structure_boundary_signal"):
                    basis_signal_counts["follow_structure_boundary"] += 1
                if basis.get("special_structure_boundary_signal"):
                    basis_signal_counts["special_structure_boundary"] += 1
                if basis.get("regulation_climate_boundary_signal"):
                    basis_signal_counts["regulation_climate_boundary"] += 1
                if basis.get("disputed_structure_signal"):
                    basis_signal_counts["disputed_structure"] += 1
                if basis.get("non_unique_candidate_signal"):
                    basis_signal_counts["non_unique_candidate"] += 1
            if domain == "useful_god":
                useful_god_rows.append(payload)
    average_scores = {
        domain: {
            candidate_id: round(total / max(1, score_counts.get(domain, {}).get(candidate_id, 0)), 3)
            for candidate_id, total in candidates.items()
        }
        for domain, candidates in score_totals.items()
    }
    useful_score_averages = average_scores.get("useful_god", {})
    useful_supporting_evidence_count = sum(
        len(row.get("supporting_evidence", []))
        for row in useful_god_rows
        if isinstance(row.get("supporting_evidence"), list)
    )
    useful_weakening_evidence_count = sum(
        len(row.get("weakening_evidence", []))
        for row in useful_god_rows
        if isinstance(row.get("weakening_evidence"), list)
    )
    useful_fixed_verdict_guard_count = sum(
        1
        for row in useful_god_rows
        if "fixed_useful_god_verdict" in (
            row.get("weakening_evidence", []) if isinstance(row.get("weakening_evidence"), list) else []
        )
    )
    useful_candidate_weights = {
        candidate_id: round(1.0 + min(0.045, float(score) * 0.045), 3)
        for candidate_id, score in useful_score_averages.items()
    }
    structure_scores = average_scores.get("structure_pattern", {})
    structure_candidate_weights = {
        "follow_structure_boundary_review": round(1.0 + min(0.045, structure_scores.get("follow_structure_boundary_review", 0.0) * 0.055), 3),
        "disputed_structure_review": round(1.0 + min(0.045, structure_scores.get("disputed_structure_review", 0.0) * 0.055), 3),
        "regulation_climate_boundary_review": round(1.0 + min(0.04, structure_scores.get("regulation_climate_boundary_review", 0.0) * 0.05), 3),
        "special_structure_boundary_review": round(1.0 + min(0.04, structure_scores.get("special_structure_boundary_review", 0.0) * 0.05), 3),
    }
    useful_evidence_coverage = round(
        min(
            1.0,
            useful_supporting_evidence_count / max(1, len(useful_god_rows) * 3) * 0.35
            + useful_fixed_verdict_guard_count / max(1, len(useful_god_rows)) * 0.25
            + len(useful_score_averages) / 5 * 0.25
            + basis_signal_counts["non_unique_candidate"] / max(1, len(rows) * 3) * 0.15,
        ),
        3,
    )
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.m5_weight_replay",
            domain="ranked_decision",
            signal_type="candidate_weight_replay_and_useful_god_evidence_calibration",
            strength=round(min(1.0, useful_evidence_coverage * 0.55 + len(average_scores) / 3 * 0.45), 3),
            source_case_ids=[
                row.case_id for row in result.results
                if isinstance(row.observed.get("ranked_decisions"), dict)
                and row.observed.get("ranked_decisions")
            ],
            payload={
                "primary_candidate_counts": primary_counts,
                "average_candidate_scores": average_scores,
                "basis_signal_counts": basis_signal_counts,
                "useful_god_candidate_weights": useful_candidate_weights,
                "structure_candidate_weights": structure_candidate_weights,
                "useful_god_evidence_coverage": useful_evidence_coverage,
                "useful_god_supporting_evidence_count": useful_supporting_evidence_count,
                "useful_god_weakening_evidence_count": useful_weakening_evidence_count,
                "useful_god_fixed_verdict_guard_count": useful_fixed_verdict_guard_count,
                "boundary": "m5_weight_replay_trains_candidate_weights_not_chart_facts",
            },
        )
    ]


def _observed_dicts(result: SyntheticValidationSuiteResult, key: str) -> list[dict[str, object]]:
    return [row.observed.get(key, {}) for row in result.results if isinstance(row.observed.get(key, {}), dict)]


def _coverage_signal(
    signal_id: str,
    domain: str,
    signal_type: str,
    result: SyntheticValidationSuiteResult,
    rows: list[dict[str, object]],
    payload: dict[str, object],
) -> SyntheticTrainingSignal:
    ready_count = sum(1 for row in rows if row.get("status") == "ready" or row.get("next_stage"))
    strength = round(min(1.0, len(rows) / max(1, result.case_count) * 0.5 + ready_count / max(1, len(rows)) * 0.5), 3)
    return SyntheticTrainingSignal(
        signal_id=signal_id,
        domain=domain,
        signal_type=signal_type,
        strength=strength,
        source_case_ids=[row.case_id for row in result.results if isinstance(row.observed.get(_signal_observed_key(signal_id), {}), dict) and row.observed.get(_signal_observed_key(signal_id), {})],
        payload={
            **payload,
            "observed_count": len(rows),
            "ready_count": ready_count,
            "boundary": f"{signal_id}_validates_runtime_context_not_chart_fact",
        },
    )


def _signal_observed_key(signal_id: str) -> str:
    return {
        "v30.training_signal.luck_cycle_alignment": "luck_cycle_context",
        "v30.training_signal.flow_timing_activation": "flow_context",
        "v30.training_signal.six_pillar_context_coverage": "six_pillar_context",
        "v30.training_signal.strength_structure_decision": "ranked_decisions",
        "v30.training_signal.practical_reading_quality": "practical_reading_context",
        "v30.training_signal.agent_question_flow_quality": "agent_question_flow",
    }.get(signal_id, "")


def _per_unit_parameter_tuning_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    unit_ids: set[str] = set()
    source_cases: list[str] = []
    failures: list[str] = []
    for row in result.results:
        observed_units = row.observed.get("krp_library_unit_ids", [])
        if isinstance(observed_units, list):
            unit_ids.update(str(unit_id) for unit_id in observed_units)
            if observed_units:
                source_cases.append(row.case_id)
        failures.extend(str(failure) for failure in row.failures)
    if not unit_ids:
        return []
    rule_weights = _rule_weights_from_units(unit_ids)
    domain_weights = _domain_weights_from_units(unit_ids)
    mechanism_weights = _mechanism_weights_from_units(unit_ids)
    failure_penalty = round(min(0.12, len(failures) / max(1, result.case_count) * 0.02), 3)
    strength = round(max(0.0, min(1.0, len(unit_ids) / 42 - failure_penalty)), 3)
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.per_unit_parameter_tuning",
            domain="policy_tuning",
            signal_type="per_unit_weight_map",
            strength=strength,
            source_case_ids=source_cases,
            payload={
                "unit_count": len(unit_ids),
                "unit_ids": sorted(unit_ids),
                "rule_weights": rule_weights,
                "domain_weights": domain_weights,
                "mechanism_weights": mechanism_weights,
                "failure_count": len(failures),
                "failure_types": sorted(set(failures)),
                "boundary": "per_unit_weights_tune_runtime_candidates_not_chart_facts",
            },
        )
    ]


def _rule_weights_from_units(unit_ids: set[str]) -> dict[str, float]:
    weights = {"*": 1.0}
    if any("time_context" in unit_id for unit_id in unit_ids):
        weights["v30.rule.time_context.blocks_timing_claim"] = 1.025
    if any("useful_god" in unit_id for unit_id in unit_ids):
        weights["v30.rule.useful_god.candidate_gate"] = 1.03
    if any("hidden_factor" in unit_id for unit_id in unit_ids):
        weights["v30.rule.hidden_factor.requires_dialogue"] = 1.035
    if any("branch_relation" in unit_id for unit_id in unit_ids):
        weights["v30.rule.branch_relation.requires_dynamic_review"] = 1.025
    return weights


def _domain_weights_from_units(unit_ids: set[str]) -> dict[str, float]:
    domains = {
        "time_context": "time_context",
        "useful_god": "useful_god",
        "hidden_factor": "hidden_factor",
        "branch_relation": "branch_relation",
        "structure": "structure_dynamic",
        "wealth": "wealth",
        "career": "career",
        "relationship": "relationship",
        "health": "health",
    }
    weights = {"*": 1.0}
    for needle, domain in domains.items():
        if any(needle in unit_id for unit_id in unit_ids):
            weights[domain] = 1.015
    return weights


def _mechanism_weights_from_units(unit_ids: set[str]) -> dict[str, float]:
    weights = {"*": 1.0}
    if any("ten_god" in unit_id for unit_id in unit_ids):
        weights["mechanism.ten_god_visibility_context"] = 1.035
    if any("useful_god" in unit_id for unit_id in unit_ids):
        weights["mechanism.useful_god_candidate_gate"] = 1.035
    if any("hidden_factor" in unit_id for unit_id in unit_ids):
        weights["mechanism.hidden_factor_dialogue_probe"] = 1.04
    if any("branch_relation" in unit_id for unit_id in unit_ids):
        weights["mechanism.branch_relation_dynamic_review"] = 1.035
    return weights


def _macro_dimension_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    domains: set[str] = set()
    source_cases: list[str] = []
    for row in result.results:
        observed_domains = row.observed.get("macro_dimension_signal_domains", [])
        if not isinstance(observed_domains, list):
            continue
        domains.update(str(domain) for domain in observed_domains)
        if observed_domains:
            source_cases.append(row.case_id)
    if not domains:
        return []
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.macro_dimension_coverage",
            domain="knowledge_macro",
            signal_type="coverage",
            strength=round(min(1.0, len(domains) / 7), 3),
            source_case_ids=source_cases,
            payload={"domain_count": len(domains), "domains": sorted(domains)},
        )
    ]


def _portrait_projection_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    domains: set[str] = set()
    source_cases: list[str] = []
    for row in result.results:
        observed_domains = row.observed.get("macro_portrait_domains", [])
        if not isinstance(observed_domains, list):
            continue
        domains.update(str(domain) for domain in observed_domains)
        if observed_domains:
            source_cases.append(row.case_id)
    if not domains:
        return []
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.portrait_projection_coverage",
            domain="portrait",
            signal_type="coverage",
            strength=round(min(1.0, len(domains) / 6), 3),
            source_case_ids=source_cases,
            payload={"domain_count": len(domains), "domains": sorted(domains)},
        )
    ]


def _portrait_projection_view_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    domains: set[str] = set()
    roles: set[str] = set()
    visibility: set[str] = set()
    source_cases: list[str] = []
    hidden_factor_admin_count = 0
    hidden_factor_guest_count = 0
    view_counts: list[float] = []
    for row in result.results:
        observed_domains = row.observed.get("macro_portrait_view_domains", [])
        summary = row.observed.get("macro_portrait_view_summary", {})
        contrast = row.observed.get("macro_portrait_role_contrast", {})
        if isinstance(observed_domains, list):
            domains.update(str(domain) for domain in observed_domains)
        if isinstance(summary, dict):
            roles.update(str(role) for role in summary.get("roles", []) if role)
            visibility.update(str(item) for item in summary.get("visibility", []) if item)
            view_counts.append(_float(summary.get("view_count")))
        if isinstance(contrast, dict):
            guest = contrast.get("guest", {})
            admin = contrast.get("admin", {})
            if isinstance(guest, dict):
                hidden_factor_guest_count += int(_float(guest.get("hidden_factor_view_count")))
                roles.update(str(role) for role in guest.get("roles", []) if role)
            if isinstance(admin, dict):
                hidden_factor_admin_count += int(_float(admin.get("hidden_factor_view_count")))
                roles.update(str(role) for role in admin.get("roles", []) if role)
        if observed_domains:
            source_cases.append(row.case_id)
    if not domains:
        return []
    average_views = sum(view_counts) / max(1, len(view_counts))
    role_contrast_score = 1.0 if hidden_factor_admin_count > 0 and hidden_factor_guest_count == 0 else 0.5
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.portrait_projection_view_coverage",
            domain="portrait",
            signal_type="role_view_coverage",
            strength=round(min(1.0, len(domains) / 7 * 0.45 + len(roles) / 3 * 0.35 + role_contrast_score * 0.2), 3),
            source_case_ids=source_cases,
            payload={
                "domain_count": len(domains),
                "domains": sorted(domains),
                "roles": sorted(roles),
                "visibility": sorted(visibility),
                "average_view_count": round(average_views, 3),
                "admin_hidden_factor_view_count": hidden_factor_admin_count,
                "guest_hidden_factor_view_count": hidden_factor_guest_count,
                "role_contrast_coverage": role_contrast_score,
            },
        )
    ]


def _role_locale_client_projection_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    roles: set[str] = set()
    locales: set[str] = set()
    clients: set[str] = set()
    sampled_roles: set[str] = set()
    sampled_locales: set[str] = set()
    sampled_clients: set[str] = set()
    diagnostic_roles: set[str] = set()
    compact_clients: set[str] = set()
    source_cases: list[str] = []
    combination_count = 0
    sampled_combination_count = 0
    for row in result.results:
        matrix = row.observed.get("role_locale_client_projection_matrix", {})
        if not isinstance(matrix, dict) or not matrix:
            continue
        roles.update(str(item) for item in matrix.get("roles", []) if item)
        locales.update(str(item) for item in matrix.get("locales", []) if item)
        clients.update(str(item) for item in matrix.get("clients", []) if item)
        sampled_roles.update(str(item) for item in matrix.get("sampled_roles", []) if item)
        sampled_locales.update(str(item) for item in matrix.get("sampled_locales", []) if item)
        sampled_clients.update(str(item) for item in matrix.get("sampled_clients", []) if item)
        diagnostic_roles.update(str(item) for item in matrix.get("diagnostic_roles", []) if item)
        compact_clients.update(str(item) for item in matrix.get("compact_clients", []) if item)
        combination_count = max(combination_count, int(_float(matrix.get("combination_count"))))
        sampled_combination_count = max(sampled_combination_count, int(_float(matrix.get("sampled_combination_count"))))
        source_cases.append(row.case_id)
    if not roles or not locales or not clients:
        return []
    role_coverage = len(sampled_roles) / max(1, len(roles))
    locale_coverage = len(sampled_locales) / max(1, len(locales))
    client_coverage = len(sampled_clients) / max(1, len(clients))
    diagnostics_score = 1.0 if {"analyst", "admin", "lab"} & diagnostic_roles else 0.5
    compact_score = 1.0 if "mobile" in compact_clients else 0.5
    strength = round(min(1.0, role_coverage * 0.3 + locale_coverage * 0.25 + client_coverage * 0.25 + diagnostics_score * 0.1 + compact_score * 0.1), 3)
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.role_locale_client_projection_coverage",
            domain="presentation",
            signal_type="role_locale_client_projection_coverage",
            strength=strength,
            source_case_ids=source_cases,
            payload={
                "roles": sorted(roles),
                "locales": sorted(locales),
                "clients": sorted(clients),
                "sampled_roles": sorted(sampled_roles),
                "sampled_locales": sorted(sampled_locales),
                "sampled_clients": sorted(sampled_clients),
                "diagnostic_roles": sorted(diagnostic_roles),
                "compact_clients": sorted(compact_clients),
                "combination_count": combination_count,
                "sampled_combination_count": sampled_combination_count,
                "boundary": "role_locale_client_projection_trains_presentation_policy_not_chart_facts",
            },
        )
    ]


def _api_projection_contract_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    rows = [
        {
            "user": row.observed.get("api_projection_contract", {}),
            "admin": row.observed.get("admin_api_projection_contract", {}),
        }
        for row in result.results
        if isinstance(row.observed.get("api_projection_contract"), dict)
        and row.observed.get("api_projection_contract")
    ]
    if not rows:
        return []
    user_contract_ready = sum(
        1 for row in rows
        if row["user"].get("version") == "v30.api_projection_contract.v1"
    )
    user_leak_pass_count = sum(
        1 for row in rows
        if isinstance(row["user"].get("leak_scan"), dict)
        and row["user"]["leak_scan"].get("passed") is True
        and row["user"]["leak_scan"].get("diagnostics_hidden") is True
    )
    admin_diagnostic_ready = sum(
        1 for row in rows
        if isinstance(row["admin"], dict)
        and row["admin"].get("diagnostics_visible") is True
    )
    core_first_count = sum(
        1 for row in rows
        if row["user"].get("customer_surface_order", [])[:2] == ["core_bazi_reading", "domain_cards"]
    )
    core_first_policy_count = sum(
        1 for row in rows
        if isinstance(row["user"].get("core_first_projection"), dict)
        and row["user"]["core_first_projection"].get("calculation_before_questions") is True
        and row["user"]["core_first_projection"].get("required_surface_prefix", []) == ["core_bazi_reading", "domain_cards"]
    )
    customer_surface_contract_ready_count = sum(
        1 for row in rows
        if isinstance(row["user"].get("customer_surface_contract"), dict)
        and row["user"]["customer_surface_contract"].get("surface_prefix_ready") is True
    )
    required_additive_fields = {
        "reading_surface",
        "core_bazi_reading",
        "domain_cards",
        "questions",
        "answer_panel",
        "next_question_id",
        "visible_next_question_id",
        "internal_next_question_id",
        "actor_context",
        "llm_runtime_status",
        "diagnostics",
        "projection_contract",
    }
    additive_policy_count = sum(
        1 for row in rows
        if isinstance(row["user"].get("additive_api_policy"), dict)
        and required_additive_fields <= set(row["user"]["additive_api_policy"].get("must_preserve", []))
    )
    forbidden_field_policy_count = sum(
        1 for row in rows
        if isinstance(row["user"].get("customer_forbidden_fields"), dict)
        and {"raw_score", "raw_weight", "training_signal", "policy_effect", "internal_next_question_id"} <= set(
            row["user"]["customer_forbidden_fields"].get("fields", [])
        )
    )
    strength = round(min(
        1.0,
        user_contract_ready / max(1, len(rows)) * 0.15
        + user_leak_pass_count / max(1, len(rows)) * 0.2
        + admin_diagnostic_ready / max(1, len(rows)) * 0.15
        + core_first_count / max(1, len(rows)) * 0.1
        + core_first_policy_count / max(1, len(rows)) * 0.15
        + customer_surface_contract_ready_count / max(1, len(rows)) * 0.1
        + additive_policy_count / max(1, len(rows)) * 0.1
        + forbidden_field_policy_count / max(1, len(rows)) * 0.05,
    ), 3)
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.api_projection_contract",
            domain="presentation",
            signal_type="api_projection_contract_coverage",
            strength=strength,
            source_case_ids=[
                row.case_id for row in result.results
                if isinstance(row.observed.get("api_projection_contract"), dict)
                and row.observed.get("api_projection_contract")
            ],
            payload={
                "contract_observation_count": len(rows),
                "user_contract_ready_count": user_contract_ready,
                "user_leak_pass_count": user_leak_pass_count,
                "admin_diagnostic_ready_count": admin_diagnostic_ready,
                "core_first_count": core_first_count,
                "core_first_policy_count": core_first_policy_count,
                "customer_surface_contract_ready_count": customer_surface_contract_ready_count,
                "additive_policy_count": additive_policy_count,
                "forbidden_field_policy_count": forbidden_field_policy_count,
                "required_additive_fields": sorted(required_additive_fields),
                "boundary": "api_projection_contract_trains_visibility_policy_not_chart_facts",
            },
        )
    ]


def _question_graph_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    edge_counts: list[int] = []
    source_cases: list[str] = []
    for row in result.results:
        graph = row.observed.get("question_dialogue_graph", {})
        if not isinstance(graph, dict):
            continue
        edges = graph.get("edges", [])
        if not isinstance(edges, list):
            continue
        edge_counts.append(len(edges))
        if edges:
            source_cases.append(row.case_id)
    if not edge_counts:
        return []
    average_edges = sum(edge_counts) / len(edge_counts)
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.question_graph_edge_coverage",
            domain="question_intelligence",
            signal_type="coverage",
            strength=round(min(1.0, average_edges / 3), 3),
            source_case_ids=source_cases,
            payload={"average_edge_count": round(average_edges, 3), "max_edge_count": max(edge_counts)},
        )
    ]


def _question_dialogue_outcome_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    outcomes: list[dict[str, object]] = []
    source_cases: list[str] = []
    for row in result.results:
        observed = row.observed.get("question_outcomes", [])
        if not isinstance(observed, list) or not observed:
            continue
        rows = [item for item in observed if isinstance(item, dict)]
        outcomes.extend(rows)
        if rows:
            source_cases.append(row.case_id)
    if not outcomes:
        return []
    topics = sorted({str(row.get("topic")) for row in outcomes if row.get("topic")})
    statuses = sorted({str(row.get("outcome_status")) for row in outcomes if row.get("outcome_status")})
    confidences = [_float(row.get("confidence")) for row in outcomes]
    followup_topics = {
        str(row.get("topic"))
        for row in outcomes
        if row.get("topic") and str(row.get("outcome_status") or "answered") in {"answered", "confirmed"}
    }
    average_confidence = sum(confidences) / len(confidences)
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.question_dialogue_outcome",
            domain="question_intelligence",
            signal_type="outcome_feedback",
            strength=round(min(1.0, len(outcomes) / 4 * 0.4 + len(topics) / 4 * 0.3 + average_confidence * 0.3), 3),
            source_case_ids=source_cases,
            payload={
                "outcome_count": len(outcomes),
                "answered_topic_count": len(topics),
                "topics": topics,
                "statuses": statuses,
                "average_confidence": round(average_confidence, 3),
                "followup_topic_coverage": round(len(followup_topics) / max(1, len(topics)), 3),
            },
        )
    ]


def _interaction_state_machine_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    rows = [row for row in _observed_dicts(result, "interaction_state") if row]
    if not rows:
        return []
    stages = sorted({str(row.get("interaction_stage")) for row in rows if row.get("interaction_stage")})
    selected_domains = sorted({str(row.get("selected_domain")) for row in rows if row.get("selected_domain")})
    visible_count = sum(1 for row in rows if row.get("visible_next_question_id"))
    internal_count = sum(1 for row in rows if row.get("internal_next_question_id"))
    split_count = sum(
        1
        for row in rows
        if row.get("visible_next_question_id")
        and row.get("internal_next_question_id")
        and row.get("visible_next_question_id") != row.get("internal_next_question_id")
    )
    answered_count = sum(
        len(row.get("answered_question_ids", []))
        for row in rows
        if isinstance(row.get("answered_question_ids"), list)
    )
    strength = round(min(1.0, len(stages) / 2 * 0.3 + visible_count / max(1, len(rows)) * 0.25 + internal_count / max(1, len(rows)) * 0.25 + (0.2 if split_count else 0.0)), 3)
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.interaction_state_machine",
            domain="question_intelligence",
            signal_type="interaction_state_coverage",
            strength=strength,
            source_case_ids=[
                row.case_id for row in result.results
                if isinstance(row.observed.get("interaction_state"), dict)
                and row.observed.get("interaction_state")
            ],
            payload={
                "observed_count": len(rows),
                "stages": stages,
                "selected_domains": selected_domains,
                "visible_next_question_count": visible_count,
                "internal_next_question_count": internal_count,
                "visible_internal_split_count": split_count,
                "answered_question_count": answered_count,
                "boundary": "interaction_state_machine_trains_followup_policy_not_chart_facts",
            },
        )
    ]


def _interaction_loop_quality_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    rows = [
        {
            "state": row.observed.get("interaction_state", {}),
            "surface": row.observed.get("customer_reading_surface", {}),
        }
        for row in result.results
        if isinstance(row.observed.get("interaction_state"), dict)
        and isinstance(row.observed.get("customer_reading_surface"), dict)
    ]
    if not rows:
        return []
    visible_surface_count = sum(
        1
        for row in rows
        if row["surface"].get("visible_next_question_id")
        or row["surface"].get("next_question_id")
    )
    internal_leak_count = sum(
        1
        for row in rows
        if "internal_next_question_id" in row["surface"]
    )
    selected_domain_surface_count = sum(
        1
        for row in rows
        if row["state"].get("selected_domain")
        and row["surface"].get("selected_domain") == row["state"].get("selected_domain")
    )
    strength = round(min(1.0, visible_surface_count / max(1, len(rows)) * 0.6 + (1.0 if internal_leak_count == 0 else 0.0) * 0.25 + selected_domain_surface_count / max(1, len(rows)) * 0.15), 3)
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.interaction_loop_quality",
            domain="question_intelligence",
            signal_type="visible_followup_projection_quality",
            strength=strength,
            source_case_ids=[
                row.case_id for row in result.results
                if isinstance(row.observed.get("interaction_state"), dict)
            ],
            payload={
                "observed_count": len(rows),
                "visible_surface_next_question_count": visible_surface_count,
                "internal_next_question_surface_leak_count": internal_leak_count,
                "selected_domain_surface_count": selected_domain_surface_count,
                "boundary": "interaction_loop_quality_trains_presentation_and_question_strategy_not_chart_facts",
            },
        )
    ]


def _interaction_brain_structured_constraint_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    rows: list[dict[str, object]] = []
    source_cases: list[str] = []
    for case in result.results:
        brain = case.observed.get("interaction_brain_result", {})
        outcomes = case.observed.get("question_outcomes", [])
        state = case.observed.get("interaction_state", {})
        if not isinstance(brain, dict) or not brain:
            continue
        latest_outcome = (
            outcomes[-1]
            if isinstance(outcomes, list) and outcomes and isinstance(outcomes[-1], dict)
            else {}
        )
        rows.append(
            {
                "brain": brain,
                "outcome": latest_outcome,
                "state": state if isinstance(state, dict) else {},
            }
        )
        source_cases.append(case.case_id)
    if not rows:
        return []
    accepted_count = sum(1 for row in rows if row["outcome"].get("constraint_valid") is True)
    rejected_count = sum(1 for row in rows if row["outcome"].get("constraint_valid") is False)
    hidden_allowed_count = sum(1 for row in rows if row["brain"].get("allowed_to_update_hidden_factor") is True)
    retry_count = sum(1 for row in rows if row["state"].get("invalid_retry_question_id"))
    chart_mutation_allowed_count = sum(1 for row in rows if row["brain"].get("chart_fact_mutation_allowed") is True)
    absorbed_count = sum(
        len(row["brain"].get("absorbed_signals", []))
        for row in rows
        if isinstance(row["brain"].get("absorbed_signals", []), list)
    )
    rejected_signal_count = sum(
        len(row["brain"].get("rejected_signals", []))
        for row in rows
        if isinstance(row["brain"].get("rejected_signals", []), list)
    )
    coverage = (
        min(1.0, accepted_count / 2) * 0.3
        + min(1.0, rejected_count / 1) * 0.25
        + min(1.0, retry_count / 1) * 0.2
        + (0.15 if chart_mutation_allowed_count == 0 else 0.0)
        + min(1.0, (absorbed_count + rejected_signal_count) / 6) * 0.1
    )
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.interaction_brain_structured_constraints",
            domain="question_intelligence",
            signal_type="structured_constraint_pollution_guard",
            strength=round(min(1.0, coverage), 3),
            source_case_ids=source_cases,
            payload={
                "observed_count": len(rows),
                "accepted_count": accepted_count,
                "rejected_count": rejected_count,
                "hidden_factor_update_allowed_count": hidden_allowed_count,
                "invalid_retry_count": retry_count,
                "absorbed_signal_count": absorbed_count,
                "rejected_signal_count": rejected_signal_count,
                "chart_fact_mutation_allowed_count": chart_mutation_allowed_count,
                "boundary": "structured_constraints_train_question_strategy_and_pollution_guards_not_chart_facts",
            },
        )
    ]


def _adaptive_question_replay_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    source_cases: list[str] = []
    decision_count = 0
    weighted_decision_count = 0
    aligned_count = 0
    topics: set[str] = set()
    stages: set[str] = set()
    intents: set[str] = set()
    strategies: set[str] = set()
    reason_category_counts = {
        "central_brain": 0,
        "policy": 0,
        "feedback": 0,
        "boundary": 0,
    }
    policy_weights: list[float] = []
    top_topics: list[str] = []
    for row in result.results:
        diagnostics = row.observed.get("adaptive_question_diagnostics", {})
        if not isinstance(diagnostics, dict):
            continue
        decisions = diagnostics.get("decision_rows", [])
        if not isinstance(decisions, list) or not decisions:
            continue
        source_cases.append(row.case_id)
        decision_count += len(decisions)
        if str(diagnostics.get("alignment_status") or "") in {"brain_graph_and_rank_aligned", "graph_and_rank_aligned"}:
            aligned_count += 1
        strategy = str(diagnostics.get("question_strategy") or "")
        if strategy:
            strategies.add(strategy)
        for index, decision in enumerate(decisions):
            if not isinstance(decision, dict):
                continue
            topic = str(decision.get("topic") or "")
            stage = str(decision.get("stage") or "")
            intent = str(decision.get("intent_id") or "")
            if topic:
                topics.add(topic)
                if index == 0:
                    top_topics.append(topic)
            if stage:
                stages.add(stage)
            if intent:
                intents.add(intent)
            weight = _float_default(decision.get("policy_weight"), 1.0)
            policy_weights.append(weight)
            if weight != 1.0:
                weighted_decision_count += 1
            reason_category_counts["central_brain"] += int(_float(decision.get("central_brain_reason_count")))
            reason_category_counts["policy"] += int(_float(decision.get("policy_reason_count")))
            reason_category_counts["feedback"] += int(_float(decision.get("feedback_reason_count")))
            reason_category_counts["boundary"] += int(_float(decision.get("boundary_reason_count")))
    if not decision_count:
        return []
    average_policy_weight = sum(policy_weights) / max(1, len(policy_weights))
    alignment_coverage = aligned_count / max(1, len(source_cases))
    weighted_coverage = weighted_decision_count / max(1, decision_count)
    strength = round(min(1.0, alignment_coverage * 0.4 + min(1.0, len(topics) / 4) * 0.25 + weighted_coverage * 0.2 + min(1.0, len(strategies) / 3) * 0.15), 3)
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.adaptive_question_replay",
            domain="question_intelligence",
            signal_type="trace_replay_policy_candidate_source",
            strength=strength,
            source_case_ids=source_cases,
            payload={
                "decision_count": decision_count,
                "weighted_decision_count": weighted_decision_count,
                "alignment_coverage": round(alignment_coverage, 3),
                "weighted_decision_coverage": round(weighted_coverage, 3),
                "average_policy_weight": round(average_policy_weight, 3),
                "topics": sorted(topics),
                "stages": sorted(stages),
                "intents": sorted(intents),
                "top_topics": sorted(set(top_topics)),
                "question_strategies": sorted(strategies),
                "reason_category_counts": reason_category_counts,
                "boundary": "adaptive_question_replay_trains_policy_candidates_not_chart_facts",
            },
        )
    ]


def _structure_dynamic_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    competing: list[float] = []
    suppressed: list[float] = []
    blocked: list[float] = []
    countered: list[float] = []
    conflict_families: list[float] = []
    resolution_families: list[float] = []
    branch_conflict_edges: list[float] = []
    branch_alignment_edges: list[float] = []
    domain_paths: list[float] = []
    useful_god_candidate_paths: list[float] = []
    wealth_competition_paths: list[float] = []
    wealth_output_generation_paths: list[float] = []
    wealth_authority_bridge_paths: list[float] = []
    career_authority_pressure_paths: list[float] = []
    career_resource_resolution_paths: list[float] = []
    relationship_conflict_paths: list[float] = []
    relationship_alignment_paths: list[float] = []
    relationship_marker_paths: list[float] = []
    health_element_excess_reviews: list[float] = []
    health_element_thin_reviews: list[float] = []
    health_conflict_pressure_reviews: list[float] = []
    useful_god_ranked_candidates: list[float] = []
    tongguan_paths: list[float] = []
    tongguan_resource_paths: list[float] = []
    tongguan_output_wealth_paths: list[float] = []
    zhihua_paths: list[float] = []
    zhihua_output_authority_paths: list[float] = []
    zhihua_wealth_authority_resource_paths: list[float] = []
    model_signal_ready: list[float] = []
    model_signal_energy_bands: list[float] = []
    model_signal_adjustments: list[float] = []
    source_cases: list[str] = []
    for row in result.results:
        path_scores = row.observed.get("structure_path_scores", {})
        if not isinstance(path_scores, dict):
            continue
        if "dynamic_path_count" not in path_scores:
            continue
        competing.append(_float(path_scores.get("dynamic_competing_path_count")))
        suppressed.append(_float(path_scores.get("dynamic_suppressed_path_count")))
        blocked.append(_float(path_scores.get("dynamic_blocked_path_count")))
        countered.append(_float(path_scores.get("dynamic_countered_path_count")))
        conflict_families.append(_float(path_scores.get("dynamic_conflict_family_count")))
        resolution_families.append(_float(path_scores.get("dynamic_path_resolution_family_count")))
        branch_conflict_edges.append(_float(path_scores.get("dynamic_branch_conflict_edge_count")))
        branch_alignment_edges.append(_float(path_scores.get("dynamic_branch_alignment_edge_count")))
        domain_paths.append(
            _float(path_scores.get("dynamic_wealth_path_count"))
            + _float(path_scores.get("dynamic_career_path_count"))
            + _float(path_scores.get("dynamic_relationship_path_count"))
            + _float(path_scores.get("dynamic_health_review_path_count"))
        )
        useful_god_candidate_paths.append(_float(path_scores.get("dynamic_useful_god_candidate_path_count")))
        wealth_competition_paths.append(_float(path_scores.get("dynamic_wealth_competition_path_count")))
        wealth_output_generation_paths.append(_float(path_scores.get("dynamic_wealth_output_generation_path_count")))
        wealth_authority_bridge_paths.append(_float(path_scores.get("dynamic_wealth_authority_bridge_path_count")))
        career_authority_pressure_paths.append(_float(path_scores.get("dynamic_career_authority_pressure_path_count")))
        career_resource_resolution_paths.append(_float(path_scores.get("dynamic_career_resource_resolution_path_count")))
        relationship_conflict_paths.append(_float(path_scores.get("dynamic_relationship_conflict_path_count")))
        relationship_alignment_paths.append(_float(path_scores.get("dynamic_relationship_alignment_path_count")))
        relationship_marker_paths.append(_float(path_scores.get("dynamic_relationship_marker_path_count")))
        health_element_excess_reviews.append(_float(path_scores.get("dynamic_health_element_excess_review_count")))
        health_element_thin_reviews.append(_float(path_scores.get("dynamic_health_element_thin_review_count")))
        health_conflict_pressure_reviews.append(_float(path_scores.get("dynamic_health_conflict_pressure_review_count")))
        useful_god_ranked_candidates.append(_float(path_scores.get("dynamic_useful_god_ranked_candidate_count")))
        tongguan_paths.append(_float(path_scores.get("dynamic_tongguan_path_count")))
        tongguan_resource_paths.append(_float(path_scores.get("dynamic_tongguan_resource_mediator_path_count")))
        tongguan_output_wealth_paths.append(_float(path_scores.get("dynamic_tongguan_output_wealth_bridge_path_count")))
        zhihua_paths.append(_float(path_scores.get("dynamic_zhihua_path_count")))
        zhihua_output_authority_paths.append(_float(path_scores.get("dynamic_zhihua_output_authority_path_count")))
        zhihua_wealth_authority_resource_paths.append(_float(path_scores.get("dynamic_zhihua_wealth_authority_resource_path_count")))
        model_signal_ready.append(_float(path_scores.get("model_signal_summary_ready")))
        model_signal_energy_bands.append(_float(path_scores.get("model_signal_energy_band_count")))
        model_signal_adjustments.append(_float(path_scores.get("model_signal_structure_path_adjustment")))
        source_cases.append(row.case_id)
    if not competing:
        return []
    average_competing = sum(competing) / len(competing)
    average_suppressed = sum(suppressed) / len(suppressed)
    average_blocked = sum(blocked) / len(blocked)
    average_countered = sum(countered) / len(countered)
    average_conflict_families = sum(conflict_families) / len(conflict_families)
    average_resolution_families = sum(resolution_families) / len(resolution_families)
    average_branch_conflict_edges = sum(branch_conflict_edges) / len(branch_conflict_edges)
    average_branch_alignment_edges = sum(branch_alignment_edges) / len(branch_alignment_edges)
    average_domain_paths = sum(domain_paths) / len(domain_paths)
    average_useful_god_candidate_paths = sum(useful_god_candidate_paths) / len(useful_god_candidate_paths)
    average_domain_rule_depth = sum(
        sum(rows) / len(rows)
        for rows in (
            wealth_competition_paths,
            wealth_output_generation_paths,
            wealth_authority_bridge_paths,
            career_authority_pressure_paths,
            career_resource_resolution_paths,
            relationship_conflict_paths,
            relationship_alignment_paths,
            relationship_marker_paths,
            health_element_excess_reviews,
            health_element_thin_reviews,
            health_conflict_pressure_reviews,
            useful_god_ranked_candidates,
            tongguan_resource_paths,
            tongguan_output_wealth_paths,
            zhihua_output_authority_paths,
            zhihua_wealth_authority_resource_paths,
        )
    ) / 16
    average_tongguan_paths = sum(tongguan_paths) / len(tongguan_paths)
    average_zhihua_paths = sum(zhihua_paths) / len(zhihua_paths)
    average_model_signal_ready = sum(model_signal_ready) / len(model_signal_ready)
    average_model_signal_energy_bands = sum(model_signal_energy_bands) / len(model_signal_energy_bands)
    average_model_signal_adjustment = sum(model_signal_adjustments) / len(model_signal_adjustments)
    strength = round(min(1.0, (average_competing + average_suppressed + average_conflict_families + average_resolution_families + average_domain_paths + average_tongguan_paths + average_zhihua_paths) / 12), 3)
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.structure_dynamic_competition",
            domain="structure_dynamic",
            signal_type="competition",
            strength=strength,
            source_case_ids=source_cases,
            payload={
                "average_competing_path_count": round(average_competing, 3),
                "average_suppressed_path_count": round(average_suppressed, 3),
                "average_blocked_path_count": round(average_blocked, 3),
                "average_countered_path_count": round(average_countered, 3),
                "average_conflict_family_count": round(average_conflict_families, 3),
                "average_path_resolution_family_count": round(average_resolution_families, 3),
                "average_branch_conflict_edge_count": round(average_branch_conflict_edges, 3),
                "average_branch_alignment_edge_count": round(average_branch_alignment_edges, 3),
                "average_domain_path_count": round(average_domain_paths, 3),
                "average_useful_god_candidate_path_count": round(average_useful_god_candidate_paths, 3),
                "average_domain_rule_depth_path_count": round(average_domain_rule_depth, 3),
                "average_tongguan_path_count": round(average_tongguan_paths, 3),
                "average_tongguan_resource_mediator_path_count": round(sum(tongguan_resource_paths) / len(tongguan_resource_paths), 3),
                "average_tongguan_output_wealth_bridge_path_count": round(sum(tongguan_output_wealth_paths) / len(tongguan_output_wealth_paths), 3),
                "average_zhihua_path_count": round(average_zhihua_paths, 3),
                "average_model_signal_ready": round(average_model_signal_ready, 3),
                "average_model_signal_energy_band_count": round(average_model_signal_energy_bands, 3),
                "average_model_signal_structure_path_adjustment": round(average_model_signal_adjustment, 3),
                "average_zhihua_output_authority_path_count": round(sum(zhihua_output_authority_paths) / len(zhihua_output_authority_paths), 3),
                "average_zhihua_wealth_authority_resource_path_count": round(sum(zhihua_wealth_authority_resource_paths) / len(zhihua_wealth_authority_resource_paths), 3),
                "average_wealth_competition_path_count": round(sum(wealth_competition_paths) / len(wealth_competition_paths), 3),
                "average_wealth_output_generation_path_count": round(sum(wealth_output_generation_paths) / len(wealth_output_generation_paths), 3),
                "average_wealth_authority_bridge_path_count": round(sum(wealth_authority_bridge_paths) / len(wealth_authority_bridge_paths), 3),
                "average_career_authority_pressure_path_count": round(sum(career_authority_pressure_paths) / len(career_authority_pressure_paths), 3),
                "average_career_resource_resolution_path_count": round(sum(career_resource_resolution_paths) / len(career_resource_resolution_paths), 3),
                "average_relationship_conflict_path_count": round(sum(relationship_conflict_paths) / len(relationship_conflict_paths), 3),
                "average_relationship_alignment_path_count": round(sum(relationship_alignment_paths) / len(relationship_alignment_paths), 3),
                "average_relationship_marker_path_count": round(sum(relationship_marker_paths) / len(relationship_marker_paths), 3),
                "average_health_element_excess_review_count": round(sum(health_element_excess_reviews) / len(health_element_excess_reviews), 3),
                "average_health_element_thin_review_count": round(sum(health_element_thin_reviews) / len(health_element_thin_reviews), 3),
                "average_health_conflict_pressure_review_count": round(sum(health_conflict_pressure_reviews) / len(health_conflict_pressure_reviews), 3),
                "average_useful_god_ranked_candidate_count": round(sum(useful_god_ranked_candidates) / len(useful_god_ranked_candidates), 3),
                "max_competing_path_count": max(competing),
                "max_suppressed_path_count": max(suppressed),
                "max_conflict_family_count": max(conflict_families),
                "max_path_resolution_family_count": max(resolution_families),
                "max_domain_path_count": max(domain_paths),
                "max_useful_god_candidate_path_count": max(useful_god_candidate_paths),
                "max_tongguan_path_count": max(tongguan_paths),
                "max_zhihua_path_count": max(zhihua_paths),
            },
        )
    ]


def _central_brain_route_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    domains: set[str] = set()
    phases: set[str] = set()
    source_cases: list[str] = []
    for row in result.results:
        trace = row.observed.get("central_brain_trace", {})
        if not isinstance(trace, dict):
            continue
        routes = row.observed.get("central_brain_training_signal_domains", [])
        if isinstance(routes, list):
            domains.update(str(domain) for domain in routes)
        state = trace.get("brain_state", {})
        if isinstance(state, dict) and state.get("session_phase"):
            phases.add(str(state["session_phase"]))
        if routes:
            source_cases.append(row.case_id)
    if not domains:
        return []
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.central_brain_route_coverage",
            domain="central_brain",
            signal_type="route_coverage",
            strength=round(min(1.0, len(domains) / 3), 3),
            source_case_ids=source_cases,
            payload={"route_domains": sorted(domains), "session_phases": sorted(phases)},
        )
    ]


def _central_brain_judge_quality_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    rows: list[dict[str, object]] = []
    source_cases: list[str] = []
    for row in result.results:
        surface = row.observed.get("customer_reading_surface", {})
        surface = surface if isinstance(surface, dict) else {}
        final_synthesis = surface.get("final_synthesis", {})
        final_synthesis = final_synthesis if isinstance(final_synthesis, dict) else {}
        judge = final_synthesis.get("brain_judge", {}) or final_synthesis.get("quality_judge", {})
        judge = judge if isinstance(judge, dict) else {}
        if not judge:
            continue
        rows.append(judge)
        source_cases.append(row.case_id)
    if not rows:
        return []
    accepted_count = sum(1 for row in rows if row.get("accepted") is True)
    rejected_count = len(rows) - accepted_count
    quality_scores = [_float(row.get("quality_score")) for row in rows]
    score_rows = [_dict(row.get("scores")) for row in rows]
    failure_counts: dict[str, int] = {}
    reason_counts: dict[str, int] = {}
    for row in rows:
        for failure in _list(row.get("failures")):
            key = str(failure)
            if key:
                failure_counts[key] = failure_counts.get(key, 0) + 1
        for reason in _list(row.get("reason_codes")):
            key = str(reason)
            if key:
                reason_counts[key] = reason_counts.get(key, 0) + 1
    average_quality = sum(quality_scores) / max(1, len(quality_scores))
    average_template_risk = sum(_float(row.get("template_risk")) for row in score_rows) / max(1, len(score_rows))
    average_overclaim_risk = sum(_float(row.get("overclaim_risk")) for row in score_rows) / max(1, len(score_rows))
    average_advice_actionability = sum(_float(row.get("advice_actionability")) for row in score_rows) / max(1, len(score_rows))
    strength = round(
        max(
            0.0,
            min(
                1.0,
                accepted_count / max(1, len(rows)) * 0.45
                + average_quality * 0.35
                + max(0.0, 1.0 - average_template_risk) * 0.10
                + max(0.0, 1.0 - average_overclaim_risk) * 0.10,
            ),
        ),
        3,
    )
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.central_brain_judge_quality",
            domain="central_brain",
            signal_type="final_synthesis_quality_judge",
            strength=strength,
            source_case_ids=source_cases,
            payload={
                "observed_count": len(rows),
                "accepted_count": accepted_count,
                "rejected_count": rejected_count,
                "average_quality_score": round(average_quality, 3),
                "average_template_risk": round(average_template_risk, 3),
                "average_overclaim_risk": round(average_overclaim_risk, 3),
                "average_advice_actionability": round(average_advice_actionability, 3),
                "failure_counts": dict(sorted(failure_counts.items())),
                "reason_counts": dict(sorted(reason_counts.items())),
                "can_tune_final_synthesis_quality": True,
                "can_tune_template_risk_penalty": True,
                "can_tune_chart_facts": False,
                "boundary": "central_brain_judge_quality_trains_synthesis_policy_not_chart_facts",
            },
        )
    ]


def _central_brain_synthesis_blueprint_quality_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    rows: list[dict[str, object]] = []
    source_cases: list[str] = []
    for row in result.results:
        surface = row.observed.get("customer_reading_surface", {})
        surface = surface if isinstance(surface, dict) else {}
        final_synthesis = surface.get("final_synthesis", {})
        final_synthesis = final_synthesis if isinstance(final_synthesis, dict) else {}
        if not final_synthesis:
            continue
        rows.append(final_synthesis)
        source_cases.append(row.case_id)
    if not rows:
        return []
    observed_count = len(rows)
    decision_focus_count = sum(1 for row in rows if str(row.get("decision_focus") or "").strip())
    action_step_counts = [len(_list(row.get("action_steps"))) for row in rows]
    risk_boundary_count = sum(1 for row in rows if str(row.get("risk_boundary") or "").strip())
    evidence_chain_count = sum(1 for row in rows if _list(row.get("evidence_chain")))
    conclusion_count = sum(1 for row in rows if str(row.get("conclusion") or "").startswith("结论："))
    advice_count = sum(1 for row in rows if str(row.get("advice") or "").startswith("建议："))
    chart_fact_mutation_allowed_count = sum(
        1
        for row in rows
        if _dict(row.get("quality_contract")).get("chart_fact_mutation_allowed") is True
    )
    average_action_step_count = sum(action_step_counts) / max(1, observed_count)
    focus_coverage = decision_focus_count / max(1, observed_count)
    action_coverage = sum(1 for count in action_step_counts if count > 0) / max(1, observed_count)
    risk_coverage = risk_boundary_count / max(1, observed_count)
    evidence_coverage = evidence_chain_count / max(1, observed_count)
    strength = round(
        max(
            0.0,
            min(
                1.0,
                focus_coverage * 0.25
                + action_coverage * 0.25
                + risk_coverage * 0.20
                + evidence_coverage * 0.20
                + min(1.0, average_action_step_count / 2.0) * 0.10,
            ),
        ),
        3,
    )
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.central_brain_synthesis_blueprint_quality",
            domain="central_brain",
            signal_type="final_synthesis_blueprint_quality",
            strength=strength,
            source_case_ids=source_cases,
            payload={
                "observed_count": observed_count,
                "decision_focus_count": decision_focus_count,
                "action_step_surface_count": sum(1 for count in action_step_counts if count > 0),
                "risk_boundary_count": risk_boundary_count,
                "evidence_chain_count": evidence_chain_count,
                "conclusion_first_count": conclusion_count,
                "advice_explicit_count": advice_count,
                "average_action_step_count": round(average_action_step_count, 3),
                "decision_focus_coverage": round(focus_coverage, 3),
                "action_step_coverage": round(action_coverage, 3),
                "risk_boundary_coverage": round(risk_coverage, 3),
                "evidence_chain_coverage": round(evidence_coverage, 3),
                "chart_fact_mutation_allowed_count": chart_fact_mutation_allowed_count,
                "can_tune_synthesis_blueprint": True,
                "can_tune_final_synthesis_quality": True,
                "can_tune_chart_facts": False,
                "boundary": "central_brain_synthesis_blueprint_quality_trains_synthesis_policy_not_chart_facts",
            },
        )
    ]


def _expression_quality_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    bazi_counts: list[int] = []
    forbidden_hits: list[str] = []
    missing_boundary_cases: list[str] = []
    voices: set[str] = set()
    densities: set[str] = set()
    source_cases: list[str] = []
    for row in result.results:
        if row.observed.get("case_domain") == "core_calculation":
            continue
        quality = row.observed.get("expression_quality", {})
        if not isinstance(quality, dict) or not quality:
            continue
        bazi_counts.append(int(_float(quality.get("bazi_term_count"))))
        hits = quality.get("forbidden_token_hits", [])
        if isinstance(hits, list):
            forbidden_hits.extend(str(hit) for hit in hits)
        if not quality.get("has_boundary_language"):
            missing_boundary_cases.append(row.case_id)
        if quality.get("voice"):
            voices.add(str(quality["voice"]))
        if quality.get("density"):
            densities.add(str(quality["density"]))
        source_cases.append(row.case_id)
    if not bazi_counts:
        return []
    average_terms = sum(bazi_counts) / len(bazi_counts)
    leakage_penalty = min(0.4, len(forbidden_hits) / max(1, len(bazi_counts)) * 0.2)
    boundary_penalty = min(0.3, len(missing_boundary_cases) / max(1, len(bazi_counts)) * 0.2)
    strength = round(max(0.0, min(1.0, average_terms / 4 - leakage_penalty - boundary_penalty)), 3)
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.expression_quality",
            domain="expression",
            signal_type="quality",
            strength=strength,
            source_case_ids=source_cases,
            payload={
                "average_bazi_term_count": round(average_terms, 3),
                "min_bazi_term_count": min(bazi_counts),
                "forbidden_token_hits": sorted(set(forbidden_hits)),
                "missing_boundary_cases": missing_boundary_cases,
                "voices": sorted(voices),
                "densities": sorted(densities),
            },
        )
    ]


def _llm_output_contract_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    contract_counts: list[int] = []
    task_types: set[str] = set()
    drift_failures: set[str] = set()
    failed_cases: list[str] = []
    source_cases: list[str] = []
    answer_call_statuses: set[str] = set()
    answer_call_fallback_reasons: set[str] = set()
    answer_call_executed_count = 0
    for row in result.results:
        quality = row.observed.get("llm_output_contract_quality", {})
        if not isinstance(quality, dict):
            continue
        answer_call = row.observed.get("llm_answer_draft_call", {})
        if isinstance(answer_call, dict):
            status = str(answer_call.get("status") or "")
            if status:
                answer_call_statuses.add(status)
            reason = str(answer_call.get("fallback_reason") or "")
            if reason:
                answer_call_fallback_reasons.add(reason)
            if answer_call.get("executed"):
                answer_call_executed_count += 1
        count = int(_float(quality.get("contract_count")))
        if count <= 0:
            failed_cases.append(row.case_id)
        contract_counts.append(count)
        raw_tasks = quality.get("task_types", [])
        if isinstance(raw_tasks, list):
            task_types.update(str(task) for task in raw_tasks)
        raw_failures = quality.get("drift_failures", [])
        if isinstance(raw_failures, list):
            drift_failures.update(str(failure) for failure in raw_failures)
        if quality.get("validation_status") != "passed":
            failed_cases.append(row.case_id)
        if count:
            source_cases.append(row.case_id)
    if not contract_counts:
        return []
    average_count = sum(contract_counts) / len(contract_counts)
    expected_tasks = {
        "answer_draft",
        "question_explanation",
        "synthetic_case_draft",
        "failure_cluster_summary",
    }
    task_coverage = len(task_types & expected_tasks) / len(expected_tasks)
    strength = round(
        max(0.0, min(1.0, average_count / 4 * 0.55 + task_coverage * 0.45 - len(drift_failures) * 0.1 - len(failed_cases) * 0.05)),
        3,
    )
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.llm_output_contract_quality",
            domain="llm",
            signal_type="output_contract_quality",
            strength=strength,
            source_case_ids=source_cases,
            payload={
                "average_contract_count": round(average_count, 3),
                "task_types": sorted(task_types),
                "task_coverage": round(task_coverage, 3),
                "drift_failures": sorted(drift_failures),
                "failed_cases": sorted(set(failed_cases)),
                "answer_call_statuses": sorted(answer_call_statuses),
                "answer_call_fallback_reasons": sorted(answer_call_fallback_reasons),
                "answer_call_executed_count": answer_call_executed_count,
                "boundary": "llm_signal_trains_expression_policy_not_chart_facts",
            },
        )
    ]


def _bazi_llm_output_acceptance_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    source_cases: list[str] = []
    accepted_count = 0
    rejected_count = 0
    schema_rejected_count = 0
    role_failure_count = 0
    drift_rejected_count = 0
    live_llm_required_count = 0
    chart_fact_mutation_allowed_count = 0
    target_training_domains: set[str] = set()
    forbidden_training_domains: set[str] = set()
    for row in result.results:
        quality = row.observed.get("bazi_llm_output_acceptance_quality", {})
        if not isinstance(quality, dict) or not quality:
            continue
        source_cases.append(row.case_id)
        accepted_count += int(_float(quality.get("accepted_count")))
        rejected_count += int(_float(quality.get("rejected_count")))
        schema_rejected_count += int(_float(quality.get("schema_rejected_count")))
        role_failure_count += int(_float(quality.get("role_failure_count")))
        drift_rejected_count += int(_float(quality.get("drift_rejected_count")))
        if quality.get("live_llm_required"):
            live_llm_required_count += 1
        if quality.get("chart_fact_mutation_allowed"):
            chart_fact_mutation_allowed_count += 1
        raw_targets = quality.get("target_training_domains", [])
        if isinstance(raw_targets, list):
            target_training_domains.update(str(row) for row in raw_targets)
        raw_forbidden = quality.get("forbidden_training_domains", [])
        if isinstance(raw_forbidden, list):
            forbidden_training_domains.update(str(row) for row in raw_forbidden)
    if not source_cases:
        return []
    required_targets = {"expression", "question_intelligence"}
    forbidden_chart_targets = {"chart_facts", "calendar_conversion", "luck_cycle", "flow_timing"}
    target_ready = required_targets.issubset(target_training_domains)
    forbidden_present = bool(forbidden_chart_targets & target_training_domains)
    strength = 1.0
    if accepted_count < 2:
        strength -= 0.2
    if rejected_count < 3:
        strength -= 0.2
    if not target_ready:
        strength -= 0.2
    if forbidden_present or live_llm_required_count or chart_fact_mutation_allowed_count:
        strength -= 0.3
    strength = round(max(0.0, min(1.0, strength)), 3)
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.bazi_llm_output_acceptance_quality",
            domain="llm",
            signal_type="bazi_llm_output_acceptance_quality",
            strength=strength,
            source_case_ids=source_cases,
            payload={
                "accepted_count": accepted_count,
                "rejected_count": rejected_count,
                "schema_rejected_count": schema_rejected_count,
                "role_failure_count": role_failure_count,
                "drift_rejected_count": drift_rejected_count,
                "live_llm_required_count": live_llm_required_count,
                "chart_fact_mutation_allowed_count": chart_fact_mutation_allowed_count,
                "target_training_domains": sorted(target_training_domains),
                "forbidden_training_domains": sorted(forbidden_training_domains),
                "can_tune_expression": "expression" in target_training_domains,
                "can_tune_question_strategy": "question_intelligence" in target_training_domains,
                "can_tune_chart_facts": False,
                "boundary": "bazi_llm_output_acceptance_signal_trains_expression_and_question_strategy_not_chart_facts",
            },
        )
    ]


def _failure_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    failures = [
        failure
        for row in result.results
        for failure in row.failures
    ]
    if not failures:
        return []
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.synthetic_failure_cluster",
            domain="validation",
            signal_type="failure_cluster",
            strength=round(min(1.0, len(failures) / max(1, result.case_count)), 3),
            source_case_ids=[row.case_id for row in result.results if row.failures],
            payload={"failures": failures},
        )
    ]


def _hidden_factor_event_alignment_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    states: list[dict[str, object]] = []
    source_cases: list[str] = []
    for row in result.results:
        state = row.observed.get("hidden_factor_state", {})
        if not isinstance(state, dict) or not state:
            continue
        states.append(state)
        source_cases.append(row.case_id)
    if not states:
        return []
    strengths = [_float(state.get("amplifier_strength")) for state in states]
    alignment_scores = [_float(state.get("alignment_score")) for state in states]
    time_layer_scores = [_float(state.get("time_layer_alignment_score")) for state in states]
    candidate_count = sum(1 for state in states if state.get("amplifier_candidate"))
    conflict_count = sum(1 for state in states if state.get("status") == "conflicting")
    denial_count = sum(1 for state in states if state.get("status") == "user_denied")
    expired_count = sum(1 for state in states if state.get("status") == "expired")
    year_aligned = 0
    state_aligned = 0
    time_bound = 0
    domains: set[str] = set()
    for state in states:
        event_signal = state.get("event_year_signal", {})
        repeated_signal = state.get("repeated_state_signal", {})
        if isinstance(event_signal, dict):
            if _float(event_signal.get("year_count")) > 0:
                year_aligned += 1
            if event_signal.get("bound_to_time_context"):
                time_bound += 1
        if isinstance(repeated_signal, dict):
            if _float(repeated_signal.get("state_count")) > 0:
                state_aligned += 1
            raw_domains = repeated_signal.get("domains", [])
            if isinstance(raw_domains, list):
                domains.update(str(domain) for domain in raw_domains)
    coverage = (year_aligned + state_aligned) / max(1, len(states) * 2)
    average_strength = sum(strengths) / len(strengths)
    average_alignment = sum(alignment_scores) / len(alignment_scores)
    average_time_layer_alignment = sum(time_layer_scores) / len(time_layer_scores)
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.hidden_factor_event_alignment",
            domain="hidden_factor",
            signal_type="event_year_alignment",
            strength=round(min(1.0, coverage * 0.5 + average_alignment * 0.3 + candidate_count / max(1, len(states)) * 0.2), 3),
            source_case_ids=source_cases,
            payload={
                "state_count": len(states),
                "state_domains": sorted(domains),
                "average_strength": round(average_strength, 3),
                "average_alignment_score": round(average_alignment, 3),
                "average_time_layer_alignment_score": round(average_time_layer_alignment, 3),
                "candidate_count": candidate_count,
                "conflict_count": conflict_count,
                "denial_count": denial_count,
                "expired_count": expired_count,
                "event_year_coverage": round(year_aligned / max(1, len(states)), 3),
                "repeated_state_coverage": round(state_aligned / max(1, len(states)), 3),
                "time_layer_alignment_coverage": round(time_bound / max(1, len(states)), 3),
            },
        )
    ]


def _latent_bazi_attribute_alignment_signals(result: SyntheticValidationSuiteResult) -> list[SyntheticTrainingSignal]:
    rows: list[dict[str, object]] = []
    source_cases: list[str] = []
    for row in result.results:
        observed = row.observed
        if not isinstance(observed, dict) or observed.get("version") != "v30.synthetic.latent_bazi_divergence.v1":
            continue
        rows.append(observed)
        source_cases.append(row.case_id)
    if not rows:
        return []

    chart_stable_count = sum(1 for row in rows if row.get("chart_facts_stable") is True)
    base_model_stable_count = sum(1 for row in rows if row.get("base_model_stable") is True)
    latent_divergence_count = sum(1 for row in rows if row.get("latent_attributes_diverged") is True)
    projection_divergence_count = sum(1 for row in rows if row.get("individualized_projection_diverged") is True)
    variants = [
        variant
        for row in rows
        for variant in (_dict(row.get("left")), _dict(row.get("right")))
        if variant
    ]
    chart_fact_mutation_allowed_count = sum(1 for variant in variants if variant.get("chart_fact_mutation_allowed") is True)
    individualization_ready_count = sum(1 for variant in variants if variant.get("individualization_ready") is True)
    blocked_routes = sorted({
        str(route)
        for row in rows
        for route in (row.get("blocked_training_routes") if isinstance(row.get("blocked_training_routes"), list) else [])
        if route
    })
    training_routes = sorted({
        str(route)
        for row in rows
        for route in (row.get("training_routes") if isinstance(row.get("training_routes"), list) else [])
        if route
    })
    strength = round(min(
        1.0,
        chart_stable_count / max(1, len(rows)) * 0.25
        + base_model_stable_count / max(1, len(rows)) * 0.25
        + latent_divergence_count / max(1, len(rows)) * 0.25
        + projection_divergence_count / max(1, len(rows)) * 0.25,
    ), 3)
    return [
        SyntheticTrainingSignal(
            signal_id="v30.training_signal.latent_bazi_attribute_alignment",
            domain="hidden_factor",
            signal_type="same_bazi_latent_attribute_and_projection_alignment",
            strength=strength,
            source_case_ids=source_cases,
            payload={
                "case_count": len(rows),
                "variant_count": len(variants),
                "chart_facts_stable_count": chart_stable_count,
                "base_model_stable_count": base_model_stable_count,
                "latent_attribute_divergence_count": latent_divergence_count,
                "individualized_projection_divergence_count": projection_divergence_count,
                "individualization_ready_count": individualization_ready_count,
                "chart_fact_mutation_allowed_count": chart_fact_mutation_allowed_count,
                "state_tags": sorted({str(variant.get("state_tag")) for variant in variants if variant.get("state_tag")}),
                "active_global_attributes": sorted({
                    str(item)
                    for variant in variants
                    for item in (variant.get("active_global_attributes") if isinstance(variant.get("active_global_attributes"), list) else [])
                    if item
                }),
                "active_ten_god_modifiers": sorted({
                    str(item)
                    for variant in variants
                    for item in (variant.get("active_ten_god_modifiers") if isinstance(variant.get("active_ten_god_modifiers"), list) else [])
                    if item
                }),
                "active_domain_biases": sorted({
                    str(item)
                    for variant in variants
                    for item in (variant.get("active_domain_biases") if isinstance(variant.get("active_domain_biases"), list) else [])
                    if item
                }),
                "adjusted_domains": sorted({
                    str(item)
                    for variant in variants
                    for item in (variant.get("adjusted_domains") if isinstance(variant.get("adjusted_domains"), list) else [])
                    if item
                }),
                "training_routes": training_routes,
                "blocked_training_routes": blocked_routes,
                "can_tune_latent_inference": "latent_attribute_inference" in training_routes,
                "can_tune_question_strategy": "question_strategy" in training_routes,
                "can_tune_individualized_projection": "individualized_projection" in training_routes,
                "can_tune_chart_facts": False,
                "boundary": "latent_bazi_attribute_alignment_trains_personalization_not_chart_facts",
            },
        )
    ]


def _float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _dict(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, dict) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _float_default(value: object, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
