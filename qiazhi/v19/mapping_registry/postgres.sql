CREATE TABLE IF NOT EXISTS v19_mapping_units (
    id BIGSERIAL PRIMARY KEY,
    mapping_id TEXT NOT NULL UNIQUE,
    domain TEXT NOT NULL CHECK (domain IN ('wealth')),
    source_signal TEXT NOT NULL,
    target_signal TEXT NOT NULL,
    mapping_type TEXT NOT NULL CHECK (mapping_type IN ('lookup', 'bounded_value_mapping', 'aggregation')),
    value_map JSONB NOT NULL,
    conditions JSONB NOT NULL DEFAULT '{}'::jsonb,
    version TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('draft', 'reviewed', 'deprecated')),
    created_by TEXT NOT NULL,
    reviewed_by TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_v19_mapping_units_domain_status
    ON v19_mapping_units (domain, status);

CREATE INDEX IF NOT EXISTS idx_v19_mapping_units_source_signal
    ON v19_mapping_units (source_signal);

CREATE INDEX IF NOT EXISTS idx_v19_mapping_units_target_signal
    ON v19_mapping_units (target_signal);
