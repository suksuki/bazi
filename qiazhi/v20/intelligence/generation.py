from __future__ import annotations

from v20.corpus.job_runner import read_full_precompute_status
from v20.corpus.artifacts import (
    read_corpus_artifact_status,
    read_corpus_cluster_model,
    read_corpus_coverage_summary,
    read_corpus_training_artifacts,
)
from v20.interaction.portrait_ontology import portrait_ontology_manifest
from v20.knowledge.catalog import build_knowledge_catalog
from v20.knowledge.rule_extraction import (
    build_llm_rule_extraction_report,
    build_rule_extraction_report,
    validate_llm_rule_extraction_report,
    validate_rule_extraction_report,
)
from v20.knowledge.rule_proposal import build_first_wave_rule_proposal_preflight, build_first_wave_rule_proposals
from v20.llm.contracts import LLM_CONTRACTS
from v20.llm.provider import llm_provider_readiness_report
from v20.validation.suite import run_synthetic_suite


def build_intelligence_generation_manifest() -> dict[str, object]:
    knowledge = build_knowledge_catalog()
    rule_proposals = build_first_wave_rule_proposals(limit_per_domain=1)
    rule_preflight = build_first_wave_rule_proposal_preflight(limit_per_domain=1)
    rule_extraction = build_rule_extraction_report(limit=12)
    rule_extraction_validation = validate_rule_extraction_report(limit=12)
    llm_rule_extraction = build_llm_rule_extraction_report(limit=2)
    llm_rule_extraction_validation = validate_llm_rule_extraction_report(limit=2)
    portrait = portrait_ontology_manifest()
    synthetic = run_synthetic_suite()
    corpus_status = read_full_precompute_status()
    corpus_artifacts = read_corpus_artifact_status()
    corpus_summary = read_corpus_coverage_summary()
    corpus_clusters = read_corpus_cluster_model()
    corpus_training = read_corpus_training_artifacts()
    llm = llm_provider_readiness_report()
    return {
        "version": "v20.intelligence_generation_manifest.v1",
        "status": "ready",
        "current_mode": "feature_discovery_fusion_with_shadow_training_priors",
        "knowledge_generation": {
            "source_layers": [
                "reviewed_seed_knowledge_units",
                "v19_migration_audit",
                "draft_import_preview",
                "deterministic_review_assist",
                "future_bounded_llm_extraction",
            ],
            "generated_artifacts": [
                "KnowledgeUnit",
                "KnowledgeSource",
                "KnowledgeReviewPacket",
                "KnowledgeReviewAssistSuggestion",
            ],
            "reviewed_unit_count": knowledge["unit_count"],
            "runtime_role": "reviewed_evidence_context_only",
            "shadow_learning_allowed": True,
            "user_visible_promotion_gate": [
                "source_review",
                "coverage_report",
                "synthetic_validation",
                "decision_registry_record",
            ],
        },
        "rule_generation": {
            "source_layers": [
                "reviewed_knowledge_units",
                "feature_hook_contracts",
                "question_hook_contracts",
                "boundary_text",
                "future_llm_rule_proposal_drafts",
            ],
            "source_authority": rule_extraction["source_authority"],
            "corpus_role": rule_extraction["corpus_role"],
            "generated_artifacts": [
                "KnowledgeRuleProposal",
                "ExtractedRuleAtom",
                "ExtractedRuleCandidate",
                "candidate_rule_path",
                "shadow_training_signal",
            ],
            "proposal_count": rule_proposals["proposal_count"],
            "extracted_candidate_count": rule_extraction["candidate_count"],
            "extracted_atom_count": rule_extraction["atom_count"],
            "extraction_validation_status": rule_extraction_validation["status"],
            "llm_extraction_status": llm_rule_extraction["status"],
            "llm_extraction_accepted_count": llm_rule_extraction["accepted_count"],
            "llm_extraction_fallback_count": llm_rule_extraction["fallback_count"],
            "llm_extraction_validation_status": llm_rule_extraction_validation["status"],
            "preflight_status": rule_preflight["status"],
            "shadow_training_allowed": True,
            "user_visible_runtime_allowed": False,
            "promotion_requirement_count": rule_preflight["promotion_requirement_count"],
        },
        "portrait_generation": {
            "source_layers": [
                "compiled_bazi_features",
                "reviewed_knowledge_boundaries",
                "feature_confidence",
                "calibration_ledger",
                "full_corpus_label_snapshots",
            ],
            "generated_artifacts": [
                "PortraitProjection",
                "PortraitAxis",
                "PortraitKnowledgeLink",
                "FeatureCalibrationSignal",
            ],
            "source_policy": portrait["source_policy"],
            "runtime_role": "feature_projection_and_calibration_surface",
            "shadow_learning_allowed": True,
            "user_visible_runtime_allowed": True,
        },
        "feature_discovery_generation": {
            "source_layers": [
                "compiled_bazi_features",
                "reviewed_knowledge_refs",
                "knowledge_semantic_model",
                "portrait_projection_axes",
                "portrait_intelligence_axes",
                "shadow_rule_candidate_ranking",
                "bounded_llm_intent_assist",
                "full_corpus_training_artifacts",
            ],
            "generated_artifacts": [
                "FeatureDiscoveryReport",
                "FeatureDiscoveryTrainingSignal",
                "KnowledgeSemanticModel",
                "PortraitIntelligence",
                "feature_discovery_question_policy",
                "ranked_domain_hypotheses",
            ],
            "runtime_role": "central_intelligence_router_for_features_questions_portraits_and_answers",
            "training_role": "518k_corpus_priors_reorder_questions_and_surface_candidate_domains_only",
            "runtime_mutation": False,
            "user_visible_runtime_allowed": True,
            "guardrails": [
                "NO_CORE_FACT_MUTATION",
                "NO_RUNTIME_RULE_ACTIVATION",
                "NO_DESTINY_LABEL_TRAINING",
            ],
        },
        "knowledge_semantic_modeling": {
            "source_layers": [
                "reviewed_knowledge_units",
                "feature_hook_contracts",
                "question_hook_contracts",
                "deterministic_rule_extraction",
                "llm_structured_draft_lane",
            ],
            "generated_artifacts": [
                "domain_semantic_models",
                "portrait_label_candidates",
                "interaction_keyword_index",
                "rule_atom_count_signal",
            ],
            "runtime_role": "semantic_index_for_feature_discovery_portrait_and_interaction",
            "llm_role": "draft_only_validator_required",
            "runtime_mutation": False,
        },
        "llm_generation": {
            "ready_for_connection": llm["ready_for_connection"],
            "provider": llm["provider"],
            "task_contracts": [contract.task_name for contract in LLM_CONTRACTS],
            "allowed_roles": [
                "knowledge_extraction_draft",
                "rule_proposal_draft",
                "portrait_template_draft",
                "answer_plan_rewrite",
                "feedback_summary",
                "safety_review_advisory",
            ],
            "forbidden_roles": [
                "chart_fact_generation",
                "core_rule_truth_override",
                "direct_fortune_verdict",
                "production_promotion",
            ],
        },
        "validation_policy": {
            "synthetic_required_for": [
                "user_visible_rule_promotion",
                "knowledge_release_promotion",
                "answer_boundary_release",
                "learned_ranking_policy_promotion",
            ],
            "synthetic_not_required_for": [
                "shadow_training",
                "candidate_generation",
                "offline_clustering",
                "coverage_gap_detection",
            ],
            "current_synthetic_status": "pass" if synthetic["ok"] else "fail",
            "synthetic_case_count": synthetic["case_count"],
            "full_corpus_status": corpus_status["status"],
            "full_corpus_completed": corpus_status.get("completed_from_start", 0),
            "corpus_artifact_status": corpus_artifacts["status"],
            "corpus_cluster_count": corpus_summary.get("cluster_count", 0),
            "corpus_cluster_model_status": corpus_clusters["status"],
            "corpus_training_artifact_status": corpus_training["status"],
        },
        "runtime_mutation": False,
        "guardrails": [
            "INTELLIGENCE_GENERATION_CONTRACT_ONLY",
            "SHADOW_LEARNING_ALLOWED_BY_DEFAULT",
            "SYNTHETIC_VALIDATION_REQUIRED_FOR_USER_VISIBLE_PROMOTION",
            "NO_LLM_AUTHORITY_OVER_CORE_BAZI_TRUTH",
        ],
    }
