from __future__ import annotations

import hashlib
import re

from v20.interaction.feedback import FeatureCalibrationSignal
from v20.learning.ledger import LedgerEntry
from v20.learning.proposal import LearningProposal
from v20.llm.tasks import summarize_feedback


def analyze_feedback(
    *,
    input_id: str,
    source_role: str,
    feedback_text: str,
    feature_ids: tuple[str, ...] = (),
    locale: str = "zh",
) -> dict[str, object]:
    redacted = _redact_feedback(feedback_text)
    source_hash = _source_hash(input_id, source_role, feedback_text)
    llm_summary = summarize_feedback(redacted, locale=locale)
    domains = tuple(llm_summary["result"]["candidate_domains"])
    signals = tuple(
        FeatureCalibrationSignal(
            feature_id=feature_id,
            profile_id=source_hash,
            signal="needs_review",
            source_role=source_role,
            note="feedback_signal_anonymized",
        )
        for feature_id in feature_ids[:12]
    )
    proposal = LearningProposal(
        proposal_id=f"v20.feedback.proposal.{source_hash}",
        proposal_type="feedback_calibration_review",
        summary=f"Review anonymized feedback domains: {', '.join(domains) if domains else 'open'}",
        risk="low" if signals else "medium",
    )
    ledger = LedgerEntry(
        run_id=f"v20.feedback.run.{source_hash}",
        source="feedback_analyzer",
        input_hash=source_hash,
        artifact_hash=_source_hash(redacted, ",".join(domains), ",".join(feature_ids)),
    )
    return {
        "version": "v20.feedback_analysis_report.v1",
        "source_hash": source_hash,
        "raw_feedback_retained": False,
        "redacted_summary": redacted[:240],
        "llm_summary": llm_summary,
        "candidate_domains": list(domains),
        "calibration_signals": [row.to_dict() for row in signals],
        "learning_proposal": proposal.to_dict(),
        "ledger_entry": ledger.to_dict(),
        "runtime_mutation": False,
        "guardrails": [
            "FEEDBACK_ANALYSIS_ONLY",
            "RAW_FEEDBACK_NOT_RETAINED",
            "CALIBRATION_SIGNAL_REQUIRES_VALIDATION",
            "NO_AUTOMATIC_PROMOTION",
        ],
    }


def _source_hash(*values: str) -> str:
    raw = "|".join(values)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _redact_feedback(text: str) -> str:
    value = text.strip()
    value = re.sub(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", "[email]", value)
    value = re.sub(r"\b(?:\+?\d[\d -]{6,}\d)\b", "[number]", value)
    value = re.sub(r"(姓名|名字|name)\s*[:：]\s*[\w\u4e00-\u9fff]+", r"\1:[redacted]", value, flags=re.IGNORECASE)
    return value
