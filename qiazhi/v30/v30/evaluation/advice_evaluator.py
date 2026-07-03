from __future__ import annotations

from typing import Any

from v30.evaluation.contracts import AdviceEvalResult, EvaluationCaseSpec


_ACTION_TERMS = ("建议", "先", "重点", "确认", "建立", "控制", "拆分", "选择", "避免", "减少")
_BOUNDARY_TERMS = ("必然", "一定", "绝对", "保证", "稳赚", "立刻")


def evaluate_advice(*, case_spec: EvaluationCaseSpec, runtime_payload: dict[str, Any]) -> AdviceEvalResult:
    verdicts = _verdicts(runtime_payload)
    advice_rows: list[tuple[dict[str, Any], str]] = [
        (verdict, str(item))
        for verdict in verdicts
        for item in _list(verdict.get("advice_points"))
        if str(item).strip()
    ]
    grounded = [(verdict, text) for verdict, text in advice_rows if _list(verdict.get("evidence_refs"))]
    ungrounded = [text for verdict, text in advice_rows if not _list(verdict.get("evidence_refs"))]
    expected_terms = [term for expected in case_spec.expected_advice for term in expected.must_include_any]
    action_hits = sum(1 for _, text in advice_rows if any(term in text for term in [*expected_terms, *_ACTION_TERMS]))
    boundary_hits = [text for _, text in advice_rows if any(term in text for term in _BOUNDARY_TERMS)]
    advice_count = len(advice_rows)
    grounding_rate = _ratio(len(grounded), advice_count)
    actionability = _ratio(action_hits, advice_count)
    assertion_boundary = 0.0 if boundary_hits else 1.0
    failed = []
    if grounding_rate < 1.0:
        failed.append("advice_not_fully_grounded")
    if actionability < 0.62:
        failed.append("advice_actionability_low")
    if boundary_hits:
        failed.append("advice_oversteps_assertion_boundary")
    return AdviceEvalResult(
        case_id=case_spec.case_id,
        reading_id=str(runtime_payload.get("reading_id") or ""),
        advice_count=advice_count,
        grounded_advice_count=len(grounded),
        advice_grounding_rate=grounding_rate,
        actionability_score=actionability,
        assertion_boundary_score=assertion_boundary,
        ungrounded_advice=ungrounded,
        failed_reasons=failed,
        passed=not failed,
    )


def _verdicts(runtime_payload: dict[str, Any]) -> list[dict[str, Any]]:
    central = _dict(_dict(_dict(runtime_payload.get("question_plan")).get("policy_effect")).get("central_reading_state"))
    decision = _dict(central.get("decision_result"))
    return [row for row in _list(decision.get("verdicts")) if isinstance(row, dict)]


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 1.0
    return round(max(0.0, min(1.0, numerator / denominator)), 3)


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []
