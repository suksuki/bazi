from __future__ import annotations

from typing import Any

CENTRAL_BRAIN_PHASE2_DISTRIBUTION_GATE_VERSION = "v30.central_brain_phase2_distribution_gate.v1"


def build_central_brain_phase2_distribution_gate(
    *,
    replay_gate: dict[str, Any],
    sample_result: dict[str, Any],
    shard_result: dict[str, Any] | None = None,
    min_sample_cases: int = 1,
    require_shard: bool = False,
) -> dict[str, Any]:
    shard_result = shard_result or {}
    checks = [
        _check(
            "synthetic_replay_gate_eligible",
            replay_gate.get("promotion_signal") == "eligible",
            {"promotion_signal": replay_gate.get("promotion_signal"), "status": replay_gate.get("status")},
        ),
        _check(
            "sample_518k_eligible",
            _signal(sample_result) == "eligible",
            {"promotion_signal": _signal(sample_result), "mode": sample_result.get("mode")},
        ),
        _check(
            "sample_518k_case_count",
            _case_count(sample_result) >= min_sample_cases,
            {"case_count": _case_count(sample_result), "min_sample_cases": min_sample_cases},
        ),
        _check(
            "sample_518k_failure_free",
            not _failures(sample_result),
            {"failure_count": len(_failures(sample_result))},
        ),
        _check(
            "shard_518k_required",
            (not require_shard) or bool(shard_result),
            {"require_shard": require_shard, "has_shard_result": bool(shard_result)},
        ),
        _check(
            "shard_518k_eligible",
            (not require_shard and not shard_result) or _signal(shard_result) == "eligible",
            {"promotion_signal": _signal(shard_result), "mode": shard_result.get("mode")},
        ),
        _check(
            "chart_fact_immutability",
            replay_gate.get("chart_fact_mutation_allowed") is False
            and sample_result.get("chart_fact_mutation_allowed", False) is False
            and shard_result.get("chart_fact_mutation_allowed", False) is False,
            {
                "replay_chart_fact_mutation_allowed": replay_gate.get("chart_fact_mutation_allowed"),
                "sample_chart_fact_mutation_allowed": sample_result.get("chart_fact_mutation_allowed", False),
                "shard_chart_fact_mutation_allowed": shard_result.get("chart_fact_mutation_allowed", False),
            },
        ),
    ]
    failed = [row for row in checks if row["passed"] is False]
    eligible = not failed
    return {
        "version": CENTRAL_BRAIN_PHASE2_DISTRIBUTION_GATE_VERSION,
        "status": "passed" if eligible else "blocked",
        "promotion_signal": "eligible" if eligible else "blocked",
        "decision": {
            "phase2_distribution_gate_ready": eligible,
            "check_count": len(checks),
            "passed_check_count": len(checks) - len(failed),
            "failed_check_ids": [str(row["check_id"]) for row in failed],
            "full_518k_required": False,
            "chart_fact_mutation_allowed": False,
            "policy_pointer_write_allowed": False,
        },
        "checks": checks,
        "distribution_518k": {
            "sample": _compact_518k_result(sample_result),
            "shard": _compact_518k_result(shard_result) if shard_result else {},
        },
        "chart_fact_mutation_allowed": False,
        "boundary": "central_brain_phase2_distribution_gate_validates_518k_distribution_without_mutating_chart_facts_or_pointer",
    }


def _compact_518k_result(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "run_id": str(payload.get("run_id") or ""),
        "mode": str(payload.get("mode") or ""),
        "case_count": _case_count(payload),
        "promotion_signal": _signal(payload),
        "shard_ids": payload.get("shard_ids", []),
        "artifact_uri": payload.get("artifact_uri"),
        "artifact_record_id": payload.get("artifact_record_id"),
        "failure_count": len(_failures(payload)),
    }


def _check(check_id: str, passed: bool, details: dict[str, Any]) -> dict[str, Any]:
    return {"check_id": check_id, "passed": bool(passed), "details": details}


def _signal(payload: dict[str, Any]) -> str:
    return str(payload.get("promotion_signal") or "")


def _case_count(payload: dict[str, Any]) -> int:
    try:
        return int(payload.get("case_count") or 0)
    except (TypeError, ValueError):
        return 0


def _failures(payload: dict[str, Any]) -> list[Any]:
    failures = payload.get("failure_clusters", [])
    return failures if isinstance(failures, list) else []
