import type {
  DreamCommand,
  DreamEntry,
  DreamSnapshot,
} from "./api";
import { request } from "./http";

export function ensureEncounter(): Promise<DreamSnapshot> {
  return request("/api/v60/dream/encounter", { method: "POST" });
}

export function loadDreamEntry(): Promise<DreamEntry> {
  return request("/api/v60/dream/entry");
}

export function selectDreamTree(candidateRef: string): Promise<DreamSnapshot> {
  return request(`/api/v60/dream/grove/${encodeURIComponent(candidateRef)}`, {
    method: "POST",
  });
}

export function loadEncounter(): Promise<DreamSnapshot> {
  return request("/api/v60/dream/encounter");
}

export function executeDreamCommand(
  snapshot: DreamSnapshot,
  command: DreamCommand,
  payload: { targetRef?: string; choiceId?: string } = {},
): Promise<DreamSnapshot> {
  const identity = payload.targetRef ?? payload.choiceId ?? "none";
  const idempotencyKey = [
    "v60-dream-command",
    snapshot.encounter.encounter_ref,
    snapshot.encounter.version,
    command,
    identity,
  ].join(":");
  return request("/api/v60/dream/command", {
    method: "POST",
    body: JSON.stringify({
      command,
      encounter_ref: snapshot.encounter.encounter_ref,
      expected_version: snapshot.encounter.version,
      idempotency_key: idempotencyKey,
      ...(payload.targetRef ? { target_ref: payload.targetRef } : {}),
      ...(payload.choiceId ? { choice_id: payload.choiceId } : {}),
    }),
  });
}

export function returnToDreamGrove(
  snapshot: DreamSnapshot,
): Promise<DreamEntry> {
  const command: DreamCommand = "RETURN_TO_GROVE";
  return request("/api/v60/dream/command", {
    method: "POST",
    body: JSON.stringify({
      command,
      encounter_ref: snapshot.encounter.encounter_ref,
      expected_version: snapshot.encounter.version,
      idempotency_key: [
        "v60-dream-command",
        snapshot.encounter.encounter_ref,
        snapshot.encounter.version,
        command,
        "none",
      ].join(":"),
    }),
  });
}
