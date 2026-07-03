from __future__ import annotations

from v30.engines import infer_engine_plan, run_engine_plan
from v30.api.app import create_app
from v30.evaluation import (
    build_training_impact_diff,
    evaluate_advice,
    evaluate_verdicts,
    load_phase1_evaluation_cases,
    load_phase2_evaluation_cases,
    run_evaluation_case,
)
from v30.runtime import create_smoke_runtime
from v30.training.mingli_training import build_engine_training_example, load_phase1_mingli_golden_cases
from v30.validation.evaluation_training_spine import run_evaluation_training_spine


def test_evaluation_case_bank_upgrades_mingli_cases_to_case_specs() -> None:
    phase1 = load_phase1_evaluation_cases()
    phase2 = load_phase2_evaluation_cases()

    assert len(phase1) == 3
    assert len(phase2) == 3
    assert all(case.expected_verdicts for case in [*phase1, *phase2])
    assert all(case.expected_advice for case in [*phase1, *phase2])
    assert all(case.forbidden_assertions for case in [*phase1, *phase2])
    assert any(case.expected_signals for case in phase2)


def test_evaluation_run_scores_runtime_verdict_advice_and_probe() -> None:
    source_case = load_phase1_mingli_golden_cases()[1]
    case_spec = next(case for case in load_phase1_evaluation_cases() if case.linked_case_id == source_case.case_id)
    runtime = create_smoke_runtime("pytest-evaluation-spine")
    plan = infer_engine_plan(reading_id=runtime.reading_id, user_question=source_case.user_question, role="practitioner")
    multi_engine = run_engine_plan(
        plan,
        runtime=runtime,
        engine_contexts={"ziwei": {"ziwei_matched_rule_ids": source_case.ziwei_matched_rule_ids}},
    )
    result = run_evaluation_case(
        case_spec=case_spec,
        runtime_payload=runtime.model_dump(mode="json"),
        multi_engine_result=multi_engine,
    )

    assert result.version == "v30.evaluation_run_result.v1"
    assert result.verdict_eval.evidence_coverage_rate == 1.0
    assert result.verdict_eval.overclaim_rate == 0.0
    assert result.advice_eval.advice_grounding_rate == 1.0
    assert result.probe_eval.probe_candidate_count > 0
    assert result.metric_summary.overall_score >= 0.72
    assert result.status == "passed"
    assert result.chart_fact_mutation_allowed is False
    assert result.production_policy_write_allowed is False


def test_verdict_evaluator_catches_forbidden_assertion_and_overclaim() -> None:
    case_spec = load_phase1_evaluation_cases()[0]
    runtime = create_smoke_runtime("pytest-evaluation-overclaim")
    payload = runtime.model_dump(mode="json")
    verdict = payload["question_plan"]["policy_effect"]["central_reading_state"]["decision_result"]["verdicts"][0]
    verdict["headline"] = "事业必然升职，无需努力。"
    verdict["assertion_level"] = "confirmed"
    verdict["evidence_refs"] = []

    result = evaluate_verdicts(case_spec=case_spec, runtime_payload=payload)

    assert result.passed is False
    assert result.overclaim_rate > 0
    assert "必然升职" in result.forbidden_assertion_hits
    assert "forbidden_assertion_hit" in result.failed_reasons
    assert "overclaim_detected" in result.failed_reasons


def test_advice_evaluator_catches_ungrounded_advice() -> None:
    case_spec = load_phase1_evaluation_cases()[0]
    runtime = create_smoke_runtime("pytest-evaluation-advice")
    payload = runtime.model_dump(mode="json")
    verdict = payload["question_plan"]["policy_effect"]["central_reading_state"]["decision_result"]["verdicts"][0]
    verdict["advice_points"] = ["建议立刻创业，保证成功。"]
    verdict["evidence_refs"] = []

    result = evaluate_advice(case_spec=case_spec, runtime_payload=payload)

    assert result.passed is False
    assert result.advice_grounding_rate < 1.0
    assert result.assertion_boundary_score == 0.0
    assert "advice_not_fully_grounded" in result.failed_reasons


def test_training_impact_diff_tracks_metric_delta_without_policy_write() -> None:
    source_case = load_phase1_mingli_golden_cases()[0]
    runtime = create_smoke_runtime("pytest-evaluation-impact")
    plan = infer_engine_plan(reading_id=runtime.reading_id, user_question=source_case.user_question, role="user")
    multi_engine = run_engine_plan(plan, runtime=runtime)
    good = build_engine_training_example(
        golden_case=source_case,
        multi_engine_result=multi_engine,
        runtime_payload=runtime.model_dump(mode="json"),
    )
    bad = good.model_copy(
        update={
            "quality_score": good.quality_score.model_copy(
                update={"overall_score": 0.4, "evidence_binding": 0.2, "advice_actionability": 0.2, "overclaim_risk": 0.5}
            )
        }
    )

    diff = build_training_impact_diff(run_id="pytest-impact", before_examples=[bad], after_examples=[good])

    assert diff.metric_deltas["overall_quality"] > 0
    assert diff.metric_deltas["evidence_binding"] > 0
    assert "engine_signal_weight" in diff.changed_trainable_targets
    assert diff.regression_detected is False
    assert diff.production_policy_write_allowed is False


def test_evaluation_training_spine_runner_passes_sidecar_pack() -> None:
    payload = run_evaluation_training_spine()

    assert payload["version"] == "v30.evaluation_training_spine_runner.v1"
    assert payload["status"] == "passed"
    assert payload["decision"]["evaluation_training_spine_ready"] is True
    assert payload["decision"]["case_count"] == 6
    assert payload["decision"]["passed_case_count"] == 6
    assert payload["decision"]["evidence_coverage_rate"] == 1.0
    assert payload["decision"]["overclaim_rate"] == 0.0
    assert payload["decision"]["production_policy_write_allowed"] is False


def test_admin_evaluation_training_spine_endpoint_is_quality_gate_only() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/evaluation/training-spine"
    )
    payload = route.endpoint(include_phase2=False)

    assert payload["version"] == "v30.evaluation_training_spine_runner.v1"
    assert payload["status"] == "passed"
    assert payload["decision"]["case_count"] == 3
    assert payload["admin_projection"]["ready"] is True
    assert payload["policy_boundary"]["production_policy_write_allowed"] is False
    assert payload["policy_boundary"]["chart_fact_mutation_allowed"] is False
    assert payload["policy_boundary"]["llm_as_sole_evaluator_allowed"] is False


def test_training_orchestrator_exposes_evaluation_spine_quality_gate() -> None:
    local_app = create_app()
    route = next(
        route for route in local_app.routes
        if getattr(route, "path", "") == "/api/v30/admin/training/orchestrator/plans"
    )
    payload = route.endpoint()
    plans = {row["plan_id"]: row for row in payload["plans"]}

    assert "evaluation_spine_quality_gate" in plans
    plan = plans["evaluation_spine_quality_gate"]
    assert plan["auto_apply"] is False
    assert plan["steps"] == ["evaluation_training_spine", "policy_lineage_snapshot", "quality_diff_snapshot"]
    assert plan["default_include_phase2"] is True
