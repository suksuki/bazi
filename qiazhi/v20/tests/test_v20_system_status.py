from __future__ import annotations

from types import SimpleNamespace

import pytest
import v20.ops.status as status_module
import v20.server as server_module
from v20.server import app


class _StorageContract:
    def to_dict(self) -> dict[str, object]:
        return {"table_count": 9}


@pytest.fixture()
def system_status_report(monkeypatch) -> dict[str, object]:
    monkeypatch.setattr(status_module, "load_runtime_config_from_env", lambda: SimpleNamespace(active_profile="test"))
    monkeypatch.setattr(status_module, "validate_runtime_config", lambda _config: {"ok": True, "runtime_mutation": False})
    monkeypatch.setattr(status_module, "build_postgres_schema_contract", lambda: _StorageContract())
    monkeypatch.setattr(status_module, "redis_contract_manifest", lambda: {"version": "redis"})
    monkeypatch.setattr(status_module, "validate_redis_contract", lambda _redis: {"ok": True, "runtime_mutation": False})
    monkeypatch.setattr(status_module, "dependency_readiness_report", lambda: {"runtime_mutation": False})
    monkeypatch.setattr(status_module, "sync_readiness_report", lambda _config: {"status": "ready_for_manual_sync", "runtime_mutation": False})

    monkeypatch.setattr(status_module, "build_knowledge_catalog", lambda: {"status": "ready", "unit_count": 21})
    monkeypatch.setattr(
        status_module,
        "build_knowledge_completion_report",
        lambda: {
            "status": "needs_work",
            "completion_percent": 0,
            "mainline_complete": False,
            "mainline_blockers": ("macro_dimension_topic_units_not_complete",),
        },
    )
    monkeypatch.setattr(
        status_module,
        "build_knowledge_directory_manifest",
        lambda: {"status": "directory_ready_full_seed_library_ready", "node_count": 13, "p0_node_count": 9},
    )
    monkeypatch.setattr(
        status_module,
        "build_full_directory_seed_library",
        lambda: {
            "status": "full_directory_seeded_for_review",
            "full_content_status": "full_content_draft_ready",
            "seed_count": 200,
            "directory_node_count": 13,
        },
    )
    monkeypatch.setattr(
        status_module,
        "build_macro_dimension_catalog",
        lambda: {"dimension_count": 5, "current_primary_dimensions": ("wealth", "career", "relationship", "romance", "health")},
    )
    monkeypatch.setattr(
        status_module,
        "build_bazi_feature_graph_model_contract",
        lambda: {"status": "phase1_contract_ready", "topic_projection_count": 5, "decision_state_keys": tuple(range(9))},
    )
    monkeypatch.setattr(status_module, "build_knowledge_source_catalog", lambda: {"status": "ready"})
    monkeypatch.setattr(status_module, "build_knowledge_coverage_report", lambda: {"status": "pass", "gap_count": 0})
    monkeypatch.setattr(status_module, "build_knowledge_release_manifest", lambda: {"status": "ready_for_release_review"})
    monkeypatch.setattr(status_module, "build_v19_knowledge_migration_audit", lambda: {"status": "audit_ready", "candidate_count": 50})
    monkeypatch.setattr(status_module, "build_knowledge_draft_import_preview", lambda limit=0: {"status": "preview_ready", "candidate_count": 50})
    monkeypatch.setattr(status_module, "build_knowledge_review_queue", lambda limit_per_domain=0: {"status": "ready", "domain_count": 10})
    monkeypatch.setattr(status_module, "build_first_wave_review_packets", lambda limit_per_domain=0: {"status": "ready", "domain_count": 5})
    monkeypatch.setattr(status_module, "build_first_wave_approval_preflight", lambda: {"status": "blocked", "blocked_domain_count": 1})
    monkeypatch.setattr(status_module, "build_first_wave_review_assist", lambda limit_per_domain=0: {"status": "ready", "total_suggestion_count": 1})
    monkeypatch.setattr(status_module, "build_first_wave_rule_proposals", lambda limit_per_domain=0: {"status": "ready", "proposal_count": 1})
    monkeypatch.setattr(status_module, "build_first_wave_rule_proposal_preflight", lambda limit_per_domain=0: {"status": "active_ready"})
    monkeypatch.setattr(status_module, "build_rule_extraction_report", lambda limit=0: {"status": "ready", "candidate_count": 1})
    monkeypatch.setattr(status_module, "validate_rule_extraction_report", lambda limit=0: {"status": "pass"})
    monkeypatch.setattr(status_module, "build_llm_rule_extraction_report", lambda limit=0, execute_llm=False: {"status": "ready", "accepted_count": 0, "fallback_count": 0})
    monkeypatch.setattr(status_module, "validate_llm_rule_extraction_report", lambda limit=0, execute_llm=False: {"status": "pass"})
    monkeypatch.setattr(status_module, "build_knowledge_rule_library", lambda limit=0: {"status": "ready", "definition_count": 24 if not limit else 12, "runtime_allowed_count": 12})
    monkeypatch.setattr(
        status_module,
        "build_knowledge_rule_validation_report",
        lambda limit=0: {"status": "active_ready", "synthetic_covered_count": 24 if not limit else 12, "missing_synthetic_count": 0},
    )
    monkeypatch.setattr(
        status_module,
        "build_bazi_rule_catalog",
        lambda: {
            "status": "complete_active_rule_catalog",
            "rule_count": 40,
            "directory_node_count": 13,
            "runtime_ready_count": 10,
            "runtime_allowed_count": 10,
            "blocked_count": 2,
            "archive_only_count": 0,
        },
    )

    monkeypatch.setattr(status_module, "build_full_precompute_manifest", lambda: {"status": "ready_for_dry_run", "cost_estimate": {"estimated_total_minutes": 1}})
    monkeypatch.setattr(status_module, "read_corpus_artifact_status", lambda: {"status": "not_built"})
    monkeypatch.setattr(status_module, "read_corpus_coverage_summary", lambda: {"cluster_count": 0})
    monkeypatch.setattr(status_module, "read_corpus_cluster_model", lambda: {"status": "not_built"})
    monkeypatch.setattr(status_module, "read_corpus_training_artifacts", lambda: {"status": "not_built"})
    monkeypatch.setattr(status_module, "access_role_manifest", lambda: {"roles": ("guest", "user", "practitioner", "admin")})
    monkeypatch.setattr(status_module, "build_test_coverage_matrix", lambda: {"area_count": 7})
    monkeypatch.setattr(status_module, "build_evolution_dry_run_plan", lambda: {"status": "ready_for_dry_run"})
    monkeypatch.setattr(status_module, "build_learning_run_plan", lambda: {"status": "ready_for_dry_run", "target_case_count": 518_400})

    monkeypatch.setattr(
        status_module,
        "build_rule_activation_report",
        lambda limit=0: {
            "status": "ready",
            "packet_count": 12,
            "active_weight_candidate_count": 1,
            "runtime_activation_candidate_count": 12,
            "blocked_count": 0,
            "needs_subcondition_count": 0,
            "subcondition_active_ready_count": 3,
        },
    )
    monkeypatch.setattr(
        status_module,
        "build_rule_subcondition_split_report",
        lambda limit=0, per_rule=0: {"status": "ready", "packet_count": 3, "subcondition_count": 6, "quality_status": "active_ready"},
    )
    monkeypatch.setattr(
        status_module,
        "build_rule_replay_eval_report",
        lambda limit=0, per_rule=0: {
            "status": "ready",
            "replay_eval_ready_count": 3,
            "evaluated_packet_count": 3,
            "portrait_mapping_ok_count": 3,
            "decision_domain_ok_count": 3,
            "runtime_activation_count": 3,
        },
    )
    monkeypatch.setattr(
        status_module,
        "build_decision_registry_iteration_report",
        lambda limit=0, per_rule=0: {"status": "ready", "decision_record_count": 6, "batch_iteration_signal_count": 1, "runtime_activation_count": 6},
    )
    monkeypatch.setattr(status_module, "question_ranking_manifest", lambda: {"version": "question"})
    monkeypatch.setattr(status_module, "knowledge_retrieval_manifest", lambda: {"version": "knowledge"})
    monkeypatch.setattr(status_module, "confidence_calibration_manifest", lambda: {"version": "confidence"})
    monkeypatch.setattr(status_module, "registry_manifest", lambda: {"version": "registries"})
    return status_module.system_status_report()


def test_v20_system_status_core_contracts_are_read_only(system_status_report: dict[str, object]) -> None:
    report = system_status_report

    assert report["status"] == "ok"
    assert report["runtime_mutation"] is False
    assert report["storage_table_count"] == 9
    assert report["sync_readiness"]["status"] == "ready_for_manual_sync"
    assert report["redis_validation"]["ok"] is True
    assert "NO_SECRET_VALUES_RENDERED" in report["guardrails"]


def test_v20_system_status_knowledge_sections_are_mapped(system_status_report: dict[str, object]) -> None:
    report = system_status_report

    assert report["knowledge_catalog_status"] == "ready"
    assert report["knowledge_completion_status"] == "needs_work"
    assert report["knowledge_completion_percent"] == 0
    assert report["knowledge_mainline_complete"] is False
    assert report["knowledge_mainline_blocker_count"] >= 1
    assert report["knowledge_directory_status"] == "directory_ready_full_seed_library_ready"
    assert report["knowledge_directory_node_count"] == 13
    assert report["knowledge_full_directory_seed_count"] >= 200
    assert set(report["knowledge_macro_dimensions"]) == {"wealth", "career", "relationship", "romance", "health"}
    assert report["knowledge_feature_graph_model_status"] == "phase1_contract_ready"
    assert report["knowledge_coverage_status"] == "pass"
    assert report["knowledge_review_queue_status"] == "ready"
    assert report["knowledge_first_wave_packet_status"] == "ready"
    assert report["knowledge_rule_proposal_preflight_status"] == "active_ready"


def test_v20_system_status_rule_sections_are_mapped(system_status_report: dict[str, object]) -> None:
    report = system_status_report

    assert report["knowledge_rule_library_status"] == "ready"
    assert report["knowledge_rule_library_definition_count"] >= 12
    assert report["knowledge_rule_validation_status"] == "active_ready"
    assert report["knowledge_rule_validation_synthetic_covered_count"] >= report["knowledge_rule_library_definition_count"]
    assert report["bazi_rule_catalog_status"] == "complete_active_rule_catalog"
    assert report["bazi_rule_catalog_runtime_allowed_count"] == report["bazi_rule_catalog_runtime_ready_count"]
    assert report["rule_activation_status"] == "ready"
    assert report["rule_activation_packet_count"] >= 12
    assert report["rule_subcondition_split_subcondition_count"] >= report["rule_subcondition_split_packet_count"]
    assert report["rule_replay_eval_runtime_activation_count"] == report["rule_replay_eval_evaluated_packet_count"]
    assert report["decision_registry_iteration_runtime_activation_count"] == report["decision_registry_iteration_record_count"]


def test_v20_system_status_corpus_learning_and_policy_surfaces_are_mapped(system_status_report: dict[str, object]) -> None:
    report = system_status_report

    assert report["full_precompute_status"] == "ready_for_dry_run"
    assert report["corpus_artifact_status"] in {"not_built", "running", "completed"}
    assert report["access_role_count"] == 4
    assert report["test_area_count"] >= 7
    assert report["learning_status"] == "ready_for_dry_run"
    assert report["learning_run_plan_status"] == "ready_for_dry_run"
    assert report["learning_target_case_count"] == 518_400
    assert set(report["policy_surfaces"]) >= {"question_ranking", "knowledge_retrieval", "confidence_calibration", "registries"}
    assert "policy_review" not in report["policy_surfaces"]


def test_v20_system_status_endpoint_is_safe_for_monitoring(monkeypatch) -> None:
    monkeypatch.setattr(
        server_module,
        "system_status_report",
        lambda: {
            "version": "v20.system_status_report.v1",
            "status": "ok",
            "runtime_mutation": False,
            "dependency_readiness": {"runtime_mutation": False},
            "sync_readiness": {"runtime_mutation": False},
            "guardrails": ["NO_SECRET_VALUES_RENDERED"],
        },
    )
    route = next(route for route in app.routes if getattr(route, "path", "") == "/api/v20/system/status")
    data = route.endpoint()

    assert data["runtime_mutation"] is False
    assert "NO_SECRET_VALUES_RENDERED" in data["guardrails"]
    assert data["dependency_readiness"]["runtime_mutation"] is False
    assert data["sync_readiness"]["runtime_mutation"] is False
