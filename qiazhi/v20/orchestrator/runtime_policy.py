from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from v20.learning.orchestrator_policy_versioning import BASELINE_POLICY_VERSION
from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


RUNTIME_POLICY_POINTER_VERSION = "v20.orchestrator_runtime_policy_pointer.v1"
ACTIVE_POINTER_VERSION = "v20.orchestrator_runtime_active_pointer.v1"
ROLLBACK_AUDIT_LEDGER = "orchestrator_policy_rollback_audit"


def build_runtime_policy_pointer(
    *,
    brain_memory_signal: dict[str, Any],
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    memory_key = str(brain_memory_signal.get("memory_key", "")) if isinstance(brain_memory_signal, dict) else ""
    candidate = _read_latest_candidate(storage)
    candidate_version = _candidate_version(candidate)
    override = _read_active_pointer(storage)
    active_version = _active_version(candidate_version, override)
    fast_track_active = bool(candidate_version and active_version == candidate_version)
    rollback_active = active_version == BASELINE_POLICY_VERSION and bool(candidate_version)
    candidate_count = int(candidate.get("candidate_count", 0)) if candidate else 0
    policy_payload = _policy_payload(candidate) if fast_track_active else {}
    return {
        "version": RUNTIME_POLICY_POINTER_VERSION,
        "status": _pointer_status(fast_track_active=fast_track_active, rollback_active=rollback_active),
        "active_policy_version": active_version,
        "candidate_policy_version": candidate_version,
        "rollback_policy_version": BASELINE_POLICY_VERSION,
        "active_pointer_source": str(override.get("source", "")) if override else ("latest_candidate" if fast_track_active else "baseline"),
        "policy_family": "orchestrator_policy_bundle",
        "rollout_mode": _rollout_mode(fast_track_active=fast_track_active, rollback_active=rollback_active),
        "fast_iteration_enabled": True,
        "auto_learning_enabled": True,
        "shadow_signal_ref": memory_key,
        "candidate_status": str(candidate.get("status", "")) if candidate else "not_built",
        "candidate_count": candidate_count,
        "policy_payload": policy_payload,
        "consumable_policy_types": sorted(policy_payload.keys()),
        "candidate_source_path": str(candidate.get("source_path", "")) if candidate else "",
        "runtime_applied": fast_track_active,
        "runtime_effect": "version_pointer_active" if fast_track_active else ("rollback_pointer_active" if rollback_active else "baseline_pointer_active"),
        "runtime_mutation": False,
        "guardrails": [
            "RUNTIME_POLICY_POINTER_READS_LATEST_FAST_TRACK",
            "FAST_TRACK_CANDIDATES_CAN_ADVANCE_WITHOUT_HUMAN_GATE",
            "ROLLBACK_POINTER_RETAINED",
            "ACTIVE_POINTER_OVERRIDE_CAN_ROLL_BACK_TO_BASELINE",
            "CORE_FACTS_REMAIN_DETERMINISTIC",
        ],
    }


def write_runtime_policy_rollback(
    *,
    source_role: str,
    reason: str = "",
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    if source_role not in {"admin", "lab", "system"}:
        raise ValueError(f"Unsupported rollback source_role: {source_role}")
    storage = store or local_jsonl_store_from_env()
    candidate = _read_latest_candidate(storage)
    previous_active = _candidate_version(candidate) or BASELINE_POLICY_VERSION
    active_pointer = {
        "version": ACTIVE_POINTER_VERSION,
        "status": "rolled_back_to_baseline",
        "active_policy_version": BASELINE_POLICY_VERSION,
        "previous_active_policy_version": previous_active,
        "rollback_policy_version": BASELINE_POLICY_VERSION,
        "source": "admin_rollback",
        "source_role": source_role,
        "reason": reason[:240],
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
        "guardrails": [
            "ROLLBACK_WRITES_VERSION_POINTER_ONLY",
            "NO_CHART_FACT_MUTATION",
            "NO_USER_HISTORY_MUTATION",
        ],
    }
    directory = storage.runtime_dir / "training" / "orchestrator_policy_versions"
    directory.mkdir(parents=True, exist_ok=True)
    pointer_path = directory / "active_pointer.json"
    pointer_path.write_text(json.dumps(active_pointer, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    audit = storage.append_record(
        ROLLBACK_AUDIT_LEDGER,
        {
            "version": "v20.orchestrator_policy_rollback_audit.v1",
            "source_role": source_role,
            "active_policy_version": BASELINE_POLICY_VERSION,
            "previous_active_policy_version": previous_active,
            "rollback_policy_version": BASELINE_POLICY_VERSION,
            "reason": reason[:240],
            "runtime_mutation": False,
            "guardrails": [
                "ROLLBACK_AUDIT_APPEND_ONLY",
                "NO_SECRET_VALUES_RENDERED",
                "NO_USER_TEXT_REQUIRED",
            ],
        },
    )
    return {
        "version": "v20.orchestrator_policy_rollback_result.v1",
        "status": "rolled_back",
        "active_pointer_path": str(pointer_path),
        "active_policy_version": BASELINE_POLICY_VERSION,
        "previous_active_policy_version": previous_active,
        "rollback_policy_version": BASELINE_POLICY_VERSION,
        "audit": audit,
        "runtime_mutation": True,
        "guardrails": [
            "ROLLBACK_WRITES_VERSION_POINTER_ONLY",
            "ROLLBACK_AUDIT_APPEND_ONLY",
            "CORE_FACTS_REMAIN_DETERMINISTIC",
        ],
    }


def write_runtime_policy_activate_latest_candidate(
    *,
    source_role: str,
    reason: str = "",
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    if source_role not in {"admin", "lab", "system"}:
        raise ValueError(f"Unsupported activation source_role: {source_role}")
    storage = store or local_jsonl_store_from_env()
    candidate = _read_latest_candidate(storage)
    candidate_version = _candidate_version(candidate)
    if not candidate_version:
        return {
            "version": "v20.orchestrator_policy_activation_result.v1",
            "status": "blocked_no_latest_candidate",
            "active_policy_version": BASELINE_POLICY_VERSION,
            "candidate_policy_version": "",
            "runtime_mutation": False,
            "guardrails": [
                "LATEST_CANDIDATE_REQUIRED_FOR_ACTIVATION",
                "NO_POLICY_WRITE_ON_BLOCKED_ACTIVATION",
            ],
        }
    previous_pointer = _read_active_pointer(storage)
    previous_active = str(previous_pointer.get("active_policy_version", "")) or BASELINE_POLICY_VERSION
    active_pointer = {
        "version": ACTIVE_POINTER_VERSION,
        "status": "latest_candidate_active",
        "active_policy_version": candidate_version,
        "candidate_policy_version": candidate_version,
        "previous_active_policy_version": previous_active,
        "rollback_policy_version": BASELINE_POLICY_VERSION,
        "source": "admin_activate_latest_candidate",
        "source_role": source_role,
        "reason": reason[:240],
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
        "guardrails": [
            "ACTIVATION_WRITES_VERSION_POINTER_ONLY",
            "NO_CHART_FACT_MUTATION",
            "NO_USER_HISTORY_MUTATION",
        ],
    }
    directory = storage.runtime_dir / "training" / "orchestrator_policy_versions"
    directory.mkdir(parents=True, exist_ok=True)
    pointer_path = directory / "active_pointer.json"
    pointer_path.write_text(json.dumps(active_pointer, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    audit = storage.append_record(
        ROLLBACK_AUDIT_LEDGER,
        {
            "version": "v20.orchestrator_policy_activation_audit.v1",
            "source_role": source_role,
            "active_policy_version": candidate_version,
            "candidate_policy_version": candidate_version,
            "previous_active_policy_version": previous_active,
            "rollback_policy_version": BASELINE_POLICY_VERSION,
            "reason": reason[:240],
            "runtime_mutation": False,
            "guardrails": [
                "ACTIVATION_AUDIT_APPEND_ONLY",
                "NO_SECRET_VALUES_RENDERED",
                "NO_USER_TEXT_REQUIRED",
            ],
        },
    )
    return {
        "version": "v20.orchestrator_policy_activation_result.v1",
        "status": "latest_candidate_active",
        "active_pointer_path": str(pointer_path),
        "active_policy_version": candidate_version,
        "candidate_policy_version": candidate_version,
        "previous_active_policy_version": previous_active,
        "rollback_policy_version": BASELINE_POLICY_VERSION,
        "audit": audit,
        "runtime_mutation": True,
        "guardrails": [
            "ACTIVATION_WRITES_VERSION_POINTER_ONLY",
            "ACTIVATION_AUDIT_APPEND_ONLY",
            "CORE_FACTS_REMAIN_DETERMINISTIC",
        ],
    }
def _read_latest_candidate(store: LocalJsonlStore) -> dict[str, object]:
    path = store.runtime_dir / "training" / "orchestrator_policy_versions" / "latest.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    if payload.get("version") != "v20.orchestrator_policy_version_candidate.v1":
        return {}
    if not payload.get("runtime_allowed"):
        return {}
    return dict(payload) | {"source_path": path}


def _read_active_pointer(store: LocalJsonlStore) -> dict[str, object]:
    path = store.runtime_dir / "training" / "orchestrator_policy_versions" / "active_pointer.json"
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict):
        return {}
    if payload.get("version") != ACTIVE_POINTER_VERSION:
        return {}
    active = str(payload.get("active_policy_version", ""))
    if active not in {BASELINE_POLICY_VERSION, str(payload.get("candidate_policy_version", ""))} and not active.startswith("v20.orchestrator_policy."):
        return {}
    return dict(payload) | {"source_path": path}


def _active_version(candidate_version: str, override: dict[str, object]) -> str:
    active = str(override.get("active_policy_version", "")) if override else ""
    if active:
        return active
    return candidate_version or BASELINE_POLICY_VERSION


def _pointer_status(*, fast_track_active: bool, rollback_active: bool) -> str:
    if fast_track_active:
        return "fast_track_candidate_active"
    if rollback_active:
        return "rollback_baseline_active"
    return "baseline_active_fast_track_ready"


def _rollout_mode(*, fast_track_active: bool, rollback_active: bool) -> str:
    if fast_track_active:
        return "fast_track_candidate"
    if rollback_active:
        return "rollback_to_baseline"
    return "baseline_with_fast_track_shadow_ready"


def _candidate_version(candidate: dict[str, object]) -> str:
    return str(candidate.get("candidate_policy_version", "")) if candidate else ""


def _policy_payload(candidate: dict[str, object]) -> dict[str, object]:
    if not candidate:
        return {}
    payload = candidate.get("policy_payload", {})
    return dict(payload) if isinstance(payload, dict) else {}
