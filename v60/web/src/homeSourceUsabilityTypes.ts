export type HomeSourceUsabilityScopeId =
  | "EXACT_IDENTITY_ONLY"
  | "ELEMENT_AFFINITY_INCLUDED";

export type HomeSourceUsabilityRequirementId =
  | "MATCH_SCOPE_RULE"
  | "RELATION_EFFECT_RULE"
  | "SEASONAL_CAPACITY_RULE"
  | "MULTI_SOURCE_AGGREGATION_RULE"
  | "ROOT_USABILITY_RULE"
  | "PROFESSIONAL_ADMISSION";

export interface HomeSourceUsabilityScope {
  scope_ref: string;
  scope_id: HomeSourceUsabilityScopeId;
  source_review_refs: string[];
  relation_review_refs: string[];
  intersection_refs: string[];
  source_review_count: number;
  clear_count: number;
  relation_review_count: number;
  intersection_count: number;
  relation_effect_status: "UNRESOLVED";
  root_usability_status: "UNRESOLVED";
  selection_authority: false;
}

export interface HomeSourceUsabilityRequirement {
  requirement_id: HomeSourceUsabilityRequirementId;
  status: "NOT_ADMITTED" | "NOT_TRIGGERED" | "UNRESOLVED";
  evidence_refs: string[];
  meaning: string;
  next_evidence: string;
}

export interface HomeSourceUsabilityCarrier {
  carrier_ref: string;
  visible_slot: "year" | "month" | "day" | "hour";
  visible_stem: string;
  scopes: HomeSourceUsabilityScope[];
  requirements: HomeSourceUsabilityRequirement[];
  discussion_ready: false;
}

export interface HomeSourceUsabilityPrerequisiteEnvelope {
  prerequisite_ref: string;
  prerequisite_hash: string;
  prerequisite_version: string;
  case_ref: string;
  chart_version_ref: string;
  quant_vector_ref: string;
  quant_vector_hash: string;
  source_review_vector_ref: string;
  source_review_vector_hash: string;
  carriers: HomeSourceUsabilityCarrier[];
  carrier_count: number;
  exact_identity_only_clear_count: number;
  exact_identity_only_review_required_count: number;
  element_affinity_included_clear_count: number;
  element_affinity_included_review_required_count: number;
  competing_carrier_count: number;
  ready_carrier_count: number;
  projection_semantics: "EVIDENCE_GAPS_AND_COMPETING_SCOPES_ONLY";
  professional_verdict_allowed: false;
  probability_claim_allowed: false;
  canonical_write_allowed: false;
  read_only: true;
}
