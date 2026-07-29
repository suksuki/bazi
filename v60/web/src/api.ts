export { request } from "./http";
export {
  loadBootstrap,
  loadSession,
  login,
  logout,
} from "./runtimeApi";
export {
  ensureEncounter,
  executeDreamCommand,
  loadDreamEntry,
  loadEncounter,
  returnToDreamGrove,
  selectDreamTree,
} from "./dreamRuntimeApi";

export interface RuntimeManifest {
  product_id: string;
  product_version: string;
  foundation_version: string;
  entry_experience: "PRIVATE_LIFE_TREE_HOME";
  engines: {
    context: string;
    decision: string;
    game: string;
    world: string;
    mingli: string;
    story: string;
  };
  architecture: {
    architecture_version: string;
    default_locale: "zh-CN";
    localization_status: "RESERVED";
    product_units: string[];
    product_core: "unit-mingli";
    priority_breakthrough: "unit-dream";
    unit_placements: Array<{
      unit_id: string;
      priority: number;
      role:
        | "CORE_TRUTH_PRODUCT"
        | "PRIORITY_GAME_BREAKTHROUGH"
        | "RESEARCH_IMPROVEMENT_LOOP"
        | "NATIVE_EXPRESSION_LAYER"
        | "INDEPENDENT_MEDIA_STUDIO";
      boundary: string;
    }>;
    modules: Array<{
      module_id: string;
      kind: "AUTHORITY" | "ENGINE" | "PRODUCT_UNIT" | "PLATFORM";
      version: string;
      status: "ACTIVE" | "BOUNDED" | "RESERVED";
      owns_schemas: string[];
      reads_from: string[];
      capabilities: string[];
      writes_canonical_state: boolean;
    }>;
  };
  v50_runtime_dependency: false;
}

export interface RuntimeAssetDelivery {
  asset_ref: string;
  asset_version: string;
  url: string;
  media_type: string;
  sha256: string;
}

export interface RuntimeMediaCue {
  cue_ref: string;
  version: string;
  trigger: string;
  playback: "LOOP" | "PLAY_ONCE";
  interruptible: boolean;
  deliveries: Record<string, RuntimeAssetDelivery>;
}

export interface RuntimeMediaManifest {
  registry_version: string;
  catalog_version: string;
  assets: {
    brand_logo: RuntimeAssetDelivery;
    grove_background: RuntimeAssetDelivery;
    life_world_background: RuntimeAssetDelivery;
  };
  cues: {
    abu_idle: RuntimeMediaCue;
    abu_guide_left: RuntimeMediaCue;
  };
}

export interface Bootstrap {
  manifest: RuntimeManifest;
  media: RuntimeMediaManifest;
  world: {
    world_ref: string;
    world_version: string;
    branch: string;
    current_epoch: number;
    current_tick: number;
  };
  experience: {
    state: "FOUNDATION_READY" | "FIRST_SLICE_READY";
    entry: "PRIVATE_LIFE_TREE_HOME";
    available_life_trees: number;
    unavailable_reason: string | null;
  };
}

export interface Session {
  account: {
    account_ref: string;
    email: string;
    display_name: string;
    account_role: string;
  };
  profiles: Array<{
    profile_ref: string;
    display_name: string;
  }>;
}

export interface TreeOrgan {
  key: string;
  organ_ref: string;
  role: "EVIDENCE_LEAF" | "STRUCTURE_BRANCH" | "QUESTION_FLOWER" | "OUTCOME_FRUIT";
  source_refs: string[];
  label: string;
  visible: boolean;
  status: "HIDDEN" | "AVAILABLE" | "COMPLETED" | "OPEN" | "SEALED" | "MATURED";
}

export interface UnitDisclosure {
  unit: "dream" | "mingli" | "abu" | "theater" | "lab";
  source_kinds: string[];
  source_refs: string[];
}

export interface DreamSnapshot {
  encounter: {
    encounter_ref: string;
    status: string;
    version: number;
    correlation_id: string;
    causation_id: string;
    chapter: "FIRST_VISIT" | "RETURN_VISIT";
    state: {
      observed_organs: string[];
      question_visible: boolean;
      answer_sealed: boolean;
      world_settled: boolean;
      revealed: boolean;
      reconciled: boolean;
    };
  };
  world: {
    world_ref: string;
    current_tick: number;
  };
  game: {
    engine_version: string;
    gameplay_id: "life_tree_question_v1";
    scene_id: string;
    scene_version: number;
    layout_key: "picture_book_fixed_tree";
    episode_ref: string;
    episode_version: number;
    content_key: string;
    phase:
      | "OBSERVING"
      | "QUESTION_OPEN"
      | "WAITING_FOR_WORLD"
      | "REVEAL_READY"
      | "REVEALED"
      | "COMPLETED";
    available_commands: string[];
  };
  actor: {
    actor_ref: string;
    display_name: string;
    actor_kind: string;
    projection_as_of_tick: number;
    public_timeline: {
      timeline_version: number;
      events: Array<{
        world_event_ref: string;
        summary: string;
        world_tick: number;
      }>;
    };
    state: Record<string, unknown> | null;
    state_visibility:
      | "CURRENT_COMMITTED"
      | "WITHHELD_OUTSIDE_EPISODE_HORIZON";
    projection_hash: string;
  };
  tree: {
    tree_ref: string;
    episode_ref: string;
    episode_version: number;
    projection_version: number;
    state: string;
    organs: TreeOrgan[];
    phenotype: {
      element_membership_ratios: Record<string, number>;
      semantic_status: string;
    };
    projection_hash: string;
    organ_projection_hash: string;
  };
  question: null | {
    question_ref: string;
    question_version: number;
    prompt: string;
    options: Array<{ choice_id: string; label: string }>;
    cutoff_tick: number;
    due_tick: number;
    flower_name: string;
  };
  human_seal: null | {
    answer_seal_ref: string;
    choice_id: string;
    sealed_at_tick: number;
  };
  fruit: null | {
    fruit_ref: string;
    status: string;
    fruit_version: number;
    fruit_json: Record<string, unknown>;
  };
  reveal: null | {
    reveal_ref: string;
    result: "SUPPORTED" | "PARTIAL" | "NOT_SUPPORTED";
    reveal_json: {
      decision_ref?: string;
      actual_event: string;
      actual_evidence: Array<{ evidence_ref: string; summary: string }>;
      baseline_credit: false;
      human_answer: { label: string };
      npc_answer: { label: string };
      atom_reconciliation: Record<
        string,
        { predicted: string; actual: string; matched: boolean }
      >;
    };
  };
  public_evidence: Array<{
    evidence_ref: string;
    summary: string;
    epistemic_role: string;
  }>;
  context: {
    context_ref: string;
    context_version: "v60.experience-context.003";
    context_hash: string;
    cutoff_tick: number;
    current_tick: number;
    source_counts: {
      baseline_evidence: number;
      revealed_evidence: number;
      formal_facts: number;
      post_reveal_decisions: number;
    };
    unit_disclosures: Record<
      "dream" | "mingli" | "abu" | "theater" | "lab",
      UnitDisclosure
    >;
    story: {
      phase: DreamSnapshot["game"]["phase"];
      content_key: string;
      disclosure:
        | "BASELINE_ONLY"
        | "SEALED_NO_OUTCOME"
        | "WORLD_COMMITTED_HIDDEN"
        | "OUTCOME_REVEALED";
    };
    sealed_outcome_included: false;
    hidden_npc_choice_included: false;
  };
  projections: {
    dream: {
      context_ref: string;
      disclosure: UnitDisclosure;
      authority: "DREAM_GAME_ENGINE";
      world_ref: string;
      question_ref: string;
      content_key: string;
      journey_title: string;
      journey_status: string;
    };
    mingli: {
      context_ref: string;
      disclosure: UnitDisclosure;
      chart_version_ref: string;
      life_case_revision_ref: string;
      pillars: Record<"year" | "month" | "day" | "hour", string>;
      facts: Array<{
        fact_ref: string;
        fact_type: string;
        subject_ref: string;
        object_ref: string | null;
        fact_json: Record<string, unknown>;
        source_ref: string;
      }>;
      authority: "MINGLI_FACT_AUTHORITY";
      read_only: true;
    };
    abu: {
      context_ref: string;
      disclosure: UnitDisclosure;
      speaker: "ABU";
      line: string;
      authority: "GUIDE_ONLY";
      fact_creation: false;
      decision_creation: false;
      content_key: string;
    };
    theater: {
      context_ref: string;
      disclosure: UnitDisclosure;
      scene_ref: string;
      story_version: string;
      content_key: string;
      phase: DreamSnapshot["game"]["phase"];
      narrative_disclosure:
        | "BASELINE_ONLY"
        | "SEALED_NO_OUTCOME"
        | "WORLD_COMMITTED_HIDDEN"
        | "OUTCOME_REVEALED";
      beat: string;
      evidence_refs: string[];
      decision_refs: string[];
      future_outcome_visible: false;
      revealed_outcome_visible: boolean;
      scene_plan: Record<string, unknown>;
    };
    lab: {
      context_ref: string;
      disclosure: UnitDisclosure;
      chart_version_ref: string;
      pillars: Record<"year" | "month" | "day" | "hour", string>;
      facts: Array<{
        fact_ref: string;
        fact_type: string;
        subject_ref: string;
        object_ref: string | null;
        fact_json: Record<string, unknown>;
        source_ref: string;
      }>;
      candidate_paths: Array<{
        candidate_ref: string;
        chart_version_ref: string;
        path_kind: "STRUCTURAL_RELATION_CANDIDATE";
        label: string;
        relation_fact_ref: string;
        relation_type: string;
        participants: Array<{
          participant_ref: string;
          slot: string;
          branch: string;
          label: string;
        }>;
        evidence_refs: string[];
        source_refs: string[];
        path_status: "STRUCTURE_CANDIDATE";
        structure_evidence_status: "SATISFIED" | "REJECTED" | "NOT_ADMITTED";
        qualification_receipts: Array<{
          receipt_ref: string;
          evaluator_version: string;
          candidate_ref: string;
          dimension: "STRUCTURE_EVIDENCE";
          status: "SATISFIED" | "REJECTED" | "NOT_ADMITTED";
          rule_ref: string | null;
          rule_hash: string | null;
          evidence_refs: string[];
          evaluated_claims: string[];
          missing_claims: string[];
          forbidden_conclusions: string[];
          reason: string;
          selection_authority: false;
          receipt_hash: string;
        }>;
        effect_status: "UNRESOLVED";
        capacity_status: "UNRESOLVED";
        usability_status: "UNRESOLVED";
        professional_admission_status: "UNRESOLVED";
        selection_qualified: false;
        missing_requirements: string[];
      }>;
      qualification_summary: {
        profile_ref: string;
        structure_evidence_satisfied: number;
        selection_qualified: number;
      };
      candidate_projection_status:
        | "STRUCTURE_CANDIDATES_AVAILABLE"
        | "NO_ADMITTED_RELATION_CANDIDATE";
      decision_route: {
        request_id: string;
        status: "UNRESOLVED";
        authority: "NONE";
        selected_candidate_ref: null;
        result: null;
        reason: string;
      };
      interpretation_status: string;
      effect_status: string;
      capacity_status: string;
      professional_admission_status: string;
      canonical_write_allowed: false;
    };
  };
  lineage: {
    life_case_revision_ref: string;
    chart_version_ref: string;
    scene_ref: string;
    question_ref: string;
    world_event_ref: string;
    evidence_refs: string[];
    revealed_evidence_refs: string[];
    decision_refs: string[];
  };
  continuation: {
    available: boolean;
    label: string | null;
    completed_encounter_count: number;
  };
}

export interface DreamGroveCandidate {
  candidate_ref: string;
  domain: "career" | "wealth" | "relationship";
  public_alias: string;
  premise: string;
  display_order: number;
  tree: {
    state: string;
    version: number;
    phenotype: {
      profile_version: string;
      fact_basis: string;
      element_membership_ratios: Record<string, number>;
      crown_spread: number;
      branch_lift: number;
      root_spread: number;
      bark_definition: number;
      surface_moisture: number;
      semantic_status: "VISUAL_METAPHOR_ONLY";
    };
    scene_hash: string;
  };
}

export interface DreamGrove {
  grove_version: "v60.dream-grove.001";
  selection_status: "AWAITING_TREE_SELECTION";
  candidates: DreamGroveCandidate[];
  hidden_outcome_included: false;
  hidden_npc_choice_included: false;
}

export type DreamEntry =
  | { kind: "GROVE"; grove: DreamGrove }
  | { kind: "ENCOUNTER"; snapshot: DreamSnapshot };

export type DreamCommand =
  | "OBSERVE_EVIDENCE"
  | "OBSERVE_STRUCTURE"
  | "OPEN_QUESTION"
  | "SEAL_ANSWER"
  | "REVEAL"
  | "RECONCILE"
  | "CONTINUE_ENCOUNTER"
  | "RETURN_TO_GROVE";
