from __future__ import annotations

from v20.corpus.storage import corpus_postgres_index_plan, corpus_storage_policy
from v20.learning.decision_registry_review import write_decision_registry_review_artifact
from v20.storage.postgres_decision_import import build_decision_registry_postgres_import_plan
from v20.storage.postgres_schema import build_postgres_schema_contract, migration_manifest


def test_v20_postgres_schema_contract_covers_authoritative_tables() -> None:
    contract = build_postgres_schema_contract()
    table_names = {row.name for row in contract.tables}

    assert contract.backend == "postgres"
    assert contract.runtime_mutation is False
    assert len(contract.migrations) == 4
    assert table_names == {
        "v20_knowledge_units",
        "v20_artifact_registry",
        "v20_run_registry",
        "v20_decision_registry",
        "v20_feedback_ledger",
        "v20_user_profiles",
        "v20_corpus_snapshots",
        "v20_rule_proposals",
        "v20_llm_artifacts",
    }
    assert all("NO_REDIS_AUTHORITY" in row.guardrails for row in contract.tables)
    assert all(row.primary_key for row in contract.tables)


def test_v20_initial_migration_is_non_destructive_and_review_gated() -> None:
    manifest = migration_manifest()
    migration = manifest["migrations"][0]
    index_migration = manifest["migrations"][1]
    feedback_index_migration = manifest["migrations"][2]
    decision_index_migration = manifest["migrations"][3]

    assert manifest["runtime_mutation"] is False
    assert migration["migration_id"] == "v20_0001_initial_authoritative_tables"
    assert migration["destructive"] is False
    assert "MIGRATION_REQUIRES_BACKUP" in migration["guardrails"]
    assert all("CREATE TABLE IF NOT EXISTS v20_" in statement for statement in migration["sql"])
    assert index_migration["migration_id"] == "v20_0002_corpus_query_indexes"
    assert index_migration["destructive"] is False
    assert any("USING gin (payload)" in statement for statement in index_migration["sql"])
    assert any("payload->>'cluster_key'" in statement for statement in index_migration["sql"])
    assert feedback_index_migration["migration_id"] == "v20_0003_feedback_ledger_indexes"
    assert feedback_index_migration["destructive"] is False
    assert any("idx_v20_feedback_ledger_payload_gin" in statement for statement in feedback_index_migration["sql"])
    assert decision_index_migration["migration_id"] == "v20_0004_decision_registry_indexes"
    assert decision_index_migration["destructive"] is False
    assert any("idx_v20_decision_registry_payload_gin" in statement for statement in decision_index_migration["sql"])


def test_v20_corpus_storage_policy_makes_sqlite_disposable() -> None:
    policy = corpus_storage_policy()
    index_plan = corpus_postgres_index_plan()

    assert policy["authoritative_backend"] == "postgres"
    assert "v20_corpus_snapshots" in policy["authoritative_tables"]
    assert policy["full_corpus_target_count"] == 518_400
    assert policy["derived_local_backends"]["sqlite"]["authority"] is False
    assert policy["derived_local_backends"]["sqlite"]["rebuild_source"] == "v20_corpus_snapshots_or_flat_labels_jsonl"
    assert "SQLITE_IS_DERIVED_AND_DISPOSABLE" in policy["guardrails"]
    assert index_plan["table"] == "v20_corpus_snapshots"
    assert "idx_v20_corpus_payload_gin" in index_plan["indexes"]
    assert "jsonb_containment_for_feature_and_portrait_tags" in index_plan["query_surfaces"]


def test_v20_decision_registry_import_is_explicit_and_postgres_authoritative(tmp_path) -> None:
    write_decision_registry_review_artifact(output_dir=tmp_path, per_rule=2)
    plan = build_decision_registry_postgres_import_plan(artifact_dir=tmp_path, database_url="", apply=False)
    blocked = build_decision_registry_postgres_import_plan(artifact_dir=tmp_path, database_url="", apply=True)

    assert plan["status"] == "dry_run"
    assert plan["target_table"] == "v20_decision_registry"
    assert plan["record_count"] >= 1
    assert plan["runtime_mutation"] is False
    assert "REVIEW_RECORDS_ARE_NOT_RUNTIME_PROMOTIONS" in plan["guardrails"]
    assert blocked["status"] == "blocked_missing_V20_DATABASE_URL"
    assert blocked["runtime_mutation"] is True
