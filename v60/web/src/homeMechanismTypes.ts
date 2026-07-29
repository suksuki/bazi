export interface HomeMechanismCandidate {
  candidate_ref: string;
  pattern_ref: string;
  pattern_label: string;
  structural_statement: string;
  forbidden_shortcut: string;
  roles: Array<{
    role_id: "SOURCE" | "BRIDGE" | "TARGET";
    accepted_labels: string[];
    occurrence_refs: string[];
    occurrence_labels: string[];
    participant_slots: string[];
    direct_evidence_refs: string[];
    manifestation_evidence_refs: string[];
    visible_occurrence_count: number;
    hidden_occurrence_count: number;
  }>;
  support_evidence_refs: string[];
  context_evidence_refs: string[];
  counter_evidence_refs: string[];
  blocker_codes: string[];
  competing_candidate_refs: string[];
  structural_presence: "PRESENT";
  effect_status: "UNRESOLVED";
  capacity_status: "UNRESOLVED";
  usability_status: "UNRESOLVED";
  timing_activation_status: "UNRESOLVED";
  counter_evidence_status: "NOT_ADMITTED";
  professional_admission_status: "UNRESOLVED";
  comparison_eligible: true;
  professional_selection_qualified: false;
  support_score_status: "NOT_COMPUTED_NO_ADMITTED_WEIGHTS";
}

export interface HomeMechanismEvidence {
  vector_ref: string;
  vector_hash: string;
  vector_version: string;
  case_ref: string;
  chart_version_ref: string;
  quant_vector_ref: string;
  quant_vector_hash: string;
  mechanism_profile_ref: string;
  mechanism_profile_hash: string;
  candidates: HomeMechanismCandidate[];
  evidence_refs: string[];
  comparison_status:
    | "NO_CANDIDATE"
    | "ONE_CANDIDATE"
    | "MULTIPLE_CANDIDATES";
  interpretation_authority: "BOUNDED_REASONER_ATTENTION_ONLY";
  professional_verdict_allowed: false;
  probability_claim_allowed: false;
  canonical_write_allowed: false;
  read_only: true;
}

export interface HomeMechanismEvidenceDepth {
  depth_ref: string;
  depth_hash: string;
  depth_version: string;
  reading_ref: string;
  reading_hash: string;
  case_ref: string;
  chart_version_ref: string;
  quant_vector_ref: string;
  quant_vector_hash: string;
  mechanism_vector_ref: string;
  mechanism_vector_hash: string;
  timing_vector_ref: string;
  timing_vector_hash: string;
  selected_attention_candidate_ref: string | null;
  candidates: HomeCandidateMechanismEvidenceDepth[];
  semantics: "EVIDENCE_CHANNEL_CONTRAST_ONLY";
  professional_verdict_allowed: false;
  probability_claim_allowed: false;
  canonical_write_allowed: false;
  read_only: true;
}

export interface HomeCandidateMechanismEvidenceDepth {
  candidate_ref: string;
  pattern_ref: string;
  pattern_label: string;
  attention_status:
    | "PRIMARY_ATTENTION"
    | "DIRECT_COMPETITOR"
    | "UNRANKED";
  roles: Array<{
    role_id: "SOURCE" | "BRIDGE" | "TARGET";
    accepted_labels: string[];
    visible_labels: string[];
    hidden_labels: string[];
    carrier_state:
      | "VISIBLE_AND_HIDDEN"
      | "VISIBLE_ONLY"
      | "HIDDEN_ONLY";
    visible_occurrence_refs: string[];
    hidden_occurrence_refs: string[];
    month_branch_occurrence_refs: string[];
    exact_source_evidence_refs: string[];
    elemental_source_evidence_refs: string[];
    same_pillar_source_evidence_refs: string[];
    month_branch_source_evidence_refs: string[];
    direct_evidence_refs: string[];
    source_effect_status: "UNRESOLVED";
  }>;
  timing_overlaps: Array<{
    overlap_ref: string;
    timing_coordinate_ref: string;
    timing_layer: "DAYUN" | "ANNUAL" | "MONTHLY";
    timing_ten_god_label: string;
    matching_role_ids: string[];
    activation_status: "UNRESOLVED";
  }>;
  timing_relations: Array<{
    evidence_ref: string;
    timing_coordinate_ref: string;
    timing_layer: "DAYUN" | "ANNUAL" | "MONTHLY";
    natal_slot: "year" | "month" | "day" | "hour";
    relation_type:
      | "same_branch_membership"
      | "six_clash_membership"
      | "six_harmony_membership";
    matching_role_ids: string[];
    rule_ref: string;
    effect_status: "UNRESOLVED";
  }>;
  shared_participants: Array<{
    competing_candidate_ref: string;
    shared_occurrence_refs: string[];
    shared_labels: string[];
  }>;
  evidence_channels: Array<
    | "STRUCTURAL_ROLES"
    | "VISIBLE_CARRIERS"
    | "HIDDEN_MEMBERS"
    | "SOURCE_MANIFESTATION"
    | "MONTH_BRANCH_CONTEXT"
    | "TIMING_ROLE_OVERLAP"
    | "TIMING_RELATION_CONTEXT"
    | "SHARED_PARTICIPANT_COMPETITION"
  >;
  unresolved_dimensions: Array<
    | "ROOT_USABILITY"
    | "SEASONAL_CAPACITY"
    | "RELATION_EFFECT"
    | "TIMING_ACTIVATION"
    | "COUNTER_EVIDENCE"
    | "MECHANISM_EFFECT"
    | "PROFESSIONAL_ADMISSION"
  >;
  evidence_score_status: "NOT_COMPUTED";
  professional_admission: false;
}

export interface HomeMechanismComparison {
  comparison_version: string;
  request_id: string;
  reasoner_runtime: {
    runtime_ref: string;
    status: "READY" | "DISABLED" | "NOT_CONFIGURED" | "MISCONFIGURED";
    provider: string | null;
    model_ref: string | null;
    prompt_ref: string;
    network_calls_enabled: boolean;
    structured_output_required: true;
    canonical_domain_write_allowed: false;
  };
  candidate_count: number;
  decision_ref: string | null;
  decision_hash: string | null;
  authority: "RULE_ENGINE" | "LLM_REASONER" | null;
  status: "NOT_RUN" | "RESOLVED";
  selected_candidate_ref: string | null;
  rationale_summary: string | null;
  evidence_refs_used: string[];
  meaning: "ATTENTION_PRIORITY_ONLY";
  professional_verdict: false;
  canonical_mingli_write_allowed: false;
}
