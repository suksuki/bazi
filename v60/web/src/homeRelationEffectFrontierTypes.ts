import type { HomeSourceUsabilityScopeId } from "./homeSourceUsabilityTypes";

export type HomeRelationEffectDependencyStatus =
  | "SCOPE_INVARIANT_RULE_DEMAND"
  | "MATCH_SCOPE_RULE_FIRST";

export type HomeRelationEffectRequiredRuleDimension =
  | "APPLICABILITY_CONTEXT"
  | "EFFECT_DIRECTION"
  | "COMPLETION_CONDITIONS"
  | "BLOCKING_CONDITIONS"
  | "COUNTER_EVIDENCE"
  | "PROFESSIONAL_PROVENANCE";

export interface HomeRelationEffectRuleDemand {
  demand_ref: string;
  carrier_ref: string;
  visible_slot: "year" | "month" | "day" | "hour";
  visible_stem: string;
  source_review_ref: string;
  source_evidence_ref: string;
  source_match_kind:
    | "EXACT_IDENTITY"
    | "SAME_ELEMENT_DIFFERENT_IDENTITY";
  intersection_ref: string;
  relation_fact_ref: string;
  relation_type: "six_clash_membership" | "six_harmony_membership";
  source_slot: "year" | "month" | "day" | "hour";
  source_branch: string;
  peer_slot: "year" | "month" | "day" | "hour";
  peer_branch: string;
  scope_presence: HomeSourceUsabilityScopeId[];
  dependency_status: HomeRelationEffectDependencyStatus;
  required_rule_dimensions: HomeRelationEffectRequiredRuleDimension[];
  effect_status: "UNRESOLVED";
  usability_status: "UNRESOLVED";
  selection_authority: false;
}

export interface HomeRelationEffectResearchFrontierEnvelope {
  frontier_ref: string;
  frontier_hash: string;
  frontier_version: "v60.mingli-relation-effect-research-frontier.001";
  case_ref: string;
  chart_version_ref: string;
  reading_ref: string;
  reading_hash: string;
  source_review_vector_ref: string;
  source_review_vector_hash: string;
  prerequisite_ref: string;
  prerequisite_hash: string;
  refusal_receipt_ref: string;
  refusal_receipt_hash: string;
  demands: HomeRelationEffectRuleDemand[];
  demand_count: number;
  scope_invariant_rule_demand_count: number;
  match_scope_rule_first_count: number;
  admitted_effect_rule_count: 0;
  research_semantics: "MEMBERSHIP_DEPENDENCY_AND_RULE_GAPS_ONLY";
  source_discussion_disposition: "ABSTAIN";
  effect_status: "UNRESOLVED";
  usability_status: "UNRESOLVED";
  provider_invoked: false;
  decision_created: false;
  gate_invoked: false;
  selection_authority: false;
  professional_verdict_allowed: false;
  probability_claim_allowed: false;
  canonical_write_allowed: false;
  read_only: true;
}
