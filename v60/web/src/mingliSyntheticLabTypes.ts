import type { MingliStageProjection } from "./mingliStageTypes";

export type MingliSyntheticVariant = "A" | "B";
export type MingliSyntheticOutcome =
  | "PASS"
  | "PRODUCT_SAFE_MODEL_FAIL"
  | "MODEL_FAIL"
  | "INVALID_EXPERIMENT";

export interface MingliSyntheticExperimentMember {
  variant: MingliSyntheticVariant;
  member_ref: string;
  subject_id: string;
}

export interface MingliSyntheticExperimentDefinition {
  catalog_version:
    | "v60.mingli-synthetic-experiment-catalog.001"
    | "v60.mingli-synthetic-experiment-catalog.002";
  experiment_ref: string;
  definition_hash: string;
  suite: "DEV";
  family:
    | "CONTROLLED_LEGAL_HOUR_PAIR"
    | "CONTROLLED_ROOT_IDENTITY_PAIR"
    | "CONTROLLED_HIDDEN_RANK_PRIMARY_SECONDARY_PAIR"
    | "CONTROLLED_HIDDEN_RANK_SECONDARY_TERTIARY_PAIR"
    | "CONTROLLED_HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION_PAIR"
    | "CONTROLLED_REGIME_WORK_PATH_GENERALIZATION_PAIR"
    | "CONTROLLED_DECISION_DISCIPLINE_GENERALIZATION_PAIR";
  title: string;
  question: string;
  analysis_date: string;
  blind_protocol: "MEMBERS_INDEPENDENT_GOLD_NOT_IN_AGENT_PACKET";
  inference_scope:
    | "WHOLE_HOUR_PILLAR_RESPONSE_NOT_ROOT_CAUSAL_ESTIMATE"
    | "NATAL_ROOT_GATE_ONLY_WITH_FULL_HOUR_COLLATERAL"
    | "NATAL_HIDDEN_RANK_GATE_ONLY_WITH_FULL_HOUR_COLLATERAL"
    | "NATAL_HIDDEN_RANK_CROSS_DAY_MASTER_GENERALIZATION"
    | "WHOLE_CHART_DECISION_DISCIPLINE_WITH_FULL_HOUR_COLLATERAL";
  inference_limit: string;
  known_collateral_deltas: string[];
  changed_input: {
    field: "birth_time";
    A: string;
    B: string;
  };
  full_pillar_delta: {
    A: string[];
    B: string[];
    changed_slots: ["hour"];
    legal_hour_pillar_change: string;
  };
  members: MingliSyntheticExperimentMember[];
}

export interface MingliSyntheticExperimentCatalogEntry
  extends MingliSyntheticExperimentDefinition {
  run_status: "SEALED" | "NOT_RUN";
  latest_run_ref: string | null;
  latest_outcome: MingliSyntheticOutcome | null;
  runs: MingliSyntheticExperimentRunSummary[];
}

export interface MingliSyntheticExperimentRunSummary {
  run_ref: string;
  experiment_ref: string;
  created_at: string;
  outcome: MingliSyntheticOutcome;
  model_independence: "PASS" | "FAIL" | "NOT_EVALUABLE";
  evaluator_version: MingliSyntheticExperimentEvaluation["evaluator_version"];
  dev_gold_version: MingliSyntheticExperimentEvaluation["dev_gold_version"];
  review_contract_status: "CURRENT" | "SUPERSEDED";
  changed_pass_count: number;
  hold_pass_count: number;
}

export interface MingliSyntheticExperimentCatalog {
  catalog_version: "v60.mingli-synthetic-experiment-catalog.006";
  experiments: MingliSyntheticExperimentCatalogEntry[];
  browser_generation_allowed: false;
  read_only: true;
}

export interface MingliSyntheticExperimentCheck {
  check_ref: string;
  group: "EXPERIMENT_VALIDITY" | "MUST_HOLD" | "EXPECTED_CHANGE";
  status: "PASS" | "FAIL";
  statement: string;
  A: unknown;
  B: unknown;
}

export interface MingliSyntheticExperimentEvaluation {
  evaluator_version:
    | "v60.mingli-synthetic-experiment-evaluator.001"
    | "v60.mingli-synthetic-experiment-evaluator.002"
    | "v60.mingli-synthetic-experiment-evaluator.003"
    | "v60.mingli-synthetic-experiment-evaluator.004"
    | "v60.mingli-synthetic-experiment-evaluator.005"
    | "v60.mingli-synthetic-experiment-evaluator.006"
    | "v60.mingli-synthetic-experiment-evaluator.007"
    | "v60.mingli-synthetic-experiment-evaluator.008";
  dev_gold_version:
    | "v60.mingli-synthetic-experiment-dev-gold.001"
    | "v60.mingli-synthetic-experiment-dev-gold.002"
    | "v60.mingli-synthetic-experiment-dev-gold.003"
    | "v60.mingli-synthetic-experiment-dev-gold.004"
    | "v60.mingli-synthetic-experiment-dev-gold.005";
  dev_gold_hash: string;
  outcome: MingliSyntheticOutcome;
  checks: MingliSyntheticExperimentCheck[];
  server_issue_keys: { A: string[]; B: string[] };
  changed_pass_count: number;
  hold_pass_count: number;
  drift_checks: string[];
  qualification_effect: "DEV_EVIDENCE_ONLY_NOT_METHOD_QUALIFICATION";
  summary: string;
}

export interface MingliSyntheticTrainingAssessment {
  assessment_version: "v60.mingli-synthetic-training-assessment.001";
  experiment_validity: "VALID" | "INVALID";
  model_independence: "PASS" | "FAIL" | "NOT_EVALUABLE";
  product_result:
    | "SAFE_MODEL_DIRECT"
    | "SAFE_WITH_REPAIR"
    | "WITHHELD"
    | "NOT_EVALUABLE";
  trace_coverage: "FIELD_LEVEL" | "PARTIAL" | "LEGACY_SUMMARY_ONLY";
  server_issue_keys: { A: string[]; B: string[] };
  summary: string;
  qualification_effect: "DEV_REVIEW_ONLY_NOT_MODEL_QUALIFICATION";
}

export interface MingliSyntheticNormalizationDelta {
  stage:
    | "EVIDENCE_ID_NORMALIZATION"
    | "PACKET_FACT_BINDING"
    | "PROFESSIONAL_ADJUDICATION"
    | "PROSE_EVIDENCE_REPAIR"
    | "OUTPUT_FORM_REPAIR"
    | "LOCAL_FIELD_REPAIR";
  path: string;
  before_present: boolean;
  after_present: boolean;
  before: unknown;
  after: unknown;
}

export interface MingliSyntheticModelTrace {
  trace_version: "v60.mingli-synthetic-model-trace.001";
  availability: "FIELD_LEVEL" | "LEGACY_NOT_CAPTURED";
  selected_agent_reading_ref: string;
  receipt_ref: string | null;
  receipt_hash: string | null;
  raw_output_hash: string | null;
  normalized_output_hash: string;
  change_count: number | null;
  stage_counts: Array<{
    stage: MingliSyntheticNormalizationDelta["stage"];
    change_count: number;
  }>;
  key_deltas: MingliSyntheticNormalizationDelta[];
  server_issue_keys: string[];
  limitation: string;
}

export interface MingliSyntheticExperimentSnapshot {
  snapshot_version: "v60.mingli-synthetic-experiment-snapshot.004";
  snapshot_ref: string;
  snapshot_hash: string;
  experiment_ref: string;
  run_ref: string;
  run_hash: string;
  selected_variant: MingliSyntheticVariant;
  member_ref: string;
  sealed_agent_reading_ref: string;
  stage: MingliStageProjection;
  evaluation: MingliSyntheticExperimentEvaluation;
  training_assessment: MingliSyntheticTrainingAssessment;
  model_trace: MingliSyntheticModelTrace;
  definition: MingliSyntheticExperimentDefinition;
  browser_generation_allowed: false;
  read_only: true;
}
