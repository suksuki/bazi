export interface HomeReadingBrief {
  brief_ref: string;
  brief_hash: string;
  brief_version: string;
  headline: string;
  qualification: {
    status: "FORMAL_BOUNDED_READING";
    fact_count: number;
    candidate_count: number;
    timing_coordinate_count: number;
    decision_mode: "SYSTEM_FACTS_ONLY" | "RULE_ENGINE" | "LLM_REASONER";
    meaning: string;
  };
  confirmed: string[];
  focus: {
    candidate_ref: string | null;
    label: string;
    statement: string;
    rationale: string | null;
    evidence_refs: string[];
    meaning: string;
    support: {
      direct_fact_count: number;
      context_fact_count: number;
      visible_occurrence_count: number;
      hidden_occurrence_count: number;
      unresolved: string[];
    } | null;
  };
  timing: {
    analysis_date: string;
    coordinates: Array<{
      layer: string;
      pillar: string;
      ten_god_label: string;
    }>;
    meaning: string;
  };
  life_domains: Array<{
    domain: "career" | "wealth" | "relationship";
    label: string;
    statement: string;
    question: string;
    signal_status: string;
    evidence_count: number;
  }>;
  boundaries: string[];
  lineage: {
    reading_ref: string;
    reading_hash: string;
    quant_vector_ref: string;
    mechanism_vector_ref: string;
    timing_vector_ref: string;
    life_domain_vector_ref: string;
    decision_ref: string | null;
  };
  professional_verdict: false;
  probability_claim: false;
  canonical_write_allowed: false;
}
