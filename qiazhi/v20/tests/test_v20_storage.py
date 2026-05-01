from __future__ import annotations

from v20.corpus.storage import corpus_postgres_index_plan, corpus_storage_policy
from v20.storage.postgres_schema import build_postgres_schema_contract, migration_manifest


def test_v20_postgres_schema_contract_covers_authoritative_tables() -> None:
    contract = build_postgres_schema_contract()
    table_names = {row.name for row in contract.tables}

    assert contract.backend == "postgres"
    assert contract.runtime_mutation is False
    assert len(contract.migrations) == 2
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

    assert manifest["runtime_mutation"] is False
    assert migration["migration_id"] == "v20_0001_initial_authoritative_tables"
    assert migration["destructive"] is False
    assert "MIGRATION_REQUIRES_BACKUP" in migration["guardrails"]
    assert all("CREATE TABLE IF NOT EXISTS v20_" in statement for statement in migration["sql"])
    assert index_migration["migration_id"] == "v20_0002_corpus_query_indexes"
    assert index_migration["destructive"] is False
    assert any("USING gin (payload)" in statement for statement in index_migration["sql"])
    assert any("payload->>'cluster_key'" in statement for statement in index_migration["sql"])


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
