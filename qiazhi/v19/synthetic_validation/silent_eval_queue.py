from __future__ import annotations

from typing import Any, Dict, List

from v19.synthetic_validation.silent_training_ledger import build_p62_silent_training_ledger


P63_SILENT_EVAL_QUEUE_VERSION = "v19.p63.silent_eval_queue.v1"
P63_SILENT_EVAL_QUEUE_REGRESSION_VERSION = "v19.p63.silent_eval_queue_regression.v1"

P63_BLOCKED_ACTIONS = [
    "core_rule_truth_update",
    "production_rule_activation",
    "user_feedback_direct_rule_update",
    "answer_conclusion_update",
    "domain_prediction_update",
]

P63_GUARDRAILS = [
    "P63_SILENT_EVAL_QUEUE",
    "EVAL_QUEUE_ONLY",
    "CHECKPOINTED_REPORT_ONLY",
    "NO_CORE_RULE_TRUTH_UPDATE",
    "NO_USER_FEEDBACK_DIRECT_RULE_UPDATE",
    "NO_RUNTIME_RULE_ACTIVATION",
    "NO_RESULT_MUTATION",
    "NO_ANSWER_MUTATION",
    "NO_DOMAIN_RESULT_PREDICTION",
]


def build_p63_silent_eval_queue() -> Dict[str, Any]:
    ledger = build_p62_silent_training_ledger()
    source_queue = [dict(row) for row in ledger.get("tuning_queue") or [] if isinstance(row, dict)]
    queue_items = [_queue_item(row, index) for index, row in enumerate(source_queue, start=1)]
    failures = []
    if ledger.get("status") != "silent_training_ledger_ready":
        failures.append(_failure("p62_ledger_not_ready", "P63 requires P62 silent training ledger."))
    status = "silent_eval_queue_ready" if not failures else "blocked"
    return {
        "ok": status == "silent_eval_queue_ready",
        "version": P63_SILENT_EVAL_QUEUE_VERSION,
        "status": status,
        "runtime_scope": "silent_eval_queue_definition_only_no_runtime_mutation",
        "summary": {
            "queue_item_count": len(queue_items),
            "ready_count": sum(1 for item in queue_items if item.get("status") == "queued"),
            "shadow_required_count": sum(1 for item in queue_items if item.get("status") == "shadow_required"),
            "blocked_count": sum(1 for item in queue_items if item.get("status") == "blocked"),
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
            "by_task_type": _count_by(queue_items, "task_type"),
        },
        "queue_items": queue_items,
        "checkpoint_policy": {
            "checkpoint_key_fields": ["queue_item_id", "source_proposal_id", "runner", "expected_invariants"],
            "resume_policy": "rerun_failed_or_stale_report_only_items",
            "write_policy": "report_only_no_runtime_or_rule_db_write",
        },
        "source_ledger_summary": ledger.get("summary") or {},
        "failures": failures,
        "guardrails": P63_GUARDRAILS,
    }


def run_p63_silent_eval_queue_regression() -> Dict[str, Any]:
    queue = build_p63_silent_eval_queue()
    failures = list(queue.get("failures") or [])
    items = [dict(row) for row in queue.get("queue_items") or [] if isinstance(row, dict)]
    if queue.get("status") != "silent_eval_queue_ready":
        failures.append(_failure("queue_not_ready", "P63 queue must be ready before downstream scheduling."))
    if len(items) < 4:
        failures.append(_failure("queue_item_count_too_low", "P63 must carry the current P62 tuning queue."))
    required_runners = {
        "v19.synthetic_validation.silent_evolution.run_p60_domain_route_eval",
        "v19.synthetic_validation.domain_route_backfill.run_p61_domain_route_backfill_regression",
    }
    observed_runners = {str(item.get("runner") or "") for item in items}
    if not required_runners <= observed_runners:
        failures.append(_failure("required_runner_missing", ",".join(sorted(required_runners - observed_runners))))
    for item in items:
        failures.extend(_item_failures(item))
    status = "pass" if not failures else "fail"
    return {
        "ok": status == "pass",
        "version": P63_SILENT_EVAL_QUEUE_REGRESSION_VERSION,
        "status": status,
        "runtime_scope": "silent_eval_queue_regression_no_runtime_mutation",
        "summary": {
            "queue_item_count": len(items),
            "failure_count": len(failures),
            "ready_count": sum(1 for item in items if item.get("status") == "queued"),
            "shadow_required_count": sum(1 for item in items if item.get("status") == "shadow_required"),
            "blocked_count": sum(1 for item in items if item.get("status") == "blocked"),
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
        },
        "queue": queue,
        "failures": failures,
        "guardrails": P63_GUARDRAILS,
    }


def _queue_item(proposal: Dict[str, Any], index: int) -> Dict[str, Any]:
    proposal_type = str(proposal.get("proposal_type") or "")
    risk = str(proposal.get("risk") or "medium")
    mapping = _task_mapping(proposal_type)
    status = "shadow_required" if risk == "medium" else "queued"
    if risk == "high" or proposal.get("decision") == "blocked":
        status = "blocked"
    return {
        "queue_item_id": f"p63.eval.{index:02d}.{proposal_type or 'unknown'}",
        "source_proposal_id": str(proposal.get("proposal_id") or ""),
        "proposal_type": proposal_type,
        "task_type": mapping["task_type"],
        "status": status,
        "priority": _priority_for(proposal_type, risk),
        "risk": risk,
        "runner": mapping["runner"],
        "cadence": mapping["cadence"],
        "input_scope": mapping["input_scope"],
        "expected_invariants": mapping["expected_invariants"],
        "allowed_actions": ["record_eval_result", "record_checkpoint", "open_silent_tuning_proposal"],
        "blocked_actions": list(P63_BLOCKED_ACTIONS),
        "rollback_policy": "drop_queue_item_no_runtime_state_to_revert",
        "runtime_mutation": False,
        "answer_mutation": False,
        "engine_enabled": False,
    }


def _task_mapping(proposal_type: str) -> Dict[str, Any]:
    if proposal_type == "question_routing_weight_review":
        return {
            "task_type": "route_weight_shadow_review",
            "runner": "v19.synthetic_validation.silent_evolution.run_p60_domain_route_eval",
            "cadence": "on_rule_graph_change_or_daily_shadow",
            "input_scope": ["relationship_structure", "health_structure", "domain_safety_bridge"],
            "expected_invariants": {
                "direct_domain_hit_count": 8,
                "domain_candidate_gap_count": 0,
                "runtime_mutation": False,
            },
        }
    if proposal_type == "eval_sampling_priority_review":
        return {
            "task_type": "recurring_route_wrapper_regression",
            "runner": "v19.synthetic_validation.domain_route_backfill.run_p61_domain_route_backfill_regression",
            "cadence": "on_knowledge_or_rule_candidate_change",
            "input_scope": ["p36.relationship", "p36.health", "p61_route_only_wrappers"],
            "expected_invariants": {
                "candidate_count": 6,
                "sample_count": 24,
                "runtime_mutation": False,
            },
        }
    if proposal_type == "draft_priority_review":
        return {
            "task_type": "domain_gap_watch_closeout",
            "runner": "v19.synthetic_validation.silent_evolution.run_p60_domain_route_eval",
            "cadence": "weekly_shadow_or_on_route_candidate_change",
            "input_scope": ["P60_domain_candidate_gaps"],
            "expected_invariants": {
                "domain_candidate_gap_count": 0,
                "direct_domain_hit_count": 8,
                "runtime_mutation": False,
            },
        }
    if proposal_type == "shadow_dataset_expansion":
        return {
            "task_type": "domain_safety_negative_sample_expansion",
            "runner": "v19.synthetic_validation.domain_route_backfill.build_p61_domain_route_backfill_eval_dataset",
            "cadence": "manual_shadow_batch_before_rule_conversion",
            "input_scope": ["relationship_negative_samples", "health_negative_samples"],
            "expected_invariants": {
                "minimum_current_sample_count": 24,
                "forbidden_text_failure_count": 0,
                "runtime_mutation": False,
            },
        }
    return {
        "task_type": "generic_silent_review",
        "runner": "manual_review_only",
        "cadence": "manual",
        "input_scope": ["unknown"],
        "expected_invariants": {"runtime_mutation": False},
    }


def _priority_for(proposal_type: str, risk: str) -> str:
    if risk == "high":
        return "blocked"
    if proposal_type in {"question_routing_weight_review", "eval_sampling_priority_review"}:
        return "high"
    if risk == "medium":
        return "medium"
    return "normal"


def _item_failures(item: Dict[str, Any]) -> List[Dict[str, str]]:
    failures = []
    if item.get("runtime_mutation") is True or item.get("answer_mutation") is True or item.get("engine_enabled") is True:
        failures.append(_failure("queue_item_mutation_not_allowed", str(item.get("queue_item_id") or "")))
    blocked = set(item.get("blocked_actions") or [])
    required = {"core_rule_truth_update", "production_rule_activation", "user_feedback_direct_rule_update"}
    if not required <= blocked:
        failures.append(_failure("queue_item_blocked_actions_missing", str(item.get("queue_item_id") or "")))
    if not item.get("runner") or not item.get("expected_invariants"):
        failures.append(_failure("queue_item_contract_incomplete", str(item.get("queue_item_id") or "")))
    if item.get("status") not in {"queued", "shadow_required", "blocked"}:
        failures.append(_failure("queue_item_status_invalid", str(item.get("queue_item_id") or "")))
    return failures


def _count_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        value = str(row.get(key) or "unknown")
        counts[value] = counts.get(value, 0) + 1
    return counts


def _failure(failure_type: str, detail: str) -> Dict[str, str]:
    return {"failure_type": failure_type, "detail": detail}
