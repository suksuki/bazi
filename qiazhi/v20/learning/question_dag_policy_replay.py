from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v20.learning.question_dag_training import build_question_dag_training_report
from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


REPLAY_VERSION = "v20.question_dag_policy_replay_report.v1"


def build_question_dag_policy_replay_report(
    *,
    question_dag_training_report: dict[str, object] | None = None,
    store: LocalJsonlStore | None = None,
) -> dict[str, Any]:
    training = question_dag_training_report or build_question_dag_training_report(store=store)
    policy = training.get("candidate_policy", {}) if isinstance(training.get("candidate_policy"), dict) else {}
    comparisons = _comparisons(training, policy)
    impact = _impact_summary(comparisons)
    result = _replay_result(training, impact)
    return {
        "version": REPLAY_VERSION,
        "status": "ready_for_review" if comparisons else "not_enough_data",
        "source_training_version": training.get("version", ""),
        "source_training_status": training.get("status", ""),
        "policy_key": policy.get("policy_key", ""),
        "comparison_count": len(comparisons),
        "comparisons": comparisons,
        "impact_summary": impact,
        "replay_result": result,
        "runtime_mutation": False,
        "guardrails": [
            "QUESTION_DAG_REPLAY_IS_OFFLINE_ONLY",
            "QUESTION_DAG_REPLAY_DOES_NOT_PROMOTE_POLICY",
            "NO_RUNTIME_POINTER_MUTATION",
            "NO_CORE_FACT_MUTATION",
            "NO_RULE_TRUTH_MUTATION",
        ],
    }


def write_question_dag_policy_replay_artifact(
    *,
    store: LocalJsonlStore | None = None,
    output_dir: Path | None = None,
) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    report = build_question_dag_policy_replay_report(store=storage)
    directory = output_dir or storage.runtime_dir / "training" / "question_dag_policy_replay"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"question_dag_policy_replay_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.question_dag_policy_replay_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report["status"],
        "comparison_count": report["comparison_count"],
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "NO_RUNTIME_POLICY_PROMOTION",
        ],
    }


def read_question_dag_policy_replay_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "question_dag_policy_replay") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.question_dag_policy_replay_artifact_status.v1",
            "status": "not_built",
            "latest_path": str(latest_path),
            "runtime_mutation": False,
        }
    return json.loads(latest_path.read_text(encoding="utf-8")) | {"runtime_mutation": False}


def _comparisons(training: dict[str, object], policy: dict[str, object]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    coherence = training.get("coherence_report", {}) if isinstance(training.get("coherence_report"), dict) else {}
    rows.append({
        "comparison_key": "coherence_gate",
        "baseline_action": "keep_current_question_dag_policy",
        "candidate_action": "apply_candidate_if_coherence_passes",
        "candidate_effect": "validates_candidate_dag_before_runtime_pointer",
        "offline_score": 1.0 if coherence.get("status") == "pass" else -1.0,
        "risk_count": int(coherence.get("failure_count", 0) or 0),
        "basis": f"coherence status {coherence.get('status', '')}; failures {coherence.get('failure_count', 0)}",
        "runtime_allowed": False,
    })
    stage_coverage = training.get("stage_coverage", {}) if isinstance(training.get("stage_coverage"), dict) else {}
    coverage_ratio = float(stage_coverage.get("coverage_ratio", 0.0) or 0.0)
    rows.append({
        "comparison_key": "stage_coverage",
        "baseline_action": "keep_current_question_dag_policy",
        "candidate_action": "apply_candidate_if_stage_coverage_complete",
        "candidate_effect": "checks_training_stage_coverage",
        "offline_score": 1.0 if coverage_ratio >= 1.0 else -0.5,
        "risk_count": 0 if coverage_ratio >= 1.0 else 1,
        "basis": f"coverage ratio {coverage_ratio}",
        "runtime_allowed": False,
    })
    transitions = policy.get("synthetic_transition_policy", ())
    transition_count = len(transitions) if isinstance(transitions, tuple | list) else 0
    rows.append({
        "comparison_key": "synthetic_transition_support",
        "baseline_action": "keep_current_question_dag_policy",
        "candidate_action": "apply_supported_synthetic_transitions_after_pointer",
        "candidate_effect": "may_change_next_question_stage_priority_after_pointer",
        "offline_score": 0.5 if transition_count > 0 else -0.5,
        "risk_count": 0 if transition_count > 0 else 1,
        "basis": f"{transition_count} transition rows",
        "runtime_allowed": False,
    })
    review_policy = policy.get("question_review_policy", {}) if isinstance(policy.get("question_review_policy"), dict) else {}
    review_recommendations = review_policy.get("training_recommendations", ())
    review_count = len(review_recommendations) if isinstance(review_recommendations, tuple | list) else 0
    rows.append({
        "comparison_key": "question_review_recommendations",
        "baseline_action": "ignore_review_training_for_dag_policy",
        "candidate_action": "attach_review_training_recommendations_to_dag_policy",
        "candidate_effect": "may_change_question_template_or_stage_priority_after_replay",
        "offline_score": 0.5 if review_count > 0 else 0.0,
        "risk_count": 0,
        "basis": f"{review_count} review recommendations",
        "runtime_allowed": False,
    })
    return rows


def _impact_summary(comparisons: list[dict[str, Any]]) -> dict[str, Any]:
    score_total = round(sum(float(row.get("offline_score", 0.0) or 0.0) for row in comparisons), 3)
    risk_total = sum(int(row.get("risk_count", 0) or 0) for row in comparisons)
    return {
        "version": "v20.question_dag_policy_replay_impact_summary.v1",
        "comparison_count": len(comparisons),
        "offline_score_total": score_total,
        "offline_score_average": round(score_total / max(1, len(comparisons)), 3),
        "risk_count": risk_total,
        "candidate_win": bool(comparisons and score_total > 0 and risk_total == 0),
        "runtime_allowed": False,
    }


def _replay_result(training: dict[str, object], impact: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "review_required" if training.get("status") == "ready" else "blocked_by_training_status",
        "eligible_for_runtime": False,
        "blocking_gate": "question_dag_runtime_pointer_not_enabled",
        "candidate_win": impact.get("candidate_win", False),
        "offline_score_average": impact.get("offline_score_average", 0.0),
        "risk_count": impact.get("risk_count", 0),
    }
