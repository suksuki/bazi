from __future__ import annotations

from v30.storage.names import V30_TABLES


CREATE_TABLE_STATEMENTS = {
    "v30_readings": """
CREATE TABLE IF NOT EXISTS v30_readings (
  reading_id TEXT PRIMARY KEY,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
""".strip(),
    "v30_runtime_traces": """
CREATE TABLE IF NOT EXISTS v30_runtime_traces (
  trace_id TEXT PRIMARY KEY,
  reading_id TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
""".strip(),
    "v30_feedback_events": """
CREATE TABLE IF NOT EXISTS v30_feedback_events (
  event_id TEXT PRIMARY KEY,
  reading_id TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
""".strip(),
    "v30_hidden_factor_states": """
CREATE TABLE IF NOT EXISTS v30_hidden_factor_states (
  state_id TEXT PRIMARY KEY,
  reading_id TEXT NOT NULL,
  context_id TEXT NOT NULL,
  payload JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
""".strip(),
    "v30_validation_cases": """
CREATE TABLE IF NOT EXISTS v30_validation_cases (
  case_id TEXT PRIMARY KEY,
  payload JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
""".strip(),
    "v30_m3_knowledge_units": """
CREATE TABLE IF NOT EXISTS v30_m3_knowledge_units (
  unit_id TEXT PRIMARY KEY,
  unit_type TEXT NOT NULL,
  domain TEXT NOT NULL,
  family TEXT NOT NULL,
  pack_id TEXT NOT NULL,
  pack_version TEXT NOT NULL,
  payload JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
""".strip(),
    "v30_m3_rule_specs": """
CREATE TABLE IF NOT EXISTS v30_m3_rule_specs (
  rule_id TEXT PRIMARY KEY,
  domain TEXT NOT NULL,
  decision_state TEXT NOT NULL,
  payload JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
""".strip(),
    "v30_m3_portrait_assets": """
CREATE TABLE IF NOT EXISTS v30_m3_portrait_assets (
  asset_id TEXT PRIMARY KEY,
  asset_type TEXT NOT NULL,
  domain TEXT NOT NULL,
  payload JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
""".strip(),
    "v30_m3_validation_snapshots": """
CREATE TABLE IF NOT EXISTS v30_m3_validation_snapshots (
  snapshot_id TEXT PRIMARY KEY,
  family TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
""".strip(),
    "v30_m3_source_backlog": """
CREATE TABLE IF NOT EXISTS v30_m3_source_backlog (
  backlog_id TEXT PRIMARY KEY,
  source_family_id TEXT NOT NULL,
  queue_state TEXT NOT NULL,
  priority TEXT NOT NULL,
  review_status TEXT NOT NULL,
  target_domains JSONB NOT NULL,
  payload JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
""".strip(),
    "v30_diagnosis_runs": """
CREATE TABLE IF NOT EXISTS v30_diagnosis_runs (
  diagnosis_id TEXT PRIMARY KEY,
  reading_id TEXT NOT NULL,
  status TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
""".strip(),
    "v30_diagnosis_rule_matches": """
CREATE TABLE IF NOT EXISTS v30_diagnosis_rule_matches (
  rule_match_id TEXT PRIMARY KEY,
  diagnosis_id TEXT NOT NULL,
  reading_id TEXT NOT NULL,
  rule_id TEXT NOT NULL,
  domain_targets JSONB NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
""".strip(),
    "v30_diagnosis_paths": """
CREATE TABLE IF NOT EXISTS v30_diagnosis_paths (
  path_id TEXT NOT NULL,
  diagnosis_id TEXT NOT NULL,
  reading_id TEXT NOT NULL,
  mechanism TEXT NOT NULL,
  domain_targets JSONB NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (diagnosis_id, path_id)
);
""".strip(),
    "v30_diagnosis_portraits": """
CREATE TABLE IF NOT EXISTS v30_diagnosis_portraits (
  portrait_id TEXT NOT NULL,
  diagnosis_id TEXT NOT NULL,
  reading_id TEXT NOT NULL,
  domain TEXT NOT NULL,
  dimension TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (diagnosis_id, portrait_id)
);
""".strip(),
    "v30_diagnosis_claims": """
CREATE TABLE IF NOT EXISTS v30_diagnosis_claims (
  claim_id TEXT NOT NULL,
  diagnosis_id TEXT NOT NULL,
  reading_id TEXT NOT NULL,
  domain TEXT NOT NULL,
  claim_level TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (diagnosis_id, claim_id)
);
""".strip(),
    "v30_diagnosis_feedback": """
CREATE TABLE IF NOT EXISTS v30_diagnosis_feedback (
  feedback_id TEXT PRIMARY KEY,
  diagnosis_id TEXT NOT NULL,
  reading_id TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
""".strip(),
    "v30_policy_pointers": """
CREATE TABLE IF NOT EXISTS v30_policy_pointers (
  family TEXT PRIMARY KEY,
  artifact_id TEXT NOT NULL,
  payload JSONB NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
""".strip(),
    "v30_artifacts": """
CREATE TABLE IF NOT EXISTS v30_artifacts (
  artifact_id TEXT PRIMARY KEY,
  family TEXT NOT NULL,
  runtime_path TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
""".strip(),
}


def schema_sql() -> str:
    return "\n\n".join(CREATE_TABLE_STATEMENTS[table] for table in V30_TABLES)
