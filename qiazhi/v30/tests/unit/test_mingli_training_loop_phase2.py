from __future__ import annotations

import pytest

from v30.engines import infer_engine_plan, run_engine_plan
from v30.engines.contracts import EngineKey
from v30.runtime import create_smoke_runtime
from v30.training.mingli_phase2 import (
    PractitionerLabel,
    build_mingli_phase2_gate,
    build_practitioner_label_projection,
    build_reality_probe_verdict_diff,
    build_replay_queue,
    load_phase2_ziwei_golden_cases,
)
from v30.training.mingli_training import (
    build_engine_training_example,
    build_mingli_training_quality_gate,
    load_phase1_mingli_golden_cases,
)
from v30.validation.mingli_training_phase2_gate import run_mingli_training_phase2_gate


def test_phase2_ziwei_golden_cases_are_sidecar_cases() -> None:
    cases = load_phase2_ziwei_golden_cases()

    assert len(cases) == 3
    assert all(EngineKey.ZIWEI in case.required_engines for case in cases)
    assert all(case.ziwei_matched_rule_ids for case in cases)
    assert all(case.reality_probe_answers for case in cases)
    assert all("紫微直接定论" in case.forbidden_assertions for case in cases)


def test_phase2_replay_queue_routes_failed_examples() -> None:
    case = load_phase1_mingli_golden_cases()[0]
    example = _failed_example(_example_for_case(case, "pytest-phase2-replay"))
    replay = build_replay_queue([example])

    assert len(replay) == 1
    assert replay[0].case_id == case.case_id
    assert replay[0].promotion_blocked is True
    assert "overall_score_below_case_threshold" in replay[0].failed_reasons
    assert replay[0].priority in {"medium", "high", "critical"}
    assert replay[0].rerun_plan


def test_phase2_practitioner_label_projection_is_training_only() -> None:
    case = load_phase1_mingli_golden_cases()[0]
    example = _example_for_case(case, "pytest-phase2-label")
    label = PractitionerLabel(
        label_id="label-phase2-career",
        case_id=example.case_id,
        reading_id=example.reading_id,
        decision="accept",
        accepted_verdict_domains=["career"],
        advice_tags=["资质", "平台"],
        quality_overrides={"overall_quality": 0.91},
    )
    projection = build_practitioner_label_projection(example=example, labels=[label])

    assert projection.label_count == 1
    assert projection.accepted_domain_count == 1
    assert projection.label_alignment_score == 1.0
    assert projection.quality_overrides["overall_quality"] == 0.91
    assert "practitioner_label_alignment" in projection.trainable_targets
    assert projection.chart_fact_mutation_allowed is False
    assert projection.production_policy_write_allowed is False


def test_phase2_practitioner_label_rejects_fact_mutation() -> None:
    with pytest.raises(ValueError, match="cannot allow chart fact mutation"):
        PractitionerLabel(
            label_id="bad-label",
            case_id="bad-case",
            reading_id="bad-reading",
            accepted_verdict_domains=["career"],
            chart_fact_mutation_allowed=True,
        )


def test_phase2_reality_probe_verdict_diff_aligns_answers_to_verdict_domains() -> None:
    case = load_phase2_ziwei_golden_cases()[1]
    example = _example_for_case(case, "pytest-phase2-diff")
    diff = build_reality_probe_verdict_diff(golden_case=case, example=example)

    assert diff.answer_signal_count == 1
    assert "wealth" in diff.matched_verdict_domains
    assert diff.alignment_score == 1.0
    assert diff.requires_followup is False
    assert diff.manifestation_updates


def test_phase2_gate_runner_passes_default_pack_without_policy_write() -> None:
    payload = run_mingli_training_phase2_gate()

    assert payload["version"] == "v30.mingli_training_phase2_gate_runner.v1"
    assert payload["status"] == "passed"
    assert payload["decision"]["mingli_training_phase2_ready"] is True
    assert payload["decision"]["phase1_status"] == "passed"
    assert payload["decision"]["ziwei_golden_case_count"] == 3
    assert payload["decision"]["reality_probe_diff_count"] == 3
    assert payload["decision"]["replay_queue_count"] == 0
    assert payload["decision"]["production_pointer_write_allowed"] is False
    assert payload["decision"]["full_518k_required"] is False
    assert payload["practitioner_projections"]
    assert payload["reality_probe_diffs"]


def test_phase2_gate_blocks_when_phase1_has_unresolved_replay() -> None:
    bad_case = load_phase1_mingli_golden_cases()[0]
    bad_example = _failed_example(_example_for_case(bad_case, "pytest-phase2-blocked"))
    phase1_gate = build_mingli_training_quality_gate([bad_example], min_case_count=1, min_average_quality=0.1)
    ziwei_examples = [_example_for_case(case, f"pytest-phase2-ziwei-{index}") for index, case in enumerate(load_phase2_ziwei_golden_cases(), start=1)]
    gate = build_mingli_phase2_gate(phase1_gate=phase1_gate, ziwei_examples=ziwei_examples)

    assert gate.status == "blocked"
    assert gate.replay_queue_count == 1
    assert gate.replay_queue[0].promotion_blocked is True
    assert "先处理 replay queue" in gate.recommendations[0]


def _example_for_case(case, reading_id: str):
    runtime = create_smoke_runtime(reading_id)
    plan = infer_engine_plan(reading_id=runtime.reading_id, user_question=case.user_question, role="practitioner")
    multi_engine = run_engine_plan(
        plan,
        runtime=runtime,
        engine_contexts={
            "ziwei": {"ziwei_matched_rule_ids": case.ziwei_matched_rule_ids, "ziwei_chart_id": f"{reading_id}:ziwei"},
            "reality_probe": {"answer_signals": case.reality_probe_answers},
        },
    )
    return build_engine_training_example(
        golden_case=case,
        multi_engine_result=multi_engine,
        runtime_payload=runtime.model_dump(mode="json"),
    )


def _failed_example(example):
    return example.model_copy(
        update={
            "quality_score": example.quality_score.model_copy(
                update={
                    "passed": False,
                    "overall_score": 0.42,
                    "failed_reasons": ["overall_score_below_case_threshold"],
                }
            )
        }
    )
