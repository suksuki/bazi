import type { CanvasContextPack, ReadOnlySixPillarCanvas } from "./contracts";


async function dreamRequest<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(String(payload.detail || `dream_request_failed_${response.status}`));
  }
  return response.json() as Promise<T>;
}

export interface DreamFeatureStatus {
  enabled: boolean;
  available: boolean;
  resumable: boolean;
  eligible_scene_count: number;
  reason_code: string;
  consent_state: "not_granted" | "active" | "withdrawn" | "source_changed" | "case_unavailable";
  human_scene_eligible: boolean;
  canonical_npc_scene_count: number;
  composition_ready: boolean;
  projection_version: string;
}

export interface DreamConsentStatus {
  case_id: string;
  state: DreamFeatureStatus["consent_state"];
  consent_version: "deepbazi.dream_pilot_consent.v1";
  can_grant: boolean;
  can_withdraw: boolean;
  revocable: true;
}

export type DreamSourceKind = "authorized_human" | "canonical_npc";
export type DreamSourceLabelKey = "dream.source.authorized_human" | "dream.source.canonical_npc";

export interface DreamVisitView {
  visit_id: string;
  state: string;
  selected_scene_ref: string;
  allowed_actions: string[];
  projection_version: string;
  updated_at: string;
}

export interface DreamTreeCard {
  scene_ref: string;
  art_variant: "mist" | "brook" | "ridge";
  primary_element: "wood" | "fire" | "earth" | "metal" | "water" | "unknown";
  climate_token: "quiet" | "luck_present" | "year_present";
  relation_tokens: string[];
  source_version: string;
  source_kind: DreamSourceKind;
  source_label_key: DreamSourceLabelKey;
}

export interface DreamEncounterProjection {
  projection_id: string;
  trees: DreamTreeCard[];
  content_hash: string;
}

export interface DreamTreeProjection {
  projection_id: string;
  source_refs: string[];
  source_kind: DreamSourceKind;
  source_label_key: DreamSourceLabelKey;
  visual_tokens: {
    art_variant: DreamTreeCard["art_variant"];
    primary_element: DreamTreeCard["primary_element"];
    climate: DreamTreeCard["climate_token"];
    relation_count: number;
    path_animation: "disabled";
  };
  relation_tokens: string[];
  work_path_state: "unavailable_unconfirmed" | "none_confirmed" | "available";
  work_path_message_key: "dream.path.none_confirmed";
  content_hash: string;
}

export interface DreamMirrorProjection {
  public_scene_ref: string;
  source_version: string;
  source_kind: DreamSourceKind;
  source_label_key: DreamSourceLabelKey;
  work_path_state: "unavailable_unconfirmed" | "none_confirmed" | "available";
  work_path_message_key: "dream.path.none_confirmed";
  canvas: ReadOnlySixPillarCanvas;
  content_hash: string;
}

export function loadDreamStatus(caseId = ""): Promise<DreamFeatureStatus> {
  const query = caseId ? `?case_id=${encodeURIComponent(caseId)}` : "";
  return dreamRequest(`/api/v50/dream/status${query}`);
}

export function grantDreamConsent(caseId: string): Promise<DreamConsentStatus> {
  return dreamRequest("/api/v50/dream/consent", {
    method: "POST",
    body: JSON.stringify({
      case_id: caseId,
      accepted: true,
      consent_version: "deepbazi.dream_pilot_consent.v1",
    }),
  });
}

export function withdrawDreamConsent(caseId: string): Promise<DreamConsentStatus> {
  return dreamRequest("/api/v50/dream/consent/withdraw", {
    method: "POST",
    body: JSON.stringify({ case_id: caseId, confirmed: true }),
  });
}

export function createDreamVisit(homeCaseId: string): Promise<DreamVisitView> {
  return dreamRequest("/api/v50/dream/visits", {
    method: "POST",
    body: JSON.stringify({ home_case_id: homeCaseId }),
  });
}

export function loadDreamVisit(visitId: string): Promise<DreamVisitView> {
  return dreamRequest(`/api/v50/dream/visits/${encodeURIComponent(visitId)}`);
}

export function enterDreamVisit(visitId: string): Promise<DreamVisitView> {
  return dreamRequest(`/api/v50/dream/visits/${encodeURIComponent(visitId)}/enter`, {
    method: "POST",
    body: "{}",
  });
}

export function loadDreamEncounter(visitId: string): Promise<DreamEncounterProjection> {
  return dreamRequest(`/api/v50/dream/visits/${encodeURIComponent(visitId)}/encounter`);
}

export function selectDreamTree(visitId: string, sceneRef: string): Promise<DreamVisitView> {
  return dreamRequest(`/api/v50/dream/visits/${encodeURIComponent(visitId)}/select-tree`, {
    method: "POST",
    body: JSON.stringify({ scene_ref: sceneRef }),
  });
}

export function loadDreamTree(visitId: string, sceneRef: string): Promise<DreamTreeProjection> {
  return dreamRequest(`/api/v50/dream/visits/${encodeURIComponent(visitId)}/trees/${encodeURIComponent(sceneRef)}`);
}

export function openDreamMirror(visitId: string): Promise<DreamVisitView> {
  return dreamRequest(`/api/v50/dream/visits/${encodeURIComponent(visitId)}/mirror/open`, {
    method: "POST",
    body: "{}",
  });
}

export function closeDreamMirror(visitId: string): Promise<DreamVisitView> {
  return dreamRequest(`/api/v50/dream/visits/${encodeURIComponent(visitId)}/mirror/close`, {
    method: "POST",
    body: "{}",
  });
}

export function loadDreamMirror(visitId: string, sceneRef: string): Promise<DreamMirrorProjection> {
  return dreamRequest(`/api/v50/dream/visits/${encodeURIComponent(visitId)}/trees/${encodeURIComponent(sceneRef)}/mirror`);
}

export async function loadDreamMirrorContext(
  visitId: string,
  sceneRef: string,
  stage: string,
  selected: string,
  layer: string,
): Promise<CanvasContextPack> {
  const params = new URLSearchParams({ stage, selected, layer });
  return dreamRequest(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/trees/${encodeURIComponent(sceneRef)}/mirror/context?${params.toString()}`,
  );
}
