from __future__ import annotations

from dataclasses import replace
from typing import Any

from v20.interaction.questions import QuestionCandidate


QUESTION_MAINLINE_FOCUS_VERSION = "v20.question_mainline_focus.v1"


def align_questions_to_mainline(
    questions: tuple[QuestionCandidate, ...],
    selected_question: QuestionCandidate,
    mainline_arbitration: dict[str, Any],
    *,
    explicit_question_requested: bool = False,
    limit: int = 14,
    runtime_policy_pointer: dict[str, Any] | None = None,
) -> tuple[tuple[QuestionCandidate, ...], QuestionCandidate, dict[str, object]]:
    primary = mainline_arbitration.get("primary_mainline", {}) if isinstance(mainline_arbitration, dict) else {}
    primary_domain = str(primary.get("domain", "")) if isinstance(primary, dict) else ""
    before_key = selected_question.question_key
    before_id = selected_question.question_id or selected_question.question_key
    same_domain = tuple(row for row in questions if primary_domain and row.domain == primary_domain)
    focused_selected = selected_question
    status = "explicit_question_preserved" if explicit_question_requested else "ready"
    if not explicit_question_requested and same_domain:
        focused_selected = _boost_for_mainline(
            same_domain[0],
            primary_domain,
            selected=True,
            runtime_policy_pointer=runtime_policy_pointer or {},
        )
        status = "selected_mainline_domain_question" if focused_selected.question_key != before_key else "already_aligned"
    elif not primary_domain:
        status = "no_primary_domain"
    elif not same_domain:
        status = "no_domain_match"
    ordered = _ordered_questions(
        questions,
        focused_selected,
        primary_domain=primary_domain,
        explicit_question_requested=explicit_question_requested,
        runtime_policy_pointer=runtime_policy_pointer or {},
        limit=limit,
    )
    selected_id = focused_selected.question_id or focused_selected.question_key
    if ordered:
        focused_selected = next(
            (
                row
                for row in ordered
                if (row.question_id or row.question_key) == selected_id
                or (not row.question_id and row.question_key == focused_selected.question_key)
            ),
            focused_selected,
        )
    report = {
        "version": QUESTION_MAINLINE_FOCUS_VERSION,
        "status": status,
        "source": "Questions+MainlineArbitration",
        "primary_domain": primary_domain,
        "primary_mainline_key": str(primary.get("candidate_key", "") or primary.get("candidate_id", "")) if isinstance(primary, dict) else "",
        "selected_question_key_before": before_key,
        "selected_question_id_before": before_id,
        "selected_question_key_after": focused_selected.question_key,
        "selected_question_id_after": focused_selected.question_id or focused_selected.question_key,
        "reordered": bool(ordered and (ordered[0].question_key != (questions[0].question_key if questions else "") or focused_selected.question_key != before_key)),
        "explicit_question_requested": explicit_question_requested,
        "domain_match_count": len(same_domain),
        "runtime_policy_effect": _policy_effect(runtime_policy_pointer or {}, primary_domain),
        "runtime_mutation": False,
        "guardrails": [
            "QUESTION_FOCUS_FOLLOWS_MAINLINE_ARBITRATION",
            "EXPLICIT_USER_QUESTION_IS_PRESERVED",
            "RERANK_ONLY_NO_FACT_MUTATION",
            "FAST_TRACK_POLICY_CAN_RERANK_QUESTIONS",
        ],
    }
    return ordered, focused_selected, report


def _ordered_questions(
    questions: tuple[QuestionCandidate, ...],
    selected_question: QuestionCandidate,
    *,
    primary_domain: str,
    explicit_question_requested: bool,
    runtime_policy_pointer: dict[str, Any],
    limit: int,
) -> tuple[QuestionCandidate, ...]:
    selected_id = selected_question.question_id or selected_question.question_key
    ranked: list[tuple[int, float, str, QuestionCandidate]] = []
    for index, row in enumerate(questions):
        row_id = row.question_id or row.question_key
        is_selected = row_id == selected_id or (not row.question_id and row.question_key == selected_question.question_key)
        if is_selected:
            candidate = selected_question
            bucket = 0
        elif primary_domain and row.domain == primary_domain:
            candidate = _boost_for_mainline(row, primary_domain, runtime_policy_pointer=runtime_policy_pointer)
            bucket = 1 if explicit_question_requested else 0
        else:
            candidate = row
            bucket = 2
        ranked.append((bucket, -float(candidate.score or 0.0), f"{index:04d}", candidate))
    unique: dict[str, QuestionCandidate] = {}
    for _, _, _, row in sorted(ranked):
        key = row.question_id or row.question_key
        unique.setdefault(key, row)
    return tuple(unique.values())[:limit]


def _boost_for_mainline(
    question: QuestionCandidate,
    primary_domain: str,
    *,
    selected: bool = False,
    runtime_policy_pointer: dict[str, Any] | None = None,
) -> QuestionCandidate:
    strategy = "mainline_focus_selected" if selected else "mainline_focus"
    policy_boost = _question_policy_boost(primary_domain, runtime_policy_pointer or {})
    return replace(
        question,
        score=round(min(1.2, float(question.score or 0.0) + (0.1 if selected else 0.06) + policy_boost), 3),
        question_strategy=question.question_strategy or strategy,
    )


def _question_policy_boost(primary_domain: str, runtime_policy_pointer: dict[str, Any]) -> float:
    if not primary_domain or not runtime_policy_pointer.get("runtime_applied"):
        return 0.0
    payload = runtime_policy_pointer.get("policy_payload", {})
    if not isinstance(payload, dict):
        return 0.0
    for policy in payload.get("question_focus_policy", ()):
        if not isinstance(policy, dict) or not policy.get("runtime_allowed"):
            continue
        if str(policy.get("domain", "")) == primary_domain:
            try:
                strength = float(policy.get("average_strength", 0) or 0)
            except (TypeError, ValueError):
                strength = 0.0
            return round(min(0.06, max(0.02, strength * 0.04)), 3)
    return 0.0


def _policy_effect(runtime_policy_pointer: dict[str, Any], primary_domain: str) -> dict[str, object]:
    boost = _question_policy_boost(primary_domain, runtime_policy_pointer)
    return {
        "version": "v20.question_focus_runtime_policy_effect.v1",
        "status": "applied" if boost else "not_applied",
        "active_policy_version": str(runtime_policy_pointer.get("active_policy_version", "")),
        "primary_domain": primary_domain,
        "domain_boost": boost,
        "runtime_mutation": False,
        "guardrails": [
            "POLICY_EFFECT_RERANKS_ONLY",
            "NO_QUESTION_FACT_MUTATION",
            "EXPLICIT_USER_QUESTION_IS_PRESERVED",
        ],
    }
