import { request } from "./api";
import type { HomeAbuExpression, HomeMingliExplanation } from "./homeExplanationTypes";
import type {
  HomeCandidateMechanismEvidenceDepth,
  HomeMechanismCandidate,
  HomeMechanismComparison,
  HomeMechanismEvidence,
  HomeMechanismEvidenceDepth,
} from "./homeMechanismTypes";
import type {
  HomeCandidateMechanismQualification,
  HomeMechanismQualification,
} from "./homeQualificationTypes";
import type { HomeReadingBrief } from "./homeReadingTypes";
import type { HomeRelationEffectAdmissionReviewEnvelope } from "./homeRelationEffectAdmissionTypes";
import type { HomeRelationEffectResearchFrontierEnvelope } from "./homeRelationEffectFrontierTypes";
import type {
  HomeSourceCoordinateReview,
  HomeSourceCoordinateReviewVector,
} from "./homeSourceReviewTypes";
import type { HomeSourceDiscussionAbstentionReceipt } from "./homeSourceDiscussionTypes";
import type {
  HomeSourceUsabilityCarrier,
  HomeSourceUsabilityPrerequisiteEnvelope,
} from "./homeSourceUsabilityTypes";

export type { HomeReadingBrief } from "./homeReadingTypes";
export type { HomeRelationEffectAdmissionReviewEnvelope } from "./homeRelationEffectAdmissionTypes";
export type { HomeRelationEffectResearchFrontierEnvelope } from "./homeRelationEffectFrontierTypes";
export type { HomeMechanismQualification } from "./homeQualificationTypes";
export type {
  HomeCandidateMechanismEvidenceDepth,
  HomeMechanismEvidenceDepth,
} from "./homeMechanismTypes";
export type {
  HomeSourceCoordinateReview,
  HomeSourceCoordinateReviewVector,
} from "./homeSourceReviewTypes";
export type { HomeSourceDiscussionAbstentionReceipt } from "./homeSourceDiscussionTypes";
export type {
  HomeSourceUsabilityCarrier,
  HomeSourceUsabilityPrerequisiteEnvelope,
} from "./homeSourceUsabilityTypes";

export interface HomeQuantFoundation {
  vector_ref: string;
  vector_hash: string;
  vector_version: string;
  case_ref: string;
  chart_version_ref: string;
  quant_profile_ref: string;
  quant_profile_hash: string;
  day_master_stem: string;
  day_master_element: "wood" | "fire" | "earth" | "metal" | "water";
  day_master_polarity: "yin" | "yang";
  visible_stem_total: 4;
  hidden_stem_membership_total: number;
  element_measurements: Array<{
    element: "wood" | "fire" | "earth" | "metal" | "water";
    visible_stem_count: number;
    hidden_stem_membership_count: number;
    total_membership_count: number;
    total_membership_share: number;
  }>;
  polarity_measurements: Array<{
    polarity: "yin" | "yang";
    visible_stem_count: number;
    hidden_stem_membership_count: number;
    total_membership_count: number;
  }>;
  ten_god_occurrences: Array<{
    occurrence_ref: string;
    pillar_slot: "year" | "month" | "day" | "hour";
    layer: "VISIBLE_STEM" | "HIDDEN_STEM";
    stem: string;
    branch: string | null;
    membership_order: number | null;
    label: string;
    evidence_refs: string[];
  }>;
  ten_god_counts: Array<{
    label: string;
    visible_count: number;
    hidden_membership_count: number;
  }>;
  source_manifestation_evidence: Array<{
    evidence_ref: string;
    visible_slot: "year" | "month" | "day" | "hour";
    visible_stem: string;
    source_slot: "year" | "month" | "day" | "hour";
    source_branch: string;
    hidden_stem: string;
    source_match_kind:
      | "EXACT_IDENTITY"
      | "SAME_ELEMENT_DIFFERENT_IDENTITY";
    evidence_states: string[];
    evidence_refs: string[];
    effect_status: "EFFECT_UNRESOLVED";
  }>;
  measurement_semantics: "DETERMINISTIC_UNWEIGHTED_STRUCTURE";
  calibration_status: "NOT_CALIBRATED";
  forbidden_conclusions: string[];
  read_only: true;
}

export interface HomeTimingEvidence {
  vector_ref: string;
  vector_hash: string;
  vector_version: string;
  case_ref: string;
  chart_version_ref: string;
  life_case_revision_ref: string;
  timing_profile_ref: string;
  timing_profile_hash: string;
  analysis_date: string;
  timezone: string;
  day_master_stem: string;
  coordinates: Array<{
    coordinate_ref: string;
    layer: "DAYUN" | "ANNUAL" | "MONTHLY";
    pillar: string;
    stem: string;
    branch: string;
    ten_god_label: string;
    start_year: number | null;
    end_year: number | null;
    calculation_status: "DETERMINISTIC_COORDINATE";
  }>;
  relation_evidence: Array<{
    evidence_ref: string;
    timing_coordinate_ref: string;
    timing_layer: "DAYUN" | "ANNUAL" | "MONTHLY";
    timing_branch: string;
    natal_slot: "year" | "month" | "day" | "hour";
    natal_branch: string;
    relation_type:
      | "same_branch_membership"
      | "six_clash_membership"
      | "six_harmony_membership";
    evidence_refs: string[];
    rule_ref: string;
    relation_status: "MEMBERSHIP_PRESENT";
    effect_status: "UNRESOLVED";
  }>;
  candidate_overlaps: Array<{
    overlap_ref: string;
    timing_coordinate_ref: string;
    timing_layer: "DAYUN" | "ANNUAL" | "MONTHLY";
    timing_ten_god_label: string;
    candidate_ref: string;
    matching_role_ids: string[];
    overlap_status: "LABEL_OVERLAP_ONLY";
    activation_status: "UNRESOLVED";
    effect_status: "UNRESOLVED";
  }>;
  timing_semantics: "COORDINATE_AND_MEMBERSHIP_ONLY";
  activation_status: "UNRESOLVED";
  effect_status: "UNRESOLVED";
  calibration_status: "NOT_CALIBRATED";
  forbidden_conclusions: string[];
  read_only: true;
}

export interface HomeLifeDomainEvidence {
  vector_ref: string;
  vector_hash: string;
  vector_version: string;
  case_ref: string;
  chart_version_ref: string;
  life_case_revision_ref: string;
  mechanism_vector_ref: string;
  mechanism_vector_hash: string;
  timing_vector_ref: string;
  timing_vector_hash: string;
  policy_ref: string;
  policy_hash: string;
  observations: Array<{
    observation_ref: string;
    domain: "career" | "wealth" | "relationship";
    label: string;
    signal_status:
      | "TIMING_MECHANISM_OVERLAP"
      | "TIMING_AND_MECHANISM_PRESENT"
      | "TIMING_ONLY"
      | "MECHANISM_ONLY"
      | "NO_BOUNDED_EVIDENCE";
    statement: string;
    observation_prompt: string;
    timing_coordinate_refs: string[];
    mechanism_candidate_refs: string[];
    overlap_refs: string[];
    evidence_refs: string[];
    unresolved_dimensions: string[];
    outcome_status: "UNRESOLVED";
    probability_status: "NOT_COMPUTED";
    professional_verdict_allowed: false;
  }>;
  evidence_semantics: "ATTENTION_WINDOW_ONLY";
  outcome_status: "UNRESOLVED";
  probability_status: "NOT_COMPUTED";
  professional_verdict_allowed: false;
  canonical_write_allowed: false;
  read_only: true;
}

export interface HomeSnapshot {
  scope: "HOME_CASE";
  context_ref: string;
  context_hash: string;
  profile: {
    profile_ref: string;
    display_name: string;
  };
  case: {
    case_ref: string;
    subject_kind: "HUMAN_OWNER";
    status: "ACTIVE";
    case_version: number;
  };
  case_options: Array<{
    case_ref: string;
    profile_ref: string;
    display_name: string;
    status: "ACTIVE" | "INACTIVE";
    pillars: Record<"year" | "month" | "day" | "hour", string>;
    active: boolean;
  }>;
  chart: {
    chart_version_ref: string;
    version: number;
    pillars: Record<"year" | "month" | "day" | "hour", string>;
    chart_hash: string;
  };
  life_case: {
    life_case_revision_ref: string;
    revision: number;
    status: string;
    revision_hash: string;
  };
  tree: {
    tree_ref: string;
    projection_version: number;
    scene_ref: string;
    phenotype: {
      profile_version: string;
      fact_basis: string;
      element_membership_ratios: Record<
        "wood" | "fire" | "earth" | "metal" | "water",
        number
      >;
      crown_spread: number;
      branch_lift: number;
      root_spread: number;
      bark_definition: number;
      surface_moisture: number;
      semantic_status: "VISUAL_METAPHOR_ONLY";
    };
    read_only: true;
    source_kind: "CANONICAL_SCENE_PROJECTION";
  };
  mingli: {
    authority: "MINGLI_FACT_AUTHORITY";
    pillars: Record<"year" | "month" | "day" | "hour", string>;
    facts: Array<{
      fact_ref: string;
      fact_type: string;
      subject_ref: string;
      object_ref: string | null;
      authority: string;
      fact_json: Record<string, unknown>;
      source_ref: string;
      fact_hash: string;
    }>;
    reading: {
      reading_ref: string;
      reading_hash: string;
      reading_version: string;
      case_ref: string;
      chart_version_ref: string;
      life_case_revision_ref: string;
      foundation_profile: HomeKnowledgeProfileBinding;
      candidate_rule_profile: HomeKnowledgeProfileBinding;
      quant_foundation_profile: HomeKnowledgeProfileBinding;
      quant_vector_ref: string;
      quant_vector_hash: string;
      source_review_profile: HomeKnowledgeProfileBinding;
      source_review_vector_ref: string;
      source_review_vector_hash: string;
      mechanism_evidence_profile: HomeKnowledgeProfileBinding;
      mechanism_vector_ref: string;
      mechanism_vector_hash: string;
      timing_evidence_profile: HomeKnowledgeProfileBinding;
      timing_vector_ref: string;
      timing_vector_hash: string;
      life_domain_vector_ref: string;
      life_domain_vector_hash: string;
      fact_refs: string[];
      candidate_refs: string[];
      decision_refs: string[];
      unresolved_dimensions: string[];
      status:
        | "BOUNDED_FACTS_AVAILABLE"
        | "STRUCTURE_CANDIDATES_UNRESOLVED"
        | "MECHANISM_CANDIDATES_UNRESOLVED";
      read_only: true;
    };
    quant_foundation: HomeQuantFoundation;
    source_coordinate_review: HomeSourceCoordinateReviewVector;
    source_usability_prerequisite: HomeSourceUsabilityPrerequisiteEnvelope;
    source_discussion_receipt: HomeSourceDiscussionAbstentionReceipt;
    relation_effect_frontier: HomeRelationEffectResearchFrontierEnvelope;
    relation_effect_admission_review: HomeRelationEffectAdmissionReviewEnvelope;
    mechanism_evidence: HomeMechanismEvidence;
    timing_evidence: HomeTimingEvidence;
    life_domains: HomeLifeDomainEvidence;
    reading_brief: HomeReadingBrief;
    explanation: HomeMingliExplanation;
    mechanism_qualification: HomeMechanismQualification;
    mechanism_evidence_depth: HomeMechanismEvidenceDepth;
    abu_expression: HomeAbuExpression;
    read_only: true;
  };
  lab: {
    reading_ref: string;
    reading_hash: string;
    explanation_ref: string;
    explanation_hash: string;
    mechanism_qualification_ref: string;
    mechanism_qualification_hash: string;
    mechanism_qualification_candidates: HomeCandidateMechanismQualification[];
    mechanism_evidence_depth_ref: string;
    mechanism_evidence_depth_hash: string;
    mechanism_evidence_depth_candidates: HomeCandidateMechanismEvidenceDepth[];
    profile_bindings: {
      foundation: HomeKnowledgeProfileBinding;
      candidate_rules: HomeKnowledgeProfileBinding;
      quant_foundation: HomeKnowledgeProfileBinding;
      source_review: HomeKnowledgeProfileBinding;
      mechanism_evidence: HomeKnowledgeProfileBinding;
      timing_evidence: HomeKnowledgeProfileBinding;
    };
    quant_vector_ref: string;
    quant_vector_hash: string;
    source_review_vector_ref: string;
    source_review_vector_hash: string;
    source_coordinate_reviews: HomeSourceCoordinateReview[];
    source_usability_prerequisite_ref: string;
    source_usability_prerequisite_hash: string;
    source_usability_prerequisite_carriers: HomeSourceUsabilityCarrier[];
    source_discussion_receipt_ref: string;
    source_discussion_receipt_hash: string;
    relation_effect_frontier_ref: string;
    relation_effect_frontier_hash: string;
    relation_effect_admission_review_ref: string;
    relation_effect_admission_review_hash: string;
    mechanism_vector_ref: string;
    mechanism_vector_hash: string;
    timing_vector_ref: string;
    timing_vector_hash: string;
    life_domain_vector_ref: string;
    life_domain_vector_hash: string;
    life_domain_observations: HomeLifeDomainEvidence["observations"];
    timing_coordinates: HomeTimingEvidence["coordinates"];
    timing_relations: HomeTimingEvidence["relation_evidence"];
    timing_candidate_overlaps: HomeTimingEvidence["candidate_overlaps"];
    candidate_paths: Array<{
      candidate_ref: string;
      label: string;
      evidence_refs: string[];
      source_refs: string[];
      effect_status: "UNRESOLVED";
      capacity_status: "UNRESOLVED";
      usability_status: "UNRESOLVED";
      professional_admission_status: "UNRESOLVED";
    }>;
    mechanism_candidates: HomeMechanismCandidate[];
    mechanism_comparison: HomeMechanismComparison;
    interpretation_status: "BOUNDED_ATTENTION_COMPARISON";
    research_admission_status: "PROFILE_ADMISSION_REQUIRED";
    canonical_write_allowed: false;
  };
  units: {
    dream: { status: "THRESHOLD_AVAILABLE"; line: string };
    abu: {
      status: "MINGLI_BOUND_EXPRESSION";
      reading_ref: string;
      line: string;
    };
    theater: { status: "NO_ADMITTED_HOME_SCENE"; line: string };
  };
  lineage: {
    case_ref: string;
    life_case_revision_ref: string;
    chart_version_ref: string;
    scene_ref: string;
    fact_refs: string[];
  };
  boundaries: {
    private_to_account: true;
    dream_encounter_subject: false;
    canonical_write_allowed: false;
    visual_semantics: "VISUAL_METAPHOR_ONLY";
  };
}

export interface HomeKnowledgeProfileBinding {
  profile_id: string;
  profile_version: string;
  profile_hash: string;
  governance_status: string;
  runtime_scope: string;
  professionally_reviewed: boolean;
  source_refs: string[];
}

export function loadHomeExperience(): Promise<HomeSnapshot> {
  return request("/api/v60/experience/home");
}

export interface MechanismComparisonResult {
  decision_ref: string;
  decision_hash: string;
  already_recorded: boolean;
  authority: "RULE_ENGINE" | "LLM_REASONER";
  selected_candidate_ref: string;
  meaning: "ATTENTION_PRIORITY_ONLY";
  professional_verdict: false;
  canonical_mingli_write_allowed: false;
  reasoner_execution: {
    runtime_ref: string;
    provider_response_ref: string;
    context_hash: string;
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    duration_ms: number;
  } | null;
}

export function compareHomeMechanisms(): Promise<MechanismComparisonResult> {
  return request("/api/v60/experience/home/mechanism-comparison", {
    method: "POST",
  });
}

export interface OwnerCaseInput {
  display_name: string;
  gender: "male" | "female";
  calendar_type: "solar" | "lunar";
  birth_date: string;
  birth_time: string;
  birth_location: string;
  timezone: string;
  lunar_leap_month: boolean;
  true_solar_time_policy: "not_applied";
}

export function createOwnerCase(
  payload: OwnerCaseInput,
): Promise<{ case_ref: string; profile_ref: string; active: true }> {
  return request("/api/v60/cases", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function activateOwnerCase(
  caseRef: string,
): Promise<{ case_ref: string; active: true }> {
  return request(`/api/v60/cases/${encodeURIComponent(caseRef)}/activate`, {
    method: "POST",
  });
}
