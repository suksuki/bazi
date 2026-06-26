from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import Field

from v30.contracts import V30Model
from v30.policy import PolicyCandidate, PromotionResult, RuntimePointerStore, make_baseline_candidate
from v30.policy.promotion import promote_candidate_if_valid
from v30.policy.runtime_pointer import PolicyFamily


DEFAULT_AUTO_TRAINING_FAMILIES: tuple[PolicyFamily, ...] = (
    "structure_policy",
    "mainline_policy",
    "question_policy",
    "rule_policy",
)


class AutoTrainingRunResult(V30Model):
    training_run_id: str
    families: list[PolicyFamily]
    started_at: datetime
    finished_at: datetime
    auto_apply: bool = True
    status: str
    candidates: list[PolicyCandidate] = Field(default_factory=list)
    promotions: list[PromotionResult] = Field(default_factory=list)
    active_policy_versions: dict[str, str] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    failures: list[str] = Field(default_factory=list)


def run_auto_apply_training(
    *,
    families: tuple[PolicyFamily, ...] = DEFAULT_AUTO_TRAINING_FAMILIES,
    training_run_id: str | None = None,
    store: RuntimePointerStore | None = None,
    validation_artifact_dir: str | Path | None = None,
    promotion_validation_mode: str = "strict",
) -> AutoTrainingRunResult:
    from v30.validation import extract_training_signals, run_synthetic_tier

    started_at = datetime.now(timezone.utc)
    run_id = training_run_id or f"v30.auto_training.{started_at.strftime('%Y%m%d%H%M%S')}"
    store = store or RuntimePointerStore()
    synthetic_signal_source = run_synthetic_tier("all", suite_id=f"{run_id}.training_signal_source")
    training_signals = extract_training_signals(synthetic_signal_source)
    candidates = [
        make_baseline_candidate(
            candidate_id=f"{run_id}.{family}",
            family=family,
            payload=_candidate_payload(family, run_id, training_signals),
            change_summary="auto-generated candidate from V30 mainline training loop",
        )
        for family in families
    ]
    promotions = [
        promote_candidate_if_valid(
            candidate,
            store=store,
            validation_artifact_dir=validation_artifact_dir,
            validation_mode=promotion_validation_mode,
        )
        for candidate in candidates
    ]
    failures = [failure for promotion in promotions for failure in promotion.failures]
    promoted_count = sum(1 for promotion in promotions if promotion.promoted)
    finished_at = datetime.now(timezone.utc)
    active_versions = store.active_versions(families)
    return AutoTrainingRunResult(
        training_run_id=run_id,
        families=list(families),
        started_at=started_at,
        finished_at=finished_at,
        status="applied" if promoted_count == len(promotions) else "failed",
        candidates=candidates,
        promotions=promotions,
        active_policy_versions=active_versions,
        metrics={
            "candidate_count": len(candidates),
            "promoted_count": promoted_count,
            "failed_count": len(promotions) - promoted_count,
            "training_signal_count": len(training_signals),
            "synthetic_signal_case_count": synthetic_signal_source.case_count,
            "promotion_validation_mode": promotion_validation_mode,
        },
        failures=failures,
    )


def _candidate_payload(
    family: PolicyFamily,
    training_run_id: str,
    training_signals: list[Any] | None = None,
) -> dict[str, Any]:
    training_signals = training_signals or []
    payload: dict[str, Any] = {
        "mode": "auto_apply_training",
        "family": family,
        "training_run_id": training_run_id,
        "source": "synthetic_smoke",
        "auto_apply": True,
        "training_signals": [signal.model_dump(mode="json") for signal in training_signals],
    }
    if family == "structure_policy":
        payload["weights"] = _structure_weights_from_signals(training_signals)
    if family == "question_policy":
        payload["weights"] = _question_policy_weights_from_signals(training_signals)
    if family == "rule_policy":
        hidden_factor_event_policy = _hidden_factor_event_policy_from_signals(training_signals)
        latent_bazi_attribute_policy = _latent_bazi_attribute_policy_from_signals(training_signals)
        per_unit_policy = _per_unit_policy_from_signals(training_signals)
        payload["weights"] = {
            "rule_weights": {
                "v30.rule.time_context.blocks_timing_claim": 1.02,
                "v30.rule.useful_god.candidate_gate": 1.02,
                "v30.rule.hidden_factor.requires_dialogue": hidden_factor_event_policy["dialogue_rule_weight"],
                "v30.rule.branch_relation.requires_dynamic_review": 1.01,
                "*": 1.0,
            },
            "domain_weights": {
                "time_context": 1.0,
                "useful_god": 1.0,
                "hidden_factor": hidden_factor_event_policy["rule_domain_weight"],
                "branch_relation": 1.0,
                "*": 1.0,
            },
            "hidden_factor_event_policy": hidden_factor_event_policy,
            "latent_bazi_attribute_policy": latent_bazi_attribute_policy,
            "per_unit_parameter_policy": per_unit_policy,
        }
        payload["weights"]["rule_weights"].update(per_unit_policy["rule_weights"])
        payload["weights"]["domain_weights"].update(per_unit_policy["domain_weights"])
    return payload


def _structure_weights_from_signals(training_signals: list[Any]) -> dict[str, float]:
    weights = {
        "mechanism.hidden_factor_dialogue_probe": 1.05,
        "mechanism.ten_god_visibility_context": 1.02,
        "mechanism.useful_god_candidate_gate": 1.0,
        "mechanism.branch_relation_dynamic_review": 1.0,
        "dynamic_graph.v2": 1.0,
        "dynamic_graph.competition_suppression": 1.0,
        "dynamic_graph.conflict_family": 1.0,
        "dynamic_graph.path_resolution": 1.0,
        "dynamic_graph.domain_path": 1.0,
        "dynamic_graph.domain_rule_depth": 1.0,
        "dynamic_graph.useful_god_candidate_path": 1.0,
        "dynamic_graph.tongguan_zhihua": 1.0,
        "dynamic_graph.model_signal_fusion": 1.0,
        "model_signal.energy_band_calibration": 1.0,
        "model_signal.stability_review": 1.0,
        "model_signal.volatility_review": 1.0,
        "model_signal.family_coverage": 1.0,
        "ranked_decision.follow_structure_boundary": 1.0,
        "ranked_decision.disputed_structure": 1.0,
        "ranked_decision.regulation_climate_boundary": 1.0,
        "ranked_decision.special_structure_boundary": 1.0,
        "ranked_decision.useful_god_evidence": 1.0,
    }
    for signal in training_signals:
        if getattr(signal, "signal_id", "") != "v30.training_signal.structure_dynamic_competition":
            continue
        strength = float(getattr(signal, "strength", 0.0))
        payload = getattr(signal, "payload", {})
        average_suppressed = 0.0
        average_conflict_families = 0.0
        average_resolution_families = 0.0
        average_domain_paths = 0.0
        average_domain_rule_depth = 0.0
        average_useful_god_candidate_paths = 0.0
        average_tongguan_paths = 0.0
        average_zhihua_paths = 0.0
        average_model_signal_ready = 0.0
        average_model_signal_energy_bands = 0.0
        if isinstance(payload, dict):
            try:
                average_suppressed = float(payload.get("average_suppressed_path_count", 0.0))
            except (TypeError, ValueError):
                average_suppressed = 0.0
            try:
                average_conflict_families = float(payload.get("average_conflict_family_count", 0.0))
            except (TypeError, ValueError):
                average_conflict_families = 0.0
            try:
                average_resolution_families = float(payload.get("average_path_resolution_family_count", 0.0))
            except (TypeError, ValueError):
                average_resolution_families = 0.0
            try:
                average_domain_paths = float(payload.get("average_domain_path_count", 0.0))
            except (TypeError, ValueError):
                average_domain_paths = 0.0
            try:
                average_domain_rule_depth = float(payload.get("average_domain_rule_depth_path_count", 0.0))
            except (TypeError, ValueError):
                average_domain_rule_depth = 0.0
            try:
                average_useful_god_candidate_paths = float(payload.get("average_useful_god_candidate_path_count", 0.0))
            except (TypeError, ValueError):
                average_useful_god_candidate_paths = 0.0
            try:
                average_tongguan_paths = float(payload.get("average_tongguan_path_count", 0.0))
            except (TypeError, ValueError):
                average_tongguan_paths = 0.0
            try:
                average_zhihua_paths = float(payload.get("average_zhihua_path_count", 0.0))
            except (TypeError, ValueError):
                average_zhihua_paths = 0.0
            try:
                average_model_signal_ready = float(payload.get("average_model_signal_ready", 0.0))
            except (TypeError, ValueError):
                average_model_signal_ready = 0.0
            try:
                average_model_signal_energy_bands = float(payload.get("average_model_signal_energy_band_count", 0.0))
            except (TypeError, ValueError):
                average_model_signal_energy_bands = 0.0
        weights["dynamic_graph.v2"] = round(1.0 + strength * 0.04, 3)
        weights["dynamic_graph.competition_suppression"] = round(
            1.0 + min(0.08, average_suppressed * 0.01),
            3,
        )
        weights["dynamic_graph.conflict_family"] = round(
            1.0 + min(0.06, average_conflict_families * 0.015),
            3,
        )
        weights["dynamic_graph.path_resolution"] = round(
            1.0 + min(0.06, average_resolution_families * 0.012),
            3,
        )
        weights["dynamic_graph.domain_path"] = round(
            1.0 + min(0.06, average_domain_paths * 0.006),
            3,
        )
        weights["dynamic_graph.domain_rule_depth"] = round(
            1.0 + min(0.06, average_domain_rule_depth * 0.01),
            3,
        )
        weights["dynamic_graph.useful_god_candidate_path"] = round(
            1.0 + min(0.06, average_useful_god_candidate_paths * 0.008),
            3,
        )
        weights["dynamic_graph.tongguan_zhihua"] = round(
            1.0 + min(0.06, (average_tongguan_paths + average_zhihua_paths) * 0.006),
            3,
        )
        weights["dynamic_graph.model_signal_fusion"] = round(
            1.0 + min(0.05, average_model_signal_ready * 0.02 + average_model_signal_energy_bands * 0.004),
            3,
        )
    for signal in training_signals:
        if getattr(signal, "signal_id", "") != "v30.training_signal.ten_god_energy_fusion":
            continue
        strength = float(getattr(signal, "strength", 0.0))
        weights["dynamic_graph.model_signal_fusion"] = round(
            max(weights.get("dynamic_graph.model_signal_fusion", 1.0), 1.0 + min(0.05, strength * 0.035)),
            3,
        )
        payload = getattr(signal, "payload", {})
        if isinstance(payload, dict):
            family_count = len(payload.get("calibration_family_coverage", [])) if isinstance(payload.get("calibration_family_coverage", []), list) else 0
            replay_family_count = len(payload.get("real_case_replay_family_coverage", [])) if isinstance(payload.get("real_case_replay_family_coverage", []), list) else 0
            calibration_case_count = float(payload.get("calibration_case_count", 0.0) or 0.0)
            replay_ready_count = float(payload.get("real_case_replay_interface_ready_count", 0.0) or 0.0)
            energy_band_counts = payload.get("energy_band_counts", {})
            stability_band_counts = payload.get("stability_band_counts", {})
            volatility_band_counts = payload.get("volatility_band_counts", {})
            high_energy_count = float(energy_band_counts.get("high", 0.0) or 0.0) if isinstance(energy_band_counts, dict) else 0.0
            low_stability_count = float(stability_band_counts.get("low", 0.0) or 0.0) if isinstance(stability_band_counts, dict) else 0.0
            high_volatility_count = float(volatility_band_counts.get("high", 0.0) or 0.0) if isinstance(volatility_band_counts, dict) else 0.0
            weights["model_signal.family_coverage"] = round(
                max(weights["model_signal.family_coverage"], 1.0 + min(0.04, family_count * 0.006 + replay_family_count * 0.003)),
                3,
            )
            weights["model_signal.energy_band_calibration"] = round(
                max(weights["model_signal.energy_band_calibration"], 1.0 + min(0.04, calibration_case_count * 0.004 + replay_ready_count * 0.002 + high_energy_count * 0.002)),
                3,
            )
            weights["model_signal.stability_review"] = round(
                max(weights["model_signal.stability_review"], 1.0 + min(0.035, low_stability_count * 0.006)),
                3,
            )
            weights["model_signal.volatility_review"] = round(
                max(weights["model_signal.volatility_review"], 1.0 + min(0.035, high_volatility_count * 0.005)),
                3,
            )
    for signal in training_signals:
        if getattr(signal, "signal_id", "") != "v30.training_signal.m5_weight_replay":
            continue
        payload = getattr(signal, "payload", {})
        if not isinstance(payload, dict):
            continue
        structure_candidate_weights = payload.get("structure_candidate_weights", {})
        useful_coverage = float(payload.get("useful_god_evidence_coverage", 0.0) or 0.0)
        if isinstance(structure_candidate_weights, dict):
            weights["ranked_decision.follow_structure_boundary"] = round(
                max(weights["ranked_decision.follow_structure_boundary"], float(structure_candidate_weights.get("follow_structure_boundary_review", 1.0) or 1.0)),
                3,
            )
            weights["ranked_decision.disputed_structure"] = round(
                max(weights["ranked_decision.disputed_structure"], float(structure_candidate_weights.get("disputed_structure_review", 1.0) or 1.0)),
                3,
            )
            weights["ranked_decision.regulation_climate_boundary"] = round(
                max(weights["ranked_decision.regulation_climate_boundary"], float(structure_candidate_weights.get("regulation_climate_boundary_review", 1.0) or 1.0)),
                3,
            )
            weights["ranked_decision.special_structure_boundary"] = round(
                max(weights["ranked_decision.special_structure_boundary"], float(structure_candidate_weights.get("special_structure_boundary_review", 1.0) or 1.0)),
                3,
            )
        weights["ranked_decision.useful_god_evidence"] = round(
            max(weights["ranked_decision.useful_god_evidence"], 1.0 + min(0.045, useful_coverage * 0.04)),
            3,
        )
    per_unit_policy = _per_unit_policy_from_signals(training_signals)
    for key, value in per_unit_policy["mechanism_weights"].items():
        if key == "*":
            continue
        weights[key] = round(max(weights.get(key, 1.0), float(value)), 3)
    return weights


def _question_policy_weights_from_signals(training_signals: list[Any]) -> dict[str, Any]:
    topic_weights = {
        "time_context": 1.03,
        "hidden_factor": 1.01,
        "useful_god": 1.0,
        "structure_dynamic": 1.0,
        "mainline": 1.0,
    }
    intent_weights = {
        "confirm_missing_time_context": 1.02,
        "discover_hidden_factor_amplifier": 1.01,
        "review_useful_god_candidate_paths": 1.0,
        "*": 1.0,
    }
    stage_weights = {
        "context_completion": 1.02,
        "dialogue_discovery": 1.01,
        "candidate_review": 1.0,
        "mainline_review": 1.0,
    }
    for signal in training_signals:
        if getattr(signal, "signal_id", "") != "v30.training_signal.question_dialogue_outcome":
            continue
        strength = float(getattr(signal, "strength", 0.0))
        payload = getattr(signal, "payload", {})
        raw_topics = payload.get("topics", []) if isinstance(payload, dict) else []
        topics = [str(topic) for topic in raw_topics] if isinstance(raw_topics, list) else []
        for topic in topics:
            key = str(topic)
            if key in topic_weights and key != "time_context":
                topic_weights[key] = round(topic_weights[key] + min(0.035, strength * 0.02), 3)
        if "hidden_factor" in topics:
            intent_weights["discover_hidden_factor_amplifier"] = round(
                intent_weights["discover_hidden_factor_amplifier"] + min(0.03, strength * 0.018),
                3,
            )
        if "useful_god" in topics:
            intent_weights["review_useful_god_candidate_paths"] = round(1.0 + min(0.03, strength * 0.018), 3)
    adaptive_policy = _adaptive_question_policy_from_signals(training_signals)
    interaction_policy = _interaction_followup_policy_from_signals(training_signals)
    model_signal_policy = _model_signal_question_policy_from_signals(training_signals)
    latent_bazi_attribute_policy = _latent_bazi_attribute_policy_from_signals(training_signals)
    for topic, weight in adaptive_policy["topic_weights"].items():
        if topic in topic_weights:
            topic_weights[topic] = round(max(topic_weights[topic], float(weight)), 3)
    for intent, weight in adaptive_policy["intent_weights"].items():
        if intent in intent_weights:
            intent_weights[intent] = round(max(intent_weights[intent], float(weight)), 3)
    for stage, weight in adaptive_policy["stage_weights"].items():
        if stage in stage_weights:
            stage_weights[stage] = round(max(stage_weights[stage], float(weight)), 3)
    return {
        "topic_weights": topic_weights,
        "intent_weights": intent_weights,
        "stage_weights": stage_weights,
        "adaptive_question_policy": adaptive_policy,
        "interaction_followup_policy": interaction_policy,
        "model_signal_question_policy": model_signal_policy,
        "hidden_factor_event_policy": _hidden_factor_event_policy_from_signals(training_signals),
        "latent_bazi_attribute_policy": latent_bazi_attribute_policy,
        "question_weights": {"*": 1.0},
        "krp_unit_weights": _krp_unit_weights_from_signals(training_signals),
    }


def _model_signal_question_policy_from_signals(training_signals: list[Any]) -> dict[str, Any]:
    policy: dict[str, Any] = {
        "version": "v30.model_signal_question_policy.v1",
        "source_signal_id": "v30.training_signal.question_model_signal_personalization",
        "mode": "model_signal_focus_weight_candidate_not_chart_fact",
        "topic_weights": {},
        "focus_pairs": [],
        "focus_topics": [],
        "coverage": 0.0,
        "top_question_coverage": 0.0,
        "max_delta": 0.04,
        "can_tune_question_strategy": True,
        "can_tune_chart_facts": False,
        "boundary": "model_signal_question_policy_trains_question_strategy_not_chart_facts",
    }
    topic_targets = {"career", "wealth", "relationship", "timing", "decision", "hidden_factor"}
    for signal in training_signals:
        if getattr(signal, "signal_id", "") != "v30.training_signal.question_model_signal_personalization":
            continue
        strength = float(getattr(signal, "strength", 0.0))
        payload = getattr(signal, "payload", {})
        if not isinstance(payload, dict):
            continue
        if payload.get("can_tune_chart_facts") is True:
            continue
        coverage = _payload_float(payload, "coverage")
        top_coverage = _payload_float(payload, "top_question_coverage")
        focused_count = _payload_float(payload, "model_signal_focused_count")
        reason_count = _payload_float(payload, "model_signal_focus_reason_count")
        topics = sorted(_payload_str_set(payload.get("model_signal_focus_topics")) & topic_targets)
        pairs = sorted(_payload_str_set(payload.get("model_signal_focus_pairs")))
        delta = min(0.04, strength * 0.018 + coverage * 0.01 + top_coverage * 0.008 + min(0.01, reason_count * 0.0005))
        topic_weights: dict[str, float] = {}
        for topic in topics:
            topic_weights[topic] = round(1.0 + delta, 3)
        policy.update(
            {
                "topic_weights": topic_weights,
                "focus_pairs": pairs,
                "focus_topics": topics,
                "coverage": round(coverage, 3),
                "top_question_coverage": round(top_coverage, 3),
                "model_signal_focused_count": int(focused_count),
                "model_signal_focus_reason_count": int(reason_count),
                "signal_strength": round(strength, 3),
            }
        )
    return policy


def _interaction_followup_policy_from_signals(training_signals: list[Any]) -> dict[str, Any]:
    policy: dict[str, Any] = {
        "version": "v30.interaction_followup_policy.v1",
        "source_signal_ids": [
            "v30.training_signal.interaction_state_machine",
            "v30.training_signal.interaction_loop_quality",
        ],
        "mode": "visible_followup_policy_candidate_not_chart_fact",
        "visible_next_question_weight": 1.0,
        "internal_diagnostic_weight": 1.0,
        "selected_domain_weight": 1.0,
        "max_delta": 0.035,
        "boundary": "interaction_followup_policy_trains_question_strategy_not_chart_facts",
    }
    for signal in training_signals:
        signal_id = getattr(signal, "signal_id", "")
        if signal_id not in {
            "v30.training_signal.interaction_state_machine",
            "v30.training_signal.interaction_loop_quality",
        }:
            continue
        strength = float(getattr(signal, "strength", 0.0))
        payload = getattr(signal, "payload", {})
        if not isinstance(payload, dict):
            continue
        if signal_id == "v30.training_signal.interaction_state_machine":
            split_count = _payload_float(payload, "visible_internal_split_count")
            internal_count = _payload_float(payload, "internal_next_question_count")
            policy["internal_diagnostic_weight"] = round(1.0 + min(0.03, strength * 0.012 + internal_count * 0.001), 3)
            policy["visible_next_question_weight"] = round(1.0 + min(0.035, strength * 0.015 + split_count * 0.006), 3)
            policy["stages"] = sorted(_payload_str_set(payload.get("stages")))
            policy["selected_domains"] = sorted(_payload_str_set(payload.get("selected_domains")))
        if signal_id == "v30.training_signal.interaction_loop_quality":
            visible_count = _payload_float(payload, "visible_surface_next_question_count")
            leak_count = _payload_float(payload, "internal_next_question_surface_leak_count")
            selected_domain_count = _payload_float(payload, "selected_domain_surface_count")
            policy["visible_next_question_weight"] = round(
                max(float(policy["visible_next_question_weight"]), 1.0 + min(0.035, strength * 0.018 + visible_count * 0.001)),
                3,
            )
            policy["selected_domain_weight"] = round(1.0 + min(0.025, selected_domain_count * 0.004), 3)
            policy["surface_leak_penalty"] = round(max(0.8, 1.0 - leak_count * 0.02), 3)
    return policy


def _adaptive_question_policy_from_signals(training_signals: list[Any]) -> dict[str, Any]:
    policy: dict[str, Any] = {
        "version": "v30.adaptive_question_policy.v1",
        "source_signal_id": "v30.training_signal.adaptive_question_replay",
        "mode": "trace_replay_weight_candidate_not_chart_fact",
        "topic_weights": {},
        "intent_weights": {},
        "stage_weights": {},
        "alignment_coverage": 0.0,
        "weighted_decision_coverage": 0.0,
        "max_delta": 0.035,
        "boundary": "adaptive_question_policy_weights_replay_diagnostics_not_chart_facts",
    }
    topic_targets = {"time_context", "hidden_factor", "useful_god", "structure_dynamic", "mainline"}
    intent_targets = {
        "confirm_missing_time_context",
        "discover_hidden_factor_amplifier",
        "review_useful_god_candidate_paths",
        "review_current_chart_mainline",
    }
    stage_targets = {"context_completion", "dialogue_discovery", "candidate_review", "mainline_review"}
    for signal in training_signals:
        if getattr(signal, "signal_id", "") != "v30.training_signal.adaptive_question_replay":
            continue
        strength = float(getattr(signal, "strength", 0.0))
        payload = getattr(signal, "payload", {})
        if not isinstance(payload, dict):
            continue
        alignment = _payload_float(payload, "alignment_coverage")
        weighted = _payload_float(payload, "weighted_decision_coverage")
        average_policy_weight = _payload_float(payload, "average_policy_weight")
        delta = min(0.035, strength * 0.018 + alignment * 0.01 + weighted * 0.007)
        top_topics = _payload_str_set(payload.get("top_topics"))
        topics = _payload_str_set(payload.get("topics"))
        intents = _payload_str_set(payload.get("intents"))
        stages = _payload_str_set(payload.get("stages"))
        for topic in sorted((top_topics or topics) & topic_targets):
            policy["topic_weights"][topic] = round(1.0 + delta, 3)
        for intent in sorted(intents & intent_targets):
            if intent == "review_current_chart_mainline":
                policy["intent_weights"][intent] = round(1.0 + min(0.02, delta * 0.5), 3)
            else:
                policy["intent_weights"][intent] = round(1.0 + min(0.03, delta * 0.8), 3)
        for stage in sorted(stages & stage_targets):
            policy["stage_weights"][stage] = round(1.0 + min(0.025, delta * 0.7), 3)
        policy.update(
            {
                "alignment_coverage": round(alignment, 3),
                "weighted_decision_coverage": round(weighted, 3),
                "average_policy_weight": round(average_policy_weight, 3),
                "question_strategies": sorted(_payload_str_set(payload.get("question_strategies"))),
                "signal_strength": round(strength, 3),
            }
        )
    return policy


def _hidden_factor_event_policy_from_signals(training_signals: list[Any]) -> dict[str, Any]:
    policy: dict[str, Any] = {
        "version": "v30.hidden_factor.event_policy.v1",
        "source_signal_id": "v30.training_signal.hidden_factor_event_alignment",
        "mode": "feedback_conditioned_not_chart_fact",
        "min_alignment_score": 0.45,
        "candidate_alignment_multiplier": 1.02,
        "time_layer_alignment_multiplier": 1.01,
        "expired_refresh_multiplier": 1.015,
        "conflict_multiplier": 0.88,
        "denial_multiplier": 0.82,
        "dialogue_rule_weight": 1.03,
        "rule_domain_weight": 1.0,
        "max_positive_multiplier": 1.06,
        "boundary": "hidden_factor_policy_weights_feedback_conditioned_not_chart_fact",
    }
    for signal in training_signals:
        if getattr(signal, "signal_id", "") != "v30.training_signal.hidden_factor_event_alignment":
            continue
        strength = float(getattr(signal, "strength", 0.0))
        payload = getattr(signal, "payload", {})
        if not isinstance(payload, dict):
            continue
        average_alignment = _payload_float(payload, "average_alignment_score")
        average_time_layer = _payload_float(payload, "average_time_layer_alignment_score")
        event_coverage = _payload_float(payload, "event_year_coverage")
        repeated_coverage = _payload_float(payload, "repeated_state_coverage")
        time_coverage = _payload_float(payload, "time_layer_alignment_coverage")
        candidate_count = _payload_float(payload, "candidate_count")
        conflict_count = _payload_float(payload, "conflict_count")
        denial_count = _payload_float(payload, "denial_count")
        expired_count = _payload_float(payload, "expired_count")
        positive_alignment = min(0.06, strength * 0.025 + average_alignment * 0.015 + min(event_coverage, repeated_coverage) * 0.015)
        time_alignment = min(0.035, average_time_layer * 0.015 + time_coverage * 0.012)
        policy.update(
            {
                "min_alignment_score": round(max(0.4, min(0.65, average_alignment * 0.75)), 3),
                "candidate_alignment_multiplier": round(1.0 + positive_alignment, 3),
                "time_layer_alignment_multiplier": round(1.0 + time_alignment, 3),
                "expired_refresh_multiplier": round(1.0 + min(0.03, 0.012 + expired_count * 0.004 + time_coverage * 0.008), 3),
                "conflict_multiplier": round(max(0.78, 0.9 - conflict_count * 0.015), 3),
                "denial_multiplier": round(max(0.72, 0.84 - denial_count * 0.015), 3),
                "dialogue_rule_weight": round(1.03 + min(0.025, strength * 0.015), 3),
                "rule_domain_weight": round(1.0 + min(0.02, max(0.0, candidate_count - conflict_count - denial_count) * 0.004), 3),
                "signal_payload": {
                    "candidate_count": int(candidate_count),
                    "conflict_count": int(conflict_count),
                    "denial_count": int(denial_count),
                    "expired_count": int(expired_count),
                    "event_year_coverage": round(event_coverage, 3),
                    "repeated_state_coverage": round(repeated_coverage, 3),
                    "time_layer_alignment_coverage": round(time_coverage, 3),
                },
            }
        )
    return policy


def _latent_bazi_attribute_policy_from_signals(training_signals: list[Any]) -> dict[str, Any]:
    policy: dict[str, Any] = {
        "version": "v30.latent_bazi_attribute_policy.v1",
        "source_signal_id": "v30.training_signal.latent_bazi_attribute_alignment",
        "mode": "latent_personalization_candidate_not_chart_fact",
        "reverse_inference_weight": 1.0,
        "question_need_weight": 1.0,
        "individualized_projection_weight": 1.0,
        "domain_bias_weights": {},
        "ten_god_modifier_weights": {},
        "global_attribute_weights": {},
        "blocked_training_routes": ["calendar_conversion", "chart_facts", "flow_timing", "luck_cycle"],
        "can_tune_latent_inference": False,
        "can_tune_question_strategy": False,
        "can_tune_individualized_projection": False,
        "can_tune_chart_facts": False,
        "max_delta": 0.035,
        "boundary": "latent_bazi_attribute_policy_trains_personalization_not_chart_facts",
    }
    for signal in training_signals:
        if getattr(signal, "signal_id", "") != "v30.training_signal.latent_bazi_attribute_alignment":
            continue
        strength = float(getattr(signal, "strength", 0.0))
        payload = getattr(signal, "payload", {})
        if not isinstance(payload, dict):
            continue
        if payload.get("can_tune_chart_facts") is True:
            continue
        chart_stable = _payload_float(payload, "chart_facts_stable_count") / max(1.0, _payload_float(payload, "case_count"))
        base_stable = _payload_float(payload, "base_model_stable_count") / max(1.0, _payload_float(payload, "case_count"))
        latent_divergence = _payload_float(payload, "latent_attribute_divergence_count") / max(1.0, _payload_float(payload, "case_count"))
        projection_divergence = _payload_float(payload, "individualized_projection_divergence_count") / max(1.0, _payload_float(payload, "case_count"))
        safety = min(chart_stable, base_stable)
        delta = min(0.035, strength * 0.012 + safety * 0.008 + latent_divergence * 0.008 + projection_divergence * 0.007)
        policy.update(
            {
                "reverse_inference_weight": round(1.0 + min(0.035, delta), 3),
                "question_need_weight": round(1.0 + min(0.025, delta * 0.72), 3),
                "individualized_projection_weight": round(1.0 + min(0.035, delta * 0.95), 3),
                "domain_bias_weights": {
                    key: round(1.0 + min(0.03, delta * 0.85), 3)
                    for key in sorted(_payload_str_set(payload.get("active_domain_biases")))
                },
                "ten_god_modifier_weights": {
                    key: round(1.0 + min(0.025, delta * 0.75), 3)
                    for key in sorted(_payload_str_set(payload.get("active_ten_god_modifiers")))
                },
                "global_attribute_weights": {
                    key: round(1.0 + min(0.025, delta * 0.7), 3)
                    for key in sorted(_payload_str_set(payload.get("active_global_attributes")))
                },
                "state_tags": sorted(_payload_str_set(payload.get("state_tags"))),
                "adjusted_domains": sorted(_payload_str_set(payload.get("adjusted_domains"))),
                "blocked_training_routes": sorted(_payload_str_set(payload.get("blocked_training_routes"))),
                "can_tune_latent_inference": payload.get("can_tune_latent_inference") is True,
                "can_tune_question_strategy": payload.get("can_tune_question_strategy") is True,
                "can_tune_individualized_projection": payload.get("can_tune_individualized_projection") is True,
                "can_tune_chart_facts": False,
                "signal_strength": round(strength, 3),
                "safety_coverage": round(safety, 3),
            }
        )
    return policy


def _per_unit_policy_from_signals(training_signals: list[Any]) -> dict[str, Any]:
    policy: dict[str, Any] = {
        "version": "v30.per_unit_parameter_policy.v1",
        "source_signal_id": "v30.training_signal.per_unit_parameter_tuning",
        "mode": "runtime_candidate_weighting_not_chart_fact",
        "rule_weights": {"*": 1.0},
        "domain_weights": {"*": 1.0},
        "mechanism_weights": {"*": 1.0},
        "failure_count": 0,
        "boundary": "per_unit_weights_tune_runtime_candidates_not_chart_facts",
    }
    for signal in training_signals:
        if getattr(signal, "signal_id", "") != "v30.training_signal.per_unit_parameter_tuning":
            continue
        payload = getattr(signal, "payload", {})
        if not isinstance(payload, dict):
            continue
        policy["rule_weights"] = _float_map(payload.get("rule_weights"), cap=1.08)
        policy["domain_weights"] = _float_map(payload.get("domain_weights"), cap=1.05)
        policy["mechanism_weights"] = _float_map(payload.get("mechanism_weights"), cap=1.08)
        policy["failure_count"] = int(_payload_float(payload, "failure_count"))
        policy["unit_count"] = int(_payload_float(payload, "unit_count"))
    return policy


def _float_map(value: object, *, cap: float) -> dict[str, float]:
    if not isinstance(value, dict):
        return {"*": 1.0}
    rows: dict[str, float] = {"*": 1.0}
    for key, raw in value.items():
        try:
            rows[str(key)] = round(max(0.5, min(float(raw), cap)), 3)
        except (TypeError, ValueError):
            continue
    rows.setdefault("*", 1.0)
    return rows


def _payload_float(payload: dict[str, Any], key: str) -> float:
    try:
        return float(payload.get(key, 0.0))
    except (TypeError, ValueError):
        return 0.0


def _payload_str_set(value: object) -> set[str]:
    if not isinstance(value, list):
        return set()
    return {str(row) for row in value if row is not None and str(row)}


def _krp_unit_weights_from_signals(training_signals: list[Any]) -> dict[str, float]:
    weights = {
        "hidden_factor": 1.03,
        "structure_dynamic": 1.02,
        "time_context": 1.02,
        "element": 1.01,
        "branch_relation": 1.02,
        "useful_god": 1.0,
        "ten_god": 1.0,
        "wealth": 1.0,
        "career": 1.0,
        "relationship": 1.0,
        "health": 1.0,
        "*": 1.0,
    }
    for signal in training_signals:
        if getattr(signal, "signal_id", "") == "v30.training_signal.krp_unit_coverage":
            strength = float(getattr(signal, "strength", 0.0))
            weights["hidden_factor"] = round(1.03 + strength * 0.02, 3)
            weights["time_context"] = round(1.02 + strength * 0.02, 3)
            weights["branch_relation"] = round(1.02 + strength * 0.015, 3)
            weights["wealth"] = round(1.0 + strength * 0.015, 3)
            weights["career"] = round(1.0 + strength * 0.015, 3)
            weights["relationship"] = round(1.0 + strength * 0.015, 3)
            weights["health"] = round(1.0 + strength * 0.012, 3)
        if getattr(signal, "signal_id", "") == "v30.training_signal.question_graph_edge_coverage":
            strength = float(getattr(signal, "strength", 0.0))
            weights["structure_dynamic"] = round(1.02 + strength * 0.02, 3)
    return weights
