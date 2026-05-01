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
from v20.knowledge.rule_extraction import build_rule_extraction_report, validate_rule_extraction_report
from v20.knowledge.rule_proposal import build_first_wave_rule_proposal_preflight, build_first_wave_rule_proposals
from v20.knowledge.source_catalog import build_knowledge_source_catalog
from v20.learning.evolution import build_evolution_dry_run_plan
from v20.learning.run_plan import build_learning_run_plan
from v20.learning.policy_review import policy_review_manifest
from v20.learning.registries import registry_manifest
from v20.ops.config import load_runtime_config_from_env
from v20.ops.dependencies import dependency_readiness_report
from v20.ops.profiles import validate_runtime_config
from v20.ops.sync import sync_readiness_report
from v20.redis.contracts import redis_contract_manifest, validate_redis_contract
from v20.storage.postgres_schema import build_postgres_schema_contract
from v20.testing.matrix import build_test_coverage_matrix


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
    dependencies = dependency_readiness_report()
    sync = sync_readiness_report(config)
    matrix = build_test_coverage_matrix()
    evolution = build_evolution_dry_run_plan()
    learning_run_plan = build_learning_run_plan()
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
        "full_precompute_status": precompute_manifest["status"],
        "full_precompute_estimated_minutes": precompute_manifest["cost_estimate"]["estimated_total_minutes"],
        "corpus_artifact_status": corpus_artifacts["status"],
        "corpus_cluster_count": corpus_summary.get("cluster_count", 0),
        "corpus_cluster_model_status": corpus_clusters["status"],
        "corpus_training_artifact_status": corpus_training["status"],
        "access_role_count": len(access_role_manifest()["roles"]),
        "test_area_count": matrix["area_count"],
        "learning_status": evolution["status"],
        "learning_run_plan_status": learning_run_plan["status"],
        "learning_target_case_count": learning_run_plan["target_case_count"],
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
