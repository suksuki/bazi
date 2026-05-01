from __future__ import annotations

from v20.api.runtime import run_runtime_from_pillars
from v20.validation.evaluator import evaluate_runtime_result
from v20.validation.golden import GOLDEN_CASES
from v20.validation.synthetic_schema import SyntheticCase


def run_synthetic_suite(cases: tuple[SyntheticCase, ...] = GOLDEN_CASES) -> dict[str, object]:
    results = []
    for case in cases:
        runtime = run_runtime_from_pillars(*case.pillar_displays, input_id=case.case_id)
        results.append(evaluate_runtime_result(case, runtime))
    failures = [failure for result in results for failure in result["failures"]]
    return {
        "version": "v20.synthetic_suite_report.v1",
        "case_count": len(results),
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
