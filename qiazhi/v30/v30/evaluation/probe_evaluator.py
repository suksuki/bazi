from __future__ import annotations

from typing import Any

from v30.engines.contracts import MultiEngineRunResult
from v30.evaluation.contracts import EvaluationCaseSpec, ProbeEvalResult


def evaluate_probe(
    *,
    case_spec: EvaluationCaseSpec,
    runtime_payload: dict[str, Any],
    multi_engine_result: MultiEngineRunResult | None = None,
) -> ProbeEvalResult:
    candidates = _probe_candidates(runtime_payload, multi_engine_result)
    expected = [row for row in case_spec.expected_probes if row.required]
    answers = _list(case_spec.known_reality.get("reality_probe_answers"))
    answer_required = bool(answers)
    binding_hits = 0
    for expected_probe in expected:
        if any(_probe_matches(expected_probe.domain, expected_probe.expected_keywords, candidate) for candidate in candidates):
            binding_hits += 1
    binding_rate = _ratio(binding_hits, len(expected))
    answer_signal_count = len(answers)
    answer_component = 1.0 if not answer_required or answer_signal_count else 0.0
    yield_score = round(min(1.0, binding_rate * 0.65 + answer_component * 0.35), 3)
    failed = []
    if expected and binding_rate < 1.0:
        failed.append("expected_probe_not_bound")
    if expected and answer_required and not answer_signal_count:
        failed.append("probe_has_no_answer_signal")
    return ProbeEvalResult(
        case_id=case_spec.case_id,
        reading_id=str(runtime_payload.get("reading_id") or ""),
        probe_candidate_count=len(candidates),
        expected_probe_count=len(expected),
        answer_signal_count=answer_signal_count,
        probe_binding_rate=binding_rate,
        probe_yield_score=yield_score,
        requires_followup=bool(failed),
        failed_reasons=failed,
        passed=not failed,
    )


def _probe_candidates(runtime_payload: dict[str, Any], multi_engine_result: MultiEngineRunResult | None) -> list[dict[str, Any]]:
    candidates = []
    question_plan = _dict(runtime_payload.get("question_plan"))
    candidates.extend(_list(question_plan.get("hidden_factor_probes")))
    if multi_engine_result is not None:
        for result in multi_engine_result.results:
            candidates.extend(result.probe_candidates)
    return [row for row in candidates if isinstance(row, dict)]


def _probe_matches(domain: str, keywords: list[str], candidate: dict[str, Any]) -> bool:
    text = "\n".join(str(value) for value in candidate.values())
    domain_ok = not domain or domain in text
    keyword_ok = not keywords or any(keyword in text for keyword in keywords)
    return domain_ok or keyword_ok


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 1.0
    return round(max(0.0, min(1.0, numerator / denominator)), 3)


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []
