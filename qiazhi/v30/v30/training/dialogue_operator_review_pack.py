from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from typing import Any

from v30.config import V30Settings
from v30.training.dialogue_synthetic_replay_queue import run_dialogue_synthetic_replay_queue


DIALOGUE_OPERATOR_REVIEW_PACK_VERSION = "v30.dialogue_operator_review_pack.v1"


def run_dialogue_operator_review_pack(
    *,
    runtime_payloads: Sequence[Mapping[str, Any]] | None = None,
    sample_limit: int = 20,
    run_id: str = "dtc5-dialogue-operator-review-pack",
    persist_review: bool = True,
    settings: V30Settings | None = None,
) -> dict[str, object]:
    queue = run_dialogue_synthetic_replay_queue(
        runtime_payloads=runtime_payloads,
        sample_limit=sample_limit,
        run_id=f"{run_id}:dtc4",
        persist_review=persist_review,
        settings=settings,
    )
    return build_dialogue_operator_review_pack(queue_result=queue, run_id=run_id)


def build_dialogue_operator_review_pack(
    *,
    queue_result: Mapping[str, Any],
    run_id: str = "dtc5-dialogue-operator-review-pack",
) -> dict[str, object]:
    queue = dict(queue_result)
    candidate = _mapping(queue.get("candidate_payload"))
    gate = _mapping(queue.get("gate_result"))
    review = _mapping(gate.get("review_result"))
    loop = _mapping(review.get("loop_result"))
    comparison = _mapping(review.get("question_policy_comparison"))
    aggregate = _mapping(queue.get("aggregate"))
    evidence = _evidence_summary(
        queue=queue,
        gate=gate,
        review=review,
        loop=loop,
        comparison=comparison,
        aggregate=aggregate,
    )
    review_items = _review_items(candidate=candidate, evidence=evidence, aggregate=aggregate)
    risk_register = _risk_register(evidence=evidence, aggregate=aggregate, comparison=comparison)
    operator_actions = _operator_actions(evidence=evidence, risk_register=risk_register)
    checks = _checks(
        queue=queue,
        candidate=candidate,
        evidence=evidence,
        review_items=review_items,
        risk_register=risk_register,
        operator_actions=operator_actions,
    )
    failed = [row for row in checks if row["passed"] is not True]
    ready = not failed
    return {
        "version": DIALOGUE_OPERATOR_REVIEW_PACK_VERSION,
        "run_id": run_id,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if ready else "blocked",
        "task": {
            "task_id": "DTC-5",
            "title": "Dialogue Operator Review Pack",
            "scope": "summarize_dtc1_to_dtc4_dialogue_policy_evidence_for_human_review_without_policy_release",
        },
        "queue_result": queue,
        "candidate_payload": candidate,
        "evidence_summary": evidence,
        "review_items": review_items,
        "risk_register": risk_register,
        "operator_actions": operator_actions,
        "checks": checks,
        "decision": {
            "dialogue_operator_review_pack_ready": ready,
            "decision_status": "dtc5_dialogue_operator_review_pack_ready"
            if ready else "dtc5_dialogue_operator_review_pack_blocked",
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "candidate_id": evidence["candidate_id"],
            "operator_review_required": True,
            "candidate_ready_for_heavy_validation_review": ready,
            "promotion_allowed": False,
            "policy_pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "chart_fact_mutation_allowed": False,
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
        },
        "policy_boundary": {
            "runtime_mutation_allowed": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_promotion_allowed": False,
            "auto_apply_training_allowed": False,
            "operator_review_required": True,
            "heavy_validation_required_before_release": True,
            "blocked_targets": [
                "chart_facts",
                "calendar_conversion",
                "pillar_calculation",
                "online_policy_pointer",
                "auto_promotion",
            ],
            "boundary": "dialogue_operator_review_pack_is_human_review_evidence_not_policy_release",
        },
        "next_mainline_selection": {
            "task_id": "DTC-6" if ready else "DTC-5-FIX",
            "title": "Dialogue Heavy Validation Decision" if ready else "Fix Dialogue Operator Review Pack",
            "reason": "operator_review_pack_has_complete_dtc1_to_dtc4_evidence"
            if ready else "operator_review_pack_checks_failed",
        },
        "boundary": "dtc5_packages_question_strategy_evidence_without_mutating_bazi_truth_or_runtime_policy",
    }


def _evidence_summary(
    *,
    queue: Mapping[str, Any],
    gate: Mapping[str, Any],
    review: Mapping[str, Any],
    loop: Mapping[str, Any],
    comparison: Mapping[str, Any],
    aggregate: Mapping[str, Any],
) -> dict[str, object]:
    loop_decision = _mapping(loop.get("decision"))
    gate_decision = _mapping(gate.get("decision"))
    queue_decision = _mapping(queue.get("decision"))
    sample_summary = _mapping(loop.get("sample_summary"))
    artifact_search = _mapping(gate.get("artifact_search"))
    return {
        "version": "v30.dialogue_operator_review_evidence_summary.v1",
        "candidate_id": str(queue_decision.get("candidate_id") or gate_decision.get("candidate_id") or comparison.get("candidate_id") or ""),
        "dtc1_sample_count": int(sample_summary.get("sample_count") or loop_decision.get("sample_count") or 0),
        "dtc1_policy_candidate_count": int(loop_decision.get("policy_candidate_count") or len(_list(loop.get("policy_candidates")))),
        "dtc2_weighted_delta_count": int(comparison.get("weighted_delta_count") or 0),
        "dtc2_changed_rank_count": int(comparison.get("changed_rank_count") or 0),
        "dtc2_artifact_record_id": str(comparison.get("artifact_record_id") or ""),
        "dtc2_artifact_uri": str(comparison.get("artifact_uri") or ""),
        "dtc3_candidate_deserves_synthetic_replay": bool(gate_decision.get("candidate_deserves_synthetic_replay")),
        "dtc3_artifact_search_count": int(artifact_search.get("count") or 0),
        "dtc4_case_count": int(aggregate.get("case_count") or 0),
        "dtc4_passed_case_count": int(aggregate.get("passed_case_count") or 0),
        "dtc4_pass_ratio": float(aggregate.get("pass_ratio") or 0.0),
        "dtc4_average_weighted_delta_count": float(aggregate.get("average_weighted_delta_count") or 0.0),
        "dtc4_max_rank_disruption_ratio": float(aggregate.get("max_rank_disruption_ratio") or 0.0),
        "dtc4_max_score_delta": float(aggregate.get("max_score_delta") or 0.0),
        "focus_domains": _str_list(aggregate.get("focus_domains")),
        "candidate_domains": _str_list(aggregate.get("candidate_domains")),
        "boundary": "operator_review_evidence_summarizes_question_policy_training_not_chart_facts",
    }


def _review_items(
    *,
    candidate: Mapping[str, Any],
    evidence: Mapping[str, Any],
    aggregate: Mapping[str, Any],
) -> list[dict[str, object]]:
    weights = _mapping(candidate.get("weights"))
    return [
        {
            "item_id": "candidate_scope",
            "title": "候选策略范围",
            "status": "ready",
            "summary": "候选只调整 question policy 权重，用于问题推荐排序，不改变八字事实。",
            "evidence": {
                "weight_buckets": sorted(weights.keys()),
                "candidate_domains": evidence.get("candidate_domains", []),
            },
        },
        {
            "item_id": "training_evidence",
            "title": "训练证据",
            "status": "ready" if int(evidence.get("dtc1_sample_count") or 0) >= 1 else "blocked",
            "summary": "DTC-1 已从对话痕迹提取训练样本和候选方向。",
            "evidence": {
                "sample_count": evidence.get("dtc1_sample_count"),
                "policy_candidate_count": evidence.get("dtc1_policy_candidate_count"),
            },
        },
        {
            "item_id": "comparison_artifact",
            "title": "对照回放 artifact",
            "status": "ready" if evidence.get("dtc2_artifact_uri") else "blocked",
            "summary": "DTC-2 已生成 active vs candidate 的 question policy comparison artifact。",
            "evidence": {
                "weighted_delta_count": evidence.get("dtc2_weighted_delta_count"),
                "changed_rank_count": evidence.get("dtc2_changed_rank_count"),
                "artifact_record_id": evidence.get("dtc2_artifact_record_id"),
                "artifact_uri": evidence.get("dtc2_artifact_uri"),
            },
        },
        {
            "item_id": "batch_replay_stability",
            "title": "批量回放稳定性",
            "status": "ready" if aggregate.get("stable_enough_for_operator_review") is True else "blocked",
            "summary": "DTC-4 已在多个合成场景中验证候选有稳定的可测影响。",
            "evidence": {
                "case_count": evidence.get("dtc4_case_count"),
                "passed_case_count": evidence.get("dtc4_passed_case_count"),
                "pass_ratio": evidence.get("dtc4_pass_ratio"),
                "max_rank_disruption_ratio": evidence.get("dtc4_max_rank_disruption_ratio"),
            },
        },
    ]


def _risk_register(
    *,
    evidence: Mapping[str, Any],
    aggregate: Mapping[str, Any],
    comparison: Mapping[str, Any],
) -> list[dict[str, object]]:
    rank_ratio = float(evidence.get("dtc4_max_rank_disruption_ratio") or 0.0)
    score_delta = float(evidence.get("dtc4_max_score_delta") or 0.0)
    return [
        {
            "risk_id": "rank_disruption",
            "severity": "medium" if rank_ratio >= 0.5 else "low",
            "status": "review_required",
            "summary": "候选会改变部分问题排序，需要人工确认是否符合产品交互目标。",
            "observed": {
                "max_rank_disruption_ratio": rank_ratio,
                "dtc2_changed_rank_count": evidence.get("dtc2_changed_rank_count"),
                "top_question_changed": bool(comparison.get("top_question_changed")),
            },
            "mitigation": "进入重放/人工审核，不直接发布。",
        },
        {
            "risk_id": "score_delta",
            "severity": "medium" if score_delta >= 0.25 else "low",
            "status": "review_required",
            "summary": "候选对推荐分数有可测影响，需要继续观察是否过拟合。",
            "observed": {"max_score_delta": score_delta},
            "mitigation": "DTC-6 之前不得写 policy pointer。",
        },
        {
            "risk_id": "release_boundary",
            "severity": "low",
            "status": "controlled",
            "summary": "当前证据包不允许发布策略或修改命盘事实。",
            "observed": {
                "stable_enough_for_operator_review": aggregate.get("stable_enough_for_operator_review"),
                "pass_ratio": evidence.get("dtc4_pass_ratio"),
            },
            "mitigation": "继续要求 synthetic all / 518K sample / 人工确认。",
        },
    ]


def _operator_actions(
    *,
    evidence: Mapping[str, Any],
    risk_register: Sequence[Mapping[str, Any]],
) -> list[dict[str, object]]:
    high_risk_count = sum(1 for row in risk_register if row.get("severity") == "high")
    return [
        {
            "action_id": "approve_for_heavy_validation_review",
            "label": "进入重验证审核",
            "enabled": high_risk_count == 0 and float(evidence.get("dtc4_pass_ratio") or 0.0) >= 1.0,
            "writes_policy_pointer": False,
            "mutates_chart_facts": False,
            "description": "允许进入 DTC-6 的重验证决策，但不发布策略。",
        },
        {
            "action_id": "hold_for_more_runtime_samples",
            "label": "等待更多真实对话样本",
            "enabled": True,
            "writes_policy_pointer": False,
            "mutates_chart_facts": False,
            "description": "保留候选，继续收集真实运行时对话样本。",
        },
        {
            "action_id": "reject_candidate",
            "label": "退回候选",
            "enabled": True,
            "writes_policy_pointer": False,
            "mutates_chart_facts": False,
            "description": "退回当前候选，后续由 DTC-1 重新提取训练方向。",
        },
    ]


def _checks(
    *,
    queue: Mapping[str, Any],
    candidate: Mapping[str, Any],
    evidence: Mapping[str, Any],
    review_items: Sequence[Mapping[str, Any]],
    risk_register: Sequence[Mapping[str, Any]],
    operator_actions: Sequence[Mapping[str, Any]],
) -> list[dict[str, object]]:
    queue_decision = _mapping(queue.get("decision"))
    return [
        _check(
            "dtc4_queue_ready",
            queue.get("status") == "completed"
            and queue_decision.get("candidate_ready_for_operator_review") is True,
            {
                "queue_status": queue.get("status"),
                "decision_status": queue_decision.get("decision_status"),
                "candidate_ready_for_operator_review": queue_decision.get("candidate_ready_for_operator_review"),
            },
        ),
        _check(
            "evidence_pack_complete",
            bool(evidence.get("candidate_id"))
            and int(evidence.get("dtc1_sample_count") or 0) >= 1
            and int(evidence.get("dtc2_weighted_delta_count") or 0) > 0
            and float(evidence.get("dtc4_pass_ratio") or 0.0) >= 1.0,
            {
                "candidate_id": evidence.get("candidate_id"),
                "dtc1_sample_count": evidence.get("dtc1_sample_count"),
                "dtc2_weighted_delta_count": evidence.get("dtc2_weighted_delta_count"),
                "dtc4_pass_ratio": evidence.get("dtc4_pass_ratio"),
            },
        ),
        _check(
            "review_items_are_ready",
            bool(review_items) and all(row.get("status") == "ready" for row in review_items),
            {"review_item_count": len(review_items), "blocked_items": [row.get("item_id") for row in review_items if row.get("status") != "ready"]},
        ),
        _check(
            "risks_are_registered",
            len(risk_register) >= 3 and all(row.get("status") in {"review_required", "controlled"} for row in risk_register),
            {"risk_count": len(risk_register)},
        ),
        _check(
            "operator_actions_do_not_release_policy",
            bool(operator_actions)
            and all(row.get("writes_policy_pointer") is False for row in operator_actions)
            and all(row.get("mutates_chart_facts") is False for row in operator_actions)
            and candidate.get("policy_pointer_promotion_allowed") is False,
            {
                "action_count": len(operator_actions),
                "candidate_policy_pointer_promotion_allowed": candidate.get("policy_pointer_promotion_allowed"),
            },
        ),
    ]


def _check(check_id: str, passed: bool, observed: Mapping[str, object]) -> dict[str, object]:
    return {"check_id": check_id, "passed": bool(passed), "observed": dict(observed)}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _str_list(value: object) -> list[str]:
    return [str(row) for row in value] if isinstance(value, list) else []
