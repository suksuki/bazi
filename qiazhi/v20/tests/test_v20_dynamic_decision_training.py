from __future__ import annotations

from v20.learning.decision_training import build_decision_training_plan
import v20.learning.dynamic_decision_training as dynamic_decision_training
import v20.learning.training_iteration as training_iteration
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
import v20.learning.self_evolution as self_evolution
from v20.learning.self_evolution import read_self_evolution_artifact, run_self_evolution_cycle
import v20.learning.knowledge_rule_review_overlay as knowledge_rule_review_overlay
from v20.learning.knowledge_rule_review_overlay import (
    read_knowledge_rule_review_overlay_artifact,
    write_knowledge_rule_review_overlay_artifact,
)


def test_v20_dynamic_decision_training_batch_checks_runtime_quality() -> None:
    report = run_dynamic_decision_training_batch(cases=MANUAL_DECISION_TRAINING_CASES)

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


def test_v20_dynamic_decision_training_artifact_is_local_only(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        dynamic_decision_training,
        "run_dynamic_decision_training_batch",
        lambda **_: run_dynamic_decision_training_batch(cases=MANUAL_DECISION_TRAINING_CASES),
    )

    write = write_dynamic_decision_training_artifact(output_dir=tmp_path)
    status = read_dynamic_decision_training_artifact(output_dir=tmp_path)

    assert write["status"] == "written"
    assert write["report_status"] == "pass"
    assert write["runtime_mutation"] is True
    assert status["status"] == "pass"
    assert status["runtime_mutation"] is False
    assert status["failure_count"] == 0


def test_v20_decision_training_plan_lists_current_curated_scripts() -> None:
    plan = build_decision_training_plan()

    assert "v20/scripts/run_training_iteration.py" in plan["managed_scripts"]
    assert "v20/scripts/run_knowledge_rule_orchestrator.py" in plan["managed_scripts"]
    assert "v20/scripts/run_synthetic_case_suite.py" in plan["managed_scripts"]
    assert "v20/scripts/run_knowledge_rule_review_overlay.py" in plan["managed_scripts"]
    assert "v20/scripts/run_practitioner_calibration_training.py" in plan["managed_scripts"]
    assert "v20/scripts/run_rule_subcondition_split.py" in plan["managed_scripts"]
    assert "v20/scripts/run_decision_registry_iteration.py" in plan["managed_scripts"]
    assert "v20/scripts/import_calibration_postgres.py" in plan["managed_scripts"]
    assert "v20/scripts/import_decision_registry_postgres.py" in plan["managed_scripts"]
    assert "v20/scripts/run_dynamic_decision_training.py" not in plan["managed_scripts"]
    assert "v20/scripts/run_knowledge_completion.py" not in plan["managed_scripts"]
    assert "v20/scripts/run_self_evolution.py" not in plan["managed_scripts"]
    assert "v20/scripts/run_active_generation.py" not in plan["managed_scripts"]
    assert plan["runtime_user_visible"] is False


def test_v20_training_iteration_orchestrates_script_only_loop(monkeypatch, tmp_path) -> None:
    _stub_training_iteration(monkeypatch)

    report = training_iteration.run_training_iteration(write=False, include_rule_batch=False, corpus_preview_limit=1)
    written = training_iteration.run_training_iteration(write=True, include_rule_batch=False, output_dir=tmp_path)
    status = read_training_iteration_artifact(output_dir=tmp_path)

    assert report["status"] == "pass"
    assert report["quality_status"] == "clean"
    assert report["runtime_mutation"] is False
    assert "dynamic_decision_training" in report["results"]
    assert "practitioner_calibration_training" in report["results"]
    assert "rule_synthetic_training" in report["results"]
    assert "synthetic_bazi_coverage" in report["results"]
    assert "synthetic_bazi_replay" in report["results"]
    assert "question_dag_training" in report["results"]
    assert "question_review_training" in report["results"]
    assert "question_dag_policy_replay" in report["results"]
    assert "question_dag_policy_promotion_gate" in report["results"]
    assert "next_question_synthetic_validation" in report["results"]
    assert "role_interaction_training" in report["results"]
    assert "role_question_click_training" in report["results"]
    assert "role_view_policy_candidates" in report["results"]
    assert "role_view_policy_replay" in report["results"]
    assert "role_view_policy_calibration" in report["results"]
    assert "role_view_policy_promotion_gate" in report["results"]
    assert "knowledge_rule_review_overlay" in report["results"]
    assert "decision_registry_iteration" in report["results"]
    assert "corpus_preview" in report["results"]
    assert written["status"] == "written"
    assert written["report_status"] == "pass"
    assert written["runtime_mutation"] is True
    assert status["status"] == "pass"
    assert status["runtime_mutation"] is False


def _stub_training_iteration(monkeypatch) -> None:
    def ready(name: str) -> dict[str, object]:
        return {
            "version": f"v20.test.{name}",
            "status": "pass",
            "ok": True,
            "failures": [],
            "quality_findings": [],
            "runtime_mutation": False,
        }

    phase_map = {
        "run_dynamic_decision_training_batch": "dynamic",
        "write_dynamic_decision_training_artifact": "dynamic",
        "build_practitioner_calibration_training_report": "practitioner",
        "write_practitioner_calibration_training_artifact": "practitioner",
        "build_orchestrator_memory_training_report": "memory",
        "write_orchestrator_memory_training_artifact": "memory",
        "build_policy_observability_training_report": "policy_observability",
        "write_policy_observability_training_artifact": "policy_observability",
        "build_orchestrator_policy_candidate_report": "policy_candidate",
        "write_orchestrator_policy_candidate_artifact": "policy_candidate",
        "build_orchestrator_policy_version_candidate": "policy_version",
        "write_orchestrator_policy_version_candidate_artifact": "policy_version",
        "build_orchestrator_policy_replay_report": "policy_replay",
        "write_orchestrator_policy_replay_artifact": "policy_replay",
        "build_arbitration_loop_report": "arbitration",
        "write_arbitration_loop_artifact": "arbitration",
        "build_question_ranking_learning_report": "question_ranking",
        "write_question_ranking_learning_artifact": "question_ranking",
        "synthetic_bazi_coverage_report": "synthetic_coverage",
        "run_synthetic_bazi_replay": "synthetic_replay",
        "build_question_dag_training_report": "question_dag",
        "build_question_review_training_report": "question_review",
        "write_question_review_training_artifact": "question_review",
        "build_question_dag_policy_replay_report": "question_dag_replay",
        "write_question_dag_policy_replay_artifact": "question_dag_replay",
        "build_question_dag_policy_promotion_gate": "question_dag_promotion",
        "build_next_question_synthetic_validation_report": "next_question_synthetic",
        "write_next_question_synthetic_validation_artifact": "next_question_synthetic",
        "build_role_interaction_training_report": "role_interaction",
        "build_role_question_click_training_report": "role_click",
        "write_role_question_click_training_artifact": "role_click",
        "build_role_view_policy_candidate_report": "role_policy_candidate",
        "write_role_view_policy_candidate_artifact": "role_policy_candidate",
        "build_role_view_policy_replay_report": "role_policy_replay",
        "write_role_view_policy_replay_artifact": "role_policy_replay",
        "build_role_view_policy_calibration_report": "role_policy_calibration",
        "build_role_view_policy_promotion_gate": "role_policy_promotion",
        "build_rule_synthetic_training_report": "rule_synthetic",
        "write_rule_synthetic_training_artifact": "rule_synthetic",
        "build_knowledge_rule_review_overlay": "knowledge_overlay",
        "write_knowledge_rule_review_overlay_artifact": "knowledge_overlay",
        "build_rule_subcondition_split_report": "subcondition",
        "write_rule_subcondition_split_artifact": "subcondition",
        "build_decision_registry_iteration_report": "registry",
        "write_decision_registry_iteration_artifact": "registry",
        "build_decision_training_plan": "plan",
    }
    for attr, name in phase_map.items():
        monkeypatch.setattr(training_iteration, attr, lambda *_, name=name, **__: ready(name))
    monkeypatch.setattr(training_iteration, "preview_full_precompute_batch", lambda **_: ready("corpus_preview"))


def test_v20_self_evolution_manifest_wraps_training_iteration(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(self_evolution, "run_training_iteration", lambda **_: _self_evolution_training_report())

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


def test_v20_active_package_materializes_self_evolution_requests(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(self_evolution, "run_training_iteration", lambda **_: _self_evolution_training_report())

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


def test_v20_knowledge_rule_review_overlay_artifact_is_local_only(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        knowledge_rule_review_overlay,
        "build_knowledge_rule_review_overlay",
        lambda **_: {
            "version": "v20.test.knowledge_rule_review_overlay",
            "status": "ready",
            "rule_count": 2,
            "active_weight_candidate_count": 1,
            "runtime_activation_candidate_count": 1,
            "runtime_mutation": False,
        },
    )

    written = write_knowledge_rule_review_overlay_artifact(output_dir=tmp_path)
    status = read_knowledge_rule_review_overlay_artifact(output_dir=tmp_path)

    assert written["status"] == "written"
    assert written["report_status"] == "ready"
    assert written["runtime_activation_candidate_count"] >= 1
    assert written["runtime_mutation"] is True
    assert status["status"] == "ready"
    assert status["runtime_mutation"] is False
    assert status["artifact_type"] == "knowledge_rule_review_overlay"


def _self_evolution_training_report() -> dict[str, object]:
    return {
        "version": "v20.test.training_iteration",
        "status": "pass",
        "quality_status": "clean",
        "phase_count": 4,
        "failure_count": 0,
        "quality_finding_count": 0,
        "failures": [],
        "results": {
            "dynamic_decision_training": {
                "version": "v20.test.dynamic",
                "status": "pass",
                "coverage_summary": {
                    "decision_domains": ("career", "wealth", "strength"),
                    "question_keys": ("q_career_structure", "q_income_factors"),
                },
            },
            "rule_synthetic_training": {
                "version": "v20.test.rule_synthetic",
                "status": "pass",
                "rule_domain_training": (
                    {
                        "domain": "career",
                        "training_action": "eligible_for_active_weight",
                        "case_count": 3,
                        "synthetic_confidence": 0.86,
                    },
                ),
                "suite": {"failures": ()},
            },
            "rule_replay_eval": {
                "version": "v20.test.rule_replay",
                "status": "pass",
                "evaluations": ({"domain": "career"}, {"domain": "wealth"}),
            },
            "rule_subcondition_split": {
                "version": "v20.test.subcondition",
                "status": "ready",
                "packets": (
                    {
                        "domain": "strength",
                        "rule_key": "rule.test.strength",
                        "counterexample_signal_count": 1,
                    },
                ),
            },
        },
    }
