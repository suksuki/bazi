from __future__ import annotations

from fastapi.testclient import TestClient

from v20.api.runtime import run_runtime_from_pillars
from v20.features.schema import FeatureLayer
from v20.knowledge.approval import build_first_wave_approval_preflight, build_knowledge_approval_preflight
from v20.knowledge.catalog import build_knowledge_catalog
from v20.knowledge.coverage import build_knowledge_coverage_report
from v20.knowledge.draft_import import build_knowledge_draft_import_preview
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
from v20.knowledge.source_catalog import build_knowledge_source_catalog
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
    assert catalog["unit_count"] >= 12
    assert {"strength", "useful_god", "element", "time"} <= {
        row["domain"] for row in catalog["domains"]
    }
    assert "feature.useful_god.candidate_paths" in catalog["feature_hooks"]
    assert "q_useful_god_evidence_gaps" in catalog["question_hooks"]
    assert not catalog["duplicate_ids"]
    assert catalog["source_catalog_status"] == "ready"
    assert not catalog["missing_source_refs"]


def test_v20_knowledge_catalog_endpoint_is_read_only() -> None:
    client = TestClient(app)
    response = client.get("/api/v20/knowledge/catalog")

    assert response.status_code == 200
    data = response.json()
    assert data["runtime_mutation"] is False
    assert data["audit"]["status"] == "pass"


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
    assert "NO_RUNTIME_ACTIVATION_FROM_QUEUE" in queue["guardrails"]


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


def test_v20_knowledge_to_rule_proposals_are_draft_only() -> None:
    report = build_knowledge_rule_proposals("strength", limit=2)
    first_wave = build_first_wave_rule_proposals(limit_per_domain=1)
    proposal = report["proposals"][0]

    assert report["status"] == "ready"
    assert report["runtime_mutation"] is False
    assert proposal["status"] == "released_to_shadow_training"
    assert proposal["activation_scope"] == "shadow_training_and_candidate_rule_graph"
    assert proposal["proposal_type"] == "knowledge_to_rule_path_candidate"
    assert proposal["source_knowledge_id"] == "v20.core.strength_boundary"
    assert "feature.strength" in proposal["emits_feature_hooks"]
    assert "synthetic_suite_pass" in proposal["validation_requirements"]
    assert "user_visible_runtime_activation_without_promotion" in proposal["forbidden_outputs"]
    assert "SHADOW_TRAINING_ALLOWED_BY_DEFAULT" in proposal["guardrails"]
    assert first_wave["proposal_count"] >= 5
    assert first_wave["runtime_mutation"] is False


def test_v20_rule_proposal_preflight_allows_shadow_training_before_promotion() -> None:
    report = build_rule_proposal_preflight("strength", limit=1)
    first_wave = build_first_wave_rule_proposal_preflight(limit_per_domain=1)

    assert report["ok"] is True
    assert report["status"] == "ready_for_shadow_training"
    assert not report["failures"]
    assert any(row.startswith("synthetic_validation_before_user_visible_runtime:") for row in report["promotion_requirements"])
    assert any(row.startswith("decision_record_before_user_visible_runtime:") for row in report["promotion_requirements"])
    assert first_wave["ok"] is True
    assert first_wave["blocked_domain_count"] == 0
    assert first_wave["promotion_requirement_count"] >= 1
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
    assert candidate["runtime_allowed"] is False
    assert candidate["shadow_training_allowed"] is True
    assert candidate["corpus_validation_signal"]["role"] == "coverage_validation_not_rule_source"
    assert "feature_hook_prefix" in atom_types
    assert "boundary_guard" in atom_types
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

    assert report["runtime_mutation"] is False
    assert report["status"] == "ready"
    assert first_wave["runtime_mutation"] is False
    assert first_wave["status"] == "ready"
    assert preflight["runtime_mutation"] is False
    assert preflight["status"] == "ready_for_shadow_training"
    assert first_preflight["runtime_mutation"] is False
    assert first_preflight["status"] == "ready_for_shadow_training"
    assert extraction["runtime_mutation"] is False
    assert extraction["source_authority"] == "reviewed_bazi_knowledge_base"
    assert extraction["corpus_role"] == "coverage_validation_and_refinement_only"
    assert extraction_validation["runtime_mutation"] is False
    assert extraction_validation["status"] == "pass"
    assert llm_extraction["runtime_mutation"] is False
    assert llm_extraction["status"] == "ready"
    assert llm_validation["runtime_mutation"] is False
    assert llm_validation["status"] == "pass"
