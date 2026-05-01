from __future__ import annotations

from v20.access.roles import access_role_manifest
from v20.corpus.artifacts import (
    read_corpus_artifact_status,
    read_corpus_cluster_model,
    read_corpus_coverage_summary,
    read_corpus_training_artifacts,
)
from v20.corpus.full_precompute import build_full_precompute_manifest
from v20.features.calibration import confidence_calibration_manifest
from v20.interaction.question_ranker import question_ranking_manifest
from v20.knowledge.approval import build_first_wave_approval_preflight
from v20.knowledge.catalog import build_knowledge_catalog
from v20.knowledge.coverage import build_knowledge_coverage_report
from v20.knowledge.draft_import import build_knowledge_draft_import_preview
from v20.knowledge.migration import build_v19_knowledge_migration_audit
from v20.knowledge.ranking import knowledge_retrieval_manifest
from v20.knowledge.release import build_knowledge_release_manifest
from v20.knowledge.review_packet import build_first_wave_review_packets
from v20.knowledge.review_assist import build_first_wave_review_assist
from v20.knowledge.review_queue import build_knowledge_review_queue
from v20.knowledge.rule_extraction import (
    build_llm_rule_extraction_report,
    build_rule_extraction_report,
    validate_llm_rule_extraction_report,
    validate_rule_extraction_report,
)
from v20.knowledge.rule_library import build_knowledge_rule_library
from v20.knowledge.rule_proposal import build_first_wave_rule_proposal_preflight, build_first_wave_rule_proposals
from v20.knowledge.source_catalog import build_knowledge_source_catalog
from v20.learning.evolution import build_evolution_dry_run_plan
from v20.learning.decision_registry_review import build_decision_registry_review_report
from v20.learning.run_plan import build_learning_run_plan
from v20.learning.policy_review import policy_review_manifest
from v20.learning.registries import registry_manifest
from v20.learning.rule_promotion_gate import build_rule_promotion_gate_report
from v20.learning.rule_subcondition_split import build_rule_subcondition_split_report
from v20.ops.config import load_runtime_config_from_env
from v20.ops.dependencies import dependency_readiness_report
from v20.ops.profiles import validate_runtime_config
from v20.ops.sync import sync_readiness_report
from v20.redis.contracts import redis_contract_manifest, validate_redis_contract
from v20.storage.postgres_schema import build_postgres_schema_contract
from v20.testing.matrix import build_test_coverage_matrix
from v20.validation.knowledge_rule_library import build_knowledge_rule_validation_report


def system_status_report() -> dict[str, object]:
    config = load_runtime_config_from_env()
    ops_validation = validate_runtime_config(config)
    storage = build_postgres_schema_contract()
    redis = redis_contract_manifest()
    knowledge_catalog = build_knowledge_catalog()
    knowledge_sources = build_knowledge_source_catalog()
    knowledge_coverage = build_knowledge_coverage_report()
    knowledge_release = build_knowledge_release_manifest()
    v19_knowledge_migration = build_v19_knowledge_migration_audit()
    knowledge_draft_import = build_knowledge_draft_import_preview(limit=12)
    knowledge_review_queue = build_knowledge_review_queue(limit_per_domain=3)
    first_wave_packets = build_first_wave_review_packets(limit_per_domain=2)
    first_wave_preflight = build_first_wave_approval_preflight()
    first_wave_assist = build_first_wave_review_assist(limit_per_domain=2)
    rule_proposals = build_first_wave_rule_proposals(limit_per_domain=1)
    rule_proposal_preflight = build_first_wave_rule_proposal_preflight(limit_per_domain=1)
    rule_extraction = build_rule_extraction_report(limit=12)
    rule_extraction_validation = validate_rule_extraction_report(limit=12)
    llm_rule_extraction = build_llm_rule_extraction_report(limit=2, execute_llm=False)
    llm_rule_extraction_validation = validate_llm_rule_extraction_report(limit=2, execute_llm=False)
    knowledge_rule_library = build_knowledge_rule_library(limit=12)
    knowledge_rule_library_full = build_knowledge_rule_library()
    knowledge_rule_validation = build_knowledge_rule_validation_report(limit=12)
    knowledge_rule_validation_full = build_knowledge_rule_validation_report()
    dependencies = dependency_readiness_report()
    sync = sync_readiness_report(config)
    matrix = build_test_coverage_matrix()
    evolution = build_evolution_dry_run_plan()
    learning_run_plan = build_learning_run_plan()
    rule_promotion_gate = build_rule_promotion_gate_report(limit=12)
    rule_subcondition_split = build_rule_subcondition_split_report(limit=12, per_rule=3)
    decision_registry_review = build_decision_registry_review_report(limit=12, per_rule=3)
    precompute_manifest = build_full_precompute_manifest()
    corpus_artifacts = read_corpus_artifact_status()
    corpus_summary = read_corpus_coverage_summary()
    corpus_clusters = read_corpus_cluster_model()
    corpus_training = read_corpus_training_artifacts()
    return {
        "version": "v20.system_status_report.v1",
        "status": "ok" if ops_validation["ok"] else "degraded",
        "active_profile": config.active_profile,
        "ops_validation": ops_validation,
        "dependency_readiness": dependencies,
        "sync_readiness": sync,
        "storage_table_count": storage.to_dict()["table_count"],
        "redis_validation": validate_redis_contract(redis),
        "knowledge_catalog_status": knowledge_catalog["status"],
        "knowledge_unit_count": knowledge_catalog["unit_count"],
        "knowledge_source_catalog_status": knowledge_sources["status"],
        "knowledge_coverage_status": knowledge_coverage["status"],
        "knowledge_gap_count": knowledge_coverage["gap_count"],
        "knowledge_release_status": knowledge_release["status"],
        "v19_knowledge_migration_status": v19_knowledge_migration["status"],
        "v19_knowledge_candidate_count": v19_knowledge_migration["candidate_count"],
        "knowledge_draft_import_status": knowledge_draft_import["status"],
        "knowledge_draft_candidate_count": knowledge_draft_import["candidate_count"],
        "knowledge_review_queue_status": knowledge_review_queue["status"],
        "knowledge_review_domain_count": knowledge_review_queue["domain_count"],
        "knowledge_first_wave_packet_status": first_wave_packets["status"],
        "knowledge_first_wave_domain_count": first_wave_packets["domain_count"],
        "knowledge_first_wave_approval_status": first_wave_preflight["status"],
        "knowledge_first_wave_blocked_domain_count": first_wave_preflight["blocked_domain_count"],
        "knowledge_first_wave_assist_status": first_wave_assist["status"],
        "knowledge_first_wave_suggestion_count": first_wave_assist["total_suggestion_count"],
        "knowledge_rule_proposal_status": rule_proposals["status"],
        "knowledge_rule_proposal_count": rule_proposals["proposal_count"],
        "knowledge_rule_proposal_preflight_status": rule_proposal_preflight["status"],
        "knowledge_rule_extraction_status": rule_extraction["status"],
        "knowledge_rule_extraction_candidate_count": rule_extraction["candidate_count"],
        "knowledge_rule_extraction_validation_status": rule_extraction_validation["status"],
        "knowledge_llm_rule_extraction_status": llm_rule_extraction["status"],
        "knowledge_llm_rule_extraction_accepted_count": llm_rule_extraction["accepted_count"],
        "knowledge_llm_rule_extraction_fallback_count": llm_rule_extraction["fallback_count"],
        "knowledge_llm_rule_extraction_validation_status": llm_rule_extraction_validation["status"],
        "knowledge_rule_library_status": knowledge_rule_library["status"],
        "knowledge_rule_library_definition_count": knowledge_rule_library["definition_count"],
        "knowledge_rule_library_full_definition_count": knowledge_rule_library_full["definition_count"],
        "knowledge_rule_library_runtime_allowed_count": knowledge_rule_library["runtime_allowed_count"],
        "knowledge_rule_validation_status": knowledge_rule_validation["status"],
        "knowledge_rule_validation_synthetic_covered_count": knowledge_rule_validation["synthetic_covered_count"],
        "knowledge_rule_validation_full_synthetic_covered_count": knowledge_rule_validation_full["synthetic_covered_count"],
        "knowledge_rule_validation_missing_synthetic_count": knowledge_rule_validation["missing_synthetic_count"],
        "knowledge_rule_validation_full_missing_synthetic_count": knowledge_rule_validation_full["missing_synthetic_count"],
        "full_precompute_status": precompute_manifest["status"],
        "full_precompute_estimated_minutes": precompute_manifest["cost_estimate"]["estimated_total_minutes"],
        "full_precompute_runtime_role": "offline_structure_coverage_baseline",
        "full_precompute_runtime_decision_authority": "none",
        "corpus_artifact_status": corpus_artifacts["status"],
        "corpus_cluster_count": corpus_summary.get("cluster_count", 0),
        "corpus_cluster_model_status": corpus_clusters["status"],
        "corpus_training_artifact_status": corpus_training["status"],
        "access_role_count": len(access_role_manifest()["roles"]),
        "test_area_count": matrix["area_count"],
        "learning_status": evolution["status"],
        "learning_run_plan_status": learning_run_plan["status"],
        "learning_target_case_count": learning_run_plan["target_case_count"],
        "rule_promotion_gate_status": rule_promotion_gate["status"],
        "rule_promotion_packet_count": rule_promotion_gate["packet_count"],
        "rule_promotion_shadow_weight_candidate_count": rule_promotion_gate["shadow_weight_candidate_count"],
        "rule_promotion_runtime_candidate_count": rule_promotion_gate["runtime_promotion_candidate_count"],
        "rule_promotion_blocked_count": rule_promotion_gate["blocked_count"],
        "rule_promotion_needs_subcondition_count": rule_promotion_gate["needs_subcondition_count"],
        "rule_promotion_subcondition_review_ready_count": rule_promotion_gate["subcondition_review_ready_count"],
        "rule_subcondition_split_status": rule_subcondition_split["status"],
        "rule_subcondition_split_packet_count": rule_subcondition_split["packet_count"],
        "rule_subcondition_split_subcondition_count": rule_subcondition_split["subcondition_count"],
        "rule_subcondition_split_quality_status": rule_subcondition_split["quality_status"],
        "decision_registry_review_status": decision_registry_review["status"],
        "decision_registry_review_record_count": decision_registry_review["decision_record_count"],
        "decision_registry_review_batch_count": decision_registry_review["batch_review_candidate_count"],
        "decision_registry_review_runtime_activation_count": decision_registry_review["runtime_activation_count"],
        "policy_surfaces": {
            "question_ranking": question_ranking_manifest()["version"],
            "knowledge_retrieval": knowledge_retrieval_manifest()["version"],
            "confidence_calibration": confidence_calibration_manifest()["version"],
            "policy_review": policy_review_manifest()["version"],
            "registries": registry_manifest()["version"],
        },
        "runtime_mutation": False,
        "guardrails": [
            "SYSTEM_STATUS_READ_ONLY",
            "NO_NETWORK_CONNECTION_ATTEMPTED",
            "NO_SECRET_VALUES_RENDERED",
            "NO_RUNTIME_POLICY_ACTIVATION",
        ],
    }
