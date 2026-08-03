import type { MingliSyntheticSuiteCandidateIdentity } from "./mingliSyntheticSuiteTypes";

export type MingliSyntheticTrainingCandidateState =
  | "READY_FOR_DEV_RUN"
  | "CURRENT_CANDIDATE_ALREADY_SEALED";

export interface MingliSyntheticTrainingSuiteStatus {
  suite_ref: string;
  suite_definition_hash: string;
  title: string;
  question: string;
  experiment_count: number;
  execution_fingerprint: string;
  candidate_state: MingliSyntheticTrainingCandidateState;
  sealed_suite_run_ref: string | null;
  sealed_suite_run_hash: string | null;
}

export type MingliSyntheticTrainingRequestStatus =
  | "QUEUED"
  | "RUNNING"
  | "SEALING"
  | "SUCCEEDED"
  | "FAILED";

export type MingliSyntheticTrainingProgressEvent =
  | "QUEUED"
  | "START"
  | "SEALED"
  | "ERROR"
  | "SEALING"
  | "SUCCEEDED"
  | "FAILED";

export type MingliSyntheticTrainingReviewDisposition =
  | "MODEL_INDEPENDENT_DEV"
  | "CANDIDATE_REVISION_REQUIRED"
  | "EXPERIMENT_REVISION_REQUIRED"
  | "EXECUTION_REPAIR_REQUIRED";

export interface MingliSyntheticTrainingRequest {
  request_version: "v60.mingli-synthetic-suite-run-request.001";
  request_ref: string;
  request_hash: string;
  suite_ref: string;
  suite_definition_hash: string;
  candidate_identity: MingliSyntheticSuiteCandidateIdentity;
  candidate_identity_hash: string;
  execution_fingerprint: string;
  status: MingliSyntheticTrainingRequestStatus;
  progress_event: MingliSyntheticTrainingProgressEvent;
  current_position: number;
  completed_count: number;
  total_count: number;
  current_experiment_ref: string | null;
  suite_run_ref: string | null;
  suite_run_hash: string | null;
  review_disposition: MingliSyntheticTrainingReviewDisposition | null;
  error_code: string | null;
  created_at: string;
  updated_at: string;
  projection_hash: string;
}

export interface MingliSyntheticTrainingStatus {
  status_version: "v60.mingli-synthetic-training-status.001";
  server_run_request_allowed: true;
  browser_direct_model_call_allowed: false;
  candidate_identity: MingliSyntheticSuiteCandidateIdentity;
  candidate_identity_hash: string;
  suites: MingliSyntheticTrainingSuiteStatus[];
  recommended_suite_ref: string | null;
  latest_request: MingliSyntheticTrainingRequest | null;
  qualification_effect: "DEV_REVIEW_ONLY_NOT_MODEL_QUALIFICATION";
}
