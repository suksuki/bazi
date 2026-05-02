from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v20.api.runtime import run_runtime_from_pillars
from v20.features.schema import FeatureLayer
from v20.knowledge.approval import build_first_wave_approval_preflight, build_knowledge_approval_preflight
from v20.knowledge.catalog import build_knowledge_catalog
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
    client = TestClient(app)
    manifest = client.get("/api/v20/knowledge/retrieval-policy").json()
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


def test_v20_knowledge_completion_report_marks_mainline_source_done() -> None:
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
    assert "v20/scripts/run_knowledge_completion.py" in report["recommended_review_script"]
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


def test_v20_full_knowledge_content_doc_covers_l0_to_l12() -> None:
    doc = Path("docs/bazi_knowledge/catalog/v20_knowledge_full_content_zh_v1.md")
    text = doc.read_text(encoding="utf-8")

    assert "V20 八字知识库完整内容 v1" in text
    for index in range(13):
        assert f"## L{index} " in text
    for phrase in (
        "十神为比肩、劫财、食神、伤官、偏财、正财、七杀、正官、偏印、正印",
        "做功关注谁对谁作用",
        "财富财星材料",
        "TopicProjection",
        "LLM 不裁决用神格局",
    ):
        assert phrase in text


def test_v20_decision_and_portrait_model_doc_records_system_driven_chain() -> None:
    doc = Path("docs/v20/V20_DECISION_AND_PORTRAIT_MODEL.md")
    text = doc.read_text(encoding="utf-8")

    assert "V20 裁决链路与画像层模型" in text
    assert "V20 Bazi Defeasible Decision Model" in text
    assert "RuleSpec Runtime" in text
    assert "Defeasible ArgumentNode" in text
    assert "PortraitProjection" in text
    assert "LLM 直接裁决格局" in text


def test_v20_feature_question_interaction_model_doc_records_system_chain() -> None:
    doc = Path("docs/v20/V20_FEATURE_QUESTION_INTERACTION_MODEL.md")
    text = doc.read_text(encoding="utf-8")

    assert "V20 八字特征、智能问题与交互系统模型" in text
    assert "FeatureState" in text
    assert "QuestionIntent" in text
    assert "InteractionSignal" in text
    assert "Utility-based Question Ranking" in text
    assert "直接改 RuleSpec" in text


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


def test_v20_knowledge_catalog_endpoint_is_read_only() -> None:
    client = TestClient(app)
    response = client.get("/api/v20/knowledge/catalog")
    directory = client.get("/api/v20/knowledge/directory").json()
    directory_seeds = client.get("/api/v20/knowledge/directory-seeds").json()
    completion = client.get("/api/v20/knowledge/completion").json()
    macro_dimensions = client.get("/api/v20/knowledge/macro-dimensions").json()
    feature_model = client.get("/api/v20/knowledge/feature-graph-model").json()
    rule_catalog = client.get("/api/v20/rules/catalog").json()

    assert response.status_code == 200
    data = response.json()
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
    client = TestClient(app)
    source_catalog = client.get("/api/v20/knowledge/source-catalog").json()
    coverage = client.get("/api/v20/knowledge/coverage-report").json()
    release = client.get("/api/v20/knowledge/release-manifest").json()

    assert source_catalog["runtime_mutation"] is False
    assert coverage["runtime_mutation"] is False
    assert release["runtime_mutation"] is False
    assert release["status"] == "ready_for_release_review"


def test_v20_v19_knowledge_migration_audit_is_draft_only() -> None:
    audit = build_v19_knowledge_migration_audit()

    assert audit["status"] == "audit_ready"
    assert audit["candidate_count"] >= 50
    assert audit["runtime_mutation"] is False
    assert "direct_runtime_import" in audit["blocked_actions"]
    assert "V19_KNOWLEDGE_MIGRATION_AUDIT_ONLY" in audit["guardrails"]


def test_v20_v19_knowledge_migration_endpoint_is_read_only() -> None:
    client = TestClient(app)
    audit = client.get("/api/v20/knowledge/v19-migration-audit").json()

    assert audit["runtime_mutation"] is False
    assert audit["candidate_count"] >= 50
    assert "draft_unit_review" in audit["migration_lanes"]


def test_v20_knowledge_draft_import_preview_is_not_runtime_activation() -> None:
    preview = build_knowledge_draft_import_preview(limit=8)

    assert preview["status"] == "preview_ready"
    assert preview["candidate_count"] >= 50
    assert preview["returned_candidate_count"] == 8
    assert preview["runtime_mutation"] is False
    assert preview["target_status"] == "draft_review_required"
    assert all(row["target_status"] == "draft_review_required" for row in preview["candidates"])
    assert "NO_RUNTIME_KNOWLEDGE_ACTIVATION" in preview["guardrails"]


def test_v20_knowledge_draft_import_preview_endpoint_is_read_only() -> None:
    client = TestClient(app)
    preview = client.get("/api/v20/knowledge/draft-import-preview").json()

    assert preview["runtime_mutation"] is False
    assert preview["candidate_count"] >= 50
    assert preview["migration_audit_status"] == "audit_ready"


def test_v20_knowledge_review_queue_prioritizes_core_bazi_domains() -> None:
    queue = build_knowledge_review_queue(limit_per_domain=3)

    assert queue["status"] == "ready"
    assert queue["runtime_mutation"] is False
    assert queue["candidate_count"] >= 400
    domains = [row["domain"] for row in queue["domains"]]
    assert "strength" in domains
    assert "ten_god" in domains
    assert queue["core_domain_priority"][:3] == ("strength", "ten_god", "useful_god")
    first_strength = next(row for row in queue["domains"] if row["domain"] == "strength")
    assert first_strength["recommended_first_batch"]
    assert first_strength["review_policy"] == "core_bazi_first_wave_review"


def test_v20_knowledge_review_queue_endpoint_is_read_only() -> None:
    client = TestClient(app)
    queue = client.get("/api/v20/knowledge/review-queue").json()

    assert queue["runtime_mutation"] is False
    assert queue["status"] == "ready"
    assert "QUEUE_FEEDS_ACTIVE_RUNTIME_AFTER_TRACE" in queue["guardrails"]


def test_v20_knowledge_review_packet_builds_draft_unit_skeletons() -> None:
    packet = build_knowledge_review_packet("strength", limit=4)

    assert packet["status"] == "ready_for_review"
    assert packet["runtime_mutation"] is False
    assert packet["candidate_count"] >= 4
    assert packet["selected_count"] == 4
    assert len(packet["proposed_units"]) == 4
    assert all(row["status"] == "draft_review_required" for row in packet["proposed_units"])
    assert "draft_units_have_missing_required_fields" in packet["release_blockers"]
    assert "DECISION_RECORD_REQUIRED_FOR_RELEASE" in packet["guardrails"]


def test_v20_first_wave_review_packets_prioritize_available_core_domains() -> None:
    packets = build_first_wave_review_packets(limit_per_domain=2)

    assert packets["status"] == "ready"
    assert packets["runtime_mutation"] is False
    assert packets["domain_count"] >= 5
    domains = [row["domain"] for row in packets["packets"]]
    assert domains[:3] == ["strength", "ten_god", "useful_god"]
    assert all(row["selected_count"] <= 2 for row in packets["packets"])


def test_v20_knowledge_review_packet_endpoints_are_read_only() -> None:
    client = TestClient(app)
    packet = client.get("/api/v20/knowledge/review-packet/strength").json()
    packets = client.get("/api/v20/knowledge/first-wave-review-packets").json()

    assert packet["runtime_mutation"] is False
    assert packet["status"] == "ready_for_review"
    assert packets["runtime_mutation"] is False
    assert packets["status"] == "ready"


def test_v20_knowledge_approval_preflight_blocks_incomplete_drafts() -> None:
    report = build_knowledge_approval_preflight("strength")
    first_wave = build_first_wave_approval_preflight()

    assert report["ok"] is False
    assert report["status"] == "blocked"
    assert report["runtime_mutation"] is False
    assert any("missing_evidence_template" in row for row in report["failures"])
    assert first_wave["status"] == "blocked"
    assert first_wave["blocked_domain_count"] >= 1
    assert "NO_AUTOMATIC_REVIEWED_STATUS" in first_wave["guardrails"]


def test_v20_knowledge_approval_preflight_endpoints_are_read_only() -> None:
    client = TestClient(app)
    report = client.get("/api/v20/knowledge/approval-preflight/strength").json()
    first_wave = client.get("/api/v20/knowledge/first-wave-approval-preflight").json()

    assert report["runtime_mutation"] is False
    assert report["status"] == "blocked"
    assert first_wave["runtime_mutation"] is False
    assert first_wave["status"] == "blocked"


def test_v20_knowledge_review_assist_suggests_missing_fields_without_writes() -> None:
    assist = build_knowledge_review_assist("strength", limit=3)
    first_wave = build_first_wave_review_assist(limit_per_domain=2)

    assert assist["status"] == "ready"
    assert assist["runtime_mutation"] is False
    assert assist["suggestion_count"] == 3
    suggestion = assist["suggestions"][0]
    assert suggestion["evidence_template_suggestion"]
    assert suggestion["boundary_suggestion"]
    assert suggestion["feature_hooks_suggestion"]
    assert suggestion["question_hooks_suggestion"]
    assert suggestion["status_after_suggestion"] == "draft_review_required"
    assert first_wave["status"] == "ready"
    assert first_wave["total_suggestion_count"] >= 6
    assert "NO_AUTOMATIC_APPROVAL" in first_wave["guardrails"]


def test_v20_knowledge_review_assist_endpoints_are_read_only() -> None:
    client = TestClient(app)
    assist = client.get("/api/v20/knowledge/review-assist/strength").json()
    first_wave = client.get("/api/v20/knowledge/first-wave-review-assist").json()

    assert assist["runtime_mutation"] is False
    assert assist["status"] == "ready"
    assert first_wave["runtime_mutation"] is False
    assert first_wave["status"] == "ready"


def test_v20_knowledge_to_rule_proposals_feed_active_runtime() -> None:
    report = build_knowledge_rule_proposals("strength", limit=2)
    first_wave = build_first_wave_rule_proposals(limit_per_domain=1)
    proposal = report["proposals"][0]

    assert report["status"] == "ready"
    assert report["runtime_mutation"] is False
    assert proposal["status"] == "active_ready"
    assert proposal["activation_scope"] == "active_runtime_rule_graph"
    assert proposal["proposal_type"] == "knowledge_to_rule_path_candidate"
    assert proposal["source_knowledge_id"] == "v20.core.strength_boundary"
    assert "feature.strength" in proposal["emits_feature_hooks"]
    assert "synthetic_suite_pass" in proposal["validation_requirements"]
    assert "untraced_runtime_activation" in proposal["forbidden_outputs"]
    assert proposal["bazi_alignment"]["ok"] is True
    assert proposal["bazi_alignment"]["status"] == "bazi_core_aligned"
    assert "ACTIVE_TRAINING_ALLOWED_BY_DEFAULT" in proposal["guardrails"]
    assert first_wave["proposal_count"] >= 5
    assert first_wave["runtime_mutation"] is False


def test_v20_rule_proposal_preflight_allows_active_runtime_iteration() -> None:
    report = build_rule_proposal_preflight("strength", limit=1)
    first_wave = build_first_wave_rule_proposal_preflight(limit_per_domain=1)

    assert report["ok"] is True
    assert report["status"] == "active_ready"
    assert not report["failures"]
    assert any(row.startswith("synthetic_validation_for_active_runtime:") for row in report["iteration_requirements"])
    assert any(row.startswith("decision_record_for_active_runtime:") for row in report["iteration_requirements"])
    assert first_wave["ok"] is True
    assert first_wave["blocked_domain_count"] == 0
    assert first_wave["iteration_requirement_count"] >= 1
    assert first_wave["runtime_mutation"] is False


def test_v20_rule_extraction_is_knowledge_first_with_corpus_validation_only() -> None:
    report = build_rule_extraction_report("strength", limit=1)
    validation = validate_rule_extraction_report("strength", limit=1)
    candidate = report["candidates"][0]
    atom_types = {row["atom_type"] for row in candidate["condition_atoms"]}

    assert report["status"] == "ready"
    assert report["source_authority"] == "reviewed_bazi_knowledge_base"
    assert report["corpus_role"] == "coverage_validation_and_refinement_only"
    assert report["llm_role"] == "candidate_atom_drafting_only_validator_required"
    assert candidate["source_knowledge_id"] == "v20.core.strength_boundary"
    assert candidate["source_authority"] == "reviewed_bazi_knowledge_base"
    assert candidate["runtime_allowed"] is True
    assert candidate["active_training_allowed"] is True
    assert candidate["corpus_validation_signal"]["role"] == "coverage_validation_not_rule_source"
    assert candidate["bazi_alignment"]["ok"] is True
    assert "feature_hook_prefix" in atom_types
    assert "boundary_guard" in atom_types
    assert validation["status"] == "pass"
    assert validation["runtime_mutation"] is False


def test_v20_knowledge_rule_library_is_active_traceable_runtime_layer() -> None:
    library = build_knowledge_rule_library("strength", limit=1)
    validation = validate_knowledge_rule_library("strength", limit=1)
    definition = library["definitions"][0]

    assert library["status"] == "ready"
    assert library["source_authority"] == "reviewed_bazi_knowledge_base"
    assert library["definition_count"] == 1
    assert library["runtime_allowed_count"] == 1
    assert library["portrait_output_count"] >= 1
    assert library["question_output_count"] >= 1
    assert definition["source_knowledge_id"] == "v20.core.strength_boundary"
    assert definition["runtime_allowed"] is True
    assert definition["activation_status"] == "active_iteration"
    assert definition["validation_state"] == "active_ready"
    assert any(row["source"] == "knowledge_unit_structured_atom" for row in definition["condition_atoms"])
    assert definition["portrait_outputs"][0]["label"] == "日主承载力"
    assert definition["question_outputs"][0]["title"] == "这个八字日主偏强还是偏弱，适合先看什么？"
    assert definition["bazi_alignment"]["ok"] is True
    assert validation["status"] == "pass"
    assert validation["runtime_mutation"] is False


def test_v20_llm_rule_extraction_uses_safe_fallback_when_provider_disabled() -> None:
    report = build_llm_rule_extraction_report("strength", limit=1)
    validation = validate_llm_rule_extraction_report("strength", limit=1)
    draft = report["drafts"][0]["draft_result"]

    assert report["status"] == "ready"
    assert report["source_authority"] == "reviewed_bazi_knowledge_base"
    assert report["llm_role"] == "structured_rule_atom_draft_only"
    assert report["accepted_count"] == 0
    assert report["fallback_count"] == 1
    assert draft["status"] == "fallback"
    assert draft["source"] == "deterministic_fallback"
    assert draft["llm_call"]["fallback_reason"] in {"provider_not_ready", "execute_flag_disabled"}
    assert validation["status"] == "pass"
    assert validation["runtime_mutation"] is False


def test_v20_rule_proposal_endpoints_are_read_only() -> None:
    client = TestClient(app)
    report = client.get("/api/v20/knowledge/rule-proposals/strength").json()
    first_wave = client.get("/api/v20/knowledge/first-wave-rule-proposals").json()
    preflight = client.get("/api/v20/knowledge/rule-proposal-preflight/strength").json()
    first_preflight = client.get("/api/v20/knowledge/first-wave-rule-proposal-preflight").json()
    extraction = client.get("/api/v20/knowledge/rule-extraction/strength").json()
    extraction_validation = client.get("/api/v20/knowledge/rule-extraction-validation/strength").json()
    llm_extraction = client.get("/api/v20/knowledge/llm-rule-extraction/strength").json()
    llm_validation = client.get("/api/v20/knowledge/llm-rule-extraction-validation/strength").json()
    rule_library = client.get("/api/v20/knowledge/rule-library/strength?limit=1").json()
    rule_library_validation = client.get("/api/v20/knowledge/rule-library-validation/strength?limit=1").json()

    assert report["runtime_mutation"] is False
    assert report["status"] == "ready"
    assert first_wave["runtime_mutation"] is False
    assert first_wave["status"] == "ready"
    assert preflight["runtime_mutation"] is False
    assert preflight["status"] == "active_ready"
    assert first_preflight["runtime_mutation"] is False
    assert first_preflight["status"] == "active_ready"
    assert extraction["runtime_mutation"] is False
    assert extraction["source_authority"] == "reviewed_bazi_knowledge_base"
    assert extraction["corpus_role"] == "coverage_validation_and_refinement_only"
    assert extraction_validation["runtime_mutation"] is False
    assert extraction_validation["status"] == "pass"
    assert llm_extraction["runtime_mutation"] is False
    assert llm_extraction["status"] == "ready"
    assert llm_validation["runtime_mutation"] is False
    assert llm_validation["status"] == "pass"
    assert rule_library["runtime_mutation"] is False
    assert rule_library["status"] == "ready"
    assert rule_library["runtime_allowed_count"] == rule_library["definition_count"]
    assert rule_library_validation["runtime_mutation"] is False
    assert rule_library_validation["status"] == "pass"
