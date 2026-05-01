from __future__ import annotations

import hashlib
import re

from v20.interaction.feedback import FeatureCalibrationSignal
from v20.learning.ledger import LedgerEntry
from v20.learning.proposal import LearningProposal
from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env

PORTRAIT_CALIBRATION_SIGNALS = ("confirm", "reject", "needs_review", "evidence_gap")


def analyze_portrait_calibration(
    *,
    input_id: str,
    feature_id: str,
    source_role: str,
    signal: str,
    note: str = "",
    locale: str = "zh",
) -> dict[str, object]:
    if signal not in PORTRAIT_CALIBRATION_SIGNALS:
        raise ValueError(f"Unsupported portrait calibration signal: {signal}")
    source_hash = _source_hash(input_id, feature_id, source_role, signal, note)
    redacted_note = _redact_note(note)
    calibration = FeatureCalibrationSignal(
        feature_id=feature_id,
        profile_id=source_hash,
        signal=signal,
        source_role=source_role,
        note=redacted_note[:180] or "portrait_calibration_signal",
    )
    proposal = LearningProposal(
        proposal_id=f"v20.portrait.calibration.proposal.{source_hash}",
        proposal_type="portrait_feature_calibration_review",
        summary=f"Review portrait calibration signal {signal} for {feature_id}.",
        risk="low" if signal in {"confirm", "needs_review"} else "medium",
    )
    ledger = LedgerEntry(
        run_id=f"v20.portrait.calibration.run.{source_hash}",
        source="portrait_calibration_analyzer",
        input_hash=source_hash,
        artifact_hash=_source_hash(feature_id, signal, redacted_note, locale),
    )
    return {
        "version": "v20.portrait_calibration_report.v1",
        "source_hash": source_hash,
        "raw_note_retained": False,
        "redacted_note": redacted_note,
        "calibration_signal": calibration.to_dict(),
        "learning_proposal": proposal.to_dict(),
        "ledger_entry": ledger.to_dict(),
        "runtime_mutation": False,
        "guardrails": [
            "PORTRAIT_CALIBRATION_SIGNAL_ONLY",
            "NO_QUESTION_RANKING_MUTATION",
            "NO_ANSWER_CONCLUSION_MUTATION",
            "VALIDATION_REQUIRED_BEFORE_POLICY_USE",
        ],
    }


def record_portrait_calibration(
    *,
    input_id: str,
    feature_id: str,
    source_role: str,
    signal: str,
    note: str = "",
    locale: str = "zh",
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    analysis = analyze_portrait_calibration(
        input_id=input_id,
        feature_id=feature_id,
        source_role=source_role,
        signal=signal,
        note=note,
        locale=locale,
    )
    storage = (store or local_jsonl_store_from_env()).append_record("portrait_calibration_ledger", _persistable_payload(analysis))
    return {
        "version": "v20.portrait_calibration_record_result.v1",
        "analysis": analysis,
        "storage": storage,
        "runtime_mutation": True,
        "guardrails": [
            "APPEND_ONLY_PORTRAIT_CALIBRATION",
            "ONLY_REDACTED_ANALYSIS_IS_PERSISTED",
            "NO_RUNTIME_FEATURE_MUTATION",
        ],
    }


def _persistable_payload(analysis: dict[str, object]) -> dict[str, object]:
    return {
        "version": analysis["version"],
        "source_hash": analysis["source_hash"],
        "redacted_note": analysis["redacted_note"],
        "calibration_signal": analysis["calibration_signal"],
        "learning_proposal": analysis["learning_proposal"],
        "ledger_entry": analysis["ledger_entry"],
        "raw_note_retained": analysis["raw_note_retained"],
        "runtime_mutation": False,
    }


def _source_hash(*values: str) -> str:
    raw = "|".join(values)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _redact_note(text: str) -> str:
    value = text.strip()
    value = re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", "[email]", value)
    value = re.sub(r"\b(?:\+?\d[\d -]{6,}\d)\b", "[number]", value)
    value = re.sub(r"(姓名|名字|name)\s*[:：]\s*[\w\u4e00-\u9fff]+", r"\1:[redacted]", value, flags=re.IGNORECASE)
    return value
