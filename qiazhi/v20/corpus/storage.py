from __future__ import annotations


def corpus_storage_policy() -> dict[str, object]:
    return {
        "version": "v20.corpus_storage_policy.v1",
        "authoritative_backend": "postgres",
        "authoritative_tables": ["v20_corpus_snapshots", "v20_artifact_registry", "v20_run_registry"],
        "full_corpus_target_count": 518_400,
        "derived_local_backends": {
            "sqlite": {
                "role": "rebuildable_similarity_index_and_local_probe_cache",
                "authority": False,
                "sync_policy": "do_not_sync_between_macos_and_linux",
                "rebuild_source": "v20_corpus_snapshots_or_flat_labels_jsonl",
                "advantages": [
                    "zero_service_local_debugging",
                    "single_file_snapshot_for_fast_rebuilds",
                    "offline_similarity_probe_without_postgres",
                ],
            }
        },
        "required_hashes": ["input_hash", "core_version", "feature_compiler_version", "artifact_hash"],
        "guardrails": [
            "POSTGRES_IS_AUTHORITATIVE",
            "SQLITE_IS_DERIVED_AND_DISPOSABLE",
            "VERSIONED_ARTIFACTS_ONLY",
            "NO_UNREVIEWED_RUNTIME_USE",
        ],
    }


def corpus_postgres_index_plan() -> dict[str, object]:
    return {
        "version": "v20.corpus_postgres_index_plan.v1",
        "table": "v20_corpus_snapshots",
        "purpose": "Make the 518K structural corpus queryable without relying on the local SQLite cache.",
        "indexes": [
            "idx_v20_corpus_snapshots_input_hash",
            "idx_v20_corpus_payload_day_master",
            "idx_v20_corpus_payload_day_master_element",
            "idx_v20_corpus_payload_day_master_capacity",
            "idx_v20_corpus_payload_cluster_key",
            "idx_v20_corpus_payload_wealth",
            "idx_v20_corpus_payload_wealth_level",
            "idx_v20_corpus_payload_mainline_domains",
            "idx_v20_corpus_payload_gin",
        ],
        "query_surfaces": [
            "case_lookup",
            "same_day_master_search",
            "cluster_key_search",
            "wealth_feature_filter",
            "wealth_material_level_filter",
            "mainline_domain_filter",
            "jsonb_containment_for_feature_and_portrait_tags",
        ],
        "runtime_mutation": False,
        "guardrails": [
            "INDEX_PLAN_ONLY",
            "APPLY_REQUIRES_EXPLICIT_MIGRATION_OR_IMPORT_COMMAND",
            "SQLITE_REMAINS_OPTIONAL_LOCAL_CACHE",
        ],
    }
