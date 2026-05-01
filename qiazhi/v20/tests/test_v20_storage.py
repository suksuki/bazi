from __future__ import annotations

from v20.storage.postgres_schema import build_postgres_schema_contract, migration_manifest


def test_v20_postgres_schema_contract_covers_authoritative_tables() -> None:
    contract = build_postgres_schema_contract()
    table_names = {row.name for row in contract.tables}

    assert contract.backend == "postgres"
    assert contract.runtime_mutation is False
    assert table_names == {
        "v20_knowledge_units",
        "v20_artifact_registry",
        "v20_run_registry",
        "v20_decision_registry",
        "v20_feedback_ledger",
        "v20_corpus_snapshots",
        "v20_rule_proposals",
        "v20_llm_artifacts",
    }
    assert all("NO_REDIS_AUTHORITY" in row.guardrails for row in contract.tables)
    assert all(row.primary_key for row in contract.tables)


def test_v20_initial_migration_is_non_destructive_and_review_gated() -> None:
    manifest = migration_manifest()
    migration = manifest["migrations"][0]

    assert manifest["runtime_mutation"] is False
    assert migration["migration_id"] == "v20_0001_initial_authoritative_tables"
    assert migration["destructive"] is False
    assert "MIGRATION_REQUIRES_BACKUP" in migration["guardrails"]
    assert all("CREATE TABLE IF NOT EXISTS v20_" in statement for statement in migration["sql"])
