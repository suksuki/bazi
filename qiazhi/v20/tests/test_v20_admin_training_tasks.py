from __future__ import annotations

import time

import pytest

from v20.ops.training_tasks import (
    _activate_training_bundle,
    _domain_activation_result,
    list_training_activation_preflights,
    list_training_tasks,
    pause_training_task,
    prepare_training_task_activation,
    read_training_task,
    start_training_task,
    training_task_registry,
)


def test_v20_admin_training_task_registry_exposes_safe_tasks() -> None:
    registry = training_task_registry()
    keys = {row["task_key"] for row in registry["tasks"]}

    assert registry["status"] == "ready"
    assert registry["mainline_completion"]["status"] in {"complete", "needs_work"}
    assert 0 <= registry["mainline_completion"]["percent"] <= 100
    assert registry["mainline_completion"]["component_count"] >= 5
    assert registry["parameter_impact"]["status"] == "ready"
    assert registry["parameter_impact"]["auto_parameter_optimization"] is True
    assert registry["parameter_impact"]["runtime_parameter_change_requires_activation"] is True
    assert registry["parameter_impact"]["impactful_family_count"] >= 1
    assert registry["training_plan"]["status"] == "ready"
    assert registry["training_plan"]["strategy"] == "fast_iteration_with_gated_auto_apply"
    assert {row["job_key"] for row in registry["training_plan"]["profiles"]} >= {"fast", "nightly", "weekly", "full"}
    topics = {row["topic_key"]: row for row in registry["training_plan"]["optimization_topics"]}
    assert set(topics) >= {"portrait", "rule", "knowledge", "intelligent_qa", "role_experience", "llm_context", "feature_corpus"}
    assert "rule_synthetic_training" in topics["rule"]["atomic_trainings"]
    assert "role_interaction_training" in topics["role_experience"]["atomic_trainings"]
    assert "portrait_axis_weight" in topics["portrait"]["parameter_targets"]
    assert topics["portrait"]["optimizer_writer_status"] == "ready"
    assert topics["portrait"]["training_groups"]
    assert topics["rule"]["optimizer_writer_status"] == "ready"
    assert topics["knowledge"]["optimizer_writer_status"] == "ready"
    assert topics["intelligent_qa"]["optimizer_writer_status"] == "ready"
    assert topics["role_experience"]["optimizer_writer_status"] == "ready"
    assert "role_context_density_weight" in topics["llm_context"]["parameter_targets"]
    assert topics["llm_context"]["optimizer_writer_status"] == "ready"
    assert topics["feature_corpus"]["optimizer_writer_status"] == "ready"
    assert {row["topic_key"] for row in topics.values()} >= {
        "structure_dynamics",
        "portrait",
        "intelligent_qa",
        "role_experience",
        "llm_context",
        "feature_corpus",
    }
    assert all("training_groups" in row for row in topics.values())
    assert registry["training_plan"]["synthetic_rule_plan"]["version"] == "v20.admin_synthetic_rule_training_plan.v1"
    assert registry["training_plan"]["structure_dynamics_synthetic_plan"]["version"] == "v20.admin_structure_dynamics_synthetic_plan.v1"
    assert registry["training_plan"]["structure_dynamics_synthetic_plan"]["status"] == "covered"
    assert registry["training_plan"]["structure_dynamics_synthetic_plan"]["dynamic_path_consistency"] == 1.0
    assert registry["training_plan"]["structure_dynamics_synthetic_plan"]["semantic_candidate_precision"] == 1.0
    assert registry["training_plan"]["structure_dynamics_path_distribution"]["version"] == "v20.structure_dynamics_path_distribution.v1"
    assert registry["training_plan"]["structure_dynamics_path_distribution"]["counterexample_coverage"]["status"] == "covered"
    assert registry["training_plan"]["structure_dynamics_path_distribution"]["time_blocker_coverage"]["status"] == "covered"
    assert registry["training_plan"]["structure_dynamics_knowledge_coverage"]["version"] == "v20.structure_dynamics_knowledge_coverage.v1"
    assert registry["training_plan"]["structure_dynamics_knowledge_coverage"]["status"] == "covered_current_scope"
    assert registry["training_plan"]["structure_dynamics_knowledge_coverage"]["unsupported_count"] == 0
    assert registry["training_plan"]["structure_dynamics_corpus_distribution"]["status"] in {"not_built", "completed", "completed_with_findings", "unavailable"}
    assert registry["training_plan"]["structure_dynamics_legacy_v2_switch"]["version"] == "v20.structure_dynamics_legacy_v2_switch.v1"
    assert registry["training_plan"]["structure_dynamics_legacy_v2_switch"]["status"] == "switch_ready_primary"
    assert registry["training_plan"]["structure_dynamics_legacy_v2_switch"]["unexplained_conflict_count"] == 0
    assert registry["training_plan"]["candidate_quality_signal"]["version"] == "v20.admin_candidate_quality_signal.v1"
    assert registry["training_plan"]["candidate_quality_signal"]["status"] in {"ready_for_candidate_apply", "needs_more_replay"}
    assert "synthetic_gap_count" in registry["training_plan"]["candidate_quality_signal"]
    assert "corpus_training_status" in registry["training_plan"]["candidate_quality_signal"]
    assert 0 <= registry["training_plan"]["candidate_quality_signal"]["candidate_promotion_score"] <= 1
    assert registry["training_plan"]["candidate_quality_signal"]["promotion_decision"] in {"promote_candidate", "run_recommended_replay"}
    tuning = registry["training_plan"]["central_brain_tuning_package"]
    assert tuning["version"] == "v20.central_brain_tuning_package.v1"
    assert tuning["decision"] in {"direct_apply_candidates", "continue_training"}
    assert tuning["context_drift_score"] == registry["training_plan"]["candidate_quality_signal"]["quality_scores"]["bazi_context_drift_score"]
    assert tuning["parameter_update_count"] == len(registry["training_plan"]["optimization_topics"])
    assert "orchestrator_runtime_policy_pointer" in tuning["runtime_pointer_targets"]
    assert "structure_dynamics_runtime_policy_pointer" in tuning["runtime_pointer_targets"]
    assert tuning["apply_report"]["version"] == "v20.central_brain_tuning_apply_report.v1"
    if tuning["decision"] == "direct_apply_candidates":
        assert tuning["apply_report"]["ready_pointer_count"] == tuning["apply_report"]["pointer_update_count"]
    else:
        assert tuning["apply_report"]["blocked_pointer_count"] >= 1
    assert {row["runtime_pointer_target"] for row in tuning["apply_report"]["pointer_updates"]} == set(tuning["runtime_pointer_targets"])
    assert set(tuning["input_signal_contract"]) == {"bazi_context", "synthetic", "corpus_518k", "runtime_writer"}
    assert "SYNTHETIC_AND_518K_SIGNALS_SHARE_ONE_PROMOTION_DECISION" in tuning["guardrails"]
    assert set(registry["training_plan"]["candidate_quality_signal"]["quality_scores"]) >= {
        "synthetic_pass_rate",
        "structure_dynamic_path_consistency",
        "structure_semantic_candidate_precision",
        "rule_false_positive_rate",
        "portrait_drift_score",
        "question_focus_score",
        "corpus_distribution_shift",
        "similar_case_stability",
        "bazi_context_drift_score",
    }
    assert set(registry["training_plan"]["candidate_quality_signal"]["recommended_tasks"]) <= {
        "synthetic_case_suite",
        "structure_dynamics_synthetic",
        "structure_dynamics_corpus_distribution",
        "structure_dynamics_scheduled_shard",
        "rule_synthetic_training",
        "nightly_executor_skeleton",
        "full_precompute_preview",
    }
    assert registry["training_plan"]["dedupe_summary"]["tracked_task_count"] == registry["task_count"]
    assert registry["training_plan"]["dedupe_summary"]["cooldown_blocked_count"] >= 0
    assert any(row["cadence_key"] == "nightly" for row in registry["training_plan"]["recommended_cadence"])
    assert registry["central_brain"]["version"] == "v20.admin_training_central_brain.v1"
    assert registry["central_brain"]["direct_apply_policy"] == "training_outputs_attempt_runtime_pointer_apply_without_human_review"
    brain_sections = {row["node_key"]: row for row in registry["central_brain"]["brain_graph_task_sections"]}
    assert set(brain_sections) >= {
        "knowledge_gap_pick",
        "rule_candidate_generation",
        "portrait_mapping_generation",
        "question_policy_generation",
        "role_policy_generation",
        "llm_context_policy_generation",
        "synthetic_validation",
        "corpus_replay_518k",
        "parameter_optimizer",
    }
    assert "knowledge_rule_orchestrator" in brain_sections["knowledge_gap_pick"]["task_keys"]
    assert "training_iteration_fast" in brain_sections["llm_context_policy_generation"]["task_keys"]
    assert "role_view_runtime_policy_pointer" in brain_sections["llm_context_policy_generation"]["runtime_pointer_targets"]
    assert "orchestrator_runtime_policy_pointer" in brain_sections["llm_context_policy_generation"]["runtime_pointer_targets"]
    assert "knowledge_runtime_policy_pointer" in brain_sections["knowledge_gap_pick"]["runtime_pointer_targets"]
    assert "rule_runtime_policy_pointer" in brain_sections["parameter_optimizer"]["runtime_pointer_targets"]
    assert "structure_dynamics_runtime_policy_pointer" in brain_sections["parameter_optimizer"]["runtime_pointer_targets"]
    assert {row["key"] for row in registry["mainline_completion"]["components"]} >= {
        "admin_training_page",
        "knowledge_mainline",
        "rule_iteration",
        "corpus_precompute",
        "ops_validation",
    }
    assert registry["mainline_completion"]["remaining_count"] == len(registry["mainline_completion"]["remaining_items"])
    assert "training_iteration_fast" in keys
    assert "synthetic_case_suite" in keys
    assert "structure_dynamics_synthetic" in keys
    assert "structure_dynamics_corpus_distribution" in keys
    assert "structure_dynamics_scheduled_shard" in keys
    assert "nightly_executor_skeleton" in keys
    assert "question_dag_training" in keys
    assert "next_question_synthetic_validation" in keys
    assert "role_interaction_training" in keys
    assert "rule_synthetic_training" in keys
    assert "rule_replay_eval" in keys
    assert "knowledge_rule_orchestrator" in keys
    assert "knowledge_rule_review_overlay" in keys
    assert "release_smoke" not in keys
    assert "dynamic_decision_training" not in keys
    assert registry["task_count"] == 22
    assert registry["total_task_count"] == registry["task_count"]
    assert "retired_task_count" not in registry
    assert "retired_tasks" not in registry
    assert {row["section_key"] for row in registry["sections"]} >= {"daily", "question", "rule", "knowledge", "corpus"}
    assert "ops" not in {row["section_key"] for row in registry["sections"]}
    assert registry["recommended_next"]["task_key"] == "training_iteration_fast"
    assert registry["recommended_next"]["blocked_by_active_task"] is False
    assert all(row["recommended_order"] > 0 for row in registry["tasks"])
    assert all(row["risk_level"] in {"low", "normal", "high"} for row in registry["tasks"])
    assert all(row["dedupe_policy"]["version"] == "v20.admin_training_task_dedupe_policy.v1" for row in registry["tasks"])
    assert all("fingerprint" in row["dedupe_policy"] for row in registry["tasks"])
    assert all("primary_brain_node" in row for row in registry["tasks"])
    assert all("runtime_pointer_targets" in row for row in registry["tasks"])
    orchestrator_task = next(row for row in registry["tasks"] if row["task_key"] == "knowledge_rule_orchestrator")
    assert orchestrator_task["primary_brain_node"] == "knowledge_gap_pick"
    assert "knowledge_runtime_policy_pointer" in orchestrator_task["runtime_pointer_targets"]
    assert next(row for row in registry["tasks"] if row["task_key"] == "synthetic_case_suite")["primary_brain_node"] == "synthetic_validation"
    structure_task = next(row for row in registry["tasks"] if row["task_key"] == "structure_dynamics_synthetic")
    assert structure_task["primary_brain_node"] == "synthetic_validation"
    assert "structure_dynamics_runtime_policy_pointer" in structure_task["runtime_pointer_targets"]
    structure_corpus_task = next(row for row in registry["tasks"] if row["task_key"] == "structure_dynamics_corpus_distribution")
    assert structure_corpus_task["primary_brain_node"] == "corpus_replay_518k"
    assert structure_corpus_task["writes_artifact"] is True
    assert structure_corpus_task["runtime_mutation"] is True
    assert "structure_dynamics_runtime_policy_pointer" in structure_corpus_task["runtime_pointer_targets"]
    structure_scheduled_task = next(row for row in registry["tasks"] if row["task_key"] == "structure_dynamics_scheduled_shard")
    assert structure_scheduled_task["primary_brain_node"] == "corpus_replay_518k"
    assert structure_scheduled_task["writes_artifact"] is True
    assert structure_scheduled_task["runtime_mutation"] is True
    assert structure_scheduled_task["risk_level"] == "high"
    assert "--start" in structure_scheduled_task["default_args"]
    assert "1024" in structure_scheduled_task["default_args"]
    assert "structure_dynamics_runtime_policy_pointer" in structure_scheduled_task["runtime_pointer_targets"]
    assert next(row for row in registry["tasks"] if row["task_key"] == "practitioner_calibration_training")["primary_brain_node"] == "portrait_mapping_generation"
    assert any(row["is_recommended_next"] for row in registry["tasks"])
    assert all("NO_RUNTIME_POINTER_MUTATION" in row["guardrails"] for row in registry["tasks"])
    assert "ONE_ADMIN_TRAINING_TASK_AT_A_TIME" in registry["guardrails"]
    assert "SUPPORTED_TASKS_AUTO_APPLY_RUNTIME_POINTERS" in registry["guardrails"]
    assert "MAINLINE_COMPLETION_STATUS_EXPLICIT" in registry["guardrails"]
    assert "PARAMETER_IMPACT_STATUS_EXPLICIT" in registry["guardrails"]
    assert "TRAINING_PLAN_AND_DEDUPE_POLICY_EXPLICIT" in registry["guardrails"]
    assert "CENTRAL_BRAIN_GRAPH_GROUPING_EXPLICIT" in registry["guardrails"]
    assert "CANDIDATE_QUALITY_SIGNAL_COMBINES_SYNTHETIC_AND_CORPUS_REPLAY" in registry["training_plan"]["guardrails"]
    assert "PROMOTION_SCORE_COMBINES_SYNTHETIC_AND_518K_REPLAY" in registry["training_plan"]["candidate_quality_signal"]["guardrails"]


def test_v20_admin_training_task_persists_progress_across_reads(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    task = start_training_task("question_source_training")

    assert task["status"] == "running"
    assert task["task_key"] == "question_source_training"
    assert task["progress_percent"] >= 1

    latest = {}
    for _ in range(40):
        latest = read_training_task(str(task["task_id"]))
        if latest["status"] == "succeeded" and latest.get("auto_parameter_apply"):
            break
        if latest["status"] == "failed":
            break
        time.sleep(0.1)

    assert latest["status"] == "succeeded"
    assert latest["progress_percent"] == 100
    assert latest["runtime_mutation"] is True
    assert "TASK_STATUS_PERSISTED_TO_RUNTIME_DIR" in latest["guardrails"]
    assert latest["result_summary"]["status"] == "succeeded"
    assert latest["result_summary"]["outcome"] == "训练完成"
    assert latest["result_summary"]["machine_gate"]["status"] == "machine_ready"
    assert latest["result_summary"]["machine_gate"]["can_apply_parameters"] is True
    assert latest["result_summary"]["context_quality_signal"]["version"] == "v20.training_context_quality_signal.v1"
    assert latest["result_summary"]["context_quality_signal"]["bazi_context_drift_score"] == 0
    assert latest["result_summary"]["publish_preview"]["eligible_for_publish"] is True
    assert latest["result_summary"]["publish_preview"]["status"] == "ready"
    assert latest["result_summary"]["publish_preview"]["activation_family"] == "question_policy"
    assert latest["result_summary"]["publish_preview"]["auto_optimization"]["enabled"] is True
    assert latest["result_summary"]["publish_preview"]["auto_optimization"]["parameter_apply_supported"] is True
    assert latest["result_summary"]["publish_preview"]["auto_optimization"]["auto_apply_candidate"] is True
    assert latest["auto_parameter_apply"]["activation_plan"]["activation_family"] == "question_policy"
    assert "RESULT_SUMMARY_DERIVED_FROM_TASK_STATE" in latest["result_summary"]["guardrails"]
    assert "MACHINE_OPTIMIZATION_GATE_DOES_NOT_MUTATE_RUNTIME" in latest["result_summary"]["guardrails"]
    assert "PUBLISH_PREVIEW_DOES_NOT_MUTATE_RUNTIME" in latest["result_summary"]["guardrails"]

    listing = list_training_tasks()
    assert listing["latest"]["task_id"] == task["task_id"]
    assert listing["tasks"][0]["task_id"] == task["task_id"]
    assert listing["latest_result_summary"]["status"] == "succeeded"


def test_v20_admin_structure_dynamics_task_auto_applies_pointer(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    task = start_training_task("structure_dynamics_synthetic")

    latest = {}
    for _ in range(400):
        latest = read_training_task(str(task["task_id"]))
        if latest.get("status") == "succeeded" and latest.get("auto_parameter_apply"):
            break
        if latest.get("status") == "failed":
            break
        time.sleep(0.2)

    assert latest["status"] == "succeeded"
    assert latest["runtime_mutation"] is True
    assert latest["result_summary"]["contract_version"] == "v20.structure_dynamics_synthetic.v1"
    assert latest["result_summary"]["machine_gate"]["status"] == "machine_ready"
    assert latest["result_summary"]["publish_preview"]["activation_family"] == "structure_dynamics_policy"
    assert latest["auto_parameter_apply_status"] == "candidate_active"
    assert (tmp_path / "training" / "structure_dynamics_policy_versions" / "active_pointer.json").exists()


def test_v20_admin_training_task_pause_marks_running_task(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    task = start_training_task("nightly_executor_skeleton")

    paused = pause_training_task(str(task["task_id"]))

    assert paused["task_id"] == task["task_id"]
    assert paused["status"] in {"paused", "succeeded", "failed"}
    if paused["status"] == "paused":
        assert paused["current_stage"] == "paused_by_admin"
        assert paused["paused_by"] == "admin"


def test_v20_admin_training_task_blocks_parallel_starts(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    task = start_training_task("nightly_executor_skeleton")
    blocked = start_training_task("training_iteration_fast")

    assert blocked["task_id"] == task["task_id"]
    assert blocked["start_blocked"] is True
    assert blocked["requested_task_key"] == "training_iteration_fast"
    assert "ONE_ADMIN_TRAINING_TASK_AT_A_TIME" in blocked["guardrails"]

    pause_training_task(str(task["task_id"]))


def test_v20_admin_training_task_blocks_duplicate_success_inside_cooldown(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    task = start_training_task("question_source_training")

    latest = {}
    for _ in range(100):
        latest = read_training_task(str(task["task_id"]))
        if latest["status"] in {"succeeded", "failed"}:
            break
        time.sleep(0.1)

    assert latest["status"] == "succeeded"
    blocked = start_training_task("question_source_training")

    assert blocked["status"] == "skipped"
    assert blocked["start_blocked"] is True
    assert blocked["duplicate_blocked"] is True
    assert blocked["dedupe_policy"]["blocking_gate"] == "duplicate_success_cooldown"
    assert "DUPLICATE_TRAINING_COOLDOWN_BLOCK" in blocked["guardrails"]


def test_v20_admin_training_task_rejects_removed_legacy_plan_entry(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    with pytest.raises(ValueError, match="Unknown training task"):
        start_training_task("learning_orchestrator_nightly_plan")


def test_v20_admin_rule_iteration_activation_uses_optimizer_writer(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    result = _domain_activation_result(
        task={"task_key": "rule_replay_eval"},
        eligible=True,
        family="rule_iteration",
        dry_run=False,
        confirm_token="ACTIVATE_TRAINING_RESULT",
        reason="test",
        source_role="admin",
    )

    assert result["status"] == "blocked_by_machine_gate"
    assert result["activation_family"] == "rule_iteration"
    assert result["blocking_gate"] == "blocked_by_machine_gate"
    assert result["domain_result"]["version"] == "v20.rule_runtime_pointer_activation_result.v1"
    assert result["runtime_mutation"] is False


def test_v20_admin_training_bundle_activation_fans_out_to_pointer_writers(monkeypatch) -> None:
    calls: list[str] = []

    def writer(name: str, mutates: bool):
        def run(*, source_role: str, reason: str) -> dict[str, object]:
            calls.append(f"{name}:{source_role}:{reason}")
            return {
                "version": f"v20.{name}.activation_result.v1",
                "status": f"{name}_active" if mutates else "blocked_by_machine_gate",
                "active_policy_version": f"v20.{name}.candidate.v1" if mutates else "",
                "blocking_gate": "" if mutates else f"{name}_not_ready",
                "runtime_mutation": mutates,
            }

        return run

    monkeypatch.setattr("v20.ops.training_tasks._activate_orchestrator_policy", writer("orchestrator", True))
    monkeypatch.setattr("v20.ops.training_tasks._activate_question_policy", writer("question", False))
    monkeypatch.setattr("v20.ops.training_tasks._activate_role_view_policy", writer("role_view", True))
    monkeypatch.setattr("v20.ops.training_tasks._activate_rule_policy", writer("rule", False))
    monkeypatch.setattr("v20.ops.training_tasks._activate_portrait_policy", writer("portrait", False))
    monkeypatch.setattr("v20.ops.training_tasks._activate_structure_dynamics_policy", writer("structure_dynamics", True))
    monkeypatch.setattr("v20.ops.training_tasks._activate_knowledge_policy", writer("knowledge", False))
    monkeypatch.setattr("v20.ops.training_tasks._activate_corpus_policy", writer("corpus", False))

    result = _activate_training_bundle(source_role="system", reason="auto")

    assert result["version"] == "v20.training_bundle_activation_result.v1"
    assert result["status"] == "bundle_active"
    assert result["activated_writer_count"] == 3
    assert result["blocked_writer_count"] == 5
    assert result["apply_report"]["version"] == "v20.training_bundle_apply_report.v1"
    assert result["apply_report"]["applied_pointer_count"] == 3
    assert result["apply_report"]["blocked_pointer_count"] == 5
    assert "orchestrator_runtime_policy_pointer" in {row["runtime_pointer_target"] for row in result["apply_report"]["pointer_results"]}
    assert result["runtime_mutation"] is True
    assert {row["writer_key"] for row in result["writer_results"]} == {
        "orchestrator_policy",
        "question_policy",
        "role_view_policy",
        "rule_policy",
        "portrait_policy",
        "structure_dynamics_policy",
        "knowledge_policy",
        "corpus_policy",
    }
    assert len(calls) == 8


def test_v20_admin_orchestrator_training_bundle_uses_pointer_writers(monkeypatch) -> None:
    calls: list[str] = []

    def writer(name: str):
        def run(*, source_role: str, reason: str) -> dict[str, object]:
            calls.append(f"{name}:{source_role}:{reason}")
            return {
                "version": f"v20.{name}.activation_result.v1",
                "status": "blocked_by_machine_gate",
                "blocking_gate": f"{name}_not_ready",
                "runtime_mutation": False,
            }

        return run

    monkeypatch.setattr("v20.ops.training_tasks._activate_orchestrator_policy", writer("orchestrator"))
    monkeypatch.setattr("v20.ops.training_tasks._activate_question_policy", writer("question"))
    monkeypatch.setattr("v20.ops.training_tasks._activate_role_view_policy", writer("role_view"))
    monkeypatch.setattr("v20.ops.training_tasks._activate_rule_policy", writer("rule"))
    monkeypatch.setattr("v20.ops.training_tasks._activate_portrait_policy", writer("portrait"))
    monkeypatch.setattr("v20.ops.training_tasks._activate_structure_dynamics_policy", writer("structure_dynamics"))
    monkeypatch.setattr("v20.ops.training_tasks._activate_knowledge_policy", writer("knowledge"))
    monkeypatch.setattr("v20.ops.training_tasks._activate_corpus_policy", writer("corpus"))

    result = _domain_activation_result(
        task={"task_key": "knowledge_rule_orchestrator", "category": "orchestrator"},
        eligible=True,
        family="training_bundle",
        dry_run=False,
        confirm_token="ACTIVATE_TRAINING_RESULT",
        reason="auto",
        source_role="system",
    )

    assert result["activation_family"] == "training_bundle"
    assert result["blocking_gate"] == "all_training_bundle_writers_blocked"
    assert result["domain_result"]["version"] == "v20.training_bundle_activation_result.v1"
    assert result["domain_result"]["writer_count"] == 8
    assert len(calls) == 8


def test_v20_admin_portrait_training_activation_uses_optimizer_writer(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    result = _domain_activation_result(
        task={"task_key": "rule_portrait_batch"},
        eligible=True,
        family="portrait_policy",
        dry_run=False,
        confirm_token="ACTIVATE_TRAINING_RESULT",
        reason="test",
        source_role="admin",
    )

    assert result["status"] == "blocked_by_machine_gate"
    assert result["activation_family"] == "portrait_policy"
    assert result["blocking_gate"] == "blocked_by_machine_gate"
    assert result["domain_result"]["version"] == "v20.portrait_runtime_pointer_activation_result.v1"
    assert result["runtime_mutation"] is False


def test_v20_admin_knowledge_training_activation_uses_optimizer_writer(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    result = _domain_activation_result(
        task={"task_key": "knowledge_rule_review_overlay"},
        eligible=True,
        family="knowledge_review",
        dry_run=False,
        confirm_token="ACTIVATE_TRAINING_RESULT",
        reason="test",
        source_role="admin",
    )

    assert result["status"] == "blocked_by_machine_gate"
    assert result["activation_family"] == "knowledge_review"
    assert result["blocking_gate"] == "blocked_by_machine_gate"
    assert result["domain_result"]["version"] == "v20.knowledge_runtime_pointer_activation_result.v1"
    assert result["runtime_mutation"] is False


def test_v20_admin_question_training_activation_uses_optimizer_writer(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    result = _domain_activation_result(
        task={"task_key": "question_source_training"},
        eligible=True,
        family="question_policy",
        dry_run=False,
        confirm_token="ACTIVATE_TRAINING_RESULT",
        reason="test",
        source_role="admin",
    )

    assert result["status"] == "blocked_by_machine_gate"
    assert result["activation_family"] == "question_policy"
    assert result["blocking_gate"] == "blocked_by_machine_gate"
    assert result["domain_result"]["version"] == "v20.question_runtime_pointer_activation_result.v1"
    assert result["runtime_mutation"] is False


def test_v20_admin_corpus_training_activation_uses_optimizer_writer(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    result = _domain_activation_result(
        task={"task_key": "full_precompute_preview"},
        eligible=True,
        family="corpus_precompute",
        dry_run=False,
        confirm_token="ACTIVATE_TRAINING_RESULT",
        reason="test",
        source_role="admin",
    )

    assert result["status"] == "blocked_by_machine_gate"
    assert result["activation_family"] == "corpus_precompute"
    assert result["blocking_gate"] == "blocked_by_machine_gate"
    assert result["domain_result"]["version"] == "v20.corpus_runtime_pointer_activation_result.v1"
    assert result["runtime_mutation"] is False


def test_v20_admin_supported_training_can_auto_apply_parameters(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("V20_RUNTIME_DIR", str(tmp_path))
    task = {
        "task_id": "training_iteration_fast.test",
        "task_key": "training_iteration_fast",
        "status": "succeeded",
        "runtime_mutation": True,
        "log_tail": ['{"version":"test","status":"ready","candidate_policy":{"x":1}}'],
        "guardrails": [],
    }
    preview = task | {"result_summary": task.get("result_summary", {})}
    # Write a task state so the apply path can read the same contract as the worker.
    from pathlib import Path
    from v20.storage.local_jsonl import local_jsonl_store_from_env
    import json

    task_dir = local_jsonl_store_from_env().runtime_dir / "training" / "tasks"
    task_dir.mkdir(parents=True, exist_ok=True)
    path = task_dir / "training_iteration_fast.test.json"
    path.write_text(json.dumps(task), encoding="utf-8")
    (task_dir / "latest.json").write_text(json.dumps(task), encoding="utf-8")

    latest = read_training_task("training_iteration_fast.test")
    auto = latest["result_summary"]["publish_preview"]["auto_optimization"]
    assert auto["parameter_apply_supported"] is True
    assert auto["auto_apply_candidate"] is True

    applied = prepare_training_task_activation(
        "training_iteration_fast.test",
        dry_run=False,
        confirm_token="ACTIVATE_TRAINING_RESULT",
        reason="test",
    )
    assert applied["activation_plan"]["requested_apply"] is True
    assert applied["activation_plan"]["eligible_for_publish"] is True
