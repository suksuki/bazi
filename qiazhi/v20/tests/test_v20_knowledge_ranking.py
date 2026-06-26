from __future__ import annotations

from v20.api.runtime import run_runtime_from_pillars
from v20.features.schema import FeatureLayer
from v20.knowledge.approval import build_first_wave_approval_preflight, build_knowledge_approval_preflight
from v20.knowledge.catalog import build_knowledge_catalog
import v20.knowledge.completion as knowledge_completion
from v20.knowledge.completion import build_knowledge_completion_report
from v20.knowledge.coverage import build_knowledge_coverage_report
from v20.knowledge.directory import build_knowledge_directory_manifest
from v20.knowledge.directory_seeds import build_full_directory_seed_library
from v20.knowledge.draft_import import build_knowledge_draft_import_preview
from v20.knowledge.feature_model import build_bazi_feature_graph_model_contract
from v20.knowledge.macro_dimensions import build_macro_dimension_catalog
from v20.knowledge.loader import default_knowledge_units
from v20.knowledge.migration import build_v19_knowledge_migration_audit
from v20.knowledge.ranking import KnowledgeRetrievalPolicy, knowledge_retrieval_manifest, rank_knowledge_units
from v20.knowledge.release import build_knowledge_release_manifest
from v20.knowledge.review_packet import build_first_wave_review_packets, build_knowledge_review_packet
from v20.knowledge.review_assist import build_first_wave_review_assist, build_knowledge_review_assist
from v20.knowledge.review_queue import build_knowledge_review_queue
from v20.knowledge.retrieval import retrieve_knowledge
from v20.knowledge.rule_proposal import (
    build_first_wave_rule_proposal_preflight,
    build_first_wave_rule_proposals,
    build_knowledge_rule_proposals,
    build_rule_proposal_preflight,
)
from v20.knowledge.rule_extraction import (
    build_llm_rule_extraction_report,
    build_rule_extraction_report,
    validate_llm_rule_extraction_report,
    validate_rule_extraction_report,
)
from v20.knowledge.rule_library import build_knowledge_rule_library, validate_knowledge_rule_library
from v20.knowledge.source_catalog import build_knowledge_source_catalog
from v20.rules.catalog import build_bazi_rule_catalog
from v20.server import app


def _endpoint(path: str, method: str = "GET"):
    method = method.upper()
    for route in app.routes:
        if getattr(route, "path", "") == path and method in getattr(route, "methods", set()):
            return route.endpoint
    raise AssertionError(f"route not found: {method} {path}")


def test_v20_knowledge_retrieval_policy_reorders_reviewed_units_only() -> None:
    units = default_knowledge_units()
    boosted = rank_knowledge_units(
        units,
        KnowledgeRetrievalPolicy(
            policy_id="test.boost.health",
            domain_weights={"health": 0.6},
            source="test",
            status="draft",
        ),
    )

    assert boosted[0].domain == "health"
    assert {unit.knowledge_id for unit in boosted} == {unit.knowledge_id for unit in units}
    assert all(unit.status == "reviewed" for unit in boosted)


def test_v20_knowledge_retrieval_policy_manifest_blocks_rule_truth() -> None:
    manifest = knowledge_retrieval_manifest()

    assert manifest["runtime_mutation"] is False
    assert "direct_rule_truth" in manifest["blocked_learning_outputs"]
    assert "EMBEDDING_RECALL_MUST_PASS_REVIEW_FILTER" in manifest["guardrails"]


def test_v20_knowledge_retrieval_policy_endpoint_and_runtime_context_only() -> None:
    manifest = _endpoint("/api/v20/knowledge/retrieval-policy")()
    result = run_runtime_from_pillars("甲子", "戊辰", "甲午", "辛酉", input_id="knowledge-rank")

    assert manifest["runtime_mutation"] is False
    assert result["knowledge_report"]["mode"] == "feature_spine_reviewed_knowledge_retrieval"
    assert all(row["reviewed"] is True for row in result["knowledge_refs"])


def test_v20_retrieve_knowledge_accepts_policy_without_creating_refs() -> None:
    report = retrieve_knowledge(
        FeatureLayer(version="test", features=()),
        requested_domains=("health",),
        ranking_policy=KnowledgeRetrievalPolicy(domain_weights={"health": 0.6}),
    )

    assert report.refs
    assert report.refs[0].domain == "health"
    assert all(ref.reviewed for ref in report.refs)


def test_v20_knowledge_catalog_reports_coverage_and_hooks() -> None:
    catalog = build_knowledge_catalog()

    assert catalog["status"] == "ready"
    assert catalog["completeness_status"] == "phase1_seed_coverage_ready_depth_incomplete"
    assert catalog["runtime_mutation"] is False
    assert catalog["unit_count"] >= 21
    assert {"strength", "useful_god", "element", "time"} <= {
        row["domain"] for row in catalog["domains"]
    }
    assert "feature.useful_god.candidate_paths" in catalog["feature_hooks"]
    assert "q_useful_god_evidence_gaps" in catalog["question_hooks"]
    assert not catalog["duplicate_ids"]
    assert catalog["source_catalog_status"] == "ready"
    assert not catalog["missing_source_refs"]


def test_v20_knowledge_completion_report_marks_mainline_source_done(monkeypatch) -> None:
    _stub_knowledge_completion_dependencies(monkeypatch)

    report = build_knowledge_completion_report()

    assert report["status"] == "needs_work"
    assert report["mainline_complete"] is False
    assert report["completion_percent"] == 0
    assert report["unit_count"] == report["reviewed_unit_count"]
    assert report["unit_count"] >= 21
    assert report["directory_status"] == "directory_ready_full_seed_library_ready"
    assert report["directory_node_count"] == 13
    assert report["directory_p0_node_count"] >= 9
    assert report["directory_mainline_fill_order"][:4] == ("L0", "L3", "L4", "L2")
    assert report["full_directory_seed_status"] == "full_directory_seeded_for_review"
    assert report["full_directory_content_status"] == "full_content_draft_ready"
    assert report["full_directory_content_doc"] == "docs/bazi_knowledge/catalog/v20_knowledge_full_content_zh_v1.md"
    assert report["full_directory_seed_count"] >= 200
    assert report["full_directory_seed_node_count"] == 13
    assert report["full_directory_seed_runtime_allowed_count"] == 0
    assert report["domain_count"] >= 11
    assert report["coverage_gap_count"] == 0
    assert report["rule_definition_count"] == report["synthetic_covered_count"]
    assert report["missing_synthetic_count"] == 0
    assert report["runtime_allowed_count"] == report["definition_count"]
    assert set(report["mainline_blockers"]) == {"macro_dimension_topic_units_not_complete"}
    assert report["macro_dimension_count"] == 5
    assert set(report["macro_dimensions"]) == {"wealth", "career", "relationship", "romance", "health"}
    assert report["feature_graph_model_status"] == "phase1_contract_ready"
    assert report["feature_graph_topic_projection_count"] == 5
    assert "TopicProjection[]" in report["feature_graph_chain"]
    assert set(report["feature_graph_decision_states"]) >= {"confirmed", "candidate", "mixed", "volatile"}
    assert report["recommended_status_surface"] == "/api/v20/admin/mainline-status"
    assert report["expansion_backlog"]["status"] == "not_blocking_mainline"
    assert "DRAFT_IMPORT_BACKLOG_DOES_NOT_BLOCK_REVIEWED_SEED_MAINLINE" in report["guardrails"]


def test_v20_default_knowledge_units_carry_structured_runtime_mappings() -> None:
    units = default_knowledge_units()
    library = build_knowledge_rule_library()

    assert len(units) >= 12
    assert all(unit.rule_atoms for unit in units)
    assert all(unit.portrait_mappings for unit in units)
    assert all(unit.question_mappings for unit in units)
    assert library["definition_count"] == len(units)
    assert all(
        definition["portrait_outputs"][0]["source"] == "knowledge_unit_structured_mapping"
        for definition in library["definitions"]
    )
    assert all(
        definition["question_outputs"][0]["source"] == "knowledge_unit_structured_mapping"
        for definition in library["definitions"]
    )


def test_v20_macro_dimension_catalog_adds_romance_and_health_topics() -> None:
    catalog = build_macro_dimension_catalog()
    by_key = {row["dimension_key"]: row for row in catalog["dimensions"]}

    assert catalog["status"] == "ready"
    assert catalog["current_primary_dimensions"] == ("wealth", "career", "relationship", "romance", "health")
    assert by_key["romance"]["title"] == "感情"
    assert by_key["romance"]["evidence_domain"] == "relationship"
    assert by_key["health"]["title"] == "健康"
    assert by_key["health"]["evidence_domain"] == "health"
    assert all(row["content_status"] == "needs_topic_units" for row in catalog["dimensions"])
    assert "NEW_MACRO_DIMENSIONS_MUST_MAP_TO_EXISTING_BAZI_EVIDENCE_DOMAINS_FIRST" in catalog["guardrails"]


def test_v20_knowledge_directory_manifest_prioritizes_measurement_mainline() -> None:
    manifest = build_knowledge_directory_manifest()
    nodes = {row["node_id"]: row for row in manifest["nodes"]}

    assert manifest["status"] == "directory_ready_full_seed_library_ready"
    assert manifest["node_count"] == 13
    assert manifest["full_seed_library_status"] == "full_directory_seeded_for_review"
    assert manifest["full_content_status"] == "full_content_draft_ready"
    assert manifest["full_seed_count"] >= 200
    assert manifest["full_seed_covered_node_count"] == 13
    assert manifest["runtime_mutation"] is False
    assert manifest["mainline_fill_order"][:5] == ("L0", "L3", "L4", "L2", "L5")
    assert {"L0", "L3", "L4", "L8", "L10"} <= set(manifest["p0_nodes"])
    assert nodes["L8"]["title"] == "盲派系统"
    assert nodes["L8"]["content_status"] == "directory_ready_full_seeded_needs_practitioner_review"
    assert "MechanismPath" in nodes["L8"]["maps_to_model_objects"]
    assert nodes["L10"]["role"] == "topic_projection_source"
    assert "APPLICATION_TOPICS_MUST_PROJECT_FROM_BAZI_FEATURES" in manifest["guardrails"]


def test_v20_full_directory_seed_library_covers_all_bazi_content_once() -> None:
    library = build_full_directory_seed_library()
    coverage = library["coverage_by_node"]

    assert library["status"] == "full_directory_seeded_for_review"
    assert library["full_content_status"] == "full_content_draft_ready"
    assert library["seed_count"] >= 200
    assert library["directory_node_count"] == 13
    assert library["runtime_allowed_count"] == 0
    assert set(library["covered_directory_nodes"]) == {f"L{index}" for index in range(13)}
    assert coverage["L3"] >= 30
    assert coverage["L4"] >= 20
    assert coverage["L8"] >= 20
    assert coverage["L10"] >= 20
    assert "PROMOTE_BY_DIRECTORY_NODE_BATCH_NOT_ONE_OFF_PATCHES" in library["guardrails"]


def test_v20_bazi_rule_catalog_covers_full_directory_and_runs_as_rulespec_source() -> None:
    catalog = build_bazi_rule_catalog()

    assert catalog["status"] == "complete_active_rule_catalog"
    assert catalog["rule_count"] >= 40
    assert catalog["directory_node_count"] == 13
    assert set(catalog["covered_directory_nodes"]) == {f"L{index}" for index in range(13)}
    assert catalog["runtime_ready_count"] >= 10
    assert catalog["runtime_allowed_count"] == catalog["runtime_ready_count"]
    assert catalog["blocked_count"] >= 2
    assert catalog["archive_only_count"] == 0
    assert catalog["coverage_by_node"]["L8"] >= 4
    assert catalog["coverage_by_node"]["L10"] >= 5
    assert "RULESPEC_ENGINE_IS_PRIMARY_RULE_RUNTIME" in catalog["guardrails"]
    assert "LEGACY_DECISION_ENGINE_IS_COMPATIBILITY_BRIDGE" in catalog["guardrails"]
    assert any(row["rule_id"] == "rule.l8.zuogong.path" for row in catalog["rules"])
    assert any(row["rule_id"] == "rule.l12.llm.expression_boundary" for row in catalog["rules"])


def test_v20_bazi_feature_graph_model_contract_keeps_feature_first_mainline() -> None:
    contract = build_bazi_feature_graph_model_contract()
    projections = {row["topic_domain"]: row for row in contract["topic_projections"]}

    assert contract["status"] == "phase1_contract_ready"
    assert contract["implementation_strategy"] == "lightweight_typed_objects_before_heavy_property_graph"
    assert contract["runtime_mutation"] is False
    assert "EvidenceAtom[]" in contract["mainline_chain"]
    assert "TopicProjection[]" in contract["mainline_chain"]
    assert "BaziFeature[]" in contract["product_contracts"]
    assert "ui_direct_fact_graph_consumption" in contract["blocked_direct_consumers"]
    assert "fortune_verdict_generation" in contract["llm_blocked_roles"]
    assert set(contract["decision_state_keys"]) == {
        "confirmed",
        "candidate",
        "weak_candidate",
        "blocked",
        "countered",
        "mixed",
        "volatile",
        "requires_review",
        "out_of_scope",
    }
    assert set(projections) == {"wealth", "career", "relationship", "romance", "health"}
    assert "strength" in projections["wealth"]["source_domains"]
    assert projections["health"]["boundary"] == "健康只做结构和生活节律表达，不做医疗诊断。"


def test_v20_knowledge_catalog_endpoint_is_read_only(monkeypatch) -> None:
    _stub_knowledge_completion_dependencies(monkeypatch)

    data = _endpoint("/api/v20/knowledge/catalog")()
    directory = _endpoint("/api/v20/knowledge/directory")()
    directory_seeds = _endpoint("/api/v20/knowledge/directory-seeds")()
    completion = _endpoint("/api/v20/knowledge/completion")()
    macro_dimensions = _endpoint("/api/v20/knowledge/macro-dimensions")()
    feature_model = _endpoint("/api/v20/knowledge/feature-graph-model")()
    rule_catalog = _endpoint("/api/v20/rules/catalog")()

    assert data["runtime_mutation"] is False
    assert data["audit"]["status"] == "pass"
    assert directory["runtime_mutation"] is False
    assert directory["node_count"] == 13
    assert directory_seeds["runtime_mutation"] is False
    assert directory_seeds["seed_count"] >= 200
    assert directory_seeds["full_content_status"] == "full_content_draft_ready"
    assert completion["runtime_mutation"] is False
    assert completion["status"] == "needs_work"
    assert macro_dimensions["runtime_mutation"] is False
    assert "romance" in macro_dimensions["current_primary_dimensions"]
    assert feature_model["runtime_mutation"] is False
    assert feature_model["status"] == "phase1_contract_ready"
    assert rule_catalog["runtime_mutation"] is False
    assert rule_catalog["status"] == "complete_active_rule_catalog"
    assert rule_catalog["directory_node_count"] == 13


def _stub_knowledge_completion_dependencies(monkeypatch) -> None:
    monkeypatch.setattr(
        knowledge_completion,
        "build_knowledge_catalog",
        lambda: {
            "status": "ready",
            "unit_count": 21,
            "reviewed_unit_count": 21,
            "domain_count": 11,
            "retrieval_tags": ("macro", "zuogong", "application"),
        },
    )
    monkeypatch.setattr(
        knowledge_completion,
        "build_knowledge_directory_manifest",
        lambda: {
            "status": "directory_ready_full_seed_library_ready",
            "node_count": 13,
            "p0_node_count": 9,
            "mainline_fill_order": ("L0", "L3", "L4", "L2"),
        },
    )
    monkeypatch.setattr(
        knowledge_completion,
        "build_full_directory_seed_library",
        lambda: {
            "status": "full_directory_seeded_for_review",
            "full_content_status": "full_content_draft_ready",
            "full_content_doc": "docs/bazi_knowledge/catalog/v20_knowledge_full_content_zh_v1.md",
            "seed_count": 200,
            "directory_node_count": 13,
            "runtime_allowed_count": 0,
        },
    )
    monkeypatch.setattr(knowledge_completion, "build_knowledge_source_catalog", lambda: {"status": "ready", "source_count": 12})
    monkeypatch.setattr(knowledge_completion, "build_knowledge_coverage_report", lambda: {"status": "pass", "gap_count": 0})
    monkeypatch.setattr(knowledge_completion, "build_knowledge_release_manifest", lambda: {"status": "ready_for_release_review"})
    monkeypatch.setattr(
        knowledge_completion,
        "build_knowledge_rule_library",
        lambda: {"status": "ready", "definition_count": 12, "atom_count": 12, "portrait_output_count": 5, "question_output_count": 5},
    )
    monkeypatch.setattr(knowledge_completion, "validate_knowledge_rule_library", lambda: {"status": "pass", "ok": True})
    monkeypatch.setattr(
        knowledge_completion,
        "build_knowledge_rule_validation_report",
        lambda: {
            "status": "active_ready",
            "ok": True,
            "synthetic_covered_count": 12,
            "missing_synthetic_count": 0,
            "runtime_allowed_count": 12,
            "definition_count": 12,
            "state_counts": {},
        },
    )
    monkeypatch.setattr(
        knowledge_completion,
        "build_macro_dimension_catalog",
        lambda: {
            "status": "ready",
            "dimension_count": 5,
            "current_primary_dimensions": ("wealth", "career", "relationship", "romance", "health"),
            "dimensions": ({"content_status": "missing"},),
        },
    )
    monkeypatch.setattr(
        knowledge_completion,
        "build_bazi_feature_graph_model_contract",
        lambda: {
            "status": "phase1_contract_ready",
            "phase1_objects": ("TopicProjection",),
            "topic_projection_count": 5,
            "decision_state_keys": ("confirmed", "candidate", "mixed", "volatile"),
            "mainline_chain": ("EvidenceAtom[]", "TopicProjection[]"),
        },
    )
    monkeypatch.setattr(knowledge_completion, "build_knowledge_draft_import_preview", lambda **_: {"candidate_count": 50})
    monkeypatch.setattr(knowledge_completion, "build_knowledge_review_queue", lambda **_: {"candidate_count": 400})


def test_v20_knowledge_source_coverage_and_release_are_ready() -> None:
    source_catalog = build_knowledge_source_catalog()
    coverage = build_knowledge_coverage_report()
    release = build_knowledge_release_manifest()

    assert source_catalog["status"] == "ready"
    assert source_catalog["source_count"] >= 12
    assert not source_catalog["missing_source_refs"]
    assert coverage["status"] == "pass"
    assert coverage["completeness_status"] == "domain_seed_coverage_pass_depth_incomplete"
    assert coverage["gap_count"] == 0
    assert release["status"] == "ready_for_release_review"
    assert "record_decision_registry_approval" in release["release_steps"]
    assert release["runtime_mutation"] is False


def test_v20_knowledge_rebuild_endpoints_are_read_only() -> None:
    source_catalog = _endpoint("/api/v20/knowledge/source-catalog")()
    coverage = _endpoint("/api/v20/knowledge/coverage-report")()
    release = _endpoint("/api/v20/knowledge/release-manifest")()

    assert source_catalog["runtime_mutation"] is False
    assert coverage["runtime_mutation"] is False
    assert release["runtime_mutation"] is False
    assert release["status"] == "ready_for_release_review"
