-- DeepBeing V50 clean-room database schema.
-- V50 must use V50_DATABASE_URL and v50_* tables only.
-- Do not import or share retired product schemas.

CREATE TABLE IF NOT EXISTS v50_schema_version (
    id TEXT PRIMARY KEY,
    version TEXT NOT NULL,
    boundary TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

INSERT INTO v50_schema_version (id, version, boundary)
VALUES (
    'v50.schema',
    'v50.consolidated.006',
    'v50_database_single_migration_owner'
)
ON CONFLICT (id) DO UPDATE
SET version = EXCLUDED.version,
    boundary = EXCLUDED.boundary;

CREATE TABLE IF NOT EXISTS v50_birth_inputs (
    birth_input_id TEXT PRIMARY KEY,
    payload JSONB NOT NULL,
    input_quality TEXT NOT NULL DEFAULT 'unknown',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_alpha_identities (
    identity_ref TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    account_role TEXT NOT NULL,
    identity_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_user_accounts (
    user_id TEXT PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    account_role TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    password_salt TEXT NOT NULL,
    role_status TEXT NOT NULL DEFAULT 'self_declared',
    active BOOLEAN NOT NULL DEFAULT true,
    account_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_v50_single_active_admin
ON v50_user_accounts (account_role)
WHERE account_role = 'admin' AND active = true;

CREATE TABLE IF NOT EXISTS v50_user_sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES v50_user_accounts(user_id),
    token_hash TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_bazi_profiles (
    profile_id TEXT PRIMARY KEY,
    identity_ref TEXT REFERENCES v50_alpha_identities(identity_ref),
    user_id TEXT REFERENCES v50_user_accounts(user_id),
    profile_fingerprint TEXT NOT NULL,
    display_name TEXT NOT NULL,
    gender TEXT NOT NULL DEFAULT 'unknown',
    calendar_type TEXT NOT NULL,
    birth_date TEXT NOT NULL,
    birth_time TEXT NOT NULL,
    birth_location TEXT NOT NULL DEFAULT '',
    timezone TEXT NOT NULL,
    pillars JSONB NOT NULL DEFAULT '[]'::jsonb,
    is_default BOOLEAN NOT NULL DEFAULT false,
    deleted BOOLEAN NOT NULL DEFAULT false,
    profile_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(identity_ref, profile_fingerprint)
);

CREATE INDEX IF NOT EXISTS idx_v50_bazi_profiles_identity
ON v50_bazi_profiles (identity_ref, is_default DESC, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_v50_bazi_profiles_user
ON v50_bazi_profiles (user_id, is_default DESC, updated_at DESC);

-- Upgrade older clean-room installs through the same authoritative schema.
ALTER TABLE IF EXISTS v50_bazi_profiles ALTER COLUMN identity_ref DROP NOT NULL;
ALTER TABLE IF EXISTS v50_bazi_profiles
    ADD COLUMN IF NOT EXISTS user_id TEXT REFERENCES v50_user_accounts(user_id);
ALTER TABLE IF EXISTS v50_bazi_profiles
    ADD COLUMN IF NOT EXISTS deleted BOOLEAN NOT NULL DEFAULT false;

CREATE TABLE IF NOT EXISTS v50_mingli_agent_cases (
    case_id TEXT PRIMARY KEY,
    user_id TEXT REFERENCES v50_user_accounts(user_id),
    profile_id TEXT,
    case_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v50_agent_cases_user
ON v50_mingli_agent_cases (user_id, updated_at DESC);

-- Dream Bridge stores revocable projection grants and resumable experience
-- state only. Canonical Mingli facts remain owned by v50_mingli_agent_cases.
CREATE TABLE IF NOT EXISTS v50_dream_scene_grants (
    grant_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES v50_mingli_agent_cases(case_id) ON DELETE RESTRICT,
    public_scene_ref TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL,
    grant_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v50_dream_scene_grants_status
ON v50_dream_scene_grants (status, updated_at DESC);

CREATE TABLE IF NOT EXISTS v50_dream_visits (
    visit_id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL REFERENCES v50_user_accounts(user_id) ON DELETE CASCADE,
    state TEXT NOT NULL,
    visit_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v50_dream_visits_owner
ON v50_dream_visits (owner_user_id, updated_at DESC);

-- Return/departure navigation is deliberately separate from Mingli facts. These
-- records own cross-visit anchors, device fencing, and idempotent routing only.
CREATE TABLE IF NOT EXISTS v50_dream_navigation_records (
    record_id TEXT PRIMARY KEY,
    record_kind TEXT NOT NULL,
    viewer_id TEXT NOT NULL,
    case_namespace TEXT NOT NULL,
    source_visit_id TEXT NOT NULL,
    status TEXT NOT NULL,
    idempotency_key TEXT UNIQUE,
    migration_capability_hash TEXT UNIQUE,
    record_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v50_dream_navigation_lookup
ON v50_dream_navigation_records
    (viewer_id, case_namespace, record_kind, updated_at DESC);

CREATE TABLE IF NOT EXISTS v50_dream_control_leases (
    viewer_id TEXT NOT NULL,
    case_namespace TEXT NOT NULL,
    lease_epoch BIGINT NOT NULL,
    fence_token BIGINT NOT NULL,
    lease_id TEXT NOT NULL UNIQUE,
    client_instance_id TEXT NOT NULL,
    status TEXT NOT NULL,
    real_expires_at TIMESTAMPTZ NOT NULL,
    lease_json JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (viewer_id, case_namespace)
);

CREATE TABLE IF NOT EXISTS v50_dream_projection_outbox (
    outbox_id TEXT PRIMARY KEY,
    aggregate_ref TEXT NOT NULL,
    event_type TEXT NOT NULL,
    payload_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    delivered_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_v50_dream_projection_outbox_pending
ON v50_dream_projection_outbox (created_at)
WHERE delivered_at IS NULL;

-- Problem Flower and Fruit is a bounded subdomain of the existing Dream
-- runtime. Outcome evidence is deliberately kept in a separate table so no
-- pre-reveal projection query can accidentally return it.
CREATE TABLE IF NOT EXISTS v50_dream_game_content_packs (
    pack_id TEXT PRIMARY KEY,
    evidence_class TEXT NOT NULL,
    content_state TEXT NOT NULL,
    release_eligible BOOLEAN NOT NULL DEFAULT false,
    verified_real_gate_contribution INTEGER NOT NULL DEFAULT 0,
    pack_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v50_dream_game_content_gate
ON v50_dream_game_content_packs
    (evidence_class, content_state, release_eligible, updated_at DESC);

CREATE TABLE IF NOT EXISTS v50_dream_game_rounds (
    round_id TEXT PRIMARY KEY,
    pack_id TEXT NOT NULL REFERENCES v50_dream_game_content_packs(pack_id) ON DELETE RESTRICT,
    resident_scene_ref TEXT NOT NULL,
    content_state TEXT NOT NULL,
    round_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v50_dream_game_round_scene
ON v50_dream_game_rounds (resident_scene_ref, content_state, updated_at DESC);

CREATE TABLE IF NOT EXISTS v50_dream_game_system_seals (
    seal_id TEXT PRIMARY KEY,
    round_id TEXT NOT NULL REFERENCES v50_dream_game_rounds(round_id) ON DELETE RESTRICT,
    immutable_hash TEXT NOT NULL,
    seal_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_dream_game_outcome_evidence (
    evidence_id TEXT PRIMARY KEY,
    round_id TEXT NOT NULL UNIQUE REFERENCES v50_dream_game_rounds(round_id) ON DELETE RESTRICT,
    evidence_class TEXT NOT NULL,
    verification_status TEXT NOT NULL,
    immutable_hash TEXT NOT NULL,
    evidence_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_dream_game_attempts (
    attempt_id TEXT PRIMARY KEY,
    round_id TEXT NOT NULL REFERENCES v50_dream_game_rounds(round_id) ON DELETE RESTRICT,
    viewer_id TEXT NOT NULL REFERENCES v50_user_accounts(user_id) ON DELETE CASCADE,
    visit_id TEXT NOT NULL REFERENCES v50_dream_visits(visit_id) ON DELETE CASCADE,
    state TEXT NOT NULL,
    row_version BIGINT NOT NULL,
    attempt_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (round_id, viewer_id, visit_id)
);

CREATE INDEX IF NOT EXISTS idx_v50_dream_game_attempt_viewer
ON v50_dream_game_attempts (viewer_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS v50_dream_game_flowers (
    flower_id TEXT PRIMARY KEY,
    round_id TEXT NOT NULL UNIQUE REFERENCES v50_dream_game_rounds(round_id) ON DELETE RESTRICT,
    state TEXT NOT NULL,
    row_version BIGINT NOT NULL,
    flower_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_dream_game_records (
    record_id TEXT PRIMARY KEY,
    record_kind TEXT NOT NULL,
    round_id TEXT NOT NULL REFERENCES v50_dream_game_rounds(round_id) ON DELETE RESTRICT,
    viewer_id TEXT,
    immutable_hash TEXT NOT NULL,
    record_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v50_dream_game_record_lookup
ON v50_dream_game_records (round_id, viewer_id, record_kind, created_at DESC);

CREATE TABLE IF NOT EXISTS v50_dream_game_answers (
    round_id TEXT NOT NULL REFERENCES v50_dream_game_rounds(round_id) ON DELETE RESTRICT,
    viewer_id TEXT NOT NULL REFERENCES v50_user_accounts(user_id) ON DELETE RESTRICT,
    attempt_id TEXT NOT NULL REFERENCES v50_dream_game_attempts(attempt_id) ON DELETE RESTRICT,
    seal_id TEXT NOT NULL UNIQUE REFERENCES v50_dream_game_records(record_id) ON DELETE RESTRICT,
    immutable_hash TEXT NOT NULL,
    sealed_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (round_id, viewer_id)
);

CREATE INDEX IF NOT EXISTS idx_v50_dream_game_answers_round
ON v50_dream_game_answers (round_id, sealed_at, seal_id);

CREATE TABLE IF NOT EXISTS v50_mingli_cognitive_jobs (
    job_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    user_id TEXT REFERENCES v50_user_accounts(user_id),
    job_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v50_cognitive_jobs_user
ON v50_mingli_cognitive_jobs (user_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS v50_voice_validation_sessions (
    session_id TEXT PRIMARY KEY,
    participant_ref TEXT NOT NULL REFERENCES v50_user_accounts(user_id),
    case_id TEXT NOT NULL,
    arm TEXT NOT NULL,
    session_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v50_voice_validation_participant
ON v50_voice_validation_sessions (participant_ref, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_v50_voice_validation_case
ON v50_voice_validation_sessions (case_id, created_at DESC);

CREATE TABLE IF NOT EXISTS v50_theater_sessions (
    session_id TEXT PRIMARY KEY,
    session_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_theater_envelopes (
    envelope_id TEXT PRIMARY KEY,
    source_hash TEXT NOT NULL,
    envelope_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_theater_participants (
    participant_run_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES v50_theater_sessions(session_id) ON DELETE CASCADE,
    participant_json JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_theater_cues (
    cue_instance_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES v50_theater_sessions(session_id) ON DELETE CASCADE,
    cue_hash TEXT NOT NULL,
    cue_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_theater_events (
    event_id TEXT UNIQUE NOT NULL,
    session_id TEXT NOT NULL REFERENCES v50_theater_sessions(session_id) ON DELETE CASCADE,
    sequence INTEGER NOT NULL,
    scope TEXT NOT NULL,
    participant_run_id TEXT,
    event_json JSONB NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (session_id, sequence)
);

CREATE TABLE IF NOT EXISTS v50_topic_explorations (
    exploration_id TEXT PRIMARY KEY,
    participant_run_id TEXT NOT NULL,
    exploration_json JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v50_theater_events_scope
ON v50_theater_events (session_id, scope, sequence);

CREATE INDEX IF NOT EXISTS idx_v50_theater_participants_session
ON v50_theater_participants (session_id);

CREATE TABLE IF NOT EXISTS v50_legacy_runtime_usage (
    route_key TEXT NOT NULL,
    method TEXT NOT NULL,
    request_count BIGINT NOT NULL DEFAULT 0,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (route_key, method)
);

CREATE TABLE IF NOT EXISTS v50_calendar_normalizations (
    normalization_id TEXT PRIMARY KEY,
    birth_input_id TEXT NOT NULL REFERENCES v50_birth_inputs(birth_input_id),
    payload JSONB NOT NULL,
    confidence NUMERIC NOT NULL DEFAULT 0 CHECK (confidence >= 0 AND confidence <= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_readings (
    reading_id TEXT PRIMARY KEY,
    birth_input_id TEXT NOT NULL REFERENCES v50_birth_inputs(birth_input_id),
    topic TEXT NOT NULL DEFAULT 'overview',
    status TEXT NOT NULL DEFAULT 'draft',
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_mingli_materials (
    material_id TEXT PRIMARY KEY,
    reading_id TEXT NOT NULL REFERENCES v50_readings(reading_id),
    source_engine TEXT NOT NULL,
    material_type TEXT NOT NULL,
    topic TEXT NOT NULL DEFAULT 'unknown',
    raw_value JSONB NOT NULL DEFAULT '{}'::jsonb,
    normalized_value TEXT NOT NULL DEFAULT '',
    evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    knowledge_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    rule_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence NUMERIC NOT NULL DEFAULT 0 CHECK (confidence >= 0 AND confidence <= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_knowledge_nodes (
    node_id TEXT PRIMARY KEY,
    node_type TEXT NOT NULL,
    name TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    attributes JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    validation_status TEXT NOT NULL DEFAULT 'unvalidated',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_knowledge_edges (
    edge_id TEXT PRIMARY KEY,
    from_node_id TEXT NOT NULL REFERENCES v50_knowledge_nodes(node_id),
    to_node_id TEXT NOT NULL REFERENCES v50_knowledge_nodes(node_id),
    relation_type TEXT NOT NULL,
    weight NUMERIC NOT NULL DEFAULT 1 CHECK (weight >= 0 AND weight <= 2),
    conditions JSONB NOT NULL DEFAULT '{}'::jsonb,
    source_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    validation_status TEXT NOT NULL DEFAULT 'unvalidated',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_structure_observations (
    observation_id TEXT PRIMARY KEY,
    reading_id TEXT NOT NULL REFERENCES v50_readings(reading_id),
    structure_type TEXT NOT NULL,
    claim JSONB NOT NULL,
    material_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    knowledge_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence NUMERIC NOT NULL DEFAULT 0 CHECK (confidence >= 0 AND confidence <= 1),
    validation_status TEXT NOT NULL DEFAULT 'unvalidated',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_mingli_structure_profiles (
    profile_id TEXT PRIMARY KEY,
    reading_id TEXT NOT NULL REFERENCES v50_readings(reading_id),
    day_master_state JSONB,
    element_balance JSONB,
    ten_god_profile JSONB,
    root_profile JSONB,
    branch_relation_profile JSONB,
    timing_context_profile JSONB,
    ziwei_topic_activation_profile JSONB,
    observation_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    material_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    profile_count INTEGER NOT NULL DEFAULT 0 CHECK (profile_count >= 0),
    creates_judgment BOOLEAN NOT NULL DEFAULT false,
    calls_brain BOOLEAN NOT NULL DEFAULT false,
    llm_used BOOLEAN NOT NULL DEFAULT false,
    boundary TEXT NOT NULL DEFAULT 'structure_profile_organizes_materials_without_judgment',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_flow_observations (
    flow_id TEXT PRIMARY KEY,
    reading_id TEXT NOT NULL REFERENCES v50_readings(reading_id),
    flow_type TEXT NOT NULL,
    from_node TEXT NOT NULL,
    to_node TEXT NOT NULL,
    claim JSONB NOT NULL,
    structure_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    material_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence NUMERIC NOT NULL DEFAULT 0 CHECK (confidence >= 0 AND confidence <= 1),
    validation_status TEXT NOT NULL DEFAULT 'unvalidated',
    creates_judgment BOOLEAN NOT NULL DEFAULT false,
    calls_brain BOOLEAN NOT NULL DEFAULT false,
    llm_used BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_judgment_candidates (
    candidate_id TEXT PRIMARY KEY,
    reading_id TEXT NOT NULL REFERENCES v50_readings(reading_id),
    topic TEXT NOT NULL DEFAULT 'unknown',
    judgment_type TEXT NOT NULL,
    claim JSONB NOT NULL,
    flow_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    structure_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    material_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence NUMERIC NOT NULL DEFAULT 0 CHECK (confidence >= 0 AND confidence <= 1),
    must_not_say_checked BOOLEAN NOT NULL DEFAULT false,
    validation_status TEXT NOT NULL DEFAULT 'unvalidated',
    final_verdict BOOLEAN NOT NULL DEFAULT false,
    calls_brain BOOLEAN NOT NULL DEFAULT false,
    llm_used BOOLEAN NOT NULL DEFAULT false,
    user_facing_judgment BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_brain_verdicts (
    verdict_id TEXT PRIMARY KEY,
    reading_id TEXT NOT NULL REFERENCES v50_readings(reading_id),
    topic TEXT NOT NULL DEFAULT 'unknown',
    winning_candidate_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    rejected_candidate_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    conflict_summary TEXT NOT NULL DEFAULT '',
    probe_needed BOOLEAN NOT NULL DEFAULT false,
    confidence NUMERIC NOT NULL DEFAULT 0 CHECK (confidence >= 0 AND confidence <= 1),
    expression_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    claim JSONB NOT NULL,
    llm_decision_authority BOOLEAN NOT NULL DEFAULT false,
    llm_used BOOLEAN NOT NULL DEFAULT false,
    user_facing_expression BOOLEAN NOT NULL DEFAULT false,
    boundary TEXT NOT NULL DEFAULT 'brain_verdict_is_only_judgment_output',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_probe_questions (
    probe_id TEXT PRIMARY KEY,
    reading_id TEXT NOT NULL REFERENCES v50_readings(reading_id),
    topic TEXT NOT NULL DEFAULT 'unknown',
    reason_code TEXT NOT NULL,
    question_code TEXT NOT NULL,
    option_codes JSONB NOT NULL DEFAULT '[]'::jsonb,
    target_flow_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    target_judgment_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    updates_if_answered JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence_expected_gain NUMERIC NOT NULL DEFAULT 0 CHECK (confidence_expected_gain >= 0 AND confidence_expected_gain <= 1),
    user_cost NUMERIC NOT NULL DEFAULT 0 CHECK (user_cost >= 0 AND user_cost <= 1),
    ui_text TEXT NOT NULL DEFAULT '',
    boundary TEXT NOT NULL DEFAULT 'probe_question_is_structured_brain_exploration_not_ui_copy',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_conversation_states (
    conversation_state_id TEXT PRIMARY KEY,
    reading_id TEXT NOT NULL REFERENCES v50_readings(reading_id),
    active_probe_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    answered_probe_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    current_topic TEXT NOT NULL DEFAULT 'unknown',
    exploration_depth INTEGER NOT NULL DEFAULT 0 CHECK (exploration_depth >= 0),
    brain_verdict_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    last_user_reply_ref TEXT NOT NULL DEFAULT '',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_user_reply_interpretations (
    interpretation_id TEXT PRIMARY KEY,
    probe_id TEXT NOT NULL REFERENCES v50_probe_questions(probe_id),
    reading_id TEXT NOT NULL REFERENCES v50_readings(reading_id),
    user_answer_code TEXT NOT NULL,
    mapped_material_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    mapped_flow_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    mapped_judgment_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence_delta NUMERIC NOT NULL DEFAULT 0 CHECK (confidence_delta >= -1 AND confidence_delta <= 1),
    training_event_ref TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_hidden_attributes (
    attribute_id TEXT PRIMARY KEY,
    reading_id TEXT NOT NULL REFERENCES v50_readings(reading_id),
    key TEXT NOT NULL,
    value_code TEXT NOT NULL,
    confidence NUMERIC NOT NULL DEFAULT 0 CHECK (confidence >= 0 AND confidence <= 1),
    source TEXT NOT NULL DEFAULT 'user_probe_answer',
    evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    affects JSONB NOT NULL DEFAULT '[]'::jsonb,
    creates_judgment BOOLEAN NOT NULL DEFAULT false,
    boundary TEXT NOT NULL DEFAULT 'hidden_attribute_is_reality_evidence_not_mingli_judgment',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_twin_overlays (
    overlay_id TEXT PRIMARY KEY,
    reading_id TEXT NOT NULL REFERENCES v50_readings(reading_id),
    hidden_attributes JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    affects JSONB NOT NULL DEFAULT '[]'::jsonb,
    overlay_confidence NUMERIC NOT NULL DEFAULT 0 CHECK (overlay_confidence >= 0 AND overlay_confidence <= 1),
    creates_judgment BOOLEAN NOT NULL DEFAULT false,
    boundary TEXT NOT NULL DEFAULT 'twin_overlay_stores_reality_evidence_for_brain_reevaluation',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_probe_feedback_events (
    event_id TEXT PRIMARY KEY,
    probe_id TEXT NOT NULL REFERENCES v50_probe_questions(probe_id),
    target_flow TEXT NOT NULL DEFAULT '',
    user_answer_code TEXT NOT NULL,
    confidence_delta NUMERIC NOT NULL DEFAULT 0 CHECK (confidence_delta >= -1 AND confidence_delta <= 1),
    affected_policy TEXT NOT NULL,
    before_confidence NUMERIC NOT NULL DEFAULT 0 CHECK (before_confidence >= 0 AND before_confidence <= 1),
    after_confidence NUMERIC NOT NULL DEFAULT 0 CHECK (after_confidence >= 0 AND after_confidence <= 1),
    weight_version_id TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_portrait_symbols (
    symbol_id TEXT PRIMARY KEY,
    reading_id TEXT NOT NULL REFERENCES v50_readings(reading_id),
    symbol_type TEXT NOT NULL,
    symbol_code TEXT NOT NULL,
    label_key TEXT NOT NULL,
    material_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    structure_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    flow_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    judgment_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    brain_verdict_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    confidence NUMERIC NOT NULL DEFAULT 0 CHECK (confidence >= 0 AND confidence <= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_life_scene_graphs (
    scene_graph_id TEXT PRIMARY KEY,
    reading_id TEXT NOT NULL REFERENCES v50_readings(reading_id),
    portrait_symbols JSONB NOT NULL DEFAULT '[]'::jsonb,
    relations JSONB NOT NULL DEFAULT '[]'::jsonb,
    renderer_contract_version TEXT NOT NULL,
    brain_verdict_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_training_events (
    training_event_id TEXT PRIMARY KEY,
    reading_id TEXT NOT NULL DEFAULT '',
    source TEXT NOT NULL,
    target_weight_key TEXT NOT NULL,
    feedback_score NUMERIC NOT NULL DEFAULT 0 CHECK (feedback_score >= -1 AND feedback_score <= 1),
    before_weight NUMERIC NOT NULL DEFAULT 1 CHECK (before_weight >= 0.1 AND before_weight <= 1.5),
    after_weight NUMERIC NOT NULL DEFAULT 1 CHECK (after_weight >= 0.1 AND after_weight <= 1.5),
    weight_version_id TEXT NOT NULL DEFAULT '',
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_weight_versions (
    weight_version_id TEXT PRIMARY KEY,
    base_version_id TEXT NOT NULL DEFAULT '',
    weights JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_from_training_event_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    validation_result_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_synthetic_validation_cases (
    case_id TEXT PRIMARY KEY,
    birth_input JSONB NOT NULL,
    expected_materials JSONB NOT NULL DEFAULT '[]'::jsonb,
    expected_structure_hit JSONB NOT NULL DEFAULT '[]'::jsonb,
    expected_flow_hit JSONB NOT NULL DEFAULT '[]'::jsonb,
    expected_judgment_hit JSONB NOT NULL DEFAULT '[]'::jsonb,
    must_not_say JSONB NOT NULL DEFAULT '[]'::jsonb,
    expected_evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_validation_results (
    validation_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES v50_synthetic_validation_cases(case_id),
    run_id TEXT NOT NULL,
    structure_hit NUMERIC NOT NULL DEFAULT 0 CHECK (structure_hit >= 0 AND structure_hit <= 1),
    flow_hit NUMERIC NOT NULL DEFAULT 0 CHECK (flow_hit >= 0 AND flow_hit <= 1),
    judgment_hit NUMERIC NOT NULL DEFAULT 0 CHECK (judgment_hit >= 0 AND judgment_hit <= 1),
    evidence_coverage NUMERIC NOT NULL DEFAULT 0 CHECK (evidence_coverage >= 0 AND evidence_coverage <= 1),
    unsupported_assertion_rate NUMERIC NOT NULL DEFAULT 0 CHECK (unsupported_assertion_rate >= 0 AND unsupported_assertion_rate <= 1),
    must_not_say_violation BOOLEAN NOT NULL DEFAULT false,
    score NUMERIC NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_asset_import_runs (
    import_run_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    asset_groups JSONB NOT NULL DEFAULT '[]'::jsonb,
    dry_run BOOLEAN NOT NULL DEFAULT true,
    row_counts JSONB NOT NULL DEFAULT '{}'::jsonb,
    status TEXT NOT NULL DEFAULT 'draft',
    boundary TEXT NOT NULL DEFAULT 'v50_asset_import_preserves_v50_owned_knowledge_and_validation_assets',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_knowledge_cards (
    card_id TEXT PRIMARY KEY,
    domain TEXT NOT NULL,
    category TEXT NOT NULL,
    name_zh TEXT NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    consensus_level TEXT NOT NULL DEFAULT 'unknown',
    runtime_status TEXT NOT NULL DEFAULT 'missing',
    recommended_runtime_priority TEXT NOT NULL DEFAULT 'later',
    source_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    topic_mapping JSONB NOT NULL DEFAULT '[]'::jsonb,
    related_concepts JSONB NOT NULL DEFAULT '[]'::jsonb,
    payload JSONB NOT NULL,
    source_file TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    runtime_active BOOLEAN NOT NULL DEFAULT false,
    validation_status TEXT NOT NULL DEFAULT 'draft',
    boundary TEXT NOT NULL DEFAULT 'knowledge_card_is_canon_asset_not_runtime_rule',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_knowledge_card_drafts (
    draft_id TEXT PRIMARY KEY,
    source_pack_id TEXT NOT NULL,
    source_knowledge_id TEXT NOT NULL,
    domain TEXT NOT NULL,
    category TEXT NOT NULL,
    name_zh TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    confidence_prior NUMERIC NOT NULL DEFAULT 0 CHECK (confidence_prior >= 0 AND confidence_prior <= 1),
    recommended_runtime_priority TEXT NOT NULL DEFAULT 'later',
    v50_target_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    forbidden_usage JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    payload JSONB NOT NULL,
    source_file TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    requires_validation BOOLEAN NOT NULL DEFAULT true,
    runtime_active BOOLEAN NOT NULL DEFAULT false,
    llm_used BOOLEAN NOT NULL DEFAULT false,
    validation_status TEXT NOT NULL DEFAULT 'draft',
    boundary TEXT NOT NULL DEFAULT 'knowledge_card_draft_requires_validation_before_runtime',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_synthetic_chart_cases (
    case_id TEXT PRIMARY KEY,
    taxonomy_id TEXT NOT NULL,
    case_type TEXT NOT NULL,
    chart TEXT NOT NULL,
    birth_input JSONB NOT NULL,
    expected_structure JSONB NOT NULL DEFAULT '[]'::jsonb,
    expected_top_node JSONB NOT NULL DEFAULT '[]'::jsonb,
    expected_path JSONB NOT NULL DEFAULT '[]'::jsonb,
    expected_ablation JSONB NOT NULL DEFAULT '[]'::jsonb,
    must_not JSONB NOT NULL DEFAULT '[]'::jsonb,
    timing_overlay JSONB NOT NULL DEFAULT '{}'::jsonb,
    tags JSONB NOT NULL DEFAULT '[]'::jsonb,
    payload JSONB NOT NULL,
    source_file TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    runtime_active BOOLEAN NOT NULL DEFAULT false,
    llm_used BOOLEAN NOT NULL DEFAULT false,
    brain_used BOOLEAN NOT NULL DEFAULT false,
    training_performed BOOLEAN NOT NULL DEFAULT false,
    validation_status TEXT NOT NULL DEFAULT 'taxonomy_draft',
    boundary TEXT NOT NULL DEFAULT 'synthetic_chart_case_validates_structure_not_fortune',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_timing_model_candidates (
    model_id TEXT PRIMARY KEY,
    timing_layer TEXT NOT NULL,
    model_family TEXT NOT NULL,
    current_confidence NUMERIC NOT NULL DEFAULT 0 CHECK (current_confidence >= 0 AND current_confidence <= 1),
    changes JSONB NOT NULL DEFAULT '[]'::jsonb,
    does_not_change JSONB NOT NULL DEFAULT '[]'::jsonb,
    relation_to_natal JSONB NOT NULL DEFAULT '[]'::jsonb,
    relation_to_other_timing_layers JSONB NOT NULL DEFAULT '[]'::jsonb,
    simulator_outputs JSONB NOT NULL DEFAULT '[]'::jsonb,
    validation_plan JSONB NOT NULL DEFAULT '[]'::jsonb,
    risk_notes JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    payload JSONB NOT NULL,
    source_file TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    runtime_active BOOLEAN NOT NULL DEFAULT false,
    creates_judgment BOOLEAN NOT NULL DEFAULT false,
    calls_brain BOOLEAN NOT NULL DEFAULT false,
    calls_llm BOOLEAN NOT NULL DEFAULT false,
    mutates_natal_structure BOOLEAN NOT NULL DEFAULT false,
    boundary TEXT NOT NULL DEFAULT 'timing_model_candidate_is_research_policy_not_runtime_truth',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS v50_validation_reports (
    report_id TEXT PRIMARY KEY,
    report_type TEXT NOT NULL,
    report_group TEXT NOT NULL DEFAULT '',
    source_file TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    payload JSONB NOT NULL,
    created_by_script TEXT NOT NULL DEFAULT '',
    boundary TEXT NOT NULL DEFAULT 'validation_report_is_experiment_record_not_runtime_truth',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_v50_materials_reading_id ON v50_mingli_materials(reading_id);
CREATE INDEX IF NOT EXISTS idx_v50_structure_reading_id ON v50_structure_observations(reading_id);
CREATE INDEX IF NOT EXISTS idx_v50_structure_profile_reading_id ON v50_mingli_structure_profiles(reading_id);
CREATE INDEX IF NOT EXISTS idx_v50_flow_reading_id ON v50_flow_observations(reading_id);
CREATE INDEX IF NOT EXISTS idx_v50_judgment_reading_id ON v50_judgment_candidates(reading_id);
CREATE INDEX IF NOT EXISTS idx_v50_brain_verdicts_reading_id ON v50_brain_verdicts(reading_id);
CREATE INDEX IF NOT EXISTS idx_v50_probe_reading_id ON v50_probe_questions(reading_id);
CREATE INDEX IF NOT EXISTS idx_v50_conversation_reading_id ON v50_conversation_states(reading_id);
CREATE INDEX IF NOT EXISTS idx_v50_user_reply_reading_id ON v50_user_reply_interpretations(reading_id);
CREATE INDEX IF NOT EXISTS idx_v50_hidden_attribute_reading_id ON v50_hidden_attributes(reading_id);
CREATE INDEX IF NOT EXISTS idx_v50_twin_overlay_reading_id ON v50_twin_overlays(reading_id);
CREATE INDEX IF NOT EXISTS idx_v50_probe_feedback_probe_id ON v50_probe_feedback_events(probe_id);
CREATE INDEX IF NOT EXISTS idx_v50_knowledge_cards_domain ON v50_knowledge_cards(domain);
CREATE INDEX IF NOT EXISTS idx_v50_knowledge_cards_priority ON v50_knowledge_cards(recommended_runtime_priority);
CREATE INDEX IF NOT EXISTS idx_v50_knowledge_card_drafts_source_pack ON v50_knowledge_card_drafts(source_pack_id);
CREATE INDEX IF NOT EXISTS idx_v50_synthetic_chart_cases_case_type ON v50_synthetic_chart_cases(case_type);
CREATE INDEX IF NOT EXISTS idx_v50_timing_model_candidates_layer ON v50_timing_model_candidates(timing_layer);
CREATE INDEX IF NOT EXISTS idx_v50_validation_reports_type ON v50_validation_reports(report_type);
