import type {
  ExperienceWorkspaceBootstrapResponse,
  NarrationManifest,
  NarrationStatus,
  CanvasContextPack,
  CanvasLayer,
  CanvasStage,
  ReadOnlySixPillarCanvas,
  SpeechAsset,
} from "./contracts";

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(String(payload.detail || `request_failed_${response.status}`));
  }
  return response.json() as Promise<T>;
}

export function loadWorkspaceBootstrap(input: {
  caseId?: string;
  profileId?: string;
} = {}): Promise<ExperienceWorkspaceBootstrapResponse> {
  return requestJson("/api/v50/experience/workspace/bootstrap", {
    method: "POST",
    body: JSON.stringify({
      case_id: input.caseId || "",
      profile_id: input.profileId || "",
    }),
  });
}

export interface BaselineStartResponse {
  status: "baseline_cache_reused" | "baseline_preparing" | "baseline_reconciled" | "baseline_partial" | "baseline_unavailable";
  case_id: string;
  job_id: string;
  llm_calls_started: number;
  isolated_assertion_count?: number;
}

export function startMissingBaseline(caseId: string): Promise<BaselineStartResponse> {
  return requestJson(`/api/v50/experience/workspace/cases/${encodeURIComponent(caseId)}/baseline`, {
    method: "POST",
    body: "{}",
  });
}

export function loadCognitiveJob(jobId: string): Promise<{
  status: "queued" | "running" | "completed" | "failed";
  job_id: string;
  case_id: string;
}> {
  return requestJson(`/api/v50/experience/workspace/jobs/${encodeURIComponent(jobId)}`);
}

export function loadReadOnlyCanvas(caseId: string): Promise<ReadOnlySixPillarCanvas> {
  return requestJson(`/api/v50/experience/cases/${encodeURIComponent(caseId)}/canvas`);
}

export async function loadCanvasContext(
  caseId: string,
  stage: CanvasStage,
  selectedObjectRef: string,
  layer: CanvasLayer,
): Promise<CanvasContextPack> {
  const params = new URLSearchParams({ stage, selected: selectedObjectRef, layer });
  const payload = await requestJson<{ context: CanvasContextPack }>(
    `/api/v50/experience/cases/${encodeURIComponent(caseId)}/canvas/context?${params.toString()}`,
  );
  return payload.context;
}

export async function loadNarration(caseId: string): Promise<{
  manifest: NarrationManifest;
  speechAssets: Record<string, NarrationStatus>;
}> {
  const payload = await requestJson<{
    manifest: NarrationManifest;
    speech_assets: Record<string, NarrationStatus>;
  }>(`/api/v50/narration/cases/${encodeURIComponent(caseId)}/baseline`);
  return { manifest: payload.manifest, speechAssets: payload.speech_assets };
}

export async function prepareNarrationSegment(
  caseId: string,
  segmentId: string,
): Promise<SpeechAsset> {
  const payload = await requestJson<{ speech_asset: SpeechAsset }>(
    `/api/v50/narration/cases/${encodeURIComponent(caseId)}/baseline/segments/${encodeURIComponent(segmentId)}`,
    { method: "POST" },
  );
  return payload.speech_asset;
}
