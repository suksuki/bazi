from __future__ import annotations

V30_TABLES = (
    "v30_readings",
    "v30_runtime_traces",
    "v30_feedback_events",
    "v30_hidden_factor_states",
    "v30_validation_cases",
    "v30_m3_knowledge_units",
    "v30_m3_rule_specs",
    "v30_m3_portrait_assets",
    "v30_m3_validation_snapshots",
    "v30_m3_source_backlog",
    "v30_diagnosis_runs",
    "v30_diagnosis_rule_matches",
    "v30_diagnosis_paths",
    "v30_diagnosis_portraits",
    "v30_diagnosis_claims",
    "v30_diagnosis_feedback",
    "v30_policy_pointers",
    "v30_artifacts",
    "v30_product_users",
    "v30_product_sessions",
    "v30_bazi_profiles",
)


def require_v30_table(table_name: str) -> str:
    if not table_name.startswith("v30_"):
        raise ValueError(f"V30 storage may not touch non-v30 table: {table_name}")
    return table_name


def redis_key(env: str, resource: str, identifier: str) -> str:
    key = f"v30:{env}:{resource}:{identifier}"
    if not key.startswith("v30:"):
        raise ValueError(f"V30 Redis key must start with v30:, got {key}")
    return key
