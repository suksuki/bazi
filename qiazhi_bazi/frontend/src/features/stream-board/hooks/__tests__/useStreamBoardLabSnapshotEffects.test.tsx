import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { MutableRefObject } from "react";
import * as labHydration from "@/features/stream-board/controller/labSnapshotHydration";
import type {
  LabSnapshotHydrationPatch,
  LabSnapshotHydrationSinks,
} from "@/features/stream-board/controller/labSnapshotHydration";
import { useStreamBoardLabSnapshotEffects } from "../useStreamBoardLabSnapshotEffects";
import type { LabSnapshot } from "@/features/stream-board/stores/LabSessionContext";
import type { BaziMetadata } from "@/types/bazi";
import type { SeedPayload } from "@/features/stream-board/models";

const seed: SeedPayload = {
  date: "1990-01-01",
  time: "12:00",
  calendar: "solar",
  gender: "male",
};

function labSnap(overrides: Partial<LabSnapshot> = {}): LabSnapshot {
  return {
    active_session_id: "99",
    metadata: {
      version: "1",
      pillars: {
        year: { stem: "戊", branch: "辰" },
        month: { stem: "己", branch: "巳" },
        day: { stem: "庚", branch: "午" },
        hour: { stem: "辛", branch: "未" },
      },
      conflict_matrix: { points: [] },
      flow_state: "ready",
      notes: "",
    },
    llm_prompt: "p",
    decision_selection_ids: ["d1"],
    resolved_card_ids: ["c1"],
    ...overrides,
  };
}

function createSinksRef(): MutableRefObject<LabSnapshotHydrationSinks> {
  const current: LabSnapshotHydrationSinks = {
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
    setSnapshotAvailable: vi.fn(),
  };
  return { current };
}

describe("useStreamBoardLabSnapshotEffects", () => {
  let applySpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    applySpy = vi.spyOn(labHydration, "applyLabSnapshotHydrationPatch");
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("hydrates from lab snapshot only while metadata is null (推演现场还原)", () => {
    const hydrationSinksRef = createSinksRef();
    const isSnapshotRestoringRef = { current: false };
    const inboxNonceHandledRef = { current: 0 };
    const navHandledRef = { current: true };
    const setSnapshotAvailable = vi.fn();
    const setConfirmedDecisionIds = vi.fn();
    const setResolvedCardIds = vi.fn();
    const setSelectionResetToken = vi.fn();

    const { rerender } = renderHook(
      (props: { metadata: BaziMetadata | null; labSnapshot: LabSnapshot | null }) =>
        useStreamBoardLabSnapshotEffects({
          metadata: props.metadata,
          labSnapshot: props.labSnapshot,
          lastSeedPayload: seed,
          inboxResetNonce: 0,
          isSnapshotRestoringRef,
          inboxNonceHandledRef,
          navHandledRef,
          hydrationSinksRef,
          setSnapshotAvailable,
          setConfirmedDecisionIds,
          setResolvedCardIds,
          setSelectionResetToken,
        }),
      { initialProps: { metadata: null as BaziMetadata | null, labSnapshot: labSnap() } },
    );

    expect(applySpy).toHaveBeenCalledTimes(1);
    expect(applySpy.mock.calls[0][1]).toBe(hydrationSinksRef.current);
    const patch = applySpy.mock.calls[0][0] as LabSnapshotHydrationPatch;
    expect(patch.metadata.pillars?.day?.stem).toBe("庚");

    applySpy.mockClear();
    rerender({ metadata: patch.metadata, labSnapshot: labSnap() });
    expect(applySpy).not.toHaveBeenCalled();
  });

  it("sets restoring flag true during apply and clears after microtask", async () => {
    const hydrationSinksRef = createSinksRef();
    const isSnapshotRestoringRef = { current: false };
    const inboxNonceHandledRef = { current: 0 };
    const navHandledRef = { current: true };
    applySpy.mockImplementation(() => {
      expect(isSnapshotRestoringRef.current).toBe(true);
    });

    renderHook(() =>
      useStreamBoardLabSnapshotEffects({
        metadata: null,
        labSnapshot: labSnap(),
        lastSeedPayload: seed,
        inboxResetNonce: 0,
        isSnapshotRestoringRef,
        inboxNonceHandledRef,
        navHandledRef,
        hydrationSinksRef,
        setSnapshotAvailable: vi.fn(),
        setConfirmedDecisionIds: vi.fn(),
        setResolvedCardIds: vi.fn(),
        setSelectionResetToken: vi.fn(),
      }),
    );

    await act(async () => {
      await Promise.resolve();
    });
    expect(isSnapshotRestoringRef.current).toBe(false);
  });

  it("reflects snapshot presence via setSnapshotAvailable", () => {
    const setSnapshotAvailable = vi.fn();
    const hydrationSinksRef = createSinksRef();
    const isSnapshotRestoringRef = { current: false };
    const inboxNonceHandledRef = { current: 0 };
    const navHandledRef = { current: true };

    const { rerender } = renderHook(
      (snap: LabSnapshot | null) =>
        useStreamBoardLabSnapshotEffects({
          metadata: null,
          labSnapshot: snap,
          lastSeedPayload: null,
          inboxResetNonce: 0,
          isSnapshotRestoringRef,
          inboxNonceHandledRef,
          navHandledRef,
          hydrationSinksRef,
          setSnapshotAvailable,
          setConfirmedDecisionIds: vi.fn(),
          setResolvedCardIds: vi.fn(),
          setSelectionResetToken: vi.fn(),
        }),
      { initialProps: labSnap() as LabSnapshot | null },
    );

    expect(setSnapshotAvailable).toHaveBeenLastCalledWith(true);
    setSnapshotAvailable.mockClear();
    rerender(null);
    expect(setSnapshotAvailable).toHaveBeenLastCalledWith(false);
  });

  it("on inboxResetNonce bump, syncs decision/card ids and bumps selection token", () => {
    const setConfirmedDecisionIds = vi.fn();
    const setResolvedCardIds = vi.fn();
    const setSelectionResetToken = vi.fn();
    const hydrationSinksRef = createSinksRef();
    const isSnapshotRestoringRef = { current: false };
    const inboxNonceHandledRef = { current: 0 };
    const navHandledRef = { current: true };
    const filledMeta: BaziMetadata = {
      version: "1",
      pillars: {
        year: { stem: "戊", branch: "辰" },
        month: { stem: "己", branch: "巳" },
        day: { stem: "庚", branch: "午" },
        hour: { stem: "辛", branch: "未" },
      },
      conflict_matrix: { points: [] },
      flow_state: "ready",
      notes: "",
    };

    const { rerender } = renderHook(
      (props: { nonce: number; snap: LabSnapshot }) =>
        useStreamBoardLabSnapshotEffects({
          metadata: filledMeta,
          labSnapshot: props.snap,
          lastSeedPayload: null,
          inboxResetNonce: props.nonce,
          isSnapshotRestoringRef,
          inboxNonceHandledRef,
          navHandledRef,
          hydrationSinksRef,
          setSnapshotAvailable: vi.fn(),
          setConfirmedDecisionIds,
          setResolvedCardIds,
          setSelectionResetToken,
        }),
      { initialProps: { nonce: 0, snap: labSnap() } },
    );

    expect(setConfirmedDecisionIds).not.toHaveBeenCalled();

    rerender({
      nonce: 1,
      snap: labSnap({ decision_selection_ids: ["x"], resolved_card_ids: ["y"] }),
    });

    expect(setConfirmedDecisionIds).toHaveBeenCalledWith(["x"]);
    expect(setResolvedCardIds).toHaveBeenCalledWith(["y"]);
    expect(setSelectionResetToken).toHaveBeenCalled();
    const updater = setSelectionResetToken.mock.calls[0][0] as (n: number) => number;
    expect(updater(3)).toBe(4);
  });
});
