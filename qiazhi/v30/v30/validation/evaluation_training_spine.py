from __future__ import annotations

from typing import Any

from v30.engines import infer_engine_plan, run_engine_plan
from v30.evaluation.case_bank import load_phase1_evaluation_cases, load_phase2_evaluation_cases
from v30.evaluation.regression_runner import run_evaluation_case
from v30.runtime import create_smoke_runtime
from v30.training.mingli_phase2 import load_phase2_ziwei_golden_cases
from v30.training.mingli_training import load_phase1_mingli_golden_cases


EVALUATION_TRAINING_SPINE_RUNNER_VERSION = "v30.evaluation_training_spine_runner.v1"


def run_evaluation_training_spine(
    *,
    include_phase2: bool = True,
) -> dict[str, Any]:
    specs = load_phase1_evaluation_cases()
    source_cases = load_phase1_mingli_golden_cases()
    if include_phase2:
        specs.extend(load_phase2_evaluation_cases())
        source_cases.extend(load_phase2_ziwei_golden_cases())
    results = []
    source_by_linked = {case.case_id: case for case in source_cases}
    for index, spec in enumerate(specs, start=1):
        source_case = source_by_linked.get(spec.linked_case_id)
        reading_id = f"eval-spine-{index}-{spec.linked_case_id or spec.case_id}"
        runtime = create_smoke_runtime(reading_id)
        plan = infer_engine_plan(
            reading_id=reading_id,
            user_question=spec.user_question,
            role="practitioner",
        )
        multi_engine = run_engine_plan(
            plan,
            runtime=runtime,
            engine_contexts={
                "ziwei": {
                    "ziwei_matched_rule_ids": source_case.ziwei_matched_rule_ids if source_case else [],
                    "ziwei_chart_id": f"{reading_id}:ziwei-chart",
                },
                "reality_probe": {
                    "answer_signals": source_case.reality_probe_answers if source_case else [],
                },
            },
        )
        results.append(
            run_evaluation_case(
                case_spec=spec,
                runtime_payload=runtime.model_dump(mode="json"),
                multi_engine_result=multi_engine,
            )
        )
    failed = [result for result in results if result.status != "passed"]
    return {
        "version": EVALUATION_TRAINING_SPINE_RUNNER_VERSION,
        "status": "passed" if not failed else "blocked",
        "decision": {
            "evaluation_training_spine_ready": not failed,
            "case_count": len(results),
            "passed_case_count": len(results) - len(failed),
            "failed_case_ids": [result.case_spec.case_id for result in failed],
            "average_overall_score": round(sum(result.metric_summary.overall_score for result in results) / max(1, len(results)), 3),
            "evidence_coverage_rate": round(sum(result.metric_summary.evidence_coverage_rate for result in results) / max(1, len(results)), 3),
            "overclaim_rate": round(sum(result.metric_summary.overclaim_rate for result in results) / max(1, len(results)), 3),
            "advice_grounding_rate": round(sum(result.metric_summary.advice_grounding_rate for result in results) / max(1, len(results)), 3),
            "probe_yield_score": round(sum(result.metric_summary.probe_yield_score for result in results) / max(1, len(results)), 3),
            "chart_fact_mutation_allowed": False,
            "production_policy_write_allowed": False,
        },
        "results": [result.model_dump(mode="json") for result in results],
        "boundary": "evaluation_training_spine_runner_evaluates_sidecar_outputs_without_mutating_runtime",
    }
