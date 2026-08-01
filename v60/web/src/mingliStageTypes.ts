export type MingliStageMode = "NATAL_4" | "NATAL_DAYUN_YEAR_6";
export type MingliStageSubjectId = string;

export interface MingliStageSubject {
  subject_id: MingliStageSubjectId;
  display_name: string;
  subject_kind: "HUMAN_OWNER" | "HUMAN_REFERENCE" | "CANONICAL_SYNTHETIC";
  identity_badge: "私密真实档案" | "真实参考档案" | "角色合成设定";
  default_narrator_actor_id: "ABU_NARRATOR_V1" | "DUODUO_NARRATOR_V1";
}

export interface MingliStageColumn {
  column_ref: string;
  slot:
    | "NATAL_YEAR"
    | "NATAL_MONTH"
    | "NATAL_DAY"
    | "NATAL_HOUR"
    | "DAYUN"
    | "ANNUAL";
  label: string;
  source_layer: "NATAL" | "DAYUN" | "ANNUAL";
  pillar: string;
  stem: string;
  branch: string;
  coordinate_ref: string;
  start_year: number | null;
  end_year: number | null;
  start_date?: string;
  end_date?: string;
  calculation_status: "DETERMINISTIC_COORDINATE";
}

export interface MingliStageBody {
  body_ref: string;
  column_ref: string;
  role: "STEM" | "BRANCH";
  glyph: string;
  order: number;
}

export interface MingliStageRelation {
  relation_ref: string;
  relation_type: "six_clash_membership" | "six_harmony_membership";
  label: string;
  left_column_ref: string;
  right_column_ref: string;
  left_branch: string;
  right_branch: string;
  evidence_refs: string[];
  rule_ref: string;
  rule_hash: string;
  relation_status: "MEMBERSHIP_PRESENT";
  effect_status: "UNRESOLVED";
  usable_source_status: "UNRESOLVED";
}

export interface MingliStageProjection {
  projection_ref: string;
  projection_hash: string;
  projection_version: "v60.mingli-stage-projection.003";
  subject_id: MingliStageSubjectId;
  case_ref: string;
  chart_version_ref: string;
  life_case_revision_ref: string;
  reading_ref: string | null;
  reading_hash: string | null;
  display_name: string;
  subject_kind: "HUMAN_OWNER" | "HUMAN_REFERENCE" | "CANONICAL_SYNTHETIC";
  identity_badge: "私密真实档案" | "真实参考档案" | "角色合成设定";
  privacy_scope: "PRIVATE_OWNER" | "PRIVATE_REFERENCE" | "PUBLIC_SYNTHETIC_SHOWCASE";
  stage_mode: MingliStageMode;
  selected_year: number | null;
  available_years: number[];
  current_dayun_label: string;
  current_dayun_start_year: number;
  current_dayun_end_year: number;
  current_dayun_start_date: string;
  current_dayun_end_date: string;
  dayun_boundary_precision: "START_SOLAR_DATE_TIME_UNRESOLVED_ON_BOUNDARY_DAY";
  dayun_calculation_policy: "LUNAR_PYTHON_YUN_SECT_1_START_SOLAR_DATE_BOUNDARIES";
  dayun_resolution_status: "RESOLVED_OUTSIDE_BOUNDARY_DAY";
  annual_label_semantics: "SELECTED_SOLAR_YEAR_GANZHI";
  foundation_profile_ref: string;
  foundation_profile_hash: string;
  timing_profile_ref: string;
  timing_profile_hash: string;
  columns: MingliStageColumn[];
  bodies: MingliStageBody[];
  relations: MingliStageRelation[];
  narrator_actor_id: "ABU_NARRATOR_V1" | "DUODUO_NARRATOR_V1";
  narration_voice_status: "OWNER_SELECTED" | "AUDITION_CANDIDATE";
  stage_semantics: "COORDINATES_AND_MEMBERSHIP_ONLY";
  relation_effect_status: "UNRESOLVED";
  usable_source_status: "UNRESOLVED";
  professional_verdict_allowed: false;
  forbidden_conclusions: string[];
  source_refs: string[];
  read_only: true;
}

export interface MingliReadingSummaryProjection {
  summary_ref: string;
  summary_hash: string;
  summary_version: "v60.mingli-reading-summary.002";
  case_ref: string;
  chart_version_ref: string;
  life_case_revision_ref: string;
  reading_ref: string;
  reading_hash: string;
  subject_kind: "HUMAN_OWNER" | "HUMAN_REFERENCE" | "CANONICAL_SYNTHETIC";
  reading_brief: import("./homeReadingTypes").HomeReadingBrief;
  agent_runtime_status: "READY" | "DISABLED" | "MISCONFIGURED" | "UNQUALIFIED";
  agent_generation_available: boolean;
  agent_status: "READY" | "NOT_GENERATED";
  agent_reading: MingliAgentReading | null;
  image_projection_status: "AGENT_INTERPRETATION" | "NOT_GENERATED";
  professional_verdict_allowed: false;
  canonical_write_allowed: false;
  read_only: true;
}

export type MingliAgentConfidence = "LOW" | "MEDIUM" | "HIGH";

export interface MingliAgentHypothesis {
  hypothesis_id: "H1" | "H2";
  role: "PRIMARY" | "ALTERNATIVE";
  name: string;
  judgment: "WORKS_IF" | "PARTIAL" | "BLOCKED" | "COMPETING";
  mechanism_evidence_ids: string[];
  thesis: string;
  failure_condition: string;
  evidence_ids: string[];
  confidence: MingliAgentConfidence;
}

export interface MingliAgentDomainReading {
  headline: string;
  conclusion: string;
  causal_chain: string[];
  condition: string;
  evidence_ids: string[];
  confidence: MingliAgentConfidence;
}

export interface MingliAgentTimingLayerReading {
  coordinate_evidence_id: string;
  relation_evidence_ids: string[];
  conclusion: string;
  activation_chain: string[];
  evidence_ids: string[];
  confidence: "LOW" | "MEDIUM";
}

export interface MingliAgentOutput {
  first_look: string;
  whole_chart_thesis: string;
  day_master_state:
    | "STRONG"
    | "WEAK"
    | "BALANCED"
    | "FOLLOWING_TENDENCY"
    | "SPECIALIZED_TENDENCY"
    | "UNCERTAIN";
  support_selection: {
    root_status: "NONE" | "PRESENT";
    root_coordinates: string[];
    peer_coordinates: string[];
    resource_coordinates: string[];
  };
  day_master_rationale: string;
  day_master_evidence_ids: string[];
  hypotheses: MingliAgentHypothesis[];
  work_path: {
    path_statement: string;
    transformation_codes: Array<
      "GENERATES" | "CONTROLS" | "SUPPORTS" | "CONSTRAINS" | "CHANNELS" | "COMPETES"
    >;
    closure: "CLOSED" | "CONDITIONAL" | "BROKEN" | "UNCERTAIN";
    condition: string;
    evidence_ids: string[];
  };
  life_image: {
    title: string;
    image: string;
    explanation: string;
    evidence_ids: string[];
  };
  domains: Record<
    "personality" | "career" | "wealth" | "relationship" | "family",
    MingliAgentDomainReading
  >;
  timing: {
    natal_baseline: string;
    natal_evidence_ids: string[];
    dayun: MingliAgentTimingLayerReading;
    annual: MingliAgentTimingLayerReading;
    verification_signals: string[];
  };
  discriminating_question: string;
}

export interface MingliAgentReading {
  agent_reading_ref: string;
  agent_reading_hash: string;
  agent_reading_version: "v60.mingli-agent-reading.001";
  generation_key: string;
  requester_account_ref: string;
  case_ref: string;
  chart_version_ref: string;
  life_case_revision_ref: string;
  reading_ref: string;
  reading_hash: string;
  packet_ref: string;
  packet_hash: string;
  agent_profile_ref: string;
  agent_profile_hash: string;
  provider_id: string;
  model_ref: string;
  model_digest: string;
  provider_profile_ref: string;
  provider_profile_hash: string;
  prompt_ref: string;
  prompt_hash: string;
  provider_response_ref: string;
  output: MingliAgentOutput;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  duration_ms: number;
  interpretation_status: "AGENT_INTERPRETATION";
  owner_review_status: "NOT_REVIEWED";
  canonical_fact_write_allowed: false;
  read_only: true;
}

export type MingliNarrationPhase =
  | "PREPARING"
  | "READY"
  | "PLAYING"
  | "BUFFERING"
  | "PAUSED"
  | "ENDED"
  | "FAILED";

export interface MingliNarrationCue {
  cue_id: "STRUCTURE" | "RELATION_BOUNDARY" | "EVIDENCE_GAP" | "TIME_LAYER";
  text: string;
  start_ms: number;
  end_ms: number;
  semantic_action:
    | "PILLARS_PRESENT"
    | "RELATIONS_PRESENT"
    | "BOUNDARY_HOLD"
    | "TIME_COORDINATES_PRESENT";
}

export interface MingliNarrationAsset {
  narration_ref: string;
  narration_hash: string;
  narration_version: "v60.mingli-narration.002";
  requester_account_ref: string;
  case_ref: string;
  reading_ref: string | null;
  source_scope: "FORMAL_READING" | "CANONICAL_SYNTHETIC_DEMO";
  stage_projection_ref: string;
  stage_projection_hash: string;
  cue_set_ref: "v60.mingli-stage-guide-cues.001";
  script_ref: string;
  script_hash: string;
  actor_ref: "ABU_NARRATOR_V1" | "DUODUO_NARRATOR_V1";
  voice_profile_ref: string;
  voice_profile_hash: string;
  voice_profile_status: "OWNER_SELECTED" | "AUDITION_CANDIDATE";
  provider_profile_ref: string;
  provider_profile_hash: string;
  provider_deployment_ref: string;
  preparation_status: "READY";
  audio_mime_type: "audio/wav";
  audio_sha256: string;
  audio_byte_length: number;
  duration_ms: number;
  sample_rate_hz: 24000;
  channels: 1;
  sample_width_bytes: 2;
  cues: MingliNarrationCue[];
  clock_source: "HTML_AUDIO_CURRENT_TIME";
  refresh_policy: "READY_AT_ZERO";
  upstream_exposed_to_client: false;
}

export interface MingliNarrationReadyResponse {
  asset: MingliNarrationAsset;
  audio_url: string;
}

export interface MingliNarrationVisualClock {
  phase: MingliNarrationPhase | null;
  currentTimeMs: number;
  activeCueId: MingliNarrationCue["cue_id"] | null;
  cueProgress: number;
  semanticAction: MingliNarrationCue["semantic_action"] | null;
}

export type MingliStageViewContext =
  | {
      subjectId: MingliStageSubjectId;
      status: "LOADING" | "ERROR";
      projection: null;
    }
  | {
      subjectId: MingliStageSubjectId;
      status: "READY";
      projection: MingliStageProjection;
    };
