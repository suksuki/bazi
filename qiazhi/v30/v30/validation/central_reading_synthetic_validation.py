from __future__ import annotations

from typing import Any, Mapping

from v30.brain.feedback_weight_updater import build_feedback_weight_update
from v30.brain.final_synthesis import build_final_synthesis
from v30.runtime import attach_question_outcome, create_smoke_runtime


CENTRAL_READING_SYNTHETIC_VALIDATION_VERSION = "v30.central_reading_synthetic_validation.v1"


def run_central_reading_synthetic_validation(
    reading_id: str = "cbre5-central-reading-synthetic",
) -> dict[str, object]:
    baseline = create_smoke_runtime(reading_id)
    career = attach_question_outcome(
        baseline,
        "q_v30_user_career_direction",
        {
            "event_id": f"{reading_id}:career_feedback",
            "answer": "事业压力明显，想先判断稳定承接还是转型突破。",
            "selected_option": "career:pressure",
            "confidence": 0.86,
            "feedback_tags": ["career", "pressure"],
        },
    )
    relationship = attach_question_outcome(
        baseline,
        "q_v30_user_relationship_pattern",
        {
            "event_id": f"{reading_id}:relationship_feedback",
            "answer": "关系反复更明显，想先判断沟通和边界问题。",
            "selected_option": "relationship:pattern",
            "confidence": 0.84,
            "feedback_tags": ["relationship", "boundary"],
        },
    )
    return build_central_reading_synthetic_validation(
        baseline_runtime=baseline.model_dump(mode="json"),
        career_runtime=career.model_dump(mode="json"),
        relationship_runtime=relationship.model_dump(mode="json"),
    )


def build_central_reading_synthetic_validation(
    *,
    baseline_runtime: Mapping[str, Any],
    career_runtime: Mapping[str, Any],
    relationship_runtime: Mapping[str, Any],
) -> dict[str, object]:
    baseline_state = _central_state(baseline_runtime)
    career_state = _central_state(career_runtime)
    relationship_state = _central_state(relationship_runtime)
    direct_feedback = _direct_feedback_case()
    direct_synthesis = _direct_final_synthesis_case()
    checks = [
        _check(
            "central_reading_claim_selection",
            _claim_selection_ready(baseline_state),
            {
                "top_claim_ids": _str_list(baseline_state.get("top_claim_ids"))[:3],
                "claim_score_count": len(_list(baseline_state.get("claim_scores"))),
                "final_synthesis_status": _nested(baseline_state, "final_synthesis", "status"),
            },
        ),
        _check(
            "stage_question_policy",
            _stage_question_policy_ready(baseline_state),
            {
                "dialogue_plan_version": _nested(baseline_state, "dialogue_plan", "version"),
                "current_turn_seed_version": _nested(baseline_state, "current_turn_seed", "version"),
                "current_question_id": _nested(baseline_state, "dialogue_plan", "current_question_id"),
            },
        ),
        _check(
            "semantic_ontology_mapping",
            _semantic_ontology_ready(baseline_state, baseline_runtime),
            {
                "ontology_version": baseline_state.get("semantic_ontology_version"),
                "macro_domain_count": _nested(baseline_state, "semantic_ontology", "macro_domain_count"),
                "semantic_trace_version": _nested(baseline_state, "dialogue_plan", "semantic_trace", "version"),
                "training_slots": _nested_list(baseline_state, "dialogue_plan", "semantic_trace", "training_slots")[:5],
            },
        ),
        _check(
            "dialogue_training_trace",
            _dialogue_training_trace_ready(career_state),
            {
                "trace_version": _nested(career_state, "dialogue_training_trace", "version"),
                "semantic_training_slots": _nested_list(career_state, "dialogue_training_trace", "semantic_training_slots")[:5],
                "trainable_targets": _nested_list(career_state, "dialogue_training_trace", "trainable_targets")[:5],
                "blocked_targets": _nested_list(career_state, "dialogue_training_trace", "blocked_targets")[:5],
            },
        ),
        _check(
            "feedback_weight_update",
            _feedback_ready(career_state, direct_feedback),
            {
                "runtime_feedback_version": _nested(career_state, "feedback_weight_update", "version"),
                "runtime_active_signal_count": _nested(career_state, "feedback_weight_update", "active_signal_count"),
                "direct_active_signal_count": direct_feedback.get("active_signal_count"),
            },
        ),
        _check(
            "same_bazi_divergent_feedback",
            _divergent_feedback_ready(baseline_runtime, career_runtime, relationship_runtime),
            {
                "career_positive_claim_ids": _nested_list(career_state, "feedback_weight_update", "summary", "positive_claim_ids")[:5],
                "relationship_positive_claim_ids": _nested_list(relationship_state, "feedback_weight_update", "summary", "positive_claim_ids")[:5],
                "chart_fact_fingerprint_preserved": _chart_facts(baseline_runtime) == _chart_facts(career_runtime) == _chart_facts(relationship_runtime),
            },
        ),
        _check(
            "final_synthesis_quality",
            _final_synthesis_ready(career_state, direct_synthesis),
            {
                "runtime_final_synthesis_version": _nested(career_state, "final_synthesis", "version"),
                "runtime_conclusion": _nested(career_state, "final_synthesis", "conclusion"),
                "direct_conclusion": direct_synthesis.get("conclusion"),
                "brain_judge_score": _nested(career_state, "final_synthesis", "brain_judge", "quality_score"),
                "brain_judge_accepted": _nested(career_state, "final_synthesis", "brain_judge", "accepted"),
            },
        ),
        _check(
            "final_synthesis_blueprint_quality",
            _final_synthesis_blueprint_ready(career_state),
            {
                "blueprint_version": _nested(career_state, "final_synthesis", "synthesis_blueprint", "version"),
                "decision_focus": _nested(career_state, "final_synthesis", "synthesis_blueprint", "decision_focus"),
                "action_step_count": len(_nested_list(career_state, "final_synthesis", "synthesis_blueprint", "action_steps")),
                "risk_boundary": _nested(career_state, "final_synthesis", "synthesis_blueprint", "risk_boundary"),
            },
        ),
        _check(
            "central_brain_v2_decision_loop",
            _central_brain_v2_ready(career_state),
            {
                "graph_missing": _nested(career_state, "evidence_graph_snapshot", "graph_missing"),
                "belief_version": _nested(career_state, "belief_state", "version"),
                "voi_action": _nested(career_state, "value_of_information_policy", "selected_action"),
                "decision_action": _nested(career_state, "brain_decision_trace", "selected_action"),
                "training_example_version": _nested(career_state, "brain_training_example", "version"),
                "training_example_targets": _nested_list(career_state, "brain_training_example", "trainable_targets")[:5],
            },
        ),
    ]
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": CENTRAL_READING_SYNTHETIC_VALIDATION_VERSION,
        "status": "completed" if ready else "blocked",
        "decision": {
            "central_reading_synthetic_ready": ready,
            "decision_status": "cbre5_central_reading_synthetic_ready"
            if ready else "cbre5_central_reading_synthetic_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_write_allowed": False,
        },
        "checks": checks,
        "training_targets": sorted({
            *(_str_list(_nested(career_state, "training_signal", "targets"))),
            *(_str_list(_nested(career_state, "feedback_weight_update", "training_signal", "targets"))),
            *(_str_list(_nested(career_state, "final_synthesis", "training_signal", "targets"))),
            *(_str_list(_nested(career_state, "final_synthesis", "brain_judge", "training_signal", "targets"))),
            *(_str_list(_nested(career_state, "dialogue_plan", "training_signal", "targets"))),
        }),
        "boundary": "central_reading_synthetic_validation_checks_dialogue_feedback_and_synthesis_without_mutating_chart_facts",
    }


def _direct_feedback_case() -> dict[str, object]:
    claims = [
        {"claim_id": "claim.career", "domain": "career", "claim_level": "domain", "claim_text": "事业压力需要资质承接。"},
        {"claim_id": "claim.relationship", "domain": "relationship", "claim_level": "domain", "claim_text": "关系需要边界校准。"},
    ]
    outcomes = [
        {
            "event_id": "synthetic:career",
            "question_id": "q_v30_user_career_direction",
            "topic": "career",
            "selected_option": "career:pressure",
            "outcome_status": "answered",
            "confidence": 0.9,
            "structured_payload": {},
        }
    ]
    return build_feedback_weight_update(claims=claims, question_outcomes=outcomes)


def _direct_final_synthesis_case() -> dict[str, object]:
    diagnosis = {
        "claims": [
            {
                "claim_id": "claim.career",
                "domain": "career",
                "claim_level": "domain",
                "claim_text": "事业主线落在职责压力与资质承接，需要先判断平台规则和可交付能力。",
                "path_ids": ["path.career"],
                "portrait_ids": ["portrait.career"],
            }
        ],
        "paths": [{"path_id": "path.career", "path_label": "官杀 -> 印星"}],
        "portraits": [{"portrait_id": "portrait.career", "statement": "事业画像以规则压力和资源承接为主。"}],
    }
    claim_scores = [
        {
            "claim_id": "claim.career",
            "domain": "career",
            "claim_level": "domain",
            "score": 0.82,
            "confidence_band": "high",
            "requires_question": False,
            "components": {"feedback_alignment": 0.4, "feedback_contradiction": 0.0},
        }
    ]
    practical = {
        "domain_readings": {
            "career": {
                "priority_score": 0.91,
                "action_prompt": "先确认当前职责压力能否转成资质、平台或可交付成果。",
            }
        }
    }
    feedback = {"active_signal_count": 1, "summary": {"positive_claim_ids": ["claim.career"]}}
    return build_final_synthesis(
        diagnosis=diagnosis,
        claim_scores=claim_scores,
        practical_reading_context=practical,
        feedback_weight_update=feedback,
    )


def _claim_selection_ready(state: Mapping[str, Any]) -> bool:
    return (
        str(state.get("version") or "") == "v30.central_reading_state.v1"
        and bool(_list(state.get("claim_scores")))
        and bool(_str_list(state.get("top_claim_ids")))
        and _nested(state, "final_synthesis", "status") == "ready"
    )


def _stage_question_policy_ready(state: Mapping[str, Any]) -> bool:
    return (
        _nested(state, "dialogue_plan", "version") == "v30.dialogue_plan.v1"
        and _nested(state, "current_turn_seed", "version") == "v30.dialogue_turn_seed.v1"
        and _nested(state, "dialogue_plan", "customer_decision_field") == "reading_surface.conversation_surface"
        and _nested(state, "dialogue_plan", "legacy_customer_decision_field") == "reading_surface.current_dialogue_turn"
    )


def _semantic_ontology_ready(state: Mapping[str, Any], runtime_payload: Mapping[str, Any]) -> bool:
    question_semantic_ready = False
    plan = runtime_payload.get("question_plan", {})
    if isinstance(plan, Mapping):
        recommendations = plan.get("recommended_questions", [])
        if isinstance(recommendations, list):
            question_semantic_ready = any(
                isinstance(row, Mapping)
                and _nested(row, "semantic_projection", "version") == "v30.semantic_domain_mapping.v1"
                and bool(_nested(row, "question_score_components", "semantic_weight_slot"))
                for row in recommendations
            )
    return (
        state.get("semantic_ontology_version") == "v30.bazi_semantic_ontology.v1"
        and int(_nested(state, "semantic_ontology", "ten_god_count") or 0) >= 10
        and int(_nested(state, "semantic_ontology", "macro_domain_count") or 0) >= 6
        and _nested(state, "dialogue_plan", "semantic_trace", "version") == "v30.semantic_dialogue_trace.v1"
        and "semantic_question_weight" in _str_list(_nested(state, "dialogue_plan", "training_signal", "targets"))
        and question_semantic_ready
    )


def _dialogue_training_trace_ready(state: Mapping[str, Any]) -> bool:
    return (
        _nested(state, "dialogue_training_trace", "version") == "v30.dialogue_training_trace.v1"
        and bool(_nested_list(state, "dialogue_training_trace", "semantic_training_slots"))
        and "question_selection_policy" in _nested_list(state, "dialogue_training_trace", "trainable_targets")
        and "chart_facts" in _nested_list(state, "dialogue_training_trace", "blocked_targets")
        and _nested(state, "dialogue_training_trace", "quality_gates", "requires_chart_fact_immutability") is True
    )


def _feedback_ready(state: Mapping[str, Any], direct_feedback: Mapping[str, Any]) -> bool:
    return (
        _nested(state, "feedback_weight_update", "version") == "v30.feedback_weight_update.v1"
        and int(_nested(state, "feedback_weight_update", "active_signal_count") or 0) > 0
        and int(direct_feedback.get("active_signal_count") or 0) > 0
        and "chart_facts" in _str_list(_nested(state, "feedback_weight_update", "training_signal", "blocked_targets"))
    )


def _divergent_feedback_ready(
    baseline_runtime: Mapping[str, Any],
    career_runtime: Mapping[str, Any],
    relationship_runtime: Mapping[str, Any],
) -> bool:
    career_positive = set(_nested_list(_central_state(career_runtime), "feedback_weight_update", "summary", "positive_claim_ids"))
    relationship_positive = set(_nested_list(_central_state(relationship_runtime), "feedback_weight_update", "summary", "positive_claim_ids"))
    return (
        _chart_facts(baseline_runtime) == _chart_facts(career_runtime) == _chart_facts(relationship_runtime)
        and bool(career_positive)
        and bool(relationship_positive)
        and career_positive != relationship_positive
    )


def _final_synthesis_ready(state: Mapping[str, Any], direct_synthesis: Mapping[str, Any]) -> bool:
    conclusion = str(_nested(state, "final_synthesis", "conclusion") or "")
    direct_conclusion = str(direct_synthesis.get("conclusion") or "")
    blocked = ("不作为固定人生结论", "不作为具体人生结果断语")
    return (
        _nested(state, "final_synthesis", "version") == "v30.final_synthesis.v1"
        and conclusion.startswith("结论：")
        and str(_nested(state, "final_synthesis", "advice") or "").startswith("建议：")
        and not any(fragment in conclusion for fragment in blocked)
        and direct_conclusion.startswith("结论：")
        and _nested(state, "final_synthesis", "brain_judge", "version") == "v30.central_brain_judge.v1"
        and _nested(state, "final_synthesis", "brain_judge", "accepted") is True
        and float(_nested(state, "final_synthesis", "brain_judge", "quality_score") or 0.0) >= 0.58
        and _nested(state, "final_synthesis", "quality_contract", "chart_fact_mutation_allowed") is False
        and _nested(state, "final_synthesis", "quality_contract", "brain_judge_accepted") is True
    )


def _final_synthesis_blueprint_ready(state: Mapping[str, Any]) -> bool:
    blueprint = _nested(state, "final_synthesis", "synthesis_blueprint")
    if not isinstance(blueprint, Mapping):
        return False
    decision_focus = str(blueprint.get("decision_focus") or "").strip()
    action_steps = _list(blueprint.get("action_steps"))
    risk_boundary = str(blueprint.get("risk_boundary") or "").strip()
    evidence_handles = _list(blueprint.get("evidence_handles"))
    return (
        blueprint.get("version") == "v30.final_synthesis_blueprint.v1"
        and bool(decision_focus)
        and len(action_steps) >= 1
        and bool(risk_boundary)
        and len(evidence_handles) >= 1
        and blueprint.get("boundary") == "final_synthesis_blueprint_structures_existing_claims_evidence_and_actions_not_new_facts"
    )


def _central_brain_v2_ready(state: Mapping[str, Any]) -> bool:
    decision_action = str(_nested(state, "brain_decision_trace", "selected_action") or "")
    voi_action = str(_nested(state, "value_of_information_policy", "selected_action") or "")
    return (
        _nested(state, "evidence_graph_snapshot", "version") == "v30.central_brain.evidence_graph_snapshot.v1"
        and _nested(state, "evidence_graph_snapshot", "graph_missing") is False
        and int(_nested(state, "graph_claim_metric_count") or 0) > 0
        and _nested(state, "belief_state", "version") == "v30.central_brain.belief_state.v1"
        and bool(_nested_list(state, "belief_state", "top_claims") or _nested_list(state, "belief_state", "weak_claims"))
        and _nested(state, "value_of_information_policy", "version") == "v30.central_brain.value_of_information_policy.v1"
        and voi_action in {"ask_stage_question", "conclude_stage", "continue_next_stage", "final_synthesis"}
        and _nested(state, "brain_decision_trace", "version") == "v30.central_brain.decision_trace.v1"
        and decision_action in {"ask_stage_question", "conclude_stage", "continue_next_stage", "final_synthesis"}
        and _nested(state, "brain_decision_trace", "chart_fact_mutation_allowed") is False
        and _nested(state, "brain_training_example", "version") == "v30.brain_training_example.v1"
        and _nested(state, "brain_training_example", "safety", "chart_fact_mutation_allowed") is False
        and "chart_facts" in _nested_list(state, "brain_training_example", "blocked_targets")
        and "value_of_information_policy" in _nested_list(state, "brain_training_example", "trainable_targets")
    )


def _central_state(runtime_payload: Mapping[str, Any]) -> dict[str, Any]:
    plan = runtime_payload.get("question_plan", {})
    plan = plan if isinstance(plan, Mapping) else {}
    effect = plan.get("policy_effect", {})
    effect = effect if isinstance(effect, Mapping) else {}
    state = effect.get("central_reading_state", {})
    return dict(state) if isinstance(state, Mapping) else {}


def _chart_facts(runtime_payload: Mapping[str, Any]) -> dict[str, Any]:
    chart = runtime_payload.get("chart_context", {})
    return dict(chart) if isinstance(chart, Mapping) else {}


def _check(check_id: str, passed: bool, observed: Mapping[str, Any]) -> dict[str, object]:
    return {
        "check_id": check_id,
        "passed": bool(passed),
        "observed": dict(observed),
    }


def _nested(payload: Mapping[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, Mapping):
            return ""
        current = current.get(key, "")
    return current


def _nested_list(payload: Mapping[str, Any], *keys: str) -> list[str]:
    return _str_list(_nested(payload, *keys))


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(row) for row in value if row]
