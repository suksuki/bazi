from __future__ import annotations

from typing import Any

from v20.learning.question_dag_policy_replay import build_question_dag_policy_replay_report
from v20.storage.local_jsonl import LocalJsonlStore


MIN_DAG_REPLAY_COMPARISONS = 4
MIN_DAG_OFFLINE_SCORE_AVERAGE = 0.5


def build_question_dag_policy_promotion_gate(
    *,
    replay_report: dict[str, object] | None = None,
    store: LocalJsonlStore | None = None,
    runtime_rollout_switch: bool = False,
) -> dict[str, Any]:
    replay = replay_report or build_question_dag_policy_replay_report(store=store)
    impact = replay.get("impact_summary", {}) if isinstance(replay.get("impact_summary"), dict) else {}
    comparison_count = int(replay.get("comparison_count", 0) or 0)
    score_average = float(impact.get("offline_score_average", 0.0) or 0.0)
    risk_count = int(impact.get("risk_count", 0) or 0)
    checks = (
        _check("candidate_replay_ready", replay.get("status") == "ready_for_review"),
        _check("minimum_comparisons", comparison_count >= MIN_DAG_REPLAY_COMPARISONS),
        _check("offline_score_average", score_average >= MIN_DAG_OFFLINE_SCORE_AVERAGE),
        _check("no_replay_risk", risk_count == 0),
        _check("candidate_win", impact.get("candidate_win") is True),
        _check("runtime_rollout_switch", runtime_rollout_switch, "" if runtime_rollout_switch else "runtime_rollout_switch_disabled_until_question_dag_pointer"),
    )
    failures = tuple(row["check_key"] for row in checks if not row["ok"])
    return {
        "version": "v20.question_dag_policy_promotion_gate.v1",
        "status": "blocked" if failures else "eligible",
        "eligible_for_runtime": not failures,
        "policy_key": replay.get("policy_key", ""),
        "comparison_count": comparison_count,
        "offline_score_average": score_average,
        "risk_count": risk_count,
        "checks": checks,
        "failure_count": len(failures),
        "failures": failures,
        "blocking_gate": failures[0] if failures else "",
        "runtime_mutation": False,
        "guardrails": [
            "QUESTION_DAG_PROMOTION_GATE_IS_READ_ONLY",
            "QUESTION_DAG_PROMOTION_REQUIRES_REPLAY",
            "NO_RUNTIME_POINTER_WRITE_FROM_GATE",
            "NO_CORE_FACT_MUTATION",
            "NO_RULE_TRUTH_MUTATION",
        ],
    }


def _check(check_key: str, ok: bool, detail: str = "") -> dict[str, Any]:
    return {
        "check_key": check_key,
        "ok": bool(ok),
        "detail": detail,
    }
