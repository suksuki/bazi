export interface HomeEvidenceCitation {
  evidence_ref: string;
  evidence_kind:
    | "DETERMINISTIC_FACT"
    | "SOURCE_MANIFESTATION"
    | "TIMING_COORDINATE"
    | "TIMING_RELATION"
    | "TIMING_CANDIDATE_OVERLAP"
    | "MECHANISM_CANDIDATE"
    | "VERSIONED_VECTOR";
  summary: string;
  epistemic_status:
    | "CONFIRMED"
    | "MEMBERSHIP_ONLY"
    | "CANDIDATE_ONLY"
    | "COORDINATE_ONLY";
  source_refs: string[];
}

export interface HomeExplanationClaim {
  claim_ref: string;
  claim_kind:
    | "CONFIRMED_FOUNDATION"
    | "MECHANISM_CANDIDATE"
    | "LIFE_DOMAIN_WINDOW";
  title: string;
  statement: string;
  epistemic_status: "CONFIRMED" | "CANDIDATE" | "OBSERVE";
  decision_basis:
    | "SYSTEM_DETERMINISTIC"
    | "VERSIONED_RULE_CANDIDATE"
    | "BOUNDED_ATTENTION_COMPARISON"
    | "ATTENTION_WINDOW_POLICY";
  support_evidence: HomeEvidenceCitation[];
  counter_evidence: HomeEvidenceCitation[];
  counter_evidence_status: "AVAILABLE" | "NOT_ADMITTED";
  unresolved_questions: string[];
  competing_claim_refs: string[];
  source_profile_refs: string[];
  boundary: string;
}

export interface HomeMingliExplanation {
  explanation_ref: string;
  explanation_hash: string;
  explanation_version: string;
  reading_ref: string;
  reading_hash: string;
  claims: HomeExplanationClaim[];
  confirmed_count: number;
  candidate_count: number;
  observation_count: number;
  decision_authority: "SYSTEM_FACTS_ONLY" | "RULE_ENGINE" | "LLM_REASONER";
  decision_meaning: string;
  professional_verdict: false;
  probability_claim: false;
  canonical_write_allowed: false;
  read_only: true;
}

export interface HomeAbuExpression {
  expression_ref: string;
  expression_hash: string;
  reading_ref: string;
  reading_hash: string;
  explanation_ref: string | null;
  explanation_hash: string | null;
  authority: "EXPRESSION_ONLY";
  summary: string;
  known: string;
  boundary: string;
  next_attention: string;
  fact_refs: string[];
  candidate_refs: string[];
  confirmed_claim_count: number;
  candidate_claim_count: number;
  observation_claim_count: number;
  fact_creation: false;
  decision_creation: false;
}
