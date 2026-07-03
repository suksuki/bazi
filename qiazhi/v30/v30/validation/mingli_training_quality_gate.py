from __future__ import annotations

from typing import Any

from v30.engines import infer_engine_plan, run_engine_plan
from v30.runtime import create_smoke_runtime
from v30.training.mingli_training import (
    MINGLI_TRAINING_PHASE1_VERSION,
    MingliGoldenCase,
    MingliTrainingQualityGate,
    build_engine_training_example,
    build_mingli_training_quality_gate,
    load_phase1_mingli_golden_cases,
)


MINGLI_TRAINING_QUALITY_GATE_VERSION = "v30.mingli_training_quality_gate_runner.v1"


def run_mingli_training_quality_gate(
    *,
    cases: list[MingliGoldenCase] | None = None,
    min_case_count: int = 3,
    min_average_quality: float = 0.68,
) -> dict[str, Any]:
    examples = []
    for index, golden_case in enumerate(cases or load_phase1_mingli_golden_cases(), start=1):
        reading_id = f"mtl-phase1-{index}-{golden_case.case_id}"
        runtime = create_smoke_runtime(reading_id)
        plan = infer_engine_plan(
            reading_id=reading_id,
            user_question=golden_case.user_question,
            role="practitioner",
        )
        multi_engine = run_engine_plan(
            plan,
            runtime=runtime,
            engine_contexts={
                "ziwei": {
                    "ziwei_matched_rule_ids": golden_case.ziwei_matched_rule_ids,
                    "ziwei_chart_id": f"{reading_id}:ziwei-chart",
                },
                "reality_probe": {
                    "answer_signals": golden_case.reality_probe_answers,
                },
            },
        )
        examples.append(
            build_engine_training_example(
                golden_case=golden_case,
                multi_engine_result=multi_engine,
                runtime_payload=runtime.model_dump(mode="json"),
            )
        )
    gate = build_mingli_training_quality_gate(
        examples,
        min_case_count=min_case_count,
        min_average_quality=min_average_quality,
    )
    return _gate_payload(gate)


def _gate_payload(gate: MingliTrainingQualityGate) -> dict[str, Any]:
    return {
        "version": MINGLI_TRAINING_QUALITY_GATE_VERSION,
        "training_version": MINGLI_TRAINING_PHASE1_VERSION,
        "status": gate.status,
        "decision": {
            "mingli_training_phase1_ready": gate.status == "passed",
            "case_count": gate.case_count,
            "passed_case_count": gate.passed_case_count,
            "average_quality_score": gate.average_quality_score,
            "failed_case_ids": gate.failed_case_ids,
            "chart_fact_mutation_allowed": gate.chart_fact_mutation_allowed,
            "production_policy_write_allowed": gate.production_policy_write_allowed,
            "full_518k_required": False,
            "production_pointer_write_allowed": False,
        },
        "examples": [
            {
                "example_id": example.example_id,
                "case_id": example.case_id,
                "reading_id": example.reading_id,
                "quality": example.quality_score.model_dump(mode="json"),
                "engine_contributions": example.engine_contributions,
                "signal_registry_summary": example.signal_registry_summary,
                "trainable_targets": example.trainable_targets,
                "blocked_targets": example.blocked_targets,
            }
            for example in gate.examples
        ],
        "recommendations": gate.recommendations,
        "boundary": gate.boundary,
    }
