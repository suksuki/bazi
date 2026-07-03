from __future__ import annotations

from typing import Any

from v30.evaluation.contracts import EvaluationCaseSpec, VerdictEvalResult


_OVERCLAIM_TERMS = ("必然", "一定", "绝对", "保证", "稳赚", "必定")
_CONFLICT_TERMS = ("但", "同时", "分支", "候选", "混合", "保留", "需要", "先")


def evaluate_verdicts(*, case_spec: EvaluationCaseSpec, runtime_payload: dict[str, Any]) -> VerdictEvalResult:
    verdicts = _verdicts(runtime_payload)
    expected_domains = {row.domain for row in case_spec.expected_verdicts}
    verdict_domains = {str(row.get("domain") or "") for row in verdicts}
    evidence_coverage = _ratio(sum(1 for row in verdicts if _list(row.get("evidence_refs"))), len(verdicts))
    expected_coverage = _ratio(len(expected_domains & verdict_domains), len(expected_domains))
    surface = _surface_text(verdicts)
    forbidden_hits = [row.text for row in case_spec.forbidden_assertions if row.text and row.text in surface]
    overclaim_count = sum(1 for row in verdicts if _is_overclaim(row))
    overclaim_rate = _ratio(overclaim_count + len(forbidden_hits), max(1, len(verdicts)))
    assertion_calibration = _assertion_calibration(case_spec, verdicts)
    conflict_resolution = _conflict_resolution(case_spec, verdicts)
    failed = []
    if expected_coverage < 1.0:
        failed.append("expected_verdict_domain_missing")
    if evidence_coverage < 1.0:
        failed.append("verdict_evidence_coverage_not_full")
    if forbidden_hits:
        failed.append("forbidden_assertion_hit")
    if overclaim_rate > 0.0:
        failed.append("overclaim_detected")
    if assertion_calibration < 0.72:
        failed.append("assertion_calibration_low")
    return VerdictEvalResult(
        case_id=case_spec.case_id,
        reading_id=str(runtime_payload.get("reading_id") or ""),
        verdict_count=len(verdicts),
        expected_verdict_count=len(case_spec.expected_verdicts),
        evidence_coverage_rate=evidence_coverage,
        expected_domain_coverage_rate=expected_coverage,
        overclaim_rate=overclaim_rate,
        assertion_calibration_score=assertion_calibration,
        conflict_resolution_score=conflict_resolution,
        forbidden_assertion_hits=forbidden_hits,
        failed_reasons=failed,
        passed=not failed,
    )


def _assertion_calibration(case_spec: EvaluationCaseSpec, verdicts: list[dict[str, Any]]) -> float:
    expected_by_domain = {row.domain: row for row in case_spec.expected_verdicts}
    scored = []
    for verdict in verdicts:
        domain = str(verdict.get("domain") or "")
        expected = expected_by_domain.get(domain)
        if expected is None:
            continue
        level = str(verdict.get("assertion_level") or "")
        evidence_ok = len(_list(verdict.get("evidence_refs"))) >= expected.min_evidence_count
        level_ok = level in set(expected.allowed_assertion_levels)
        scored.append(1.0 if evidence_ok and level_ok else 0.0)
    return round(sum(scored) / max(1, len(scored)), 3) if scored else 0.0


def _conflict_resolution(case_spec: EvaluationCaseSpec, verdicts: list[dict[str, Any]]) -> float:
    conflict_domains = {row.domain for row in case_spec.expected_verdicts if row.requires_conflict_handling}
    if not conflict_domains:
        return 1.0
    scored = []
    for verdict in verdicts:
        if str(verdict.get("domain") or "") not in conflict_domains:
            continue
        text = f"{verdict.get('headline') or ''}\n{verdict.get('assertion_level') or ''}"
        has_mixed_level = str(verdict.get("assertion_level") or "") in {"mixed", "weak_candidate", "blocked"}
        has_conflict_language = any(term in text for term in _CONFLICT_TERMS)
        scored.append(1.0 if has_mixed_level or has_conflict_language else 0.0)
    return round(sum(scored) / max(1, len(scored)), 3) if scored else 0.0


def _is_overclaim(verdict: dict[str, Any]) -> bool:
    text = f"{verdict.get('headline') or ''}\n" + "\n".join(str(item) for item in _list(verdict.get("advice_points")))
    if any(term in text for term in _OVERCLAIM_TERMS):
        return True
    level = str(verdict.get("assertion_level") or "")
    return level in {"confirmed", "supported"} and not _list(verdict.get("evidence_refs"))


def _surface_text(verdicts: list[dict[str, Any]]) -> str:
    return "\n".join(
        [
            *(str(row.get("headline") or "") for row in verdicts),
            *(str(item) for row in verdicts for item in _list(row.get("allowed_assertions"))),
            *(str(item) for row in verdicts for item in _list(row.get("advice_points"))),
        ]
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
