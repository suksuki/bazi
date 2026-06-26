from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

from v30.validation.central_brain_session_replay import run_central_brain_session_replay


CENTRAL_BRAIN_FAILURE_ROUTING_VERSION = "v30.brain_failure_route.v1"

FAILURE_ROUTE_MATRIX = {
    "birth_input_boundary": {
        "route_id": "route.m1_m2_fact_boundary",
        "module_target": "M1/M2 fact boundary",
        "task_family": "focused_core_fact_boundary_review",
        "default_action": "inspect BirthInput/calendar/chart-fact boundary",
    },
    "chart_fact_mutation": {
        "route_id": "route.m1_m2_fact_boundary",
        "module_target": "M1/M2 fact boundary",
        "task_family": "focused_core_fact_boundary_review",
        "default_action": "block mutation and compare deterministic fact fingerprint",
    },
    "m3_knowledge_gap": {
        "route_id": "route.m3_evidence_rule_path_gap",
        "module_target": "M3 evidence/rule/path gap",
        "task_family": "focused_m3_coverage_review",
        "default_action": "inspect K/R/P unit, rule, counter-evidence, or path coverage",
    },
    "model_signal_drift": {
        "route_id": "route.m4_m5_calibration",
        "module_target": "M4/M5 calibration",
        "task_family": "targeted_model_signal_ranked_decision_review",
        "default_action": "review model-signal bands and ranked-decision candidate weights",
    },
    "ranked_decision_drift": {
        "route_id": "route.m4_m5_calibration",
        "module_target": "M4/M5 calibration",
        "task_family": "targeted_model_signal_ranked_decision_review",
        "default_action": "review ranked decision candidate score floors and evidence links",
    },
    "practical_reading_contract": {
        "route_id": "route.m6_practical_reading_contract",
        "module_target": "M6 practical reading contract",
        "task_family": "focused_practical_reading_contract_review",
        "default_action": "inspect calculation basis, domain contracts, and blocked claims",
    },
    "projection_leak": {
        "route_id": "route.m8_projection_leak",
        "module_target": "M8 projection leak",
        "task_family": "focused_projection_visibility_review",
        "default_action": "inspect role visibility and customer leak policy",
    },
    "question_strategy": {
        "route_id": "route.question_strategy",
        "module_target": "question strategy",
        "task_family": "question_policy_strategy_review",
        "default_action": "review visible/internal next-question strategy and answered suppression",
    },
    "hidden_factor_feedback": {
        "route_id": "route.hidden_factor_feedback",
        "module_target": "hidden-factor feedback",
        "task_family": "hidden_factor_feedback_review",
        "default_action": "inspect feedback-conditioned amplifier state and denial/conflict boundaries",
    },
    "training_candidate": {
        "route_id": "route.training_candidate",
        "module_target": "training candidate",
        "task_family": "training_candidate_validation_review",
        "default_action": "quarantine or validate policy candidate without pointer write",
    },
    "release_full_validation": {
        "route_id": "route.release_full_validation",
        "module_target": "release/full validation",
        "task_family": "explicit_release_or_full_freeze_review",
        "default_action": "request explicit major validation decision",
    },
}


def run_central_brain_failure_routing() -> dict[str, Any]:
    replay = run_central_brain_session_replay()
    return build_central_brain_failure_routing(
        bt2_session_replay=replay,
        failure_events=_default_failure_events(),
    )


def build_central_brain_failure_routing(
    *,
    bt2_session_replay: Mapping[str, Any],
    failure_events: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    executed_at = datetime.now(timezone.utc)
    bt2_summary = _bt2_summary(bt2_session_replay)
    events = [_normalize_failure_event(row) for row in failure_events or []]
    route_items = [_route_item(row) for row in events]
    task_queue = _task_queue(route_items)
    checks = _routing_checks(bt2_summary, events, route_items, task_queue)
    decision = _decision(checks, route_items)
    return {
        "version": CENTRAL_BRAIN_FAILURE_ROUTING_VERSION,
        "executed_at": executed_at.isoformat(),
        "status": "completed" if decision["brain_failure_routing_ready"] else "blocked",
        "decision": decision,
        "bt2_summary": bt2_summary,
        "failure_route_matrix": _route_matrix(),
        "failure_events": events,
        "route_items": route_items,
        "task_queue": task_queue,
        "routing_checks": checks,
        "policy_boundary": {
            "operator_plan_only": True,
            "runtime_mutation_allowed": False,
            "chart_fact_mutation_allowed": False,
            "db_or_redis_direct_write_allowed": False,
            "policy_pointer_write_allowed": False,
            "auto_apply_training_allowed": False,
            "full_pytest_run_allowed_by_default": False,
            "full_518k_run_allowed_by_default": False,
            "boundary": "bt3_failure_routing_is_diagnostic_task_queue_not_runtime_mutation",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "bt3_routes_brain_failures_to_focused_tasks_without_mutation",
    }


def _default_failure_events() -> list[dict[str, Any]]:
    return [
        {
            "event_id": "bt3_projection_leak_sample",
            "failure_type": "projection_leak",
            "severity": "high",
            "summary": "Customer projection exposes diagnostic or training fields.",
        },
        {
            "event_id": "bt3_question_strategy_sample",
            "failure_type": "question_strategy",
            "severity": "medium",
            "summary": "Visible next question does not follow answered user context.",
        },
        {
            "event_id": "bt3_hidden_factor_feedback_sample",
            "failure_type": "hidden_factor_feedback",
            "severity": "medium",
            "summary": "Hidden-factor feedback needs conflict/denial route review.",
        },
        {
            "event_id": "bt3_training_candidate_sample",
            "failure_type": "training_candidate",
            "severity": "medium",
            "summary": "Policy candidate requires validation or quarantine.",
        },
        {
            "event_id": "bt3_release_full_validation_sample",
            "failure_type": "release_full_validation",
            "severity": "review",
            "summary": "Full validation requires explicit release/full-freeze decision.",
        },
    ]


def _bt2_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = payload.get("decision", {})
    decision = decision if isinstance(decision, Mapping) else {}
    return {
        "version": str(payload.get("version") or ""),
        "status": str(payload.get("status") or ""),
        "decision_status": str(decision.get("decision_status") or ""),
        "central_brain_session_replay_ready": bool(decision.get("central_brain_session_replay_ready")),
        "full_pytest_required": bool(decision.get("full_pytest_required")),
        "full_518k_required": bool(decision.get("full_518k_required")),
        "policy_pointer_promotion_allowed": bool(decision.get("policy_pointer_promotion_allowed")),
        "chart_fact_mutation_allowed": bool(decision.get("chart_fact_mutation_allowed")),
    }


def _normalize_failure_event(row: Mapping[str, Any]) -> dict[str, Any]:
    failure_type = str(row.get("failure_type") or row.get("type") or "unmapped")
    route = FAILURE_ROUTE_MATRIX.get(failure_type, FAILURE_ROUTE_MATRIX["m3_knowledge_gap"])
    return {
        "event_id": str(row.get("event_id") or f"bt3_failure_{failure_type}"),
        "failure_type": failure_type,
        "severity": str(row.get("severity") or "review"),
        "summary": str(row.get("summary") or route["default_action"]),
        "source": str(row.get("source") or "central_brain_failure_routing"),
        "chart_fact_mutation_requested": bool(row.get("chart_fact_mutation_requested", False)),
        "pointer_write_requested": bool(row.get("pointer_write_requested", False)),
        "requires_full_pytest": bool(row.get("requires_full_pytest", False)),
        "requires_full_518k": bool(row.get("requires_full_518k", False)),
    }


def _route_item(event: Mapping[str, Any]) -> dict[str, Any]:
    route = FAILURE_ROUTE_MATRIX.get(str(event["failure_type"]), FAILURE_ROUTE_MATRIX["m3_knowledge_gap"])
    return {
        "queue_item_id": f"{event['event_id']}::{route['route_id']}",
        "event_id": event["event_id"],
        "failure_type": event["failure_type"],
        "route_id": route["route_id"],
        "module_target": route["module_target"],
        "task_family": route["task_family"],
        "routing_action": route["default_action"],
        "severity": event["severity"],
        "status": "queued_for_operator_review",
        "operator_plan_only": True,
        "reopen_all_core_modules": False,
        "chart_fact_mutation_allowed": False,
        "pointer_write_allowed": False,
        "runtime_mutation_allowed": False,
        "requires_explicit_major_validation": bool(
            event["requires_full_pytest"]
            or event["requires_full_518k"]
            or event["failure_type"] == "release_full_validation"
        ),
    }


def _task_queue(route_items: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[Mapping[str, Any]]] = {}
    for item in route_items:
        grouped.setdefault(str(item["module_target"]), []).append(item)
    return [
        {
            "module_target": module_target,
            "queued_item_count": len(items),
            "route_ids": sorted({str(item["route_id"]) for item in items}),
            "task_families": sorted({str(item["task_family"]) for item in items}),
            "queue_status": "ready_for_operator_review",
            "operator_plan_only": True,
            "runtime_mutation_allowed": False,
            "chart_fact_mutation_allowed": False,
            "pointer_write_allowed": False,
        }
        for module_target, items in sorted(grouped.items())
    ]


def _routing_checks(
    bt2_summary: Mapping[str, Any],
    events: Sequence[Mapping[str, Any]],
    route_items: Sequence[Mapping[str, Any]],
    task_queue: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    expected_targets = {
        "M1/M2 fact boundary",
        "M3 evidence/rule/path gap",
        "M4/M5 calibration",
        "M6 practical reading contract",
        "M8 projection leak",
        "question strategy",
        "hidden-factor feedback",
        "training candidate",
        "release/full validation",
    }
    matrix_targets = {str(row["module_target"]) for row in FAILURE_ROUTE_MATRIX.values()}
    queued_targets = {str(row["module_target"]) for row in route_items}
    return [
        {
            "check_id": "bt2_session_replay_ready",
            "passed": (
                bt2_summary["version"] == "v30.central_brain_session_replay.v1"
                and bt2_summary["central_brain_session_replay_ready"]
                and bt2_summary["decision_status"] == "bt2_central_brain_session_replay_ready"
            ),
            "expected": "BT2 long-session replay is ready",
        },
        {
            "check_id": "route_matrix_covers_required_targets",
            "passed": expected_targets.issubset(matrix_targets),
            "expected": "route matrix covers all required BT3 target families",
        },
        {
            "check_id": "sample_events_route_to_diagnostic_queue",
            "passed": bool(events) and len(route_items) == len(events) and bool(task_queue),
            "expected": "failure events become diagnostic queue items",
        },
        {
            "check_id": "key_support_failures_are_routed",
            "passed": {
                "M8 projection leak",
                "question strategy",
                "hidden-factor feedback",
                "training candidate",
                "release/full validation",
            }.issubset(queued_targets),
            "expected": "BT3 default route samples cover support-system failure families",
        },
        {
            "check_id": "routing_is_operator_plan_only",
            "passed": (
                all(item["operator_plan_only"] and not item["runtime_mutation_allowed"] for item in route_items)
                and all(row["operator_plan_only"] and not row["runtime_mutation_allowed"] for row in task_queue)
            ),
            "expected": "routing output is an operator plan, not runtime mutation",
        },
        {
            "check_id": "no_chart_pointer_or_heavy_validation_by_default",
            "passed": (
                not bt2_summary["chart_fact_mutation_allowed"]
                and not bt2_summary["policy_pointer_promotion_allowed"]
                and not bt2_summary["full_pytest_required"]
                and not bt2_summary["full_518k_required"]
                and not any(row["chart_fact_mutation_requested"] for row in events)
                and not any(row["pointer_write_requested"] for row in events)
                and all(not item["chart_fact_mutation_allowed"] and not item["pointer_write_allowed"] for item in route_items)
            ),
            "expected": "BT3 does not authorize chart mutation, pointer write, or default heavy validation",
        },
    ]


def _decision(checks: list[Mapping[str, Any]], route_items: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if not row.get("passed")]
    ready = not failed
    return {
        "brain_failure_routing_ready": ready,
        "decision_status": "bt3_brain_failure_routing_ready" if ready else "bt3_brain_failure_routing_blocked",
        "routing_check_count": len(checks),
        "passed_routing_check_count": sum(1 for row in checks if row.get("passed")),
        "failed_check_ids": failed,
        "queued_route_count": len(route_items),
        "focused_task_required": bool(route_items),
        "central_brain_completion": 97 if ready else 94,
        "blockers": ["brain_failure_routing_checks_failed"] if failed else [],
        "external_release_ready": False,
        "full_pytest_required": False,
        "full_518k_required": False,
        "policy_pointer_promotion_allowed": False,
        "chart_fact_mutation_allowed": False,
        "rationale": (
            "Brain failure routing is ready as a diagnostic task queue contract."
            if ready
            else "BT3 cannot complete until routing blockers are repaired."
        ),
    }


def _route_matrix() -> list[dict[str, Any]]:
    return [
        {"failure_type": failure_type, **route}
        for failure_type, route in sorted(FAILURE_ROUTE_MATRIX.items())
    ]


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision["brain_failure_routing_ready"]:
        return {
            "task_id": "BT4",
            "title": "Training System Closeout Gate",
            "selected_track": "brain_training_synthetic_completion",
            "scope": [
                "verify training signals, candidates, artifacts, pointers, rollback, and lineage",
                "keep policy changes validation-gated",
                "preserve chart-fact boundaries",
            ],
        }
    return {
        "task_id": "BT3-FR",
        "title": "Brain Failure Routing Failure Review",
        "selected_track": "brain_training_synthetic_completion",
        "scope": [
            "inspect failed BT3 routing checks",
            "repair route matrix or task queue contract",
            "keep pointer/release disabled while blocked",
        ],
    }
