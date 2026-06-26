from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env
from v20.validation.structure_dynamics_corpus_distribution import read_latest_structure_dynamics_corpus_distribution
from v20.validation.structure_dynamics_synthetic import run_structure_dynamics_synthetic_suite


STRUCTURE_DYNAMICS_RUNTIME_POINTER_VERSION = "v20.structure_dynamics_runtime_pointer.v1"
STRUCTURE_DYNAMICS_ACTIVE_POINTER_VERSION = "v20.structure_dynamics_runtime_active_pointer.v1"
STRUCTURE_DYNAMICS_BASELINE_VERSION = "v20.structure_dynamics_policy.baseline.v1"
STRUCTURE_DYNAMICS_POINTER_AUDIT_LEDGER = "structure_dynamics_runtime_pointer_audit"
STRUCTURE_DYNAMICS_POINTER_RELATIVE_PATH = "training/structure_dynamics_policy_versions/active_pointer.json"


def build_structure_dynamics_runtime_pointer(*, store: LocalJsonlStore | None = None) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    report = run_structure_dynamics_synthetic_suite()
    candidate = _candidate_policy(report=report)
    active_pointer = _read_active_pointer(storage)
    candidate_version = str(candidate.get("candidate_policy_version", ""))
    active_version = _active_version(candidate_version, active_pointer)
    runtime_applied = bool(candidate_version and active_version == candidate_version and candidate.get("eligible_for_runtime"))
    return {
        "version": STRUCTURE_DYNAMICS_RUNTIME_POINTER_VERSION,
        "status": "candidate_active" if runtime_applied else ("candidate_ready" if candidate.get("eligible_for_runtime") else "blocked"),
        "policy_family": "structure_dynamics_policy",
        "active_policy_version": active_version,
        "candidate_policy_version": candidate_version,
        "rollback_policy_version": STRUCTURE_DYNAMICS_BASELINE_VERSION,
        "active_pointer_source": str(active_pointer.get("source", "")) if active_pointer else "baseline",
        "candidate": candidate,
        "policy_payload": candidate.get("policy_payload", {}) if runtime_applied else {},
        "runtime_applied": runtime_applied,
        "runtime_allowed": runtime_applied,
        "blocking_gate": "" if runtime_applied else str(candidate.get("blocking_gate", "")),
        "runtime_mutation": False,
        "guardrails": [
            "STRUCTURE_DYNAMICS_RUNTIME_POINTER_READ_ONLY",
            "STRUCTURE_DYNAMICS_POINTER_USES_SYNTHETIC_PATH_REPLAY",
            "NO_CHART_FACT_MUTATION",
            "NO_FIXED_TEMPLATE_OVERRIDE",
        ],
    }


def write_structure_dynamics_runtime_pointer_activate_candidate(
    *,
    source_role: str,
    reason: str = "",
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    if source_role not in {"admin", "lab", "system"}:
        raise ValueError(f"Unsupported structure dynamics pointer activation source_role: {source_role}")
    storage = store or local_jsonl_store_from_env()
    report = run_structure_dynamics_synthetic_suite()
    candidate = _candidate_policy(report=report)
    candidate_version = str(candidate.get("candidate_policy_version", ""))
    if not candidate.get("eligible_for_runtime") or not candidate_version:
        return {
            "version": "v20.structure_dynamics_runtime_pointer_activation_result.v1",
            "status": "blocked_by_machine_gate",
            "candidate_policy_version": candidate_version,
            "active_policy_version": STRUCTURE_DYNAMICS_BASELINE_VERSION,
            "candidate": candidate,
            "runtime_mutation": False,
            "guardrails": [
                "STRUCTURE_DYNAMICS_MACHINE_GATE_REQUIRED",
                "NO_POINTER_WRITE_ON_BLOCKED_ACTIVATION",
                "NO_HUMAN_REVIEW_FALLBACK",
            ],
        }
    previous = _read_active_pointer(storage)
    previous_active = str(previous.get("active_policy_version", "")) or STRUCTURE_DYNAMICS_BASELINE_VERSION
    pointer = {
        "version": STRUCTURE_DYNAMICS_ACTIVE_POINTER_VERSION,
        "status": "candidate_active",
        "active_policy_version": candidate_version,
        "candidate_policy_version": candidate_version,
        "previous_active_policy_version": previous_active,
        "rollback_policy_version": STRUCTURE_DYNAMICS_BASELINE_VERSION,
        "source": "admin_structure_dynamics_optimizer_activate_candidate",
        "source_role": source_role,
        "reason": reason[:240],
        "candidate_summary": _candidate_summary(candidate),
        "policy_payload": candidate.get("policy_payload", {}),
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
        "guardrails": [
            "STRUCTURE_DYNAMICS_ACTIVATION_WRITES_VERSION_POINTER_ONLY",
            "DYNAMIC_PATH_WEIGHTS_ONLY",
            "NO_CHART_FACT_MUTATION",
        ],
    }
    path = _write_active_pointer(storage, pointer)
    audit = _append_pointer_audit(storage, "v20.structure_dynamics_runtime_pointer_activation_audit.v1", pointer)
    return {
        "version": "v20.structure_dynamics_runtime_pointer_activation_result.v1",
        "status": "candidate_active",
        "active_pointer_path": str(path),
        "active_policy_version": candidate_version,
        "candidate_policy_version": candidate_version,
        "previous_active_policy_version": previous_active,
        "candidate": candidate,
        "audit": audit,
        "runtime_mutation": True,
        "guardrails": [
            "STRUCTURE_DYNAMICS_POINTER_AUDIT_APPEND_ONLY",
            "STRUCTURE_DYNAMICS_POLICY_CAN_ROLL_BACK_TO_BASELINE",
            "RUNTIME_CONSUMES_VERSIONED_STRUCTURE_DYNAMICS_POLICY",
        ],
    }


def _candidate_policy(*, report: dict[str, object]) -> dict[str, object]:
    corpus_distribution = read_latest_structure_dynamics_corpus_distribution()
    quality = report.get("quality_scores", {}) if isinstance(report.get("quality_scores"), dict) else {}
    path_score = float(quality.get("dynamic_path_consistency", 0.0) or 0.0)
    semantic_score = float(quality.get("semantic_candidate_precision", 0.0) or 0.0)
    case_count = int(report.get("case_count", 0) or 0)
    corpus_unsupported_count = int(corpus_distribution.get("unsupported_label_count", 0) or 0)
    corpus_status = str(corpus_distribution.get("status", ""))
    corpus_blocks = corpus_status in {"completed", "completed_with_findings"} and corpus_unsupported_count > 0
    eligible = bool(report.get("ok")) and case_count >= 3 and path_score >= 0.86 and semantic_score >= 0.84 and not corpus_blocks
    policy_payload = _policy_payload(
        path_score=path_score,
        semantic_score=semantic_score,
        case_count=case_count,
        corpus_distribution=corpus_distribution,
    ) if eligible else {}
    blocking_gate = "" if policy_payload else _blocking_gate(
        report=report,
        path_score=path_score,
        semantic_score=semantic_score,
        case_count=case_count,
        corpus_distribution=corpus_distribution,
    )
    version_seed = json.dumps(policy_payload, ensure_ascii=False, sort_keys=True)
    candidate_version = f"v20.structure_dynamics_policy.candidate.{_hash(version_seed)}" if policy_payload else ""
    return {
        "version": "v20.structure_dynamics_runtime_policy_candidate.v1",
        "status": "ready" if policy_payload else "blocked",
        "candidate_policy_version": candidate_version,
        "eligible_for_runtime": bool(policy_payload),
        "dynamic_path_consistency": round(path_score, 4),
        "semantic_candidate_precision": round(semantic_score, 4),
        "synthetic_case_count": case_count,
        "corpus_distribution_status": corpus_status,
        "corpus_distribution_case_count": int(corpus_distribution.get("limit", corpus_distribution.get("case_count", 0)) or 0),
        "corpus_distribution_unsupported_count": corpus_unsupported_count,
        "blocking_gate": blocking_gate,
        "policy_payload": policy_payload,
        "source_reports": {
            "structure_dynamics_synthetic_version": report.get("version", ""),
            "structure_dynamics_synthetic_ok": report.get("ok", False),
            "structure_dynamics_synthetic_pass_rate": report.get("pass_rate", 0.0),
            "structure_dynamics_corpus_distribution_version": corpus_distribution.get("version", ""),
            "structure_dynamics_corpus_distribution_status": corpus_status,
        },
        "runtime_mutation": False,
        "guardrails": [
            "STRUCTURE_DYNAMICS_CANDIDATE_FROM_SYNTHETIC_REPLAY",
            "STRUCTURE_DYNAMICS_CORPUS_DISTRIBUTION_BLOCKS_UNSUPPORTED_LABELS",
            "DYNAMIC_PATH_CONSISTENCY_REQUIRED",
            "SEMANTIC_CANDIDATE_PRECISION_REQUIRED",
            "NO_FIXED_TEMPLATE_PROMOTION",
        ],
    }


def _policy_payload(
    *,
    path_score: float,
    semantic_score: float,
    case_count: int,
    corpus_distribution: dict[str, object],
) -> dict[str, object]:
    confidence = min(path_score, semantic_score)
    corpus_case_count = int(corpus_distribution.get("limit", corpus_distribution.get("case_count", 0)) or 0)
    corpus_status = str(corpus_distribution.get("status", ""))
    return {
        "dynamic_path_weight_policy": {
            "policy_id": "v20.structure_dynamics.dynamic_path_weight_policy",
            "direct_action_priority_weight": round(0.06 + confidence * 0.04, 4),
            "continuity_bonus_weight": round(0.04 + path_score * 0.04, 4),
            "blockage_penalty_weight": round(0.14 + (1.0 - min(path_score, 1.0)) * 0.04, 4),
            "terminal_convergence_weight": round(0.08 + semantic_score * 0.04, 4),
            "synthetic_case_count": case_count,
            "corpus_distribution_case_count": corpus_case_count,
            "corpus_distribution_status": corpus_status,
            "corpus_distribution_run_id": str(corpus_distribution.get("run_id", "")),
            "corpus_distribution_start": int(corpus_distribution.get("start", 0) or 0),
            "corpus_distribution_target_count": int(corpus_distribution.get("target_count", 0) or 0),
            "source": "structure_dynamics_synthetic_plus_corpus_distribution",
        },
        "semantic_match_policy": {
            "policy_id": "v20.structure_dynamics.semantic_match_policy",
            "semantic_match_threshold": round(max(0.84, min(0.92, semantic_score)), 4),
            "path_consistency": round(path_score, 4),
            "semantic_candidate_precision": round(semantic_score, 4),
            "corpus_distribution_case_count": corpus_case_count,
            "corpus_distribution_status": corpus_status,
            "corpus_distribution_run_id": str(corpus_distribution.get("run_id", "")),
            "corpus_distribution_start": int(corpus_distribution.get("start", 0) or 0),
            "corpus_distribution_target_count": int(corpus_distribution.get("target_count", 0) or 0),
            "source": "structure_dynamics_synthetic_plus_corpus_distribution",
        },
    }


def _blocking_gate(
    *,
    report: dict[str, object],
    path_score: float,
    semantic_score: float,
    case_count: int,
    corpus_distribution: dict[str, object],
) -> str:
    if str(corpus_distribution.get("status", "")) in {"completed", "completed_with_findings"} and int(corpus_distribution.get("unsupported_label_count", 0) or 0) > 0:
        return "structure_dynamics_corpus_distribution_has_unsupported_labels"
    if report.get("ok") is not True:
        return "structure_dynamics_synthetic_not_ok"
    if case_count < 3:
        return "structure_dynamics_synthetic_case_count_too_low"
    if path_score < 0.86:
        return "dynamic_path_consistency_below_threshold"
    if semantic_score < 0.84:
        return "semantic_candidate_precision_below_threshold"
    return "structure_dynamics_policy_payload_empty"


def _candidate_summary(candidate: dict[str, object]) -> dict[str, object]:
    return {
        "candidate_policy_version": candidate.get("candidate_policy_version", ""),
        "dynamic_path_consistency": candidate.get("dynamic_path_consistency", 0.0),
        "semantic_candidate_precision": candidate.get("semantic_candidate_precision", 0.0),
        "synthetic_case_count": candidate.get("synthetic_case_count", 0),
        "corpus_distribution_status": candidate.get("corpus_distribution_status", ""),
        "corpus_distribution_case_count": candidate.get("corpus_distribution_case_count", 0),
        "corpus_distribution_unsupported_count": candidate.get("corpus_distribution_unsupported_count", 0),
        "corpus_distribution_run_id": candidate.get("policy_payload", {})
        .get("dynamic_path_weight_policy", {})
        .get("corpus_distribution_run_id", ""),
        "corpus_distribution_start": candidate.get("policy_payload", {})
        .get("dynamic_path_weight_policy", {})
        .get("corpus_distribution_start", 0),
        "blocking_gate": candidate.get("blocking_gate", ""),
    }


def _active_version(candidate_version: str, active_pointer: dict[str, object]) -> str:
    active = str(active_pointer.get("active_policy_version", "")) if active_pointer else ""
    if active == candidate_version or active == STRUCTURE_DYNAMICS_BASELINE_VERSION:
        return active or STRUCTURE_DYNAMICS_BASELINE_VERSION
    return STRUCTURE_DYNAMICS_BASELINE_VERSION


def _read_active_pointer(store: LocalJsonlStore) -> dict[str, object]:
    path = store.runtime_dir / STRUCTURE_DYNAMICS_POINTER_RELATIVE_PATH
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict) or payload.get("version") != STRUCTURE_DYNAMICS_ACTIVE_POINTER_VERSION:
        return {}
    return dict(payload) | {"source_path": path}


def _write_active_pointer(store: LocalJsonlStore, payload: dict[str, object]) -> Path:
    path = store.runtime_dir / STRUCTURE_DYNAMICS_POINTER_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _append_pointer_audit(store: LocalJsonlStore, event_version: str, pointer: dict[str, object]) -> dict[str, object]:
    return store.append_record(
        STRUCTURE_DYNAMICS_POINTER_AUDIT_LEDGER,
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
                "STRUCTURE_DYNAMICS_POINTER_AUDIT_APPEND_ONLY",
                "NO_SECRET_VALUES_RENDERED",
            ],
        },
    )


def _hash(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]
