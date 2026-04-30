from __future__ import annotations

import json
from pathlib import Path

from v19.lab_interfaces import _default_validation_cases, _run_case, guided_question_diversity_audit
from v19.synthetic_validation import P10_GUIDED_SYNTHETIC_CASES, P11_GUIDED_SYNTHETIC_CASES, run_guided_synthetic_collision
from v19.synthetic_validation.guided_runner import _agent_data_for_case


def test_p10_guided_synthetic_collision_cases_pass() -> None:
    result = run_guided_synthetic_collision(P10_GUIDED_SYNTHETIC_CASES)

    assert result["status"] == "pass"
    assert result["summary"]["total"] >= 12
    assert result["summary"]["failed"] == 0
    assert "SYNTHETIC_CASES_ONLY" in result["boundaries"]
    assert "ANALYST_REVIEW_REQUIRED_FOR_ACTIVATION" in result["boundaries"]
    assert len(result["collision_review"]["stable_structures"]) == result["summary"]["total"]
    for item in result["cases"]:
        assert item["structure_label"]
        assert "q_income_stability" in item["observed"]["wealth_question_keys"]
        assert item["baseline_vs_kb_augmented"]["evidence_delta"]["mutation_check"] == "routing_stable"

    expected_knowledge_cases = [case for case in P10_GUIDED_SYNTHETIC_CASES if case.expected_knowledge_ids]
    assert expected_knowledge_cases
    by_case = {item["case_id"]: item for item in result["cases"]}
    for case in expected_knowledge_cases:
        delta = by_case[case.case_id]["baseline_vs_kb_augmented"]["evidence_delta"]["added_knowledge_ids"]
        for knowledge_id in case.expected_knowledge_ids:
            assert knowledge_id in delta


def test_guided_synthetic_collision_reports_evolution_candidates_on_failure() -> None:
    broken = P10_GUIDED_SYNTHETIC_CASES[0].to_dict()
    broken["case_id"] = "syn.guided.expected_collision_failure"
    broken["expected_knowledge_ids"] = ["p10.nonexistent_knowledge"]

    result = run_guided_synthetic_collision([broken])

    assert result["status"] == "fail"
    assert result["evolution_report"]["proposal_count"] == 1
    assert result["evolution_report"]["audit_count"] == 1
    assert result["evolution_report"]["audit_records"][0]["review_status"] == "analyst_review_required"
    assert result["evolution_report"]["audit_records"][0]["attribution_layer"] == "knowledge"
    assert result["evolution_report"]["draft_suggestions"][0]["target"] == "knowledge_seed_draft"
    assert result["evolution_report"]["draft_suggestions"][0]["draft_type"] == "knowledge_seed"
    assert result["evolution_report"]["items"][0]["proposal_scope"] == "draft_only_requires_analyst_review"


def test_p11_guided_synthetic_expansion_cases_pass() -> None:
    result = run_guided_synthetic_collision(P11_GUIDED_SYNTHETIC_CASES)

    assert result["status"] == "pass"
    assert result["summary"]["total"] >= 20
    assert result["summary"]["failed"] == 0
    assert result["evolution_report"]["audit_count"] == 0
    required_focus = {
        "branch_clash_harm_collision",
        "branch_combination_break_collision",
        "three_harmony_three_meeting_layered_collision",
        "ten_god_visible_hidden_conflict",
        "income_wealth_visible_clashed",
        "income_wealth_visible_bound",
        "time_trigger_relation_no_natal_mutation",
    }
    assert required_focus <= {case.collision_focus for case in P11_GUIDED_SYNTHETIC_CASES}
    for item in result["cases"]:
        assert item["structure_label"]
        assert item["observed"]["standardized_knowledge_tags"]
        assert "q_income_stability" in item["observed"]["wealth_question_keys"]
        assert item["baseline_vs_kb_augmented"]["evidence_delta"]["mutation_check"] == "routing_stable"


def test_p53_legacy_p10_p11_cases_backfill_to_new_rule_graph_framework() -> None:
    from v19.synthetic_validation.framework_backfill import build_legacy_framework_adaptation_matrix

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    result = run_guided_synthetic_collision(P11_GUIDED_SYNTHETIC_CASES)
    matrix = build_legacy_framework_adaptation_matrix()
    by_case = {row["case_id"]: row for row in result["cases"]}
    review = result["framework_backfill_review"]

    assert result["status"] == "pass"
    assert review["status"] == "pass"
    assert review["case_count"] == len(P11_GUIDED_SYNTHETIC_CASES)
    assert review["failed"] == 0
    assert set(review["legacy_phases"]) == {"p10_synthetic_collision_review", "p11_synthetic_expansion"}
    assert {"core_strength_foundation", "branch_time_activation", "ten_god_mechanism", "wealth_career_bridge"} <= set(review["expected_topic_lanes_covered"])
    assert {"stem", "branch", "hidden_stem", "branch_relation", "time_relation", "ten_god"} <= set(review["expected_graph_features_covered"])
    assert "P53_LEGACY_SYNTHETIC_FRAMEWORK_BACKFILL" in result["boundaries"]
    assert matrix["status"] == "pass"
    assert matrix["summary"]["row_count"] >= 7
    assert {row["phase"] for row in matrix["rows"]} >= {"P10", "P11", "P28-P30", "P39-P45", "P46-P52"}
    assert all(row["status"] == "pass" for row in matrix["rows"])

    month = by_case["syn.guided.month_command_boundary"]["framework_backfill"]
    branch = by_case["syn.guided.branch_penalty_harm_break"]["framework_backfill"]
    income = by_case["syn.guided.income_structure_no_internal_terms"]["framework_backfill"]
    time_case = by_case["syn.guided.p11.time_trigger_relation_no_natal_mutation"]["framework_backfill"]

    assert month["expected"]["primary_intent"] == "metadata_boundary"
    assert month["actual"]["route_intents"]["primary_question_route"] == "metadata_boundary"
    assert "core_strength_foundation" in month["expected"]["expected_topic_lanes"]
    assert branch["expected"]["condition_axis_projection"]["same_layer_action"] == "branch_relation_feature"
    assert "branch_time_activation" in branch["expected"]["expected_topic_lanes"]
    assert {"wealth_career_bridge", "ten_god_mechanism"} <= set(income["expected"]["expected_topic_lanes"])
    assert time_case["expected"]["condition_axis_projection"]["time_layer"] == "time_relation_feature"
    assert "time_relation" in time_case["actual"]["graph_features"]

    for item in result["cases"]:
        backfill = item["framework_backfill"]
        assert backfill["status"] == "pass"
        assert backfill["actual"]["runtime_status"] == "rule_graph_runtime_context_ready"
        assert backfill["actual"]["answer_audit_status"] == "pass"
        assert backfill["actual"]["selected_path_count"] == backfill["actual"]["selected_by_route_count"]
        assert {"source_layer", "answer_boundary"} <= set(backfill["actual"]["condition_axes_available"])
        assert backfill["expected"]["mutation_policy"]["answer_mutation_count"] == 0

    assert "docs/v19/V19_P53_LEGACY_SYNTHETIC_FRAMEWORK_BACKFILL.md" in manifest["created_from"]
    assert manifest["p53_legacy_synthetic_framework_backfill"]["case_count"] >= 20
    assert manifest["p53_legacy_synthetic_framework_backfill"]["legacy_phases"] == [
        "p10_synthetic_collision_review",
        "p11_synthetic_expansion",
    ]
    assert manifest["p53_legacy_synthetic_framework_backfill"]["adaptation_matrix"]["status"] == "pass"
    assert "P53_LEGACY_SYNTHETIC_FRAMEWORK_BACKFILL" in manifest["guardrails"]


def test_p54_framework_chain_audit_covers_legacy_and_native_tracks() -> None:
    from v19.synthetic_validation import run_p54_framework_chain_audit

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    audit = run_p54_framework_chain_audit()
    by_section = {row["section"]: row for row in audit["rows"]}

    assert audit["status"] == "pass"
    assert audit["summary"]["row_count"] >= 6
    assert audit["summary"]["failed"] == 0
    assert audit["summary"]["engine_enabled_count"] == 0
    assert audit["summary"]["answer_mutation_count"] == 0
    assert audit["summary"]["runtime_mutation"] is False
    assert set(by_section) >= {
        "p10_p11_guided_synthetic",
        "p28_p30_ten_god_mechanisms",
        "p39_rule_conversion",
        "p42_p43_smart_gate_shadow",
        "p45_canary_runtime_trial",
        "p46_p52_rule_graph_runtime",
    }
    assert by_section["p10_p11_guided_synthetic"]["metrics"]["framework_backfill_status"] == "pass"
    assert by_section["p28_p30_ten_god_mechanisms"]["metrics"]["rule_backfill_needed_count"] >= 0
    assert by_section["p28_p30_ten_god_mechanisms"]["metrics"]["adaptation_status"].startswith("framework_compatible")
    assert by_section["p42_p43_smart_gate_shadow"]["metrics"]["shadow_scored_count"] == 158
    assert by_section["p45_canary_runtime_trial"]["metrics"]["production_engine_enabled_count"] == 0
    assert "docs/v19/V19_P54_FRAMEWORK_CHAIN_AUDIT.md" in manifest["created_from"]
    assert manifest["p54_framework_chain_audit"]["status"] == "pass"
    assert manifest["p54_framework_chain_audit"]["engine_enabled_count"] == 0
    assert "P54_FRAMEWORK_CHAIN_AUDIT" in manifest["guardrails"]


def test_p59_silent_evolution_cycle_scores_and_generates_tuning_proposals() -> None:
    from v19.synthetic_validation import run_p59_silent_evolution_cycle

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    server = (root / "v19/server.py").read_text(encoding="utf-8")
    cycle = run_p59_silent_evolution_cycle()

    assert cycle["status"] == "silent_shadow_pass"
    assert cycle["scorecard"]["status"] == "pass"
    assert cycle["scorecard"]["score"] >= 90
    assert cycle["scorecard"]["score_tier"] in {"A", "B"}
    assert cycle["run_ledger_entry"]["engine_enabled"] is False
    assert cycle["run_ledger_entry"]["answer_mutation"] is False
    assert cycle["run_ledger_entry"]["runtime_mutation"] is False
    assert cycle["run_ledger_entry"]["rollback_ready"] is True
    assert cycle["model_policy"]["active_model"] == "deterministic_rule_graph_plus_eval_scoring"
    assert "gnn" in cycle["model_policy"]["reserved_models"]
    assert "rl" in cycle["model_policy"]["reserved_models"]
    assert "black_box_core_inference" in cycle["model_policy"]["blocked_uses"]
    assert {row["proposal_type"] for row in cycle["tuning_proposals"]} >= {
        "eval_dataset_expansion",
        "question_routing_parameter_review",
        "model_policy",
        "shadow_sample_expansion",
    }
    assert all(row["decision"] == "silent_proposal_only" for row in cycle["tuning_proposals"])
    assert all(row["runtime_mutation"] is False for row in cycle["tuning_proposals"])
    assert "docs/v19/V19_P59_SILENT_EVOLUTION_SYSTEM.md" in manifest["created_from"]
    assert manifest["p59_silent_evolution_system"]["active_model"] == "deterministic_rule_graph_plus_eval_scoring"
    assert manifest["p59_silent_evolution_system"]["runtime_mutation"] is False
    assert "P59_SILENT_EVOLUTION_SYSTEM" in manifest["guardrails"]
    assert "/api/lab/framework-chain-audit" in server
    assert "/api/lab/silent-evolution/run" in server


def test_p60_domain_route_eval_and_smart_approval_gate_are_silent() -> None:
    from v19.rule_graph_orchestrator import infer_question_intent
    from v19.synthetic_validation import run_p60_domain_route_eval, run_p60_silent_evolution_extension, run_p60_smart_approval_gate

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    server = (root / "v19/server.py").read_text(encoding="utf-8")
    domain_eval = run_p60_domain_route_eval()
    gate = run_p60_smart_approval_gate()
    extension = run_p60_silent_evolution_extension()

    assert infer_question_intent("", "我的感情关系结构怎么看？", "")["intent"] == "relationship_structure"
    assert infer_question_intent("", "我的健康结构有什么需要注意的边界？", "")["intent"] == "health_structure"
    assert domain_eval["status"] == "pass"
    assert domain_eval["summary"]["domain_count"] == 4
    assert domain_eval["summary"]["sample_count"] == 8
    assert domain_eval["summary"]["failed"] == 0
    assert domain_eval["summary"]["direct_domain_hit_count"] == 8
    assert domain_eval["summary"]["bridge_without_direct_domain_count"] == 0
    assert {row["observed_intent"] for row in domain_eval["samples"]} >= {
        "income_structure",
        "career_structure",
        "relationship_structure",
        "health_structure",
    }
    assert all(row["engine_enabled_count"] == 0 for row in domain_eval["samples"])
    assert all(row["answer_mutation_count"] == 0 for row in domain_eval["samples"])
    assert domain_eval["domain_candidate_gaps"] == []

    assert gate["status"] == "smart_gate_ready_no_activation"
    assert gate["summary"]["auto_dry_run_allowed_count"] == 3
    assert gate["summary"]["shadow_dry_run_required_count"] >= 2
    assert gate["summary"]["engine_enabled_count"] == 0
    assert gate["summary"]["answer_mutation_count"] == 0
    assert gate["summary"]["runtime_mutation"] is False
    assert all(row.get("proposal_type") != "domain_rule_candidate_backfill" for row in gate["proposals"])
    assert all(row["runtime_mutation"] is False for row in gate["proposals"])

    assert extension["status"] == "pass"
    assert extension["summary"]["domain_sample_count"] == 8
    assert extension["summary"]["gate_proposal_count"] == gate["summary"]["proposal_count"]
    assert extension["summary"]["runtime_mutation"] is False
    assert "/api/lab/domain-route-eval" in server
    assert "/api/lab/smart-approval-gate/run" in server
    assert "/api/lab/silent-evolution-extension/run" in server
    assert "docs/v19/V19_P60_DOMAIN_ROUTE_AND_SMART_APPROVAL_GATE.md" in manifest["created_from"]
    assert manifest["p60_domain_route_and_smart_approval_gate"]["status"] == "pass"
    assert manifest["p60_domain_route_and_smart_approval_gate"]["runtime_mutation"] is False
    assert "P60_DOMAIN_ROUTE_AND_SMART_APPROVAL_GATE" in manifest["guardrails"]


def test_p61_relationship_health_domain_route_backfill_is_safe_and_selected() -> None:
    from v19.rule_graph_orchestrator import orchestrate_rule_graph_paths
    from v19.synthetic_validation import (
        build_p61_domain_route_backfill_candidates,
        build_p61_domain_route_backfill_eval_dataset,
        run_p60_domain_route_eval,
        run_p60_smart_approval_gate,
        run_p61_domain_route_backfill_regression,
    )

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    server = (root / "v19/server.py").read_text(encoding="utf-8")
    registry = build_p61_domain_route_backfill_candidates()
    dataset = build_p61_domain_route_backfill_eval_dataset()
    regression = run_p61_domain_route_backfill_regression()
    data = _agent_data_for_case(P11_GUIDED_SYNTHETIC_CASES[0])

    assert registry["summary"]["candidate_count"] == 6
    assert registry["summary"]["by_domain"] == {"health": 2, "relationship": 4}
    assert all(row["risk_level"] == "R2" for row in registry["candidates"])
    assert all(row["source_risk_level"] in {"R3", "R4"} for row in registry["candidates"])
    assert all(row["engine_enabled"] is False and row["activation_allowed"] is False for row in registry["candidates"])
    assert dataset["summary"]["sample_count"] == 24
    assert regression["status"] == "pass"
    assert regression["summary"]["runtime_mutation"] is False

    relationship = orchestrate_rule_graph_paths(data, message="我的感情关系结构怎么看？", limit=8)
    health = orchestrate_rule_graph_paths(data, message="我的健康结构有什么需要注意的边界？", limit=8)
    assert any(row["domain"] == "relationship" and row["topic_lane"] == "domain_safety_bridge" for row in relationship["selected_paths"])
    assert any(row["domain"] == "health" and row["topic_lane"] == "domain_safety_bridge" for row in health["selected_paths"])
    assert relationship["summary"]["candidate_count"] == 436
    assert health["summary"]["candidate_count"] == 436

    domain_eval = run_p60_domain_route_eval()
    gate = run_p60_smart_approval_gate()
    assert domain_eval["summary"]["direct_domain_hit_count"] == 8
    assert domain_eval["domain_candidate_gaps"] == []
    assert all(row.get("proposal_type") != "domain_rule_candidate_backfill" for row in gate["proposals"])

    assert "/api/lab/domain-route-backfill" in server
    assert "/api/lab/domain-route-backfill/run" in server
    assert "docs/v19/V19_P61_RELATIONSHIP_HEALTH_ROUTE_BACKFILL.md" in manifest["created_from"]
    assert manifest["p61_relationship_health_route_backfill"]["candidate_count"] == 6
    assert manifest["p61_relationship_health_route_backfill"]["runtime_mutation"] is False
    assert "P61_DOMAIN_ROUTE_BACKFILL" in manifest["guardrails"]


def test_p62_silent_training_ledger_collects_learning_signals_without_rule_updates() -> None:
    from v19.synthetic_validation import build_p62_silent_training_ledger, run_p62_silent_training_ledger_regression

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    server = (root / "v19/server.py").read_text(encoding="utf-8")
    ledger = build_p62_silent_training_ledger()
    regression = run_p62_silent_training_ledger_regression()

    assert ledger["status"] == "silent_training_ledger_ready"
    assert ledger["summary"]["entry_count"] == 3
    assert ledger["summary"]["failed"] == 0
    assert ledger["summary"]["runtime_mutation"] is False
    assert {row["source_stage"] for row in ledger["entries"]} == {
        "P59_SILENT_EVOLUTION_SYSTEM",
        "P60_DOMAIN_ROUTE_EVAL",
        "P61_DOMAIN_ROUTE_BACKFILL",
    }
    assert (ledger["source_summaries"]["p60"] or {})["direct_domain_hit_count"] == 8
    assert (ledger["source_summaries"]["p61_regression"] or {})["runtime_mutation"] is False
    assert "core_rule_truth_update" in ledger["learning_permissions"]["blocked"]
    assert "production_rule_activation" in ledger["learning_permissions"]["blocked"]
    assert all(row["runtime_mutation"] is False for row in ledger["tuning_queue"])

    assert regression["status"] == "pass"
    assert regression["summary"]["entry_count"] == 3
    assert regression["summary"]["runtime_mutation"] is False
    assert "/api/lab/silent-training-ledger" in server
    assert "/api/lab/silent-training-ledger/run" in server
    assert "docs/v19/V19_P62_SILENT_TRAINING_LEDGER.md" in manifest["created_from"]
    assert manifest["p62_silent_training_ledger"]["ledger_entry_count"] == 3
    assert manifest["p62_silent_training_ledger"]["runtime_mutation"] is False
    assert "P62_SILENT_TRAINING_LEDGER" in manifest["guardrails"]


def test_p63_silent_eval_queue_turns_training_ledger_into_checkpointed_jobs() -> None:
    from v19.synthetic_validation import build_p63_silent_eval_queue, run_p63_silent_eval_queue_regression

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    server = (root / "v19/server.py").read_text(encoding="utf-8")
    queue = build_p63_silent_eval_queue()
    regression = run_p63_silent_eval_queue_regression()

    assert queue["status"] == "silent_eval_queue_ready"
    assert queue["summary"]["queue_item_count"] == 4
    assert queue["summary"]["shadow_required_count"] == 1
    assert queue["summary"]["runtime_mutation"] is False
    assert {row["task_type"] for row in queue["queue_items"]} == {
        "route_weight_shadow_review",
        "recurring_route_wrapper_regression",
        "domain_gap_watch_closeout",
        "domain_safety_negative_sample_expansion",
    }
    assert {
        "v19.synthetic_validation.silent_evolution.run_p60_domain_route_eval",
        "v19.synthetic_validation.domain_route_backfill.run_p61_domain_route_backfill_regression",
    } <= {row["runner"] for row in queue["queue_items"]}
    assert all(row["runtime_mutation"] is False and row["answer_mutation"] is False for row in queue["queue_items"])
    assert all("production_rule_activation" in row["blocked_actions"] for row in queue["queue_items"])
    assert all(row["expected_invariants"] for row in queue["queue_items"])

    assert regression["status"] == "pass"
    assert regression["summary"]["queue_item_count"] == 4
    assert regression["summary"]["runtime_mutation"] is False
    assert "/api/lab/silent-eval-queue" in server
    assert "/api/lab/silent-eval-queue/run" in server
    assert "docs/v19/V19_P63_SILENT_EVAL_QUEUE.md" in manifest["created_from"]
    assert manifest["p63_silent_eval_queue"]["queue_item_count"] == 4
    assert manifest["p63_silent_eval_queue"]["runtime_mutation"] is False
    assert "P63_SILENT_EVAL_QUEUE" in manifest["guardrails"]


def test_p64_interactive_calibration_design_defines_safe_latent_factor_framework() -> None:
    from v19.synthetic_validation import build_p64_interactive_calibration_design, run_p64_interactive_calibration_design_regression

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    server = (root / "v19/server.py").read_text(encoding="utf-8")
    design = build_p64_interactive_calibration_design()
    regression = run_p64_interactive_calibration_design_regression()

    assert design["status"] == "interactive_calibration_design_ready_no_runtime_mutation"
    assert design["summary"]["latent_factor_count"] >= 12
    assert design["summary"]["inquiry_count"] >= 8
    assert design["summary"]["runtime_mutation"] is False
    factor_ids = {row["factor_id"] for row in design["latent_factors"]}
    assert {
        "baseline_amplifier",
        "action_efficiency",
        "resource_support",
        "timing_sensitivity",
        "wealth_amplifier",
        "career_amplifier",
        "relationship_sensitivity",
        "health_safety_modifier",
    } <= factor_ids
    required_fields = set(design["event_evidence_schema"]["required_fields"])
    assert {"event_domain", "event_type", "time_range", "date_precision", "valence", "intensity", "confidence", "allowed_use"} <= required_fields
    assert design["event_evidence_schema"]["allowed_use"] == ["personal_calibration_only"]
    assert {"wealth", "career", "relationship", "health", "relocation", "stress"} <= {
        row["domain"] for row in design["calibration_inquiries"]
    }
    forbidden = {"一定", "必然", "发财", "破财", "离婚", "疾病", "寿命", "诊断", "治疗", "应期"}
    assert all(not any(token in row["prompt_zh"] for token in forbidden) for row in design["calibration_inquiries"])
    assert "bayesian_update_for_internal_posterior" in design["model_policy"]["active_models_now"]
    assert "active_learning_question_selection" in design["model_policy"]["active_models_now"]
    assert "gnn_core_inference" in design["model_policy"]["blocked_models_now"]
    assert "rl_core_rule_update" in design["model_policy"]["blocked_models_now"]

    assert regression["status"] == "pass"
    assert regression["summary"]["runtime_mutation"] is False
    assert "/api/lab/interactive-calibration-design" in server
    assert "/api/lab/interactive-calibration-design/run" in server
    assert "docs/v19/V19_P64_INTERACTIVE_CALIBRATION_DESIGN.md" in manifest["created_from"]
    assert manifest["p64_interactive_calibration_design"]["latent_factor_count"] == 12
    assert manifest["p64_interactive_calibration_design"]["runtime_mutation"] is False
    assert "P64_INTERACTIVE_CALIBRATION_DESIGN" in manifest["guardrails"]


def test_p65_mainline_completion_audit_locks_core_chain_before_new_frameworks() -> None:
    from v19.synthetic_validation import build_p65_mainline_completion_audit, run_p65_mainline_completion_regression

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    server = (root / "v19/server.py").read_text(encoding="utf-8")
    audit = build_p65_mainline_completion_audit()
    regression = run_p65_mainline_completion_regression()

    assert audit["status"] == "mainline_completion_audit_ready"
    assert audit["summary"]["knowledge_draft_count"] == 436
    assert audit["summary"]["p39_candidate_count"] == 348
    assert audit["summary"]["p39_blocked_count"] == 88
    assert audit["summary"]["p61_route_wrapper_count"] == 6
    assert audit["summary"]["p69_safe_wrapper_count"] == 82
    assert audit["summary"]["r3_r4_safe_wrapper_coverage_count"] == 88
    assert audit["summary"]["r3_r4_unwrapped_count"] == 0
    assert audit["summary"]["rule_graph_candidate_count"] == 436
    assert audit["summary"]["route_matrix_row_count"] == 24
    assert audit["summary"]["answer_kind_gap_count"] == 0
    assert audit["summary"]["route_selected_not_applied_row_count"] == 0
    assert audit["summary"]["p0_action_count"] == 0
    assert audit["summary"]["p1_action_count"] == 1
    assert audit["summary"]["runtime_mutation"] is False

    p0_ids = {row["action_id"] for row in audit["priority_actions"] if row["priority"] == "P0"}
    assert p0_ids == set()
    for row in audit["answer_surface_matrix"]:
        assert row["observed_answer_kind"] == row["expected_answer_kind"]
        assert row["supported"] is True
        assert row["unsupported_reason"] == ""
        assert row["route_selected_not_applied_count"] == 0
        assert set(row["rule_graph_selected_knowledge_ids"]) <= set(row["applied_knowledge_ids"])
    observed_by_route = {row["route_id"]: row["observed_answer_kind"] for row in audit["answer_surface_matrix"]}
    assert observed_by_route["career"] == "career_structure"
    assert observed_by_route["relationship"] == "relationship_structure"
    assert observed_by_route["health"] == "health_structure"
    assert audit["conversion_coverage"]["blocked_by_risk"] == {"R3": 76, "R4": 12}

    assert regression["status"] == "pass"
    assert regression["summary"]["p39_regression_status"] == "pass"
    assert regression["summary"]["answer_kind_gap_count"] == 0
    assert regression["summary"]["route_selected_not_applied_row_count"] == 0
    assert regression["summary"]["runtime_mutation"] is False
    assert "/api/lab/mainline-completion-audit" in server
    assert "/api/lab/mainline-completion-audit/run" in server
    assert "docs/v19/V19_P65_MAINLINE_COMPLETION_AUDIT.md" in manifest["created_from"]
    assert "docs/v19/V19_P66_MAINLINE_P0_APPLICATION.md" in manifest["created_from"]
    assert manifest["p65_mainline_completion_audit"]["rule_graph_candidate_count"] == 436
    assert manifest["p65_mainline_completion_audit"]["p69_safe_wrapper_count"] == 82
    assert manifest["p65_mainline_completion_audit"]["r3_r4_unwrapped_count"] == 0
    assert manifest["p65_mainline_completion_audit"]["answer_kind_gap_count"] == 0
    assert manifest["p65_mainline_completion_audit"]["route_selected_not_applied_row_count"] == 0
    assert manifest["p65_mainline_completion_audit"]["runtime_mutation"] is False
    assert manifest["p66_mainline_p0_application"]["p0_action_count"] == 0
    assert manifest["p66_mainline_p0_application"]["runtime_mutation"] is False
    assert "P65_MAINLINE_COMPLETION_AUDIT" in manifest["guardrails"]
    assert "P66_MAINLINE_P0_APPLICATION" in manifest["guardrails"]


def test_p11_review_ui_wires_synthetic_collision_failure_loop() -> None:
    root = Path(__file__).resolve().parents[2]
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")

    for token in [
        "runSyntheticCollision",
        "syntheticCollisionStatus",
        "syntheticCollisionFailures",
        "syntheticCollisionDrafts",
    ]:
        assert token in admin_html

    assert "/api/lab/synthetic-collision/run" in admin_js
    assert "renderSyntheticCollisionReview" in admin_js
    assert "attribution_layer" in admin_js
    assert "draft_type" in admin_js


def test_p11_synthetic_collision_api_endpoint_runs_matrix() -> None:
    from fastapi.testclient import TestClient

    from v19.server import app

    client = TestClient(app)
    result = client.post("/api/lab/synthetic-collision/run?role=admin", json={})

    assert result.status_code == 200
    payload = result.json()
    assert payload["matrix"] == "P11_SYNTHETIC_EXPANSION"
    assert payload["run"]["status"] == "pass"
    assert payload["run"]["summary"]["total"] >= 20
    assert payload["run"]["evolution_report"]["guardrails"] == ["NO_AUTO_LEARNING", "NO_AUTO_RULE_PROMOTION", "ANALYST_REVIEW_REQUIRED"]


def test_p12_controlled_promotion_creates_rule_candidate_and_gates_active_record(tmp_path, monkeypatch) -> None:
    import v19.lab_interfaces as lab

    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")
    candidate = lab.create_synthetic_promotion_candidate(
        {
            "case_id": "syn.guided.expected_collision_failure",
            "target": "rule_db_structured_fact_draft",
            "draft_type": "rule_draft",
            "attribution_layer": "rule",
            "failure_types": ["relation_type_missing"],
            "knowledge_tags": ["ku:branch_relation"],
            "suggested_action": "draft_structured_rule_or_relation_mapping_then_rerun_collision",
        }
    )

    assert candidate["ok"]
    reviewed = lab.review_synthetic_promotion_candidate(
        candidate["item"]["candidate_id"],
        {"decision": "needs_rule", "actor_role": "admin", "note": "Create controlled rule proposal."},
    )

    assert reviewed["ok"]
    assert reviewed["item"]["status"] == "proposal_created"
    proposal_id = reviewed["downstream"]["proposal_id"]
    assert reviewed["downstream"]["kind"] == "bazi_rule_proposal"

    validated = lab.validate_bazi_rule_proposal(proposal_id)
    assert validated["passed"]
    approved = lab.approve_bazi_rule_proposal(proposal_id, {"actor_role": "admin", "note": "Approved after P12 review."})
    assert approved["ok"]
    version = lab.record_bazi_rule_version({"included_proposals": proposal_id, "activated_by_role": "admin", "note": "P12 gated record."})
    assert version["ok"]
    assert version["item"]["p12_regression_gate"]["passed"] is True
    assert version["item"]["p12_regression_gate"]["summary"]["total"] >= 20
    assert "P12_SYNTHETIC_REGRESSION_REQUIRED" in version["item"]["guardrails"]


def test_p12_review_ui_wires_controlled_promotion_queue() -> None:
    root = Path(__file__).resolve().parents[2]
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")

    for token in [
        "syntheticPromotionDecision",
        "syntheticPromotionStatus",
        "syntheticPromotionList",
        "reloadSyntheticPromotions",
    ]:
        assert token in admin_html

    assert "/api/lab/synthetic-promotions" in admin_js
    assert "Create Promotion Candidate" in admin_js
    assert "reviewSyntheticPromotion" in admin_js
    assert "P11 regression required" in admin_js


def test_p13_governance_release_records_versioned_artifacts(tmp_path, monkeypatch) -> None:
    import v19.lab_interfaces as lab

    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")
    created = lab.create_bazi_rule_proposal(
        {
            "actor_role": "admin",
            "rule_id": "v19.synthetic.p13.release.sample",
            "domain": "structural_relation",
            "input_contract": {"required": ["chart", "guided_question_context"]},
            "condition": {"source": "p13_test", "relation_type": "structural_context"},
            "output_contract": {"signal": "structure_context", "value_set": ["present", "absent"], "is_prediction": False},
            "reasoning_path": ["read reviewed proposal", "emit structural context only"],
            "guardrails": ["NO_RUNTIME_INFERENCE_MUTATION"],
            "rationale": "P13 release test proposal.",
        }
    )
    assert created["ok"]
    proposal_id = created["item"]["proposal_id"]
    assert lab.validate_bazi_rule_proposal(proposal_id)["passed"]
    assert lab.approve_bazi_rule_proposal(proposal_id, {"actor_role": "admin"})["ok"]
    version = lab.record_bazi_rule_version({"included_proposals": proposal_id, "activated_by_role": "admin"})
    assert version["ok"]

    release = lab.create_governance_release(
        {
            "bazi_rule_version_ids": version["item"]["version_id"],
            "note": "P13 manifest test.",
            "actor_role": "admin",
        }
    )

    assert release["ok"]
    item = release["item"]
    assert item["status"] == "release_record"
    assert item["runtime_mutation"] is False
    assert item["summary"]["artifact_count"] == 1
    assert item["summary"]["by_artifact_type"]["bazi_rule_versions"] == 1
    assert item["p13_regression_gate"]["passed"] is True
    assert item["p13_regression_gate"]["summary"]["total"] >= 20
    assert "P11_SYNTHETIC_REGRESSION_REQUIRED" in item["guardrails"]


def test_p13_governance_release_ui_and_api_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")

    for token in [
        "Governance Release Manifest",
        "releaseRuleVersionIds",
        "createGovernanceRelease",
        "governanceReleaseList",
    ]:
        assert token in admin_html

    assert "/api/lab/governance-releases" in admin_js
    assert "renderGovernanceReleases" in admin_js
    assert "P11 gate" in admin_js
    assert "lab_governance_release_post" in server


def test_p14_bazi_knowledge_expansion_draft_seeds_are_review_gated() -> None:
    root = Path(__file__).resolve().parents[2]
    payload = json.loads((root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    rows = payload["knowledge_drafts"]
    by_id = {row["knowledge_id"]: row for row in rows}
    p14_ids = [knowledge_id for knowledge_id in by_id if knowledge_id.startswith("p14.")]

    assert payload["seed_id"] == "v19.current_bazi_knowledge_draft_seeds.p14.v1"
    assert len(p14_ids) == 10
    assert len(by_id) == len(rows)
    for knowledge_id in [
        "p14.ten_god.peer_family_boundary.v1",
        "p14.ten_god.output_family_boundary.v1",
        "p14.ten_god.wealth_family_boundary.v1",
        "p14.ten_god.officer_family_boundary.v1",
        "p14.ten_god.resource_family_boundary.v1",
        "p14.month_command.seasonal_groups_boundary.v1",
        "p14.stem_combination.no_transformation_boundary.v1",
        "p14.branch_penalty.versioned_source_boundary.v1",
        "p14.twelve_growth_phase.boundary.v1",
        "p14.useful_god.boundary.v1",
    ]:
        row = by_id[knowledge_id]
        assert row["risk_level"] in {"R1", "R2", "R3"}
        assert "fortune" in row["forbidden_usage"] or "active_inference" in row["forbidden_usage"]

    assert by_id["p14.twelve_growth_phase.boundary.v1"]["risk_level"] == "R3"
    assert by_id["p14.useful_god.boundary.v1"]["risk_level"] == "R3"


def test_p14_seed_current_preserves_existing_knowledge_draft_review_state(tmp_path, monkeypatch) -> None:
    import v19.bazi_source_archive as archive

    seed_file = tmp_path / "seeds.json"
    runtime_file = tmp_path / "archive.json"
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", seed_file)
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", runtime_file)

    seed_file.write_text(
        json.dumps(
            {
                "knowledge_drafts": [
                    {
                        "knowledge_id": "p14.review_state.test",
                        "domain": "ten_god",
                        "category": "ten_god",
                        "title": "Review State Test",
                        "statement": "Initial statement.",
                        "risk_level": "R1",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert archive.seed_current_knowledge_drafts()["imported_count"] == 1
    reviewed = archive.update_knowledge_draft_review(
        "p14.review_state.test",
        {"review_status": "proposal_ready", "note": "Reviewed by analyst.", "actor_role": "analyst"},
    )
    assert reviewed["item"]["review_status"] == "proposal_ready"

    seed_file.write_text(
        json.dumps(
            {
                "knowledge_drafts": [
                    {
                        "knowledge_id": "p14.review_state.test",
                        "domain": "ten_god",
                        "category": "ten_god",
                        "title": "Review State Test",
                        "statement": "Updated statement.",
                        "risk_level": "R1",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    assert archive.seed_current_knowledge_drafts()["updated_count"] == 1
    rows = archive.list_knowledge_drafts(q="p14.review_state.test")["items"]

    assert rows[0]["statement"] == "Updated statement."
    assert rows[0]["review_status"] == "proposal_ready"
    assert rows[0]["review_note"] == "Reviewed by analyst."


def test_p15_p14_review_batches_group_drafts_without_status_mutation(tmp_path, monkeypatch) -> None:
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    seed_file = Path(__file__).resolve().parents[2] / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json"
    runtime_file = tmp_path / "archive.json"
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", seed_file)
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", runtime_file)
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    assert archive.seed_current_knowledge_drafts()["count"] >= 57
    seeded = lab.seed_p14_knowledge_review_batches()

    assert seeded["created_count"] == 3
    batches = lab.list_knowledge_review_batches()["items"]
    by_key = {item["batch_key"]: item for item in batches}
    assert by_key["p15.p14.r1_metadata_boundaries"]["summary"]["draft_count"] == 6
    assert by_key["p15.p14.r2_source_version_review"]["summary"]["draft_count"] == 2
    assert by_key["p15.p14.r3_archive_reference_only"]["summary"]["draft_count"] == 2
    assert all("NO_DRAFT_STATUS_MUTATION" in item["guardrails"] for item in batches)

    p14_rows = archive.list_knowledge_drafts(q="p14.")["items"]
    assert {row["review_status"] for row in p14_rows} == {"pending"}


def test_p15_knowledge_base_v2_catalog_manifest_is_valid() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))

    assert manifest["manifest_id"] == "v19.bazi_knowledge_base.v2.catalog"
    assert manifest["status"] == "catalog_manifest_only"
    assert "NO_RUNTIME_MUTATION" in manifest["guardrails"]
    assert {layer["layer"] for layer in manifest["layers"]} >= {
        "L0_source_archive",
        "L2_knowledge_unit_drafts",
        "L3_review_batches",
        "L5_governance_release_manifest",
    }
    assert {batch["batch_key"] for batch in manifest["review_batches"]} >= {
        "p15.p14.r1_metadata_boundaries",
        "p15.p14.r2_source_version_review",
        "p15.p14.r3_archive_reference_only",
        "p21.r1_guided_question_structure_boundaries",
        "p21.r2_income_collision_review",
    }
    assert manifest["proposal_generation"]["stage"] == "P16_KNOWLEDGE_BATCH_PROPOSAL_DRAFTS"
    assert manifest["proposal_generation"]["eligible_batches"] == ["p15.p14.r1_metadata_boundaries"]
    assert manifest["proposal_validation"]["stage"] == "P17_PROPOSAL_SCHEMA_VALIDATION_RUNS"
    assert "approval" in manifest["proposal_validation"]["forbidden_outputs"]
    assert manifest["proposal_review_packets"]["stage"] == "P18_PROPOSAL_APPROVAL_REVIEW_PACKETS"
    assert "auto_approval" in manifest["proposal_review_packets"]["forbidden_outputs"]
    assert "R2_R3_ANALYST_REVIEW_BEFORE_PROPOSAL" in manifest["guardrails"]
    assert "P17_SCHEMA_VALIDATION_ONLY" in manifest["guardrails"]
    assert "P18_REVIEW_PACKET_ONLY" in manifest["guardrails"]


def test_p15_review_batch_ui_and_api_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")

    for token in [
        "Knowledge Review Batches",
        "seedP14ReviewBatches",
        "kbReviewBatchList",
    ]:
        assert token in admin_html
    assert "/api/lab/knowledge-review-batches" in admin_js
    assert "renderKnowledgeReviewBatches" in admin_js
    assert "lab_knowledge_review_batch_seed_p14_post" in server


def test_p16_r1_review_batch_generates_rule_and_question_proposal_drafts(tmp_path, monkeypatch) -> None:
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    seed_file = Path(__file__).resolve().parents[2] / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json"
    runtime_file = tmp_path / "archive.json"
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", seed_file)
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", runtime_file)
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    assert archive.seed_current_knowledge_drafts()["count"] >= 57
    assert lab.seed_p14_knowledge_review_batches()["created_count"] == 3

    created = lab.create_knowledge_batch_proposal_drafts(
        "p15.p14.r1_metadata_boundaries",
        {"actor_role": "admin", "note": "P16 R1 test."},
    )

    assert created["ok"]
    run = created["item"]
    assert run["status"] == "proposal_drafts_created"
    assert run["summary"]["rule_proposal_count"] == 6
    assert run["summary"]["question_proposal_count"] == 1
    assert "NO_RUNTIME_MUTATION" in run["guardrails"]
    assert lab.list_knowledge_batch_proposal_runs()["count"] == 1
    assert lab.list_bazi_rule_proposals()["count"] == 6
    assert lab.list_guided_question_proposals()["count"] == 1

    for item in lab.list_bazi_rule_proposals()["items"]:
        validated = lab.validate_bazi_rule_proposal(item["proposal_id"])
        assert validated["passed"]
        assert item["evidence"]["source"] == "knowledge_review_batch"
        assert item["output_contract"]["is_prediction"] is False

    question = lab.list_guided_question_proposals()["items"][0]
    assert question["proposed_metadata"]["source"] == "p16_knowledge_batch_proposal"
    assert lab.validate_guided_question_proposal(question["proposal_id"])["passed"]

    p14_rows = archive.list_knowledge_drafts(q="p14.")["items"]
    assert {row["review_status"] for row in p14_rows} == {"pending"}


def test_p16_blocks_r2_r3_batches_until_analyst_source_review(tmp_path, monkeypatch) -> None:
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    seed_file = Path(__file__).resolve().parents[2] / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json"
    runtime_file = tmp_path / "archive.json"
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", seed_file)
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", runtime_file)
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    archive.seed_current_knowledge_drafts()
    lab.seed_p14_knowledge_review_batches()

    r2 = lab.create_knowledge_batch_proposal_drafts("p15.p14.r2_source_version_review", {"actor_role": "admin"})
    r3 = lab.create_knowledge_batch_proposal_drafts("p15.p14.r3_archive_reference_only", {"actor_role": "admin"})

    assert r2["ok"] is False
    assert r2["code"] == "KNOWLEDGE_BATCH_PROPOSAL_BLOCKED"
    assert r2["item"]["status"] == "blocked"
    assert r2["item"]["summary"]["blocked_count"] == 2
    assert r3["ok"] is False
    assert r3["item"]["status"] == "blocked"
    assert r3["item"]["summary"]["blocked_count"] == 2
    assert lab.list_bazi_rule_proposals()["count"] == 0
    assert lab.list_guided_question_proposals()["count"] == 0
    assert lab.list_knowledge_batch_proposal_runs()["count"] == 2


def test_p16_batch_proposal_ui_and_api_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")

    for token in [
        "P16 Batch Proposal Drafts",
        "createKbBatchProposalDrafts",
        "kbBatchProposalRunList",
    ]:
        assert token in admin_html
    assert "/api/lab/knowledge-batch-proposal-runs" in admin_js
    assert "renderKnowledgeBatchProposalRuns" in admin_js
    assert "proposal-drafts" in admin_js
    assert "lab_knowledge_review_batch_proposal_drafts_post" in server


def test_p17_validates_p16_rule_and_question_proposal_drafts(tmp_path, monkeypatch) -> None:
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    seed_file = Path(__file__).resolve().parents[2] / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json"
    runtime_file = tmp_path / "archive.json"
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", seed_file)
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", runtime_file)
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    archive.seed_current_knowledge_drafts()
    lab.seed_p14_knowledge_review_batches()
    p16 = lab.create_knowledge_batch_proposal_drafts("p15.p14.r1_metadata_boundaries", {"actor_role": "admin"})
    source_run_id = p16["item"]["run_id"]

    validated = lab.create_proposal_validation_run(
        {
            "actor_role": "admin",
            "source_run_id": source_run_id,
            "note": "P17 validation test.",
        }
    )

    assert validated["ok"]
    run = validated["item"]
    assert run["status"] == "validation_ready"
    assert run["summary"]["total"] == 7
    assert run["summary"]["passed"] == 7
    assert run["summary"]["failed"] == 0
    assert "P17_SCHEMA_VALIDATION_ONLY" in run["guardrails"]
    assert lab.list_proposal_validation_runs()["count"] == 1
    assert {row["status"] for row in lab.list_bazi_rule_proposals()["items"]} == {"validation_ready"}
    assert {row["status"] for row in lab.list_guided_question_proposals()["items"]} == {"validation_ready"}


def test_p17_records_validation_failures_without_approval_or_runtime_mutation(tmp_path, monkeypatch) -> None:
    import v19.lab_interfaces as lab

    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")
    proposal = lab.create_bazi_rule_proposal(
        {
            "actor_role": "admin",
            "rule_id": "v19.p17.invalid.missing_contract",
            "domain": "structural_relation",
            "output_contract": {"signal": "", "value_set": [], "is_prediction": True},
            "guardrails": ["NO_RUNTIME_INFERENCE_MUTATION"],
        }
    )
    assert proposal["ok"]

    validated = lab.create_proposal_validation_run(
        {
            "actor_role": "admin",
            "proposal_ids": proposal["item"]["proposal_id"],
            "note": "P17 failure test.",
        }
    )

    assert validated["ok"] is False
    run = validated["item"]
    assert run["status"] == "validation_failed"
    assert run["summary"]["total"] == 1
    assert run["summary"]["failed"] == 1
    assert run["runtime_mutation"] is False
    assert run["approval_mutation"] is False
    assert run["version_mutation"] is False
    assert run["items"][0]["failed_checks"]


def test_p17_proposal_validation_ui_and_api_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")

    for token in [
        "P17 Proposal Validation Runs",
        "createProposalValidationRun",
        "proposalValidationRunList",
    ]:
        assert token in admin_html
    assert "/api/lab/proposal-validation-runs" in admin_js
    assert "renderProposalValidationRuns" in admin_js
    assert "lab_proposal_validation_run_post" in server


def test_p18_creates_review_packet_from_validation_ready_proposals(tmp_path, monkeypatch) -> None:
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    seed_file = Path(__file__).resolve().parents[2] / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json"
    runtime_file = tmp_path / "archive.json"
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", seed_file)
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", runtime_file)
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    archive.seed_current_knowledge_drafts()
    lab.seed_p14_knowledge_review_batches()
    p16 = lab.create_knowledge_batch_proposal_drafts("p15.p14.r1_metadata_boundaries", {"actor_role": "admin"})
    p17 = lab.create_proposal_validation_run({"actor_role": "admin", "source_run_id": p16["item"]["run_id"]})

    packet = lab.create_proposal_review_packet(
        {
            "actor_role": "admin",
            "validation_run_id": p17["item"]["validation_run_id"],
            "note": "P18 packet test.",
        }
    )

    assert packet["ok"]
    item = packet["item"]
    assert item["status"] == "approval_review_ready"
    assert item["summary"]["total"] == 7
    assert item["summary"]["validation_passed"] == 7
    assert item["approval_mutation"] is False
    assert item["version_mutation"] is False
    assert item["runtime_mutation"] is False
    assert "P18_REVIEW_PACKET_ONLY" in item["guardrails"]
    assert lab.list_proposal_review_packets()["count"] == 1
    assert {row["status"] for row in lab.list_bazi_rule_proposals()["items"]} == {"validation_ready"}
    assert {row["status"] for row in lab.list_guided_question_proposals()["items"]} == {"validation_ready"}


def test_p18_blocks_review_packet_when_validation_failed(tmp_path, monkeypatch) -> None:
    import v19.lab_interfaces as lab

    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")
    proposal = lab.create_bazi_rule_proposal(
        {
            "actor_role": "admin",
            "rule_id": "v19.p18.invalid.packet",
            "domain": "structural_relation",
            "output_contract": {"signal": "", "value_set": [], "is_prediction": True},
            "guardrails": ["NO_RUNTIME_INFERENCE_MUTATION"],
        }
    )
    p17 = lab.create_proposal_validation_run({"actor_role": "admin", "proposal_ids": proposal["item"]["proposal_id"]})
    packet = lab.create_proposal_review_packet({"actor_role": "admin", "validation_run_id": p17["item"]["validation_run_id"]})

    assert packet["ok"] is False
    item = packet["item"]
    assert item["status"] == "blocked_by_validation"
    assert item["summary"]["validation_failed"] == 1
    assert item["recommended_decision"] == "fix_failed_validation_before_approval_review"
    assert lab.list_proposal_review_packets()["count"] == 1
    assert lab.list_bazi_rule_proposals()["items"][0]["status"] == "validation_failed"


def test_p18_review_packet_ui_and_api_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")

    for token in [
        "P18 Proposal Review Packets",
        "createProposalReviewPacket",
        "proposalReviewPacketList",
    ]:
        assert token in admin_html
    assert "/api/lab/proposal-review-packets" in admin_js
    assert "renderProposalReviewPackets" in admin_js
    assert "lab_proposal_review_packet_post" in server


def test_p19_guided_questions_are_chart_specific_not_static_registry_top_five() -> None:
    top_key_sequences = []
    top_label_sequences = []
    for case in P11_GUIDED_SYNTHETIC_CASES[:20]:
        data = _agent_data_for_case(case)
        questions = data["guided_question_context"]["questions"]
        top_keys = [row["key"] for row in questions[:5]]
        top_labels = [row["label"]["zh"] for row in questions[:5]]
        top_key_sequences.append(tuple(top_keys))
        top_label_sequences.append(tuple(top_labels))
        assert "q_income_stability" in [row["key"] for row in questions[:10]]

    old_static_top = (
        "q_structure_overview",
        "q_day_master_month_anchor",
        "q_income_stability",
        "q_branch_relation_detail",
        "q_month_command_anchor",
    )
    assert old_static_top not in set(top_key_sequences)
    assert len(set(top_key_sequences)) >= 3
    assert len(set(top_label_sequences)) >= 8


def test_p20_guided_question_diversity_audit_measures_synthetic_matrix() -> None:
    result = guided_question_diversity_audit()

    assert result["status"] == "pass"
    assert result["matrix"] == "P11_SYNTHETIC_EXPANSION"
    assert result["case_count"] >= 20
    assert result["summary"]["top_key_sequence_count"] >= 3
    assert result["summary"]["top_label_sequence_count"] >= 8
    assert result["summary"]["old_static_top_present"] is False
    assert result["summary"]["income_stability_top10_count"] == result["case_count"]
    assert result["summary"]["failure_count"] == 0
    assert "AUDIT_ONLY" in result["guardrails"]
    assert all(item["top_labels"] for item in result["items"])


def test_p20_guided_question_diversity_audit_api_and_ui_are_wired() -> None:
    from fastapi.testclient import TestClient

    from v19.server import app

    root = Path(__file__).resolve().parents[2]
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")

    for token in [
        "runQuestionDiversityAudit",
        "questionDiversityStatus",
        "questionDiversitySummary",
        "questionDiversityList",
    ]:
        assert token in admin_html

    assert "/api/lab/guided-question-diversity-audit" in admin_js
    assert "renderQuestionDiversityAudit" in admin_js

    client = TestClient(app)
    result = client.get("/api/lab/guided-question-diversity-audit?role=admin")

    assert result.status_code == 200
    payload = result.json()
    assert payload["status"] == "pass"
    assert payload["summary"]["old_static_top_present"] is False
    assert payload["summary"]["income_stability_top10_count"] == payload["case_count"]


def test_p21_knowledge_pack_loads_as_drafts_and_review_batches(tmp_path, monkeypatch) -> None:
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    seed_file = Path(__file__).resolve().parents[2] / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json"
    pack_dir = Path(__file__).resolve().parents[2] / "docs/bazi_knowledge/packs"
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", seed_file)
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", pack_dir)
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    seeded = archive.seed_current_knowledge_drafts()

    assert seeded["count"] >= 67
    drafts = archive.list_knowledge_drafts(q="p21.")["items"]
    assert len(drafts) == 10
    assert {row["review_status"] for row in drafts} == {"pending"}
    assert len([row for row in drafts if row["risk_level"] == "R1"]) == 6
    assert len([row for row in drafts if row["risk_level"] == "R2"]) == 4

    batches = lab.seed_p21_knowledge_review_batches()

    assert batches["created_count"] == 2
    by_key = {row["batch_key"]: row for row in lab.list_knowledge_review_batches()["items"]}
    assert by_key["p21.r1_guided_question_structure_boundaries"]["summary"]["draft_count"] == 6
    assert by_key["p21.r2_income_collision_review"]["summary"]["draft_count"] == 4
    assert "NO_RUNTIME_MUTATION" in batches["guardrails"]

    blocked = lab.create_knowledge_batch_proposal_drafts("p21.r2_income_collision_review", {"actor_role": "admin"})

    assert blocked["ok"] is False
    assert blocked["code"] == "KNOWLEDGE_BATCH_PROPOSAL_BLOCKED"
    assert blocked["item"]["summary"]["blocked_count"] == 4
    assert lab.list_bazi_rule_proposals()["count"] == 0


def test_p21_knowledge_pack_manifest_api_and_ui_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    pack = json.loads((root / "docs/bazi_knowledge/packs/p21_guided_question_collision_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")

    assert pack["pack_id"] == "p21.guided_question_collision_knowledge_pack.v1"
    assert len(pack["knowledge_drafts"]) == 10
    assert "docs/bazi_knowledge/packs/p21_guided_question_collision_knowledge_draft_seeds_v1.json" in manifest["created_from"]
    assert manifest["content_packs"][0]["pack_id"] == pack["pack_id"]
    assert "P21_NEW_CONTENT_PACKS_SEEDED_AS_DRAFTS_ONLY" in manifest["guardrails"]
    assert manifest["p21_review_packet_pipeline"]["stage"] == "P22_P21_R1_PROPOSAL_REVIEW_PACKET"
    assert "p21.r2_income_collision_review" in manifest["p21_review_packet_pipeline"]["blocked_until_review"]
    assert "P22_P21_R1_REVIEW_PACKET_ONLY" in manifest["guardrails"]

    for token in [
        "seedP21ReviewBatches",
        "生成 P21 Batches",
    ]:
        assert token in admin_html

    assert "/api/lab/knowledge-review-batches/seed-p21" in admin_js
    assert "lab_knowledge_review_batch_seed_p21_post" in server


def test_p22_p21_r1_pack_creates_validation_and_review_packet(tmp_path, monkeypatch) -> None:
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    root = Path(__file__).resolve().parents[2]
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    result = lab.create_p21_knowledge_pack_review_packet({"actor_role": "admin"})

    assert result["ok"]
    assert result["status"] == "review_packet_ready"
    assert result["summary"]["r1_rule_proposal_count"] == 6
    assert result["summary"]["r1_question_proposal_count"] == 1
    assert result["summary"]["validation_total"] == 7
    assert result["summary"]["validation_failed"] == 0
    assert result["summary"]["review_packet_items"] == 7
    assert result["r2_gate"]["eligible"] is False
    assert result["summary"]["r2_blocked_count"] == 4
    assert "NO_RUNTIME_MUTATION" in result["guardrails"]
    assert lab.list_bazi_rule_proposals()["count"] == 6
    assert lab.list_guided_question_proposals()["count"] == 1
    assert lab.list_proposal_validation_runs()["count"] == 1
    assert lab.list_proposal_review_packets()["count"] == 1

    repeated = lab.create_p21_knowledge_pack_review_packet({"actor_role": "admin"})

    assert repeated["ok"]
    assert repeated["proposal_run"]["run_id"] == result["proposal_run"]["run_id"]
    assert repeated["review_packet"]["packet_id"] == result["review_packet"]["packet_id"]
    assert lab.list_proposal_validation_runs()["count"] == 1
    assert lab.list_proposal_review_packets()["count"] == 1


def test_p22_p21_review_packet_api_and_ui_are_wired(tmp_path, monkeypatch) -> None:
    from fastapi.testclient import TestClient

    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab
    from v19.server import app

    root = Path(__file__).resolve().parents[2]
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")

    for token in [
        "P22 P21 Review Packet",
        "createP21ReviewPacket",
        "p21ReviewPacketList",
    ]:
        assert token in admin_html

    assert "/api/lab/p21/review-packet" in admin_js
    assert "renderP21ReviewPacket" in admin_js
    assert "lab_p21_review_packet_post" in server

    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")
    client = TestClient(app)
    response = client.post("/api/lab/p21/review-packet?role=admin", json={"actor_role": "admin"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "review_packet_ready"
    assert payload["summary"]["validation_failed"] == 0
    assert payload["r2_gate"]["eligible"] is False


def test_p23_records_review_packet_decision_without_approval_mutation(tmp_path, monkeypatch) -> None:
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    root = Path(__file__).resolve().parents[2]
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    result = lab.create_p21_knowledge_pack_review_packet({"actor_role": "admin"})
    packet_id = result["review_packet"]["packet_id"]

    decision = lab.record_proposal_review_packet_decision(
        packet_id,
        {
            "actor_role": "analyst",
            "decision": "approve_candidate",
            "note": "Analyst review recorded for P21 R1; approval must remain a separate action.",
        },
    )

    assert decision["ok"]
    assert "P23_DECISION_LEDGER_ONLY" in decision["guardrails"]
    packet = decision["item"]
    assert packet["status"] == "approval_review_ready"
    assert packet["decision_status"] == "decision_recorded"
    assert packet["decision_summary"]["total"] == 1
    assert packet["decision_summary"]["latest_decision"] == "approve_candidate"
    assert packet["latest_decision_record"]["approval_mutation"] is False
    assert packet["latest_decision_record"]["version_mutation"] is False
    assert packet["latest_decision_record"]["runtime_mutation"] is False
    assert {row["status"] for row in lab.list_bazi_rule_proposals()["items"]} == {"validation_ready"}
    assert {row["status"] for row in lab.list_guided_question_proposals()["items"]} == {"validation_ready"}
    assert lab.list_bazi_rule_versions()["count"] == 0
    assert lab.list_guided_question_library_versions()["count"] == 0
    assert lab.lab_status()["counts"]["proposal_review_packet_decisions"] == 1


def test_p23_review_packet_decision_api_and_ui_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))

    for token in [
        "proposalPacketDecision",
        "proposalPacketDecisionNote",
        "记录 P23 Decision",
    ]:
        assert token in admin_html or token in admin_js
    assert "/api/lab/proposal-review-packets/${encodeURIComponent(packetId)}/decisions" in admin_js
    assert "recordProposalReviewPacketDecision" in admin_js
    assert "lab_proposal_review_packet_decision_post" in server
    assert manifest["proposal_review_packet_decisions"]["stage"] == "P23_REVIEW_PACKET_DECISION_LEDGER"
    assert "NO_PROPOSAL_STATUS_CHANGE" in manifest["proposal_review_packet_decisions"]["forbidden_outputs"]
    assert "P23_DECISION_LEDGER_ONLY" in manifest["guardrails"]


def test_p24_item_decisions_and_approval_preflight_without_mutation(tmp_path, monkeypatch) -> None:
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    root = Path(__file__).resolve().parents[2]
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    result = lab.create_p21_knowledge_pack_review_packet({"actor_role": "admin"})
    packet_id = result["review_packet"]["packet_id"]
    packet = lab.list_proposal_review_packets()["items"][0]
    proposal_ids = [row["proposal_id"] for row in packet["items"]]

    blocked = lab.create_proposal_review_approval_preflight(packet_id, {"actor_role": "analyst"})

    assert blocked["ok"] is False
    assert blocked["item"]["status"] == "approval_preflight_blocked"
    assert blocked["item"]["summary"]["missing_item_decision_count"] == len(proposal_ids)
    assert "P24_APPROVAL_PREFLIGHT_ONLY" in blocked["guardrails"]

    decisions = [
        {
            "proposal_id": proposal_id,
            "decision": "approve_candidate",
            "note": "Item-level approval candidate recorded for preflight only.",
        }
        for proposal_id in proposal_ids
    ]
    decision_result = lab.record_proposal_review_packet_decision(packet_id, {"actor_role": "analyst", "decisions": decisions})
    ready = lab.create_proposal_review_approval_preflight(packet_id, {"actor_role": "analyst"})

    assert decision_result["ok"]
    assert ready["ok"]
    assert ready["item"]["status"] == "approval_preflight_ready"
    assert ready["item"]["summary"]["ready_item_count"] == len(proposal_ids)
    assert ready["item"]["summary"]["failed_checks"] == 0
    assert all(row["ready_for_approval"] for row in ready["item"]["items"])
    assert ready["item"]["approval_mutation"] is False
    assert ready["item"]["version_mutation"] is False
    assert ready["item"]["runtime_mutation"] is False
    listed = lab.list_proposal_review_packets()["items"][0]
    assert listed["approval_preflight_summary"]["total"] == 2
    assert listed["approval_preflight_summary"]["latest_status"] == "approval_preflight_ready"
    assert all((row.get("latest_review_decision") or {}).get("decision") == "approve_candidate" for row in listed["items"])
    assert {row["status"] for row in lab.list_bazi_rule_proposals()["items"]} == {"validation_ready"}
    assert {row["status"] for row in lab.list_guided_question_proposals()["items"]} == {"validation_ready"}
    assert lab.list_bazi_rule_versions()["count"] == 0
    assert lab.list_guided_question_library_versions()["count"] == 0
    assert lab.lab_status()["counts"]["proposal_review_approval_preflights"] == 2


def test_p24_approval_preflight_api_and_ui_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))

    assert "P24 item decision / preflight ledger only" in admin_html
    assert "记录条目 Decision" in admin_js
    assert "运行 P24 Preflight" in admin_js
    assert "/api/lab/proposal-review-packets/${encodeURIComponent(packetId)}/approval-preflight" in admin_js
    assert "runProposalReviewApprovalPreflight" in admin_js
    assert "lab_proposal_review_packet_approval_preflight_post" in server
    assert manifest["proposal_review_approval_preflight"]["stage"] == "P24_ITEM_DECISION_APPROVAL_PREFLIGHT"
    assert "P24_APPROVAL_PREFLIGHT_ONLY" in manifest["guardrails"]


def test_p25_controlled_approval_requires_preflight_and_is_idempotent(tmp_path, monkeypatch) -> None:
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    root = Path(__file__).resolve().parents[2]
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    result = lab.create_p21_knowledge_pack_review_packet({"actor_role": "admin"})
    packet_id = result["review_packet"]["packet_id"]
    packet = lab.list_proposal_review_packets()["items"][0]
    proposal_ids = [row["proposal_id"] for row in packet["items"]]

    blocked = lab.execute_proposal_review_packet_approval(packet_id, {"actor_role": "admin"})

    assert blocked["ok"] is False
    assert blocked["code"] == "P25_APPROVAL_PREFLIGHT_NOT_READY"
    assert blocked["item"]["status"] == "controlled_approval_blocked"
    assert "P25_CONTROLLED_APPROVAL_ONLY" in blocked["guardrails"]
    assert {row["status"] for row in lab.list_bazi_rule_proposals()["items"]} == {"validation_ready"}
    assert {row["status"] for row in lab.list_guided_question_proposals()["items"]} == {"validation_ready"}

    lab.record_proposal_review_packet_decision(
        packet_id,
        {
            "actor_role": "analyst",
            "decisions": [
                {"proposal_id": proposal_id, "decision": "approve_candidate", "note": "P25 gate candidate."}
                for proposal_id in proposal_ids
            ],
        },
    )
    preflight = lab.create_proposal_review_approval_preflight(packet_id, {"actor_role": "analyst"})
    approved = lab.execute_proposal_review_packet_approval(packet_id, {"actor_role": "admin", "note": "P25 controlled approval test."})
    repeated = lab.execute_proposal_review_packet_approval(packet_id, {"actor_role": "admin", "note": "P25 repeated approval test."})

    assert preflight["ok"]
    assert approved["ok"]
    assert approved["item"]["status"] == "controlled_approval_executed"
    assert approved["item"]["summary"]["approved_count"] == len(proposal_ids)
    assert approved["item"]["summary"]["rule_approved_count"] == 6
    assert approved["item"]["summary"]["question_approved_count"] == 1
    assert approved["item"]["auto_approval"] is False
    assert approved["item"]["version_mutation"] is False
    assert approved["item"]["runtime_mutation"] is False
    assert repeated["ok"]
    assert repeated["reused"] is True
    assert repeated["item"]["approval_execution_id"] == approved["item"]["approval_execution_id"]
    listed = lab.list_proposal_review_packets()["items"][0]
    assert listed["approval_execution_summary"]["total"] == 2
    assert listed["approval_execution_summary"]["latest_status"] == "controlled_approval_executed"
    assert {row["status"] for row in lab.list_bazi_rule_proposals()["items"]} == {"approved"}
    assert {row["status"] for row in lab.list_guided_question_proposals()["items"]} == {"approved"}
    assert lab.list_bazi_rule_versions()["count"] == 0
    assert lab.list_guided_question_library_versions()["count"] == 0
    assert lab.lab_status()["counts"]["proposal_review_approval_executions"] == 2


def test_p25_controlled_approval_api_and_ui_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))

    assert "执行 P25 Approval" in admin_js
    assert "executeProposalReviewApproval" in admin_js
    assert "/api/lab/proposal-review-packets/${encodeURIComponent(packetId)}/controlled-approval" in admin_js
    assert "lab_proposal_review_packet_controlled_approval_post" in server
    assert manifest["proposal_review_controlled_approval"]["stage"] == "P25_CONTROLLED_APPROVAL_EXECUTION_GATE"
    assert "P25_CONTROLLED_APPROVAL_ONLY" in manifest["guardrails"]


def test_p26_new_knowledge_pack_seeds_and_ingests_rule_db(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive

    root = Path(__file__).resolve().parents[2]
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    seeded = archive.seed_current_knowledge_drafts()
    p26_drafts = archive.list_knowledge_drafts(q="p26.")["items"]
    ingested = rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    p26_rules = rule_db.list_bazi_rules(q="p26.")["items"]

    assert seeded["count"] >= 79
    assert len(p26_drafts) == 12
    assert ingested["ok"]
    assert ingested["rule_count"] >= 77
    assert len(p26_rules) == 12
    assert all(row["engine_enabled"] is False for row in p26_rules)
    assert all(row["engine_adapter_status"] == "candidate_waiting_synthetic_acceptance" for row in p26_rules)
    assert all(row["status"] == "active_in_rule_db" for row in p26_rules)


def test_p26_converts_p25_approved_proposals_to_versions_and_rule_db(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    root = Path(__file__).resolve().parents[2]
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    result = lab.create_p21_knowledge_pack_review_packet({"actor_role": "admin"})
    packet_id = result["review_packet"]["packet_id"]
    proposal_ids = [row["proposal_id"] for row in lab.list_proposal_review_packets()["items"][0]["items"]]
    lab.record_proposal_review_packet_decision(
        packet_id,
        {
            "actor_role": "analyst",
            "decisions": [{"proposal_id": proposal_id, "decision": "approve_candidate"} for proposal_id in proposal_ids],
        },
    )
    lab.create_proposal_review_approval_preflight(packet_id, {"actor_role": "analyst"})
    lab.execute_proposal_review_packet_approval(packet_id, {"actor_role": "admin"})

    p26 = lab.execute_p26_knowledge_to_rules({"actor_role": "admin", "enable_engine": True})
    repeated = lab.execute_p26_knowledge_to_rules({"actor_role": "admin", "enable_engine": True})

    assert p26["ok"]
    assert p26["summary"]["p26_draft_count"] == 12
    assert p26["summary"]["approved_rule_proposals_consumed"] == 6
    assert p26["summary"]["approved_question_proposals_consumed"] == 1
    assert p26["summary"]["rule_db_rule_count"] >= 77
    assert p26["rule_version"]["rule_count"] == 6
    assert p26["question_version"]["question_count"] == 1
    assert "P26_KNOWLEDGE_TO_RULES_FAST_PATH" in p26["guardrails"]
    assert lab.list_bazi_rule_versions()["count"] == 1
    assert lab.list_guided_question_library_versions()["count"] == 1
    assert {row["status"] for row in lab.list_bazi_rule_proposals()["items"]} == {"active_record"}
    assert {row["status"] for row in lab.list_guided_question_proposals()["items"]} == {"active_record"}
    assert len(rule_db.list_bazi_rules(q="p26.")["items"]) == 12
    assert repeated["ok"]
    assert repeated["summary"]["approved_rule_proposals_consumed"] == 0
    assert repeated["summary"]["approved_question_proposals_consumed"] == 0
    assert lab.list_bazi_rule_versions()["count"] == 1
    assert lab.list_guided_question_library_versions()["count"] == 1


def test_p26_knowledge_to_rules_api_manifest_and_ui_are_wired() -> None:
    root = Path(__file__).resolve().parents[2]
    pack = json.loads((root / "docs/bazi_knowledge/packs/p26_rule_conversion_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")

    assert pack["pack_id"] == "p26.rule_conversion_knowledge_pack.v1"
    assert len(pack["knowledge_drafts"]) == 12
    assert "docs/bazi_knowledge/packs/p26_rule_conversion_knowledge_draft_seeds_v1.json" in manifest["created_from"]
    assert manifest["content_packs"][1]["pack_id"] == pack["pack_id"]
    assert manifest["knowledge_to_rules_fast_path"]["stage"] == "P26_KNOWLEDGE_TO_RULES_FAST_PATH"
    assert "P26_KNOWLEDGE_TO_RULES_FAST_PATH" in manifest["guardrails"]
    assert "executeP26KnowledgeToRules" in admin_html
    assert "/api/lab/p26/knowledge-to-rules" in admin_js
    assert "lab_p26_knowledge_to_rules_post" in server


def test_p27_domain_completion_pack_directories_and_smart_gate_wiring() -> None:
    root = Path(__file__).resolve().parents[2]
    pack = json.loads((root / "docs/bazi_knowledge/packs/p27_domain_completion_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    admin_html = (root / "v19/frontend/admin.html").read_text(encoding="utf-8")
    admin_js = (root / "v19/frontend/assets/admin.js").read_text(encoding="utf-8")
    server = (root / "v19/server.py").read_text(encoding="utf-8")

    for path in [
        "docs/bazi_knowledge/ten_god/ten_god_units_v1.md",
        "docs/bazi_knowledge/strength/strength_units_v1.md",
        "docs/bazi_knowledge/time_context/time_context_units_v1.md",
        "docs/bazi_knowledge/pattern/pattern_units_v1.md",
    ]:
        assert (root / path).exists()

    assert pack["pack_id"] == "p27.domain_completion_knowledge_pack.v1"
    assert len(pack["knowledge_drafts"]) == 40
    assert "docs/bazi_knowledge/packs/p27_domain_completion_knowledge_draft_seeds_v1.json" in manifest["created_from"]
    assert manifest["content_packs"][2]["pack_id"] == pack["pack_id"]
    assert manifest["smart_rule_activation_gate"]["stage"] == "P27_SMART_RULE_ACTIVATION_GATE"
    assert "P27_SMART_RULE_ACTIVATION_GATE" in manifest["guardrails"]
    assert "executeP27SmartRuleGate" in admin_html
    assert "/api/lab/p27/smart-rule-gate" in admin_js
    assert "lab_p27_smart_rule_gate_post" in server


def test_p27_smart_gate_seeds_rule_candidates_and_activates_low_risk_after_regression(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab

    root = Path(__file__).resolve().parents[2]
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    seeded = archive.seed_current_knowledge_drafts()
    p27_drafts = archive.list_knowledge_drafts(q="p27.")["items"]
    ingested = rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    p27_rules = rule_db.list_bazi_rules(q="p27.")["items"]

    assert seeded["count"] >= 119
    assert len(p27_drafts) == 40
    assert ingested["ok"]
    assert len(p27_rules) == 40
    assert all(row["engine_enabled"] is False for row in p27_rules)

    dry_run = lab.execute_p27_smart_rule_activation({"actor_role": "admin", "activate": False, "limit": 12})
    assert dry_run["ok"]
    assert dry_run["status"] == "dry_run"
    assert dry_run["summary"]["p27_draft_count"] == 40
    assert dry_run["summary"]["candidate_count"] >= 12
    assert dry_run["summary"]["selected_count"] == 12
    assert dry_run["summary"]["activated_count"] == 0
    assert dry_run["pre_regression"]["status"] == "pass"

    activated = lab.execute_p27_smart_rule_activation({"actor_role": "admin", "activate": True, "limit": 6})
    p27_rules_after = rule_db.list_bazi_rules(q="p27.")["items"]

    assert activated["ok"]
    assert activated["status"] == "activated"
    assert activated["summary"]["activated_count"] == 6
    assert activated["summary"]["rolled_back_count"] == 0
    assert activated["post_regression"]["status"] == "pass"
    assert sum(1 for row in p27_rules_after if row["engine_enabled"] is True) == 6
    assert all(row["risk_level"] == "R1" for row in p27_rules_after if row["engine_enabled"] is True)

    repeated_dry_run = lab.execute_p27_smart_rule_activation({"actor_role": "admin", "activate": False, "limit": 12})
    p27_rules_after_repeated_dry_run = rule_db.list_bazi_rules(q="p27.")["items"]

    assert repeated_dry_run["ok"]
    assert sum(1 for row in p27_rules_after_repeated_dry_run if row["engine_enabled"] is True) == 6


def test_p28e_ten_god_interaction_pack_seeds_and_ingests_rule_db(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive

    root = Path(__file__).resolve().parents[2]
    pack = json.loads((root / "docs/bazi_knowledge/packs/p28e_ten_god_interaction_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    p28e_knowledge_ids = {item["knowledge_id"] for item in pack["knowledge_drafts"]}
    seeded = archive.seed_current_knowledge_drafts()
    p28e_drafts = [row for row in archive.list_knowledge_drafts(q="p28.interaction.")["items"] if row["knowledge_id"] in p28e_knowledge_ids]
    ingested = rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    p28e_rules = [row for row in rule_db.list_bazi_rules(q="p28.interaction.")["items"] if row["knowledge_id"] in p28e_knowledge_ids]

    assert pack["pack_id"] == "p28e.ten_god_interaction_knowledge_pack.v1"
    assert len(pack["knowledge_drafts"]) == 24
    assert "docs/bazi_knowledge/packs/p28e_ten_god_interaction_knowledge_draft_seeds_v1.json" in manifest["created_from"]
    assert manifest["content_packs"][3]["pack_id"] == pack["pack_id"]
    assert seeded["count"] >= 143
    assert len(p28e_drafts) == 24
    assert ingested["ok"]
    assert len(p28e_rules) == 24
    assert {row["category"] for row in p28e_rules} == {"ten_god_interaction", "ten_god_interaction_mechanism"}
    assert all(row["domain"] == "ten_god_relation" for row in p28e_rules)
    assert all(row["engine_enabled"] is False for row in p28e_rules)
    assert all(row["engine_adapter_status"] == "candidate_waiting_synthetic_acceptance" for row in p28e_rules)
    assert all(any(token in row["forbidden_usage"] for token in ["fortune", "direct_fortune_output"]) for row in p28e_rules)


def test_p28f_ten_god_conflict_family_pack_seeds_and_ingests_rule_db(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive

    root = Path(__file__).resolve().parents[2]
    pack = json.loads((root / "docs/bazi_knowledge/packs/p28f_ten_god_conflict_family_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    topic = (root / "docs/bazi_knowledge/interaction/ten_god_conflict_constraint_mixed_topic_v1.md").read_text(encoding="utf-8")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    seeded = archive.seed_current_knowledge_drafts()
    p28f_drafts = archive.list_knowledge_drafts(q="p28.interaction.")["items"]
    ingested = rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    p28f_rules = [row for row in rule_db.list_bazi_rules(q="p28.interaction.")["items"] if row["knowledge_id"] in {item["knowledge_id"] for item in pack["knowledge_drafts"]}]

    assert pack["pack_id"] == "p28f.ten_god_conflict_family_knowledge_pack.v1"
    assert len(pack["knowledge_drafts"]) == 20
    assert "docs/bazi_knowledge/packs/p28f_ten_god_conflict_family_knowledge_draft_seeds_v1.json" in manifest["created_from"]
    assert manifest["content_packs"][4]["pack_id"] == pack["pack_id"]
    for token in ["伤官见官", "官杀攻身", "财滋杀", "合杀留官"]:
        assert token in topic
    assert seeded["count"] >= 163
    assert len(p28f_drafts) >= 44
    assert ingested["ok"]
    assert len(p28f_rules) == 20
    assert {row["category"] for row in p28f_rules} == {"ten_god_interaction", "ten_god_interaction_mechanism"}
    assert all(row["domain"] == "ten_god_relation" for row in p28f_rules)
    assert all(row["engine_enabled"] is False for row in p28f_rules)
    assert all(any(token in row["forbidden_usage"] for token in ["fortune", "direct_fortune_output"]) for row in p28f_rules)


def test_p28g_ten_god_conflict_matrix_covers_all_candidates(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    from v19.synthetic_validation import P28G_TEN_GOD_CONFLICT_SYNTHETIC_CASES, run_p28g_ten_god_conflict_matrix

    root = Path(__file__).resolve().parents[2]
    p28e = json.loads((root / "docs/bazi_knowledge/packs/p28e_ten_god_interaction_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    p28f = json.loads((root / "docs/bazi_knowledge/packs/p28f_ten_god_conflict_family_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    p31b = json.loads((root / "docs/bazi_knowledge/packs/p31b_all_knowledge_directory_completion_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    archive.seed_current_knowledge_drafts()
    rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    result = run_p28g_ten_god_conflict_matrix()
    p31b_interactions = [item for item in p31b["knowledge_drafts"] if str(item["knowledge_id"]).startswith("p31b.interaction.")]
    expected_ids = {item["knowledge_id"] for item in p28e["knowledge_drafts"] + p28f["knowledge_drafts"] + p31b_interactions}

    assert result["status"] == "pass"
    assert result["summary"]["total"] == 24
    assert result["summary"]["expected_rule_count"] == 48
    assert result["summary"]["covered_rule_count"] == 48
    assert result["summary"]["engine_enabled_count"] == 0
    assert set(result["coverage"]["expected_knowledge_ids"]) == expected_ids
    assert {case["family"] for case in P28G_TEN_GOD_CONFLICT_SYNTHETIC_CASES} == {
        "direct_conflict",
        "constraint_deprivation",
        "mixed_structure",
        "selection_rescue",
    }
    assert result["summary"]["by_activation_tier"]["condition_model_needed"] == 20
    assert "NO_RULE_ACTIVATION" in result["guardrails"]
    assert "docs/v19/V19_P28G_TEN_GOD_CONFLICT_SYNTHETIC_MATRIX.md" in manifest["created_from"]


def test_p28h_ten_god_conflict_review_table_marks_rule_boundaries() -> None:
    from v19.synthetic_validation import build_p28h_ten_god_conflict_review_table

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    report = (root / "docs/v19/V19_P28H_TEN_GOD_CONFLICT_REVIEW_TABLE.md").read_text(encoding="utf-8")
    result = build_p28h_ten_god_conflict_review_table()
    by_title = {row["title"]: row for row in result["items"]}

    assert result["status"] == "review_ready"
    assert result["summary"]["total"] == 24
    assert result["summary"]["existence_rule_candidate_count"] == 24
    assert result["summary"]["fast_path_candidate_count"] == 4
    assert result["summary"]["condition_model_required_count"] == 20
    assert result["summary"]["mechanism_hold_count"] == 24
    assert result["summary"]["archive_only_verdict_count"] == 24
    assert by_title["伤官见官"]["activation_decision"] == "existence_fast_path_candidate"
    assert by_title["官杀攻身"]["activation_decision"] == "condition_model_required_before_activation"
    assert by_title["印化杀"]["activation_decision"] == "condition_model_required_before_activation"
    assert by_title["财官相生"]["activation_decision"] == "condition_model_required_before_activation"
    assert "官非灾祸" in by_title["伤官见官"]["archive_only_verdicts"]
    assert "禄刃 / 控制压力模型未完成" in by_title["官杀攻身"]["condition_model_gaps"]
    assert all(row["mechanism_decision"] == "hold_for_condition_model" for row in result["items"])
    assert "docs/v19/V19_P28H_TEN_GOD_CONFLICT_REVIEW_TABLE.md" in manifest["created_from"]
    assert manifest["p28h_ten_god_conflict_review_table"]["fast_path_candidate_count"] == 4
    assert "P28I" in report


def test_p28i_ten_god_fast_path_gate_activates_precise_existence_rules(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    from v19.bazi_guided_questions import build_guided_question_answer, build_guided_question_context, guided_answer_to_plain_text
    from v19.synthetic_validation import run_p28i_ten_god_fast_path_gate
    from v19.synthetic_validation.ten_god_conflict_matrix import P28G_TEN_GOD_CONFLICT_SYNTHETIC_CASES

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    archive.seed_current_knowledge_drafts()
    rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    dry_run = run_p28i_ten_god_fast_path_gate(activate=False)
    activated = run_p28i_ten_god_fast_path_gate(activate=True)
    active_rules = [row for row in rule_db.list_bazi_rules(q="p28.interaction.")["items"] if row["engine_enabled"] is True]
    active_ids = {row["knowledge_id"] for row in active_rules}

    assert dry_run["status"] == "dry_run_pass"
    assert dry_run["summary"]["fast_path_candidate_count"] == 4
    assert dry_run["summary"]["eligible_count"] == 4
    assert dry_run["summary"]["signal_audit_status"] == "pass"
    assert all(row["matched_fast_path_signal_ids"] == [row["expected_knowledge_id"]] for row in dry_run["signal_audit"]["cases"])
    assert activated["status"] == "activated"
    assert activated["summary"]["activation_updated_count"] == 4
    assert active_ids == set(dry_run["selected_ids"])
    assert all(row["category"] == "ten_god_interaction" for row in active_rules)
    assert not any(row["category"] == "ten_god_interaction_mechanism" and row["engine_enabled"] for row in rule_db.list_bazi_rules(q="p28.interaction.")["items"])

    case = next(row for row in P28G_TEN_GOD_CONFLICT_SYNTHETIC_CASES if row["case_id"] == "syn.p28g.shangguan_see_official")
    agent_data = {"chart": case["chart"], "time_context": case["time_context"], "inference_context": {}}
    context = build_guided_question_context(agent_data)
    question_keys = [row["key"] for row in context["questions"]]
    answer = build_guided_question_answer({**agent_data, "guided_question_context": context, "knowledge_context": {"items": []}}, "kbq_ten_god_interaction_boundary", "当前命中的伤官见官应该如何按结构层阅读？")
    text = guided_answer_to_plain_text(answer, "zh")

    assert "kbq_ten_god_interaction_boundary" in question_keys
    assert "q_ten_god_metadata" in question_keys
    assert answer["source_signal_category"] == "ten_god_interaction"
    assert "伤官" in text
    assert "正官" in text
    for forbidden in ["官非", "灾祸", "事业不顺", "发财", "破财"]:
        assert forbidden not in text
    assert "docs/v19/V19_P28I_TEN_GOD_FAST_PATH_GATE.md" in manifest["created_from"]
    assert manifest["p28i_ten_god_fast_path_gate"]["fast_path_candidate_count"] == 4
    assert manifest["p28i_ten_god_fast_path_gate"]["activation_result"] == "dry_run_pass_and_activation_ready"


def test_p28j_ten_god_mechanism_condition_models_batch_all_remaining_candidates(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    from v19.synthetic_validation import build_p28j_ten_god_mechanism_condition_models

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    archive.seed_current_knowledge_drafts()
    rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    result = build_p28j_ten_god_mechanism_condition_models()
    by_title = {row["title"]: row for row in result["models"]}

    assert result["status"] == "condition_models_ready_activation_blocked"
    assert result["summary"]["mechanism_candidate_count"] == 20
    assert result["summary"]["condition_model_count"] == 20
    assert result["summary"]["activation_ready_count"] == 0
    assert result["summary"]["activation_blocked_count"] == 20
    assert result["summary"]["by_family"] == {
        "direct_conflict": 3,
        "constraint_deprivation": 6,
        "mixed_structure": 1,
        "selection_rescue": 10,
    }
    assert result["summary"]["axis_coverage"]["source_layer"] == 20
    assert result["summary"]["axis_coverage"]["capacity_strength"] == 20
    assert all("p28k_synthetic_pair_regression_required" in row["activation_blockers"] for row in result["models"])
    assert all(row["engine_enabled"] is False for row in result["models"])
    assert "resource_controls_output_target" in {axis["key"] for axis in by_title["枭神夺食"]["condition_axes"]}
    assert "wealth_feeds_pressure_boundary" in {axis["key"] for axis in by_title["财滋杀"]["condition_axes"]}
    assert "combine_effectiveness_and_keep_remove_path" in {axis["key"] for axis in by_title["合杀留官"]["condition_axes"]}
    assert "blade_control_pressure_model" in {axis["key"] for axis in by_title["羊刃驾杀"]["condition_axes"]}
    assert "seal_transform_kill_capacity" in {axis["key"] for axis in by_title["印化杀"]["condition_axes"]}
    assert "wealth_official_continuity" in {axis["key"] for axis in by_title["财官相生"]["condition_axes"]}
    assert result["next_batch"]["minimum_required_pairs"] >= 111
    assert "docs/v19/V19_P28J_TEN_GOD_MECHANISM_CONDITION_MODELS.md" in manifest["created_from"]
    assert "docs/v19/V19_P28J_FRAMEWORK_ADAPTATION_REVIEW.md" in manifest["created_from"]
    assert manifest["p28j_ten_god_mechanism_condition_models"]["mechanism_candidate_count"] == 20
    assert manifest["v19_framework_adaptation_review"]["decision"] == "extend_current_framework_do_not_replace_now"


def test_p28k_ten_god_mechanism_eval_dataset_and_regression_are_strict(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    from v19.synthetic_validation import build_p28k_ten_god_mechanism_eval_dataset, run_p28k_ten_god_mechanism_regression

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    archive.seed_current_knowledge_drafts()
    rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    dataset = build_p28k_ten_god_mechanism_eval_dataset()
    regression = run_p28k_ten_god_mechanism_regression()
    samples_by_mechanism = {}
    for sample in dataset["samples"]:
        samples_by_mechanism.setdefault(sample["source_mechanism_id"], []).append(sample)

    assert dataset["status"] == "eval_dataset_ready_no_rule_activation"
    assert dataset["summary"]["mechanism_count"] == 20
    assert dataset["summary"]["sample_count"] == 172
    assert dataset["summary"]["by_polarity"] == {
        "positive": 66,
        "negative": 66,
        "distractor_time": 20,
        "distractor_hidden": 20,
    }
    assert dataset["summary"]["min_samples_per_mechanism"] == 8
    assert dataset["summary"]["complex_mechanism_count"] == 3
    assert all({"case_id", "source_mechanism_id", "polarity", "expected_signal", "forbidden_signals", "expected_question_keys", "forbidden_text", "condition_axes_expected", "audit_tags"} <= set(sample) for sample in dataset["samples"])
    assert all(len(rows) in {8, 12} for rows in samples_by_mechanism.values())
    assert len([rows for rows in samples_by_mechanism.values() if len(rows) == 12]) == 3
    assert all(sample["expected_signal"] == sample["source_mechanism_id"] for sample in dataset["samples"] if sample["polarity"] == "positive")
    assert all(sample["source_mechanism_id"] in sample["forbidden_signals"] for sample in dataset["samples"] if sample["polarity"] != "positive")
    assert all(any(axis["expected"] == "blocked" for axis in sample["condition_axes_expected"]) for sample in dataset["samples"] if sample["polarity"] != "positive")

    assert regression["status"] == "pass"
    assert regression["summary"]["sample_count"] == 172
    assert regression["summary"]["sample_failed"] == 0
    assert regression["summary"]["false_positive_count"] == 0
    assert regression["summary"]["forbidden_text_failure_count"] == 0
    assert regression["summary"]["activation_updated_count"] == 0
    assert "docs/v19/V19_P28K_TEN_GOD_MECHANISM_EVAL_DATASET.md" in manifest["created_from"]
    assert manifest["p28k_ten_god_mechanism_eval_dataset"]["sample_count"] == 172
    assert manifest["p28k_ten_god_mechanism_eval_dataset"]["activation_allowed"] is False


def test_p28l_ten_god_mechanism_signal_gate_is_shadow_only(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    from v19.synthetic_validation import run_p28l_ten_god_mechanism_signal_gate

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    archive.seed_current_knowledge_drafts()
    rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    gate = run_p28l_ten_god_mechanism_signal_gate()

    assert gate["status"] == "shadow_gate_pass_no_activation"
    assert gate["summary"]["mechanism_count"] == 20
    assert gate["summary"]["sample_count"] == 172
    assert gate["summary"]["shadow_signal_pass_count"] == 20
    assert gate["summary"]["false_positive_count"] == 0
    assert gate["summary"]["missed_positive_count"] == 0
    assert gate["summary"]["production_activation_deferred_count"] == 20
    assert gate["summary"]["activation_updated_count"] == 0
    assert all(row["shadow_decision"] == "shadow_signal_ready" for row in gate["mechanisms"])
    assert all(row["production_decision"] == "production_activation_deferred" for row in gate["mechanisms"])
    assert all(row["engine_enabled"] is False for row in gate["mechanisms"])
    assert not any(row["matched_signal_ids"] for row in gate["samples"] if row["polarity"] != "positive")
    assert all(row["matched_signal_ids"] == [row["source_mechanism_id"]] for row in gate["samples"] if row["polarity"] == "positive")
    assert "docs/v19/V19_P28L_TEN_GOD_MECHANISM_SIGNAL_GATE.md" in manifest["created_from"]
    assert manifest["p28l_ten_god_mechanism_signal_gate"]["shadow_signal_pass_count"] == 20
    assert manifest["p28l_ten_god_mechanism_signal_gate"]["activation_allowed"] is False


def test_p29_ten_god_mechanism_internal_scoring_ranks_without_activation(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    from v19.synthetic_validation import run_p29_ten_god_mechanism_internal_scoring

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    archive.seed_current_knowledge_drafts()
    rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    scoring = run_p29_ten_god_mechanism_internal_scoring()

    assert scoring["status"] == "internal_scoring_ready_no_activation"
    assert scoring["summary"]["mechanism_count"] == 20
    assert scoring["summary"]["rank_ready_count"] == 20
    assert scoring["summary"]["blocked_count"] == 0
    assert scoring["summary"]["activation_updated_count"] == 0
    assert scoring["summary"]["p28l_status"] == "shadow_gate_pass_no_activation"
    assert all(row["scoring_decision"] == "rank_ready" for row in scoring["scores"])
    assert all(row["activation_allowed"] is False for row in scoring["scores"])
    assert all(row["user_output_allowed"] is False for row in scoring["scores"])
    assert all(row["internal_rank_score"] >= 75 for row in scoring["scores"])
    assert [row["rank"] for row in scoring["scores"]] == list(range(1, 21))
    assert "docs/v19/V19_P29_TEN_GOD_MECHANISM_INTERNAL_SCORING.md" in manifest["created_from"]
    assert manifest["p29_ten_god_mechanism_internal_scoring"]["rank_ready_count"] == 20
    assert manifest["p29_ten_god_mechanism_internal_scoring"]["user_facing_probability_allowed"] is False


def test_p30_ten_god_mechanism_arbitration_controls_focus_and_backlog(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    from v19.synthetic_validation import run_p30_ten_god_mechanism_arbitration

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    archive.seed_current_knowledge_drafts()
    rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    arbitration = run_p30_ten_god_mechanism_arbitration()

    assert arbitration["status"] == "arbitration_ready_no_activation"
    assert arbitration["summary"]["scenario_count"] == 5
    assert arbitration["summary"]["scenario_pass_count"] == 5
    assert arbitration["summary"]["blocked_count"] == 0
    assert arbitration["summary"]["primary_focus_count"] == 5
    assert arbitration["summary"]["migration_backlog_count"] == 5
    assert arbitration["summary"]["activation_updated_count"] == 0
    assert arbitration["migration_policy"]["decision"] == "dual_track_forward_first_then_backfill"
    assert all(row["primary_focus"]["mechanism_id"].startswith("p28.interaction.") for row in arbitration["scenarios"])
    assert all("user_facing_probability" in row["forbidden_outputs"] for row in arbitration["scenarios"])
    assert all(row["status"] == "pass" for row in arbitration["scenarios"])
    assert {row["decision"] for row in arbitration["migration_backlog"]} >= {"migrate_before_activation", "defer_until_topic_coverage_complete"}
    assert "docs/v19/V19_P30_TEN_GOD_MECHANISM_ARBITRATION.md" in manifest["created_from"]
    assert manifest["p30_ten_god_mechanism_arbitration"]["scenario_count"] == 5
    assert manifest["p30_ten_god_mechanism_arbitration"]["legacy_migration_policy"] == "dual_track_forward_first_then_backfill"


def test_p31_all_knowledge_coverage_audit_reads_catalog_and_new_framework_tracks() -> None:
    from v19.knowledge_base_audit import run_p31_all_knowledge_coverage_audit

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    audit = run_p31_all_knowledge_coverage_audit()

    assert audit["status"] == "audit_ready_gaps_found"
    assert audit["summary"]["taxonomy_item_count"] == 255
    assert audit["summary"]["knowledge_draft_count"] == 436
    assert audit["summary"]["by_taxonomy_status"] == {"已有": 32, "部分": 214, "归档": 9}
    assert audit["summary"]["drafts_by_domain"]["core_structure"] == 62
    assert audit["summary"]["drafts_by_domain"]["luck_flow"] == 36
    assert audit["summary"]["drafts_by_domain"]["pattern"] == 48
    assert audit["summary"]["drafts_by_domain"]["blind"] == 29
    assert audit["summary"]["drafts_by_domain"]["wealth"] == 30
    assert audit["summary"]["drafts_by_domain"]["career"] == 10
    assert audit["summary"]["drafts_by_domain"]["geo_context"] == 16
    assert audit["summary"]["drafts_by_domain"]["useful_god"] == 6
    assert audit["summary"]["drafts_by_domain"]["answer_expression"] == 22
    assert audit["summary"]["drafts_by_domain"]["lab"] == 7
    assert audit["summary"]["drafts_by_domain"]["rule_db"] == 7
    assert audit["summary"]["drafts_by_domain"]["palace"] == 7
    assert audit["directory_report"]["existing_directory_count"] == 33
    assert audit["directory_report"]["missing_directory_count"] == 0
    assert "pattern/regular" in audit["directory_report"]["existing_directories"]
    assert "blind/lifa" in audit["directory_report"]["existing_directories"]
    assert "palace" in audit["directory_report"]["existing_directories"]
    assert "career" in audit["directory_report"]["existing_directories"]
    assert "rule_db" in audit["directory_report"]["existing_directories"]
    assert audit["framework_fit"]["by_track"]["condition_model_eval_gate"] > 40
    assert audit["migration_policy"]["decision"] == "dual_track_forward_first_then_backfill"
    assert "docs/v19/V19_P31_ALL_KNOWLEDGE_COVERAGE_AUDIT.md" in manifest["created_from"]
    assert "docs/v19/V19_P31B_ALL_KNOWLEDGE_DIRECTORY_COMPLETION.md" in manifest["created_from"]
    assert manifest["p31_all_knowledge_coverage_audit"]["knowledge_draft_count"] == 436
    assert manifest["p31a_all_knowledge_foundation_gap_pack"]["draft_count"] == 35
    assert manifest["p31b_all_knowledge_directory_completion"]["draft_count"] == 36


def test_p31a_foundation_gap_pack_seeds_and_keeps_runtime_disabled(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive

    root = Path(__file__).resolve().parents[2]
    pack = json.loads((root / "docs/bazi_knowledge/packs/p31a_all_knowledge_foundation_gap_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    seeded = archive.seed_current_knowledge_drafts()
    p31a_drafts = archive.list_knowledge_drafts(q="p31a.")["items"]
    ingested = rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    p31a_rules = rule_db.list_bazi_rules(q="p31a.")["items"]

    assert pack["pack_id"] == "p31a.all_knowledge_foundation_gap_pack.v1"
    assert len(pack["knowledge_drafts"]) == 35
    assert seeded["count"] == 436
    assert len(p31a_drafts) == 35
    assert ingested["rule_count"] >= 424
    assert len(p31a_rules) == 35
    assert {row["domain"] for row in p31a_drafts} >= {"blind", "palace", "pattern", "luck_flow", "geo_context", "strength", "core_structure"}
    assert all(row["engine_enabled"] is False for row in p31a_rules)
    assert all(any(token in row["forbidden_usage"] for token in ["fortune", "direct_fortune_output"]) for row in p31a_rules)


def test_p31b_directory_completion_pack_removes_missing_directories_and_stays_shadow_only(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    from v19.knowledge_base_audit import run_p31_all_knowledge_coverage_audit

    root = Path(__file__).resolve().parents[2]
    pack = json.loads((root / "docs/bazi_knowledge/packs/p31b_all_knowledge_directory_completion_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    audit = run_p31_all_knowledge_coverage_audit()
    seeded = archive.seed_current_knowledge_drafts()
    ingested = rule_db.ingest_current_knowledge_drafts_to_rule_db(force=False, enable_engine=True)
    p31b_drafts = archive.list_knowledge_drafts(q="p31b.")["items"]
    p31b_rules = rule_db.list_bazi_rules(q="p31b.")["items"]

    assert pack["pack_id"] == "p31b.all_knowledge_directory_completion_pack.v1"
    assert len(pack["knowledge_drafts"]) == 36
    assert audit["directory_report"]["missing_directories"] == []
    assert audit["summary"]["by_taxonomy_status"].get("缺失", 0) == 0
    assert seeded["count"] == 436
    assert ingested["rule_count"] >= 424
    assert len(p31b_drafts) == 36
    assert len(p31b_rules) == 36
    assert {row["domain"] for row in p31b_drafts} >= {
        "career",
        "relationship",
        "health",
        "rule_db",
        "lab",
        "timing",
        "useful_god",
        "branch_advanced",
    }
    assert all(row["engine_enabled"] is False for row in p31b_rules)
    assert all(any(token in row["forbidden_usage"] for token in ["fortune", "auto_approval", "runtime_activation"]) for row in p31b_rules)


def test_p32_ten_god_pathway_second_wave_new_knowledge_pack_is_cataloged() -> None:
    root = Path(__file__).resolve().parents[2]
    pack = json.loads((root / "docs/bazi_knowledge/packs/p32_ten_god_pathway_second_wave_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    topic = (root / "docs/bazi_knowledge/interaction/ten_god_pathway_second_wave_topic_v1.md").read_text(encoding="utf-8")
    taxonomy = (root / "docs/bazi_knowledge/catalog/bazi_knowledge_taxonomy_master_zh_v1.md").read_text(encoding="utf-8")
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    drafts = pack["knowledge_drafts"]
    titles = {row["title"] for row in drafts}

    assert pack["pack_id"] == "p32.ten_god_pathway_second_wave_knowledge_pack.v1"
    assert len(drafts) == 24
    assert {row["risk_level"] for row in drafts} == {"R1", "R2"}
    assert {row["domain"] for row in drafts} == {"interaction"}
    assert {row["category"] for row in drafts} == {"ten_god_pathway", "ten_god_pathway_mechanism"}
    for title in [
        "伤官生财组合存在",
        "食神泄秀组合存在",
        "比劫帮身组合存在",
        "官杀制比劫组合存在",
        "官星护财组合存在",
        "财制枭护食组合存在",
        "食神生财制杀组合存在",
        "财印交战组合存在",
    ]:
        assert title in titles
    assert "P32 第二批路径补全状态" in (root / "docs/bazi_knowledge/interaction/ten_god_interaction_topics_v1.md").read_text(encoding="utf-8")
    assert "十神路径第二批" in taxonomy
    assert "财制枭护食" in topic
    assert "docs/bazi_knowledge/interaction/ten_god_pathway_second_wave_topic_v1.md" in manifest["created_from"]
    assert "docs/bazi_knowledge/packs/p32_ten_god_pathway_second_wave_knowledge_draft_seeds_v1.json" in manifest["created_from"]
    assert "docs/v19/V19_P32_TEN_GOD_PATHWAY_SECOND_WAVE_KNOWLEDGE.md" in manifest["created_from"]
    manifest_pack = next(row for row in manifest["content_packs"] if row["pack_id"] == pack["pack_id"])
    assert manifest_pack["draft_count"] == 24


def test_p33_pattern_expansion_first_wave_new_knowledge_pack_is_cataloged() -> None:
    root = Path(__file__).resolve().parents[2]
    pack = json.loads((root / "docs/bazi_knowledge/packs/p33_pattern_expansion_first_wave_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    topic = (root / "docs/bazi_knowledge/pattern/pattern_expansion_first_wave_topic_v1.md").read_text(encoding="utf-8")
    taxonomy = (root / "docs/bazi_knowledge/catalog/bazi_knowledge_taxonomy_master_zh_v1.md").read_text(encoding="utf-8")
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    drafts = pack["knowledge_drafts"]
    titles = {row["title"] for row in drafts}

    assert pack["pack_id"] == "p33.pattern_expansion_first_wave_knowledge_pack.v1"
    assert len(drafts) == 32
    assert {row["domain"] for row in drafts} == {"pattern"}
    assert {row["risk_level"] for row in drafts} == {"R2", "R3"}
    assert {row["category"] for row in drafts} == {
        "pattern_source",
        "pattern_source_boundary",
        "regular_pattern_detail",
        "regular_pattern_boundary",
        "special_pattern_boundary",
    }
    for title in [
        "月令取格来源存在",
        "杂气取格条件边界",
        "正官格候选结构",
        "七杀格制化边界",
        "财格承载边界",
        "伤官格见官配印边界",
        "从财格真从假从边界",
        "化气格合而不化边界",
    ]:
        assert title in titles
    assert "格局细化第一批" in taxonomy
    assert "月令取格" in topic
    assert "合而不化" in topic
    assert "docs/bazi_knowledge/pattern/pattern_expansion_first_wave_topic_v1.md" in manifest["created_from"]
    assert "docs/bazi_knowledge/packs/p33_pattern_expansion_first_wave_knowledge_draft_seeds_v1.json" in manifest["created_from"]
    assert "docs/v19/V19_P33_PATTERN_EXPANSION_FIRST_WAVE_KNOWLEDGE.md" in manifest["created_from"]
    manifest_pack = next(row for row in manifest["content_packs"] if row["pack_id"] == pack["pack_id"])
    assert manifest_pack["draft_count"] == 32


def test_p34_blind_lifa_expansion_first_wave_new_knowledge_pack_is_cataloged() -> None:
    root = Path(__file__).resolve().parents[2]
    pack = json.loads((root / "docs/bazi_knowledge/packs/p34_blind_lifa_expansion_first_wave_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    topic = (root / "docs/bazi_knowledge/blind/lifa/blind_lifa_expansion_first_wave_topic_v1.md").read_text(encoding="utf-8")
    taxonomy = (root / "docs/bazi_knowledge/catalog/bazi_knowledge_taxonomy_master_zh_v1.md").read_text(encoding="utf-8")
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    drafts = pack["knowledge_drafts"]
    titles = {row["title"] for row in drafts}

    assert pack["pack_id"] == "p34.blind_lifa_expansion_first_wave_knowledge_pack.v1"
    assert len(drafts) == 24
    assert {row["domain"] for row in drafts} == {"blind"}
    assert {row["risk_level"] for row in drafts} == {"R2", "R3"}
    assert {row["category"] for row in drafts} == {
        "blind_lifa_action",
        "blind_lifa_boundary",
        "blind_lifa_path",
        "blind_lifa_role",
        "blind_xiangfa_archive",
    }
    for title in [
        "宾主定位结构存在",
        "体用定位边界",
        "做功路径成立边界",
        "合冲做功边界",
        "墓库做功候选存在",
        "时间引动作功边界",
        "换象带象边界",
    ]:
        assert title in titles
    assert "盲派理法细化第一批" in taxonomy
    assert "actor" in topic
    assert "时间层不改写本命结构" in topic
    assert "docs/bazi_knowledge/blind/lifa/blind_lifa_expansion_first_wave_topic_v1.md" in manifest["created_from"]
    assert "docs/bazi_knowledge/packs/p34_blind_lifa_expansion_first_wave_knowledge_draft_seeds_v1.json" in manifest["created_from"]
    assert "docs/v19/V19_P34_BLIND_LIFA_EXPANSION_FIRST_WAVE_KNOWLEDGE.md" in manifest["created_from"]
    manifest_pack = next(row for row in manifest["content_packs"] if row["pack_id"] == pack["pack_id"])
    assert manifest_pack["draft_count"] == 24


def test_p35_branch_time_activation_first_wave_new_knowledge_pack_is_cataloged() -> None:
    root = Path(__file__).resolve().parents[2]
    pack = json.loads((root / "docs/bazi_knowledge/packs/p35_branch_time_activation_first_wave_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    topic = (root / "docs/bazi_knowledge/time_context/branch_time_activation_first_wave_topic_v1.md").read_text(encoding="utf-8")
    taxonomy = (root / "docs/bazi_knowledge/catalog/bazi_knowledge_taxonomy_master_zh_v1.md").read_text(encoding="utf-8")
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    drafts = pack["knowledge_drafts"]
    titles = {row["title"] for row in drafts}

    assert pack["pack_id"] == "p35.branch_time_activation_first_wave_knowledge_pack.v1"
    assert len(drafts) == 36
    assert {row["domain"] for row in drafts} == {"core_structure", "luck_flow"}
    assert {row["risk_level"] for row in drafts} == {"R1", "R2"}
    assert {row["category"] for row in drafts} == {
        "branch_relation",
        "branch_relation_boundary",
        "stem_relation",
        "stem_relation_boundary",
        "storage_relation",
        "storage_relation_boundary",
        "time_activation",
        "time_activation_boundary",
    }
    for title in [
        "六合合化边界",
        "六冲作用边界",
        "三合局成势边界",
        "三会局季节边界",
        "天干五合合化边界",
        "墓库开闭边界",
        "流年引动大运边界",
        "干支同动拆分边界",
        "墓库引动边界",
    ]:
        assert title in titles
    assert "地支关系与时间引动细化第一批" in taxonomy
    assert "时间引动细化第一批" in taxonomy
    assert "关系名不能直接等于作用成立" in topic
    assert "时间层不改写本命结构" in topic
    assert "docs/bazi_knowledge/time_context/branch_time_activation_first_wave_topic_v1.md" in manifest["created_from"]
    assert "docs/bazi_knowledge/packs/p35_branch_time_activation_first_wave_knowledge_draft_seeds_v1.json" in manifest["created_from"]
    assert "docs/v19/V19_P35_BRANCH_TIME_ACTIVATION_FIRST_WAVE_KNOWLEDGE.md" in manifest["created_from"]
    manifest_pack = next(row for row in manifest["content_packs"] if row["pack_id"] == pack["pack_id"])
    assert manifest_pack["draft_count"] == 36


def test_p36_domain_application_first_wave_new_knowledge_pack_is_cataloged() -> None:
    root = Path(__file__).resolve().parents[2]
    pack = json.loads((root / "docs/bazi_knowledge/packs/p36_domain_application_first_wave_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    topic = (root / "docs/bazi_knowledge/wealth/domain_application_first_wave_topic_v1.md").read_text(encoding="utf-8")
    taxonomy = (root / "docs/bazi_knowledge/catalog/bazi_knowledge_taxonomy_master_zh_v1.md").read_text(encoding="utf-8")
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    drafts = pack["knowledge_drafts"]
    titles = {row["title"] for row in drafts}

    assert pack["pack_id"] == "p36.domain_application_first_wave_knowledge_pack.v1"
    assert len(drafts) == 28
    assert {row["domain"] for row in drafts} == {
        "career",
        "children",
        "family",
        "health",
        "personality",
        "relationship",
        "wealth",
    }
    assert {row["risk_level"] for row in drafts} == {"R2", "R3", "R4"}
    assert {row["category"] for row in drafts} == {
        "domain_archive",
        "domain_archive_boundary",
        "domain_boundary",
        "domain_bridge",
    }
    for title in [
        "财富收入结构边界",
        "财星显隐可达边界",
        "财富稳定波动边界",
        "食伤变现路径边界",
        "事业官杀语境边界",
        "格局事业承接边界",
        "关系日支语境边界",
        "健康安全降级边界",
        "性格象意归档边界",
    ]:
        assert title in titles
    assert "领域应用承接第一批" in taxonomy
    assert "财富、事业、关系、健康、六亲、子女、性格" in topic
    assert "不做领域预测" in topic
    assert "docs/bazi_knowledge/wealth/domain_application_first_wave_topic_v1.md" in manifest["created_from"]
    assert "docs/bazi_knowledge/packs/p36_domain_application_first_wave_knowledge_draft_seeds_v1.json" in manifest["created_from"]
    assert "docs/v19/V19_P36_DOMAIN_APPLICATION_FIRST_WAVE_KNOWLEDGE.md" in manifest["created_from"]
    manifest_pack = next(row for row in manifest["content_packs"] if row["pack_id"] == pack["pack_id"])
    assert manifest_pack["draft_count"] == 28


def test_p37_auxiliary_geo_first_wave_new_knowledge_pack_is_cataloged() -> None:
    root = Path(__file__).resolve().parents[2]
    pack = json.loads((root / "docs/bazi_knowledge/packs/p37_auxiliary_geo_first_wave_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    topic = (root / "docs/bazi_knowledge/geo_context/auxiliary_geo_first_wave_topic_v1.md").read_text(encoding="utf-8")
    taxonomy = (root / "docs/bazi_knowledge/catalog/bazi_knowledge_taxonomy_master_zh_v1.md").read_text(encoding="utf-8")
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    drafts = pack["knowledge_drafts"]
    titles = {row["title"] for row in drafts}

    assert pack["pack_id"] == "p37.auxiliary_geo_first_wave_knowledge_pack.v1"
    assert len(drafts) == 30
    assert {row["domain"] for row in drafts} == {
        "auxiliary_pillars",
        "auxiliary_symbols",
        "geo_context",
        "growth_phase",
        "nayin",
        "shensha",
        "useful_god",
    }
    assert {row["risk_level"] for row in drafts} == {"R1", "R2", "R3", "R4"}
    assert {row["category"] for row in drafts} == {
        "auxiliary_archive",
        "auxiliary_boundary",
        "geo_boundary",
        "geo_context_archive",
        "geo_metadata",
    }
    for title in [
        "出生地时区校验边界",
        "真太阳时启用边界",
        "地域气候调候边界",
        "迁移地影响禁用边界",
        "十二长生使用边界",
        "神煞索引边界",
        "纳音归档边界",
        "空亡辅助符号边界",
        "用神候选禁用边界",
        "忌神与补救建议禁用边界",
    ]:
        assert title in titles
    assert "地理与排盘元数据细化第一批" in taxonomy
    assert "辅助体系细化第一批" in taxonomy
    assert any("不输出喜用、忌神或补救建议" in row["statement"] for row in drafts)
    assert "地理信息只作排盘校验或背景" in (root / "docs/v19/V19_P37_AUXILIARY_GEO_FIRST_WAVE_KNOWLEDGE.md").read_text(encoding="utf-8")
    assert "docs/bazi_knowledge/geo_context/auxiliary_geo_first_wave_topic_v1.md" in manifest["created_from"]
    assert "docs/bazi_knowledge/packs/p37_auxiliary_geo_first_wave_knowledge_draft_seeds_v1.json" in manifest["created_from"]
    assert "docs/v19/V19_P37_AUXILIARY_GEO_FIRST_WAVE_KNOWLEDGE.md" in manifest["created_from"]
    assert "神煞、纳音、空亡、辅助柱默认 archive-first" in topic
    manifest_pack = next(row for row in manifest["content_packs"] if row["pack_id"] == pack["pack_id"])
    assert manifest_pack["draft_count"] == 30


def test_p38_answer_governance_first_wave_new_knowledge_pack_is_cataloged() -> None:
    root = Path(__file__).resolve().parents[2]
    pack = json.loads((root / "docs/bazi_knowledge/packs/p38_answer_governance_first_wave_knowledge_draft_seeds_v1.json").read_text(encoding="utf-8"))
    topic = (root / "docs/bazi_knowledge/answer_expression/answer_governance_first_wave_topic_v1.md").read_text(encoding="utf-8")
    taxonomy = (root / "docs/bazi_knowledge/catalog/bazi_knowledge_taxonomy_master_zh_v1.md").read_text(encoding="utf-8")
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    drafts = pack["knowledge_drafts"]
    titles = {row["title"] for row in drafts}

    assert pack["pack_id"] == "p38.answer_governance_first_wave_knowledge_pack.v1"
    assert len(drafts) == 28
    assert {row["domain"] for row in drafts} == {"answer_expression", "lab", "rule_db"}
    assert {row["risk_level"] for row in drafts} == {"R0", "R1"}
    assert {row["category"] for row in drafts} == {
        "answer_boundary",
        "answer_feedback",
        "answer_safety",
        "answer_style",
        "review_ui",
        "review_ui_boundary",
        "rule_db_gate",
        "rule_db_gate_boundary",
    }
    for title in [
        "预测断语过滤存在",
        "预测断语替换边界",
        "时间层不改写表达边界",
        "领域安全降级边界",
        "用户反馈不改规则边界",
        "失败归因展示边界",
        "合成评估报告边界",
        "智能门禁报告边界",
        "回滚谱系边界",
        "自动审批禁用边界",
    ]:
        assert title in titles
    assert "回答表达与治理细化第一批" in taxonomy
    assert "不输出内部字段" in (root / "docs/v19/V19_P38_ANSWER_GOVERNANCE_FIRST_WAVE_KNOWLEDGE.md").read_text(encoding="utf-8")
    assert "不输出预测" in topic
    assert "不自动批准" in topic
    assert "docs/bazi_knowledge/answer_expression/answer_governance_first_wave_topic_v1.md" in manifest["created_from"]
    assert "docs/bazi_knowledge/packs/p38_answer_governance_first_wave_knowledge_draft_seeds_v1.json" in manifest["created_from"]
    assert "docs/v19/V19_P38_ANSWER_GOVERNANCE_FIRST_WAVE_KNOWLEDGE.md" in manifest["created_from"]
    assert manifest["content_packs"][-1]["pack_id"] == pack["pack_id"]
    assert manifest["content_packs"][-1]["draft_count"] == 28


def test_p39_rule_conversion_validation_first_wave_batches_all_eligible_knowledge() -> None:
    from v19.synthetic_validation import build_p39_rule_conversion_candidates

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    registry = build_p39_rule_conversion_candidates()
    by_knowledge_id = {row["knowledge_id"]: row for row in registry["candidates"]}

    assert registry["status"] == "rule_conversion_candidates_ready_no_activation"
    assert registry["summary"]["draft_count"] == 436
    assert registry["summary"]["eligible_candidate_count"] == 348
    assert registry["summary"]["blocked_count"] == 88
    assert registry["summary"]["engine_enabled_count"] == 0
    assert registry["summary"]["activation_updated_count"] == 0
    assert registry["summary"]["by_risk"] == {"R0": 16, "R1": 146, "R2": 186}
    assert registry["summary"]["blocked_by_risk"] == {"R3": 76, "R4": 12}
    assert registry["summary"]["by_conversion_mode"]["condition_model_candidate"] == 268
    assert registry["summary"]["by_conversion_mode"]["answer_expression_contract"] == 22
    assert registry["summary"]["by_conversion_mode"]["governance_gate_contract"] == 14
    assert registry["summary"]["by_conversion_mode"]["metadata_boundary_rule"] == 11
    assert all(row["engine_enabled"] is False for row in registry["candidates"])
    assert all(row["activation_allowed"] is False for row in registry["candidates"])
    assert all(row["risk_level"] in {"R0", "R1", "R2"} for row in registry["candidates"])
    assert all(row["risk_level"] in {"R3", "R4"} for row in registry["blocked"])
    for knowledge_id in [
        "p32.interaction.shangguan_generate_wealth.mechanism_boundary",
        "p33.pattern.month_command_source.existence",
        "p35.branch.liuhe.existence",
        "p38.answer.plain_language.existence",
    ]:
        assert knowledge_id in by_knowledge_id
        assert by_knowledge_id[knowledge_id]["condition_axes_required"]
        assert by_knowledge_id[knowledge_id]["forbidden_outputs"]

    assert "docs/v19/V19_P39_RULE_CONVERSION_VALIDATION_FIRST_WAVE.md" in manifest["created_from"]
    assert manifest["p39_rule_conversion_validation_first_wave"]["eligible_candidate_count"] == 348
    assert manifest["p39_rule_conversion_validation_first_wave"]["blocked_count"] == 88
    assert manifest["p39_rule_conversion_validation_first_wave"]["engine_enabled_count"] == 0
    assert "P39_RULE_CONVERSION_VALIDATION_FIRST_WAVE" in manifest["guardrails"]


def test_p39_rule_conversion_eval_dataset_and_regression_validate_candidates() -> None:
    from v19.synthetic_validation import build_p39_rule_conversion_eval_dataset, run_p39_rule_conversion_regression

    dataset = build_p39_rule_conversion_eval_dataset()
    regression = run_p39_rule_conversion_regression()
    samples_by_candidate = {}
    for sample in dataset["samples"]:
        samples_by_candidate.setdefault(sample["source_candidate_rule_id"], []).append(sample)

    assert dataset["status"] == "eval_dataset_ready_no_rule_activation"
    assert dataset["summary"]["candidate_count"] == 348
    assert dataset["summary"]["sample_count"] == 1392
    assert dataset["summary"]["min_samples_per_candidate"] == 4
    assert dataset["summary"]["activation_updated_count"] == 0
    assert dataset["summary"]["by_polarity"] == {
        "positive": 348,
        "negative": 348,
        "distractor_time": 348,
        "distractor_hidden": 348,
    }
    assert dataset["summary"]["by_sample_type"] == {
        "positive_contract": 348,
        "negative_missing_condition_axis": 348,
        "distractor_time_layer": 348,
        "distractor_hidden_layer": 348,
    }
    assert all(len(rows) == 4 for rows in samples_by_candidate.values())
    assert all({"case_id", "source_candidate_rule_id", "knowledge_id", "polarity", "expected_signal", "forbidden_signals", "expected_question_keys", "forbidden_text", "condition_axes_expected", "audit_tags"} <= set(sample) for sample in dataset["samples"])
    assert all(sample["expected_signal"] for sample in dataset["samples"] if sample["sample_type"] == "positive_contract")
    assert all(sample["forbidden_signals"] for sample in dataset["samples"] if sample["sample_type"] != "positive_contract")

    assert regression["status"] == "pass"
    assert regression["summary"]["candidate_count"] == 348
    assert regression["summary"]["blocked_count"] == 88
    assert regression["summary"]["sample_count"] == 1392
    assert regression["summary"]["candidate_failed"] == 0
    assert regression["summary"]["sample_failed"] == 0
    assert regression["summary"]["false_positive_count"] == 0
    assert regression["summary"]["forbidden_text_failure_count"] == 0
    assert regression["summary"]["engine_enabled_count"] == 0
    assert regression["summary"]["activation_updated_count"] == 0


def test_p40_rule_audit_applies_safe_contracts_and_queues_condition_models() -> None:
    from v19.synthetic_validation import build_p40_framework_rule_registry, build_p40_rule_audit_report

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    audit = build_p40_rule_audit_report()
    registry = build_p40_framework_rule_registry()

    assert audit["status"] == "rule_audit_ready"
    assert audit["summary"]["p39_regression_status"] == "pass"
    assert audit["summary"]["candidate_count"] == 348
    assert audit["summary"]["blocked_high_risk_count"] == 88
    assert audit["summary"]["audit_failed_count"] == 0
    assert audit["summary"]["framework_contract_ready_count"] == 80
    assert audit["summary"]["condition_synthetic_required_count"] == 268
    assert audit["summary"]["engine_enabled_count"] == 0
    assert audit["summary"]["activation_updated_count"] == 0
    assert audit["summary"]["by_audit_status"] == {
        "framework_contract_ready": 80,
        "condition_synthetic_required": 268,
    }
    assert audit["summary"]["by_application_lane"] == {
        "answer_governance_framework": 22,
        "metadata_seed_framework": 31,
        "condition_model_framework_queue": 268,
        "metadata_boundary_framework": 11,
        "archive_neutral_tag_framework": 2,
        "review_gate_framework": 14,
    }

    assert registry["status"] == "framework_registry_ready_no_runtime_activation"
    assert registry["summary"]["framework_registered_count"] == 348
    assert registry["summary"]["framework_contract_applied_count"] == 80
    assert registry["summary"]["condition_model_queue_count"] == 268
    assert registry["summary"]["condition_model_queue_validated_count"] == 268
    assert registry["summary"]["engine_enabled_count"] == 0
    assert registry["summary"]["activation_updated_count"] == 0
    assert registry["summary"]["runtime_mutation"] is False
    assert registry["summary"]["by_application_status"] == {
        "framework_contract_applied": 80,
        "condition_model_queue_validated": 268,
    }
    assert all(row["engine_enabled"] is False for row in registry["items"])
    assert all(row["activation_allowed"] is False for row in registry["items"])
    assert "docs/v19/V19_P40_RULE_AUDIT_APPLICATION.md" in manifest["created_from"]
    assert manifest["p40_rule_audit_application"]["framework_registered_count"] == 348
    assert manifest["p40_rule_audit_application"]["condition_model_queue_count"] == 268
    assert manifest["p40_rule_audit_application"]["framework_contract_applied_count"] == 80
    assert "P40_RULE_AUDIT_APPLICATION" in manifest["guardrails"]


def test_p40_condition_model_synthetic_validation_passes_before_framework_queue() -> None:
    from v19.synthetic_validation import (
        build_p40_condition_model_synthetic_dataset,
        run_p40_rule_audit_application_regression,
    )

    dataset = build_p40_condition_model_synthetic_dataset()
    regression = run_p40_rule_audit_application_regression()

    assert dataset["status"] == "condition_synthetic_dataset_ready_no_activation"
    assert dataset["summary"]["source_candidate_count"] == 268
    assert dataset["summary"]["sample_count"] == 1072
    assert dataset["summary"]["min_samples_per_candidate"] == 4
    assert dataset["summary"]["activation_updated_count"] == 0
    assert dataset["summary"]["by_sample_type"] == {
        "positive_all_axes_present": 268,
        "negative_missing_action_path": 268,
        "distractor_time_only": 268,
        "distractor_hidden_only": 268,
    }
    assert dataset["summary"]["by_polarity"] == {
        "positive": 268,
        "negative": 268,
        "distractor_time": 268,
        "distractor_hidden": 268,
    }
    assert all(sample["expected_signal"] for sample in dataset["samples"] if sample["sample_type"] == "positive_all_axes_present")
    assert all(sample["forbidden_signals"] for sample in dataset["samples"] if sample["sample_type"] != "positive_all_axes_present")

    assert regression["status"] == "pass"
    assert regression["summary"]["candidate_count"] == 348
    assert regression["summary"]["blocked_high_risk_count"] == 88
    assert regression["summary"]["framework_registered_count"] == 348
    assert regression["summary"]["framework_contract_applied_count"] == 80
    assert regression["summary"]["condition_model_queue_count"] == 268
    assert regression["summary"]["condition_synthetic_sample_count"] == 1072
    assert regression["summary"]["audit_failed_count"] == 0
    assert regression["summary"]["condition_synthetic_failed_count"] == 0
    assert regression["summary"]["false_positive_count"] == 0
    assert regression["summary"]["engine_enabled_count"] == 0
    assert regression["summary"]["activation_updated_count"] == 0
    assert regression["summary"]["runtime_mutation"] is False


def test_p41_condition_topic_batches_cover_all_validated_condition_models() -> None:
    from v19.synthetic_validation import build_p41_condition_topic_batches, build_p41_smart_gate_candidate_batches

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    batches = build_p41_condition_topic_batches()
    gate = build_p41_smart_gate_candidate_batches()

    assert batches["status"] == "condition_topic_batches_ready"
    assert batches["summary"]["p40_regression_status"] == "pass"
    assert batches["summary"]["topic_batch_count"] == 6
    assert batches["summary"]["condition_candidate_count"] == 268
    assert batches["summary"]["assigned_candidate_count"] == 268
    assert batches["summary"]["activation_updated_count"] == 0
    assert batches["summary"]["engine_enabled_count"] == 0
    assert batches["summary"]["by_topic_lane"] == {
        "ten_god_mechanism": 93,
        "branch_time_activation": 74,
        "wealth_career_bridge": 38,
        "pattern_structure": 30,
        "core_strength_foundation": 20,
        "blind_lifa_palace": 13,
    }
    assert all(row["minimum_samples_per_candidate"] == 10 for row in batches["batches"])
    assert all(row["engine_enabled"] is False for row in batches["batches"])

    assert gate["status"] == "smart_gate_candidate_batches_ready_no_activation"
    assert gate["summary"]["topic_batch_count"] == 6
    assert gate["summary"]["gate_candidate_count"] == 268
    assert gate["summary"]["deep_sample_count"] == 2680
    assert gate["summary"]["ready_batch_count"] == 6
    assert gate["summary"]["blocked_batch_count"] == 0
    assert gate["summary"]["engine_enabled_count"] == 0
    assert gate["summary"]["activation_updated_count"] == 0
    assert gate["summary"]["runtime_mutation"] is False
    assert all(row["readiness_status"] == "smart_gate_candidate_ready" for row in gate["batches"])
    assert "docs/v19/V19_P41_CONDITION_TOPIC_DEEP_VALIDATION.md" in manifest["created_from"]
    assert manifest["p41_condition_topic_deep_validation"]["smart_gate_candidate_count"] == 268
    assert manifest["p41_condition_topic_deep_validation"]["topic_lanes"]["ten_god_mechanism"] == 93
    assert "P41_CONDITION_TOPIC_DEEP_VALIDATION" in manifest["guardrails"]


def test_p41_condition_deep_eval_dataset_and_regression_are_strict() -> None:
    from v19.synthetic_validation import build_p41_condition_deep_eval_dataset, run_p41_topic_batch_application_regression

    dataset = build_p41_condition_deep_eval_dataset()
    regression = run_p41_topic_batch_application_regression()

    assert dataset["status"] == "condition_deep_eval_dataset_ready_no_activation"
    assert dataset["summary"]["topic_batch_count"] == 6
    assert dataset["summary"]["condition_candidate_count"] == 268
    assert dataset["summary"]["sample_count"] == 2680
    assert dataset["summary"]["min_samples_per_candidate"] == 10
    assert dataset["summary"]["activation_updated_count"] == 0
    assert dataset["summary"]["engine_enabled_count"] == 0
    assert dataset["summary"]["by_topic_lane"] == {
        "ten_god_mechanism": 930,
        "branch_time_activation": 740,
        "wealth_career_bridge": 380,
        "pattern_structure": 300,
        "core_strength_foundation": 200,
        "blind_lifa_palace": 130,
    }
    assert dataset["summary"]["by_polarity"] == {
        "positive": 804,
        "negative": 1340,
        "distractor_time": 268,
        "distractor_hidden": 268,
    }
    assert dataset["summary"]["by_sample_type"] == {
        "positive_all_axes_present": 268,
        "positive_rescue_path_present": 268,
        "positive_same_layer_action_present": 268,
        "negative_missing_source_layer": 268,
        "negative_missing_action_path": 268,
        "negative_capacity_insufficient": 268,
        "negative_cross_layer_no_action": 268,
        "negative_relation_name_no_transformation": 268,
        "distractor_time_trigger_only": 268,
        "distractor_hidden_stem_only": 268,
    }
    assert all(sample["expected_signal"] for sample in dataset["samples"] if sample["sample_type"].startswith("positive_"))
    assert all(sample["forbidden_signals"] for sample in dataset["samples"] if not sample["sample_type"].startswith("positive_"))

    assert regression["status"] == "pass"
    assert regression["summary"]["topic_batch_count"] == 6
    assert regression["summary"]["gate_candidate_count"] == 268
    assert regression["summary"]["deep_sample_count"] == 2680
    assert regression["summary"]["ready_batch_count"] == 6
    assert regression["summary"]["blocked_batch_count"] == 0
    assert regression["summary"]["engine_enabled_count"] == 0
    assert regression["summary"]["activation_updated_count"] == 0
    assert regression["summary"]["runtime_mutation"] is False


def test_p42_smart_gate_audit_accelerates_low_risk_and_shadows_r2() -> None:
    from v19.synthetic_validation import build_p42_framework_gate_plan, build_p42_smart_gate_audit

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    audit = build_p42_smart_gate_audit()
    plan = build_p42_framework_gate_plan()

    assert audit["status"] == "smart_gate_audit_ready"
    assert audit["summary"]["p41_regression_status"] == "pass"
    assert audit["summary"]["candidate_count"] == 268
    assert audit["summary"]["dry_run_candidate_count"] == 110
    assert audit["summary"]["shadow_scoring_candidate_count"] == 158
    assert audit["summary"]["blocked_count"] == 0
    assert audit["summary"]["engine_enabled_count"] == 0
    assert audit["summary"]["activation_updated_count"] == 0
    assert audit["summary"]["by_gate_decision"] == {
        "dry_run_candidate": 110,
        "shadow_scoring_candidate": 158,
    }
    assert audit["summary"]["by_risk_level"] == {"R1": 108, "R2": 158, "R0": 2}
    assert all(row["gate_decision"] == "dry_run_candidate" for row in audit["items"] if row["risk_level"] in {"R0", "R1"})
    assert all(row["gate_decision"] == "shadow_scoring_candidate" for row in audit["items"] if row["risk_level"] == "R2")

    assert plan["status"] == "framework_gate_plan_ready_no_activation"
    assert plan["summary"]["candidate_count"] == 268
    assert plan["summary"]["dry_run_candidate_count"] == 110
    assert plan["summary"]["shadow_scoring_candidate_count"] == 158
    assert plan["summary"]["blocked_count"] == 0
    assert plan["summary"]["engine_enabled_count"] == 0
    assert plan["summary"]["activation_updated_count"] == 0
    assert plan["summary"]["runtime_mutation"] is False
    assert plan["summary"]["by_application_status"] == {
        "dry_run_planned": 110,
        "shadow_scoring_planned": 158,
    }
    assert "docs/v19/V19_P42_SMART_GATE_ACCELERATION.md" in manifest["created_from"]
    assert manifest["p42_smart_gate_acceleration"]["dry_run_candidate_count"] == 110
    assert manifest["p42_smart_gate_acceleration"]["shadow_scoring_candidate_count"] == 158
    assert "P42_SMART_GATE_ACCELERATION" in manifest["guardrails"]


def test_p42_smart_gate_eval_and_application_regression_pass_without_activation() -> None:
    from v19.synthetic_validation import build_p42_smart_gate_eval_dataset, run_p42_smart_gate_application_regression

    dataset = build_p42_smart_gate_eval_dataset()
    regression = run_p42_smart_gate_application_regression()

    assert dataset["status"] == "smart_gate_eval_dataset_ready_no_activation"
    assert dataset["summary"]["candidate_count"] == 268
    assert dataset["summary"]["sample_count"] == 1072
    assert dataset["summary"]["min_samples_per_candidate"] == 4
    assert dataset["summary"]["activation_updated_count"] == 0
    assert dataset["summary"]["engine_enabled_count"] == 0
    assert dataset["summary"]["by_sample_type"] == {
        "gate_decision_contract": 268,
        "risk_boundary_contract": 268,
        "forbidden_runtime_activation_contract": 268,
        "rollback_contract": 268,
    }
    assert dataset["summary"]["by_gate_decision"] == {
        "dry_run_candidate": 440,
        "shadow_scoring_candidate": 632,
    }

    assert regression["status"] == "pass"
    assert regression["summary"]["candidate_count"] == 268
    assert regression["summary"]["dry_run_candidate_count"] == 110
    assert regression["summary"]["shadow_scoring_candidate_count"] == 158
    assert regression["summary"]["blocked_count"] == 0
    assert regression["summary"]["engine_enabled_count"] == 0
    assert regression["summary"]["activation_updated_count"] == 0
    assert regression["summary"]["runtime_mutation"] is False


def test_p43_dry_run_shadow_eval_executes_without_answer_or_runtime_mutation() -> None:
    from v19.synthetic_validation import build_p43_dry_run_shadow_eval_dataset, run_p43_dry_run_shadow_scoring

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    dataset = build_p43_dry_run_shadow_eval_dataset()
    scoring = run_p43_dry_run_shadow_scoring()

    assert dataset["status"] == "dry_run_shadow_eval_dataset_ready_no_runtime_activation"
    assert dataset["summary"]["candidate_count"] == 268
    assert dataset["summary"]["dry_run_candidate_count"] == 110
    assert dataset["summary"]["shadow_scoring_candidate_count"] == 158
    assert dataset["summary"]["sample_count"] == 1072
    assert dataset["summary"]["min_samples_per_candidate"] == 4
    assert dataset["summary"]["engine_enabled_count"] == 0
    assert dataset["summary"]["activation_updated_count"] == 0
    assert dataset["summary"]["answer_mutation_count"] == 0
    assert dataset["summary"]["by_execution_mode"] == {
        "dry_run_internal": 440,
        "shadow_scoring_internal": 632,
    }
    assert dataset["summary"]["by_sample_type"] == {
        "internal_signal_contract": 268,
        "no_answer_mutation_contract": 268,
        "forbidden_text_contract": 268,
        "rollback_contract": 268,
    }

    assert scoring["status"] == "pass"
    assert scoring["summary"]["candidate_count"] == 268
    assert scoring["summary"]["dry_run_candidate_count"] == 110
    assert scoring["summary"]["shadow_scoring_candidate_count"] == 158
    assert scoring["summary"]["sample_count"] == 1072
    assert scoring["summary"]["sample_failed"] == 0
    assert scoring["summary"]["false_positive_count"] == 0
    assert scoring["summary"]["forbidden_text_failure_count"] == 0
    assert scoring["summary"]["answer_mutation_count"] == 0
    assert scoring["summary"]["rollback_ready_count"] == 268
    assert scoring["summary"]["engine_enabled_count"] == 0
    assert scoring["summary"]["activation_updated_count"] == 0
    assert "docs/v19/V19_P43_DRY_RUN_SHADOW_SCORING.md" in manifest["created_from"]
    assert manifest["p43_dry_run_shadow_scoring"]["dry_run_passed_count"] == 110
    assert manifest["p43_dry_run_shadow_scoring"]["shadow_scored_count"] == 158
    assert "P43_DRY_RUN_SHADOW_SCORING" in manifest["guardrails"]


def test_p43_feedback_ledger_and_execution_regression_are_ready() -> None:
    from v19.synthetic_validation import build_p43_feedback_ledger, run_p43_execution_regression

    ledger = build_p43_feedback_ledger()
    regression = run_p43_execution_regression()

    assert ledger["status"] == "feedback_ledger_ready_no_runtime_activation"
    assert ledger["summary"]["candidate_count"] == 268
    assert ledger["summary"]["dry_run_passed_count"] == 110
    assert ledger["summary"]["shadow_scored_count"] == 158
    assert ledger["summary"]["blocked_count"] == 0
    assert ledger["summary"]["engine_enabled_count"] == 0
    assert ledger["summary"]["answer_mutation_count"] == 0
    assert ledger["summary"]["runtime_mutation"] is False
    assert ledger["summary"]["by_feedback_status"] == {
        "dry_run_passed": 110,
        "shadow_scored": 158,
    }

    assert regression["status"] == "pass"
    assert regression["summary"]["candidate_count"] == 268
    assert regression["summary"]["dry_run_passed_count"] == 110
    assert regression["summary"]["shadow_scored_count"] == 158
    assert regression["summary"]["blocked_count"] == 0
    assert regression["summary"]["engine_enabled_count"] == 0
    assert regression["summary"]["answer_mutation_count"] == 0
    assert regression["summary"]["runtime_mutation"] is False


def test_p44_controlled_activation_candidates_have_rollback_and_no_runtime_activation() -> None:
    from v19.synthetic_validation import (
        build_p44_controlled_activation_packet,
        build_p44_rollback_manifest,
        run_p44_release_candidate_regression,
    )

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    packet = build_p44_controlled_activation_packet()
    rollback = build_p44_rollback_manifest()
    regression = run_p44_release_candidate_regression()

    assert packet["status"] == "controlled_activation_packet_ready_no_runtime_activation"
    assert packet["summary"]["source_candidate_count"] == 268
    assert packet["summary"]["activation_candidate_count"] == 110
    assert packet["summary"]["shadow_hold_count"] == 158
    assert packet["summary"]["ring0_canary_count"] == 2
    assert packet["summary"]["ring1_internal_count"] == 108
    assert packet["summary"]["engine_enabled_count"] == 0
    assert packet["summary"]["answer_mutation_count"] == 0
    assert packet["summary"]["activation_updated_count"] == 0
    assert packet["summary"]["runtime_mutation"] is False
    assert packet["summary"]["by_topic_lane"] == {
        "branch_time_activation": 42,
        "core_strength_foundation": 10,
        "ten_god_mechanism": 56,
        "wealth_career_bridge": 2,
    }
    assert packet["summary"]["shadow_hold_by_topic_lane"] == {
        "branch_time_activation": 32,
        "wealth_career_bridge": 36,
        "pattern_structure": 30,
        "core_strength_foundation": 10,
        "ten_god_mechanism": 37,
        "blind_lifa_palace": 13,
    }

    assert rollback["status"] == "rollback_manifest_ready_no_runtime_activation"
    assert rollback["summary"]["activation_candidate_count"] == 110
    assert rollback["summary"]["rollback_item_count"] == 110
    assert rollback["summary"]["missing_rollback_count"] == 0
    assert rollback["summary"]["engine_enabled_count"] == 0
    assert rollback["summary"]["answer_mutation_count"] == 0
    assert rollback["summary"]["runtime_mutation"] is False

    assert regression["status"] == "pass"
    assert regression["summary"]["activation_candidate_count"] == 110
    assert regression["summary"]["shadow_hold_count"] == 158
    assert regression["summary"]["ring0_canary_count"] == 2
    assert regression["summary"]["ring1_internal_count"] == 108
    assert regression["summary"]["rollback_item_count"] == 110
    assert regression["summary"]["missing_rollback_count"] == 0
    assert regression["summary"]["engine_enabled_count"] == 0
    assert regression["summary"]["answer_mutation_count"] == 0
    assert regression["summary"]["activation_updated_count"] == 0
    assert regression["summary"]["runtime_mutation"] is False
    assert "docs/v19/V19_P44_CONTROLLED_ACTIVATION_CANDIDATES.md" in manifest["created_from"]
    assert manifest["p44_controlled_activation_candidates"]["activation_candidate_count"] == 110
    assert manifest["p44_controlled_activation_candidates"]["rollback_item_count"] == 110
    assert "P44_CONTROLLED_ACTIVATION_CANDIDATES" in manifest["guardrails"]


def test_p45_canary_runtime_trial_is_isolated_and_reversible() -> None:
    from v19.synthetic_validation import run_p45_canary_release_regression

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    regression = run_p45_canary_release_regression()
    plan = regression["canary_plan"]
    trial = regression["canary_trial"]
    dataset = trial["eval_dataset"]

    assert plan["status"] == "canary_activation_plan_ready_isolated_runtime_only"
    assert plan["summary"]["p44_regression_status"] == "pass"
    assert plan["summary"]["ring0_canary_count"] == 2
    assert plan["summary"]["canary_runtime_enabled_count"] == 2
    assert plan["summary"]["production_engine_enabled_count"] == 0
    assert plan["summary"]["rollback_covered_count"] == 2
    assert plan["summary"]["kill_switch_covered_count"] == 2
    assert plan["summary"]["answer_mutation_count"] == 0
    assert plan["summary"]["production_runtime_mutation"] is False
    assert {row["knowledge_id"] for row in plan["canaries"]} == {
        "core.five_element_relations.v1",
        "core.stem_attributes.v1",
    }
    assert all(row["canary_engine_enabled"] is True for row in plan["canaries"])
    assert all(row["production_engine_enabled"] is False for row in plan["canaries"])

    assert dataset["status"] == "canary_eval_dataset_ready_isolated_runtime_only"
    assert dataset["summary"]["ring0_canary_count"] == 2
    assert dataset["summary"]["sample_count"] == 12
    assert dataset["summary"]["min_samples_per_canary"] == 6
    assert dataset["summary"]["canary_runtime_enabled_count"] == 2
    assert dataset["summary"]["production_engine_enabled_count"] == 0
    assert dataset["summary"]["answer_mutation_count"] == 0
    assert dataset["summary"]["by_sample_type"] == {
        "canary_internal_signal_contract": 2,
        "production_route_no_signal_contract": 2,
        "answer_text_no_mutation_contract": 2,
        "forbidden_text_contract": 2,
        "rollback_execution_contract": 2,
        "kill_switch_contract": 2,
    }

    assert trial["status"] == "pass"
    assert trial["summary"]["ring0_canary_count"] == 2
    assert trial["summary"]["sample_count"] == 12
    assert trial["summary"]["sample_failed"] == 0
    assert trial["summary"]["canary_internal_signal_count"] == 2
    assert trial["summary"]["production_signal_leak_count"] == 0
    assert trial["summary"]["forbidden_text_failure_count"] == 0
    assert trial["summary"]["rollback_ready_count"] == 2
    assert trial["summary"]["kill_switch_ready_count"] == 2
    assert trial["summary"]["canary_runtime_enabled_count"] == 2
    assert trial["summary"]["production_engine_enabled_count"] == 0
    assert trial["summary"]["answer_mutation_count"] == 0
    assert trial["summary"]["production_runtime_mutation"] is False

    assert regression["status"] == "pass"
    assert regression["summary"]["ring0_canary_count"] == 2
    assert regression["summary"]["sample_failed"] == 0
    assert regression["summary"]["production_engine_enabled_count"] == 0
    assert regression["summary"]["production_signal_leak_count"] == 0
    assert regression["summary"]["forbidden_text_failure_count"] == 0
    assert regression["summary"]["rollback_ready_count"] == 2
    assert regression["summary"]["kill_switch_ready_count"] == 2
    assert regression["summary"]["answer_mutation_count"] == 0
    assert regression["summary"]["production_runtime_mutation"] is False
    assert "docs/v19/V19_P45_CANARY_RUNTIME_TRIAL.md" in manifest["created_from"]
    assert manifest["p45_canary_runtime_trial"]["ring0_canary_count"] == 2
    assert manifest["p45_canary_runtime_trial"]["canary_runtime_enabled_count"] == 2
    assert manifest["p45_canary_runtime_trial"]["production_engine_enabled_count"] == 0
    assert "P45_CANARY_RUNTIME_TRIAL" in manifest["guardrails"]


def test_p46_rule_graph_orchestrator_selects_chart_specific_paths() -> None:
    from v19.rule_graph_orchestrator import orchestrate_rule_graph_paths

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    data = _agent_data_for_case(P11_GUIDED_SYNTHETIC_CASES[0])
    income = orchestrate_rule_graph_paths(
        data,
        question_key="q_income_stability",
        message="我的收入稳定性结构如何？",
        answer_kind="income_structure",
    )
    metadata = orchestrate_rule_graph_paths(
        data,
        question_key="q_element_flow_metadata",
        message="五行生克如何只按结构关系阅读？",
        answer_kind="metadata_boundary",
    )

    assert income["status"] == "rule_graph_paths_ready"
    assert income["chart_graph"]["node_count"] > 0
    assert income["chart_graph"]["edge_count"] > 0
    assert income["summary"]["candidate_count"] == 354
    assert income["summary"]["selected_count"] <= 8
    assert income["summary"]["engine_enabled_count"] == 0
    assert income["summary"]["answer_mutation_count"] == 0
    assert income["question_intent"]["intent"] == "income_structure"
    assert income["selected_paths"]
    assert {row["topic_lane"] for row in income["selected_paths"]} & {"wealth_career_bridge", "ten_god_mechanism"}
    assert all(row["score"] > 0 for row in income["selected_paths"])
    assert income["answer_audit"]["status"] == "pass"

    assert metadata["question_intent"]["intent"] == "metadata_boundary"
    assert metadata["summary"]["canary_selected_count"] == 2
    assert metadata["summary"]["runtime_allowed_count"] == 2
    assert {row["knowledge_id"] for row in metadata["selected_paths"] if row["runtime_allowed"]} == {
        "core.five_element_relations.v1",
        "core.stem_attributes.v1",
    }
    assert metadata["future_model_slots"]["gnn"].startswith("reserved")
    assert "docs/v19/V19_P46_RULE_GRAPH_ORCHESTRATOR.md" in manifest["created_from"]
    assert manifest["p46_rule_graph_orchestrator"]["engine_enabled_count"] == 0
    assert "P46_RULE_GRAPH_ORCHESTRATOR" in manifest["guardrails"]


def test_p46_guided_context_and_answer_carry_rule_graph_audit() -> None:
    from v19.bazi_guided_questions import build_guided_question_answer, guided_answer_to_plain_text

    data = _agent_data_for_case(P11_GUIDED_SYNTHETIC_CASES[0])
    context = data["guided_question_context"]
    answer = build_guided_question_answer(data, "q_element_flow_metadata", "五行生克如何只按结构关系阅读？")
    text = guided_answer_to_plain_text(answer, "zh")

    assert context["rule_graph_context"]["status"] == "rule_graph_paths_ready"
    assert context["rule_graph_context"]["summary"]["candidate_count"] == 354
    assert any(row.get("source") == "rule_graph_orchestrator" for row in context["signals"])
    assert "RULE_GRAPH_PATH_SELECTION" in context["guardrails"]
    assert answer["rule_graph_context"]["status"] == "rule_graph_paths_ready"
    assert answer["rule_graph_answer_audit"]["status"] == "pass"
    assert answer["retrieved_facts"]["rule_graph_context"]["answer_audit_status"] == "pass"
    assert answer["rule_graph_context"]["summary"]["engine_enabled_count"] == 0
    assert answer["rule_graph_context"]["summary"]["answer_mutation_count"] == 0
    assert "五行" in text or "结构" in text
    for forbidden in ["发财", "破财", "官非", "灾祸", "疾病", "应期", "必然", "一定"]:
        assert forbidden not in text


def test_p47_rule_graph_runtime_context_routes_measurement_chain() -> None:
    from v19.bazi_guided_questions import build_guided_question_answer
    from v19.llm import build_agent_messages
    from v19.rule_graph_runtime_context import rule_graph_runtime_context_to_prompt_context

    data = _agent_data_for_case(P11_GUIDED_SYNTHETIC_CASES[0])
    runtime_context = data["rule_graph_runtime_context"]
    answer = build_guided_question_answer(data, "q_income_stability", "我的收入稳定性结构如何？")
    prompt_messages = build_agent_messages(data, "我的收入稳定性结构如何？", [])
    compact = json.loads(prompt_messages[1]["content"].split("STRUCTURE_CONTEXT_JSON:\n", 1)[1])
    prompt_context = rule_graph_runtime_context_to_prompt_context(runtime_context)

    assert runtime_context["status"] == "rule_graph_runtime_context_ready"
    assert runtime_context["route_count"] >= 2
    assert {row["route_id"] for row in runtime_context["routes"]} >= {
        "primary_question_route",
        "income_structure_route",
        "structure_overview_route",
    }
    assert runtime_context["summary"]["candidate_count"] == 354
    assert runtime_context["summary"]["selected_path_count"] >= 8
    assert runtime_context["summary"]["engine_enabled_count"] == 0
    assert runtime_context["summary"]["answer_mutation_count"] == 0
    assert runtime_context["summary"]["runtime_mutation"] is False
    assert runtime_context["answer_audit"]["status"] == "pass"
    assert runtime_context["knowledge_route"]["selected_knowledge_ids"]
    assert runtime_context["knowledge_route"]["selected_rule_ids"]
    assert set(runtime_context["knowledge_route"]["by_topic_lane"]) & {"wealth_career_bridge", "ten_god_mechanism", "branch_time_activation"}
    assert all(row.get("selected_by_route") for row in runtime_context["selected_paths"])

    assert answer["rule_graph_runtime_context"]["status"] == "rule_graph_runtime_context_ready"
    assert answer["retrieved_facts"]["rule_graph_runtime_context"]["answer_audit_status"] == "pass"
    assert prompt_context["runtime_scope"] == "llm_context_route_hints_only_no_answer_mutation"
    assert prompt_context["evidence_bindings"]
    assert compact["rule_graph_runtime_context"]["selected_knowledge_ids"] == prompt_context["selected_knowledge_ids"]
    assert "USE_AS_ROUTE_HINTS_ONLY" in compact["rule_graph_runtime_context"]["guardrails"]


def test_p48_initial_questions_are_personalized_by_rule_graph_routes() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    first = _agent_data_for_case(P11_GUIDED_SYNTHETIC_CASES[0])["guided_question_context"]
    branch_heavy = _agent_data_for_case(P11_GUIDED_SYNTHETIC_CASES[3])["guided_question_context"]

    first_personalization = first["question_personalization_context"]
    branch_personalization = branch_heavy["question_personalization_context"]
    first_top = first["questions"][:6]
    branch_top = branch_heavy["questions"][:6]
    first_top_signature = [(row["key"], (row.get("label") or {}).get("zh", "")) for row in first_top]
    branch_top_signature = [(row["key"], (row.get("label") or {}).get("zh", "")) for row in branch_top]

    assert first_personalization["status"] == "ready"
    assert branch_personalization["status"] == "ready"
    assert first_personalization["source"] == "rule_graph_runtime_context"
    assert branch_personalization["source"] == "rule_graph_runtime_context"
    assert first_personalization["route_bucket_order"]
    assert branch_personalization["route_bucket_order"]
    assert {"branch_relation", "ten_god_interaction", "income_stability"} <= set(first_personalization["route_bucket_order"])
    assert {"branch_relation", "ten_god_interaction", "income_stability"} <= set(branch_personalization["route_bucket_order"])
    assert first_top_signature != branch_top_signature
    assert all((row.get("personalization") or {}).get("applied") is True for row in first_top[:5])
    assert all(int(row.get("personalized_score") or 0) >= int(row.get("score") or 0) for row in first_top + branch_top)
    assert "q_income_stability" in [row["key"] for row in first["questions"][:10]]
    assert "q_income_stability" in [row["key"] for row in branch_heavy["questions"][:10]]
    assert "RULE_GRAPH_PERSONALIZED_QUESTION_RANKING" in first["guardrails"]
    assert first_personalization["runtime_scope"] == "question_ranking_only_no_inference_mutation"
    assert "docs/v19/V19_P48_PERSONALIZED_QUESTION_ROUTING.md" in manifest["created_from"]
    assert manifest["p48_personalized_question_routing"]["answer_mutation_count"] == 0
    assert "P48_PERSONALIZED_QUESTION_ROUTING" in manifest["guardrails"]


def test_p49_route_aware_knowledge_retrieval_uses_rule_graph_context() -> None:
    from v19.bazi_guided_questions import build_guided_question_answer

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    branch_case = P11_GUIDED_SYNTHETIC_CASES[3]
    month_case = next(row for row in P11_GUIDED_SYNTHETIC_CASES if row.case_id == "syn.guided.p11.month_command_neutral_with_income_collision")
    branch_data = _agent_data_for_case(branch_case)
    month_data = _agent_data_for_case(month_case)
    branch_kc = branch_data["knowledge_context"]
    month_kc = month_data["knowledge_context"]
    branch_answer = build_guided_question_answer(branch_data, branch_case.question_key, branch_case.message)
    month_answer = build_guided_question_answer(month_data, month_case.question_key, month_case.message)

    assert branch_kc["mode"] == "reviewed_evidence_templates_with_rule_graph_route_bias"
    assert branch_kc["route_context"]["status"] == "ready"
    assert branch_kc["route_context"]["source"] == "rule_graph_runtime_context"
    assert branch_kc["route_context"]["runtime_scope"] == "knowledge_retrieval_route_bias_only_no_rule_activation"
    assert any(int(row.get("route_match_score") or 0) > 0 for row in branch_kc["items"])
    assert any(row.get("route_match_reasons") for row in branch_kc["items"])
    assert branch_kc["items"][0]["knowledge_id"] == "p10.branch_penalty_harm_break_boundary"
    assert "p10.branch_penalty_harm_break_boundary" in [row["knowledge_id"] for row in branch_answer["applied_knowledge"]]
    assert any(int(row.get("route_match_score") or 0) > 0 for row in branch_answer["applied_knowledge"])

    assert month_kc["route_context"]["status"] == "ready"
    assert month_kc["items"][0]["knowledge_id"] == "p10.month_command_season_not_verdict"
    assert "p10.month_command_season_not_verdict" in [row["knowledge_id"] for row in month_answer["applied_knowledge"]]
    assert int(month_kc["items"][0].get("route_match_score") or 0) <= 12
    assert manifest["p49_route_aware_knowledge_retrieval"]["route_bias_policy"]["generic_route_match_cap"] == 12
    assert "docs/v19/V19_P49_ROUTE_AWARE_KNOWLEDGE_RETRIEVAL.md" in manifest["created_from"]
    assert "P49_ROUTE_AWARE_KNOWLEDGE_RETRIEVAL" in manifest["guardrails"]


def test_p50_guided_answer_evidence_pack_unifies_answer_contexts() -> None:
    from v19.bazi_guided_questions import build_guided_question_answer
    from v19.guided_evidence_pack import evidence_pack_to_prompt_context
    from v19.server import _guided_answer_rewrite_messages

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    case = P11_GUIDED_SYNTHETIC_CASES[3]
    data = _agent_data_for_case(case)
    answer = build_guided_question_answer(data, case.question_key, case.message)
    pack = answer["evidence_pack"]
    prompt_context = evidence_pack_to_prompt_context(pack)
    rewrite_messages = _guided_answer_rewrite_messages(answer, case.message)
    rewrite_payload = json.loads(rewrite_messages[2]["content"].split("\n", 1)[1])

    assert pack["status"] == "ready"
    assert pack["question"]["question_key"] == case.question_key
    assert pack["question"]["answer_kind"] == answer["answer_kind"]
    assert pack["fact_evidence"]["present_fact_scopes"]
    assert pack["knowledge_evidence"]["applied_ids"]
    assert "p10.branch_penalty_harm_break_boundary" in pack["knowledge_evidence"]["applied_ids"]
    assert any(row["kind"] == "knowledge" for row in pack["evidence_bindings"])
    assert any(row["kind"] == "rule_graph_path" for row in pack["evidence_bindings"])
    assert pack["rule_graph_evidence"]["runtime_selected_knowledge_ids"]
    assert pack["summary"]["engine_enabled_count"] == 0
    assert pack["summary"]["answer_mutation_count"] == 0
    assert pack["summary"]["runtime_mutation"] is False
    assert pack["audit"]["status"] == "pass"
    assert "GUIDED_ANSWER_EVIDENCE_PACK" in pack["guardrails"]

    assert answer["retrieved_facts"]["evidence_pack"]["status"] == "ready"
    assert answer["retrieved_facts"]["evidence_pack"]["binding_count"] == len(pack["evidence_bindings"])
    assert prompt_context["runtime_scope"] == "llm_prompt_evidence_pack_context_only"
    assert prompt_context["bindings"]
    assert rewrite_payload["target_locale"] == "zh"
    assert rewrite_payload["evidence_pack"]["status"] == "ready"
    assert rewrite_payload["evidence_pack"]["bindings"]
    assert "docs/v19/V19_P50_GUIDED_ANSWER_EVIDENCE_PACK.md" in manifest["created_from"]
    assert manifest["p50_guided_answer_evidence_pack"]["answer_mutation_count"] == 0
    assert "P50_GUIDED_ANSWER_EVIDENCE_PACK" in manifest["guardrails"]


def test_p51_ui_surfaces_latest_framework_context() -> None:
    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    lab_html = (root / "v19/frontend/lab.html").read_text(encoding="utf-8")
    app_js = (root / "v19/frontend/assets/app.js").read_text(encoding="utf-8")
    oracle_html = (root / "v19/frontend/oracle.html").read_text(encoding="utf-8")
    oracle_js = (root / "v19/frontend/assets/oracle.js").read_text(encoding="utf-8")
    styles = (root / "v19/frontend/assets/styles.css").read_text(encoding="utf-8")

    assert "ruleGraphRoutePack" in lab_html
    assert "personalizedQuestionsPanel" in lab_html
    assert "guidedAnswerEvidencePack" in lab_html
    assert "renderRuleGraphRoutePack" in app_js
    assert "rule_graph_runtime_context" in app_js
    assert "question_personalization_context" in app_js
    assert "route_match_score" in app_js
    assert "evidence_pack" in app_js

    assert "answerEvidenceSummary" in oracle_html
    assert "personalized-question-chip" in oracle_js
    assert "question-personalization" in oracle_js
    assert "renderAnswerEvidenceSummary" in oracle_js
    assert "evidence_pack" in oracle_js
    assert "answer-evidence-summary" in styles

    assert "docs/v19/V19_P51_UI_FRAMEWORK_ALIGNMENT.md" in manifest["created_from"]
    assert manifest["p51_ui_framework_alignment"]["runtime_scope"] == "ui_visibility_only_no_inference_or_answer_mutation"
    assert manifest["p51_ui_framework_alignment"]["answer_mutation_count"] == 0
    assert "P51_UI_FRAMEWORK_ALIGNMENT" in manifest["guardrails"]


def test_p52_initial_question_recommendations_are_more_chart_specific() -> None:
    from fastapi.testclient import TestClient

    from v19.server import app

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    oracle_js = (root / "v19/frontend/assets/oracle.js").read_text(encoding="utf-8")

    contexts = [_agent_data_for_case(case)["guided_question_context"] for case in P11_GUIDED_SYNTHETIC_CASES[:12]]
    signatures = [tuple(row["key"] for row in context["questions"][:5]) for context in contexts]
    by_case = {case.case_id: context for case, context in zip(P11_GUIDED_SYNTHETIC_CASES[:12], contexts)}

    assert len(set(signatures)) >= 6
    assert by_case["syn.guided.three_meeting_boundary"]["questions"][0]["key"] == "q_three_harmony_context"
    assert by_case["syn.guided.income_three_harmony_binding"]["questions"][0]["key"] == "q_three_harmony_context"
    assert by_case["syn.guided.income_wealth_missing_unstable"]["questions"][0]["key"] == "q_vault_structure"
    assert by_case["syn.guided.income_wealth_disrupted_volatility"]["questions"][0]["key"] == "q_branch_relation_detail"
    assert all(len({(row.get("source_signal_category") or row["key"]) for row in context["questions"][:5]}) >= 4 for context in contexts)

    client = TestClient(app)
    first_preview = client.post(
        "/api/agent/structure?role=admin",
        json={"birth_input": {"year": 1990, "month": 5, "day": 12, "hour": 10, "gender": "unknown", "calendar": "solar"}, "selected_year": 2026},
    ).json()["data"]
    second_preview = client.post(
        "/api/agent/structure?role=admin",
        json={"birth_input": {"year": 1988, "month": 11, "day": 23, "hour": 1, "gender": "unknown", "calendar": "solar"}, "selected_year": 2026},
    ).json()["data"]
    first_label = first_preview["guided_question_context"]["questions"][0]["label"]["zh"]
    second_label = second_preview["guided_question_context"]["questions"][0]["label"]["zh"]
    assert first_preview["inference_context"]["runtime_scope"] == "structure_preview_question_routing_signal_only"
    assert first_label != second_label
    assert "当前命中的" in first_label
    assert "当前命中的" in second_label

    assert "backendPersonalizedQuestionKeys" in oracle_js
    assert "return backendOrdered.slice(0, 5)" in oracle_js
    assert "personalized_score ?? item.score" in oracle_js
    assert "docs/v19/V19_P52_INITIAL_QUESTION_DIVERSITY_FIX.md" in manifest["created_from"]
    assert manifest["p52_initial_question_diversity_fix"]["runtime_scope"] == "initial_question_ordering_only_no_inference_or_answer_mutation"
    assert manifest["p52_initial_question_diversity_fix"]["answer_mutation_count"] == 0
    assert "P52_INITIAL_QUESTION_DIVERSITY_FIX" in manifest["guardrails"]


def test_p70_rule_graph_can_route_runtime_rule_db_records(monkeypatch) -> None:
    import v19.rule_graph_orchestrator as rgo

    sample_rule = {
        "rule_id": "v19.rule.test.runtime_income_path",
        "knowledge_id": "test.runtime_income_path",
        "title": "收入路径结构边界",
        "domain": "income_stability",
        "category": "income_path",
        "risk_level": "R1",
        "status": "active_in_rule_db",
        "engine_enabled": True,
        "engine_adapter_status": "available_for_structural_signal_adapter",
        "input_contract": {"required": ["chart", "inference_context.income_stability"]},
        "condition": {"conditions": {"keywords": ["收入", "财星", "食伤"]}, "structured_facts": {"candidate_signal": "output_to_wealth_path"}},
        "output_contract": {"is_prediction": False},
        "allowed_usage": ["rule_db", "engine_adapter_candidate"],
        "forbidden_usage": ["direct_fortune_output"],
    }
    candidate = rgo._rule_db_record_to_candidate(sample_rule)
    monkeypatch.setattr(rgo, "_runtime_rule_db_candidates", lambda: [candidate])

    case = P11_GUIDED_SYNTHETIC_CASES[0]
    data = _agent_data_for_case(case)
    report = rgo.orchestrate_rule_graph_paths(
        data,
        question_key="q_income_stability",
        message="我的收入稳定性结构如何？",
        answer_kind="income_structure",
        limit=12,
    )
    selected = report["selected_paths"]

    assert report["summary"]["runtime_rule_db_candidate_count"] == 1
    assert any(row["knowledge_id"] == "test.runtime_income_path" for row in selected)
    runtime_path = next(row for row in selected if row["knowledge_id"] == "test.runtime_income_path")
    assert runtime_path["source"] == "runtime_bazi_rule_db"
    assert runtime_path["topic_lane"] == "wealth_career_bridge"
    assert runtime_path["engine_enabled"] is True
    assert runtime_path["runtime_allowed"] is False
    assert runtime_path["framework_state"] == "rule_db_engine_available_route_only"
    assert report["answer_audit"]["status"] == "pass"


def test_p71_runtime_rule_db_categories_create_specific_guided_questions(monkeypatch) -> None:
    import v19.rule_graph_orchestrator as rgo

    sample_rule = {
        "rule_id": "v19.rule.test.runtime_income_collision",
        "knowledge_id": "test.runtime_income_collision",
        "title": "收入牵制结构边界",
        "domain": "income_stability",
        "category": "income_collision",
        "risk_level": "R2",
        "status": "active_in_rule_db",
        "engine_enabled": False,
        "engine_adapter_status": "candidate_waiting_synthetic_acceptance",
        "input_contract": {"required": ["chart", "inference_context.income_stability"]},
        "condition": {"conditions": {"keywords": ["收入", "财星", "牵制"]}, "structured_facts": {"candidate_signal": "wealth_visible_with_binding"}},
        "output_contract": {"is_prediction": False},
        "allowed_usage": ["rule_db", "shadow_signal_candidate"],
        "forbidden_usage": ["direct_fortune_output", "wealth_verdict"],
    }
    candidate = rgo._rule_db_record_to_candidate(sample_rule)
    monkeypatch.setattr(rgo, "_runtime_rule_db_candidates", lambda: [candidate])

    data = _agent_data_for_case(P11_GUIDED_SYNTHETIC_CASES[0])
    context = data["guided_question_context"]
    questions = context["questions"]
    by_key = {row["key"]: row for row in questions}

    assert "kbq_income_collision_route" in by_key
    question = by_key["kbq_income_collision_route"]
    assert question["source"] == "rule_graph_dynamic_question"
    assert question["source_knowledge_id"] == "test.runtime_income_collision"
    assert question["source_rule_category"] == "income_collision"
    assert question["source_framework_state"] == "rule_db_shadow_route_candidate"
    assert question["source_engine_enabled"] is False
    assert "财富断语" in question["label"]["zh"]
    assert (question.get("personalization") or {}).get("applied") is True
    assert question["runtime_scope"] == "runtime_rule_graph_question_hint_only_no_result_mutation"


def test_mainline_runtime_rule_db_readiness_audit_classifies_activation_pipeline() -> None:
    from v19.synthetic_validation import run_runtime_rule_db_readiness_regression

    result = run_runtime_rule_db_readiness_regression()
    audit = result["audit"]

    assert result["status"] == "pass"
    assert audit["status"] == "readiness_audit_only_no_activation"
    assert audit["summary"]["synthetic_gate_candidate_count"] == 1
    assert audit["summary"]["shadow_eval_candidate_count"] == 1
    assert audit["summary"]["adapter_fact_gap_count"] == 1
    assert audit["summary"]["blocked_count"] == 1
    assert audit["selected_for_next_synthetic_gate"][0]["knowledge_id"] == "ready.ten_god"
    assert audit["selected_for_next_synthetic_gate"][0]["synthetic_gate"] == "required"
    assert "ten_god_relation" in audit["eval_requirements"]
    assert "NO_ENGINE_ACTIVATION" in audit["guardrails"]


def test_mainline_runtime_rule_db_synthetic_gate_queue_builds_case_slots() -> None:
    from v19.synthetic_validation import run_runtime_rule_db_synthetic_gate_queue_regression

    result = run_runtime_rule_db_synthetic_gate_queue_regression()
    queue = result["queue"]

    assert result["status"] == "pass"
    assert queue["status"] == "synthetic_gate_queue_ready_no_activation"
    assert queue["candidate_count"] == 2
    assert queue["case_count"] == 16
    assert "NO_SYNTHETIC_CASE_AUTO_PASS" in queue["guardrails"]
    assert {case["polarity"] for case in queue["cases"]} == {
        "positive",
        "negative",
        "time_interference",
        "hidden_source_interference",
    }
    assert all("source_layer" in case["condition_axes_expected"] for case in queue["cases"])


def test_mainline_runtime_rule_db_synthetic_eval_dataset_is_runnable_contract() -> None:
    from v19.synthetic_validation import build_runtime_rule_db_synthetic_eval_dataset, run_runtime_rule_db_synthetic_eval_regression

    result = run_runtime_rule_db_synthetic_eval_regression()
    dataset = build_runtime_rule_db_synthetic_eval_dataset(
        [
            {
                "rule_id": "v19.rule.ready.ten_god",
                "knowledge_id": "ready.ten_god",
                "title": "ready.ten_god",
                "domain": "ten_god_relation",
                "category": "ten_god_interaction",
                "risk_level": "R1",
                "confidence": 0.82,
                "engine_enabled": False,
                "input_contract": {"required": ["chart"]},
                "condition": {"structured_facts": {"candidate_signal": "ready.ten_god"}},
                "allowed_usage": ["rule_db"],
                "forbidden_usage": [],
            }
        ],
        limit=5,
    )

    assert result["status"] == "pass"
    assert dataset["status"] == "runtime_rule_db_eval_dataset_ready_no_activation"
    assert dataset["summary"]["sample_count"] == 8
    assert dataset["summary"]["min_samples_per_rule"] == 8
    assert dataset["summary"]["by_polarity"] == {
        "positive": 3,
        "negative": 3,
        "time_interference": 1,
        "hidden_source_interference": 1,
    }
    assert all(sample["chart"]["status"] == "ok" for sample in dataset["samples"])
    assert all(sample["expected_signal"] for sample in dataset["samples"] if sample["polarity"] == "positive")
    assert all(sample["forbidden_signals"] for sample in dataset["samples"] if sample["polarity"] != "positive")
    assert result["summary"]["activation_updated_count"] == 0


def test_mainline_runtime_rule_db_synthetic_route_regression_blocks_false_positive_routes() -> None:
    from v19.synthetic_validation import run_runtime_rule_db_synthetic_route_regression

    result = run_runtime_rule_db_synthetic_route_regression()

    assert result["status"] == "shadow_route_pass_no_activation"
    assert result["summary"]["sample_count"] == 16
    assert result["summary"]["false_positive_count"] == 0
    assert result["summary"]["missed_positive_count"] == 0
    assert result["summary"]["activation_updated_count"] == 0
    assert all(route["matched_route_ids"] for route in result["routes"] if route["polarity"] == "positive")
    assert all(not route["matched_route_ids"] for route in result["routes"] if route["polarity"] != "positive")
    assert "SHADOW_ROUTE_ONLY" in result["guardrails"]


def test_p31c_priority_topic_conversion_registry_batches_partial_topics() -> None:
    from v19.synthetic_validation import build_p31c_priority_topic_conversion_registry

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    registry = build_p31c_priority_topic_conversion_registry()
    by_model = {row["model_id"]: row for row in registry["models"]}

    assert registry["status"] == "priority_topic_conversion_ready_no_activation"
    assert registry["summary"]["high_priority_partial_count"] == 155
    assert registry["summary"]["existing_ten_god_chain_case_count"] == 24
    assert registry["summary"]["new_condition_model_count"] == 28
    assert registry["summary"]["eval_sample_requirement_count"] == 112
    assert registry["summary"]["activation_updated_count"] == 0
    assert registry["summary"]["by_lane"] == {
        "career_domain_bridge": 4,
        "palace_domain_bridge": 1,
        "pattern_quality": 4,
        "regular_pattern": 10,
        "time_activation": 7,
        "wealth_domain_bridge": 2,
    }
    assert registry["eval_dataset"]["by_polarity"] == {
        "positive": 28,
        "negative": 28,
        "distractor_time": 28,
        "distractor_hidden": 28,
    }
    for model_id in [
        "p31c.pattern.regular.zhengguan",
        "p31c.pattern.quality.formation_break",
        "p31c.time.luck_to_natal",
        "p31c.time.ten_god_activation",
        "p31c.domain.wealth_income_structure",
        "p31c.domain.career_official_kill",
    ]:
        assert model_id in by_model
        assert by_model[model_id]["activation_allowed"] is False
        assert "fortune" in by_model[model_id]["forbidden_outputs"]
    assert "docs/v19/V19_P31C_PRIORITY_TOPIC_CONVERSION_REGISTRY.md" in manifest["created_from"]
    assert manifest["p31c_priority_topic_conversion_registry"]["new_condition_model_count"] == 28
    assert manifest["p31c_priority_topic_conversion_registry"]["eval_sample_count"] == 112


def test_p31c_priority_topic_regression_is_strict_and_no_activation() -> None:
    from v19.synthetic_validation import run_p31c_priority_topic_regression

    regression = run_p31c_priority_topic_regression()

    assert regression["status"] == "pass"
    assert regression["summary"]["model_count"] == 28
    assert regression["summary"]["sample_count"] == 112
    assert regression["summary"]["sample_failed"] == 0
    assert regression["summary"]["false_positive_count"] == 0
    assert regression["summary"]["forbidden_text_failure_count"] == 0
    assert regression["summary"]["activation_updated_count"] == 0
    assert regression["summary"]["by_polarity"] == {
        "positive": 28,
        "negative": 28,
        "distractor_time": 28,
        "distractor_hidden": 28,
    }
    assert all(row["status"] == "pass" for row in regression["models"])
    assert all(row["sample_count"] == 4 for row in regression["models"])


def test_p31d_priority_topic_smart_gate_dry_run_selects_low_risk_only() -> None:
    from v19.synthetic_validation import run_p31d_priority_topic_smart_gate

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    gate = run_p31d_priority_topic_smart_gate()

    assert gate["status"] == "dry_run_ready"
    assert gate["summary"]["model_count"] == 28
    assert gate["summary"]["selected_shadow_proposal_count"] == 22
    assert gate["summary"]["blocked_count"] == 6
    assert gate["summary"]["activation_updated_count"] == 0
    assert gate["summary"]["p31c_regression_status"] == "pass"
    assert gate["summary"]["blocked_by_reason"] == {"risk_above_shadow_gate": 6}
    assert gate["summary"]["selected_by_lane"] == {
        "regular_pattern": 10,
        "time_activation": 7,
        "wealth_domain_bridge": 2,
        "career_domain_bridge": 2,
        "palace_domain_bridge": 1,
    }
    assert {row["risk_level"] for row in gate["selected"]} <= {"R1", "R2"}
    assert {row["risk_level"] for row in gate["blocked"]} == {"R3"}
    assert all(row["activation_allowed"] is False for row in gate["selected"] + gate["blocked"])
    assert manifest["p31d_priority_topic_smart_gate"]["selected_shadow_proposal_count"] == 22
    assert manifest["p31d_priority_topic_smart_gate"]["activation_allowed"] is False
    assert "docs/v19/V19_P31D_PRIORITY_TOPIC_SMART_GATE.md" in manifest["created_from"]


def test_p31e_priority_topic_rule_proposal_generation_creates_validation_ready_only(tmp_path, monkeypatch) -> None:
    import v19.lab_interfaces as lab
    from v19.synthetic_validation import run_p31e_priority_topic_rule_proposal_generation

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    generated = run_p31e_priority_topic_rule_proposal_generation()
    proposals = lab.list_bazi_rule_proposals()["items"]

    assert generated["status"] == "proposal_generation_ready"
    assert generated["summary"]["gate_selected_count"] == 22
    assert generated["summary"]["created_rule_proposal_count"] == 22
    assert generated["summary"]["validation_ready_count"] == 22
    assert generated["summary"]["validation_failed_count"] == 0
    assert generated["summary"]["activation_updated_count"] == 0
    assert generated["summary"]["approval_mutation"] is False
    assert generated["summary"]["version_mutation"] is False
    assert generated["summary"]["runtime_mutation"] is False
    assert generated["summary"]["by_domain"] == {
        "structural_relation": 13,
        "time_structure": 7,
        "income_stability": 2,
    }
    assert generated["summary"]["by_lane"] == {
        "regular_pattern": 10,
        "time_activation": 7,
        "wealth_domain_bridge": 2,
        "career_domain_bridge": 2,
        "palace_domain_bridge": 1,
    }
    assert len(proposals) == 22
    assert {row["status"] for row in proposals} == {"validation_ready"}
    assert all((row["validation"] or {}).get("passed") is True for row in proposals)
    assert all("NO_RUNTIME_INFERENCE_MUTATION" in row["guardrails"] for row in proposals)
    assert all((row["output_contract"] or {}).get("is_prediction") is False for row in proposals)
    assert all(row["rule_id"].startswith("v19.p31e.") for row in proposals)
    assert manifest["p31e_priority_topic_rule_proposals"]["created_rule_proposal_count"] == 22
    assert manifest["p31e_priority_topic_rule_proposals"]["runtime_mutation"] is False
    assert "docs/v19/V19_P31E_PRIORITY_TOPIC_RULE_PROPOSALS.md" in manifest["created_from"]


def test_p31f_priority_topic_review_packet_wraps_validated_proposals_only(tmp_path, monkeypatch) -> None:
    import v19.lab_interfaces as lab
    from v19.synthetic_validation import run_p31f_priority_topic_review_packet

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    packetized = run_p31f_priority_topic_review_packet()
    validation_runs = lab.list_proposal_validation_runs()
    review_packets = lab.list_proposal_review_packets()
    proposals = lab.list_bazi_rule_proposals()["items"]

    assert packetized["status"] == "review_packet_ready"
    assert packetized["summary"]["proposal_count"] == 22
    assert packetized["summary"]["validation_run_count"] == 1
    assert packetized["summary"]["validation_passed"] == 22
    assert packetized["summary"]["validation_failed"] == 0
    assert packetized["summary"]["review_packet_count"] == 1
    assert packetized["summary"]["review_packet_item_count"] == 22
    assert packetized["summary"]["approval_mutation"] is False
    assert packetized["summary"]["approval_preflight_mutation"] is False
    assert packetized["summary"]["version_mutation"] is False
    assert packetized["summary"]["runtime_mutation"] is False
    assert len(proposals) == 22
    assert {row["status"] for row in proposals} == {"validation_ready"}
    assert validation_runs["count"] == 1
    assert validation_runs["items"][0]["status"] == "validation_ready"
    assert validation_runs["items"][0]["summary"]["passed"] == 22
    assert review_packets["count"] == 1
    assert review_packets["items"][0]["status"] == "approval_review_ready"
    assert review_packets["items"][0]["summary"]["total"] == 22
    assert review_packets["items"][0]["summary"]["validation_failed"] == 0
    assert review_packets["items"][0]["summary"]["by_kind"] == [{"key": "bazi_rule_proposal", "count": 22}]
    assert review_packets["items"][0]["approval_preflight_status"] == "not_run"
    assert review_packets["items"][0]["approval_execution_status"] == "not_run"
    assert manifest["p31f_priority_topic_review_packet"]["review_packet_item_count"] == 22
    assert manifest["p31f_priority_topic_review_packet"]["approval_preflight_mutation"] is False
    assert manifest["p31f_priority_topic_review_packet"]["runtime_mutation"] is False
    assert "docs/v19/V19_P31F_PRIORITY_TOPIC_REVIEW_PACKET.md" in manifest["created_from"]


def test_p31g_priority_topic_decision_preflight_records_item_decisions_only(tmp_path, monkeypatch) -> None:
    import v19.lab_interfaces as lab
    from v19.synthetic_validation import run_p31g_priority_topic_decision_preflight

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    preflighted = run_p31g_priority_topic_decision_preflight()
    packet = lab.list_proposal_review_packets()["items"][0]
    proposals = lab.list_bazi_rule_proposals()["items"]

    assert preflighted["status"] == "decision_preflight_ready"
    assert preflighted["summary"]["proposal_count"] == 22
    assert preflighted["summary"]["decision_record_count"] == 22
    assert preflighted["summary"]["approve_candidate_count"] == 22
    assert preflighted["summary"]["approval_preflight_record_count"] == 1
    assert preflighted["summary"]["preflight_status"] == "approval_preflight_ready"
    assert preflighted["summary"]["preflight_ready_item_count"] == 22
    assert preflighted["summary"]["preflight_failed_checks"] == 0
    assert preflighted["summary"]["approval_execution_mutation"] is False
    assert preflighted["summary"]["proposal_status_mutation"] is False
    assert preflighted["summary"]["version_mutation"] is False
    assert preflighted["summary"]["runtime_mutation"] is False
    assert packet["decision_summary"]["total"] == 22
    assert packet["decision_summary"]["latest_decision"] == "approve_candidate"
    assert packet["approval_preflight_summary"]["latest_status"] == "approval_preflight_ready"
    assert all((row.get("latest_review_decision") or {}).get("decision") == "approve_candidate" for row in packet["items"])
    assert {row["status"] for row in proposals} == {"validation_ready"}
    assert lab.list_bazi_rule_versions()["count"] == 0
    assert lab.lab_status()["counts"]["proposal_review_packet_decisions"] == 22
    assert lab.lab_status()["counts"]["proposal_review_approval_preflights"] == 1
    assert manifest["p31g_priority_topic_decision_preflight"]["decision_record_count"] == 22
    assert manifest["p31g_priority_topic_decision_preflight"]["proposal_status_mutation"] is False
    assert manifest["p31g_priority_topic_decision_preflight"]["runtime_mutation"] is False
    assert "docs/v19/V19_P31G_PRIORITY_TOPIC_DECISION_PREFLIGHT.md" in manifest["created_from"]


def test_p31h_priority_topic_controlled_approval_approves_proposals_without_version_or_runtime(tmp_path, monkeypatch) -> None:
    import v19.lab_interfaces as lab
    from v19.synthetic_validation import run_p31h_priority_topic_controlled_approval

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")

    approved = run_p31h_priority_topic_controlled_approval()
    proposals = lab.list_bazi_rule_proposals()["items"]
    packet = lab.list_proposal_review_packets()["items"][0]

    assert approved["status"] == "controlled_approval_executed"
    assert approved["summary"]["proposal_count"] == 22
    assert approved["summary"]["approval_execution_count"] == 1
    assert approved["summary"]["approved_count"] == 22
    assert approved["summary"]["failed_count"] == 0
    assert approved["summary"]["rule_approved_count"] == 22
    assert approved["summary"]["question_approved_count"] == 0
    assert approved["summary"]["controlled_approval_mutation"] is True
    assert approved["summary"]["auto_approval"] is False
    assert approved["summary"]["version_mutation"] is False
    assert approved["summary"]["runtime_mutation"] is False
    assert {row["status"] for row in proposals} == {"approved"}
    assert packet["approval_execution_summary"]["latest_status"] == "controlled_approval_executed"
    assert lab.list_bazi_rule_versions()["count"] == 0
    assert lab.list_guided_question_library_versions()["count"] == 0
    assert lab.lab_status()["counts"]["proposal_review_approval_executions"] == 1
    assert manifest["p31h_priority_topic_controlled_approval"]["approved_count"] == 22
    assert manifest["p31h_priority_topic_controlled_approval"]["version_mutation"] is False
    assert manifest["p31h_priority_topic_controlled_approval"]["runtime_mutation"] is False
    assert "docs/v19/V19_P31H_PRIORITY_TOPIC_CONTROLLED_APPROVAL.md" in manifest["created_from"]


def test_p31i_priority_topic_rule_version_records_approved_p31e_proposals_only(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab
    from v19.synthetic_validation import run_p31i_priority_topic_rule_version_record

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    versioned = run_p31i_priority_topic_rule_version_record()
    proposals = lab.list_bazi_rule_proposals()["items"]
    versions = lab.list_bazi_rule_versions()

    assert versioned["status"] == "rule_version_recorded"
    assert versioned["summary"]["approved_count"] == 22
    assert versioned["summary"]["version_record_count"] == 1
    assert versioned["summary"]["included_proposal_count"] == 22
    assert versioned["summary"]["rule_count"] == 22
    assert versioned["summary"]["proposal_status_mutation"] is True
    assert versioned["summary"]["version_mutation"] is True
    assert versioned["summary"]["runtime_mutation"] is False
    assert versioned["regression_baseline"]["rule_db_rule_count"] >= 200
    assert versions["count"] == 1
    assert versions["items"][0]["rule_count"] == 22
    assert versions["items"][0]["runtime_mutation"] is False
    assert len(versions["items"][0]["included_proposals"]) == 22
    assert {row["status"] for row in proposals} == {"active_record"}
    assert lab.list_guided_question_library_versions()["count"] == 0
    assert lab.list_governance_releases()["count"] == 0
    assert manifest["p31i_priority_topic_rule_version"]["version_record_count"] == 1
    assert manifest["p31i_priority_topic_rule_version"]["runtime_mutation"] is False
    assert "docs/v19/V19_P31I_PRIORITY_TOPIC_RULE_VERSION.md" in manifest["created_from"]


def test_p31j_priority_topic_governance_release_records_rule_version_only(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab
    from v19.synthetic_validation import run_p31j_priority_topic_governance_release

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    released = run_p31j_priority_topic_governance_release()
    releases = lab.list_governance_releases()
    versions = lab.list_bazi_rule_versions()
    proposals = lab.list_bazi_rule_proposals()["items"]

    assert released["status"] == "governance_release_recorded"
    assert released["summary"]["rule_version_count"] == 1
    assert released["summary"]["governance_release_count"] == 1
    assert released["summary"]["artifact_count"] == 1
    assert released["summary"]["bazi_rule_version_artifact_count"] == 1
    assert released["summary"]["release_mutation"] is True
    assert released["summary"]["runtime_mutation"] is False
    assert releases["count"] == 1
    assert releases["items"][0]["release_type"] == "p31j_priority_topic_rule_release"
    assert releases["items"][0]["summary"]["by_artifact_type"]["bazi_rule_versions"] == 1
    assert releases["items"][0]["runtime_mutation"] is False
    assert versions["count"] == 1
    assert {row["status"] for row in proposals} == {"active_record"}
    assert manifest["p31j_priority_topic_governance_release"]["governance_release_count"] == 1
    assert manifest["p31j_priority_topic_governance_release"]["runtime_mutation"] is False
    assert "docs/v19/V19_P31J_PRIORITY_TOPIC_GOVERNANCE_RELEASE.md" in manifest["created_from"]


def test_p31k_priority_topic_rule_db_candidates_ingest_disabled_adapter_records(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab
    from v19.synthetic_validation import run_p31k_priority_topic_rule_db_candidates

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    ingested = run_p31k_priority_topic_rule_db_candidates()
    p31_rules = rule_db.list_bazi_rules(q="v19.p31e.")["items"]

    assert ingested["status"] == "rule_db_candidates_ingested"
    assert ingested["summary"]["governance_release_count"] == 1
    assert ingested["summary"]["rule_version_count"] == 1
    assert ingested["summary"]["versioned_proposal_count"] == 22
    assert ingested["summary"]["rule_db_candidate_count"] == 22
    assert ingested["summary"]["imported_count"] == 22
    assert ingested["summary"]["blocked_count"] == 0
    assert ingested["summary"]["engine_enabled_count"] == 0
    assert ingested["summary"]["runtime_mutation"] is False
    assert len(p31_rules) == 22
    assert {row["status"] for row in p31_rules} == {"active_record"}
    assert {row["engine_enabled"] for row in p31_rules} == {False}
    assert {row["engine_adapter_status"] for row in p31_rules} == {"candidate_waiting_synthetic_acceptance"}
    assert all(row["source_version_id"] for row in p31_rules)
    assert all("runtime_activation_without_synthetic_gate" in row["forbidden_usage"] for row in p31_rules)
    assert manifest["p31k_priority_topic_rule_db_candidates"]["rule_db_candidate_count"] == 22
    assert manifest["p31k_priority_topic_rule_db_candidates"]["engine_enabled_count"] == 0
    assert manifest["p31k_priority_topic_rule_db_candidates"]["runtime_mutation"] is False
    assert "docs/v19/V19_P31K_PRIORITY_TOPIC_RULE_DB_CANDIDATES.md" in manifest["created_from"]


def test_p31l_priority_topic_adapter_readiness_reports_blockers_without_activation(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab
    from v19.synthetic_validation import run_p31l_priority_topic_adapter_readiness

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    readiness = run_p31l_priority_topic_adapter_readiness()
    p31_rules = rule_db.list_bazi_rules(q="v19.p31e.")["items"]

    assert readiness["status"] == "adapter_readiness_report_ready"
    assert readiness["summary"]["rule_db_candidate_count"] == 22
    assert readiness["summary"]["ready_candidate_count"] == 0
    assert readiness["summary"]["selected_count"] == 0
    assert readiness["summary"]["blocked_count"] == 22
    assert readiness["summary"]["engine_enabled_count"] == 0
    assert readiness["summary"]["runtime_mutation"] is False
    assert readiness["summary"]["blocked_by_reason"]["missing_structured_facts"] == 22
    assert readiness["summary"]["blocked_by_reason"]["missing_synthetic_gate_candidate"] == 22
    assert {row["engine_enabled"] for row in p31_rules} == {False}
    assert manifest["p31l_priority_topic_adapter_readiness"]["blocked_count"] == 22
    assert manifest["p31l_priority_topic_adapter_readiness"]["engine_enabled_count"] == 0
    assert manifest["p31l_priority_topic_adapter_readiness"]["runtime_mutation"] is False
    assert "docs/v19/V19_P31L_PRIORITY_TOPIC_ADAPTER_READINESS.md" in manifest["created_from"]


def test_p31m_priority_topic_adapter_fact_enrichment_makes_candidates_gate_ready_without_activation(tmp_path, monkeypatch) -> None:
    import v19.bazi_rule_db as rule_db
    import v19.bazi_source_archive as archive
    import v19.lab_interfaces as lab
    from v19.synthetic_validation import run_p31m_priority_topic_adapter_fact_enrichment

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_SEED_FILE", root / "docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json")
    monkeypatch.setattr(archive, "KNOWLEDGE_DRAFT_PACK_DIR", root / "docs/bazi_knowledge/packs")
    monkeypatch.setattr(archive, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(lab, "LAB_FILE", tmp_path / "lab_interfaces.json")
    monkeypatch.setattr(rule_db, "SOURCE_ARCHIVE_FILE", tmp_path / "archive.json")
    monkeypatch.setattr(rule_db, "RULE_DB_FILE", tmp_path / "rule_db.json")

    enriched = run_p31m_priority_topic_adapter_fact_enrichment()
    p31_rules = rule_db.list_bazi_rules(q="v19.p31e.")["items"]

    assert enriched["status"] == "adapter_facts_regression_ready"
    assert enriched["summary"]["rule_db_candidate_count"] == 22
    assert enriched["summary"]["adapter_fact_updated_count"] == 22
    assert enriched["summary"]["eval_sample_count"] == 88
    assert enriched["summary"]["eval_failed_count"] == 0
    assert enriched["summary"]["gate_selected_count"] == 22
    assert enriched["summary"]["gate_blocked_count"] == 0
    assert enriched["summary"]["engine_enabled_count"] == 0
    assert enriched["summary"]["runtime_mutation"] is False
    assert enriched["summary"]["by_eval_sample_type"] == {
        "structured_facts_present": 22,
        "synthetic_gate_candidate_present": 22,
        "engine_disabled_contract": 22,
        "forbidden_runtime_outputs_present": 22,
    }
    assert {row["engine_enabled"] for row in p31_rules} == {False}
    assert {row["engine_adapter_status"] for row in p31_rules} == {"adapter_facts_seeded_waiting_synthetic_gate"}
    assert all((row["condition"] or {}).get("structured_facts", {}).get("adapter_marker") == "p31m_priority_topic_candidate" for row in p31_rules)
    assert all("synthetic_gate_candidate" in row["allowed_usage"] for row in p31_rules)
    assert manifest["p31m_priority_topic_adapter_facts"]["adapter_fact_updated_count"] == 22
    assert manifest["p31m_priority_topic_adapter_facts"]["gate_selected_count"] == 22
    assert manifest["p31m_priority_topic_adapter_facts"]["engine_enabled_count"] == 0
    assert manifest["p31m_priority_topic_adapter_facts"]["runtime_mutation"] is False
    assert "docs/v19/V19_P31M_PRIORITY_TOPIC_ADAPTER_FACTS.md" in manifest["created_from"]


def test_lab_default_validation_cases_are_synthetic_explicit_pillars() -> None:
    cases = _default_validation_cases()

    assert cases
    assert all("chart" in case for case in cases)
    assert all("input" not in case for case in cases)
    assert all("NO_BIRTHDATE" in case["guardrails"] for case in cases)
    assert all(_run_case(case)["passed"] for case in cases)
