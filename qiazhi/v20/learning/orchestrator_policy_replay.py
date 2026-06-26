from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from v20.learning.orchestrator_policy_versioning import (
    BASELINE_POLICY_VERSION,
    build_orchestrator_policy_version_candidate,
)
from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


ProgressCallback = Callable[[str], None]


def build_orchestrator_policy_replay_report(
    *,
    policy_version_candidate: dict[str, object] | None = None,
    store: LocalJsonlStore | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    candidate = policy_version_candidate or build_orchestrator_policy_version_candidate(store=store, progress=progress)
    comparisons = _comparisons(candidate)
    _emit(progress, f"orchestrator policy replay comparisons: {len(comparisons)}")
    return {
        "version": "v20.orchestrator_policy_replay_report.v1",
        "status": "ready_for_fast_iteration" if comparisons else "not_enough_data",
        "baseline_policy_version": candidate.get("baseline_policy_version", BASELINE_POLICY_VERSION),
        "candidate_policy_version": candidate.get("candidate_policy_version", ""),
        "comparison_count": len(comparisons),
        "comparisons": comparisons,
        "replay_result": _replay_result(comparisons),
        "runtime_mutation": False,
        "guardrails": [
            "REPLAY_IS_FAST_ITERATION_POLICY_DIFF",
            "AUTO_ITERATION_REPLAY_RESULT",
            "RUNTIME_ROLLOUT_REQUIRES_VERSION_POINTER",
            "CORE_FACTS_REMAIN_DETERMINISTIC",
        ],
    }


def write_orchestrator_policy_replay_artifact(
    *,
    store: LocalJsonlStore | None = None,
    output_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    report = build_orchestrator_policy_replay_report(store=storage, progress=progress)
    directory = output_dir or storage.runtime_dir / "training" / "orchestrator_policy_replay"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"orchestrator_policy_replay_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.orchestrator_policy_replay_artifact_write.v1",
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


def read_orchestrator_policy_replay_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "orchestrator_policy_replay") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.orchestrator_policy_replay_artifact_status.v1",
            "status": "not_built",
            "latest_path": str(latest_path),
            "runtime_mutation": False,
        }
    return json.loads(latest_path.read_text(encoding="utf-8")) | {"runtime_mutation": False}


def _comparisons(candidate: dict[str, object]) -> list[dict[str, object]]:
    payload = candidate.get("policy_payload", {})
    if not isinstance(payload, dict):
        return []
    rows = []
    for policy_key in (
        "mainline_arbitration_weight_policy",
        "question_focus_policy",
        "brain_memory_policy",
        "question_source_graph_quality_policy",
    ):
        policy_rows = payload.get(policy_key, ())
        if not isinstance(policy_rows, list):
            continue
        for row in policy_rows:
            if not isinstance(row, dict):
                continue
            rows.append({
                "policy_key": policy_key,
                "candidate_id": row.get("candidate_id", ""),
                "baseline_action": "keep_current_runtime_policy",
                "candidate_action": row.get("suggested_action", ""),
                "expected_effect": _expected_effect(policy_key, str(row.get("suggested_action", ""))),
                "requires_human_review": False,
                "runtime_allowed": bool(row.get("runtime_allowed", False)),
            })
    return rows


def _expected_effect(policy_key: str, action: str) -> str:
    if policy_key == "mainline_arbitration_weight_policy":
        return "may_change_future_mainline_ranking_after_approval"
    if policy_key == "question_focus_policy":
        return "may_change_future_question_order_after_approval"
    if policy_key == "brain_memory_policy":
        return "may_change_future_review_boundary_after_approval"
    if policy_key == "question_source_graph_quality_policy":
        return "may_change_source_quality_weight_after_approval"
    return action or "review_only"


def _replay_result(comparisons: list[dict[str, object]]) -> dict[str, object]:
    return {
        "status": "auto_fast_track_ready" if comparisons else "no_candidate_policy",
        "eligible_for_runtime": bool(comparisons),
        "blocking_gate": "",
        "comparison_count": len(comparisons),
    }


def _emit(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(message)
