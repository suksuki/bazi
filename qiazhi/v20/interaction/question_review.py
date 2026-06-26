from __future__ import annotations

import hashlib
import json

from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


LEDGER_NAME = "question_review_ledger"
REVIEW_VERSION = "v20.question_review_signal.v1"

QUESTION_REVIEW_ACTIONS: tuple[str, ...] = (
    "approve",
    "rewrite",
    "downrank",
    "merge",
    "delete",
)

QUESTION_REVIEW_REASONS: tuple[str, ...] = (
    "role_mismatch",
    "mainline_mismatch",
    "too_technical",
    "duplicate",
    "unfocused",
)


def analyze_question_review(
    *,
    input_id: str,
    source_role: str,
    question: dict[str, object],
    action: str,
    reason: str = "",
    locale: str = "zh",
) -> dict[str, object]:
    _validate_source_role(source_role)
    _validate_action(action)
    _validate_reason(reason)
    _validate_no_raw_markers(question)
    persistable = _persistable_question(question)
    _validate_question_payload(persistable)
    source_hash = _source_hash(
        input_id,
        source_role,
        action,
        reason,
        locale,
        json.dumps(persistable, ensure_ascii=False, sort_keys=True),
    )
    return {
        "version": "v20.question_review_analysis.v1",
        "source_hash": source_hash,
        "source_role": source_role,
        "input_id": input_id,
        "action": action,
        "reason": reason,
        "question_key": persistable.get("question_key", ""),
        "question_id": persistable.get("question_id", ""),
        "domain": persistable.get("domain", ""),
        "stage": persistable.get("stage", ""),
        "role_target": persistable.get("role_target", ""),
        "review_signal": persistable,
        "runtime_mutation": False,
        "guardrails": [
            "QUESTION_REVIEW_ANALYSIS_ONLY",
            "NO_RAW_USER_TEXT_PERSISTED",
            "NO_QUESTION_TITLE_PERSISTED",
            "NO_RUNTIME_RULE_OR_MAINLINE_MUTATION",
            "QUESTION_REVIEW_TRAINS_CANDIDATE_POLICY_ONLY",
        ],
    }


def record_question_review(
    *,
    input_id: str,
    source_role: str,
    question: dict[str, object],
    action: str,
    reason: str = "",
    locale: str = "zh",
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    analysis = analyze_question_review(
        input_id=input_id,
        source_role=source_role,
        question=question,
        action=action,
        reason=reason,
        locale=locale,
    )
    storage = (store or local_jsonl_store_from_env()).append_record(LEDGER_NAME, _persistable_payload(analysis))
    return {
        "version": "v20.question_review_record_result.v1",
        "analysis": analysis,
        "storage": storage,
        "runtime_mutation": True,
        "guardrails": [
            "APPEND_ONLY_QUESTION_REVIEW_SIGNAL",
            "NO_RUNTIME_RULE_OR_MAINLINE_MUTATION",
            "NO_USER_VISIBLE_VERDICT_MUTATION",
        ],
    }


def question_review_manifest() -> dict[str, object]:
    return {
        "version": "v20.question_review_manifest.v1",
        "actions": QUESTION_REVIEW_ACTIONS,
        "reasons": QUESTION_REVIEW_REASONS,
        "ledger_name": LEDGER_NAME,
        "runtime_mutation": False,
        "guardrails": [
            "QUESTION_REVIEW_IS_STRUCTURED_ONLY",
            "QUESTION_REVIEW_TRAINS_CANDIDATE_POLICY_ONLY",
            "NO_RUNTIME_RULE_OR_MAINLINE_MUTATION",
        ],
    }


def _persistable_payload(analysis: dict[str, object]) -> dict[str, object]:
    return {
        "version": analysis["version"],
        "source_hash": analysis["source_hash"],
        "source_role": analysis["source_role"],
        "input_id": analysis["input_id"],
        "action": analysis["action"],
        "reason": analysis["reason"],
        "question_key": analysis["question_key"],
        "question_id": analysis["question_id"],
        "domain": analysis["domain"],
        "stage": analysis["stage"],
        "role_target": analysis["role_target"],
        "review_signal": analysis["review_signal"],
        "runtime_mutation": False,
        "guardrails": analysis["guardrails"],
    }


def _persistable_question(question: dict[str, object]) -> dict[str, object]:
    return {
        "version": REVIEW_VERSION,
        "question_key": str(question.get("question_key", "")),
        "question_id": str(question.get("question_id", "")),
        "domain": str(question.get("domain", "")),
        "stage": str(question.get("stage") or question.get("measurement_stage") or question.get("role_view_level") or ""),
        "role_target": str(question.get("role_target") or question.get("role") or ""),
        "question_strategy": str(question.get("question_strategy", "")),
        "source": str(question.get("source", "")),
        "runtime_mutation": False,
    }


def _validate_source_role(source_role: str) -> None:
    if source_role not in {"analyst", "admin", "lab", "practitioner"}:
        raise ValueError(f"Unsupported question review source role: {source_role}")


def _validate_action(action: str) -> None:
    if action not in QUESTION_REVIEW_ACTIONS:
        raise ValueError(f"Unsupported question review action: {action}")


def _validate_reason(reason: str) -> None:
    if reason and reason not in QUESTION_REVIEW_REASONS:
        raise ValueError(f"Unsupported question review reason: {reason}")


def _validate_question_payload(question: dict[str, object]) -> None:
    if not str(question.get("question_key", "")) and not str(question.get("question_id", "")):
        raise ValueError("question_key or question_id is required")


def _validate_no_raw_markers(question: dict[str, object]) -> None:
    text = json.dumps(question, ensure_ascii=False, sort_keys=True)
    blocked = ("title", "source_title", "user_text", "feedback_text", "raw_feedback", "raw_private", "email", "phone")
    if any(token in text for token in blocked):
        raise ValueError("question review contains raw text or private-field markers")


def _source_hash(*values: str) -> str:
    return hashlib.sha256("|".join(values).encode("utf-8")).hexdigest()[:16]
