from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v30.validation.intelligent_question_closeout import run_intelligent_question_closeout
from v30.validation.m8_projection_api_contract_closeout import run_m8_projection_api_contract_closeout
from v30.validation.synthetic_case import run_synthetic_tier
from v30.validation.training_signals import extract_training_signals


IQ_INTELLIGENT_QUESTION_SUPPORT_REVIEW_VERSION = "v30.iq_intelligent_question_support_review.v1"


def run_iq_intelligent_question_support_review(
    *,
    sample_limit: int = 8,
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    m8_closeout = run_m8_projection_api_contract_closeout(
        sample_limit=sample_limit,
        artifact_dir=artifact_dir,
    )
    iq_closeout = run_intelligent_question_closeout("iq-support-review")
    interaction_loop = run_synthetic_tier("interaction_loop")
    interaction_payload = interaction_loop.model_dump(mode="json")
    interaction_payload["training_signals"] = [
        signal.model_dump(mode="json") for signal in extract_training_signals(interaction_loop)
    ]
    return build_iq_intelligent_question_support_review(
        m8_closeout=m8_closeout,
        iq_closeout=iq_closeout,
        interaction_loop=interaction_payload,
        artifact_dir=artifact_dir,
    )


def build_iq_intelligent_question_support_review(
    *,
    m8_closeout: Mapping[str, Any],
    iq_closeout: Mapping[str, Any],
    interaction_loop: Mapping[str, Any],
    artifact_dir: str | Path | None = None,
) -> dict[str, Any]:
    reviewed_at = datetime.now(timezone.utc)
    review_id = f"v30.iq.s1.{reviewed_at.strftime('%Y%m%d%H%M%S%f')}"
    m8_summary = _m8_summary(m8_closeout)
    iq_summary = _iq_summary(iq_closeout)
    interaction_summary = _interaction_summary(interaction_loop)
    support_summary = _support_summary(iq_closeout)
    checks = _checks(
        m8_summary=m8_summary,
        iq_summary=iq_summary,
        interaction_summary=interaction_summary,
        support_summary=support_summary,
    )
    decision = _decision(checks, interaction_summary)
    payload: dict[str, Any] = {
        "version": IQ_INTELLIGENT_QUESTION_SUPPORT_REVIEW_VERSION,
        "review_id": review_id,
        "reviewed_at": reviewed_at.isoformat(),
        "status": "completed" if decision["iq_support_review_ready"] else "blocked",
        "decision": decision,
        "m8_closeout_summary": m8_summary,
        "iq_closeout_summary": iq_summary,
        "interaction_loop_summary": interaction_summary,
        "support_summary": support_summary,
        "checks": checks,
        "policy_boundary": {
            "supports_core_bazi_reading": decision["iq_support_review_ready"],
            "question_strategy_training_allowed": True,
            "hidden_factor_feedback_as_clue_only": True,
            "llm_expression_context_allowed": True,
            "runtime_decision_write_allowed": False,
            "auto_apply_training_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "pointer_write_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
            "full_pytest_required": False,
            "full_518k_required": False,
            "live_llm_required": False,
            "boundary": "iq_support_review_keeps_questions_auxiliary_to_core_bazi_calculation",
        },
        "monitoring_baseline": _monitoring_baseline(interaction_summary),
        "next_mainline_selection": _next_selection(decision),
        "boundary": "iq_intelligent_question_support_review_validates_question_flow_after_m8_closeout",
    }
    if artifact_dir is not None:
        payload["artifact_uri"] = str(_write_artifact(payload, Path(artifact_dir)))
    return payload


def _m8_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "m8_projection_api_contract_closed": bool(decision.get("m8_projection_api_contract_closed")),
        "projection_case_count": int(decision.get("projection_case_count", 0) or 0),
        "projection_contract_count": int(decision.get("projection_contract_count", 0) or 0),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
    }


def _iq_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("decision"))
    completion = _mapping(payload.get("module_completion"))
    return {
        "version": str(payload.get("version") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "intelligent_question_closeout_ready": bool(decision.get("intelligent_question_closeout_ready")),
        "passed_count": int(decision.get("passed_count", 0) or 0),
        "check_count": int(decision.get("check_count", 0) or 0),
        "question_dialogue_graph_completion": int(completion.get("question_dialogue_graph", 0) or 0),
        "question_policy_training_completion": int(completion.get("question_policy_training", 0) or 0),
        "llm_question_context_completion": int(completion.get("llm_question_context", 0) or 0),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
        "policy_pointer_write_allowed": bool(decision.get("policy_pointer_write_allowed")),
        "live_llm_required": bool(decision.get("live_llm_required")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
    }


def _interaction_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    signal_ids = {
        str(_mapping(row).get("signal_id") or "")
        for row in _list(payload.get("training_signals"))
        if _mapping(row).get("signal_id")
    }
    return {
        "suite_id": str(payload.get("suite_id") or ""),
        "passed": bool(payload.get("passed")),
        "case_count": int(payload.get("case_count", 0) or 0),
        "passed_count": int(payload.get("passed_count", 0) or 0),
        "signal_ids": sorted(signal_ids),
        "has_question_dialogue_outcome": "v30.training_signal.question_dialogue_outcome" in signal_ids,
        "has_interaction_state_machine": "v30.training_signal.interaction_state_machine" in signal_ids,
        "has_interaction_loop_quality": "v30.training_signal.interaction_loop_quality" in signal_ids,
        "has_question_model_signal_personalization": "v30.training_signal.question_model_signal_personalization" in signal_ids,
        "boundary": "interaction_loop_trains_question_strategy_not_chart_facts",
    }


def _support_summary(iq_closeout: Mapping[str, Any]) -> dict[str, Any]:
    closeout = _mapping(iq_closeout.get("closeout_summary"))
    layer = _mapping(closeout.get("layer_contract"))
    training = _mapping(closeout.get("training_candidate"))
    llm_role = _mapping(closeout.get("llm_and_role"))
    core = _mapping(closeout.get("core_boundary"))
    steady = _mapping(closeout.get("steady_state"))
    return {
        "recommendation_count": int(layer.get("recommendation_count", 0) or 0),
        "user_question_count": int(layer.get("user_question_count", 0) or 0),
        "visible_next_question_id": str(layer.get("visible_next_question_id") or ""),
        "internal_next_question_id": str(layer.get("internal_next_question_id") or ""),
        "user_diagnostic_key_count": int(layer.get("user_diagnostic_key_count", 0) or 0),
        "admin_has_interaction_state": bool(layer.get("admin_has_interaction_state")),
        "admin_has_question_dialogue_graph": bool(layer.get("admin_has_question_dialogue_graph")),
        "has_model_signal_question_policy": bool(training.get("has_model_signal_question_policy")),
        "model_signal_policy_can_tune_chart_facts": bool(training.get("model_signal_policy_can_tune_chart_facts")),
        "has_interaction_followup_policy": bool(training.get("has_interaction_followup_policy")),
        "has_adaptive_question_policy": bool(training.get("has_adaptive_question_policy")),
        "answer_task_type": str(llm_role.get("answer_task_type") or ""),
        "answer_context_pack": str(llm_role.get("answer_context_pack") or ""),
        "domain_chart_fact_mutation_allowed": bool(llm_role.get("domain_chart_fact_mutation_allowed")),
        "user_internal_next_visible": bool(llm_role.get("user_internal_next_visible")),
        "core_fingerprint_unchanged": bool(core.get("core_fingerprint_unchanged")),
        "model_signal_version": str(core.get("model_signal_version") or ""),
        "ranked_decision_domain_count": len(_list(core.get("ranked_decision_domains"))),
        "business_topic_count": len(_list(core.get("business_topics_present"))),
        "heavy_validation_required": any(
            steady.get(key) is True
            for key in ("full_pytest_required", "synthetic_all_required", "full_518k_required", "live_llm_required")
        ),
        "pointer_or_fact_write_allowed": bool(steady.get("policy_pointer_write_allowed"))
        or bool(steady.get("chart_fact_mutation_allowed")),
        "boundary": "iq_support_summary_reviews_personalized_question_flow_not_chart_fact_generation",
    }


def _checks(
    *,
    m8_summary: Mapping[str, Any],
    iq_summary: Mapping[str, Any],
    interaction_summary: Mapping[str, Any],
    support_summary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        {
            "check_id": "m8_projection_surface_ready_before_iq_review",
            "passed": (
                m8_summary["version"] == "v30.m8_projection_api_contract_closeout.v1"
                and m8_summary["m8_projection_api_contract_closed"]
                and m8_summary["projection_case_count"] >= 30
                and m8_summary["projection_contract_count"] >= 20
                and not m8_summary["policy_pointer_promotion_allowed"]
                and not m8_summary["chart_fact_mutation_allowed"]
            ),
            "expected": "M8 projection/API contract is closed before IQ review",
        },
        {
            "check_id": "iq5_closeout_remains_ready",
            "passed": (
                iq_summary["version"] == "v30.intelligent_question_closeout.v1"
                and iq_summary["intelligent_question_closeout_ready"]
                and iq_summary["passed_count"] == iq_summary["check_count"]
                and iq_summary["question_dialogue_graph_completion"] >= 98
                and iq_summary["question_policy_training_completion"] >= 92
                and iq_summary["llm_question_context_completion"] >= 92
            ),
            "expected": "IQ5 closeout still supports current M1-M8 projection surfaces",
        },
        {
            "check_id": "interaction_loop_trainable_and_passing",
            "passed": (
                interaction_summary["suite_id"] == "v30.synthetic.interaction_loop"
                and interaction_summary["passed"]
                and interaction_summary["case_count"] == interaction_summary["passed_count"]
                and interaction_summary["case_count"] >= 5
                and interaction_summary["has_question_dialogue_outcome"]
                and interaction_summary["has_interaction_state_machine"]
                and interaction_summary["has_interaction_loop_quality"]
                and interaction_summary["has_question_model_signal_personalization"]
            ),
            "expected": "interaction_loop passes and emits question strategy training signals",
        },
        {
            "check_id": "question_flow_is_personalized_and_role_safe",
            "passed": (
                support_summary["recommendation_count"] >= 5
                and support_summary["user_question_count"] >= 3
                and bool(support_summary["visible_next_question_id"])
                and bool(support_summary["internal_next_question_id"])
                and support_summary["user_diagnostic_key_count"] == 0
                and support_summary["admin_has_interaction_state"]
                and support_summary["admin_has_question_dialogue_graph"]
                and not support_summary["user_internal_next_visible"]
            ),
            "expected": "visible/internal question split and role projection are stable",
        },
        {
            "check_id": "question_training_and_llm_boundaries_locked",
            "passed": (
                support_summary["has_model_signal_question_policy"]
                and not support_summary["model_signal_policy_can_tune_chart_facts"]
                and support_summary["has_interaction_followup_policy"]
                and support_summary["has_adaptive_question_policy"]
                and support_summary["answer_task_type"] == "domain_followup"
                and support_summary["answer_context_pack"] == "BaziDomainContext"
                and not support_summary["domain_chart_fact_mutation_allowed"]
            ),
            "expected": "question training and LLM context support expression/follow-up only",
        },
        {
            "check_id": "core_bazi_chain_remains_authoritative",
            "passed": (
                support_summary["core_fingerprint_unchanged"]
                and support_summary["model_signal_version"] == "v30.model_signal_summary.v1"
                and support_summary["ranked_decision_domain_count"] >= 3
                and support_summary["business_topic_count"] >= 3
                and not support_summary["heavy_validation_required"]
                and not support_summary["pointer_or_fact_write_allowed"]
                and not iq_summary["chart_fact_mutation_allowed"]
                and not iq_summary["policy_pointer_write_allowed"]
            ),
            "expected": "questions support Bazi measurement without replacing deterministic facts",
        },
    ]


def _decision(
    checks: list[Mapping[str, Any]],
    interaction_summary: Mapping[str, Any],
) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    ready = not failed
    return {
        "decision_status": "iq_intelligent_question_support_ready" if ready else "iq_intelligent_question_support_blocked",
        "iq_support_review_ready": ready,
        "question_flow_ready": ready,
        "interaction_loop_case_count": int(interaction_summary.get("case_count", 0) or 0),
        "closeout_check_count": len(checks),
        "passed_closeout_check_count": sum(1 for row in checks if row.get("passed") is True),
        "failed_closeout_check_ids": failed,
        "policy_pointer_promotion_allowed": False,
        "pointer_write_performed": False,
        "chart_fact_mutation_allowed": False,
        "fixed_bazi_verdict_allowed": False,
        "live_llm_required": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "blockers": ["iq_support_review_checks_failed"] if failed else [],
        "rationale": (
            "IQ remains ready as personalized, trainable, role-safe support for the sealed M1-M8 Bazi chain."
            if ready
            else "IQ support review is blocked until the failed M8, IQ5, interaction, role, LLM, or fact-boundary checks pass."
        ),
    }


def _monitoring_baseline(interaction_summary: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "monitoring_id": "iq_intelligent_question_support_steady_state_monitoring",
        "recommended_trigger": "after_question_strategy_change_or_before_release",
        "commands": [
            "python3 scripts/run_iq_intelligent_question_support_review.py --sample-limit 8",
            "python3 scripts/run_synthetic_validation.py --tier interaction_loop",
        ],
        "watched_metrics": {
            "interaction_loop_case_count": int(interaction_summary.get("case_count", 0) or 0),
            "interaction_loop_passed_count": int(interaction_summary.get("passed_count", 0) or 0),
        },
        "full_pytest_required": False,
        "full_518k_required": False,
        "boundary": "monitoring_tracks_iq_drift_without_fact_or_pointer_writes",
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["iq_support_review_ready"]:
        return {
            "next_task": "LLM Bazi Expression Support Review",
            "reason": "IQ support is ready on top of M1-M8; next review LLM expression against bounded Bazi context and role-specific prompts.",
            "full_pytest_required": False,
            "full_518k_required": False,
        }
    return {
        "next_task": "IQ Intelligent Question Support Remediation",
        "reason": "IQ support checks failed; repair question flow, interaction synthetic, role projection, LLM context, or no-write boundaries.",
        "full_pytest_required": False,
        "full_518k_required": False,
    }


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _write_artifact(payload: Mapping[str, Any], artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"{payload['review_id']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path
