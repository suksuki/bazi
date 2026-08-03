import { request } from "./http";
import type { MingliSyntheticSuiteCatalog } from "./mingliSyntheticSuiteTypes";
import { validateSyntheticSuiteCatalog } from "./mingliSyntheticSuiteValidation";

export async function loadSyntheticSuiteCatalog(
  suiteRunRef: string | null,
  signal?: AbortSignal,
): Promise<MingliSyntheticSuiteCatalog> {
  const path = suiteRunRef
    ? `/api/v60/mingli/lab/synthetic-suite-runs/${encodeURIComponent(suiteRunRef)}`
    : "/api/v60/mingli/lab/synthetic-suite-runs";
  const value = await request<unknown>(
    path,
    { signal },
  );
  return validateSyntheticSuiteCatalog(value);
}
