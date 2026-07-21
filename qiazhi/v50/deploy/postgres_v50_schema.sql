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
    'v50.clean_room.001',
    'v50_database_clean_room_isolation'
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
