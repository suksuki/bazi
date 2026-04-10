"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useReducer,
  type ReactNode,
} from "react";
import type { FinalVerdictChangeLog, SeedPayload } from "@/features/stream-board/models";
import type { Lang } from "@/types/bazi";

export type { ShellActiveView } from "@/components/layout/ActiveViewContext";
export { useActiveView } from "@/components/layout/ActiveViewContext";

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

export type LabStoreState = {
  snapshot: LabSnapshot | null;
  updates: LabUpdateRow[];
  causalRevertNonce: number;
  lastSeedPayload: SeedPayload | null;
  uiLang: Lang;
};

const emptyState = (): LabStoreState => ({
  snapshot: null,
  updates: [],
  causalRevertNonce: 0,
  lastSeedPayload: null,
  uiLang: "ZH",
});

type LabAction =
  | { type: "mergeSnapshot"; payload: Partial<LabSnapshot> }
  | { type: "clearSnapshot" }
  | { type: "requestCausalRevert" }
  | { type: "setLastSeedPayload"; payload: SeedPayload | null }
  | { type: "setUiLang"; lang: Lang };

function labReducer(state: LabStoreState, action: LabAction): LabStoreState {
  switch (action.type) {
    case "mergeSnapshot": {
      const payload = action.payload;
      const nextSnapshot: LabSnapshot = {
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
      return {
        ...state,
        snapshot: nextSnapshot,
        updates: [updateRow, ...state.updates].slice(0, 5),
      };
    }
    case "clearSnapshot":
      return { ...emptyState(), uiLang: state.uiLang };
    case "requestCausalRevert": {
      const snap = state.snapshot;
      if (!snap?.baseline_snapshot) return state;
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
      return {
        ...state,
        snapshot: nextSnapshot,
        updates: [updateRow, ...state.updates].slice(0, 5),
        causalRevertNonce: state.causalRevertNonce + 1,
      };
    }
    case "setLastSeedPayload": {
      const payload = action.payload;
      const snap = state.snapshot;
      return {
        ...state,
        lastSeedPayload: payload,
        snapshot: snap ? { ...snap, ts: Date.now() } : snap,
      };
    }
    case "setUiLang":
      return { ...state, uiLang: action.lang };
    default:
      return state;
  }
}

export type LabStoreValue = {
  state: LabStoreState;
  mergeSnapshot: (payload: Partial<LabSnapshot>) => void;
  clearSnapshot: () => void;
  requestCausalRevert: () => void;
  setLastSeedPayload: (payload: SeedPayload | null) => void;
  setUiLang: (lang: Lang) => void;
};

const LabSessionContext = createContext<LabStoreValue | null>(null);

export function LabStoreProvider({ children }: { children: ReactNode }) {
  const [st, dispatch] = useReducer(labReducer, undefined, emptyState);

  const mergeSnapshot = useCallback((payload: Partial<LabSnapshot>) => {
    dispatch({ type: "mergeSnapshot", payload });
  }, []);
  const clearSnapshot = useCallback(() => {
    dispatch({ type: "clearSnapshot" });
  }, []);
  const requestCausalRevert = useCallback(() => {
    dispatch({ type: "requestCausalRevert" });
  }, []);
  const setLastSeedPayload = useCallback((payload: SeedPayload | null) => {
    dispatch({ type: "setLastSeedPayload", payload });
  }, []);
  const setUiLang = useCallback((lang: Lang) => {
    dispatch({ type: "setUiLang", lang });
  }, []);

  const value = useMemo<LabStoreValue>(
    () => ({
      state: st,
      mergeSnapshot,
      clearSnapshot,
      requestCausalRevert,
      setLastSeedPayload,
      setUiLang,
    }),
    [st, mergeSnapshot, clearSnapshot, requestCausalRevert, setLastSeedPayload, setUiLang],
  );

  return <LabSessionContext.Provider value={value}>{children}</LabSessionContext.Provider>;
}

export function useLabStore(): LabStoreValue {
  const ctx = useContext(LabSessionContext);
  if (!ctx) {
    throw new Error("useLabStore must be used within LabStoreProvider");
  }
  return ctx;
}

export function useUiLang(): { uiLang: Lang; setUiLang: (lang: Lang) => void } {
  const { state, setUiLang } = useLabStore();
  return { uiLang: state.uiLang, setUiLang };
}
