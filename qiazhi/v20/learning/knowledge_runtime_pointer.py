from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v20.knowledge.rule_proposal import build_first_wave_rule_proposal_preflight
from v20.learning.knowledge_rule_review_overlay import read_knowledge_rule_review_overlay_artifact
from v20.learning.training_iteration import read_training_iteration_artifact
from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


KNOWLEDGE_RUNTIME_POINTER_VERSION = "v20.knowledge_runtime_pointer.v1"
KNOWLEDGE_ACTIVE_POINTER_VERSION = "v20.knowledge_runtime_active_pointer.v1"
KNOWLEDGE_BASELINE_VERSION = "v20.knowledge_policy.baseline.v1"
KNOWLEDGE_POINTER_AUDIT_LEDGER = "knowledge_runtime_pointer_audit"
KNOWLEDGE_POINTER_RELATIVE_PATH = "training/knowledge_policy_versions/active_pointer.json"


def build_knowledge_runtime_pointer(*, store: LocalJsonlStore | None = None) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    overlay = read_knowledge_rule_review_overlay_artifact()
    preflight = build_first_wave_rule_proposal_preflight(limit_per_domain=1)
    training_iteration = read_training_iteration_artifact()
    candidate = _candidate_policy(overlay=overlay, preflight=preflight, training_iteration=training_iteration)
    active_pointer = _read_active_pointer(storage)
    candidate_version = str(candidate.get("candidate_policy_version", ""))
    active_version = _active_version(candidate_version, active_pointer)
    runtime_applied = bool(candidate_version and active_version == candidate_version and candidate.get("eligible_for_runtime"))
    return {
        "version": KNOWLEDGE_RUNTIME_POINTER_VERSION,
        "status": "candidate_active" if runtime_applied else ("candidate_ready" if candidate.get("eligible_for_runtime") else "blocked"),
        "policy_family": "knowledge_review",
        "active_policy_version": active_version,
        "candidate_policy_version": candidate_version,
        "rollback_policy_version": KNOWLEDGE_BASELINE_VERSION,
        "active_pointer_source": str(active_pointer.get("source", "")) if active_pointer else "baseline",
        "candidate": candidate,
        "policy_payload": candidate.get("policy_payload", {}) if runtime_applied else {},
        "runtime_applied": runtime_applied,
        "runtime_allowed": runtime_applied,
        "blocking_gate": "" if runtime_applied else str(candidate.get("blocking_gate", "")),
        "runtime_mutation": False,
        "guardrails": [
            "KNOWLEDGE_RUNTIME_POINTER_READ_ONLY",
            "KNOWLEDGE_POINTER_USES_OVERLAY_AND_RULE_PROPOSAL_PREFLIGHT",
            "NO_KNOWLEDGE_TRUTH_MUTATION",
            "NO_HUMAN_REVIEW_GATE",
        ],
    }


def write_knowledge_runtime_pointer_activate_candidate(
    *,
    source_role: str,
    reason: str = "",
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    if source_role not in {"admin", "lab", "system"}:
        raise ValueError(f"Unsupported knowledge pointer activation source_role: {source_role}")
    storage = store or local_jsonl_store_from_env()
    overlay = read_knowledge_rule_review_overlay_artifact()
    preflight = build_first_wave_rule_proposal_preflight(limit_per_domain=1)
    training_iteration = read_training_iteration_artifact()
    candidate = _candidate_policy(overlay=overlay, preflight=preflight, training_iteration=training_iteration)
    candidate_version = str(candidate.get("candidate_policy_version", ""))
    if not candidate.get("eligible_for_runtime") or not candidate_version:
        return {
            "version": "v20.knowledge_runtime_pointer_activation_result.v1",
            "status": "blocked_by_machine_gate",
            "candidate_policy_version": candidate_version,
            "active_policy_version": KNOWLEDGE_BASELINE_VERSION,
            "candidate": candidate,
            "runtime_mutation": False,
            "guardrails": [
                "KNOWLEDGE_MACHINE_GATE_REQUIRED",
                "NO_POINTER_WRITE_ON_BLOCKED_ACTIVATION",
                "NO_HUMAN_REVIEW_FALLBACK",
            ],
        }
    previous = _read_active_pointer(storage)
    previous_active = str(previous.get("active_policy_version", "")) or KNOWLEDGE_BASELINE_VERSION
    pointer = {
        "version": KNOWLEDGE_ACTIVE_POINTER_VERSION,
        "status": "candidate_active",
        "active_policy_version": candidate_version,
        "candidate_policy_version": candidate_version,
        "previous_active_policy_version": previous_active,
        "rollback_policy_version": KNOWLEDGE_BASELINE_VERSION,
        "source": "admin_knowledge_optimizer_activate_candidate",
        "source_role": source_role,
        "reason": reason[:240],
        "candidate_summary": _candidate_summary(candidate),
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
        "guardrails": [
            "KNOWLEDGE_ACTIVATION_WRITES_VERSION_POINTER_ONLY",
            "NO_KNOWLEDGE_TRUTH_MUTATION",
            "NO_HUMAN_REVIEW_GATE",
        ],
    }
    path = _write_active_pointer(storage, pointer)
    audit = _append_pointer_audit(storage, "v20.knowledge_runtime_pointer_activation_audit.v1", pointer)
    return {
        "version": "v20.knowledge_runtime_pointer_activation_result.v1",
        "status": "candidate_active",
        "active_pointer_path": str(path),
        "active_policy_version": candidate_version,
        "candidate_policy_version": candidate_version,
        "previous_active_policy_version": previous_active,
        "candidate": candidate,
        "audit": audit,
        "runtime_mutation": True,
        "guardrails": [
            "KNOWLEDGE_POINTER_AUDIT_APPEND_ONLY",
            "KNOWLEDGE_POLICY_CAN_ROLL_BACK_TO_BASELINE",
            "RUNTIME_CONSUMES_VERSIONED_MAPPING_POLICY",
        ],
    }


def _candidate_policy(
    *,
    overlay: dict[str, object],
    preflight: dict[str, object],
    training_iteration: dict[str, object] | None = None,
) -> dict[str, object]:
    answer_governance = _answer_governance_signal(training_iteration or {})
    rows = _policy_rows(overlay=overlay, answer_governance=answer_governance) if _gate_ready(overlay=overlay, preflight=preflight) else []
    blocking_gate = "" if rows else _blocking_gate(overlay=overlay, preflight=preflight)
    version_seed = json.dumps(rows, ensure_ascii=False, sort_keys=True)
    candidate_version = f"v20.knowledge_policy.candidate.{_hash(version_seed)}" if rows else ""
    return {
        "version": "v20.knowledge_runtime_policy_candidate.v1",
        "status": "ready" if rows else "blocked",
        "candidate_policy_version": candidate_version,
        "eligible_for_runtime": bool(rows),
        "knowledge_policy_count": len(rows),
        "blocking_gate": blocking_gate,
        "policy_payload": {
            "knowledge_rule_mapping_policy": rows,
        } if rows else {},
        "source_reports": {
            "knowledge_rule_review_overlay_status": overlay.get("status", "not_built"),
            "knowledge_rule_review_overlay_latest_path": overlay.get("latest_path", ""),
            "rule_proposal_preflight_status": preflight.get("status", "not_built"),
            "rule_proposal_preflight_ok": preflight.get("ok", False),
            "training_iteration_status": (training_iteration or {}).get("status", "not_built"),
            "answer_governance_average_quality_score": answer_governance.get("average_quality_score", 0.0),
            "answer_governance_weight_delta": answer_governance.get("answer_guidance_weight_delta", 0.0),
        },
        "runtime_mutation": False,
        "guardrails": [
            "KNOWLEDGE_CANDIDATE_FROM_OVERLAY_ARTIFACT",
            "RULE_PROPOSAL_PREFLIGHT_REQUIRED",
            "NO_MANUAL_REVIEW_REQUIRED",
        ],
    }


def _gate_ready(*, overlay: dict[str, object], preflight: dict[str, object]) -> bool:
    return (
        overlay.get("status") == "ready"
        and int(overlay.get("runtime_activation_candidate_count", 0) or 0) > 0
        and preflight.get("status") == "active_ready"
        and preflight.get("ok") is True
        and int(preflight.get("proposal_count", 0) or 0) > 0
    )


def _policy_rows(*, overlay: dict[str, object], answer_governance: dict[str, object]) -> list[dict[str, object]]:
    rows = []
    for row in overlay.get("rules", ()):
        if not isinstance(row, dict) or row.get("runtime_activation_candidate") is not True:
            continue
        rule_key = str(row.get("rule_key", ""))
        source_knowledge_id = str(row.get("source_knowledge_id", ""))
        if not rule_key or not source_knowledge_id:
            continue
        rows.append(
            {
                "rule_key": rule_key,
                "source_knowledge_id": source_knowledge_id,
                "domain": str(row.get("domain", "")),
                "mapping_weight_delta": _mapping_weight_delta(row),
                "answer_guidance_delta": _answer_guidance_delta(row, answer_governance=answer_governance),
                "answer_governance_quality_delta": float(answer_governance.get("answer_guidance_weight_delta", 0.0) or 0.0),
                "answer_governance_quality_score": float(answer_governance.get("average_quality_score", 0.0) or 0.0),
                "source_trust_delta": _source_trust_delta(row),
                "synthetic_case_count": int(row.get("synthetic_case_count", 0) or 0),
                "support_quality": str(row.get("support_quality", "")),
                "source": "knowledge_rule_review_overlay+rule_proposal_preflight",
            }
        )
    return sorted(rows, key=lambda item: (str(item["domain"]), str(item["rule_key"])))


def _mapping_weight_delta(row: dict[str, object]) -> float:
    base = 0.012
    active_bonus = 0.012 if row.get("active_weight_candidate") is True else 0.004
    synthetic_bonus = min(0.018, int(row.get("synthetic_case_count", 0) or 0) * 0.002)
    quality_bonus = 0.008 if str(row.get("support_quality", "")) in {"strong", "active_ready", "supported"} else 0.0
    return round(min(0.06, base + active_bonus + synthetic_bonus + quality_bonus), 4)


def _answer_guidance_delta(row: dict[str, object], *, answer_governance: dict[str, object]) -> float:
    synthetic_bonus = min(0.012, int(row.get("synthetic_case_count", 0) or 0) * 0.0015)
    governance_bonus = float(answer_governance.get("answer_guidance_weight_delta", 0.0) or 0.0)
    return round(min(0.04, 0.006 + synthetic_bonus + governance_bonus), 4)


def _answer_governance_signal(training_iteration: dict[str, object]) -> dict[str, object]:
    results = training_iteration.get("results", {}) if isinstance(training_iteration, dict) else {}
    report = results.get("answer_governance_training", {}) if isinstance(results, dict) else {}
    if not isinstance(report, dict):
        report = {}
    targets = report.get("parameter_targets", {})
    if not isinstance(targets, dict):
        targets = {}
    return {
        "average_quality_score": float(report.get("average_quality_score", 0.0) or 0.0),
        "answer_guidance_weight_delta": float(targets.get("answer_guidance_weight", 0.0) or 0.0),
    }


def _source_trust_delta(row: dict[str, object]) -> float:
    if str(row.get("validation_state", "")) == "active_ready" and str(row.get("synthetic_state", "")) == "synthetic_passed":
        return 0.02
    if str(row.get("synthetic_state", "")) == "synthetic_passed":
        return 0.014
    return 0.006


def _blocking_gate(*, overlay: dict[str, object], preflight: dict[str, object]) -> str:
    if overlay.get("status") != "ready":
        return "knowledge_rule_review_overlay_not_ready"
    if int(overlay.get("runtime_activation_candidate_count", 0) or 0) <= 0:
        return "knowledge_overlay_has_no_runtime_candidates"
    if preflight.get("status") != "active_ready":
        return "knowledge_rule_proposal_preflight_not_ready"
    if preflight.get("ok") is not True:
        return "knowledge_rule_proposal_preflight_not_ok"
    if int(preflight.get("proposal_count", 0) or 0) <= 0:
        return "knowledge_rule_proposal_preflight_has_no_proposals"
    return "knowledge_policy_payload_empty"


def _candidate_summary(candidate: dict[str, object]) -> dict[str, object]:
    return {
        "candidate_policy_version": candidate.get("candidate_policy_version", ""),
        "knowledge_policy_count": candidate.get("knowledge_policy_count", 0),
        "blocking_gate": candidate.get("blocking_gate", ""),
    }


def _active_version(candidate_version: str, active_pointer: dict[str, object]) -> str:
    active = str(active_pointer.get("active_policy_version", "")) if active_pointer else ""
    if active == candidate_version or active == KNOWLEDGE_BASELINE_VERSION:
        return active or KNOWLEDGE_BASELINE_VERSION
    return KNOWLEDGE_BASELINE_VERSION


def _read_active_pointer(store: LocalJsonlStore) -> dict[str, object]:
    path = store.runtime_dir / KNOWLEDGE_POINTER_RELATIVE_PATH
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict) or payload.get("version") != KNOWLEDGE_ACTIVE_POINTER_VERSION:
        return {}
    return dict(payload) | {"source_path": path}


def _write_active_pointer(store: LocalJsonlStore, payload: dict[str, object]) -> Path:
    path = store.runtime_dir / KNOWLEDGE_POINTER_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _append_pointer_audit(store: LocalJsonlStore, event_version: str, pointer: dict[str, object]) -> dict[str, object]:
    return store.append_record(
        KNOWLEDGE_POINTER_AUDIT_LEDGER,
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
                "KNOWLEDGE_POINTER_AUDIT_APPEND_ONLY",
                "NO_SECRET_VALUES_RENDERED",
            ],
        },
    )


def _hash(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]
