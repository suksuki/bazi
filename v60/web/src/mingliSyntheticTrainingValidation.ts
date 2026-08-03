import type { MingliSyntheticSuiteCandidateIdentity } from "./mingliSyntheticSuiteTypes";
import type {
  MingliSyntheticTrainingRequest,
  MingliSyntheticTrainingStatus,
} from "./mingliSyntheticTrainingTypes";

const HASH = /^[0-9a-f]{64}$/;
const REQUEST_STATUSES = ["QUEUED", "RUNNING", "SEALING", "SUCCEEDED", "FAILED"];
const PROGRESS_EVENTS = [
  "QUEUED",
  "START",
  "SEALED",
  "ERROR",
  "SEALING",
  "SUCCEEDED",
  "FAILED",
];
const REVIEW_DISPOSITIONS = [
  "MODEL_INDEPENDENT_DEV",
  "CANDIDATE_REVISION_REQUIRED",
  "EXPERIMENT_REVISION_REQUIRED",
  "EXECUTION_REPAIR_REQUIRED",
];

export function validateSyntheticTrainingStatus(
  value: unknown,
): MingliSyntheticTrainingStatus {
  if (!isRecord(value) || !Array.isArray(value.suites)) {
    throw new Error("mingli_synthetic_training_status_invalid");
  }
  const status = value as unknown as MingliSyntheticTrainingStatus;
  validateCandidate(status.candidate_identity);
  if (
    status.status_version !== "v60.mingli-synthetic-training-status.001"
    || status.server_run_request_allowed !== true
    || status.browser_direct_model_call_allowed !== false
    || !HASH.test(status.candidate_identity_hash)
    || status.qualification_effect !== "DEV_REVIEW_ONLY_NOT_MODEL_QUALIFICATION"
    || status.suites.length < 1
  ) {
    throw new Error("mingli_synthetic_training_status_shape_invalid");
  }
  status.suites.forEach((suite) => {
    const sealed = suite.candidate_state === "CURRENT_CANDIDATE_ALREADY_SEALED";
    if (
      !suite.suite_ref
      || !HASH.test(suite.suite_definition_hash)
      || !suite.title
      || !suite.question
      || suite.experiment_count < 1
      || !HASH.test(suite.execution_fingerprint)
      || !["READY_FOR_DEV_RUN", "CURRENT_CANDIDATE_ALREADY_SEALED"].includes(
        suite.candidate_state,
      )
      || sealed !== Boolean(suite.sealed_suite_run_ref && suite.sealed_suite_run_hash)
      || (suite.sealed_suite_run_hash !== null && !HASH.test(suite.sealed_suite_run_hash))
    ) {
      throw new Error("mingli_synthetic_training_suite_status_invalid");
    }
  });
  if (
    new Set(status.suites.map((suite) => suite.suite_ref)).size !== status.suites.length
    || (status.recommended_suite_ref !== null
      && !status.suites.some((suite) => suite.suite_ref === status.recommended_suite_ref))
  ) {
    throw new Error("mingli_synthetic_training_suite_binding_invalid");
  }
  if (status.latest_request !== null) validateSyntheticTrainingRequest(status.latest_request);
  return status;
}

export function validateSyntheticTrainingRequest(
  value: unknown,
): MingliSyntheticTrainingRequest {
  if (!isRecord(value) || !isRecord(value.candidate_identity)) {
    throw new Error("mingli_synthetic_training_request_invalid");
  }
  const request = value as unknown as MingliSyntheticTrainingRequest;
  validateCandidate(request.candidate_identity);
  const succeeded = request.status === "SUCCEEDED";
  const failed = request.status === "FAILED";
  if (
    request.request_version !== "v60.mingli-synthetic-suite-run-request.001"
    || !request.request_ref
    || !HASH.test(request.request_hash)
    || !request.suite_ref
    || !HASH.test(request.suite_definition_hash)
    || !HASH.test(request.candidate_identity_hash)
    || !HASH.test(request.execution_fingerprint)
    || !REQUEST_STATUSES.includes(request.status)
    || !PROGRESS_EVENTS.includes(request.progress_event)
    || !Number.isInteger(request.current_position)
    || !Number.isInteger(request.completed_count)
    || !Number.isInteger(request.total_count)
    || request.total_count < 1
    || request.current_position < 0
    || request.current_position > request.total_count
    || request.completed_count < 0
    || request.completed_count > request.total_count
    || succeeded !== Boolean(
      request.suite_run_ref && request.suite_run_hash && request.review_disposition,
    )
    || (request.review_disposition !== null
      && !REVIEW_DISPOSITIONS.includes(request.review_disposition))
    || (!succeeded && request.review_disposition !== null)
    || failed !== Boolean(request.error_code)
    || (request.suite_run_hash !== null && !HASH.test(request.suite_run_hash))
    || Number.isNaN(Date.parse(request.created_at))
    || Number.isNaN(Date.parse(request.updated_at))
    || !HASH.test(request.projection_hash)
  ) {
    throw new Error("mingli_synthetic_training_request_shape_invalid");
  }
  return request;
}

function validateCandidate(candidate: MingliSyntheticSuiteCandidateIdentity): void {
  if (
    !isRecord(candidate)
    || !candidate.agent_profile_ref
    || !HASH.test(candidate.agent_profile_hash)
    || !candidate.provider_id
    || !candidate.model_ref
    || !HASH.test(candidate.model_digest)
    || !candidate.provider_profile_ref
    || !HASH.test(candidate.provider_profile_hash)
    || !candidate.prompt_ref
    || !HASH.test(candidate.prompt_hash)
    || !candidate.agent_reading_version
  ) {
    throw new Error("mingli_synthetic_training_candidate_invalid");
  }
}

function isRecord(value: unknown): value is Record<string, any> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}
