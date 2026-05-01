from __future__ import annotations

from v20.storage.schema import ColumnSpec, MigrationSpec, StorageSchemaContract, TableSpec


def build_postgres_schema_contract() -> StorageSchemaContract:
    tables = _tables()
    return StorageSchemaContract(
        version="v20.postgres_schema_contract.v1",
        backend="postgres",
        tables=tables,
        migrations=(
            _initial_migration(tables),
            _corpus_index_migration(),
            _feedback_ledger_index_migration(),
            _decision_registry_index_migration(),
        ),
    )


def migration_manifest() -> dict[str, object]:
    contract = build_postgres_schema_contract()
    return {
        "version": "v20.storage_migration_manifest.v1",
        "backend": contract.backend,
        "migrations": [row.to_dict() for row in contract.migrations],
        "table_names": [row.name for row in contract.tables],
        "runtime_mutation": False,
        "guardrails": [
            "MIGRATION_MANIFEST_ONLY",
            "APPLY_REQUIRES_EXPLICIT_COMMAND",
            "BACKUP_REQUIRED_BEFORE_REMOTE_APPLY",
        ],
    }


def _tables() -> tuple[TableSpec, ...]:
    common = (
        ColumnSpec("created_at", "timestamptz", purpose="server-side creation timestamp"),
        ColumnSpec("updated_at", "timestamptz", purpose="server-side update timestamp"),
        ColumnSpec("payload", "jsonb", purpose="versioned structured payload"),
    )
    return (
        TableSpec(
            name="v20_knowledge_units",
            owner_module="v20.knowledge",
            purpose="Reviewed knowledge units and release metadata.",
            columns=(
                ColumnSpec("knowledge_id", "text", purpose="stable knowledge unit id"),
                ColumnSpec("version", "text", purpose="knowledge schema or content version"),
                ColumnSpec("status", "text", purpose="draft, reviewed, deprecated"),
                *common,
            ),
            primary_key=("knowledge_id", "version"),
        ),
        TableSpec(
            name="v20_artifact_registry",
            owner_module="v20.learning",
            purpose="Versioned model, corpus, eval, and ranking artifacts.",
            columns=(
                ColumnSpec("artifact_id", "text", purpose="stable artifact id"),
                ColumnSpec("artifact_type", "text", purpose="artifact category"),
                ColumnSpec("artifact_hash", "text", purpose="content hash"),
                *common,
            ),
            primary_key=("artifact_id",),
        ),
        TableSpec(
            name="v20_run_registry",
            owner_module="v20.learning",
            purpose="Dry-run, eval, corpus, and service run records.",
            columns=(
                ColumnSpec("run_id", "text", purpose="stable run id"),
                ColumnSpec("run_type", "text", purpose="run category"),
                ColumnSpec("status", "text", purpose="recorded, pass, fail, blocked"),
                *common,
            ),
            primary_key=("run_id",),
        ),
        TableSpec(
            name="v20_decision_registry",
            owner_module="v20.learning",
            purpose="Human or validator decisions for proposals and promotions.",
            columns=(
                ColumnSpec("decision_id", "text", purpose="stable decision id"),
                ColumnSpec("subject_id", "text", purpose="artifact, proposal, or run id"),
                ColumnSpec("decision_status", "text", purpose="approved, rejected, needs_review"),
                *common,
            ),
            primary_key=("decision_id",),
        ),
        TableSpec(
            name="v20_feedback_ledger",
            owner_module="v20.interaction",
            purpose="Anonymized feedback summaries and calibration signals.",
            columns=(
                ColumnSpec("feedback_id", "text", purpose="stable feedback id"),
                ColumnSpec("source_hash", "text", purpose="anonymized source/session hash"),
                ColumnSpec("calibration_status", "text", purpose="recorded_only or reviewed"),
                *common,
            ),
            primary_key=("feedback_id",),
            pii_policy="anonymized_or_hashed_only",
        ),
        TableSpec(
            name="v20_user_profiles",
            owner_module="v20.profiles",
            purpose="Imported and native user Bazi profiles for guest, practitioner, and admin workflows.",
            columns=(
                ColumnSpec("profile_id", "text", purpose="stable profile id"),
                ColumnSpec("owner_id", "text", purpose="local user or account owner id"),
                ColumnSpec("source_ref", "text", purpose="migration source reference or native source marker"),
                ColumnSpec("status", "text", purpose="active, imported_from_v19, archived"),
                *common,
            ),
            primary_key=("profile_id",),
            pii_policy="local_private_profile_data",
        ),
        TableSpec(
            name="v20_corpus_snapshots",
            owner_module="v20.corpus",
            purpose="Canonical chart/corpus precompute snapshots.",
            columns=(
                ColumnSpec("snapshot_id", "text", purpose="stable snapshot id"),
                ColumnSpec("input_hash", "text", purpose="canonical chart hash"),
                ColumnSpec("compiler_version", "text", purpose="feature compiler version"),
                *common,
            ),
            primary_key=("snapshot_id",),
        ),
        TableSpec(
            name="v20_rule_proposals",
            owner_module="v20.knowledge",
            purpose="Knowledge-to-rule proposals released to shadow training and later promotion review.",
            columns=(
                ColumnSpec("proposal_id", "text", purpose="stable rule proposal id"),
                ColumnSpec("source_knowledge_id", "text", purpose="source reviewed or draft knowledge id"),
                ColumnSpec("status", "text", purpose="released_to_shadow_training, promoted, rejected"),
                *common,
            ),
            primary_key=("proposal_id",),
        ),
        TableSpec(
            name="v20_llm_artifacts",
            owner_module="v20.llm",
            purpose="Bounded LLM extraction, rewrite, critique, and modeling artifacts.",
            columns=(
                ColumnSpec("artifact_id", "text", purpose="stable LLM artifact id"),
                ColumnSpec("task_name", "text", purpose="bounded LLM task contract name"),
                ColumnSpec("validation_status", "text", purpose="accepted, rejected, fallback, shadow_only"),
                *common,
            ),
            primary_key=("artifact_id",),
        ),
    )


def _initial_migration(tables: tuple[TableSpec, ...]) -> MigrationSpec:
    sql = tuple(_create_table_sql(table) for table in tables)
    return MigrationSpec(
        migration_id="v20_0001_initial_authoritative_tables",
        description="Create V20 authoritative Postgres tables without mutating runtime truth.",
        sql=sql,
    )


def _corpus_index_migration() -> MigrationSpec:
    return MigrationSpec(
        migration_id="v20_0002_corpus_query_indexes",
        description="Create query indexes for the 518K corpus snapshots so Postgres can replace local SQLite as the query authority.",
        sql=(
            "CREATE INDEX IF NOT EXISTS idx_v20_corpus_snapshots_input_hash ON v20_corpus_snapshots(input_hash);",
            "CREATE INDEX IF NOT EXISTS idx_v20_corpus_payload_day_master ON v20_corpus_snapshots ((payload->>'day_master'));",
            "CREATE INDEX IF NOT EXISTS idx_v20_corpus_payload_day_master_element ON v20_corpus_snapshots ((payload->>'day_master_element'));",
            "CREATE INDEX IF NOT EXISTS idx_v20_corpus_payload_day_master_capacity ON v20_corpus_snapshots ((payload->>'day_master_capacity'));",
            "CREATE INDEX IF NOT EXISTS idx_v20_corpus_payload_cluster_key ON v20_corpus_snapshots ((payload->>'cluster_key'));",
            "CREATE INDEX IF NOT EXISTS idx_v20_corpus_payload_wealth ON v20_corpus_snapshots (((payload->>'wealth_feature_present')::boolean));",
            "CREATE INDEX IF NOT EXISTS idx_v20_corpus_payload_gin ON v20_corpus_snapshots USING gin (payload);",
        ),
    )


def _feedback_ledger_index_migration() -> MigrationSpec:
    return MigrationSpec(
        migration_id="v20_0003_feedback_ledger_indexes",
        description="Create query indexes for feedback and structured calibration ledgers imported from local append-only records.",
        sql=(
            "CREATE INDEX IF NOT EXISTS idx_v20_feedback_ledger_source_hash ON v20_feedback_ledger(source_hash);",
            "CREATE INDEX IF NOT EXISTS idx_v20_feedback_ledger_payload_gin ON v20_feedback_ledger USING gin (payload);",
        ),
    )


def _decision_registry_index_migration() -> MigrationSpec:
    return MigrationSpec(
        migration_id="v20_0004_decision_registry_indexes",
        description="Create query indexes for DecisionRegistry review records and approval workflows.",
        sql=(
            "CREATE INDEX IF NOT EXISTS idx_v20_decision_registry_subject_id ON v20_decision_registry(subject_id);",
            "CREATE INDEX IF NOT EXISTS idx_v20_decision_registry_status ON v20_decision_registry(decision_status);",
            "CREATE INDEX IF NOT EXISTS idx_v20_decision_registry_payload_gin ON v20_decision_registry USING gin (payload);",
        ),
    )


def _create_table_sql(table: TableSpec) -> str:
    column_lines = [_column_sql(column) for column in table.columns]
    pk = ", ".join(table.primary_key)
    column_lines.append(f"PRIMARY KEY ({pk})")
    body = ",\n  ".join(column_lines)
    return f"CREATE TABLE IF NOT EXISTS {table.name} (\n  {body}\n);"


def _column_sql(column: ColumnSpec) -> str:
    nullability = "" if column.nullable else " NOT NULL"
    default = ""
    if column.name in {"created_at", "updated_at"}:
        default = " DEFAULT now()"
    return f"{column.name} {column.data_type}{default}{nullability}"
