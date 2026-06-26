from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from v20.learning.orchestrator_policy_candidates import build_orchestrator_policy_candidate_report
from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


ProgressCallback = Callable[[str], None]
POLICY_FAMILY = "orchestrator_policy_bundle"
BASELINE_POLICY_VERSION = "v20.orchestrator_policy.baseline.v1"


def build_orchestrator_policy_version_candidate(
    *,
    candidate_report: dict[str, object] | None = None,
    store: LocalJsonlStore | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    report = candidate_report or build_orchestrator_policy_candidate_report(store=store, progress=progress)
    candidates = [row for row in report.get("candidates", ()) if isinstance(row, dict)]
    bundle_hash = _hash_json(candidates)
    version_id = f"v20.orchestrator_policy.candidate.{bundle_hash}"
    _emit(progress, f"orchestrator policy version candidate: {version_id}")
    return {
        "version": "v20.orchestrator_policy_version_candidate.v1",
        "status": "ready_for_replay" if candidates else "not_enough_data",
        "policy_family": POLICY_FAMILY,
        "baseline_policy_version": BASELINE_POLICY_VERSION,
        "candidate_policy_version": version_id,
        "candidate_count": len(candidates),
        "candidate_hash": bundle_hash,
        "source_report_version": report.get("version", ""),
        "source_review_artifact": report.get("review_artifact", {}),
        "source_policy_observability_input_summary": report.get("policy_observability_input_summary", {}),
        "source_candidate_quality_summary": report.get("candidate_quality_summary", {}),
        "source_quality_scoring_policy": report.get("quality_scoring_policy", {}),
        "policy_payload": {
            "mainline_arbitration_weight_policy": _payload_rows(candidates, "mainline_arbitration_weight_policy"),
            "question_focus_policy": _payload_rows(candidates, "question_focus_policy"),
            "brain_memory_policy": _payload_rows(candidates, "brain_memory_policy"),
            "question_source_graph_quality_policy": _payload_rows(
                candidates,
                "question_source_graph_quality_policy",
            ),
        },
        "promotion_status": "auto_fast_track_locked_candidate",
        "runtime_allowed": bool(candidates),
        "runtime_mutation": False,
        "guardrails": [
            "POLICY_VERSION_CANDIDATE_IS_FAST_TRACK_MATERIAL",
            "AUTO_ITERATION_VERSION_CANDIDATE",
            "RUNTIME_ROLLOUT_REQUIRES_VERSION_POINTER",
            "CORE_FACTS_REMAIN_DETERMINISTIC",
        ],
    }


def write_orchestrator_policy_version_candidate_artifact(
    *,
    store: LocalJsonlStore | None = None,
    output_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    report = build_orchestrator_policy_version_candidate(store=storage, progress=progress)
    directory = output_dir or storage.runtime_dir / "training" / "orchestrator_policy_versions"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_path = directory / f"orchestrator_policy_version_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.orchestrator_policy_version_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report["status"],
        "candidate_policy_version": report["candidate_policy_version"],
        "candidate_count": report["candidate_count"],
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "NO_RUNTIME_POLICY_PROMOTION",
        ],
    }


def read_orchestrator_policy_version_candidate_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "orchestrator_policy_versions") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.orchestrator_policy_version_artifact_status.v1",
            "status": "not_built",
            "latest_path": str(latest_path),
            "runtime_mutation": False,
        }
    return json.loads(latest_path.read_text(encoding="utf-8")) | {"runtime_mutation": False}


def _payload_rows(candidates: list[dict[str, object]], candidate_type: str) -> list[dict[str, object]]:
    rows = []
    for row in candidates:
        if row.get("candidate_type") != candidate_type:
            continue
        rows.append({
            "candidate_id": row.get("candidate_id", ""),
            "suggested_action": row.get("suggested_action", ""),
            "status": row.get("status", ""),
            "next_gate": row.get("next_gate", ""),
            "runtime_allowed": bool(row.get("runtime_allowed", False)),
            "source_key": row.get("source_key", ""),
            "primary_mainline_key": row.get("primary_mainline_key", ""),
            "supporting_direction": row.get("supporting_direction", ""),
            "domain": row.get("domain", ""),
            "average_strength": row.get("average_strength", 0),
            "support_ratio": row.get("support_ratio", 0),
            "sample_count": row.get("sample_count", 0),
            "average_graph_score": row.get("average_graph_score", 0),
            "average_question_score": row.get("average_question_score", 0),
            "source_recommendation_key": row.get("source_recommendation_key", ""),
            "source_recommendation_type": row.get("source_recommendation_type", ""),
            "quality_rank": row.get("quality_rank", 0),
            "quality_score": row.get("quality_score", 0),
            "quality_band": row.get("quality_band", ""),
            "quality_policy_version": row.get("quality_policy_version", ""),
        })
    return rows


def _hash_json(value: object) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def _emit(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(message)
