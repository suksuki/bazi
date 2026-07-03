from __future__ import annotations

from typing import Any

from v30.engines.contracts import MultiEngineRunResult
from v30.evaluation.advice_evaluator import evaluate_advice
from v30.evaluation.contracts import EvaluationCaseSpec, EvaluationRunResult, TrainingImpactDiff
from v30.evaluation.metrics import build_metric_summary
from v30.evaluation.probe_evaluator import evaluate_probe
from v30.evaluation.verdict_evaluator import evaluate_verdicts


def run_evaluation_case(
    *,
    case_spec: EvaluationCaseSpec,
    runtime_payload: dict[str, Any],
    multi_engine_result: MultiEngineRunResult | None = None,
    training_impact: TrainingImpactDiff | None = None,
) -> EvaluationRunResult:
    verdict_eval = evaluate_verdicts(case_spec=case_spec, runtime_payload=runtime_payload)
    advice_eval = evaluate_advice(case_spec=case_spec, runtime_payload=runtime_payload)
    probe_eval = evaluate_probe(
        case_spec=case_spec,
        runtime_payload=runtime_payload,
        multi_engine_result=multi_engine_result,
    )
    summary = build_metric_summary(
        verdict_eval=verdict_eval,
        advice_eval=advice_eval,
        probe_eval=probe_eval,
    )
    status = "passed" if summary.status == "passed" and not (training_impact and training_impact.regression_detected) else "blocked"
    return EvaluationRunResult(
        run_id=f"evaluation:{case_spec.case_id}:{runtime_payload.get('reading_id') or 'unknown'}",
        case_spec=case_spec,
        reading_id=str(runtime_payload.get("reading_id") or ""),
        verdict_eval=verdict_eval,
        advice_eval=advice_eval,
        probe_eval=probe_eval,
        metric_summary=summary,
        training_impact=training_impact,
        status=status,
    )
