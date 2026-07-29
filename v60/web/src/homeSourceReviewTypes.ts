export interface HomeSourceRelationIntersection {
  intersection_ref: string;
  relation_fact_ref: string;
  relation_type: "six_clash_membership" | "six_harmony_membership";
  source_slot: "year" | "month" | "day" | "hour";
  source_branch: string;
  peer_slot: "year" | "month" | "day" | "hour";
  peer_branch: string;
  rule_ref: string;
  review_state:
    | "SIX_CLASH_COORDINATE_REVIEW_REQUIRED"
    | "SIX_HARMONY_COORDINATE_REVIEW_REQUIRED";
  effect_status: "UNRESOLVED";
}

export interface HomeSourceCoordinateReview {
  review_ref: string;
  source_evidence_ref: string;
  visible_slot: "year" | "month" | "day" | "hour";
  visible_stem: string;
  source_slot: "year" | "month" | "day" | "hour";
  source_branch: string;
  hidden_stem: string;
  source_match_kind:
    | "EXACT_IDENTITY"
    | "SAME_ELEMENT_DIFFERENT_IDENTITY";
  relation_intersections: HomeSourceRelationIntersection[];
  review_states: Array<
    | "NO_ADMITTED_RELATION_INTERSECTION"
    | "SIX_CLASH_COORDINATE_REVIEW_REQUIRED"
    | "SIX_HARMONY_COORDINATE_REVIEW_REQUIRED"
  >;
  evidence_refs: string[];
  relation_effect_status: "UNRESOLVED";
  root_usability_status: "UNRESOLVED";
}

export interface HomeSourceCoordinateReviewVector {
  vector_ref: string;
  vector_hash: string;
  vector_version: string;
  case_ref: string;
  chart_version_ref: string;
  quant_vector_ref: string;
  quant_vector_hash: string;
  source_review_profile_ref: string;
  source_review_profile_hash: string;
  reviews: HomeSourceCoordinateReview[];
  source_evidence_count: number;
  exact_identity_count: number;
  elemental_affinity_count: number;
  clear_coordinate_count: number;
  review_required_count: number;
  six_clash_intersection_count: number;
  six_harmony_intersection_count: number;
  review_semantics: "SOURCE_COORDINATE_RELATION_TRIAGE_ONLY";
  professional_verdict_allowed: false;
  probability_claim_allowed: false;
  canonical_write_allowed: false;
  unresolved_dimensions: string[];
  forbidden_conclusions: string[];
  read_only: true;
}
