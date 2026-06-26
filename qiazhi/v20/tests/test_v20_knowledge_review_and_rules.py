from __future__ import annotations

from v20.knowledge.approval import build_first_wave_approval_preflight, build_knowledge_approval_preflight
from v20.knowledge.draft_import import build_knowledge_draft_import_preview
from v20.knowledge.migration import build_v19_knowledge_migration_audit
from v20.knowledge.review_packet import build_first_wave_review_packets, build_knowledge_review_packet
from v20.knowledge.review_assist import build_first_wave_review_assist, build_knowledge_review_assist
from v20.knowledge.review_queue import build_knowledge_review_queue
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
from v20.server import app


def _endpoint(path: str, method: str = "GET"):
    method = method.upper()
    for route in app.routes:
        if getattr(route, "path", "") == path and method in getattr(route, "methods", set()):
            return route.endpoint
    raise AssertionError(f"route not found: {method} {path}")
def test_v20_v19_knowledge_migration_audit_is_draft_only() -> None:
    audit = build_v19_knowledge_migration_audit()

    assert audit["status"] == "audit_ready"
    assert audit["candidate_count"] >= 50
    assert audit["runtime_mutation"] is False
    assert "direct_runtime_import" in audit["blocked_actions"]
    assert "V19_KNOWLEDGE_MIGRATION_AUDIT_ONLY" in audit["guardrails"]
def test_v20_v19_knowledge_migration_endpoint_is_read_only() -> None:
    audit = _endpoint("/api/v20/knowledge/v19-migration-audit")()

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
    preview = _endpoint("/api/v20/knowledge/draft-import-preview")()

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
    queue = _endpoint("/api/v20/knowledge/review-queue")()

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
    packet = _endpoint("/api/v20/knowledge/review-packet/{domain}")("strength")
    packets = _endpoint("/api/v20/knowledge/first-wave-review-packets")()

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
    report = _endpoint("/api/v20/knowledge/approval-preflight/{domain}")("strength")
    first_wave = _endpoint("/api/v20/knowledge/first-wave-approval-preflight")()

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
    assist = _endpoint("/api/v20/knowledge/review-assist/{domain}")("strength")
    first_wave = _endpoint("/api/v20/knowledge/first-wave-review-assist")()

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
    assert draft["llm_call"]["fallback_reason"] in {"provider_not_ready", "execute_flag_disabled"} or "failed:" in draft["llm_call"]["fallback_reason"]
    assert validation["status"] == "pass"
    assert validation["runtime_mutation"] is False
def test_v20_rule_proposal_endpoints_are_read_only() -> None:
    report = _endpoint("/api/v20/knowledge/rule-proposals/{domain}")("strength")
    first_wave = _endpoint("/api/v20/knowledge/first-wave-rule-proposals")()
    preflight = _endpoint("/api/v20/knowledge/rule-proposal-preflight/{domain}")("strength")
    first_preflight = _endpoint("/api/v20/knowledge/first-wave-rule-proposal-preflight")()
    extraction = _endpoint("/api/v20/knowledge/rule-extraction/{domain}")("strength")
    extraction_validation = _endpoint("/api/v20/knowledge/rule-extraction-validation/{domain}")("strength")
    llm_extraction = _endpoint("/api/v20/knowledge/llm-rule-extraction/{domain}")("strength")
    llm_validation = _endpoint("/api/v20/knowledge/llm-rule-extraction-validation/{domain}")("strength")
    rule_library = _endpoint("/api/v20/knowledge/rule-library/{domain}")("strength", limit=1)
    rule_library_validation = _endpoint("/api/v20/knowledge/rule-library-validation/{domain}")("strength", limit=1)

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
