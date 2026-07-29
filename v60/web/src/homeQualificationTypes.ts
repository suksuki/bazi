export type MechanismQualificationDimension =
  | "STRUCTURAL_ROLES"
  | "SOURCE_MANIFESTATION"
  | "TIMING_OVERLAP"
  | "COUNTER_EVIDENCE"
  | "EFFECT"
  | "CAPACITY"
  | "USABILITY"
  | "PROFESSIONAL_ADMISSION";

export type MechanismQualificationStatus =
  | "PRESENT"
  | "PARTIAL"
  | "MISSING"
  | "NOT_ADMITTED"
  | "UNRESOLVED";

export interface HomeMechanismQualificationCheck {
  dimension: MechanismQualificationDimension;
  label: string;
  status: MechanismQualificationStatus;
  evidence_refs: string[];
  meaning: string;
  next_evidence: string;
  falsifier: string;
}

export interface HomeCandidateMechanismQualification {
  candidate_ref: string;
  pattern_ref: string;
  pattern_label: string;
  checks: HomeMechanismQualificationCheck[];
  evidence_present_count: number;
  unresolved_or_unadmitted_count: number;
  readiness: "STRUCTURE_CANDIDATE_ONLY";
  professional_admission: false;
}

export interface HomeMechanismQualification {
  qualification_ref: string;
  qualification_hash: string;
  qualification_version: string;
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
  candidates: HomeCandidateMechanismQualification[];
  summary: string;
  professional_verdict_allowed: false;
  probability_claim_allowed: false;
  canonical_write_allowed: false;
  read_only: true;
}
