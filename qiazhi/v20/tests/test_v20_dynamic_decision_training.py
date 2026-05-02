from __future__ import annotations

from v20.learning.decision_training import build_decision_training_plan
from v20.learning.active_generation import (
    build_active_package,
    read_active_package_artifact,
    write_active_package_artifact,
)
from v20.learning.dynamic_decision_training import (
    MANUAL_DECISION_TRAINING_CASES,
    default_dynamic_decision_training_cases,
    read_dynamic_decision_training_artifact,
    run_dynamic_decision_training_batch,
    write_dynamic_decision_training_artifact,
)
from v20.learning.training_iteration import read_training_iteration_artifact, run_training_iteration
from v20.learning.self_evolution import read_self_evolution_artifact, run_self_evolution_cycle
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
    assert "v20/scripts/run_knowledge_completion.py" in plan["managed_scripts"]
    assert "v20/scripts/run_knowledge_rule_review_overlay.py" in plan["managed_scripts"]
    assert "v20/scripts/run_practitioner_calibration_training.py" in plan["managed_scripts"]
    assert "v20/scripts/run_rule_subcondition_split.py" in plan["managed_scripts"]
    assert "v20/scripts/run_decision_registry_iteration.py" in plan["managed_scripts"]
    assert "v20/scripts/import_calibration_postgres.py" in plan["managed_scripts"]
    assert "v20/scripts/import_decision_registry_postgres.py" in plan["managed_scripts"]
    assert "v20/scripts/run_training_iteration.py" in plan["managed_scripts"]
    assert "v20/scripts/run_self_evolution.py" in plan["managed_scripts"]
    assert "v20/scripts/run_active_generation.py" in plan["managed_scripts"]
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
    assert "decision_registry_iteration" in report["results"]
    assert "corpus_preview" in report["results"]
    assert written["status"] == "written"
    assert written["report_status"] == "pass"
    assert written["runtime_mutation"] is True
    assert status["status"] == "pass"
    assert status["runtime_mutation"] is False


def test_v20_self_evolution_manifest_wraps_training_iteration(tmp_path) -> None:
    manifest = run_self_evolution_cycle(
        write=False,
        include_rule_batch=False,
        corpus_preview_limit=1,
    )
    written = run_self_evolution_cycle(
        write=True,
        include_rule_batch=False,
        output_dir=tmp_path,
    )
    status = read_self_evolution_artifact(output_dir=tmp_path)

    assert manifest["version"] == "v20.self_evolution_manifest.v1"
    assert manifest["training_status"] == "pass"
    assert manifest["runtime_mutation"] is False
    assert manifest["active_item_requests"]["total_request_count"] > 0
    assert manifest["activation_policy"]["runtime_activation_allowed"] is True
    assert manifest["status"] == "active_ready"
    assert "LLM_GENERATES_ACTIVE_ITEMS_NOT_CORE_TRUTH" in manifest["guardrails"]
    assert written["status"] == "written"
    assert written["runtime_mutation"] is True
    assert status["version"] == "v20.self_evolution_manifest.v1"
    assert status["runtime_mutation"] is False


def test_v20_active_package_materializes_self_evolution_requests(tmp_path) -> None:
    manifest = run_self_evolution_cycle(
        write=False,
        include_rule_batch=False,
        corpus_preview_limit=1,
    )
    package = build_active_package(manifest)
    written = write_active_package_artifact(package, output_dir=tmp_path)
    status = read_active_package_artifact(output_dir=tmp_path)

    assert package["version"] == "v20.active_package.v1"
    assert package["source_run_id"] == manifest["run_id"]
    assert package["status"] == "active"
    assert package["active_item_count"] == manifest["active_item_requests"]["total_request_count"]
    assert package["active_item_type_counts"]["rule_active_item"] >= 1
    assert package["active_item_type_counts"]["portrait_active_item"] >= 1
    assert package["active_item_type_counts"]["feature_active_item"] >= 1
    assert package["active_item_type_counts"]["question_active_item"] >= 1
    assert package["activation_policy"]["runtime_activation_allowed"] is True
    assert "ACTIVE_PACKAGE_CAN_FEED_RUNTIME" in package["guardrails"]
    assert all(row["runtime_allowed"] is True for row in package["active_items"])
    assert all(row["active_item_status"] == "active" for row in package["active_items"])
    assert all(row["validation_requirements"] for row in package["active_items"])
    assert written["status"] == "written"
    assert written["active_item_count"] == package["active_item_count"]
    assert status["version"] == "v20.active_package.v1"
    assert status["runtime_mutation"] is False


def test_v20_knowledge_rule_review_overlay_artifact_is_local_only(tmp_path) -> None:
    written = write_knowledge_rule_review_overlay_artifact(output_dir=tmp_path)
    status = read_knowledge_rule_review_overlay_artifact(output_dir=tmp_path)

    assert written["status"] == "written"
    assert written["report_status"] == "ready"
    assert written["runtime_activation_candidate_count"] >= 1
    assert written["runtime_mutation"] is True
    assert status["status"] == "ready"
    assert status["runtime_mutation"] is False
    assert status["artifact_type"] == "knowledge_rule_review_overlay"
