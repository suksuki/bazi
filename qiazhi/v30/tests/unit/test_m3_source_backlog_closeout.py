from __future__ import annotations

from pathlib import Path

from v30.validation import (
    build_m3_source_backlog_closeout,
    run_m3_source_backlog_closeout,
)


def _training_review(*, blocked: bool = False) -> dict[str, object]:
    return {
        "version": "v30.m3_training_candidate_review.v1",
        "status": "blocked" if blocked else "completed",
        "decision": {
            "decision_status": "m3_g3_training_candidate_review_blocked" if blocked else "m3_g3_training_candidate_review_ready",
            "ready_for_training_review": not blocked,
            "candidate_count": 8,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
        },
        "candidate_summary": {
            "candidate_count": 8,
            "candidate_types": [
                "source_coverage_weight_candidate",
                "rule_path_priority_candidate",
                "domain_rule_depth_candidate",
                "counterevidence_trace_candidate",
                "dynamic_path_priority_candidate",
                "question_strategy_candidate",
                "training_distribution_candidate",
                "distribution_518k_candidate",
            ],
        },
        "source_summary": {
            "training_pipeline_passed": True,
            "validation_518k": {"included": True, "case_count": 8},
        },
    }


def _backlog_surface(*, blocked: bool = False) -> dict[str, object]:
    return {
        "version": "v30.m3_source_backlog_review_surface.v1",
        "status": "blocked" if blocked else "completed",
        "decision": {
            "decision_status": "m3_g5_backlog_review_surface_blocked" if blocked else "m3_g5_backlog_review_surface_ready",
            "ready_for_admin_review_surface": not blocked,
            "row_count": 6,
            "policy_pointer_promotion_allowed": False,
            "chart_fact_mutation_allowed": False,
            "fixed_bazi_verdict_allowed": False,
            "runtime_v20_import_allowed": False,
        },
        "query_summary": {
            "backend": "unit_test",
            "row_count": 6,
            "target_domains": ["structure_pattern", "useful_god", "ten_god"],
        },
    }


def _m3_synthetic(*, failed: bool = False) -> dict[str, object]:
    return {
        "suite_id": "v30.synthetic.m3_core_spine",
        "passed": not failed,
        "case_count": 8,
        "passed_count": 7 if failed else 8,
        "failed_count": 1 if failed else 0,
    }


def test_m3_source_backlog_closeout_ready(tmp_path: Path) -> None:
    result = build_m3_source_backlog_closeout(
        training_candidate_review=_training_review(),
        backlog_review_surface=_backlog_surface(),
        m3_synthetic=_m3_synthetic(),
        artifact_dir=tmp_path,
    )
    decision = result["decision"]

    assert result["version"] == "v30.m3_source_backlog_closeout.v1"
    assert result["status"] == "completed"
    assert decision["decision_status"] == "m3_g6_source_backlog_closeout_ready"
    assert decision["m3_closeout_ready"] is True
    assert decision["m3_steady_state_ready"] is True
    assert decision["return_to_ranked_decision_hardening_ready"] is True
    assert decision["policy_pointer_promotion_allowed"] is False
    assert decision["chart_fact_mutation_allowed"] is False
    assert result["policy_boundary"]["closeout_is_read_only"] is True
    assert result["next_mainline_selection"]["next_task"] == "M5 Evidence Consumption Hardening"
    assert Path(str(result["artifact_uri"])).exists()


def test_m3_source_backlog_closeout_blocks_missing_g5_surface() -> None:
    result = build_m3_source_backlog_closeout(
        training_candidate_review=_training_review(),
        backlog_review_surface=_backlog_surface(blocked=True),
        m3_synthetic=_m3_synthetic(),
    )

    assert result["status"] == "blocked"
    assert result["decision"]["m3_closeout_ready"] is False
    assert "g5_backlog_review_surface_ready" in result["decision"]["failed_closeout_check_ids"]
    assert result["next_mainline_selection"]["next_task"] == "M3-G6 Remediation"


def test_m3_source_backlog_closeout_blocks_failed_m3_synthetic() -> None:
    result = build_m3_source_backlog_closeout(
        training_candidate_review=_training_review(),
        backlog_review_surface=_backlog_surface(),
        m3_synthetic=_m3_synthetic(failed=True),
    )

    assert result["status"] == "blocked"
    assert result["decision"]["m3_closeout_ready"] is False
    assert "m3_core_synthetic_passed" in result["decision"]["failed_closeout_check_ids"]


def test_m3_source_backlog_closeout_script_path_runs_targeted_gates(tmp_path: Path) -> None:
    result = run_m3_source_backlog_closeout(sample_limit=8, artifact_dir=tmp_path)

    assert result["decision"]["decision_status"] == "m3_g6_source_backlog_closeout_ready"
    assert result["decision"]["training_candidate_count"] >= 8
    assert result["decision"]["source_backlog_row_count"] >= 6
    assert result["m3_synthetic_summary"]["passed"] is True
