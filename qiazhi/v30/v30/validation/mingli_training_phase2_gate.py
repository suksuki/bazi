from __future__ import annotations

from typing import Any

from v30.engines import infer_engine_plan, run_engine_plan
from v30.runtime import create_smoke_runtime
from v30.training.mingli_phase2 import (
    MINGLI_TRAINING_PHASE2_VERSION,
    MingliPhase2Gate,
    build_mingli_phase2_gate,
    load_phase2_ziwei_golden_cases,
)
from v30.training.mingli_training import (
    MingliGoldenCase,
    build_engine_training_example,
    build_mingli_training_quality_gate,
    load_phase1_mingli_golden_cases,
)


MINGLI_TRAINING_PHASE2_GATE_VERSION = "v30.mingli_training_phase2_gate_runner.v1"


def run_mingli_training_phase2_gate(
    *,
    phase1_cases: list[MingliGoldenCase] | None = None,
    ziwei_cases: list[MingliGoldenCase] | None = None,
) -> dict[str, Any]:
    phase1_examples = _examples_from_cases(phase1_cases or load_phase1_mingli_golden_cases(), prefix="phase1")
    phase1_gate = build_mingli_training_quality_gate(phase1_examples)
    ziwei_examples = _examples_from_cases(ziwei_cases or load_phase2_ziwei_golden_cases(), prefix="phase2-ziwei")
    gate = build_mingli_phase2_gate(
        phase1_gate=phase1_gate,
        ziwei_examples=ziwei_examples,
    )
    return _gate_payload(gate)


def _examples_from_cases(cases: list[MingliGoldenCase], *, prefix: str) -> list[Any]:
    examples = []
    for index, golden_case in enumerate(cases, start=1):
        reading_id = f"mtl-{prefix}-{index}-{golden_case.case_id}"
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
    return examples


def _gate_payload(gate: MingliPhase2Gate) -> dict[str, Any]:
    return {
        "version": MINGLI_TRAINING_PHASE2_GATE_VERSION,
        "training_version": MINGLI_TRAINING_PHASE2_VERSION,
        "status": gate.status,
        "decision": {
            "mingli_training_phase2_ready": gate.status == "passed",
            "phase1_status": gate.phase1_status,
            "example_count": gate.example_count,
            "replay_queue_count": gate.replay_queue_count,
            "practitioner_label_projection_count": gate.practitioner_label_projection_count,
            "ziwei_golden_case_count": gate.ziwei_golden_case_count,
            "reality_probe_diff_count": gate.reality_probe_diff_count,
            "chart_fact_mutation_allowed": gate.chart_fact_mutation_allowed,
            "production_policy_write_allowed": gate.production_policy_write_allowed,
            "production_pointer_write_allowed": False,
            "full_518k_required": False,
        },
        "replay_queue": [row.model_dump(mode="json") for row in gate.replay_queue],
        "practitioner_projections": [row.model_dump(mode="json") for row in gate.practitioner_projections],
        "reality_probe_diffs": [row.model_dump(mode="json") for row in gate.reality_probe_diffs],
        "recommendations": gate.recommendations,
        "boundary": gate.boundary,
    }
