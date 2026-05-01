from __future__ import annotations

from v20.access.roles import access_role_manifest
from v20.features.calibration import confidence_calibration_manifest
from v20.interaction.question_ranker import question_ranking_manifest
from v20.knowledge.catalog import build_knowledge_catalog
from v20.knowledge.coverage import build_knowledge_coverage_report
from v20.knowledge.migration import build_v19_knowledge_migration_audit
from v20.knowledge.ranking import knowledge_retrieval_manifest
from v20.knowledge.release import build_knowledge_release_manifest
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
    dependencies = dependency_readiness_report()
    sync = sync_readiness_report(config)
    matrix = build_test_coverage_matrix()
    evolution = build_evolution_dry_run_plan()
    learning_run_plan = build_learning_run_plan()
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
