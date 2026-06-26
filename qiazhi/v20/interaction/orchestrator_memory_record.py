from __future__ import annotations

import hashlib
import json
from typing import Any

from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


LEDGER_NAME = "orchestrator_memory_ledger"
SIGNAL_VERSION = "v20.orchestrator_brain_memory_signal.v1"


def analyze_orchestrator_memory_signal(
    *,
    input_id: str,
    source_role: str,
    brain_memory_signal: dict[str, object],
    locale: str = "zh",
) -> dict[str, object]:
    _validate_source_role(source_role)
    _validate_signal(brain_memory_signal)
    persistable = _persistable_signal(brain_memory_signal)
    source_hash = _source_hash(input_id, source_role, locale, json.dumps(persistable, ensure_ascii=False, sort_keys=True))
    return {
        "version": "v20.orchestrator_memory_signal_analysis.v1",
        "source_hash": source_hash,
        "source_role": source_role,
        "input_id": input_id,
        "memory_key": persistable.get("memory_key", ""),
        "primary_mainline_key": persistable.get("primary_mainline_key", ""),
        "selected_question_key": persistable.get("selected_question_key", ""),
        "coordination_status": persistable.get("coordination_status", ""),
        "signal_count": len(persistable.get("signals", ())) if isinstance(persistable.get("signals", ()), list) else 0,
        "brain_memory_signal": persistable,
        "runtime_mutation": False,
        "guardrails": [
            "ORCHESTRATOR_MEMORY_SIGNAL_ANALYSIS_ONLY",
            "NO_RAW_USER_TEXT_PERSISTED",
            "NO_RUNTIME_RULE_OR_MAINLINE_MUTATION",
            "RECORD_REQUIRES_EXPLICIT_ENDPOINT_OR_SCRIPT",
        ],
    }


def record_orchestrator_memory_signal(
    *,
    input_id: str,
    source_role: str,
    brain_memory_signal: dict[str, object],
    locale: str = "zh",
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    analysis = analyze_orchestrator_memory_signal(
        input_id=input_id,
        source_role=source_role,
        brain_memory_signal=brain_memory_signal,
        locale=locale,
    )
    storage = (store or local_jsonl_store_from_env()).append_record(LEDGER_NAME, _persistable_payload(analysis))
    return {
        "version": "v20.orchestrator_memory_record_result.v1",
        "analysis": analysis,
        "storage": storage,
        "runtime_mutation": True,
        "guardrails": [
            "APPEND_ONLY_ORCHESTRATOR_MEMORY_SIGNAL",
            "NO_RUNTIME_RULE_OR_MAINLINE_MUTATION",
            "NO_USER_VISIBLE_VERDICT_MUTATION",
        ],
    }


def _persistable_payload(analysis: dict[str, object]) -> dict[str, object]:
    return {
        "version": analysis["version"],
        "source_hash": analysis["source_hash"],
        "source_role": analysis["source_role"],
        "input_id": analysis["input_id"],
        "memory_key": analysis["memory_key"],
        "primary_mainline_key": analysis["primary_mainline_key"],
        "selected_question_key": analysis["selected_question_key"],
        "coordination_status": analysis["coordination_status"],
        "signal_count": analysis["signal_count"],
        "brain_memory_signal": analysis["brain_memory_signal"],
        "runtime_mutation": False,
        "guardrails": analysis["guardrails"],
    }


def _persistable_signal(signal: dict[str, object]) -> dict[str, object]:
    rows = []
    for row in signal.get("signals", ()):
        if not isinstance(row, dict):
            continue
        rows.append(
            {
                "signal_key": str(row.get("signal_key", "")),
                "signal_type": str(row.get("signal_type", "")),
                "domain": str(row.get("domain", "")),
                "target": str(row.get("target", "")),
                "direction": str(row.get("direction", "")),
                "strength": row.get("strength", 0),
                "allowed_use": str(row.get("allowed_use", "")),
                "runtime_rule_mutation": bool(row.get("runtime_rule_mutation", False)),
            }
        )
    return {
        "version": SIGNAL_VERSION,
        "status": str(signal.get("status", "")),
        "memory_key": str(signal.get("memory_key", "")),
        "primary_mainline_key": str(signal.get("primary_mainline_key", "")),
        "primary_title": str(signal.get("primary_title", "")),
        "primary_domain": str(signal.get("primary_domain", "")),
        "selected_question_key": str(signal.get("selected_question_key", "")),
        "selected_question_domain": str(signal.get("selected_question_domain", "")),
        "question_focus_status": str(signal.get("question_focus_status", "")),
        "coordination_status": str(signal.get("coordination_status", "")),
        "coordination_flags": [str(row) for row in signal.get("coordination_flags", ()) if str(row)] if isinstance(signal.get("coordination_flags", ()), (list, tuple)) else [],
        "signal_count": len(rows),
        "signals": rows,
        "runtime_mutation": False,
    }


def _validate_signal(signal: dict[str, object]) -> None:
    if not isinstance(signal, dict):
        raise ValueError("brain_memory_signal must be an object")
    if signal.get("version") != SIGNAL_VERSION:
        raise ValueError(f"Unsupported brain_memory_signal version: {signal.get('version', '')}")
    if not str(signal.get("memory_key", "")):
        raise ValueError("brain_memory_signal.memory_key is required")
    if not isinstance(signal.get("signals", ()), (list, tuple)):
        raise ValueError("brain_memory_signal.signals must be a list")
    text = json.dumps(signal, ensure_ascii=False, sort_keys=True)
    blocked = ("user_text", "feedback_text", "raw_feedback", "raw_private", "email", "phone")
    if any(token in text for token in blocked):
        raise ValueError("brain_memory_signal contains raw text or private-field markers")


def _validate_source_role(source_role: str) -> None:
    if source_role not in {"analyst", "admin", "lab", "practitioner"}:
        raise ValueError(f"Unsupported orchestrator memory source role: {source_role}")


def _source_hash(*values: str) -> str:
    return hashlib.sha256("|".join(values).encode("utf-8")).hexdigest()[:16]
