from __future__ import annotations

from v20.api.runtime import run_runtime_from_pillars
from v20.corpus.canonical_case import CanonicalCase


def precompute_case(case: CanonicalCase) -> dict[str, object]:
    result = run_runtime_from_pillars(*case.pillar_displays, input_id=case.case_id)
    return {
        "version": "v20.corpus_precompute.v1",
        "case": case.to_dict(),
        "feature_count": result["feature_layer"]["feature_count"],
        "question_count": len(result["questions"]),
        "answer_plan_version": result["answer_plan"]["version"],
        "runtime_mutation": False,
        "guardrails": ["PRECOMPUTE_DRY_RUN_ONLY", "NO_PROMOTION"],
    }
