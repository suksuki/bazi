from __future__ import annotations

import hashlib
import json

from v20.storage.local_jsonl import LocalJsonlStore, local_jsonl_store_from_env


LEDGER_NAME = "role_question_click_ledger"
CLICK_VERSION = "v20.role_question_click_signal.v1"
ACTION_REWARD_VALUES: dict[str, float] = {
    "select": 1.0,
    "click": 1.0,
    "followup": 0.8,
    "answer_helpful": 1.0,
    "skip": -0.4,
    "downrank": -0.7,
    "answer_unhelpful": -1.0,
}


def analyze_role_question_click(
    *,
    input_id: str,
    source_role: str,
    question: dict[str, object],
    locale: str = "zh",
) -> dict[str, object]:
    _validate_source_role(source_role)
    _validate_no_raw_markers(question)
    persistable = _persistable_question(question)
    _validate_question_payload(persistable)
    source_hash = _source_hash(input_id, source_role, locale, json.dumps(persistable, ensure_ascii=False, sort_keys=True))
    return {
        "version": "v20.role_question_click_analysis.v1",
        "source_hash": source_hash,
        "source_role": source_role,
        "input_id": input_id,
        "question_key": persistable.get("question_key", ""),
        "question_id": persistable.get("question_id", ""),
        "domain": persistable.get("domain", ""),
        "role_view_level": persistable.get("role_view_level", ""),
        "question_strategy": persistable.get("question_strategy", ""),
        "question_group": persistable.get("question_group", ""),
        "click_signal": persistable,
        "runtime_mutation": False,
        "guardrails": [
            "ROLE_QUESTION_CLICK_ANALYSIS_ONLY",
            "NO_RAW_USER_TEXT_PERSISTED",
            "NO_QUESTION_TITLE_PERSISTED",
            "NO_RUNTIME_RULE_OR_MAINLINE_MUTATION",
        ],
    }


def record_role_question_click(
    *,
    input_id: str,
    source_role: str,
    question: dict[str, object],
    locale: str = "zh",
    store: LocalJsonlStore | None = None,
) -> dict[str, object]:
    analysis = analyze_role_question_click(
        input_id=input_id,
        source_role=source_role,
        question=question,
        locale=locale,
    )
    storage = (store or local_jsonl_store_from_env()).append_record(LEDGER_NAME, _persistable_payload(analysis))
    return {
        "version": "v20.role_question_click_record_result.v1",
        "analysis": analysis,
        "storage": storage,
        "runtime_mutation": True,
        "guardrails": [
            "APPEND_ONLY_ROLE_QUESTION_CLICK_SIGNAL",
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
        "question_key": analysis["question_key"],
        "question_id": analysis["question_id"],
        "domain": analysis["domain"],
        "role_view_level": analysis["role_view_level"],
        "question_strategy": analysis["question_strategy"],
        "question_group": analysis["question_group"],
        "click_signal": analysis["click_signal"],
        "runtime_mutation": False,
        "guardrails": analysis["guardrails"],
    }


def _persistable_question(question: dict[str, object]) -> dict[str, object]:
    return {
        "version": CLICK_VERSION,
        "question_key": str(question.get("question_key", "")),
        "question_id": str(question.get("question_id", "")),
        "domain": str(question.get("domain", "")),
        "role_view_level": str(question.get("role_view_level", "")),
        "question_strategy": str(question.get("question_strategy", "")),
        "question_group": str(question.get("question_group", "")),
        "measurement_topic": str(question.get("measurement_topic", "")),
        "measurement_stage": str(question.get("measurement_stage", "")),
        "role_view_source": str(question.get("role_view_source", "")),
        "seed_source_key": _safe_seed_key(question.get("seed_source_key", "")),
        "next_question_atom_id": _safe_next_question_atom_id(question.get("next_question_atom_id", "")),
        "next_question_topic": _safe_token(question.get("next_question_topic", "")),
        "next_question_stage": _safe_token(question.get("next_question_stage", "")),
        "action_type": _safe_action_type(question.get("action_type", "")),
        "reward_value": _reward_value(question.get("action_type", "")),
        "runtime_mutation": False,
    }


def _validate_source_role(source_role: str) -> None:
    if source_role not in {"guest", "user", "analyst", "admin", "lab", "practitioner"}:
        raise ValueError(f"Unsupported role question click source role: {source_role}")


def _validate_question_payload(question: dict[str, object]) -> None:
    if not str(question.get("question_key", "")) and not str(question.get("question_id", "")):
        raise ValueError("question_key or question_id is required")


def _validate_no_raw_markers(question: dict[str, object]) -> None:
    text = json.dumps(question, ensure_ascii=False, sort_keys=True)
    blocked = ("title", "source_title", "user_text", "feedback_text", "raw_feedback", "raw_private", "email", "phone")
    if any(token in text for token in blocked):
        raise ValueError("role question click contains raw text or private-field markers")


def _safe_seed_key(value: object) -> str:
    seed_key = str(value or "")
    if not seed_key:
        return ""
    if not seed_key.startswith("seed."):
        return ""
    return seed_key[:96]


def _safe_next_question_atom_id(value: object) -> str:
    atom_id = str(value or "")
    if not atom_id:
        return ""
    if not atom_id.startswith("atom."):
        return ""
    return atom_id[:120]


def _safe_token(value: object) -> str:
    token = str(value or "").strip()
    if not token:
        return ""
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-.")
    return "".join(ch for ch in token[:80] if ch in allowed)


def _safe_action_type(value: object) -> str:
    action = str(value or "select").strip() or "select"
    if action not in ACTION_REWARD_VALUES:
        return "select"
    return action


def _reward_value(action_type: object) -> float:
    return ACTION_REWARD_VALUES[_safe_action_type(action_type)]


def _source_hash(*values: str) -> str:
    return hashlib.sha256("|".join(values).encode("utf-8")).hexdigest()[:16]
