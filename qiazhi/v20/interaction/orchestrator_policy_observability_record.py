from __future__ import annotations

import hashlib
import json

from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


LEDGER_NAME = "orchestrator_policy_observability_ledger"
OBSERVABILITY_VERSION = "v20.orchestrator_policy_observability.v1"


def analyze_policy_observability(
    *,
    input_id: str,
    source_role: str,
    policy_observability: dict[str, object],
    locale: str = "zh",
) -> dict[str, object]:
    _validate_source_role(source_role)
    _validate_observability(policy_observability)
    persistable = _persistable_observability(policy_observability)
    source_hash = _source_hash(input_id, source_role, locale, json.dumps(persistable, ensure_ascii=False, sort_keys=True))
    return {
        "version": "v20.orchestrator_policy_observability_analysis.v1",
        "source_hash": source_hash,
        "source_role": source_role,
        "input_id": input_id,
        "active_policy_version": persistable.get("active_policy_version", ""),
        "candidate_policy_version": persistable.get("candidate_policy_version", ""),
        "rollback_policy_version": persistable.get("rollback_policy_version", ""),
        "status": persistable.get("status", ""),
        "fallback_active": persistable.get("fallback_active", False),
        "applied_consumer_count": persistable.get("applied_consumer_count", 0),
        "policy_observability": persistable,
        "runtime_mutation": False,
        "guardrails": [
            "POLICY_OBSERVABILITY_ANALYSIS_ONLY",
            "NO_USER_TEXT_PERSISTED",
            "NO_POLICY_WRITE_FROM_OBSERVATION",
            "APPEND_REQUIRES_EXPLICIT_ENDPOINT_OR_SCRIPT",
        ],
    }


def record_policy_observability(
    *,
    input_id: str,
    source_role: str,
    policy_observability: dict[str, object],
    locale: str = "zh",
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    analysis = analyze_policy_observability(
        input_id=input_id,
        source_role=source_role,
        policy_observability=policy_observability,
        locale=locale,
    )
    storage = (store or local_jsonl_store_from_env()).append_record(LEDGER_NAME, _persistable_payload(analysis))
    return {
        "version": "v20.orchestrator_policy_observability_record_result.v1",
        "analysis": analysis,
        "storage": storage,
        "runtime_mutation": True,
        "guardrails": [
            "APPEND_ONLY_POLICY_OBSERVABILITY",
            "NO_POLICY_WRITE_FROM_OBSERVATION",
            "NO_USER_VISIBLE_VERDICT_MUTATION",
        ],
    }


def _persistable_payload(analysis: dict[str, object]) -> dict[str, object]:
    return {
        "version": analysis["version"],
        "source_hash": analysis["source_hash"],
        "source_role": analysis["source_role"],
        "input_id": analysis["input_id"],
        "active_policy_version": analysis["active_policy_version"],
        "candidate_policy_version": analysis["candidate_policy_version"],
        "rollback_policy_version": analysis["rollback_policy_version"],
        "status": analysis["status"],
        "fallback_active": analysis["fallback_active"],
        "applied_consumer_count": analysis["applied_consumer_count"],
        "policy_observability": analysis["policy_observability"],
        "runtime_mutation": False,
        "guardrails": analysis["guardrails"],
    }


def _persistable_observability(observability: dict[str, object]) -> dict[str, object]:
    consumers = []
    for row in observability.get("consumers", ()):
        if not isinstance(row, dict):
            continue
        consumers.append(
            {
                "module_key": str(row.get("module_key", "")),
                "status": str(row.get("status", "")),
                "active_policy_version": str(row.get("active_policy_version", "")),
                "applied_adjustment_count": int(row.get("applied_adjustment_count", 0) or 0),
                "domain_boost": float(row.get("domain_boost", 0) or 0),
                "runtime_mutation": False,
            }
        )
    return {
        "version": OBSERVABILITY_VERSION,
        "status": str(observability.get("status", "")),
        "active_policy_version": str(observability.get("active_policy_version", "")),
        "candidate_policy_version": str(observability.get("candidate_policy_version", "")),
        "rollback_policy_version": str(observability.get("rollback_policy_version", "")),
        "runtime_applied": bool(observability.get("runtime_applied", False)),
        "fallback_active": bool(observability.get("fallback_active", False)),
        "consumer_count": len(consumers),
        "applied_consumer_count": int(observability.get("applied_consumer_count", 0) or 0),
        "consumers": consumers,
        "runtime_mutation": False,
    }


def _validate_observability(observability: dict[str, object]) -> None:
    if not isinstance(observability, dict):
        raise ValueError("policy_observability must be an object")
    if observability.get("version") != OBSERVABILITY_VERSION:
        raise ValueError(f"Unsupported policy_observability version: {observability.get('version', '')}")
    if not str(observability.get("active_policy_version", "")):
        raise ValueError("policy_observability.active_policy_version is required")
    if not isinstance(observability.get("consumers", ()), (list, tuple)):
        raise ValueError("policy_observability.consumers must be a list")
    text = json.dumps(observability, ensure_ascii=False, sort_keys=True)
    blocked = ("user_text", "feedback_text", "raw_feedback", "raw_private", "email", "phone")
    if any(token in text for token in blocked):
        raise ValueError("policy_observability contains raw text or private-field markers")


def _validate_source_role(source_role: str) -> None:
    if source_role not in {"analyst", "admin", "lab", "practitioner", "system"}:
        raise ValueError(f"Unsupported policy observability source role: {source_role}")


def _source_hash(*values: str) -> str:
    return hashlib.sha256("|".join(values).encode("utf-8")).hexdigest()[:16]
