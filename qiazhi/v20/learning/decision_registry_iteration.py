from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from v20.learning.rule_activation import build_rule_activation_report
from v20.learning.rule_subcondition_split import (
    build_rule_subcondition_split_report,
    read_rule_subcondition_split_artifact,
)
from v20.storage.local_jsonl import local_jsonl_store_from_env

ProgressCallback = Callable[[str], None]


def build_decision_registry_iteration_report(
    domain: str = "",
    *,
    limit: int = 0,
    per_rule: int = 0,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    limit_value = _normalize_limit(limit)
    per_rule_value = _normalize_limit(per_rule)
    gate = build_rule_activation_report(domain, limit=limit_value)
    split = build_rule_subcondition_split_report(
        domain,
        limit=limit_value,
        per_rule=per_rule_value,
        progress=progress,
    )
    split_by_rule_key = {
        str(row.get("rule_key", "")): row
        for row in split.get("packets", ())
        if isinstance(row, dict) and row.get("rule_key")
    }
    records = []
    gate_packets = [row for row in gate.get("packets", ()) if isinstance(row, dict)]
    for index, packet in enumerate(gate_packets, start=1):
        _emit(progress, f"[{index}/{len(gate_packets)}] registry {packet.get('domain', '')}")
        records.extend(_decision_records_for_packet(packet, split_by_rule_key.get(str(packet.get("rule_key", "")), {})))

    status_counts = Counter(str(row["decision_status"]) for row in records)
    subject_counts = Counter(str(row["subject_type"]) for row in records)
    triage_counts = Counter(str(row["triage_lane"]) for row in records)
    return {
        "version": "v20.decision_registry_iteration_report.v1",
        "status": "ready" if records else "empty",
        "domain": domain.strip(),
        "decision_record_count": len(records),
        "batch_iteration_signal_count": sum(1 for row in records if row["triage_lane"] == "batch_iteration_signal"),
        "system_iteration_count": sum(1 for row in records if row["triage_lane"] == "system_iteration"),
        "runtime_activation_count": sum(1 for row in records if row.get("runtime_allowed") is True),
        "decision_status_counts": dict(sorted(status_counts.items())),
        "subject_type_counts": dict(sorted(subject_counts.items())),
        "triage_lane_counts": dict(sorted(triage_counts.items())),
        "records": tuple(records),
        "upstream": {
            "activation_status": gate.get("status", ""),
            "activation_packet_count": gate.get("packet_count", 0),
            "subcondition_split_status": split.get("status", ""),
            "subcondition_packet_count": split.get("packet_count", 0),
            "subcondition_count": split.get("subcondition_count", 0),
        },
        "runtime_mutation": False,
        "guardrails": [
            "DECISION_REGISTRY_IS_ITERATION_LEDGER",
            "ITERATION_RECORD_FEEDS_ACTIVE_RUNTIME",
            "BATCH_ITERATION_IS_ACTIVE_SIGNAL",
            "ITERATION_RECORDS_REFINE_ACTIVE_RULES",
        ],
    }


def write_decision_registry_iteration_artifact(
    *,
    domain: str = "",
    limit: int = 0,
    per_rule: int = 0,
    output_dir: Path | None = None,
    progress: ProgressCallback | None = None,
) -> dict[str, object]:
    report = build_decision_registry_iteration_report(
        domain,
        limit=_normalize_limit(limit),
        per_rule=_normalize_limit(per_rule),
        progress=progress,
    )
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    directory = output_dir or runtime_dir / "training" / "decision_registry_iteration"
    directory.mkdir(parents=True, exist_ok=True)
    latest_path = directory / "latest.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = f"_{_safe(domain)}" if domain.strip() else ""
    run_path = directory / f"decision_registry_iteration{suffix}_{stamp}.json"
    payload = report | {
        "written_at": datetime.now(timezone.utc).isoformat(),
        "runtime_mutation": True,
    }
    latest_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    return {
        "version": "v20.decision_registry_iteration_artifact_write.v1",
        "status": "written",
        "latest_path": str(latest_path),
        "run_path": str(run_path),
        "report_status": report["status"],
        "decision_record_count": report["decision_record_count"],
        "batch_iteration_signal_count": report["batch_iteration_signal_count"],
        "system_iteration_count": report["system_iteration_count"],
        "runtime_mutation": True,
        "guardrails": [
            "LOCAL_RUNTIME_ARTIFACT_ONLY",
            "NO_POSTGRES_WRITE",
            "ACTIVE_RULE_ITERATION",
        ],
    }


def read_decision_registry_iteration_artifact(*, output_dir: Path | None = None) -> dict[str, object]:
    latest_split = read_rule_subcondition_split_artifact()
    runtime_dir = local_jsonl_store_from_env().runtime_dir
    latest_path = (output_dir or runtime_dir / "training" / "decision_registry_iteration") / "latest.json"
    if not latest_path.exists():
        return {
            "version": "v20.decision_registry_iteration_artifact_status.v1",
            "status": "not_built",
            "latest_path": str(latest_path),
            "upstream_subcondition_status": latest_split.get("status", "not_built"),
            "runtime_mutation": False,
        }
    return json.loads(latest_path.read_text(encoding="utf-8")) | {
        "latest_path": str(latest_path),
        "runtime_mutation": False,
    }


def _decision_records_for_packet(packet: dict[str, object], split_packet: dict[str, object]) -> tuple[dict[str, object], ...]:
    lane = str(packet.get("activation_lane", ""))
    if lane in {"needs_subcondition_split", "subcondition_review_ready", "subcondition_active_ready"}:
        subconditions = [
            _subcondition_record(packet, row)
            for row in split_packet.get("subconditions", ())
            if isinstance(row, dict)
        ]
        counterexamples = [
            _counterexample_record(packet, row)
            for row in split_packet.get("counterexample_candidates", ())
            if isinstance(row, dict)
        ]
        return tuple(subconditions + counterexamples)
    if lane == "active_weight_ready":
        return (_active_weight_record(packet),)
    return (_manual_packet_record(packet),)


def _base_record(
    packet: dict[str, object],
    *,
    subject_id: str,
    subject_type: str,
    proposed_decision: str,
    triage_lane: str,
    rationale: str,
    support_count: int = 0,
    support_weight: float = 0.0,
    payload: dict[str, object] | None = None,
) -> dict[str, object]:
    decision_id = f"v20.decision_review.{_hash(str(packet.get('rule_key', '')), subject_id, proposed_decision)}"
    return {
        "version": "v20.decision_registry_iteration_record.v1",
        "decision_id": decision_id,
        "decision_status": "active_iteration",
        "subject_id": subject_id,
        "subject_type": subject_type,
        "source_rule_key": packet.get("rule_key", ""),
        "source_knowledge_id": packet.get("source_knowledge_id", ""),
        "domain": packet.get("domain", ""),
        "portrait": packet.get("portrait", ""),
        "question": packet.get("question", ""),
        "activation_lane": packet.get("activation_lane", ""),
        "proposed_decision": proposed_decision,
        "triage_lane": triage_lane,
        "reviewer_role": "system_or_practitioner_architect",
        "support_count": support_count,
        "support_weight": support_weight,
        "rationale": rationale,
        "runtime_effect": "active_runtime_iteration",
        "runtime_allowed": True,
        "payload": payload or {},
        "guardrails": [
            "RECORD_IS_ACTIVE_ITERATION_SIGNAL",
            "RUNTIME_ACTIVATION_ALLOWED_WITH_TRACE",
            "ITERATION_LEDGER_RECORDS_RUNTIME_CHANGES",
        ],
    }


def _subcondition_record(packet: dict[str, object], subcondition: dict[str, object]) -> dict[str, object]:
    support_count = int(subcondition.get("support_count", 0) or 0)
    support_weight = float(subcondition.get("support_weight", 0.0) or 0.0)
    triage_lane = "batch_iteration_signal" if support_count >= 100 and support_weight >= 0.0002 else "system_iteration"
    return _base_record(
        packet,
        subject_id=str(subcondition.get("subcondition_key", "")),
        subject_type="rule_subcondition_signal",
        proposed_decision="activate_for_replay_eval",
        triage_lane=triage_lane,
        rationale=str(subcondition.get("iteration_prompt", "")),
        support_count=support_count,
        support_weight=support_weight,
        payload={
            "rank": subcondition.get("rank", 0),
            "feature_ids": subcondition.get("feature_ids", ()),
            "discriminator_feature_ids": subcondition.get("discriminator_feature_ids", ()),
            "condition_model": subcondition.get("condition_model", {}),
        },
    )


def _counterexample_record(packet: dict[str, object], counterexample: dict[str, object]) -> dict[str, object]:
    return _base_record(
        packet,
        subject_id=str(counterexample.get("counterexample_key", "")),
        subject_type="rule_counterexample_signal",
        proposed_decision="iterate_as_exclusion_or_split",
        triage_lane="system_iteration",
        rationale=str(counterexample.get("iteration_question", "")),
        support_count=int(counterexample.get("support_count", 0) or 0),
        support_weight=float(counterexample.get("support_weight", 0.0) or 0.0),
        payload={
            "cluster_id": counterexample.get("cluster_id", ""),
            "cluster_key": counterexample.get("cluster_key", ""),
            "contrast_against_broad_features": counterexample.get("contrast_against_broad_features", ()),
        },
    )


def _active_weight_record(packet: dict[str, object]) -> dict[str, object]:
    return _base_record(
        packet,
        subject_id=str(packet.get("packet_id", "")),
        subject_type="active_weight_signal",
        proposed_decision="activate_weight_for_runtime_replay",
        triage_lane="system_iteration",
        rationale="合成验证与语料先验均已通过，可进入运行回放权重迭代；并进入持续运行调优。",
        support_count=int(packet.get("synthetic_case_count", 0) or 0),
        support_weight=float(packet.get("support_ratio", 0.0) or 0.0),
        payload={
            "synthetic_confidence": packet.get("synthetic_confidence", 0.0),
            "required_evidence_before_runtime": packet.get("required_evidence_before_runtime", ()),
        },
    )


def _manual_packet_record(packet: dict[str, object]) -> dict[str, object]:
    return _base_record(
        packet,
        subject_id=str(packet.get("packet_id", "")),
        subject_type="activation_packet_iteration",
        proposed_decision=str(packet.get("iteration_action", "system_iteration")),
        triage_lane="system_iteration",
        rationale=str(packet.get("risk", "system iteration required")),
        support_count=int(packet.get("synthetic_case_count", 0) or 0),
        support_weight=float(packet.get("support_ratio", 0.0) or 0.0),
        payload={
            "human_decision_options": packet.get("human_decision_options", ()),
            "required_evidence_before_runtime": packet.get("required_evidence_before_runtime", ()),
        },
    )


def _hash(*values: str) -> str:
    return hashlib.sha256("|".join(values).encode("utf-8")).hexdigest()[:16]


def _safe(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value.strip())


def _normalize_limit(value: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, parsed)


def _emit(progress: ProgressCallback | None, message: str) -> None:
    if progress is not None:
        progress(f"[v20-decision-registry-iteration] {message}")
