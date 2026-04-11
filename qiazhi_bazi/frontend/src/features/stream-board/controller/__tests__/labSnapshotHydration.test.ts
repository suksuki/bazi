import { describe, expect, it, vi } from "vitest";
import type { LabSnapshotHydrationPatch, LabSnapshotHydrationSinks } from "../labSnapshotHydration";
import { applyLabSnapshotHydrationPatch, buildLabSnapshotHydrationPatch } from "../labSnapshotHydration";
import type { LabSnapshot } from "@/features/stream-board/stores/LabSessionContext";
import type { SeedPayload } from "@/features/stream-board/models";

const minimalSeed: SeedPayload = {
  date: "1990-01-01",
  time: "12:00",
  calendar: "solar",
  gender: "male",
};

function minimalSnapshot(overrides: Partial<LabSnapshot> = {}): LabSnapshot {
  return {
    active_session_id: "42",
    metadata: {
      version: "1",
      pillars: {
        year: { stem: "甲", branch: "子" },
        month: { stem: "乙", branch: "丑" },
        day: { stem: "丙", branch: "寅" },
        hour: { stem: "丁", branch: "卯" },
      },
      conflict_matrix: { points: [] },
      flow_state: "ready",
      notes: "",
    },
    timeline: { dayun: "x", liunian: "y", reference_year: 2026 },
    llm_prompt: "hello",
    ...overrides,
  };
}

function createMockSinks(): LabSnapshotHydrationSinks {
  return {
    setMetadata: vi.fn(),
    setTimeline: vi.fn(),
    setFirstPromptText: vi.fn(),
    setConsultationId: vi.fn(),
    setHealth: vi.fn(),
    setAuditItems: vi.fn(),
    setResultLogs: vi.fn(),
    setLlmDiagnosticData: vi.fn(),
    setDeityScores: vi.fn(),
    setDeityEnergyAxes: vi.fn(),
    setDeityComponents: vi.fn(),
    setDeityTraceDetails: vi.fn(),
    setPhysicsAudit: vi.fn(),
    setPhysicsConfidence: vi.fn(),
    setPhysicsEvidence: vi.fn(),
    setPhysicsParams: vi.fn(),
    setGlobalEntropy: vi.fn(),
    setFinalVerdictBody: vi.fn(),
    setFinalVerdictChangeLog: vi.fn(),
    setFinalVerdictVersionId: vi.fn(),
    setFinalLogicalEvidence: vi.fn(),
    setFinalWorkVector: vi.fn(),
    setFinalTopologyGraphV1: vi.fn(),
    setFinalStructureCandidatesV0: vi.fn(),
    setFinalStructureFinalDecisionV0: vi.fn(),
    setResolvedCardIds: vi.fn(),
    setConfirmedDecisionIds: vi.fn(),
    setLogicDiff: vi.fn(),
    setLastSeedPayload: vi.fn(),
  };
}

describe("buildLabSnapshotHydrationPatch", () => {
  it("returns null when snapshot is missing or has no metadata", () => {
    expect(buildLabSnapshotHydrationPatch(null, null)).toBeNull();
    expect(buildLabSnapshotHydrationPatch({ timeline: {} }, null)).toBeNull();
  });

  it("maps core fields and consultation id from active_session_id", () => {
    const patch = buildLabSnapshotHydrationPatch(minimalSnapshot(), minimalSeed);
    expect(patch).not.toBeNull();
    expect(patch!.metadata.version).toBe("1");
    expect(patch!.metadata.pillars?.year?.stem).toBe("甲");
    expect(patch!.consultationId).toBe(42);
    expect(patch!.firstPromptText).toBe("hello");
    expect(patch!.lastSeedPayload).toEqual(minimalSeed);
  });

  it("prefers interaction_hub.consultation_id when numeric", () => {
    const patch = buildLabSnapshotHydrationPatch(
      minimalSnapshot({
        interaction_hub: { consultation_id: 7 },
      }),
      null,
    );
    expect(patch!.consultationId).toBe(7);
  });

  it("normalizes decision_selection_ids onto patch", () => {
    const patch = buildLabSnapshotHydrationPatch(
      minimalSnapshot({ decision_selection_ids: [" a ", "b", "a"] }),
      null,
    );
    expect(patch!.confirmedDecisionIds).toEqual(["a", "b"]);
  });
});

describe("applyLabSnapshotHydrationPatch", () => {
  it("writes through sinks", () => {
    const sinks = createMockSinks();
    const patch: LabSnapshotHydrationPatch = buildLabSnapshotHydrationPatch(minimalSnapshot(), minimalSeed)!;
    applyLabSnapshotHydrationPatch(patch, sinks);

    expect(sinks.setMetadata).toHaveBeenCalledWith(patch.metadata);
    expect(sinks.setTimeline).toHaveBeenCalledWith(patch.timeline);
    expect(sinks.setFirstPromptText).toHaveBeenCalledWith("hello");
    expect(sinks.setConsultationId).toHaveBeenCalledWith(42);
    expect(sinks.setLastSeedPayload).toHaveBeenCalledWith(minimalSeed);
  });
});
