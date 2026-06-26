from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence

from pydantic import Field

from v30.contracts import V30Model
from v30.policy.promotion import PolicyCandidate, PromotionResult
from v30.policy.runtime_pointer import RuntimePointerStore


TRAINING_CANDIDATE_QUARANTINE_VERSION = "v30.training_candidate_quarantine_record.v1"


class TrainingCandidateQuarantineRecord(V30Model):
    version: str = TRAINING_CANDIDATE_QUARANTINE_VERSION
    record_id: str
    candidate_id: str
    family: str
    status: str = "quarantined"
    created_at: datetime
    source_signal_ids: list[str] = Field(default_factory=list)
    source_signal_count: int = 0
    failed_validation_ids: list[str] = Field(default_factory=list)
    validation_run_id: str = ""
    failures: list[str] = Field(default_factory=list)
    rollback_target_pointer: dict[str, Any] = Field(default_factory=dict)
    active_pointer_before: dict[str, Any] = Field(default_factory=dict)
    active_pointer_after: dict[str, Any] = Field(default_factory=dict)
    pointer_unchanged: bool = True
    candidate_payload_summary: dict[str, Any] = Field(default_factory=dict)
    remediation_route: dict[str, Any] = Field(default_factory=dict)
    artifact_uri: str = ""
    boundary: str = "failed_training_candidate_is_quarantined_without_runtime_pointer_write"


def quarantine_failed_candidate(
    *,
    candidate: PolicyCandidate,
    promotion: PromotionResult,
    store: RuntimePointerStore | None = None,
    source_signals: Sequence[Mapping[str, Any] | Any] = (),
    persist: bool = True,
) -> TrainingCandidateQuarantineRecord:
    store = store or RuntimePointerStore()
    before = store.load_pointer(candidate.family)
    record = build_training_candidate_quarantine_record(
        candidate=candidate,
        promotion=promotion,
        active_pointer_before=before.model_dump(mode="json"),
        active_pointer_after=store.load_pointer(candidate.family).model_dump(mode="json"),
        source_signals=source_signals,
    )
    if not persist:
        return record
    path = _quarantine_path(store, record)
    path.parent.mkdir(parents=True, exist_ok=True)
    persisted = record.model_copy(update={"artifact_uri": str(path)})
    path.write_text(json.dumps(persisted.model_dump(mode="json"), ensure_ascii=False, indent=2), encoding="utf-8")
    return persisted


def build_training_candidate_quarantine_record(
    *,
    candidate: PolicyCandidate,
    promotion: PromotionResult,
    active_pointer_before: Mapping[str, Any],
    active_pointer_after: Mapping[str, Any],
    source_signals: Sequence[Mapping[str, Any] | Any] = (),
) -> TrainingCandidateQuarantineRecord:
    before = dict(active_pointer_before)
    after = dict(active_pointer_after)
    return TrainingCandidateQuarantineRecord(
        record_id=f"{candidate.family}.{candidate.candidate_id}.quarantine",
        candidate_id=candidate.candidate_id,
        family=candidate.family,
        created_at=datetime.now(timezone.utc),
        source_signal_ids=_source_signal_ids(source_signals),
        source_signal_count=len(source_signals),
        failed_validation_ids=_failed_validation_ids(promotion),
        validation_run_id=promotion.validation_run_id,
        failures=list(promotion.failures),
        rollback_target_pointer=_rollback_target(before),
        active_pointer_before=before,
        active_pointer_after=after,
        pointer_unchanged=before.get("active_artifact_id") == after.get("active_artifact_id"),
        candidate_payload_summary=_candidate_payload_summary(candidate),
        remediation_route=_remediation_route(candidate, promotion),
    )


def _source_signal_ids(source_signals: Sequence[Mapping[str, Any] | Any]) -> list[str]:
    ids: list[str] = []
    for signal in source_signals:
        if isinstance(signal, Mapping):
            signal_id = str(signal.get("signal_id") or "")
        else:
            signal_id = str(getattr(signal, "signal_id", "") or "")
        if signal_id:
            ids.append(signal_id)
    return sorted(set(ids))


def _failed_validation_ids(promotion: PromotionResult) -> list[str]:
    ids = [row for row in str(promotion.validation_run_id or "").split("+") if row]
    if not ids:
        ids = ["unrecorded_validation_failure"]
    return ids


def _rollback_target(pointer: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "family": pointer.get("family", ""),
        "active_artifact_id": pointer.get("active_artifact_id", ""),
        "active_artifact_version": pointer.get("active_artifact_version", ""),
        "status": pointer.get("status", ""),
    }


def _candidate_payload_summary(candidate: PolicyCandidate) -> dict[str, Any]:
    payload = candidate.payload
    weights = payload.get("weights", {}) if isinstance(payload, Mapping) else {}
    training_signals = payload.get("training_signals", []) if isinstance(payload, Mapping) else []
    return {
        "base_artifact_id": candidate.base_artifact_id,
        "payload_mode": str(payload.get("mode") or "") if isinstance(payload, Mapping) else "",
        "payload_family": str(payload.get("family") or "") if isinstance(payload, Mapping) else "",
        "weight_key_count": len(weights) if isinstance(weights, Mapping) else 0,
        "training_signal_count": len(training_signals) if isinstance(training_signals, list) else 0,
        "change_summary": candidate.change_summary,
    }


def _remediation_route(candidate: PolicyCandidate, promotion: PromotionResult) -> dict[str, Any]:
    first_failure = promotion.failures[0] if promotion.failures else "unknown_training_candidate_failure"
    return {
        "route_id": "route.training_candidate_quarantine",
        "module_target": "training candidate",
        "task_family": "training_candidate_validation_review",
        "candidate_id": candidate.candidate_id,
        "family": candidate.family,
        "first_failure": first_failure,
        "default_action": "inspect source signals, validation replay, and candidate weights before any retry",
        "runtime_pointer_write_allowed": False,
        "chart_fact_mutation_allowed": False,
    }


def _quarantine_path(store: RuntimePointerStore, record: TrainingCandidateQuarantineRecord) -> Path:
    settings = getattr(store, "_settings")
    return settings.runtime_dir / "quarantine" / "training_candidates" / f"{record.record_id}.json"
