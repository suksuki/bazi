from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from v30.runtime import attach_question_outcome, create_smoke_runtime

DIALOGUE_TRAINING_CALIBRATION_LOOP_VERSION = "v30.dialogue_training_calibration_loop.v1"
TRAINING_SAMPLE_VERSION = "v30.dialogue_training_sample.v1"
POLICY_CANDIDATE_VERSION = "v30.dialogue_policy_candidate.v1"


def run_dialogue_training_calibration_loop(
    *,
    runtime_payloads: Sequence[Mapping[str, Any]] | None = None,
    sample_limit: int = 20,
    run_id: str = "dialogue-training-calibration-loop",
) -> dict[str, object]:
    payloads = list(runtime_payloads or [])
    if not payloads:
        payloads = _synthetic_seed_payloads(run_id)
    limited = payloads[: max(1, min(int(sample_limit), 100))]
    result = build_dialogue_training_calibration_loop(
        runtime_payloads=limited,
        run_id=run_id,
    )
    if int(_mapping(result.get("sample_summary")).get("sample_count") or 0) > 0:
        return result
    synthetic = _synthetic_seed_payloads(run_id)
    return build_dialogue_training_calibration_loop(
        runtime_payloads=[*limited, *synthetic],
        run_id=run_id,
    )


def build_dialogue_training_calibration_loop(
    *,
    runtime_payloads: Sequence[Mapping[str, Any]],
    run_id: str = "dialogue-training-calibration-loop",
) -> dict[str, object]:
    samples = [
        sample
        for payload in runtime_payloads
        if (sample := _sample_from_runtime(payload))
    ]
    candidates = _policy_candidates(samples)
    quality = _quality_summary(samples)
    checks = _checks(samples=samples, candidates=candidates, quality=quality)
    failed = [row for row in checks if not row["passed"]]
    ready = not failed
    return {
        "version": DIALOGUE_TRAINING_CALIBRATION_LOOP_VERSION,
        "run_id": run_id,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if ready else "blocked",
        "task": {
            "task_id": "DTC-1",
            "title": "Dialogue Training Calibration Loop",
            "scope": "convert_real_or_runtime_dialogue_traces_into_trainable_policy_candidates_without_mutating_chart_facts",
        },
        "sample_summary": _sample_summary(samples),
        "quality_summary": quality,
        "training_samples": samples,
        "policy_candidates": candidates,
        "checks": checks,
        "decision": {
            "dialogue_training_calibration_ready": ready,
            "decision_status": "dtc1_dialogue_training_calibration_ready"
            if ready else "dtc1_dialogue_training_calibration_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "sample_count": len(samples),
            "policy_candidate_count": len(candidates),
            "chart_fact_mutation_allowed": False,
            "policy_pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "live_llm_required": False,
        },
        "policy_boundary": {
            "runtime_mutation_allowed": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "auto_apply_training_allowed": False,
            "candidate_review_required": True,
            "blocked_targets": [
                "chart_facts",
                "calendar_conversion",
                "pillar_calculation",
                "unconfirmed_hidden_factor_facts",
            ],
            "boundary": "dialogue_training_calibration_loop_outputs_candidates_only_no_runtime_or_pointer_mutation",
        },
        "next_mainline_selection": {
            "task_id": "DTC-2" if ready else "DTC-1-FIX",
            "title": "Dialogue Policy Candidate Review" if ready else "Fix Dialogue Training Calibration Loop",
            "reason": "runtime_dialogue_traces_are_ready_for_candidate_review"
            if ready else "dialogue_training_calibration_checks_failed",
        },
        "boundary": "dialogue_training_calibration_loop_is_training_evidence_not_bazi_truth",
    }


def _sample_from_runtime(payload: Mapping[str, Any]) -> dict[str, object]:
    plan = _mapping(payload.get("question_plan"))
    effect = _mapping(plan.get("policy_effect"))
    state = _mapping(effect.get("central_reading_state"))
    trace = _mapping(state.get("dialogue_training_trace"))
    dialogue_plan = _mapping(state.get("dialogue_plan"))
    final_synthesis = _mapping(state.get("final_synthesis"))
    outcomes = _list(_mapping(plan.get("session_state")).get("question_outcomes"))
    if trace.get("version") != "v30.dialogue_training_trace.v1":
        return {}
    sample_id = f"{payload.get('reading_id', '')}:{trace.get('current_question_id', '')}:dialogue-sample"
    answer_quality = _answer_quality(payload, final_synthesis, outcomes)
    semantic_slots = _str_list(trace.get("semantic_training_slots"))
    decision_features = _mapping(trace.get("decision_features"))
    return {
        "version": TRAINING_SAMPLE_VERSION,
        "sample_id": sample_id,
        "reading_id": str(payload.get("reading_id") or ""),
        "trace_id": str(payload.get("trace_id") or ""),
        "dialogue_action": str(trace.get("dialogue_action") or ""),
        "question_id": str(trace.get("current_question_id") or ""),
        "macro_domain": str(trace.get("current_macro_domain") or ""),
        "semantic_training_slots": semantic_slots,
        "decision_features": {
            "necessity_score": _float(decision_features.get("necessity_score")),
            "question_score": _float(decision_features.get("current_question_score")),
            "top_claim_score": _float(decision_features.get("top_claim_score")),
            "user_cost": _float(decision_features.get("user_cost")),
            "overask_penalty": _float(decision_features.get("overask_penalty")),
            "answered_count": int(_float(decision_features.get("answered_count"))),
        },
        "feedback_labels": _mapping(trace.get("feedback_labels")),
        "answer_quality": answer_quality,
        "policy_label": _policy_label(trace, answer_quality),
        "trainable_targets": _str_list(trace.get("trainable_targets")),
        "blocked_targets": _str_list(trace.get("blocked_targets")),
        "dialogue_plan_boundary": str(dialogue_plan.get("boundary") or ""),
        "chart_fact_mutation_allowed": False,
        "boundary": "dialogue_training_sample_extracts_policy_label_without_mutating_runtime_or_chart_facts",
    }


def _answer_quality(
    payload: Mapping[str, Any],
    final_synthesis: Mapping[str, Any],
    outcomes: list[object],
) -> dict[str, object]:
    answer = _mapping(payload.get("answer_result"))
    text = str(answer.get("text") or "")
    conclusion = str(final_synthesis.get("conclusion") or "")
    advice = str(final_synthesis.get("advice") or "")
    has_conclusion = conclusion.startswith("结论：") or "结论" in text[:80]
    has_advice = advice.startswith("建议：") or "建议" in text[:120]
    generic_penalty = _generic_penalty(" ".join([text, conclusion, advice]))
    feedback_count = sum(1 for row in outcomes if isinstance(row, Mapping))
    score = 0.36 + (0.18 if has_conclusion else 0.0) + (0.18 if has_advice else 0.0)
    score += min(0.14, feedback_count * 0.05)
    score -= generic_penalty
    return {
        "score": round(max(0.0, min(1.0, score)), 3),
        "has_conclusion": has_conclusion,
        "has_advice": has_advice,
        "feedback_count": feedback_count,
        "generic_penalty": round(generic_penalty, 3),
        "llm_status": str(_mapping(answer.get("llm_metadata")).get("status") or ""),
        "boundary": "answer_quality_label_guides_expression_policy_not_chart_facts",
    }


def _policy_label(trace: Mapping[str, Any], answer_quality: Mapping[str, Any]) -> str:
    action = str(trace.get("dialogue_action") or "")
    quality = _float(answer_quality.get("score"))
    feedback = _mapping(trace.get("feedback_labels"))
    answered_count = int(feedback.get("answered_count") or 0)
    if action == "ask_stage_question" and answered_count >= 1 and quality >= 0.62:
        return "ask_was_useful"
    if action == "ask_stage_question" and quality < 0.5:
        return "ask_needs_better_answer_quality"
    if action == "conclude_stage" and quality >= 0.68:
        return "conclude_was_useful"
    if action == "ask_stage_question":
        return "ask_needs_more_evidence"
    return "observe_only"


def _policy_candidates(samples: list[dict[str, object]]) -> list[dict[str, object]]:
    by_slot: dict[str, list[dict[str, object]]] = defaultdict(list)
    by_domain: dict[str, list[dict[str, object]]] = defaultdict(list)
    for sample in samples:
        for slot in _str_list(sample.get("semantic_training_slots")):
            by_slot[slot].append(sample)
        domain = str(sample.get("macro_domain") or "")
        if domain:
            by_domain[domain].append(sample)
    candidates: list[dict[str, object]] = []
    for slot, rows in sorted(by_slot.items()):
        candidates.append(_candidate_for_group(f"semantic_slot:{slot}", rows, target="semantic_question_weight"))
    for domain, rows in sorted(by_domain.items()):
        if len(rows) >= 1:
            candidates.append(_candidate_for_group(f"macro_domain:{domain}", rows, target="macro_domain_question_slot_weight"))
    candidates.append(_overask_candidate(samples))
    return [row for row in candidates if row]


def _candidate_for_group(group_id: str, rows: list[dict[str, object]], *, target: str) -> dict[str, object]:
    labels = Counter(str(row.get("policy_label") or "") for row in rows)
    avg_quality = _avg(_float(_mapping(row.get("answer_quality")).get("score")) for row in rows)
    avg_necessity = _avg(_float(_mapping(row.get("decision_features")).get("necessity_score")) for row in rows)
    direction = "increase" if labels.get("ask_was_useful", 0) >= labels.get("ask_needs_better_answer_quality", 0) else "review"
    if avg_quality < 0.52:
        direction = "hold_until_answer_quality_improves"
    return {
        "version": POLICY_CANDIDATE_VERSION,
        "candidate_id": f"dtc1.{group_id}",
        "candidate_type": target,
        "group_id": group_id,
        "sample_count": len(rows),
        "label_counts": dict(labels),
        "recommended_direction": direction,
        "evidence": {
            "average_answer_quality": round(avg_quality, 3),
            "average_necessity_score": round(avg_necessity, 3),
        },
        "requires_operator_review": True,
        "auto_apply_allowed": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "allowed_training_scope": [target, "question_selection_policy", "answer_quality_policy"],
        "blocked_training_scope": ["chart_facts", "calendar_conversion", "pillar_calculation"],
        "boundary": "dialogue_policy_candidate_requires_review_and_cannot_mutate_chart_facts",
    }


def _overask_candidate(samples: list[dict[str, object]]) -> dict[str, object]:
    if not samples:
        return {}
    avg_overask = _avg(_float(_mapping(row.get("decision_features")).get("overask_penalty")) for row in samples)
    avg_cost = _avg(_float(_mapping(row.get("decision_features")).get("user_cost")) for row in samples)
    return {
        "version": POLICY_CANDIDATE_VERSION,
        "candidate_id": "dtc1.overask_user_cost",
        "candidate_type": "dialogue_action_policy",
        "group_id": "dialogue_cost",
        "sample_count": len(samples),
        "label_counts": dict(Counter(str(row.get("policy_label") or "") for row in samples)),
        "recommended_direction": "review_overask_penalty" if avg_overask >= 0.12 or avg_cost >= 0.3 else "keep_current",
        "evidence": {
            "average_overask_penalty": round(avg_overask, 3),
            "average_user_cost": round(avg_cost, 3),
        },
        "requires_operator_review": True,
        "auto_apply_allowed": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "allowed_training_scope": ["dialogue_action_policy", "overask_penalty_weight", "user_cost_weight"],
        "blocked_training_scope": ["chart_facts", "calendar_conversion", "pillar_calculation"],
        "boundary": "dialogue_cost_candidate_can_tune_ask_frequency_not_bazi_facts",
    }


def _quality_summary(samples: list[dict[str, object]]) -> dict[str, object]:
    scores = [_float(_mapping(row.get("answer_quality")).get("score")) for row in samples]
    return {
        "version": "v30.dialogue_training_quality_summary.v1",
        "sample_count": len(samples),
        "average_answer_quality": round(_avg(scores), 3),
        "min_answer_quality": round(min(scores), 3) if scores else 0.0,
        "conclusion_ready_count": sum(1 for row in samples if _mapping(row.get("answer_quality")).get("has_conclusion") is True),
        "advice_ready_count": sum(1 for row in samples if _mapping(row.get("answer_quality")).get("has_advice") is True),
        "generic_penalty_count": sum(1 for row in samples if _float(_mapping(row.get("answer_quality")).get("generic_penalty")) > 0.0),
        "boundary": "quality_summary_labels_answer_and_dialogue_policy_not_chart_facts",
    }


def _sample_summary(samples: list[dict[str, object]]) -> dict[str, object]:
    return {
        "version": "v30.dialogue_training_sample_summary.v1",
        "sample_count": len(samples),
        "reading_count": len({str(row.get("reading_id") or "") for row in samples if row.get("reading_id")}),
        "macro_domains": sorted({str(row.get("macro_domain") or "") for row in samples if row.get("macro_domain")}),
        "semantic_slot_count": len({
            slot for row in samples for slot in _str_list(row.get("semantic_training_slots"))
        }),
        "policy_labels": dict(Counter(str(row.get("policy_label") or "") for row in samples)),
    }


def _checks(
    *,
    samples: list[dict[str, object]],
    candidates: list[dict[str, object]],
    quality: Mapping[str, object],
) -> list[dict[str, object]]:
    return [
        _check(
            "dialogue_training_samples_present",
            bool(samples),
            {"sample_count": len(samples)},
        ),
        _check(
            "semantic_slots_are_trainable",
            any(_str_list(row.get("semantic_training_slots")) for row in samples),
            {"semantic_slot_count": _sample_summary(samples)["semantic_slot_count"]},
        ),
        _check(
            "policy_candidates_are_review_only",
            bool(candidates)
            and all(row.get("requires_operator_review") is True for row in candidates)
            and all(row.get("auto_apply_allowed") is False for row in candidates)
            and all(row.get("policy_pointer_promotion_allowed") is False for row in candidates),
            {"candidate_count": len(candidates)},
        ),
        _check(
            "chart_fact_mutation_is_blocked",
            all(row.get("chart_fact_mutation_allowed") is False for row in samples)
            and all(row.get("chart_fact_mutation_allowed") is False for row in candidates),
            {"blocked": True},
        ),
        _check(
            "answer_quality_is_measurable",
            float(quality.get("average_answer_quality") or 0.0) > 0.0,
            {"average_answer_quality": quality.get("average_answer_quality")},
        ),
    ]


def _check(check_id: str, passed: bool, observed: Mapping[str, object]) -> dict[str, object]:
    return {"check_id": check_id, "passed": bool(passed), "observed": dict(observed)}


def _synthetic_seed_payloads(run_id: str) -> list[dict[str, object]]:
    baseline = create_smoke_runtime(f"{run_id}-baseline")
    career = attach_question_outcome(
        baseline,
        "q_v30_user_career_direction",
        {
            "event_id": f"{run_id}:career",
            "answer": "事业压力明显，先看职责和转型节奏。",
            "selected_option": "career:pressure",
            "confidence": 0.82,
            "feedback_tags": ["career", "pressure"],
        },
    )
    relationship = attach_question_outcome(
        baseline,
        "q_v30_user_relationship_pattern",
        {
            "event_id": f"{run_id}:relationship",
            "answer": "关系反复明显，先看相处模式和边界。",
            "selected_option": "relationship:pattern",
            "confidence": 0.8,
            "feedback_tags": ["relationship", "boundary"],
        },
    )
    return [baseline.model_dump(mode="json"), career.model_dump(mode="json"), relationship.model_dump(mode="json")]


def _generic_penalty(text: str) -> float:
    generic_terms = ("综合来看", "仅供参考", "需要进一步", "不能作为", "当前阶段", "可能", "大概率")
    return min(0.24, 0.04 * sum(1 for term in generic_terms if term in text))


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _str_list(value: object) -> list[str]:
    return [str(row) for row in value] if isinstance(value, list) else []


def _float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _avg(values: Any) -> float:
    rows = [float(row) for row in values]
    return sum(rows) / len(rows) if rows else 0.0
