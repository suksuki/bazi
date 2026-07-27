export type LifeTreeQuestionCategory =
  | "factual_observation"
  | "candidate_comparison"
  | "discriminating"
  | "temporal_change"
  | "counterfactual"
  | "life_observation";

export interface LifeTreeQuestionOption {
  option_id: string;
  label_template: string;
  exploration_meaning: string;
}

export interface LifeTreeQuestion {
  instance_id: string;
  blueprint_id: string;
  blueprint_version: string;
  category: LifeTreeQuestionCategory;
  purpose: "lab_learning" | "life_observation";
  title: string;
  prompt: string;
  options: LifeTreeQuestionOption[];
  why_this_question: string;
  distinguished_hypothesis_refs: string[];
  distinguished_hypotheses: string[];
  relation_fact_revision_refs: string[];
  work_path_candidate_refs: string[];
  counterfactual_subject_refs: string[];
  source_foundation_ref: string;
  source_foundation_hash: string;
  provenance_refs: string[];
  life_domain: string;
  observation_window: string;
  reveal_policy: "NONE" | "REALITY_FEEDBACK";
  future_evidence_requirements: string[];
  professional_status: "STRUCTURAL_LEARNING" | "STRUCTURAL_CANDIDATE_ONLY";
  baseline_credit_allowed: false;
  permitted_write_owner: "TopicExploration";
  writes_life_case: false;
}

export interface LifeTreeExploration {
  exploration_id: string;
  participant_run_id: string;
  topic_id: string;
  responses: Record<string, string>;
  observations: string[];
  created_at: string;
  writes_life_case: false;
}

export interface LifeTreeSceneNode {
  node_id: string;
  organ: "LEAF" | "TRUNK" | "ROOT" | "FLOWER";
  category: LifeTreeQuestionCategory;
  status: "available" | "explored" | "locked" | "unavailable";
  question_refs: string[];
  projection_ref: string;
  visual_truth_authority: false;
}

export interface RealLifeTreeBootstrap {
  schema_version: string;
  data_source: "CURRENT_REAL_LIFECASE";
  case_id: string;
  participant_run_id: string;
  foundation_ref: string;
  foundation_hash: string;
  question_bank_version: string;
  question_count: number;
  questions: LifeTreeQuestion[];
  explorations: LifeTreeExploration[];
  tree_scene: {
    scene_id: string;
    foundation_ref: string;
    foundation_hash: string;
    nodes: LifeTreeSceneNode[];
    flower_unlocked: boolean;
    persistent_source: "TopicExploration";
    frontend_truth_inference_allowed: false;
  };
  tree_visual_profile: {
    schema_version: string;
    profile_id: string;
    source: "SERVER_DERIVED_CURRENT_LIFECASE_GRAPH";
    form: "wide_balanced" | "tall_tensed" | "compact_grounded";
    material: "dew_fed" | "sun_warmed" | "mineral_cool";
    metrics: {
      density: number;
      tension: number;
      moisture: number;
      light: number;
      growth: number;
      balance: number;
    };
    render_tokens: {
      scale_x: number;
      scale_y: number;
      rotation_deg: number;
      hue_rotate_deg: number;
      saturation: number;
      brightness: number;
      canopy_echo_opacity: number;
      ground_sheen_opacity: number;
    };
    visual_metaphor_only: true;
    professional_judgment: false;
    frontend_metric_inference_allowed: false;
  };
  empty_state: string;
  professional_state: {
    resolved_count: number;
    message: string;
    main_work_declared: boolean;
    fail_closed?: boolean;
  };
}

export interface RelationFactProjection {
  relation_fact_id: string;
  fact_revision_ref: string;
  fact_key_ref: string;
  relation_family: string;
  relation_kind: string;
  participant_refs: string[];
  participant_kinds: string[];
  participant_coordinates: Array<{
    node_ref: string;
    scope: string;
    slot: string;
    level: string;
    component: string;
    temporal_snapshot_ref?: string;
  }>;
  participant_roles: Record<string, string>;
  directionality: "directed" | "symmetric";
  direct_or_mediated: "direct" | "mediated" | "not_applicable" | "unsupported" | "illegal";
  mediator_refs: string[];
  prerequisite_refs: string[];
  exclusion_refs: string[];
  source_layer: string;
  time_scope: string;
  professional_stage: string;
  rule_id: string;
  rule_version: string;
  provenance_status: "complete" | "incomplete" | "quarantined" | "illegal";
  legality_class:
    | "legal_direct"
    | "legal_mediated"
    | "containment"
    | "positional"
    | "unsupported"
    | "illegal_cross_layer";
  legality_policy_version: string;
  missing_requirements: string[];
  default_path_eligible: boolean;
  inventory_visible: boolean;
  fact_state: string;
  activation_state: string;
  temporal_stage: string;
  effect_status: string;
  unresolved_reasons: string[];
  evidence_refs: string[];
}

export interface WorkPathProjection {
  work_path_candidate_ref: string;
  label: string;
  actor_ref: string;
  actor_role: string;
  action: string;
  receiver_ref: string;
  receiver_role: string;
  ordered_fact_revision_refs: string[];
  participant_coordinates: RelationFactProjection["participant_coordinates"];
  blocker_types: string[];
  shared_resource_refs: string[];
  competing_path_group_ref: string;
  bottleneck_node_refs: string[];
  axes: Record<string, string>;
  unresolved_reasons: string[];
  provenance_refs: string[];
  professional_rank: null;
  main_work_declared: false;
}

export interface RelationWorkProjection {
  foundation_ref: string;
  foundation_content_hash: string;
  factual_view: RelationFactProjection[];
  candidate_path_view: WorkPathProjection[];
  professionally_resolved_view: Array<{
    effect_resolution_ref: string;
    relation_fact_revision_refs: string[];
    resolved_effect_atoms: string[];
  }>;
  consumer_inference_allowed: false;
}

export interface RealMingliLabBootstrap {
  schema_version: string;
  data_source: "CURRENT_REAL_LIFECASE";
  case_id: string;
  relation_work: RelationWorkProjection;
  relation_audit: {
    schema_version: string;
    policy_version: string;
    total_relation_facts: number;
    legal_direct_edges: number;
    legal_mediated_relations: number;
    containment_edges: number;
    positional_edges: number;
    unsupported_edges: number;
    illegal_cross_layer_edges: number;
    missing_rule_id: number;
    missing_provenance: number;
    missing_participant_constraints: number;
    visible_inventory_fact_refs: string[];
    quarantined_fact_count: number;
    quarantined_facts: Array<{
      relation_fact_id: string;
      relation_kind: string;
      participant_refs: string[];
      participant_kinds: string[];
      legality_class: string;
      provenance_status: string;
      missing_requirements: string[];
    }>;
    illegal_facts: Array<{
      relation_fact_id: string;
      relation_kind: string;
      participant_refs: string[];
      participant_kinds: string[];
      legality_class: string;
      provenance_status: string;
      missing_requirements: string[];
    }>;
    default_paths_consume_quarantine: false;
  };
  path_focus: {
    schema_version: string;
    selection_policy: string;
    selection_is_professional_ranking: false;
    main_work_declared: false;
    primary_path_ref: string;
    competition_path_ref: string;
    visible_path_refs: string[];
    hidden_candidate_count: number;
    primary_shape: "single_segment_candidate" | "multi_segment_candidate" | "none";
    key_blocker: {
      blocker_type: string;
      message: string;
    };
    empty_state: string;
  };
  canonical_timing: {
    default_stage: string;
    stages: Record<string, { summary: string }>;
  };
  learning_questions: LifeTreeQuestion[];
  professional_state: {
    resolved_count: number;
    message: string;
    main_work_declared: boolean;
    fail_closed: boolean;
  };
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    credentials: "same-origin",
    cache: "no-store",
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(String(payload.detail || `request_failed_${response.status}`));
  }
  return response.json() as Promise<T>;
}

export function loadRealLifeTree(caseId: string): Promise<RealLifeTreeBootstrap> {
  return requestJson(
    `/api/v50/experience/cases/${encodeURIComponent(caseId)}/life-tree/questions`,
  );
}

export async function answerRealLifeTreeQuestion(
  caseId: string,
  questionId: string,
  optionId: string,
): Promise<LifeTreeExploration> {
  const payload = await requestJson<{ exploration: LifeTreeExploration }>(
    `/api/v50/experience/cases/${encodeURIComponent(caseId)}/life-tree/questions/${encodeURIComponent(questionId)}/answer`,
    {
      method: "POST",
      body: JSON.stringify({ selected_option_id: optionId }),
    },
  );
  return payload.exploration;
}

export function loadRealMingliLab(caseId: string): Promise<RealMingliLabBootstrap> {
  return requestJson(
    `/api/v50/experience/cases/${encodeURIComponent(caseId)}/mingli-lab/relation-work`,
  );
}
