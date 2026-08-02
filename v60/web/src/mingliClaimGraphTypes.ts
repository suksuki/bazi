export type MingliReadingClaimSemanticKey =
  | "WHOLE_CHART"
  | "DAY_MASTER"
  | "HYPOTHESIS_H1"
  | "HYPOTHESIS_H2"
  | "WORK_PATH"
  | "LIFE_IMAGE"
  | "DOMAIN_PERSONALITY"
  | "DOMAIN_CAREER"
  | "DOMAIN_WEALTH"
  | "DOMAIN_RELATIONSHIP"
  | "DOMAIN_FAMILY"
  | "TIMING_NATAL"
  | "TIMING_DAYUN"
  | "TIMING_ANNUAL"
  | "DISCRIMINATING_QUESTION";

export interface MingliReadingClaim {
  claim_ref: string;
  source_agent_reading_ref: string;
  semantic_key: MingliReadingClaimSemanticKey;
  layer: "PRINCIPLE" | "IMAGE" | "THEMES" | "TIMING" | "QUESTION";
  kind:
    | "WHOLE_CHART_THESIS"
    | "DAY_MASTER_STATE"
    | "COMPETING_HYPOTHESIS"
    | "WORK_PATH"
    | "LIFE_IMAGE"
    | "LIFE_DOMAIN"
    | "TIMING_BASELINE"
    | "TIMING_LAYER"
    | "DISCRIMINATING_QUESTION";
  role: "SYNTHESIS" | "PRIMARY" | "ALTERNATIVE" | "PROJECTION" | "QUESTION";
  status:
    | "ESTABLISHED"
    | "PROVISIONAL"
    | "NEEDS_RECONCILIATION"
    | "WITHHELD"
    | "OPEN_QUESTION";
  headline: string;
  statement: string;
  causal_chain: string[];
  condition: string | null;
  evidence_ids: string[];
  mechanism_evidence_ids: string[];
  coordinate_evidence_id: string | null;
  relation_evidence_ids: string[];
  confidence: "LOW" | "MEDIUM" | "HIGH" | null;
  codes: string[];
  assessment_codes: Array<
    | "CLAIM_EVIDENCE_MISSING"
    | "PRIMARY_HYPOTHESIS_CHART_BASIS_INCOMPLETE"
    | "MECHANISM_CANDIDATE_REQUIRES_ADJUDICATION"
    | "CONFIDENCE_EXCEEDS_PACKET"
    | "DEPENDENCY_WITHHELD"
    | "NATAL_CLAIM_CITES_TIMING_EVIDENCE"
    | "NATAL_CLAIM_USES_SELECTED_TIMING"
    | "TIMING_COORDINATE_EVIDENCE_MISSING"
    | "TIMING_NATAL_BASIS_MISSING"
    | "TIMING_RELATION_EVIDENCE_MISSING"
    | "RELATION_MEMBERSHIP_PROMOTED_TO_EFFECT"
    | "WORK_PATH_CLOSURE_EXCEEDS_PACKET"
    | "HIGH_RISK_EVENT_ASSERTION"
    | "ROOT_ASSERTION_CONFLICTS_WITH_PACKET"
    | "NAMED_COORDINATE_CONFLICTS_WITH_PACKET"
    | "TEN_GOD_MANIFESTATION_CONFLICTS_WITH_PACKET"
    | "PEER_COUNT_CONFLICTS_WITH_PACKET"
    | "UNSELECTED_TIMING_LAYER_ASSERTION"
    | "UNLISTED_RELATION_COORDINATE_ASSERTION"
    | "UNADMITTED_CLASSICAL_ASSERTION"
    | "MODEL_FIELD_INVALID"
    | "NON_READING_LANGUAGE"
    | "LOW_INFORMATION_LANGUAGE"
    | "TIMING_LAYER_PROSE_CONFLICT"
    | "UNSUPPORTED_SOCIAL_RESOURCE_INFERENCE"
    | "EXACT_ROLE_PATH_MISSING"
    | "DOMAIN_PRIMARY_PATH_MISSING"
    | "DOMAIN_METHOD_AXES_INCOMPLETE"
    | "DOMAIN_METHOD_POSITIVE_RULE_NOT_ADMITTED"
    | "TEN_GOD_TO_LIFE_STORY_SHORTCUT"
  >;
}

export interface MingliReadingClaimEdge {
  edge_ref: string;
  relation:
    | "SUPPORTS"
    | "COMPETES_WITH"
    | "PROJECTS_TO"
    | "TEMPORALLY_EXTENDS"
    | "DISCRIMINATES";
  source_claim_ref: string;
  target_claim_ref: string;
}

export interface MingliReadingClaimGraph {
  graph_ref: string;
  graph_hash: string;
  graph_version: "v60.mingli-reading-claim-graph.010";
  case_ref: string;
  chart_version_ref: string;
  life_case_revision_ref: string;
  reading_ref: string;
  reading_hash: string;
  agent_reading_ref: string;
  agent_reading_hash: string;
  packet_ref: string;
  packet_hash: string;
  agent_profile_ref: string;
  agent_profile_hash: string;
  model_ref: string;
  model_digest: string;
  reasoning_mode: "BLIND_READING";
  reasoning_mode_contract_ref: string;
  reasoning_mode_contract_hash: string;
  reconciliation_status: "NOT_ADMITTED";
  projection_authority: "DETERMINISTIC_AGENT_READING";
  qualification_status: "OWNER_REVIEW_REQUIRED";
  claims: MingliReadingClaim[];
  edges: MingliReadingClaimEdge[];
  owner_review_projection_allowed: true;
  public_projection_allowed: false;
  canonical_fact_write_allowed: false;
  read_only: true;
}
