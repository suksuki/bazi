from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v20.corpus.artifacts import (
    read_corpus_artifact_status,
    read_corpus_cluster_model,
    read_corpus_coverage_summary,
    read_corpus_training_artifacts,
)
from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


CORPUS_RUNTIME_POINTER_VERSION = "v20.corpus_runtime_pointer.v1"
CORPUS_ACTIVE_POINTER_VERSION = "v20.corpus_runtime_active_pointer.v1"
CORPUS_BASELINE_VERSION = "v20.corpus_policy.baseline.v1"
CORPUS_POINTER_AUDIT_LEDGER = "corpus_runtime_pointer_audit"
CORPUS_POINTER_RELATIVE_PATH = "training/corpus_policy_versions/active_pointer.json"


def build_corpus_runtime_pointer(*, store: LocalJsonlStore | None = None) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    status = read_corpus_artifact_status()
    coverage = read_corpus_coverage_summary()
    clusters = read_corpus_cluster_model()
    training = read_corpus_training_artifacts()
    candidate = _candidate_policy(status=status, coverage=coverage, clusters=clusters, training=training)
    active_pointer = _read_active_pointer(storage)
    candidate_version = str(candidate.get("candidate_policy_version", ""))
    active_version = _active_version(candidate_version, active_pointer)
    runtime_applied = bool(candidate_version and active_version == candidate_version and candidate.get("eligible_for_runtime"))
    return {
        "version": CORPUS_RUNTIME_POINTER_VERSION,
        "status": "candidate_active" if runtime_applied else ("candidate_ready" if candidate.get("eligible_for_runtime") else "blocked"),
        "policy_family": "corpus_precompute",
        "active_policy_version": active_version,
        "candidate_policy_version": candidate_version,
        "rollback_policy_version": CORPUS_BASELINE_VERSION,
        "active_pointer_source": str(active_pointer.get("source", "")) if active_pointer else "baseline",
        "candidate": candidate,
        "policy_payload": candidate.get("policy_payload", {}) if runtime_applied else {},
        "runtime_applied": runtime_applied,
        "runtime_allowed": runtime_applied,
        "blocking_gate": "" if runtime_applied else str(candidate.get("blocking_gate", "")),
        "runtime_mutation": False,
        "guardrails": [
            "CORPUS_RUNTIME_POINTER_READ_ONLY",
            "CORPUS_POINTER_USES_VERSIONED_ARTIFACTS",
            "NO_DESTINY_TRUTH_LABEL",
            "NO_RULE_ACTIVATION",
        ],
    }


def write_corpus_runtime_pointer_activate_candidate(
    *,
    source_role: str,
    reason: str = "",
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    if source_role not in {"admin", "lab", "system"}:
        raise ValueError(f"Unsupported corpus pointer activation source_role: {source_role}")
    storage = store or local_jsonl_store_from_env()
    status = read_corpus_artifact_status()
    coverage = read_corpus_coverage_summary()
    clusters = read_corpus_cluster_model()
    training = read_corpus_training_artifacts()
    candidate = _candidate_policy(status=status, coverage=coverage, clusters=clusters, training=training)
    candidate_version = str(candidate.get("candidate_policy_version", ""))
    if not candidate.get("eligible_for_runtime") or not candidate_version:
        return {
            "version": "v20.corpus_runtime_pointer_activation_result.v1",
            "status": "blocked_by_machine_gate",
            "candidate_policy_version": candidate_version,
            "active_policy_version": CORPUS_BASELINE_VERSION,
            "candidate": candidate,
            "runtime_mutation": False,
            "guardrails": [
                "CORPUS_MACHINE_GATE_REQUIRED",
                "NO_POINTER_WRITE_ON_BLOCKED_ACTIVATION",
                "NO_ARTIFACT_BUILD_DURING_ACTIVATION",
            ],
        }
    previous = _read_active_pointer(storage)
    previous_active = str(previous.get("active_policy_version", "")) or CORPUS_BASELINE_VERSION
    pointer = {
        "version": CORPUS_ACTIVE_POINTER_VERSION,
        "status": "candidate_active",
        "active_policy_version": candidate_version,
        "candidate_policy_version": candidate_version,
        "previous_active_policy_version": previous_active,
        "rollback_policy_version": CORPUS_BASELINE_VERSION,
        "source": "admin_corpus_optimizer_activate_candidate",
        "source_role": source_role,
        "reason": reason[:240],
        "candidate_summary": _candidate_summary(candidate),
        "policy_payload": candidate.get("policy_payload", {}),
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
        "guardrails": [
            "CORPUS_ACTIVATION_WRITES_VERSION_POINTER_ONLY",
            "NO_DESTINY_TRUTH_LABEL",
            "NO_RULE_ACTIVATION",
        ],
    }
    path = _write_active_pointer(storage, pointer)
    audit = _append_pointer_audit(storage, "v20.corpus_runtime_pointer_activation_audit.v1", pointer)
    return {
        "version": "v20.corpus_runtime_pointer_activation_result.v1",
        "status": "candidate_active",
        "active_pointer_path": str(path),
        "active_policy_version": candidate_version,
        "candidate_policy_version": candidate_version,
        "previous_active_policy_version": previous_active,
        "candidate": candidate,
        "audit": audit,
        "runtime_mutation": True,
        "guardrails": [
            "CORPUS_POINTER_AUDIT_APPEND_ONLY",
            "CORPUS_POLICY_CAN_ROLL_BACK_TO_BASELINE",
            "RUNTIME_CONSUMES_VERSIONED_CORPUS_POLICY",
        ],
    }


def _candidate_policy(
    *,
    status: dict[str, object],
    coverage: dict[str, object],
    clusters: dict[str, object],
    training: dict[str, object],
) -> dict[str, object]:
    payload = _policy_payload(status=status, coverage=coverage, clusters=clusters, training=training) if _gate_ready(status=status, coverage=coverage, clusters=clusters, training=training) else {}
    blocking_gate = "" if payload else _blocking_gate(status=status, coverage=coverage, clusters=clusters, training=training)
    version_seed = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    candidate_version = f"v20.corpus_policy.candidate.{_hash(version_seed)}" if payload else ""
    return {
        "version": "v20.corpus_runtime_policy_candidate.v1",
        "status": "ready" if payload else "blocked",
        "candidate_policy_version": candidate_version,
        "eligible_for_runtime": bool(payload),
        "feature_threshold_policy_count": len(payload.get("feature_threshold_policy", ())) if isinstance(payload.get("feature_threshold_policy"), list) else 0,
        "similarity_tag_weight_policy_count": len(payload.get("similarity_tag_weight_policy", ())) if isinstance(payload.get("similarity_tag_weight_policy"), list) else 0,
        "blocking_gate": blocking_gate,
        "policy_payload": payload,
        "source_reports": {
            "corpus_artifact_status": status.get("status", "not_built"),
            "coverage_status": coverage.get("status", "not_built"),
            "cluster_status": clusters.get("status", "not_built"),
            "training_status": training.get("status", "not_built"),
            "run_id": status.get("run_id", coverage.get("run_id", "")),
        },
        "runtime_mutation": False,
        "guardrails": [
            "CORPUS_CANDIDATE_FROM_COMPLETED_ARTIFACTS",
            "SIMILARITY_POLICY_REWEIGHTS_RETRIEVAL_ONLY",
            "NO_CORPUS_CONTENT_IN_POINTER",
        ],
    }


def _gate_ready(
    *,
    status: dict[str, object],
    coverage: dict[str, object],
    clusters: dict[str, object],
    training: dict[str, object],
) -> bool:
    return (
        status.get("status") == "completed"
        and coverage.get("status") == "ready"
        and clusters.get("status") == "ready"
        and training.get("status") == "ready"
        and int(coverage.get("case_count", 0) or 0) > 0
    )


def _policy_payload(
    *,
    status: dict[str, object],
    coverage: dict[str, object],
    clusters: dict[str, object],
    training: dict[str, object],
) -> dict[str, object]:
    return {
        "feature_threshold_policy": _feature_threshold_rows(coverage),
        "coverage_prior_policy": _coverage_prior_rows(coverage),
        "similarity_tag_weight_policy": _similarity_weight_rows(training),
        "corpus_shard_quality_policy": [_shard_quality_row(status, coverage, clusters)],
    }


def _feature_threshold_rows(coverage: dict[str, object]) -> list[dict[str, object]]:
    distributions = coverage.get("distributions", {}) if isinstance(coverage.get("distributions"), dict) else {}
    feature_domains = distributions.get("feature_domains", {}) if isinstance(distributions.get("feature_domains"), dict) else {}
    total = max(1, int(coverage.get("case_count", 0) or 0))
    rows = []
    for domain, count in sorted(feature_domains.items()):
        ratio = int(count or 0) / total
        rows.append(
            {
                "domain": str(domain),
                "coverage_ratio": round(ratio, 4),
                "feature_threshold_delta": round(min(0.04, 0.008 + ratio * 0.018), 4),
                "source": "corpus_coverage_summary",
            }
        )
    return rows


def _coverage_prior_rows(coverage: dict[str, object]) -> list[dict[str, object]]:
    averages = coverage.get("averages", {}) if isinstance(coverage.get("averages"), dict) else {}
    return [
        {
            "prior_key": key,
            "average_value": float(value or 0.0),
            "prior_delta": round(min(0.04, float(value or 0.0) * 0.004), 4),
            "source": "corpus_coverage_summary",
        }
        for key, value in sorted(averages.items())
    ]


def _similarity_weight_rows(training: dict[str, object]) -> list[dict[str, object]]:
    manifest = training.get("similarity_manifest", {}) if isinstance(training.get("similarity_manifest"), dict) else {}
    tag_sources = manifest.get("tag_sources", ()) if isinstance(manifest.get("tag_sources", ()), list) else []
    base = {
        "feature_ids": 0.16,
        "portrait_domains": 0.08,
        "relation_types": 0.1,
        "question_keys": 0.06,
        "knowledge_ids": 0.06,
        "mainline_domains": 0.12,
    }
    return [
        {
            "tag_prefix": str(tag_source),
            "weight_delta": round(base.get(str(tag_source), 0.04), 4),
            "source": "corpus_similarity_manifest",
        }
        for tag_source in tag_sources
    ]


def _shard_quality_row(status: dict[str, object], coverage: dict[str, object], clusters: dict[str, object]) -> dict[str, object]:
    case_count = int(coverage.get("case_count", 0) or status.get("processed", 0) or 0)
    cluster_count = int(coverage.get("cluster_count", 0) or clusters.get("cluster_count", 0) or 0)
    return {
        "run_id": str(status.get("run_id", coverage.get("run_id", ""))),
        "case_count": case_count,
        "cluster_count": cluster_count,
        "quality_score": round(min(1.0, (case_count / max(1, case_count)) * (1.0 if cluster_count else 0.5)), 4),
        "source": "corpus_artifact_status+cluster_model",
    }


def _blocking_gate(
    *,
    status: dict[str, object],
    coverage: dict[str, object],
    clusters: dict[str, object],
    training: dict[str, object],
) -> str:
    gates = []
    if status.get("status") != "completed":
        gates.append("corpus_artifact_status_not_completed")
    if coverage.get("status") != "ready":
        gates.append("corpus_coverage_summary_not_ready")
    if clusters.get("status") != "ready":
        gates.append("corpus_cluster_model_not_ready")
    if training.get("status") != "ready":
        gates.append("corpus_training_artifacts_not_ready")
    if int(coverage.get("case_count", 0) or 0) <= 0:
        gates.append("corpus_coverage_has_no_cases")
    return ",".join(gates) or "corpus_policy_payload_empty"


def _candidate_summary(candidate: dict[str, object]) -> dict[str, object]:
    return {
        "candidate_policy_version": candidate.get("candidate_policy_version", ""),
        "feature_threshold_policy_count": candidate.get("feature_threshold_policy_count", 0),
        "similarity_tag_weight_policy_count": candidate.get("similarity_tag_weight_policy_count", 0),
        "blocking_gate": candidate.get("blocking_gate", ""),
    }


def _active_version(candidate_version: str, active_pointer: dict[str, object]) -> str:
    active = str(active_pointer.get("active_policy_version", "")) if active_pointer else ""
    if active == candidate_version or active == CORPUS_BASELINE_VERSION:
        return active or CORPUS_BASELINE_VERSION
    return CORPUS_BASELINE_VERSION


def _read_active_pointer(store: LocalJsonlStore) -> dict[str, object]:
    path = store.runtime_dir / CORPUS_POINTER_RELATIVE_PATH
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict) or payload.get("version") != CORPUS_ACTIVE_POINTER_VERSION:
        return {}
    return dict(payload) | {"source_path": path}


def _write_active_pointer(store: LocalJsonlStore, payload: dict[str, object]) -> Path:
    path = store.runtime_dir / CORPUS_POINTER_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _append_pointer_audit(store: LocalJsonlStore, event_version: str, pointer: dict[str, object]) -> dict[str, object]:
    return store.append_record(
        CORPUS_POINTER_AUDIT_LEDGER,
        {
            "version": event_version,
            "source_role": pointer.get("source_role", ""),
            "active_policy_version": pointer.get("active_policy_version", ""),
            "candidate_policy_version": pointer.get("candidate_policy_version", ""),
            "previous_active_policy_version": pointer.get("previous_active_policy_version", ""),
            "rollback_policy_version": pointer.get("rollback_policy_version", ""),
            "reason": pointer.get("reason", ""),
            "runtime_mutation": False,
            "guardrails": [
                "CORPUS_POINTER_AUDIT_APPEND_ONLY",
                "NO_SECRET_VALUES_RENDERED",
            ],
        },
    )


def _hash(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]
