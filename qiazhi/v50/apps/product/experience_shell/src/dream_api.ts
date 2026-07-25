import type { CanvasContextPack, ReadOnlySixPillarCanvas } from "./contracts";


const DREAM_CLIENT_KEY = "deepbazi.dream.client.v1";
const DREAM_CONTROL_KEY = "deepbazi.dream.control.v1";
const DREAM_NAVIGATION_HANDOFF_KEY = "deepbazi.dream.navigation-handoff.v1";
let pageClientInstanceId = "";


export class DreamApiError extends Error {
  constructor(
    readonly code: string,
    readonly status: number,
  ) {
    super(code);
    this.name = "DreamApiError";
  }
}


function randomId(prefix: string): string {
  const value = globalThis.crypto?.randomUUID?.()
    || `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
  return `${prefix}-${value}`;
}


export function dreamClientInstanceId(): string {
  if (pageClientInstanceId) return pageClientInstanceId;
  const navigation = performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming | undefined;
  const handoffAt = Number(sessionStorage.getItem(DREAM_NAVIGATION_HANDOFF_KEY));
  const handoffIsCurrent = Number.isFinite(handoffAt) && Date.now() - handoffAt < 15000;
  const existing = sessionStorage.getItem(DREAM_CLIENT_KEY);
  sessionStorage.removeItem(DREAM_NAVIGATION_HANDOFF_KEY);
  if (existing && existing.length >= 8 && (navigation?.type === "reload" || handoffIsCurrent)) {
    pageClientInstanceId = existing;
    return existing;
  }
  const created = randomId("dream-client");
  sessionStorage.setItem(DREAM_CLIENT_KEY, created);
  pageClientInstanceId = created;
  return created;
}


export function markDreamNavigationHandoff(): void {
  sessionStorage.setItem(DREAM_NAVIGATION_HANDOFF_KEY, String(Date.now()));
}


interface StoredDreamControl {
  visitId: string;
  worldProjectionRef: string;
  lease: DreamControlLease;
}


function readStoredControl(visitId = ""): StoredDreamControl | null {
  try {
    const raw = sessionStorage.getItem(DREAM_CONTROL_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as StoredDreamControl;
    if (!parsed.lease?.lease_id || (visitId && parsed.visitId !== visitId)) return null;
    return parsed;
  } catch {
    sessionStorage.removeItem(DREAM_CONTROL_KEY);
    return null;
  }
}


function rememberDreamControl(visit: DreamVisitView): DreamVisitView {
  if (visit.control_lease) {
    sessionStorage.setItem(DREAM_CONTROL_KEY, JSON.stringify({
      visitId: visit.visit_id,
      worldProjectionRef: visit.world_projection_ref,
      lease: visit.control_lease,
    } satisfies StoredDreamControl));
  }
  return visit;
}


export function clearDreamControl(): void {
  sessionStorage.removeItem(DREAM_CONTROL_KEY);
}


export function currentDreamWorldProjectionRef(visitId: string): string {
  return readStoredControl(visitId)?.worldProjectionRef || "";
}


function dreamControlHeaders(visitId: string): Record<string, string> {
  const control = readStoredControl(visitId);
  if (!control) throw new DreamApiError("dream_control_lease_required", 409);
  return {
    "x-dream-client-instance": control.lease.client_instance_id,
    "x-dream-lease-id": control.lease.lease_id,
    "x-dream-lease-epoch": String(control.lease.lease_epoch),
    "x-dream-fence-token": String(control.lease.fence_token),
  };
}


export async function dreamRequest<T>(
  url: string,
  init?: RequestInit,
  visitId = "",
): Promise<T> {
  const response = await fetch(url, {
    credentials: "same-origin",
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(visitId ? dreamControlHeaders(visitId) : {}),
      ...(init?.headers || {}),
    },
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: response.statusText }));
    throw new DreamApiError(
      String(payload.detail || `dream_request_failed_${response.status}`),
      response.status,
    );
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

export interface DreamWorldPoint {
  x: number;
  y: number;
}

export interface DreamNavigationSample {
  world_projection_ref: string;
  world_space_ref: "dream-world:canonical-grove:v1";
  position: DreamWorldPoint;
  camera_heading: number;
  geometry_version: "dream-grove-geometry.v1";
}

export interface DreamControlLease {
  lease_id: string;
  client_instance_id: string;
  lease_epoch: number;
  fence_token: number;
  real_expires_at: string;
}

export interface DreamAnchorResolution {
  source: "departure_anchor" | "recovery_checkpoint" | "own_tree_safe_point" | "formal_grove_entrance";
  world_space_ref: "dream-world:canonical-grove:v1";
  position: DreamWorldPoint;
  camera_heading: number;
  geometry_version: "dream-grove-geometry.v1";
  source_ref: string;
  fallback_reason: string;
}

export interface CanonicalAbuProjection {
  canonical_abu_ref: "canonical-being:abu";
  identity_mode: "CANONICAL_UNIQUE_BEING";
  world_space_ref: "dream-world:canonical-grove:v1";
  public_position: DreamWorldPoint;
  public_action: "resting" | "walking" | "elsewhere";
  world_state_version: string;
  private_content_included: false;
}

export interface DreamVisitView {
  visit_id: string;
  state: string;
  selected_scene_ref: string;
  prepared_onecanvas_view_ref: string;
  active_onecanvas_view_ref: string;
  case_namespace: string;
  runtime_state: string;
  is_return_visit: boolean;
  control_lease: DreamControlLease | null;
  anchor_resolution: DreamAnchorResolution | null;
  world_projection_ref: string;
  canonical_abu: CanonicalAbuProjection | null;
  recovery_sequence: number;
  departure_commit_sequence: number;
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
  resident_label: string;
  autonomous_phase_ms: number;
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
  verification: DreamVerificationProjection;
  canvas: ReadOnlySixPillarCanvas;
  content_hash: string;
}

export type DreamRevealKind = "path" | "relation" | "node" | "none";
export type DreamVerificationLens =
  | "overview"
  | "five_element"
  | "combination_conflict"
  | "roots_reveal"
  | "timing"
  | "work_path";
export type DreamVerificationStage = "natal" | "luck" | "year";

export interface DreamRevealProjection {
  public_scene_ref: string;
  source_version: string;
  source_kind: DreamSourceKind;
  revealable_assertion_ref: string;
  reveal_kind: DreamRevealKind;
  visual_mode:
    | "path_sequence"
    | "relation_directional"
    | "relation_sync"
    | "local_node"
    | "natural_contact_only";
  authorized_statement: string;
  onecanvas_view_ref: string;
  target_stage: DreamVerificationStage;
  target_lens: DreamVerificationLens;
  content_hash: string;
}

export interface DreamVerificationProjection {
  state: "focused" | "quiet_overview";
  onecanvas_view_ref: string;
  revealable_assertion_ref: string;
  reveal_kind: DreamRevealKind;
  target_object_ref: string;
  verification_copy: "刚才树中显露的，是命盘里的这一处。";
  authorized_statement: string;
  binding: {
    dream_projection_version: string;
    source_version: string;
    assertion_version: string;
    life_case_version: string;
    coordinate_version: "canonical-six-pillar-twelve-node.v1";
    target_stage: DreamVerificationStage;
    target_lens: DreamVerificationLens;
  };
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

export async function createDreamVisit(
  homeCaseId: string,
  takeover = false,
): Promise<DreamVisitView> {
  const visit = await dreamRequest<DreamVisitView>("/api/v50/dream/visits", {
    method: "POST",
    body: JSON.stringify({
      home_case_id: homeCaseId,
      client_instance_id: dreamClientInstanceId(),
      takeover,
    }),
  });
  return rememberDreamControl(visit);
}

export async function loadDreamVisit(visitId: string): Promise<DreamVisitView> {
  const visit = await dreamRequest<DreamVisitView>(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}`,
    undefined,
    visitId,
  );
  return rememberDreamControl(visit);
}


export async function takeoverDreamVisit(visitId: string): Promise<DreamVisitView> {
  const visit = await dreamRequest<DreamVisitView>(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/control/takeover`,
    {
      method: "POST",
      body: JSON.stringify({ client_instance_id: dreamClientInstanceId() }),
    },
  );
  return rememberDreamControl(visit);
}

export async function enterDreamVisit(visitId: string): Promise<DreamVisitView> {
  const visit = await dreamRequest<DreamVisitView>(`/api/v50/dream/visits/${encodeURIComponent(visitId)}/enter`, {
    method: "POST",
    body: "{}",
  }, visitId);
  return rememberDreamControl(visit);
}

export function loadDreamEncounter(visitId: string): Promise<DreamEncounterProjection> {
  return dreamRequest(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/encounter`,
    undefined,
    visitId,
  );
}

export async function selectDreamTree(visitId: string, sceneRef: string): Promise<DreamVisitView> {
  const visit = await dreamRequest<DreamVisitView>(`/api/v50/dream/visits/${encodeURIComponent(visitId)}/select-tree`, {
    method: "POST",
    body: JSON.stringify({ scene_ref: sceneRef }),
  }, visitId);
  return rememberDreamControl(visit);
}

export function loadDreamTree(visitId: string, sceneRef: string): Promise<DreamTreeProjection> {
  return dreamRequest(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/trees/${encodeURIComponent(sceneRef)}`,
    undefined,
    visitId,
  );
}

export function prepareDreamReveal(
  visitId: string,
  sceneRef: string,
): Promise<DreamRevealProjection> {
  return dreamRequest(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/trees/${encodeURIComponent(sceneRef)}/reveal`,
    { method: "POST", body: "{}" },
    visitId,
  );
}

export async function openDreamMirror(
  visitId: string,
  onecanvasViewRef: string,
  navigation: DreamNavigationSample,
): Promise<DreamVisitView> {
  const visit = await dreamRequest<DreamVisitView>(`/api/v50/dream/visits/${encodeURIComponent(visitId)}/mirror/open`, {
    method: "POST",
    body: JSON.stringify({ onecanvas_view_ref: onecanvasViewRef, navigation }),
  }, visitId);
  return rememberDreamControl(visit);
}

export async function closeDreamMirror(visitId: string): Promise<DreamVisitView> {
  const visit = await dreamRequest<DreamVisitView>(`/api/v50/dream/visits/${encodeURIComponent(visitId)}/mirror/close`, {
    method: "POST",
    body: "{}",
  }, visitId);
  return rememberDreamControl(visit);
}

export function loadDreamMirror(
  visitId: string,
  sceneRef: string,
  onecanvasViewRef: string,
): Promise<DreamMirrorProjection> {
  const query = new URLSearchParams({ view_ref: onecanvasViewRef });
  return dreamRequest(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/trees/${encodeURIComponent(sceneRef)}/mirror?${query.toString()}`,
    undefined,
    visitId,
  );
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
    undefined,
    visitId,
  );
}


export async function heartbeatDreamControl(visitId: string): Promise<DreamVisitView> {
  const visit = await dreamRequest<DreamVisitView>(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/control/heartbeat`,
    { method: "POST", body: "{}" },
    visitId,
  );
  return rememberDreamControl(visit);
}


export async function checkpointDreamVisit(
  visitId: string,
  navigation: DreamNavigationSample,
  recoverySequence: number,
): Promise<DreamVisitView> {
  const result = await dreamRequest<{ visit: DreamVisitView }>(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/recovery/checkpoint`,
    {
      method: "POST",
      body: JSON.stringify({ navigation, recovery_sequence: recoverySequence }),
    },
    visitId,
  );
  return rememberDreamControl(result.visit);
}


export async function suspendDreamVisit(
  visitId: string,
  navigation: DreamNavigationSample,
  recoverySequence: number,
  keepalive = false,
): Promise<DreamVisitView> {
  const visit = await dreamRequest<DreamVisitView>(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/suspend`,
    {
      method: "POST",
      keepalive,
      body: JSON.stringify({ navigation, recovery_sequence: recoverySequence }),
    },
    visitId,
  );
  return rememberDreamControl(visit);
}


export async function recoverDreamVisit(visitId: string): Promise<DreamVisitView> {
  const visit = await dreamRequest<DreamVisitView>(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/recover`,
    { method: "POST", body: "{}" },
    visitId,
  );
  return rememberDreamControl(visit);
}


export async function setDreamDepartureIntent(
  visitId: string,
  active: boolean,
): Promise<DreamVisitView> {
  const visit = await dreamRequest<DreamVisitView>(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/departure/intent`,
    { method: "POST", body: JSON.stringify({ active }) },
    visitId,
  );
  return rememberDreamControl(visit);
}


export interface DreamDepartureResult {
  departure_commit_id: string;
  visit_id: string;
  case_namespace: string;
  commit_sequence: number;
  trigger: "SPATIAL_BOUNDARY" | "SEMANTIC_EXIT";
  waking_route: "/experience";
  idempotent_replay: boolean;
}


export async function commitDreamDeparture(
  visitId: string,
  trigger: DreamDepartureResult["trigger"],
  navigation: DreamNavigationSample,
  commitSequence: number,
  boundaryPosition?: DreamWorldPoint,
): Promise<DreamDepartureResult> {
  const result = await dreamRequest<DreamDepartureResult>(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/departure/commit`,
    {
      method: "POST",
      body: JSON.stringify({
        trigger,
        navigation,
        boundary_position: boundaryPosition || null,
        commit_sequence: commitSequence,
      }),
    },
    visitId,
  );
  clearDreamControl();
  return result;
}


export function loadDreamDepartureResult(
  visitId: string,
  commitSequence: number,
): Promise<DreamDepartureResult> {
  const params = new URLSearchParams({ commit_sequence: String(commitSequence) });
  return dreamRequest(
    `/api/v50/dream/visits/${encodeURIComponent(visitId)}/departure/result?${params.toString()}`,
  );
}


export function migrateGuestDreamAnchor(
  caseId: string,
  guestAnchorCapability: string,
  accepted: true,
): Promise<{ migrated: true }> {
  return dreamRequest("/api/v50/dream/anchors/migrate-guest", {
    method: "POST",
    body: JSON.stringify({
      case_id: caseId,
      guest_anchor_capability: guestAnchorCapability,
      accepted,
    }),
  });
}
