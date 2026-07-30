import type { HomeRelationEffectResearchFrontierEnvelope } from "./homeRelationEffectFrontierTypes";

export const RELATION_EFFECT_ADMISSION_REVIEW_VERSION =
  "v60.mingli-relation-rule-admission-review.001" as const;

export const RELATION_EFFECT_ADMISSION_DIMENSIONS = [
  "APPLICABILITY_CONTEXT",
  "EFFECT_DIRECTION",
  "COMPLETION_CONDITIONS",
  "BLOCKING_CONDITIONS",
  "COUNTER_EVIDENCE",
  "PROFESSIONAL_PROVENANCE",
] as const;

export const RELATION_EFFECT_INTERPRETATIONS = [
  "RELATION_MEMBERSHIP_DISTURBANCE_ONLY",
  "SOURCE_OPEN_OR_EXPOSE",
  "SOURCE_DAMAGE_OR_REMOVE",
] as const;

export const RELATION_EFFECT_REJECTION_CODES = [
  "APPLICABILITY_AUTHORITY_INCOMPLETE",
  "EFFECT_DIRECTION_COMPETING",
  "COMPLETION_CONDITIONS_MISSING",
  "BLOCKING_CONDITIONS_MISSING",
  "COUNTER_EVIDENCE_MISSING",
  "PROFESSIONAL_PROVENANCE_MISSING",
] as const;

export const RELATION_EFFECT_BLOCKED_CLAIMS = [
  "AUTOMATIC_RELATION_DAMAGE",
  "AUTOMATIC_SOURCE_UNUSABLE",
] as const;

export type HomeRelationEffectAdmissionDimension =
  (typeof RELATION_EFFECT_ADMISSION_DIMENSIONS)[number];

export type HomeRelationEffectProposalDimensionStatus =
  | "VERIFIED"
  | "PARTIAL"
  | "COMPETING"
  | "UNSUPPORTED"
  | "MISSING";

export type HomeRelationEffectInterpretationId =
  (typeof RELATION_EFFECT_INTERPRETATIONS)[number];

export interface HomeRelationEffectCompetingInterpretation {
  interpretation_ref: string;
  interpretation_id: HomeRelationEffectInterpretationId;
  summary: string;
  status: "HELD";
  selected: false;
  effect_atom_created: false;
}

export interface HomeRelationEffectDimensionAssessment {
  dimension_id: HomeRelationEffectAdmissionDimension;
  submission_status: HomeRelationEffectProposalDimensionStatus;
  current_basis_refs: string[];
  gap: string;
  satisfied: false;
}

export interface HomeRelationEffectRuleAdmissionAssessment {
  assessment_ref: string;
  assessment_hash: string;
  demand_ref: string;
  source_review_ref: string;
  source_evidence_ref: string;
  intersection_ref: string;
  relation_fact_ref: string;
  carrier_ref: string;
  visible_slot: "year" | "month" | "day" | "hour";
  visible_stem: string;
  source_slot: "year" | "month" | "day" | "hour";
  source_branch: "午";
  peer_slot: "year" | "month" | "day" | "hour";
  peer_branch: "子";
  relation_type: "six_clash_membership";
  source_match_kind: "EXACT_IDENTITY";
  policy_ref: string;
  policy_hash: string;
  proposal_ref: string;
  proposal_hash: string;
  proposal_claim: string;
  interpretations: HomeRelationEffectCompetingInterpretation[];
  dimension_assessments: HomeRelationEffectDimensionAssessment[];
  disposition: "REJECTED_PRE_ADMISSION";
  candidate_truth_status: "NOT_EVALUATED_AS_TRUE_OR_FALSE";
  rejection_codes: (typeof RELATION_EFFECT_REJECTION_CODES)[number][];
  blocked_claims: (typeof RELATION_EFFECT_BLOCKED_CLAIMS)[number][];
  admitted_effect_atom_refs: string[];
  effect_status: "UNRESOLVED";
  usability_status: "UNRESOLVED";
}

export interface HomeRelationEffectAdmissionReviewEnvelope {
  review_ref: string;
  review_hash: string;
  review_version: typeof RELATION_EFFECT_ADMISSION_REVIEW_VERSION;
  case_ref: string;
  chart_version_ref: string;
  reading_ref: string;
  reading_hash: string;
  frontier_ref: string;
  frontier_hash: string;
  policy_ref: string;
  policy_hash: string;
  proposal_ref: string;
  proposal_hash: string;
  assessments: HomeRelationEffectRuleAdmissionAssessment[];
  reviewed_demand_count: number;
  rejected_pre_admission_count: number;
  admitted_effect_rule_count: 0;
  frontier_scope_invariant_demand_refs: string[];
  frontier_match_scope_demand_refs: string[];
  deferred_match_scope_demand_refs: string[];
  unreviewed_scope_invariant_demand_refs: string[];
  disposition: "REJECTED_PRE_ADMISSION" | "NOT_TRIGGERED";
  review_semantics: "SHORTCUT_ADMISSION_REJECTION_NOT_EFFECT_NEGATION";
  effect_status: "UNRESOLVED";
  usability_status: "UNRESOLVED";
  provider_invoked: false;
  owner_professional_review_invoked: false;
  knowledge_promotion_request_created: false;
  gate_invoked: false;
  decision_created: false;
  selection_authority: false;
  professional_verdict_allowed: false;
  probability_claim_allowed: false;
  canonical_write_allowed: false;
  read_only: true;
}

export interface HomeRelationEffectAdmissionDisplayBindings {
  frontier: HomeRelationEffectResearchFrontierEnvelope;
  reading: {
    case_ref: string;
    chart_version_ref: string;
    reading_ref: string;
    reading_hash: string;
    read_only: true;
  };
  lab: {
    reading_ref: string;
    reading_hash: string;
    relation_effect_frontier_ref: string;
    relation_effect_frontier_hash: string;
    relation_effect_admission_review_ref: string;
    relation_effect_admission_review_hash: string;
  };
}
