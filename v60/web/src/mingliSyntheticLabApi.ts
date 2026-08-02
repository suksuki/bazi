import { request } from "./http";
import type {
  MingliSyntheticExperimentCatalog,
  MingliSyntheticExperimentSnapshot,
  MingliSyntheticVariant,
} from "./mingliSyntheticLabTypes";
import {
  validateSyntheticExperimentCatalog,
  validateSyntheticExperimentSnapshot,
} from "./mingliSyntheticLabValidation";

export async function loadSyntheticExperimentCatalog(
  signal?: AbortSignal,
): Promise<MingliSyntheticExperimentCatalog> {
  const value = await request<unknown>(
    "/api/v60/mingli/lab/synthetic-experiments",
    { signal },
  );
  return validateSyntheticExperimentCatalog(value);
}

export async function loadSyntheticExperimentSnapshot(
  experimentRef: string,
  runRef: string,
  variant: MingliSyntheticVariant,
  signal?: AbortSignal,
): Promise<MingliSyntheticExperimentSnapshot> {
  const parameters = new URLSearchParams({ variant, run_ref: runRef });
  const path = `/api/v60/mingli/lab/synthetic-experiments/${encodeURIComponent(
    experimentRef,
  )}/snapshot?${parameters}`;
  const value = await request<unknown>(path, { signal });
  return validateSyntheticExperimentSnapshot(value, {
    experimentRef,
    runRef,
    variant,
  });
}
