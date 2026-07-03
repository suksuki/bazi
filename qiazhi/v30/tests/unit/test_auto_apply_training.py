from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from v30.config import V30Settings
from v30.learning import run_auto_apply_training
from v30.learning.auto_apply import _candidate_payload
from v30.policy import RuntimePointerStore
from v30.runtime import create_smoke_runtime
from v30.validation import extract_training_signals, run_synthetic_tier


def _settings(tmp_path: Path) -> V30Settings:
    return V30Settings(
        database_url=None,
        redis_url=None,
        redis_prefix="v30",
        runtime_dir=tmp_path / ".runtime",
        host="127.0.0.1",
        port=9030,
        env="test",
        repository="memory",
    )


def test_auto_apply_training_updates_core_policy_pointers(tmp_path: Path) -> None:
    store = RuntimePointerStore(_settings(tmp_path))
    result = run_auto_apply_training(
        training_run_id="unit-auto",
        store=store,
        promotion_validation_mode="smoke",
    )
    structure_artifact = store.load_active_artifact("structure_policy")
    question_artifact = store.load_active_artifact("question_policy")
    rule_artifact = store.load_active_artifact("rule_policy")
    assert result.status == "applied"
    assert result.metrics["promoted_count"] == 4
    assert result.policy_application["mode"] == "validated_auto_apply"
    assert result.policy_application["policy_pointer_write_performed"] is True
    assert result.policy_application["promoted_family_count"] == 4
    assert result.policy_application["rollback_available"] is True
    assert result.policy_application["chart_fact_mutation_allowed"] is False
    assert result.training_signal_summary["brain_judge_quality_present"] is True
    assert result.training_signal_summary["synthesis_blueprint_quality_present"] is True
    assert result.training_signal_summary["can_tune_chart_facts"] is False
    assert result.training_signal_summary["signal_count"] == result.metrics["training_signal_count"]
    quality_metrics = result.training_signal_summary["quality_metrics"]
    assert quality_metrics["version"] == "v30.training_quality_metrics.v1"
    assert quality_metrics["final_synthesis_quality_score"] > 0
    assert quality_metrics["advice_actionability"] > 0
    assert quality_metrics["decision_focus_coverage"] > 0
    assert quality_metrics["quality_metric_count"] >= 8
    assert quality_metrics["chart_fact_mutation_allowed"] is False
    assert result.active_policy_versions["structure_policy"] == "structure_policy.unit-auto.structure_policy"
    assert result.active_policy_versions["mainline_policy"] == "mainline_policy.unit-auto.mainline_policy"
    assert result.active_policy_versions["question_policy"] == "question_policy.unit-auto.question_policy"
    assert result.active_policy_versions["rule_policy"] == "rule_policy.unit-auto.rule_policy"
    assert structure_artifact.payload["weights"]["mechanism.hidden_factor_dialogue_probe"] == 1.05
    assert structure_artifact.payload["weights"]["mechanism.useful_god_candidate_gate"] > 1.0
    assert structure_artifact.payload["weights"]["mechanism.branch_relation_dynamic_review"] > 1.0
    assert structure_artifact.payload["weights"]["dynamic_graph.v2"] > 1.0
    assert structure_artifact.payload["weights"]["dynamic_graph.competition_suppression"] > 1.0
    assert structure_artifact.payload["weights"]["dynamic_graph.conflict_family"] > 1.0
    assert structure_artifact.payload["weights"]["dynamic_graph.path_resolution"] > 1.0
    assert structure_artifact.payload["weights"]["dynamic_graph.domain_path"] > 1.0
    assert structure_artifact.payload["weights"]["dynamic_graph.domain_rule_depth"] > 1.0
    assert structure_artifact.payload["weights"]["dynamic_graph.useful_god_candidate_path"] > 1.0
    assert structure_artifact.payload["weights"]["dynamic_graph.tongguan_zhihua"] > 1.0
    assert structure_artifact.payload["weights"]["dynamic_graph.model_signal_fusion"] > 1.0
    assert structure_artifact.payload["weights"]["model_signal.family_coverage"] > 1.0
    assert structure_artifact.payload["weights"]["model_signal.energy_band_calibration"] > 1.0
    assert structure_artifact.payload["weights"]["model_signal.stability_review"] > 1.0
    assert structure_artifact.payload["weights"]["model_signal.volatility_review"] > 1.0
    assert structure_artifact.payload["weights"]["ranked_decision.follow_structure_boundary"] > 1.0
    assert structure_artifact.payload["weights"]["ranked_decision.disputed_structure"] > 1.0
    assert structure_artifact.payload["weights"]["ranked_decision.useful_god_evidence"] > 1.0
    assert any(
        signal["signal_id"] == "v30.training_signal.structure_dynamic_competition"
        for signal in structure_artifact.payload["training_signals"]
    )
    assert any(
        signal["signal_id"] == "v30.training_signal.m5_weight_replay"
        for signal in structure_artifact.payload["training_signals"]
    )
    assert question_artifact.payload["weights"]["topic_weights"]["time_context"] >= 1.03
    assert question_artifact.payload["weights"]["topic_weights"]["hidden_factor"] > 1.01
    assert question_artifact.payload["weights"]["intent_weights"]["confirm_missing_time_context"] >= 1.02
    assert question_artifact.payload["weights"]["intent_weights"]["discover_hidden_factor_amplifier"] > 1.01
    hidden_event_policy = question_artifact.payload["weights"]["hidden_factor_event_policy"]
    adaptive_policy = question_artifact.payload["weights"]["adaptive_question_policy"]
    interaction_policy = question_artifact.payload["weights"]["interaction_followup_policy"]
    model_signal_question_policy = question_artifact.payload["weights"]["model_signal_question_policy"]
    central_brain_synthesis_policy = question_artifact.payload["weights"]["central_brain_synthesis_policy"]
    assert adaptive_policy["mode"] == "trace_replay_weight_candidate_not_chart_fact"
    assert adaptive_policy["boundary"] == "adaptive_question_policy_weights_replay_diagnostics_not_chart_facts"
    assert adaptive_policy["alignment_coverage"] > 0
    assert adaptive_policy["topic_weights"]["time_context"] > 1.0
    assert adaptive_policy["stage_weights"]["context_completion"] > 1.0
    assert question_artifact.payload["weights"]["topic_weights"]["time_context"] >= adaptive_policy["topic_weights"]["time_context"]
    assert interaction_policy["mode"] == "visible_followup_policy_candidate_not_chart_fact"
    assert interaction_policy["visible_next_question_weight"] > 1.0
    assert interaction_policy["internal_diagnostic_weight"] > 1.0
    assert interaction_policy["boundary"] == "interaction_followup_policy_trains_question_strategy_not_chart_facts"
    assert model_signal_question_policy["mode"] == "model_signal_focus_weight_candidate_not_chart_fact"
    assert model_signal_question_policy["source_signal_id"] == "v30.training_signal.question_model_signal_personalization"
    assert model_signal_question_policy["topic_weights"]["wealth"] > 1.0
    assert model_signal_question_policy["topic_weights"]["career"] > 1.0
    assert model_signal_question_policy["can_tune_question_strategy"] is True
    assert model_signal_question_policy["can_tune_chart_facts"] is False
    assert model_signal_question_policy["boundary"] == "model_signal_question_policy_trains_question_strategy_not_chart_facts"
    assert central_brain_synthesis_policy["mode"] == "judge_quality_weight_candidate_not_chart_fact"
    assert central_brain_synthesis_policy["source_signal_id"] == "v30.training_signal.central_brain_judge_quality"
    assert "v30.training_signal.central_brain_synthesis_blueprint_quality" in central_brain_synthesis_policy["source_signal_ids"]
    assert central_brain_synthesis_policy["weights"]["final_synthesis_quality"] > 1.0
    assert central_brain_synthesis_policy["weights"]["conclusion_strength"] > 1.0
    assert central_brain_synthesis_policy["weights"]["advice_actionability"] > 1.0
    assert central_brain_synthesis_policy["weights"]["risk_boundary_clarity"] > 1.0
    assert central_brain_synthesis_policy["blueprint_quality"]["decision_focus_coverage"] >= 0.9
    assert central_brain_synthesis_policy["blueprint_quality"]["action_step_coverage"] >= 0.9
    assert central_brain_synthesis_policy["can_tune_final_synthesis_quality"] is True
    assert central_brain_synthesis_policy["can_tune_synthesis_blueprint"] is True
    assert central_brain_synthesis_policy["can_tune_question_strategy"] is True
    assert central_brain_synthesis_policy["can_tune_chart_facts"] is False
    assert "chart_facts" in central_brain_synthesis_policy["blocked_training_routes"]
    assert central_brain_synthesis_policy["boundary"] == "central_brain_synthesis_policy_trains_quality_and_dialogue_strategy_not_chart_facts"
    assert hidden_event_policy["mode"] == "feedback_conditioned_not_chart_fact"
    assert hidden_event_policy["candidate_alignment_multiplier"] > 1.0
    assert hidden_event_policy["time_layer_alignment_multiplier"] > 1.0
    assert hidden_event_policy["conflict_multiplier"] < 1.0
    assert hidden_event_policy["denial_multiplier"] < hidden_event_policy["conflict_multiplier"]
    assert question_artifact.payload["weights"]["krp_unit_weights"]["time_context"] > 1.02
    assert question_artifact.payload["weights"]["krp_unit_weights"]["wealth"] > 1.0
    assert question_artifact.payload["weights"]["krp_unit_weights"]["career"] > 1.0
    assert question_artifact.payload["weights"]["krp_unit_weights"]["relationship"] > 1.0
    assert question_artifact.payload["weights"]["krp_unit_weights"]["health"] > 1.0
    assert question_artifact.payload["training_signals"]
    assert any(
        signal["signal_id"] == "v30.training_signal.question_dialogue_outcome"
        for signal in question_artifact.payload["training_signals"]
    )
    assert any(
        signal["signal_id"] == "v30.training_signal.adaptive_question_replay"
        for signal in question_artifact.payload["training_signals"]
    )
    assert any(
        signal["signal_id"] == "v30.training_signal.question_model_signal_personalization"
        for signal in question_artifact.payload["training_signals"]
    )
    assert any(
        signal["signal_id"] == "v30.training_signal.central_brain_judge_quality"
        for signal in question_artifact.payload["training_signals"]
    )
    assert any(
        signal["signal_id"] == "v30.training_signal.central_brain_synthesis_blueprint_quality"
        for signal in question_artifact.payload["training_signals"]
    )
    comparison = question_artifact.validation_summary["question_policy_comparison"]
    assert comparison["version"] == "v30.question_policy_comparison.v1"
    assert comparison["candidate_id"] == "unit-auto.question_policy"
    assert comparison["artifact_uri"]
    assert question_artifact.metrics["question_policy_comparison_weighted_delta_count"] > 0
    assert result.metrics["training_signal_count"] >= 3
    family_rows = {row["family"]: row for row in result.policy_application["families"]}
    assert family_rows["question_policy"]["active_artifact_id"] == "question_policy.unit-auto.question_policy"
    assert family_rows["question_policy"]["rollback_target_artifact_id"]
    assert family_rows["question_policy"]["promoted"] is True
    assert rule_artifact.payload["weights"]["rule_weights"]["v30.rule.hidden_factor.requires_dialogue"] >= 1.03
    assert rule_artifact.payload["weights"]["hidden_factor_event_policy"]["boundary"] == "hidden_factor_policy_weights_feedback_conditioned_not_chart_fact"
    assert question_artifact.payload["weights"]["latent_bazi_attribute_policy"]["reverse_inference_weight"] == 1.0
    assert rule_artifact.payload["weights"]["latent_bazi_attribute_policy"]["reverse_inference_weight"] == 1.0
    assert rule_artifact.payload["weights"]["per_unit_parameter_policy"]["boundary"] == "per_unit_weights_tune_runtime_candidates_not_chart_facts"
    assert rule_artifact.payload["weights"]["rule_weights"]["v30.rule.useful_god.candidate_gate"] > 1.02
    assert rule_artifact.payload["weights"]["domain_weights"]["structure_dynamic"] > 1.0


def test_latent_bazi_attribute_signal_builds_candidate_policy() -> None:
    signals = extract_training_signals(run_synthetic_tier("latent_bazi_divergence"))
    question_payload = _candidate_payload("question_policy", "unit-latent", signals)
    rule_payload = _candidate_payload("rule_policy", "unit-latent", signals)

    latent_policy = question_payload["weights"]["latent_bazi_attribute_policy"]
    rule_latent_policy = rule_payload["weights"]["latent_bazi_attribute_policy"]
    assert latent_policy["mode"] == "latent_personalization_candidate_not_chart_fact"
    assert latent_policy["source_signal_id"] == "v30.training_signal.latent_bazi_attribute_alignment"
    assert latent_policy["reverse_inference_weight"] > 1.0
    assert latent_policy["question_need_weight"] > 1.0
    assert latent_policy["individualized_projection_weight"] > 1.0
    assert {"career_bias", "wealth_bias", "relationship_bias"} <= set(latent_policy["domain_bias_weights"])
    assert {"authority", "resource", "wealth"} <= set(latent_policy["ten_god_modifier_weights"])
    assert {"resource_index", "risk_index", "stability_index"} <= set(latent_policy["global_attribute_weights"])
    assert latent_policy["blocked_training_routes"] == ["calendar_conversion", "chart_facts", "flow_timing", "luck_cycle"]
    assert latent_policy["can_tune_latent_inference"] is True
    assert latent_policy["can_tune_question_strategy"] is True
    assert latent_policy["can_tune_individualized_projection"] is True
    assert latent_policy["can_tune_chart_facts"] is False
    assert latent_policy["boundary"] == "latent_bazi_attribute_policy_trains_personalization_not_chart_facts"
    assert rule_latent_policy == latent_policy
    assert any(
        signal["signal_id"] == "v30.training_signal.latent_bazi_attribute_alignment"
        for signal in question_payload["training_signals"]
    )


def test_runtime_consumes_latent_bazi_attribute_question_policy() -> None:
    signals = extract_training_signals(run_synthetic_tier("latent_bazi_divergence"))
    question_payload = _candidate_payload("question_policy", "unit-latent-runtime", signals)
    runtime = create_smoke_runtime(
        "latent-policy-runtime",
        policy_payload_overrides={"question_policy": question_payload},
        active_policy_version_overrides={"question_policy": "question_policy.unit-latent-runtime"},
    )

    hidden_row = next(
        row for row in runtime.question_plan.recommended_questions
        if row["question_id"] == "q_v30_hidden_factor_boundary_discovery"
    )
    assert "latent_bazi_attribute_policy:personalization_not_chart_fact" in hidden_row["reasons"]
    assert any(
        str(reason).startswith("latent_bazi_attribute_policy:question_need:")
        for reason in hidden_row["reasons"]
    )


def test_runtime_reports_auto_applied_policy_versions(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("V30_RUNTIME_DIR", str(tmp_path / ".runtime"))
    monkeypatch.setenv("V30_ENV", "test")
    run_auto_apply_training(training_run_id="runtime-auto", promotion_validation_mode="smoke")
    runtime = create_smoke_runtime("runtime-auto-reading")
    versions = runtime.question_plan.policy_effect["active_policy_versions"]
    assert versions["structure_policy"] == "structure_policy.runtime-auto.structure_policy"
    assert versions["mainline_policy"] == "mainline_policy.runtime-auto.mainline_policy"
    assert versions["question_policy"] == "question_policy.runtime-auto.question_policy"
    assert versions["rule_policy"] == "rule_policy.runtime-auto.rule_policy"
    assert runtime.structure_state.path_scores["structure_policy_weighted"] == 1.0
    assert runtime.structure_state.path_scores["structure_policy_model_signal_fusion"] > 1.0
    assert runtime.question_plan.policy_effect["structure_policy_payload"]["weights"]
    assert runtime.question_plan.policy_effect["question_policy_payload"]["weights"]
    assert runtime.question_plan.policy_effect["rule_policy_payload"]["weights"]
    assert runtime.question_plan.policy_effect["structure_policy_payload"]["weights"]["mechanism.useful_god_candidate_gate"] > 1.0
    assert runtime.question_plan.policy_effect["rule_policy_payload"]["weights"]["per_unit_parameter_policy"]["unit_count"] >= 42
    assert any(
        "rule_policy_weight:" in support
        for row in runtime.feature_evidence
        if row.domain == "rule"
        for support in row.supports
    )
    assert any(
        float(row.get("score", 0.0)) > 0.0
        for row in runtime.structure_state.graph_nodes
        if row.get("kind") == "mechanism_path" and row.get("node_id") == "mechanism.useful_god_candidate_gate"
    )
    assert runtime.question_plan.recommended_questions[0]["policy_weight"] > 1.0
    final_synthesis = runtime.question_plan.policy_effect["central_reading_state"]["final_synthesis"]
    assert final_synthesis["synthesis_policy_effect"]["applied"] is True
    assert final_synthesis["synthesis_policy_effect"]["source_signal_id"] == "v30.training_signal.central_brain_judge_quality"
    assert final_synthesis["quality_contract"]["synthesis_policy_applied"] is True
    assert final_synthesis["quality_contract"]["chart_fact_mutation_allowed"] is False


def test_auto_apply_training_reports_progress_events(tmp_path: Path) -> None:
    store = RuntimePointerStore(_settings(tmp_path))
    events: list[dict[str, object]] = []

    result = run_auto_apply_training(
        training_run_id="unit-auto-progress",
        store=store,
        promotion_validation_mode="smoke",
        progress_callback=events.append,
    )

    steps = [event["step"] for event in events]
    assert result.status == "applied"
    assert events[0]["step"] == "started"
    assert "synthetic_signal_source_ready" in steps
    assert "training_signals_extracted" in steps
    assert "candidates_generated" in steps
    assert "promoted_question_policy" in steps
    assert events[-1]["step"] == "completed"
    assert events[-1]["progress_percent"] == 100


def test_auto_training_script_applies_without_review_gate(tmp_path: Path) -> None:
    env = {
        **os.environ,
        "V30_RUNTIME_DIR": str(tmp_path / ".runtime"),
        "V30_ENV": "test",
    }
    result = subprocess.run(
        [
            sys.executable,
            "scripts/run_auto_training.py",
            "--training-run-id",
            "script-auto",
            "--promotion-validation-mode",
            "smoke",
        ],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    pointer_path = tmp_path / ".runtime" / "policies" / "question_policy" / "active.json"
    assert result.returncode == 0
    assert "script-auto: applied (4/4 promoted)" in result.stdout
    assert pointer_path.exists()
    assert "question_policy.script-auto.question_policy" in pointer_path.read_text(encoding="utf-8")


def test_admin_training_ui_states_validated_auto_apply() -> None:
    html = Path("admin_frontend/app.js").read_text(encoding="utf-8")

    assert "推荐训练与验证" in html
    assert "启动计划" in html
    assert "高级训练工具" in html
    assert "策略训练并自动生效" in html
    assert "/api/v30/admin/training/auto-apply/run" in html
    assert "/api/v30/admin/training/auto-apply/status" in html
    assert "/api/v30/admin/training/auto-apply/history" in html
    assert "/api/v30/admin/policies/lineage/summary" in html
    assert "/api/v30/admin/policies/rollback" in html
    assert "/api/v30/admin/training/orchestrator/plans" in html
    assert "/api/v30/admin/training/orchestrator/run" in html
    assert "/api/v30/admin/training/orchestrator/status" in html
    assert "/api/v30/admin/training/orchestrator/history" in html
    assert "/api/v30/admin/training/orchestrator/diff" in html
    assert "/api/v30/admin/training/orchestrator/rerun-failed" in html
    assert "/api/v30/admin/training/brain-examples/summary" in html
    assert "admin/training/brain-examples/distribution-gate" in Path("v30/api/app.py").read_text(encoding="utf-8")
    assert "中枢训练样本" in html
    assert "Synthetic Replay Gate" in html
    assert "renderTrainingOrchestratorJob" in html
    assert "renderTrainingOrchestratorHistory" in html
    assert "renderTrainingOrchestratorDiff" in html
    assert "/api/v30/admin/training/dialogue-heavy-validation-decision" not in html
    assert "/api/v30/admin/training/dialogue-calibration-loop" not in html
    assert "智能质量对比" in html
    assert "重跑失败步骤" in html
    assert "m3_518k_validation" in html
    assert "central_brain_phase2_training" in html
    assert "include_readiness_matrix" in html
    assert "renderAutoTrainingHistory" in html
    assert "renderPolicyLineageSummary" in html
    assert "训练任务已启动；验证通过后会自动生效，页面会刷新进度。" in html
    assert "renderAutoTrainingJobProgress" in html
    assert "renderAutoApplyTrainingRun" in html
    assert "未自动发布策略" not in html
