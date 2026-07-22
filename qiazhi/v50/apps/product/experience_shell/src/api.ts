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

export type AuthMode = "login" | "register";

export interface ProductAccount {
  user_id: string;
  email: string;
  display_name: string;
  account_role: string;
  role: string;
}

export interface ProductProfile {
  profile_id: string;
  birth_input_id: string;
  display_name: string;
  gender: "male" | "female" | "unknown";
  calendar_type: "solar" | "lunar" | "unknown";
  birth_date: string;
  birth_time: string;
  birth_location: string;
  timezone: string;
  lunar_leap_month: boolean | null;
  true_solar_time_policy: string;
  input_quality: string;
  warnings: string[];
  pillars: string[];
  is_default: boolean;
}

export interface BirthProfileInput {
  birth_input_id: string;
  name: string;
  gender: ProductProfile["gender"];
  calendar_type: ProductProfile["calendar_type"];
  birth_date: string;
  birth_time: string;
  birth_location: string;
  timezone: string;
  true_solar_time_policy: string;
  lunar_leap_month: boolean | null;
  year_pillar: string;
  month_pillar: string;
  day_pillar: string;
  hour_pillar: string;
  input_quality: string;
  warnings: string[];
}

export function authenticate(input: {
  mode: AuthMode;
  email: string;
  password: string;
  displayName?: string;
  role?: string;
}): Promise<{ account: ProductAccount }> {
  const payload = input.mode === "register"
    ? {
        email: input.email,
        password: input.password,
        display_name: input.displayName || "DeepBazi 用户",
        role: input.role || "member",
      }
    : { email: input.email, password: input.password };
  return requestJson(`/api/v50/product/auth/${input.mode}`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function logout(): Promise<{ status: "logged_out" }> {
  return requestJson("/api/v50/product/auth/logout", { method: "POST", body: "{}" });
}

export async function loadProfiles(): Promise<ProductProfile[]> {
  const payload = await requestJson<{ profiles: ProductProfile[] }>("/api/v50/product/profiles");
  return payload.profiles;
}

export async function saveProfile(
  birthInput: BirthProfileInput,
  profileId = "",
): Promise<ProductProfile> {
  const payload = await requestJson<{ profile: ProductProfile }>(
    profileId
      ? `/api/v50/product/profiles/${encodeURIComponent(profileId)}`
      : "/api/v50/product/profiles",
    {
      method: profileId ? "PUT" : "POST",
      body: JSON.stringify({ birth_input: birthInput }),
    },
  );
  return payload.profile;
}

export function deleteProfile(profileId: string): Promise<{ status: "profile_deleted" }> {
  return requestJson(`/api/v50/product/profiles/${encodeURIComponent(profileId)}`, {
    method: "DELETE",
  });
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
