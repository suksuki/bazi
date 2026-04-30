from __future__ import annotations

from typing import Any, Dict, List

from v19.synthetic_validation.domain_route_backfill import (
    build_p61_domain_route_backfill_candidates,
    build_p61_domain_route_backfill_eval_dataset,
    run_p61_domain_route_backfill_regression,
)
from v19.synthetic_validation.silent_evolution import run_p59_silent_evolution_cycle, run_p60_domain_route_eval


P62_SILENT_TRAINING_LEDGER_VERSION = "v19.p62.silent_training_ledger.v1"
P62_SILENT_TRAINING_REGRESSION_VERSION = "v19.p62.silent_training_ledger_regression.v1"

P62_GUARDRAILS = [
    "P62_SILENT_TRAINING_LEDGER",
    "TRAINING_SIGNAL_ONLY",
    "DETERMINISTIC_EVAL_SIGNAL",
    "NO_CORE_RULE_TRUTH_UPDATE",
    "NO_USER_FEEDBACK_DIRECT_RULE_UPDATE",
    "NO_RUNTIME_RULE_ACTIVATION",
    "NO_RESULT_MUTATION",
    "NO_ANSWER_MUTATION",
    "NO_BLACK_BOX_CORE_INFERENCE",
]


def build_p62_silent_training_ledger() -> Dict[str, Any]:
    cycle = run_p59_silent_evolution_cycle()
    domain_eval = run_p60_domain_route_eval()
    registry = build_p61_domain_route_backfill_candidates()
    dataset = build_p61_domain_route_backfill_eval_dataset()
    regression = run_p61_domain_route_backfill_regression()
    entries = [
        _entry(
            "p62.ledger.p59.shadow_score",
            "P59_SILENT_EVOLUTION_SYSTEM",
            cycle.get("status") == "silent_shadow_pass",
            {
                "score": (cycle.get("scorecard") or {}).get("score"),
                "score_tier": (cycle.get("scorecard") or {}).get("score_tier"),
                "proposal_count": len(cycle.get("tuning_proposals") or []),
            },
            "parameter_tuning_signal",
        ),
        _entry(
            "p62.ledger.p60.domain_route",
            "P60_DOMAIN_ROUTE_EVAL",
            domain_eval.get("status") == "pass" and int((domain_eval.get("summary") or {}).get("direct_domain_hit_count") or 0) == 8,
            {
                "sample_count": (domain_eval.get("summary") or {}).get("sample_count"),
                "direct_domain_hit_count": (domain_eval.get("summary") or {}).get("direct_domain_hit_count"),
                "domain_candidate_gap_count": len(domain_eval.get("domain_candidate_gaps") or []),
            },
            "route_eval_regression_signal",
        ),
        _entry(
            "p62.ledger.p61.route_backfill",
            "P61_DOMAIN_ROUTE_BACKFILL",
            regression.get("status") == "pass",
            {
                "candidate_count": (registry.get("summary") or {}).get("candidate_count"),
                "sample_count": (dataset.get("summary") or {}).get("sample_count"),
                "regression_status": regression.get("status"),
            },
            "route_wrapper_regression_signal",
        ),
    ]
    failures = [entry for entry in entries if entry.get("status") != "pass"]
    status = "silent_training_ledger_ready" if not failures else "blocked"
    return {
        "ok": status == "silent_training_ledger_ready",
        "version": P62_SILENT_TRAINING_LEDGER_VERSION,
        "status": status,
        "runtime_scope": "silent_learning_signal_ledger_only_no_runtime_mutation",
        "summary": {
            "entry_count": len(entries),
            "passed": sum(1 for entry in entries if entry.get("status") == "pass"),
            "failed": len(failures),
            "training_signal_count": len(entries),
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
        },
        "learning_permissions": {
            "allowed": [
                "question_routing_weight_review",
                "eval_sampling_priority_review",
                "draft_priority_review",
                "shadow_dataset_expansion",
            ],
            "blocked": [
                "core_rule_truth_update",
                "production_rule_activation",
                "user_feedback_direct_rule_update",
                "answer_conclusion_update",
                "domain_prediction_update",
            ],
        },
        "entries": entries,
        "tuning_queue": _tuning_queue(cycle, domain_eval, registry, dataset, regression),
        "source_summaries": {
            "p59": cycle.get("run_ledger_entry") or {},
            "p60": domain_eval.get("summary") or {},
            "p61_registry": registry.get("summary") or {},
            "p61_eval_dataset": dataset.get("summary") or {},
            "p61_regression": regression.get("summary") or {},
        },
        "failures": failures,
        "guardrails": P62_GUARDRAILS,
    }


def run_p62_silent_training_ledger_regression() -> Dict[str, Any]:
    ledger = build_p62_silent_training_ledger()
    failures: List[Dict[str, Any]] = []
    summary = ledger.get("summary") or {}
    if ledger.get("status") != "silent_training_ledger_ready":
        failures.append(_failure("ledger_not_ready", "P62 requires P59/P60/P61 signals to pass."))
    if int(summary.get("engine_enabled_count") or 0) != 0 or int(summary.get("answer_mutation_count") or 0) != 0:
        failures.append(_failure("mutation_not_allowed", "Silent training ledger cannot enable engine or mutate answers."))
    if summary.get("runtime_mutation") is True:
        failures.append(_failure("runtime_mutation_not_allowed", "P62 must remain report-only."))
    blocked = set((ledger.get("learning_permissions") or {}).get("blocked") or [])
    required_blocked = {"core_rule_truth_update", "production_rule_activation", "user_feedback_direct_rule_update"}
    if not required_blocked <= blocked:
        failures.append(_failure("learning_permission_guardrail_missing", "P62 must block direct rule learning paths."))
    for entry in ledger.get("entries") or []:
        if entry.get("training_use") not in {"parameter_tuning_signal", "route_eval_regression_signal", "route_wrapper_regression_signal"}:
            failures.append(_failure("unknown_training_use", str(entry.get("entry_id") or "")))
    status = "pass" if not failures else "fail"
    return {
        "ok": status == "pass",
        "version": P62_SILENT_TRAINING_REGRESSION_VERSION,
        "status": status,
        "runtime_scope": "silent_training_ledger_regression_no_runtime_mutation",
        "summary": {
            "entry_count": len(ledger.get("entries") or []),
            "failure_count": len(failures),
            "tuning_queue_count": len(ledger.get("tuning_queue") or []),
            "engine_enabled_count": 0,
            "answer_mutation_count": 0,
            "runtime_mutation": False,
        },
        "ledger": ledger,
        "failures": failures,
        "guardrails": P62_GUARDRAILS,
    }


def _entry(entry_id: str, stage: str, passed: bool, metrics: Dict[str, Any], training_use: str) -> Dict[str, Any]:
    return {
        "entry_id": entry_id,
        "source_stage": stage,
        "status": "pass" if passed else "fail",
        "training_use": training_use,
        "metrics": metrics,
        "runtime_mutation": False,
        "answer_mutation": False,
        "engine_enabled": False,
    }


def _tuning_queue(
    cycle: Dict[str, Any],
    domain_eval: Dict[str, Any],
    registry: Dict[str, Any],
    dataset: Dict[str, Any],
    regression: Dict[str, Any],
) -> List[Dict[str, Any]]:
    queue = [
        {
            "proposal_id": "p62.tuning.keep_domain_safety_bridge_in_route_eval",
            "proposal_type": "question_routing_weight_review",
            "risk": "low",
            "reason": "Relationship and health direct route candidates now resolve through domain_safety_bridge.",
            "decision": "silent_proposal_only",
            "runtime_mutation": False,
        },
        {
            "proposal_id": "p62.tuning.promote_p61_samples_to_recurring_eval",
            "proposal_type": "eval_sampling_priority_review",
            "risk": "low",
            "reason": "P61 route-only samples should remain in recurring domain route regression.",
            "decision": "silent_proposal_only",
            "runtime_mutation": False,
        },
    ]
    if len(domain_eval.get("domain_candidate_gaps") or []) == 0 and regression.get("status") == "pass":
        queue.append(
            {
                "proposal_id": "p62.tuning.close_p60_domain_gap_watch",
                "proposal_type": "draft_priority_review",
                "risk": "low",
                "reason": "P60 relationship/health gaps are resolved by P61 route wrappers.",
                "decision": "silent_proposal_only",
                "runtime_mutation": False,
            }
        )
    if int((registry.get("summary") or {}).get("candidate_count") or 0) > 0 and int((dataset.get("summary") or {}).get("sample_count") or 0) > 0:
        queue.append(
            {
                "proposal_id": "p62.tuning.expand_domain_safety_negative_samples",
                "proposal_type": "shadow_dataset_expansion",
                "risk": "medium",
                "reason": "Add more negative health and relationship samples before any domain rule conversion.",
                "decision": "silent_proposal_only",
                "runtime_mutation": False,
            }
        )
    if cycle.get("status") != "silent_shadow_pass":
        queue.append(
            {
                "proposal_id": "p62.tuning.block_until_p59_passes",
                "proposal_type": "framework_adapter_review",
                "risk": "high",
                "reason": "P59 must pass before training signals can be trusted.",
                "decision": "blocked",
                "runtime_mutation": False,
            }
        )
    return queue


def _failure(failure_type: str, detail: str) -> Dict[str, str]:
    return {"failure_type": failure_type, "detail": detail}
