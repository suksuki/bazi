from __future__ import annotations

from v20.interaction.feedback_analysis import analyze_feedback
from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


def record_feedback_analysis(
    *,
    input_id: str,
    source_role: str,
    feedback_text: str,
    feature_ids: tuple[str, ...] = (),
    locale: str = "zh",
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    analysis = analyze_feedback(
        input_id=input_id,
        source_role=source_role,
        feedback_text=feedback_text,
        feature_ids=feature_ids,
        locale=locale,
    )
    storage = (store or local_jsonl_store_from_env()).append_record("feedback_ledger", _persistable_payload(analysis))
    return {
        "version": "v20.feedback_record_result.v1",
        "analysis": analysis,
        "storage": storage,
        "runtime_mutation": True,
        "guardrails": [
            "FEEDBACK_RECORD_APPEND_ONLY",
            "ONLY_REDACTED_ANALYSIS_IS_PERSISTED",
            "NO_RULE_OR_FEATURE_MUTATION",
        ],
    }


def _persistable_payload(analysis: dict[str, object]) -> dict[str, object]:
    return {
        "version": analysis["version"],
        "source_hash": analysis["source_hash"],
        "raw_feedback_retained": analysis["raw_feedback_retained"],
        "redacted_summary": analysis["redacted_summary"],
        "candidate_domains": analysis["candidate_domains"],
        "calibration_signals": analysis["calibration_signals"],
        "learning_proposal": analysis["learning_proposal"],
        "ledger_entry": analysis["ledger_entry"],
        "guardrails": analysis["guardrails"],
    }
