from __future__ import annotations

from fastapi.testclient import TestClient

from v20.ops.status import system_status_report
from v20.server import app


def test_v20_system_status_aggregates_core_contracts_read_only() -> None:
    report = system_status_report()

    assert report["status"] == "ok"
    assert report["runtime_mutation"] is False
    assert report["storage_table_count"] == 9
    assert report["sync_readiness"]["status"] == "ready_for_manual_sync"
    assert report["redis_validation"]["ok"] is True
    assert report["knowledge_catalog_status"] == "ready"
    assert report["knowledge_completion_status"] == "needs_work"
    assert report["knowledge_completion_percent"] == 0
    assert report["knowledge_mainline_complete"] is False
    assert report["knowledge_mainline_blocker_count"] >= 1
    assert report["knowledge_directory_status"] == "directory_ready_full_seed_library_ready"
    assert report["knowledge_directory_node_count"] == 13
    assert report["knowledge_directory_p0_node_count"] >= 9
    assert report["knowledge_full_directory_seed_status"] == "full_directory_seeded_for_review"
    assert report["knowledge_full_directory_content_status"] == "full_content_draft_ready"
    assert report["knowledge_full_directory_seed_count"] >= 200
    assert report["knowledge_full_directory_seed_node_count"] == 13
    assert report["knowledge_macro_dimension_count"] == 5
    assert set(report["knowledge_macro_dimensions"]) == {"wealth", "career", "relationship", "romance", "health"}
    assert report["knowledge_feature_graph_model_status"] == "phase1_contract_ready"
    assert report["knowledge_feature_graph_topic_projection_count"] == 5
    assert report["knowledge_feature_graph_decision_state_count"] == 9
    assert report["knowledge_unit_count"] >= 21
    assert report["knowledge_source_catalog_status"] == "ready"
    assert report["knowledge_coverage_status"] == "pass"
    assert report["knowledge_gap_count"] == 0
    assert report["knowledge_release_status"] == "ready_for_release_review"
    assert report["v19_knowledge_migration_status"] == "audit_ready"
    assert report["v19_knowledge_candidate_count"] >= 50
    assert report["knowledge_draft_import_status"] == "preview_ready"
    assert report["knowledge_draft_candidate_count"] >= 50
    assert report["knowledge_review_queue_status"] == "ready"
    assert report["knowledge_review_domain_count"] >= 10
    assert report["knowledge_first_wave_packet_status"] == "ready"
    assert report["knowledge_first_wave_domain_count"] >= 5
    assert report["knowledge_first_wave_approval_status"] == "blocked"
    assert report["knowledge_first_wave_blocked_domain_count"] >= 1
    assert report["knowledge_first_wave_assist_status"] == "ready"
    assert report["knowledge_first_wave_suggestion_count"] >= 1
    assert report["knowledge_rule_proposal_status"] == "ready"
    assert report["knowledge_rule_proposal_count"] >= 1
    assert report["knowledge_rule_proposal_preflight_status"] == "active_ready"
    assert report["knowledge_rule_library_status"] == "ready"
    assert report["knowledge_rule_library_definition_count"] >= 12
    assert report["knowledge_rule_library_full_definition_count"] >= report["knowledge_rule_library_definition_count"]
    assert report["knowledge_rule_library_runtime_allowed_count"] >= 0
    assert report["knowledge_rule_validation_status"] == "active_ready"
    assert report["knowledge_rule_validation_synthetic_covered_count"] >= report["knowledge_rule_library_definition_count"]
    assert report["knowledge_rule_validation_full_synthetic_covered_count"] >= report["knowledge_rule_library_full_definition_count"]
    assert report["knowledge_rule_validation_missing_synthetic_count"] == 0
    assert report["knowledge_rule_validation_full_missing_synthetic_count"] == 0
    assert report["bazi_rule_catalog_status"] == "complete_active_rule_catalog"
    assert report["bazi_rule_catalog_rule_count"] >= 40
    assert report["bazi_rule_catalog_node_count"] == 13
    assert report["bazi_rule_catalog_runtime_ready_count"] >= 10
    assert report["bazi_rule_catalog_runtime_allowed_count"] == report["bazi_rule_catalog_runtime_ready_count"]
    assert report["bazi_rule_catalog_blocked_count"] >= 2
    assert report["bazi_rule_catalog_archive_only_count"] == 0
    assert report["full_precompute_status"] == "ready_for_dry_run"
    assert report["full_precompute_estimated_minutes"] > 0
    assert report["full_precompute_runtime_role"] == "offline_structure_coverage_baseline"
    assert report["full_precompute_runtime_decision_authority"] == "none"
    assert report["corpus_artifact_status"] in {"not_built", "running", "completed"}
    assert report["corpus_cluster_count"] >= 0
    assert report["access_role_count"] == 4
    assert report["test_area_count"] >= 7
    assert report["learning_status"] == "ready_for_dry_run"
    assert report["learning_run_plan_status"] == "ready_for_dry_run"
    assert report["learning_target_case_count"] == 518_400
    assert report["rule_activation_status"] == "ready"
    assert report["rule_activation_packet_count"] >= 12
    assert report["rule_activation_runtime_candidate_count"] == report["rule_activation_packet_count"]
    assert report["rule_activation_blocked_count"] == 0
    assert report["rule_activation_needs_subcondition_count"] == 0
    assert report["rule_activation_subcondition_active_ready_count"] >= 1
    assert report["rule_subcondition_split_status"] == "ready"
    assert report["rule_subcondition_split_packet_count"] == report["rule_activation_subcondition_active_ready_count"]
    assert report["rule_subcondition_split_subcondition_count"] >= report["rule_subcondition_split_packet_count"]
    assert report["rule_replay_eval_status"] == "ready"
    assert report["rule_replay_eval_evaluated_packet_count"] == report["rule_activation_subcondition_active_ready_count"]
    assert report["rule_replay_eval_ready_count"] == report["rule_replay_eval_evaluated_packet_count"]
    assert report["rule_replay_eval_portrait_mapping_ok_count"] == report["rule_replay_eval_evaluated_packet_count"]
    assert report["rule_replay_eval_decision_domain_ok_count"] == report["rule_replay_eval_evaluated_packet_count"]
    assert report["rule_replay_eval_runtime_activation_count"] == report["rule_replay_eval_evaluated_packet_count"]
    assert report["decision_registry_iteration_status"] == "ready"
    assert report["decision_registry_iteration_record_count"] >= report["rule_subcondition_split_subcondition_count"]
    assert report["decision_registry_iteration_batch_count"] >= 1
    assert report["decision_registry_iteration_runtime_activation_count"] == report["decision_registry_iteration_record_count"]
    assert set(report["policy_surfaces"]) >= {
        "question_ranking",
        "knowledge_retrieval",
        "confidence_calibration",
        "policy_review",
        "registries",
    }


def test_v20_system_status_endpoint_is_safe_for_monitoring() -> None:
    client = TestClient(app)
    response = client.get("/api/v20/system/status")

    assert response.status_code == 200
    data = response.json()
    assert data["runtime_mutation"] is False
    assert "NO_SECRET_VALUES_RENDERED" in data["guardrails"]
    assert data["dependency_readiness"]["runtime_mutation"] is False
    assert data["sync_readiness"]["runtime_mutation"] is False
