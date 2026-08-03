import type {
  MingliSyntheticExperimentEvaluation,
  MingliSyntheticOutcome,
} from "./mingliSyntheticLabTypes";

export type MingliSyntheticSuiteMode = "DEV" | "QUALIFICATION" | "HOLDOUT";

export interface MingliSyntheticSuiteModeEntry {
  mode: MingliSyntheticSuiteMode;
  availability: "ACTIVE" | "LOCKED_OWNER_GATE";
  description: string;
}

export interface MingliSyntheticSuiteCandidateIdentity {
  agent_profile_ref: string;
  agent_profile_hash: string;
  provider_id: string;
  model_ref: string;
  model_digest: string;
  provider_profile_ref: string;
  provider_profile_hash: string;
  prompt_ref: string;
  prompt_hash: string;
  agent_reading_version?: string;
}

export interface MingliSyntheticSuiteVariantReview {
  variant: "A" | "B";
  reason_keys: string[];
}

export interface MingliSyntheticSuiteRunItem {
  position: number;
  experiment_ref: string;
  definition_hash: string;
  execution_status: "SEALED" | "ERROR";
  experiment_run_ref: string | null;
  experiment_run_hash: string | null;
  outcome: MingliSyntheticOutcome | null;
  evaluator_version: MingliSyntheticExperimentEvaluation["evaluator_version"] | null;
  dev_gold_version: MingliSyntheticExperimentEvaluation["dev_gold_version"] | null;
  dev_gold_hash: string | null;
  model_independence: "PASS" | "FAIL" | "NOT_EVALUABLE" | null;
  changed_pass_count: number | null;
  hold_pass_count: number | null;
  review_contract_status: "CURRENT" | "SUPERSEDED" | null;
  review_required: boolean;
  review_reason_keys: string[];
  variant_reviews: MingliSyntheticSuiteVariantReview[];
  error_code: string | null;
}

export interface MingliSyntheticSuiteErrorCluster {
  kind:
    | "SERVER_REPAIR"
    | "EXPECTED_CHECK_FAIL"
    | "EXPERIMENT_INVALID"
    | "CONTRACT_SUPERSEDED"
    | "RUNNER_ERROR";
  key: string;
  label: string;
  occurrence_count: number;
  experiment_count: number;
  experiment_refs: string[];
  member_occurrences: string[];
}

export interface MingliSyntheticSuiteCounts {
  experiments: number;
  sealed: number;
  runner_errors: number;
  review_required: number;
}

export interface MingliSyntheticSuiteCurrentReviewProjection {
  projection_version: "v60.mingli-synthetic-suite-review-projection.001";
  projection_hash: string;
  source_suite_run_ref: string;
  source_suite_run_hash: string;
  items: MingliSyntheticSuiteRunItem[];
  counts: MingliSyntheticSuiteCounts;
  error_clusters: MingliSyntheticSuiteErrorCluster[];
}

export interface MingliSyntheticSuiteRun {
  suite_run_ref: string;
  suite_run_hash: string;
  created_at: string;
  suite_run_version:
    | "v60.mingli-synthetic-suite-run.001"
    | "v60.mingli-synthetic-suite-run.002";
  suite_ref: string;
  suite_definition_hash: string;
  suite_mode: "DEV";
  runner_version:
    | "v60.mingli-synthetic-suite-runner.001"
    | "v60.mingli-synthetic-suite-runner.002";
  candidate_identity: MingliSyntheticSuiteCandidateIdentity | null;
  status: "COMPLETED" | "COMPLETED_WITH_ERRORS";
  items: MingliSyntheticSuiteRunItem[];
  counts: MingliSyntheticSuiteCounts;
  outcomes: Record<MingliSyntheticOutcome, number>;
  error_clusters: MingliSyntheticSuiteErrorCluster[];
  qualification_effect: "DEV_REVIEW_ONLY_NOT_MODEL_QUALIFICATION";
  current_review_projection: MingliSyntheticSuiteCurrentReviewProjection;
}

export interface MingliSyntheticSuiteCatalogEntry {
  suite_definition_version: "v60.mingli-synthetic-suite-definition.001";
  suite_ref: string;
  suite_definition_hash: string;
  mode: "DEV";
  availability: "ACTIVE";
  title: string;
  question: string;
  experiment_refs: string[];
  experiment_definition_hashes: Array<{
    experiment_ref: string;
    definition_hash: string;
  }>;
  execution_policy: "SEQUENTIAL_CONTINUE_ON_BOUNDED_ERROR_THEN_SEAL";
  inference_limit: string;
  run_status: "SEALED" | "NOT_RUN";
  latest_suite_run_ref: string | null;
  runs: MingliSyntheticSuiteRun[];
}

export interface MingliSyntheticSuiteCatalog {
  catalog_version: "v60.mingli-synthetic-suite-catalog.001";
  modes: MingliSyntheticSuiteModeEntry[];
  suites: MingliSyntheticSuiteCatalogEntry[];
  browser_generation_allowed: false;
  read_only: true;
}

export interface MingliSyntheticSuiteRunSelection {
  suite: MingliSyntheticSuiteCatalogEntry;
  run: MingliSyntheticSuiteRun;
  review: MingliSyntheticSuiteCurrentReviewProjection;
}
