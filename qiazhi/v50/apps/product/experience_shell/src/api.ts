import type {
  CaseWorkspaceEnvelope,
  ExperienceCaseSummary,
  MingliExperienceEnvelope,
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

export async function loadAccount(): Promise<{ display_name: string; role: string }> {
  const payload = await requestJson<{ account: { display_name: string; role: string } }>(
    "/api/v50/product/auth/me",
  );
  return payload.account;
}

export async function loadCases(): Promise<ExperienceCaseSummary[]> {
  const payload = await requestJson<{ cases: ExperienceCaseSummary[] }>(
    "/api/v50/experience/cases",
  );
  return payload.cases;
}

export function loadEnvelope(caseId: string): Promise<MingliExperienceEnvelope> {
  return requestJson(`/api/v50/experience/cases/${encodeURIComponent(caseId)}/baseline`);
}

export function loadCaseWorkspace(caseId: string): Promise<CaseWorkspaceEnvelope> {
  return requestJson(`/api/v50/scenes/cases/${encodeURIComponent(caseId)}/workspace`);
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
