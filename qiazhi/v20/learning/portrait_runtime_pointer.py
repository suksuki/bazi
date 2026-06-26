from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env
from v20.validation.rule_portrait_batch import read_rule_portrait_batch_artifact


PORTRAIT_RUNTIME_POINTER_VERSION = "v20.portrait_runtime_pointer.v1"
PORTRAIT_ACTIVE_POINTER_VERSION = "v20.portrait_runtime_active_pointer.v1"
PORTRAIT_BASELINE_VERSION = "v20.portrait_policy.baseline.v1"
PORTRAIT_POINTER_AUDIT_LEDGER = "portrait_runtime_pointer_audit"
PORTRAIT_POINTER_RELATIVE_PATH = "training/portrait_policy_versions/active_pointer.json"


def build_portrait_runtime_pointer(*, store: LocalJsonlStore | None = None) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    batch = read_rule_portrait_batch_artifact()
    candidate = _candidate_policy(batch=batch)
    active_pointer = _read_active_pointer(storage)
    candidate_version = str(candidate.get("candidate_policy_version", ""))
    active_version = _active_version(candidate_version, active_pointer)
    runtime_applied = bool(candidate_version and active_version == candidate_version and candidate.get("eligible_for_runtime"))
    return {
        "version": PORTRAIT_RUNTIME_POINTER_VERSION,
        "status": "candidate_active" if runtime_applied else ("candidate_ready" if candidate.get("eligible_for_runtime") else "blocked"),
        "policy_family": "portrait_policy",
        "active_policy_version": active_version,
        "candidate_policy_version": candidate_version,
        "rollback_policy_version": PORTRAIT_BASELINE_VERSION,
        "active_pointer_source": str(active_pointer.get("source", "")) if active_pointer else "baseline",
        "candidate": candidate,
        "policy_payload": candidate.get("policy_payload", {}) if runtime_applied else {},
        "runtime_applied": runtime_applied,
        "runtime_allowed": runtime_applied,
        "blocking_gate": "" if runtime_applied else str(candidate.get("blocking_gate", "")),
        "runtime_mutation": False,
        "guardrails": [
            "PORTRAIT_RUNTIME_POINTER_READ_ONLY",
            "PORTRAIT_POINTER_USES_RULE_PORTRAIT_BATCH",
            "NO_CHART_FACT_MUTATION",
            "NO_ROLE_VISIBILITY_BYPASS",
        ],
    }


def write_portrait_runtime_pointer_activate_candidate(
    *,
    source_role: str,
    reason: str = "",
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    if source_role not in {"admin", "lab", "system"}:
        raise ValueError(f"Unsupported portrait pointer activation source_role: {source_role}")
    storage = store or local_jsonl_store_from_env()
    batch = read_rule_portrait_batch_artifact()
    candidate = _candidate_policy(batch=batch)
    candidate_version = str(candidate.get("candidate_policy_version", ""))
    if not candidate.get("eligible_for_runtime") or not candidate_version:
        return {
            "version": "v20.portrait_runtime_pointer_activation_result.v1",
            "status": "blocked_by_machine_gate",
            "candidate_policy_version": candidate_version,
            "active_policy_version": PORTRAIT_BASELINE_VERSION,
            "candidate": candidate,
            "runtime_mutation": False,
            "guardrails": [
                "PORTRAIT_MACHINE_GATE_REQUIRED",
                "NO_POINTER_WRITE_ON_BLOCKED_ACTIVATION",
                "ROLE_DEPTH_REMAINS_ROLE_GATED",
            ],
        }
    previous = _read_active_pointer(storage)
    previous_active = str(previous.get("active_policy_version", "")) or PORTRAIT_BASELINE_VERSION
    pointer = {
        "version": PORTRAIT_ACTIVE_POINTER_VERSION,
        "status": "candidate_active",
        "active_policy_version": candidate_version,
        "candidate_policy_version": candidate_version,
        "previous_active_policy_version": previous_active,
        "rollback_policy_version": PORTRAIT_BASELINE_VERSION,
        "source": "admin_portrait_optimizer_activate_candidate",
        "source_role": source_role,
        "reason": reason[:240],
        "candidate_summary": _candidate_summary(candidate),
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
        "guardrails": [
            "PORTRAIT_ACTIVATION_WRITES_VERSION_POINTER_ONLY",
            "NO_CHART_FACT_MUTATION",
            "NO_ROLE_VISIBILITY_BYPASS",
        ],
    }
    path = _write_active_pointer(storage, pointer)
    audit = _append_pointer_audit(storage, "v20.portrait_runtime_pointer_activation_audit.v1", pointer)
    return {
        "version": "v20.portrait_runtime_pointer_activation_result.v1",
        "status": "candidate_active",
        "active_pointer_path": str(path),
        "active_policy_version": candidate_version,
        "candidate_policy_version": candidate_version,
        "previous_active_policy_version": previous_active,
        "candidate": candidate,
        "audit": audit,
        "runtime_mutation": True,
        "guardrails": [
            "PORTRAIT_POINTER_AUDIT_APPEND_ONLY",
            "PORTRAIT_POLICY_CAN_ROLL_BACK_TO_BASELINE",
            "ROLE_DEPTH_REMAINS_ROLE_GATED",
        ],
    }


def _candidate_policy(*, batch: dict[str, object]) -> dict[str, object]:
    rows = _policy_rows(batch=batch) if _batch_ready(batch) else []
    blocking_gate = "" if rows else _blocking_gate(batch=batch)
    version_seed = json.dumps(rows, ensure_ascii=False, sort_keys=True)
    candidate_version = f"v20.portrait_policy.candidate.{_hash(version_seed)}" if rows else ""
    return {
        "version": "v20.portrait_runtime_policy_candidate.v1",
        "status": "ready" if rows else "blocked",
        "candidate_policy_version": candidate_version,
        "eligible_for_runtime": bool(rows),
        "portrait_policy_count": len(rows),
        "blocking_gate": blocking_gate,
        "policy_payload": {
            "portrait_axis_weight_policy": rows,
        } if rows else {},
        "source_reports": {
            "rule_portrait_batch_status": batch.get("status", "not_built"),
            "rule_portrait_batch_ok": batch.get("ok", False),
            "rule_portrait_batch_latest_path": batch.get("latest_path", ""),
        },
        "runtime_mutation": False,
        "guardrails": [
            "PORTRAIT_CANDIDATE_FROM_SYNTHETIC_BATCH",
            "PORTRAIT_ALIGNMENT_REQUIRED",
            "NO_ROLE_DEPTH_ESCALATION_WITHOUT_ROLE_GATE",
        ],
    }


def _batch_ready(batch: dict[str, object]) -> bool:
    return (
        batch.get("status") == "pass"
        and batch.get("ok") is True
        and int(batch.get("case_count", 0) or 0) > 0
        and int(batch.get("failure_count", 0) or 0) == 0
    )


def _policy_rows(*, batch: dict[str, object]) -> list[dict[str, object]]:
    case_rows = [row for row in batch.get("case_results", ()) if isinstance(row, dict) and row.get("ok") is True]
    counts = _domain_counts(case_rows)
    coverage = batch.get("coverage_summary", {})
    coverage_domains = []
    if isinstance(coverage, dict):
        coverage_domains = [str(domain) for domain in coverage.get("portrait_domains", ()) if str(domain)]
    domains = sorted(set(coverage_domains) | set(counts))
    rows: list[dict[str, object]] = []
    case_count = max(1, int(batch.get("case_count", 0) or len(case_rows) or 1))
    for domain in domains:
        hit_count = counts.get(domain, 0)
        if hit_count <= 0:
            continue
        rows.append(
            {
                "domain": domain,
                "axis_weight_delta": _axis_weight_delta(hit_count, case_count),
                "confidence_floor_delta": _confidence_floor_delta(hit_count, case_count),
                "role_depth_hint": _role_depth_hint(hit_count),
                "positive_case_count": hit_count,
                "batch_case_count": case_count,
                "source": "rule_portrait_batch",
            }
        )
    return rows


def _domain_counts(case_rows: list[dict[str, object]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in case_rows:
        domains = {
            str(domain)
            for key in ("portrait_domains", "decision_domains")
            for domain in row.get(key, ())
            if str(domain)
        }
        for domain in domains:
            counts[domain] = counts.get(domain, 0) + 1
    return counts


def _axis_weight_delta(hit_count: int, case_count: int) -> float:
    coverage = hit_count / max(1, case_count)
    return round(min(0.05, 0.015 + coverage * 0.025), 4)


def _confidence_floor_delta(hit_count: int, case_count: int) -> float:
    coverage = hit_count / max(1, case_count)
    return round(min(0.03, 0.006 + coverage * 0.012), 4)


def _role_depth_hint(hit_count: int) -> str:
    if hit_count >= 3:
        return "practitioner_detail"
    if hit_count == 2:
        return "guided_summary"
    return "entry_overview"


def _blocking_gate(*, batch: dict[str, object]) -> str:
    if batch.get("status") != "pass":
        return "rule_portrait_batch_not_passed"
    if batch.get("ok") is not True:
        return "rule_portrait_batch_not_ok"
    if int(batch.get("case_count", 0) or 0) <= 0:
        return "rule_portrait_batch_has_no_cases"
    if int(batch.get("failure_count", 0) or 0) > 0:
        return "rule_portrait_batch_has_failures"
    return "portrait_policy_payload_empty"


def _candidate_summary(candidate: dict[str, object]) -> dict[str, object]:
    return {
        "candidate_policy_version": candidate.get("candidate_policy_version", ""),
        "portrait_policy_count": candidate.get("portrait_policy_count", 0),
        "blocking_gate": candidate.get("blocking_gate", ""),
    }


def _active_version(candidate_version: str, active_pointer: dict[str, object]) -> str:
    active = str(active_pointer.get("active_policy_version", "")) if active_pointer else ""
    if active == candidate_version or active == PORTRAIT_BASELINE_VERSION:
        return active or PORTRAIT_BASELINE_VERSION
    return PORTRAIT_BASELINE_VERSION


def _read_active_pointer(store: LocalJsonlStore) -> dict[str, object]:
    path = store.runtime_dir / PORTRAIT_POINTER_RELATIVE_PATH
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict) or payload.get("version") != PORTRAIT_ACTIVE_POINTER_VERSION:
        return {}
    return dict(payload) | {"source_path": path}


def _write_active_pointer(store: LocalJsonlStore, payload: dict[str, object]) -> Path:
    path = store.runtime_dir / PORTRAIT_POINTER_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _append_pointer_audit(store: LocalJsonlStore, event_version: str, pointer: dict[str, object]) -> dict[str, object]:
    return store.append_record(
        PORTRAIT_POINTER_AUDIT_LEDGER,
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
                "PORTRAIT_POINTER_AUDIT_APPEND_ONLY",
                "NO_SECRET_VALUES_RENDERED",
            ],
        },
    )


def _hash(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12]
