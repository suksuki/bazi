"use client";

import React from "react";
import type { FinalVerdictChangeLog, SeedPayload } from "@/features/stream-board/models";
import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

/** 实时镜像 vault（磁盘影子副本） */
const VAULT_KEY = "qiazhi_lab_vault";
/** 旧键：仅用于一次性迁移读入 */
const LEGACY_VAULT_KEY = "qiazhi_lab_snapshot";

export type LabSnapshot = {
  ts?: number;
  active_session_id?: string | null;
  physics_tensor?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  timeline?: Record<string, unknown> | null;
  llm_prompt?: string;
  audit_summary?: unknown;
  resolved_card_ids?: string[];
  logic_diff?: {
    baseline_abs_loss_total?: number | null;
    current_abs_loss_total?: number | null;
    abs_delta?: number | null;
    baseline_entropy?: number | null;
    current_entropy?: number | null;
    entropy_delta?: number | null;
  };
  baseline_snapshot?: {
    physics_tensor?: Record<string, unknown> | null;
    global_entropy?: number | null;
    abs_loss_total?: number | null;
    at?: number;
  };
  interaction_hub?: {
    consultation_id?: number | null;
    health?: { db_ok?: boolean; llm_ok?: boolean };
    i18n_calls?: number;
    audit_items?: Array<{ id?: string; step?: string; role?: string; action?: string; timestamp?: string }>;
    result_logs?: string[];
    pending_cards?: Array<{ id?: string; title?: string; card_type?: string }>;
    resolved_card_ids?: string[];
    auditor_briefing?: Record<string, unknown>;
  };
  final_verdict?: {
    body?: string;
    change_log?: FinalVerdictChangeLog;
    logical_evidence?: string[];
    work_vector?: Record<string, unknown> | null;
    topology_graph_v1?: Record<string, unknown> | null;
    structure_candidates_v0?: Record<string, unknown> | null;
    structure_final_decision_v0?: Record<string, unknown> | null;
    version_id?: string;
  };
  /** 主页 Decision 多选（未执行前）与跨页导航恢复 */
  decision_selection_ids?: string[];
};

type LabUpdateRow = {
  id: string;
  ts: number;
  keys: string[];
  abs_delta: number | null;
  overload: boolean;
  last_log?: string;
  reversionImpact?: boolean;
  decisionMutation?: boolean;
};

type LabStoreState = {
  snapshot: LabSnapshot | null;
  updates: LabUpdateRow[];
  causalRevertNonce: number;
  lastSeedPayload: SeedPayload | null;
  sessionRestoredFromVault: boolean;
  _hasHydrated: boolean;
};

const emptyLabStoreState = (): LabStoreState => ({
  snapshot: null,
  updates: [],
  causalRevertNonce: 0,
  lastSeedPayload: null,
  sessionRestoredFromVault: false,
  _hasHydrated: false,
});

function snapshotIndicatesVaultRestore(snapshot: LabSnapshot | null): boolean {
  if (!snapshot) return false;
  return Boolean(
    snapshot.active_session_id
      || snapshot.physics_tensor
      || snapshot.metadata,
  );
}

type LabStoreValue = {
  state: LabStoreState;
  mergeSnapshot: (payload: Partial<LabSnapshot>) => void;
  clearSnapshot: () => void;
  requestCausalRevert: () => void;
  setLastSeedPayload: (payload: SeedPayload | null) => void;
  consumeSessionRestoreMarker: () => void;
  hasHydrated: () => boolean;
};

type LabStoreInternal = LabStoreState & {
  mergeSnapshot: (payload: Partial<LabSnapshot>) => void;
  clearSnapshot: () => void;
  requestCausalRevert: () => void;
  setLastSeedPayload: (payload: SeedPayload | null) => void;
  consumeSessionRestoreMarker: () => void;
};

const useLabStoreInternal = create<LabStoreInternal>()(
  persist(
    (set, get) => ({
      ...emptyLabStoreState(),
      mergeSnapshot: (payload) => {
        const state = get();
        const nextSnapshot = {
          ...(state.snapshot || {}),
          ...payload,
          ts: Date.now(),
        };
        const absDeltaRaw = (nextSnapshot.logic_diff || {}).abs_delta;
        const absDelta = typeof absDeltaRaw === "number" && Number.isFinite(absDeltaRaw) ? absDeltaRaw : null;
        const logs = Array.isArray((nextSnapshot.interaction_hub || {}).result_logs)
          ? ((nextSnapshot.interaction_hub || {}).result_logs as string[])
          : [];
        const lastLog = logs.length > 0 ? String(logs[logs.length - 1]) : "";
        const keys = Object.keys(payload || {});
        const decisionMutation = keys.some(
          (k) => k === "final_verdict" || k === "resolved_card_ids" || k === "decision_selection_ids",
        );
        const updateRow: LabUpdateRow = {
          id: `u-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          ts: Date.now(),
          keys,
          abs_delta: absDelta,
          overload: typeof absDelta === "number" && absDelta > 100,
          last_log: lastLog || undefined,
          reversionImpact: lastLog.includes("[REVERSION_IMPACT]"),
          decisionMutation,
        };
        set({
          snapshot: nextSnapshot,
          updates: [updateRow, ...state.updates].slice(0, 5),
        });
      },
      clearSnapshot: () => set(emptyLabStoreState()),
      requestCausalRevert: () => {
        const state = get();
        const snap = state.snapshot;
        if (!snap?.baseline_snapshot) return;
        const b = snap.baseline_snapshot;
        const physics =
          b.physics_tensor != null
            ? (JSON.parse(JSON.stringify(b.physics_tensor)) as Record<string, unknown>)
            : b.physics_tensor === null
              ? undefined
              : snap.physics_tensor;
        const absLoss = typeof b.abs_loss_total === "number" ? b.abs_loss_total : null;
        const entropy = typeof b.global_entropy === "number" ? b.global_entropy : null;
        const logic_diff = {
          baseline_abs_loss_total: absLoss,
          current_abs_loss_total: absLoss,
          abs_delta: 0,
          baseline_entropy: entropy,
          current_entropy: entropy,
          entropy_delta: 0,
        };
        const nextSnapshot: LabSnapshot = {
          ...snap,
          physics_tensor: physics,
          logic_diff,
          ts: Date.now(),
        };
        const updateRow: LabUpdateRow = {
          id: `u-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
          ts: Date.now(),
          keys: ["causal_revert", "physics_tensor", "logic_diff"],
          abs_delta: 0,
          overload: false,
          reversionImpact: false,
          decisionMutation: false,
        };
        set({
          snapshot: nextSnapshot,
          updates: [updateRow, ...state.updates].slice(0, 5),
          causalRevertNonce: state.causalRevertNonce + 1,
        });
      },
      setLastSeedPayload: (payload) => {
        const snapshot = get().snapshot;
        set({
          lastSeedPayload: payload,
          snapshot: snapshot ? { ...snapshot, ts: Date.now() } : snapshot,
        });
      },
      consumeSessionRestoreMarker: () => set({ sessionRestoredFromVault: false }),
    }),
    {
      name: VAULT_KEY,
      storage: createJSONStorage(() => sessionStorage),
      skipHydration: false,
      partialize: (state) => ({
        snapshot: state.snapshot,
        updates: state.updates,
        lastSeedPayload: state.lastSeedPayload,
      }),
      onRehydrateStorage: () => (state) => {
        if (!state) return;
        const restored = snapshotIndicatesVaultRestore(state.snapshot);
        state.sessionRestoredFromVault = restored;
        state._hasHydrated = true;
      },
    },
  ),
);

export function LabStoreProvider({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

export function useLabStore(): LabStoreValue {
  const snapshot = useLabStoreInternal((s) => s.snapshot);
  const updates = useLabStoreInternal((s) => s.updates);
  const causalRevertNonce = useLabStoreInternal((s) => s.causalRevertNonce);
  const lastSeedPayload = useLabStoreInternal((s) => s.lastSeedPayload);
  const sessionRestoredFromVault = useLabStoreInternal((s) => s.sessionRestoredFromVault);
  const _hasHydrated = useLabStoreInternal((s) => s._hasHydrated);
  const mergeSnapshot = useLabStoreInternal((s) => s.mergeSnapshot);
  const clearSnapshot = useLabStoreInternal((s) => s.clearSnapshot);
  const requestCausalRevert = useLabStoreInternal((s) => s.requestCausalRevert);
  const setLastSeedPayload = useLabStoreInternal((s) => s.setLastSeedPayload);
  const consumeSessionRestoreMarker = useLabStoreInternal((s) => s.consumeSessionRestoreMarker);
  return {
    state: {
      snapshot,
      updates,
      causalRevertNonce,
      lastSeedPayload,
      sessionRestoredFromVault,
      _hasHydrated,
    },
    mergeSnapshot,
    clearSnapshot,
    requestCausalRevert,
    setLastSeedPayload,
    consumeSessionRestoreMarker,
    hasHydrated: () => _hasHydrated,
  };
}

useLabStore.persist = {
  hasHydrated: () => {
    // eslint-disable-next-line react-hooks/rules-of-hooks
    return useLabStoreInternal((s) => s._hasHydrated);
  },
};


