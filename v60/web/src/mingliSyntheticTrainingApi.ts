import { request } from "./http";
import type {
  MingliSyntheticTrainingRequest,
  MingliSyntheticTrainingStatus,
  MingliSyntheticTrainingSuiteStatus,
} from "./mingliSyntheticTrainingTypes";
import {
  validateSyntheticTrainingRequest,
  validateSyntheticTrainingStatus,
} from "./mingliSyntheticTrainingValidation";

export async function loadSyntheticTrainingStatus(
  signal?: AbortSignal,
): Promise<MingliSyntheticTrainingStatus> {
  const value = await request<unknown>(
    "/api/v60/mingli/lab/synthetic-training",
    { signal },
  );
  return validateSyntheticTrainingStatus(value);
}

export async function createSyntheticTrainingRequest(
  suite: MingliSyntheticTrainingSuiteStatus,
  idempotencyKey: string,
): Promise<MingliSyntheticTrainingRequest> {
  const value = await request<unknown>(
    "/api/v60/mingli/lab/synthetic-suite-run-requests",
    {
      method: "POST",
      body: JSON.stringify({
        request_version: "v60.mingli-synthetic-suite-run-request.001",
        suite_ref: suite.suite_ref,
        expected_suite_definition_hash: suite.suite_definition_hash,
        expected_execution_fingerprint: suite.execution_fingerprint,
        idempotency_key: idempotencyKey,
      }),
    },
  );
  return validateSyntheticTrainingRequest(value);
}

export async function loadSyntheticTrainingRequest(
  requestRef: string,
  signal?: AbortSignal,
): Promise<MingliSyntheticTrainingRequest> {
  const value = await request<unknown>(
    `/api/v60/mingli/lab/synthetic-suite-run-requests/${encodeURIComponent(requestRef)}`,
    { signal },
  );
  return validateSyntheticTrainingRequest(value);
}
