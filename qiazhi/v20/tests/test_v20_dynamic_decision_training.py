from __future__ import annotations

from v20.learning.decision_training import build_decision_training_plan
from v20.learning.dynamic_decision_training import (
    MANUAL_DECISION_TRAINING_CASES,
    default_dynamic_decision_training_cases,
    read_dynamic_decision_training_artifact,
    run_dynamic_decision_training_batch,
    write_dynamic_decision_training_artifact,
)
from v20.learning.training_iteration import read_training_iteration_artifact, run_training_iteration
from v20.learning.knowledge_rule_review_overlay import (
    read_knowledge_rule_review_overlay_artifact,
    write_knowledge_rule_review_overlay_artifact,
)


def test_v20_dynamic_decision_training_batch_checks_runtime_quality() -> None:
    report = run_dynamic_decision_training_batch()

    assert report["status"] == "pass"
    assert report["quality_status"] == "clean"
    assert report["failure_count"] == 0
    assert report["quality_finding_count"] == 0
    assert report["case_count"] >= len(MANUAL_DECISION_TRAINING_CASES)
    assert {"career", "wealth", "strength"} <= set(report["coverage_summary"]["decision_domains"])
    assert {"q_career_structure", "q_income_factors"} <= set(report["coverage_summary"]["question_keys"])
    assert "control.shang_guan_jian_guan" in report["coverage_summary"]["practitioner_control_keys"]
    assert report["runtime_mutation"] is False
    assert not report["training_proposals"]


def test_v20_dynamic_decision_training_routes_user_intent_to_selected_question() -> None:
    cases = tuple(row for row in default_dynamic_decision_training_cases() if row.case_id.startswith("v20.dynamic.training."))
    report = run_dynamic_decision_training_batch(cases=cases)
    by_id = {row["case_id"]: row for row in report["case_results"]}

    career = by_id["v20.dynamic.training.career_shang_guan_jian_guan"]
    wealth = by_id["v20.dynamic.training.wealth_capacity"]

    assert career["selected_question_key"] == "q_career_structure"
    assert "官星、伤官和印星" in career["selected_question_title"]
    assert wealth["selected_question_key"] in {"q_income_factors", "q_income_stability"}
    assert "财" in wealth["selected_question_title"]
    assert all("材料" not in title for row in report["case_results"] for title in row["question_titles"])
    assert all("触发边界" not in title for row in report["case_results"] for title in row["question_titles"])


def test_v20_dynamic_decision_training_artifact_is_local_only(tmp_path) -> None:
    write = write_dynamic_decision_training_artifact(output_dir=tmp_path)
    status = read_dynamic_decision_training_artifact(output_dir=tmp_path)

    assert write["status"] == "written"
    assert write["report_status"] == "pass"
    assert write["runtime_mutation"] is True
    assert status["status"] == "pass"
    assert status["runtime_mutation"] is False
    assert status["failure_count"] == 0


def test_v20_decision_training_plan_includes_dynamic_script() -> None:
    plan = build_decision_training_plan()

    assert "v20/scripts/run_dynamic_decision_training.py" in plan["managed_scripts"]
    assert "v20/scripts/run_knowledge_rule_review_overlay.py" in plan["managed_scripts"]
    assert "v20/scripts/run_practitioner_calibration_training.py" in plan["managed_scripts"]
    assert "v20/scripts/run_rule_subcondition_split.py" in plan["managed_scripts"]
    assert "v20/scripts/run_decision_registry_review.py" in plan["managed_scripts"]
    assert "v20/scripts/import_calibration_postgres.py" in plan["managed_scripts"]
    assert "v20/scripts/import_decision_registry_postgres.py" in plan["managed_scripts"]
    assert "v20/scripts/run_training_iteration.py" in plan["managed_scripts"]
    assert plan["runtime_user_visible"] is False


def test_v20_training_iteration_orchestrates_script_only_loop(tmp_path) -> None:
    report = run_training_iteration(write=False, include_rule_batch=False, corpus_preview_limit=1)
    written = run_training_iteration(write=True, include_rule_batch=False, output_dir=tmp_path)
    status = read_training_iteration_artifact(output_dir=tmp_path)

    assert report["status"] == "pass"
    assert report["quality_status"] == "clean"
    assert report["runtime_mutation"] is False
    assert "dynamic_decision_training" in report["results"]
    assert "practitioner_calibration_training" in report["results"]
    assert "rule_synthetic_training" in report["results"]
    assert "knowledge_rule_review_overlay" in report["results"]
    assert "decision_registry_review" in report["results"]
    assert "corpus_preview" in report["results"]
    assert written["status"] == "written"
    assert written["report_status"] == "pass"
    assert written["runtime_mutation"] is True
    assert status["status"] == "pass"
    assert status["runtime_mutation"] is False


def test_v20_knowledge_rule_review_overlay_artifact_is_local_only(tmp_path) -> None:
    written = write_knowledge_rule_review_overlay_artifact(output_dir=tmp_path)
    status = read_knowledge_rule_review_overlay_artifact(output_dir=tmp_path)

    assert written["status"] == "written"
    assert written["report_status"] == "ready"
    assert written["runtime_promotion_candidate_count"] == 0
    assert written["runtime_mutation"] is True
    assert status["status"] == "ready"
    assert status["runtime_mutation"] is False
    assert status["artifact_type"] == "knowledge_rule_review_overlay"
