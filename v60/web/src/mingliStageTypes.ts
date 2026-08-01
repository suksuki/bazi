export type MingliStageMode = "NATAL_4" | "NATAL_DAYUN_YEAR_6";
export type MingliStageSubjectId = "current" | "abu" | "duoduo";

export interface MingliStageSubject {
  subject_id: MingliStageSubjectId;
  display_name: string;
  subject_kind: "HUMAN_OWNER" | "CANONICAL_SYNTHETIC";
  identity_badge: "私密真实档案" | "角色合成设定";
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
  projection_version: "v60.mingli-stage-projection.002";
  subject_id: MingliStageSubjectId;
  case_ref: string;
  chart_version_ref: string;
  life_case_revision_ref: string;
  reading_ref: string | null;
  reading_hash: string | null;
  display_name: string;
  subject_kind: "HUMAN_OWNER" | "CANONICAL_SYNTHETIC";
  identity_badge: "私密真实档案" | "角色合成设定";
  privacy_scope: "PRIVATE_OWNER" | "PUBLIC_SYNTHETIC_SHOWCASE";
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
