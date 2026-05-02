from __future__ import annotations

import os

from v20.api.runtime import run_runtime_from_pillars
from v20.validation.evaluator import evaluate_runtime_result
from v20.validation.golden import GOLDEN_CASES
from v20.validation.synthetic_schema import SyntheticCase


def run_synthetic_suite(
    cases: tuple[SyntheticCase, ...] = GOLDEN_CASES,
    *,
    max_cases: int | None = None,
) -> dict[str, object]:
    if max_cases is None:
        try:
            env_max = os.getenv("V20_SYNTHETIC_SUITE_MAX_CASES")
            max_cases = int(env_max) if env_max is not None else None
        except ValueError:
            max_cases = None
    if max_cases is not None and max_cases <= 0:
        max_cases = None
    selected_cases = tuple(cases if max_cases is None else cases[:max_cases])
    results = []
    for case in selected_cases:
        runtime = run_runtime_from_pillars(*case.pillar_displays, input_id=case.case_id)
        results.append(evaluate_runtime_result(case, runtime))
    failures = [failure for result in results for failure in result["failures"]]
    return {
        "version": "v20.synthetic_suite_report.v1",
        "case_count": len(results),
        "input_case_count": len(cases),
        "max_cases": max_cases,
        "ok": not failures,
        "results": results,
        "failures": failures,
        "runtime_mutation": False,
        "guardrails": [
            "SYNTHETIC_SUITE_IS_VALIDATION_ONLY",
            "NO_LEARNING_PROMOTION_FROM_SUITE_ALONE",
            "CORE_FACTS_AND_RULES_ARE_READ_ONLY",
        ],
    }
