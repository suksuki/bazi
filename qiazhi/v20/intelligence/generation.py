from __future__ import annotations

from v20.corpus.job_runner import read_full_precompute_status
from v20.corpus.artifacts import (
    read_corpus_artifact_status,
    read_corpus_cluster_model,
    read_corpus_coverage_summary,
    read_corpus_training_artifacts,
)
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
from v20.measurement.domain_alignment import bazi_alignment_manifest
from v20.validation.rule_synthetic import build_rule_synthetic_training_report, run_rule_synthetic_suite
from v20.validation.suite import run_synthetic_suite


def build_intelligence_generation_manifest() -> dict[str, object]:
    knowledge = build_knowledge_catalog()
    rule_proposals = build_first_wave_rule_proposals(limit_per_domain=1)
    rule_preflight = build_first_wave_rule_proposal_preflight(limit_per_domain=1)
    rule_extraction = build_rule_extraction_report(limit=12)
    rule_extraction_validation = validate_rule_extraction_report(limit=12)
    llm_rule_extraction = build_llm_rule_extraction_report(limit=2)
    llm_rule_extraction_validation = validate_llm_rule_extraction_report(limit=2)
    synthetic = run_synthetic_suite()
    rule_synthetic = run_rule_synthetic_suite()
    rule_synthetic_training = build_rule_synthetic_training_report()
    corpus_status = read_full_precompute_status()
    corpus_artifacts = read_corpus_artifact_status()
    corpus_summary = read_corpus_coverage_summary()
    corpus_clusters = read_corpus_cluster_model()
    corpus_training = read_corpus_training_artifacts()
    llm = llm_provider_readiness_report()
    bazi_alignment = bazi_alignment_manifest()
    return {
        "version": "v20.intelligence_generation_manifest.v1",
        "status": "ready",
        "current_mode": "dynamic_decision_spine_with_offline_training_priors",
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
            "synthetic_role": "primary_rule_collision_validation_and_training_gate",
            "generated_artifacts": [
                "KnowledgeRuleProposal",
                "ExtractedRuleAtom",
                "ExtractedRuleCandidate",
                "candidate_rule_path",
                "shadow_training_signal",
                "SyntheticRuleCase",
                "rule_synthetic_training_report",
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
            "synthetic_rule_suite_status": rule_synthetic["status"],
            "synthetic_rule_case_count": rule_synthetic["case_count"],
            "synthetic_rule_training_status": rule_synthetic_training["status"],
            "shadow_training_allowed": rule_synthetic_training["status"] == "ready",
            "user_visible_runtime_allowed": False,
            "promotion_requirement_count": rule_preflight["promotion_requirement_count"],
        },
        "portrait_generation": {
            "source_layers": [
                "runtime_rule_decisions",
                "reviewed_knowledge_boundaries",
                "practitioner_calibration_ledger",
                "offline_training_priors",
            ],
            "generated_artifacts": [
                "PortraitProjection",
                "PortraitAxis",
                "PractitionerControl",
                "DecisionCalibrationSignal",
            ],
            "source_policy": "dynamic_rule_decision_supported",
            "bazi_alignment_required": True,
            "runtime_role": "decision_state_to_portrait_projection",
            "shadow_learning_allowed": True,
            "user_visible_runtime_allowed": True,
        },
        "decision_generation": {
            "source_layers": [
                "chart_facts",
                "core_inference",
                "compiled_features_as_evidence",
                "reviewed_knowledge_rules",
                "deterministic_rule_hit_templates",
                "practitioner_structured_overrides",
                "bounded_llm_intent_assist",
                "offline_synthetic_and_corpus_training_artifacts",
            ],
            "generated_artifacts": [
                "RuleHit",
                "RuleDecision",
                "PortraitProjection",
                "PractitionerControl",
                "decision_question_candidates",
                "decision_parameter_training_signal",
            ],
            "runtime_role": "central_runtime_intelligence_for_portraits_questions_and_llm_context",
            "question_alignment_policy": bazi_alignment["version"],
            "training_role": "offline_priors_calibrate_decision_parameters_only",
            "runtime_mutation": False,
            "user_visible_runtime_allowed": True,
            "guardrails": [
                "NO_CORE_FACT_MUTATION",
                "NO_518K_STATIC_PORTRAIT_TRUTH",
                "PRACTITIONER_OVERRIDE_IS_STRUCTURED_SIGNAL",
                "BAZI_DOMAIN_ALIGNMENT_REQUIRED",
            ],
        },
        "bazi_domain_alignment": bazi_alignment,
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
            "runtime_role": "semantic_index_for_dynamic_decision_knowledge_and_interaction",
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
                "evidence_bounded_practitioner_answer",
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
                "rule_shadow_training_gate",
                "user_visible_rule_promotion",
                "knowledge_release_promotion",
                "answer_boundary_release",
                "learned_ranking_policy_promotion",
            ],
            "synthetic_not_required_for": [
                "full_corpus_coverage_priors",
                "offline_decision_prior_training",
                "active_generation",
                "offline_clustering",
                "coverage_gap_detection",
            ],
            "current_synthetic_status": "pass" if synthetic["ok"] else "fail",
            "synthetic_case_count": synthetic["case_count"],
            "rule_synthetic_status": rule_synthetic["status"],
            "rule_synthetic_case_count": rule_synthetic["case_count"],
            "rule_synthetic_training_status": rule_synthetic_training["status"],
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
