from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from v20.learning.decision_registry_iteration import read_decision_registry_iteration_artifact
from v20.learning.rule_replay_eval import read_rule_replay_eval_artifact
from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


RULE_RUNTIME_POINTER_VERSION = "v20.rule_runtime_pointer.v1"
RULE_ACTIVE_POINTER_VERSION = "v20.rule_runtime_active_pointer.v1"
RULE_BASELINE_VERSION = "v20.rule_policy.baseline.v1"
RULE_POINTER_AUDIT_LEDGER = "rule_runtime_pointer_audit"
RULE_POINTER_RELATIVE_PATH = "training/rule_policy_versions/active_pointer.json"


def build_rule_runtime_pointer(*, store: LocalJsonlStore | None = None) -> dict[str, object]:
    storage = store or local_jsonl_store_from_env()
    replay = read_rule_replay_eval_artifact()
    registry = read_decision_registry_iteration_artifact()
    candidate = _candidate_policy(replay=replay, registry=registry)
    active_pointer = _read_active_pointer(storage)
    candidate_version = str(candidate.get("candidate_policy_version", ""))
    active_version = _active_version(candidate_version, active_pointer)
    runtime_applied = bool(candidate_version and active_version == candidate_version and candidate.get("eligible_for_runtime"))
    return {
        "version": RULE_RUNTIME_POINTER_VERSION,
        "status": "candidate_active" if runtime_applied else ("candidate_ready" if candidate.get("eligible_for_runtime") else "blocked"),
        "policy_family": "rule_policy",
        "active_policy_version": active_version,
        "candidate_policy_version": candidate_version,
        "rollback_policy_version": RULE_BASELINE_VERSION,
        "active_pointer_source": str(active_pointer.get("source", "")) if active_pointer else "baseline",
        "candidate": candidate,
        "policy_payload": candidate.get("policy_payload", {}) if runtime_applied else {},
        "runtime_applied": runtime_applied,
        "runtime_allowed": runtime_applied,
        "blocking_gate": "" if runtime_applied else str(candidate.get("blocking_gate", "")),
        "runtime_mutation": False,
        "guardrails": [
            "RULE_RUNTIME_POINTER_READ_ONLY",
            "RULE_POINTER_USES_REPLAY_AND_DECISION_REGISTRY",
            "NO_CHART_FACT_MUTATION",
            "NO_KNOWLEDGE_TRUTH_MUTATION",
        ],
    }


def write_rule_runtime_pointer_activate_candidate(
    *,
    source_role: str,
    reason: str = "",
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    if source_role not in {"admin", "lab", "system"}:
        raise ValueError(f"Unsupported rule pointer activation source_role: {source_role}")
    storage = store or local_jsonl_store_from_env()
    replay = read_rule_replay_eval_artifact()
    registry = read_decision_registry_iteration_artifact()
    candidate = _candidate_policy(replay=replay, registry=registry)
    candidate_version = str(candidate.get("candidate_policy_version", ""))
    if not candidate.get("eligible_for_runtime") or not candidate_version:
        return {
            "version": "v20.rule_runtime_pointer_activation_result.v1",
            "status": "blocked_by_machine_gate",
            "candidate_policy_version": candidate_version,
            "active_policy_version": RULE_BASELINE_VERSION,
            "candidate": candidate,
            "runtime_mutation": False,
            "guardrails": [
                "RULE_MACHINE_GATE_REQUIRED",
                "NO_POINTER_WRITE_ON_BLOCKED_ACTIVATION",
                "CORE_FACTS_REMAIN_DETERMINISTIC",
            ],
        }
    previous = _read_active_pointer(storage)
    previous_active = str(previous.get("active_policy_version", "")) or RULE_BASELINE_VERSION
    pointer = {
        "version": RULE_ACTIVE_POINTER_VERSION,
        "status": "candidate_active",
        "active_policy_version": candidate_version,
        "candidate_policy_version": candidate_version,
        "previous_active_policy_version": previous_active,
        "rollback_policy_version": RULE_BASELINE_VERSION,
        "source": "admin_rule_optimizer_activate_candidate",
        "source_role": source_role,
        "reason": reason[:240],
        "candidate_summary": _candidate_summary(candidate),
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
        "guardrails": [
            "RULE_ACTIVATION_WRITES_VERSION_POINTER_ONLY",
            "NO_CHART_FACT_MUTATION",
            "NO_KNOWLEDGE_TRUTH_MUTATION",
        ],
    }
    path = _write_active_pointer(storage, pointer)
    audit = _append_pointer_audit(storage, "v20.rule_runtime_pointer_activation_audit.v1", pointer)
    return {
        "version": "v20.rule_runtime_pointer_activation_result.v1",
        "status": "candidate_active",
        "active_pointer_path": str(path),
        "active_policy_version": candidate_version,
        "candidate_policy_version": candidate_version,
        "previous_active_policy_version": previous_active,
        "candidate": candidate,
        "audit": audit,
        "runtime_mutation": True,
        "guardrails": [
            "RULE_POINTER_AUDIT_APPEND_ONLY",
            "RULE_POLICY_CAN_ROLL_BACK_TO_BASELINE",
            "CORE_FACTS_REMAIN_DETERMINISTIC",
        ],
    }


def _candidate_policy(*, replay: dict[str, object], registry: dict[str, object]) -> dict[str, object]:
    replay_ready = replay.get("status") == "ready" and int(replay.get("runtime_activation_count", 0) or 0) > 0
    registry_ready = registry.get("status") == "ready" and int(registry.get("runtime_activation_count", 0) or 0) > 0
    rows = _policy_rows(replay=replay, registry=registry) if replay_ready and registry_ready else []
    blocking_gate = "" if rows else _blocking_gate(replay=replay, registry=registry)
    version_seed = json.dumps(rows, ensure_ascii=False, sort_keys=True)
    candidate_version = f"v20.rule_policy.candidate.{_hash(version_seed)}" if rows else ""
    return {
        "version": "v20.rule_runtime_policy_candidate.v1",
        "status": "ready" if rows else "blocked",
        "candidate_policy_version": candidate_version,
        "eligible_for_runtime": bool(rows),
        "rule_policy_count": len(rows),
        "blocking_gate": blocking_gate,
        "policy_payload": {
            "rule_weight_policy": rows,
        } if rows else {},
        "source_reports": {
            "rule_replay_eval_status": replay.get("status", "not_built"),
            "decision_registry_iteration_status": registry.get("status", "not_built"),
            "rule_replay_eval_latest_path": replay.get("latest_path", ""),
            "decision_registry_iteration_latest_path": registry.get("latest_path", ""),
        },
        "runtime_mutation": False,
        "guardrails": [
            "RULE_CANDIDATE_FROM_SYNTHETIC_REPLAY",
            "DECISION_REGISTRY_REQUIRED",
            "NO_DIRECT_RULE_TRUTH_MUTATION",
        ],
    }


def _policy_rows(*, replay: dict[str, object], registry: dict[str, object]) -> list[dict[str, object]]:
    registry_counts = _registry_counts(registry)
    rows: list[dict[str, object]] = []
    for row in replay.get("evaluations", ()):
        if not isinstance(row, dict) or row.get("runtime_activation") is not True:
            continue
        rule_key = str(row.get("rule_key", ""))
        if not rule_key:
            continue
        rows.append(
            {
                "rule_key": rule_key,
                "domain": str(row.get("domain", "")),
                "weight_delta": _weight_delta(row, registry_counts.get(rule_key, 0)),
                "subcondition_count": int(row.get("subcondition_count", 0) or 0),
                "counterexample_signal_count": int(row.get("counterexample_signal_count", 0) or 0),
                "decision_registry_record_count": registry_counts.get(rule_key, 0),
                "source": "rule_replay_eval+decision_registry_iteration",
            }
        )
    return sorted(rows, key=lambda item: (str(item["domain"]), str(item["rule_key"])))


def _weight_delta(row: dict[str, object], registry_count: int) -> float:
    base = 0.015
    subcondition_bonus = min(0.02, int(row.get("subcondition_count", 0) or 0) * 0.002)
    registry_bonus = min(0.015, registry_count * 0.001)
    counterexample_penalty = min(0.02, int(row.get("counterexample_signal_count", 0) or 0) * 0.001)
    return round(base + subcondition_bonus + registry_bonus - counterexample_penalty, 4)


def _registry_counts(registry: dict[str, object]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in registry.get("records", ()):
        if not isinstance(row, dict):
            continue
        key = str(row.get("source_rule_key", ""))
        if key and row.get("runtime_allowed") is True:
            counts[key] = counts.get(key, 0) + 1
    return counts


def _blocking_gate(*, replay: dict[str, object], registry: dict[str, object]) -> str:
    if replay.get("status") != "ready":
        return "rule_replay_eval_not_ready"
    if int(replay.get("runtime_activation_count", 0) or 0) <= 0:
        return "rule_replay_eval_has_no_runtime_candidates"
    if registry.get("status") != "ready":
        return "decision_registry_iteration_not_ready"
    if int(registry.get("runtime_activation_count", 0) or 0) <= 0:
        return "decision_registry_iteration_has_no_runtime_candidates"
    return "rule_policy_payload_empty"


def _candidate_summary(candidate: dict[str, object]) -> dict[str, object]:
    return {
        "candidate_policy_version": candidate.get("candidate_policy_version", ""),
        "rule_policy_count": candidate.get("rule_policy_count", 0),
        "blocking_gate": candidate.get("blocking_gate", ""),
    }


def _active_version(candidate_version: str, active_pointer: dict[str, object]) -> str:
    active = str(active_pointer.get("active_policy_version", "")) if active_pointer else ""
    if active == candidate_version or active == RULE_BASELINE_VERSION:
        return active or RULE_BASELINE_VERSION
    return RULE_BASELINE_VERSION


def _read_active_pointer(store: LocalJsonlStore) -> dict[str, object]:
    path = store.runtime_dir / RULE_POINTER_RELATIVE_PATH
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(payload, dict) or payload.get("version") != RULE_ACTIVE_POINTER_VERSION:
        return {}
    return dict(payload) | {"source_path": path}


def _write_active_pointer(store: LocalJsonlStore, payload: dict[str, object]) -> Path:
    path = store.runtime_dir / RULE_POINTER_RELATIVE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return path


def _append_pointer_audit(store: LocalJsonlStore, event_version: str, pointer: dict[str, object]) -> dict[str, object]:
    return store.append_record(
        RULE_POINTER_AUDIT_LEDGER,
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
                "RULE_POINTER_AUDIT_APPEND_ONLY",
                "NO_SECRET_VALUES_RENDERED",
            ],
        },
    )


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
