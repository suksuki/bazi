export type ElementName = "wood" | "fire" | "earth" | "metal" | "water" | "";
export type Polarity = "yin" | "yang" | "";

export interface HiddenStemFact {
  stem: string;
  ten_god: string;
  element: ElementName;
  polarity: Polarity;
}

export interface AllowedChartFact {
  fact_ref: string;
  fact_type: string;
  display_value: string;
  visual_anchor: string;
  pillar_slot: "year" | "month" | "day" | "hour" | "";
  pillar_label: string;
  stem: string;
  branch: string;
  stem_element: ElementName;
  stem_polarity: Polarity;
  branch_element: ElementName;
  branch_polarity: Polarity;
  visible_ten_god: string;
  hidden_stems: HiddenStemFact[];
}

export interface ApprovedClaim {
  claim_ref: string;
  category: string;
  approved_meaning: string;
  spoken_summary: string;
  subtitle_summary: string;
  certainty: "low" | "medium" | "high";
  conditions: string[];
  counter_signals: string[];
  evidence_refs: string[];
  visual_anchors: string[];
}

export interface ApprovedReasoningStep {
  step_ref: string;
  premise: string;
  conclusion: string;
  source_refs: string[];
  visual_anchor: string;
}

export interface MingliExperienceEnvelope {
  envelope_id: string;
  schema_version: "deepbazi.mingli_experience_envelope.v1";
  mode: "personal_ready" | "chart_facts_only" | "observer";
  source: {
    chart_version: string;
    life_case_version: string | null;
    case_ref: string | null;
    generated_at: string;
    source_hash: string;
  };
  allowed_chart_facts: AllowedChartFact[];
  approved_claims: ApprovedClaim[];
  approved_reasoning_steps: ApprovedReasoningStep[];
  competing_hypotheses: Array<{
    hypothesis_ref: string;
    approved_meaning: string;
    unresolved_reason: string;
  }>;
  uncertainty: { level: "low" | "medium" | "high"; reasons: string[] };
  must_not_say: string[];
}

export interface ExperienceCaseSummary {
  case_id: string;
  profile_id: string | null;
  display_name: string;
  case_version: string;
  status: string;
  baseline_available: boolean;
  experience_url: string;
}

export interface NarrationSegment {
  segment_id: string;
  order: number;
  kind: "thesis" | "work_path" | "condition" | "uncertainty";
  title: string;
  text: string;
  visual_anchor_ids: string[];
  visual_cues: Array<{ at_ms: number; action: string; target: string }>;
}

export interface NarrationManifest {
  manifest_id: string;
  case_id: string;
  segments: NarrationSegment[];
}

export interface NarrationStatus {
  status: "ready" | "missing";
  speech_asset_id: string;
  audio_url: string;
  audio_format: string;
}

export interface SpeechAsset {
  speech_asset_id: string;
  media: {
    audio_url: string;
    playback_variants: Array<{ format: "opus"; audio_url: string }>;
  };
}

export type CanvasStage = "natal" | "luck" | "year";
export type CanvasLayer = "generation_control" | "combination" | "conflict" | "work_path";
export type CanvasEpistemicStatus =
  | "fact"
  | "derived"
  | "candidate"
  | "committed"
  | "blocked"
  | "hypothetical"
  | "presentation_only";

export interface CanvasTrace {
  source_mode: "canonical" | "committed" | "derived" | "hypothetical" | "presentation";
  epistemic_status: CanvasEpistemicStatus;
  source_refs: string[];
  commitment_refs: string[];
  uncertainty: string[];
  rejection_or_block_reasons: string[];
  disclosure: "public" | "member" | "practitioner" | "research";
}

export interface CanvasSemanticSlot {
  slot_ref: string;
  slot_type: "natal_year" | "natal_month" | "natal_day" | "natal_hour" | "luck" | "year";
  label: string;
  stem: string;
  branch: string;
  hidden_stems: string[];
  immutable: boolean;
  trace: CanvasTrace;
}

export interface CanvasNode {
  node_ref: string;
  label: string;
  node_type: string;
  semantic_slot_ref: string;
  element: ElementName;
  polarity: Polarity;
  ten_god: string;
  trace: CanvasTrace;
}

export interface CanvasRelation {
  relation_ref: string;
  from_node_ref: string;
  to_node_ref: string;
  relation_type: string;
  label: string;
  semantic_state: "latent" | "active" | "reinforced" | "weakened" | "blocked";
  trace: CanvasTrace;
  state_trace: CanvasTrace;
  change_reason_refs: string[];
}

export interface CanvasPath {
  path_ref: string;
  label: string;
  node_refs: string[];
  relation_refs: string[];
  required_refs: string[];
  semantic_state: "latent" | "active" | "reinforced" | "weakened" | "blocked";
  trace: CanvasTrace;
  state_trace: CanvasTrace;
  change_reason_refs: string[];
}

export interface MingliCanvasSpec {
  schema_version: "deepbazi.mingli_canvas_spec.v1";
  identity: {
    canvas_spec_id: string;
    chart_version_id: string;
    temporal_snapshot_id: string;
    life_case_id: string;
    audience_role: string | null;
    content_hash: string;
  };
  stage: CanvasStage;
  semantic_slots: CanvasSemanticSlot[];
  nodes: CanvasNode[];
  relations: CanvasRelation[];
  clusters: Array<{
    cluster_ref: string;
    label: string;
    node_refs: string[];
    relation_refs: string[];
    trace: CanvasTrace;
  }>;
  paths: CanvasPath[];
  epistemology: {
    epistemic_statuses: CanvasEpistemicStatus[];
    source_refs: string[];
    commitment_refs: string[];
    uncertainty: string[];
    rejection_or_block_reasons: string[];
    must_not_say: string[];
  };
}

export interface CanvasObjectDelta {
  object_type: "node" | "relation" | "cluster" | "path";
  target_ref: string;
  change_type: "introduced" | "removed" | "activated" | "reinforced" | "weakened" | "blocked" | "reopened" | "unchanged";
  before_state: string;
  after_state: string;
  reason_refs: string[];
  source_refs: string[];
}

export interface CanvasDiffSpec {
  diff_id: string;
  from_spec_id: string;
  to_spec_id: string;
  source_action_ref: string;
  added_nodes: CanvasObjectDelta[];
  removed_nodes: CanvasObjectDelta[];
  added_relations: CanvasObjectDelta[];
  removed_relations: CanvasObjectDelta[];
  changed_relations: CanvasObjectDelta[];
  introduced_paths: CanvasObjectDelta[];
  removed_paths: CanvasObjectDelta[];
  activated_paths: CanvasObjectDelta[];
  blocked_paths: CanvasObjectDelta[];
  reopened_paths: CanvasObjectDelta[];
  reinforced_paths: CanvasObjectDelta[];
  weakened_paths: CanvasObjectDelta[];
  unchanged_paths: CanvasObjectDelta[];
  explanation_refs: string[];
  uncertainty: string[];
}

export interface CanvasContextPack {
  context_pack_id: string;
  canvas_spec_id: string;
  diff_spec_id: string;
  role: string;
  current_stage: CanvasStage;
  selected_object_refs: string[];
  visible_layers: string[];
  committed_path_refs: string[];
  candidate_path_refs: string[];
  blocked_path_refs: string[];
  diff_reason_refs: string[];
  uncertainty: string[];
  must_not_say: string[];
  disclosed_object_refs: string[];
}

export interface CanvasLayerProjection {
  layer_id: CanvasLayer;
  label: string;
  description: string;
  relation_refs: string[];
  available: boolean;
  count: number;
}

export interface CanvasChangeGroup {
  change_type: "introduced" | "removed" | "activated" | "reinforced" | "weakened" | "blocked" | "reopened" | "unchanged";
  label: string;
  count: number;
  items: Array<{
    target_ref: string;
    object_type: string;
    label: string;
    before_state: string;
    after_state: string;
    reason_refs: string[];
  }>;
}

export interface CanvasStageProjection {
  stage: CanvasStage;
  title: string;
  summary: string;
  spec: MingliCanvasSpec;
  diff: CanvasDiffSpec | null;
  context: CanvasContextPack;
  layers: CanvasLayerProjection[];
  default_layer_id: CanvasLayer;
  change_groups: CanvasChangeGroup[];
}

export interface ReadOnlySixPillarCanvas {
  schema_version: "deepbazi.read_only_six_pillar_canvas.v1";
  status: "read_only_canvas_ready";
  case_id: string;
  role: string;
  stage_order: CanvasStage[];
  default_stage: CanvasStage;
  source: {
    chart_version_id: string;
    life_case_id: string;
    life_case_version: string;
    cognitive_record_id: string;
    luck_pillar: string;
    luck_year_range: number[];
    annual_pillar: string;
    analysis_year: number | null;
    timing_validation_status: string;
    timing_publicly_supported: boolean;
  };
  path_availability: {
    status: "available" | "unavailable";
    message: string;
    committed_path_count: number;
    candidate_path_count: number;
  };
  stages: Record<CanvasStage, CanvasStageProjection>;
  renderer_policy: {
    read_only: true;
    allowed_interactions: string[];
    forbidden_interactions: string[];
  };
  boundaries: string[];
  llm_used: false;
  formal_state_writes: false;
  sandbox_mutations: false;
}
