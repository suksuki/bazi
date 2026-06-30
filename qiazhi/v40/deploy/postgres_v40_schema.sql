-- Qiazhi V40 isolated runtime schema.
-- All tables must use v40_ prefix and live in qiazhi_v40.

CREATE TABLE IF NOT EXISTS v40_runtime_records (
    reading_id TEXT PRIMARY KEY,
    version TEXT NOT NULL DEFAULT 'v40.runtime_record.v1',
    runtime_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v40_evaluation_cases (
    case_id TEXT PRIMARY KEY,
    version TEXT NOT NULL DEFAULT 'v40.evaluation_case_spec.v1',
    case_type TEXT NOT NULL,
    case_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v40_evaluation_runs (
    run_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    reading_id TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT 'v40.evaluation_run_result.v1',
    status TEXT NOT NULL,
    metric_json JSONB NOT NULL,
    run_json JSONB NOT NULL,
    release_gate_id TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v40_evaluation_runs_case
ON v40_evaluation_runs (case_id);

CREATE TABLE IF NOT EXISTS v40_evaluation_batches (
    batch_id TEXT PRIMARY KEY,
    candidate_version TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT 'v40.evaluation_batch_summary.v1',
    summary_json JSONB NOT NULL,
    recommendation TEXT NOT NULL,
    production_write_allowed BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v40_training_label_events (
    event_id TEXT PRIMARY KEY,
    reading_id TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT 'v40.training_label_event.v1',
    label_json JSONB NOT NULL,
    local_only BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v40_training_label_events_reading
ON v40_training_label_events (reading_id);

CREATE TABLE IF NOT EXISTS v40_training_impact_diffs (
    training_run_id TEXT PRIMARY KEY,
    base_version TEXT NOT NULL,
    candidate_version TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT 'v40.training_impact_diff.v1',
    diff_json JSONB NOT NULL,
    recommendation TEXT NOT NULL,
    production_write_allowed BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v40_global_weight_versions (
    weight_version_id TEXT PRIMARY KEY,
    source_training_run_id TEXT NOT NULL,
    release_gate_id TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT 'v40.global_weight_version.v1',
    weight_json JSONB NOT NULL,
    active BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v40_release_readiness (
    readiness_id TEXT PRIMARY KEY,
    candidate_version TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT 'v40.release_readiness_summary.v1',
    summary_json JSONB NOT NULL,
    recommendation TEXT NOT NULL,
    production_write_allowed BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v40_weight_activation_reviews (
    review_id TEXT PRIMARY KEY,
    weight_version_id TEXT NOT NULL,
    release_readiness_id TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT 'v40.weight_activation_review.v1',
    review_json JSONB NOT NULL,
    decision TEXT NOT NULL,
    activation_applied BOOLEAN NOT NULL DEFAULT false,
    production_write_allowed BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v40_shadow_compare_runs (
    compare_id TEXT PRIMARY KEY,
    source_export_id TEXT NOT NULL,
    v40_reading_id TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT 'v40.shadow_compare_result.v1',
    compare_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v40_release_gates (
    gate_id TEXT PRIMARY KEY,
    candidate_version TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT 'v40.release_gate_result.v1',
    gate_json JSONB NOT NULL,
    recommendation TEXT NOT NULL,
    production_write_allowed BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
