"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useReducer,
  useRef,
  type ReactNode,
} from "react";
import type {
  FinalVerdictChangeLog,
  PatternThresholdRow,
  PhysicsLabConfig,
  PluginSwitches,
  PluginWeights,
  SeedPayload,
} from "@/features/stream-board/models";
import type { DecisionJournalEntry } from "@/features/stream-board/decisionJournal";
import { normalizeDecisionJournalEntries } from "@/features/stream-board/decisionJournal";
import { expandResolvedInboxIds } from "@/features/stream-board/cardBuilder";
import { syncLlmRoundsCanonical } from "@/features/stream-board/controller/labLlmRounds";
import type { LabLlmRoundEntry } from "@/features/stream-board/controller/labLlmRounds";
import { computeVerdictEffectiveBlindSkillIds } from "@/features/stream-board/utils/blindSkillRuntime";
import type { Lang } from "@/types/bazi";

export type { ShellActiveView } from "@/components/layout/ActiveViewContext";
export { useActiveView } from "@/components/layout/ActiveViewContext";

const DEFAULT_LAB_RUNTIME: PhysicsLabConfig = {
  WEIGHT_LUCK: 0.4,
  WEIGHT_YEAR: 0.2,
  BASE_BACKFIRE_RISK: 0.2,
  HIGH_IMBALANCE_RISK: 0.35,
  TOMB_LOCK_RATE: 0.9,
  CLIMATE_INTENSITY: 1.0,
  STEM_RESONANCE_BOOST: 1.5,
  TRANSFER_DISTANCE_DECAY: 0.1,
  WORK_MIN_THRESHOLD: 0.5,
  SHOW_WEAK_WORK_PATHS: 1,
  L0_HIDDEN_ENERGY_SCALE: 1.0,
  L0_ROOT_BOOST_FACTOR: 1.0,
  L0_YM_DH_WEIGHT_RATIO: 1.0,
  L1_OP_PROD_ETA: 1.0,
  L1_OP_DEST_ETA: 1.0,
  L1_OP_CONN_ETA: 1.0,
  INTERDIMENSIONAL_CONDUCTIVITY: 0.0,
  INTERDIMENSIONAL_BARRIER_STRENGTH: 1.0,
  CONDUCTIVITY_DECAY_RATE: 0.7,
  GHOST_ENERGY_DAMPING: 0.3,
  MANGPAI_ETA_DIMENSIONAL_CRUSH: 0.6,
  MANGPAI_ROOT_RESONANCE: 1.2,
  INTERDIMENSIONAL_SHIELD_ENABLE: 1.0,
  STEM_BRANCH_ROOT_RESONANCE_ENABLE: 1.0,
  STEM_BRANCH_VERTICAL_CRUSH_ENABLE: 1.0,
  L1_CORE_CONFLICT_OPS_ENABLE: 1.0,
  L1_OWL_FOOD_DAMPING: 0.15,
  L1_WEALTH_SEAL_COLLAPSE: 0.22,
  L1_BLADE_CLASH_INSTABILITY: 0.85,
  L1_ROBBER_WEALTH_ALLOC_LOSS: 0.18,
  L1_GOV_KILL_EFFICIENCY_LOSS: 0.35,
  SGJG_COORDINATE_DISTORTION_DECAY: 0.3,
  GRAVE_BURST_MULTIPLIER: 1.3,
  L1_SANHE_PHI_CLAMP: 1.0,
  STATUS_BOOST_MULTIPLIER: 1.15,
  SUB_BRANCH_SANHE_REQ_WANG_ZHI: 0.0,
  SANHE_ALPHA_LEAKAGE: 0.0,
  user_intention: "seek_stability",
};

const DEFAULT_SWITCHES_RUNTIME: PluginSwitches = {
  blindSchool: true,
  wangshuai: true,
  wealthRisk: false,
  blindSchoolPierceHarm: true,
  blindSchoolTombVault: true,
  blindSchoolHostGuest: true,
};

const DEFAULT_WEIGHTS_RUNTIME: PluginWeights = {
  blindSchool: 0.8,
  wangshuai: 0.6,
};

export type LabRuntimeConfig = {
  labConfig: PhysicsLabConfig;
  pluginSwitches: PluginSwitches;
  pluginWeights: PluginWeights;
};

/** 单次 LLM 往返（首观 / 审计等），供 Debug 与排障 */
export type LabLlmRoundSnapshot = {
  messages?: Array<{ role: string; content: string }>;
  response_text?: string;
  meta?: Record<string, unknown>;
  repair_mode?: string;
};

export type LabSnapshot = {
  ts?: number;
  seed_signature?: string;
  active_session_id?: string | null;
  physics_tensor?: Record<string, unknown>;
  metadata?: Record<string, unknown>;
  timeline?: Record<string, unknown> | null;
  llm_prompt?: string;
  /** 多轮 LLM 往返（由 canonical 字段同步；Debug 页主数据源） */
  llm_rounds?: LabLlmRoundEntry[];
  /** analyze-seed 首观 LLM：完整 messages + 模型回复 + 遥测 */
  first_observation_llm?: LabLlmRoundSnapshot;
  /** /v1/audit-physics-with-llm 结构化审计（含重试则以后端返回为准） */
  physics_auditor_llm?: LabLlmRoundSnapshot;
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
    /** 宾主红利指数（盲派 Skill 审计同步） */
    causal_dividend_index?: number;
    /** 红利 > 0.8 时实验室置顶「主权占优」 */
    sovereignty_dominant?: boolean;
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
    llm_request_messages?: Array<{ role: string; content: string }>;
    llm_raw_response?: string;
    llm_meta?: Record<string, unknown>;
    brain_hub?: Record<string, unknown> | null;
    assertion_tree?: Record<string, unknown> | null;
    narrative_strategy?: string;
    /** 终判段落锚点（地支 / conflict_point），供八字元数据 Tab 联动 */
    narrative_chunks?: Array<{
      chunk_id: string;
      text: string;
      branch_chars?: string[];
      pillar_keys?: string[];
      conflict_point_ids?: string[];
    }>;
  };
  decision_selection_ids?: string[];
  /** 追加型决策日志：语义抑制 Inbox（如三合地支集合），与 physics 张量 id 漂移解耦 */
  decision_journal?: DecisionJournalEntry[];
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

export type FinalizationReport = {
  hash: string;
  committedAt: number;
  /** 签发时生效的盲派 Skill ID（与 skill_manifest / 物理层对齐） */
  effectiveSkillIds?: string[];
};

/** 意志「影子预览」：悬停 Inbox 卡时临时展示，不落 mergeSnapshot */
export type LabShadowPreviewPatch = {
  activePreviewId?: string | null;
  previewDeityScores?: Record<string, number> | null;
  previewDeityEnergyAxes?: Record<string, { absolute_energy?: number; relative_percentage?: number }> | null;
  previewVfSkeleton?: string;
  previewDeltaPctByDeity?: Record<string, number>;
  /** 结构预览：格局跃迁 / 平衡点重塑风险提示（PREVIEW） */
  previewPatternAlert?: string;
  /** 中枢已回传结构类 vf_discovered（预览链建立） */
  previewStructuralLinkActive?: boolean;
  /** 预览 physics_update：格局引力水位 */
  previewPatternThresholds?: PatternThresholdRow[] | null;
};

export type LabStoreState = {
  snapshot: LabSnapshot | null;
  updates: LabUpdateRow[];
  causalRevertNonce: number;
  inboxResetNonce: number;
  lastSeedPayload: SeedPayload | null;
  uiLang: Lang;
  runtimeConfig: LabRuntimeConfig;
  /** 终审已签发：冻结运行时配置写入与快照合并（同宇宙内） */
  isFinalized: boolean;
  finalizationReport: FinalizationReport | null;
  /** 物理静默重算与终判 LLM 协调后的单调序列（供屏障与排障） */
  syncBarrierSeq: number;
  /** 影子预览：当前悬停卡片 id */
  activePreviewId: string | null;
  previewDeityScores: Record<string, number> | null;
  previewDeityEnergyAxes: Record<string, { absolute_energy?: number; relative_percentage?: number }> | null;
  previewVfSkeleton: string;
  previewDeltaPctByDeity: Record<string, number>;
  previewPatternAlert: string;
  previewStructuralLinkActive: boolean;
  previewPatternThresholds: PatternThresholdRow[] | null;
};

const defaultRuntimeConfig = (): LabRuntimeConfig => ({
  labConfig: { ...DEFAULT_LAB_RUNTIME },
  pluginSwitches: { ...DEFAULT_SWITCHES_RUNTIME },
  pluginWeights: { ...DEFAULT_WEIGHTS_RUNTIME },
});

const emptyState = (): LabStoreState => ({
  snapshot: null,
  updates: [],
  causalRevertNonce: 0,
  inboxResetNonce: 0,
  lastSeedPayload: null,
  uiLang: "ZH",
  runtimeConfig: defaultRuntimeConfig(),
  isFinalized: false,
  finalizationReport: null,
  syncBarrierSeq: 0,
  activePreviewId: null,
  previewDeityScores: null,
  previewDeityEnergyAxes: null,
  previewVfSkeleton: "",
  previewDeltaPctByDeity: {},
  previewPatternAlert: "",
  previewStructuralLinkActive: false,
  previewPatternThresholds: null,
});

type LabAction =
  | { type: "mergeSnapshot"; payload: Partial<LabSnapshot> }
  | { type: "clearSnapshot" }
  | { type: "requestCausalRevert" }
  | { type: "setLastSeedPayload"; payload: SeedPayload | null }
  | { type: "setUiLang"; lang: Lang }
  | { type: "setRuntimeConfig"; payload: LabRuntimeConfig }
  | { type: "addConfirmedDecision"; payload: string[] }
  | { type: "clearDecisionInbox" }
  | { type: "finalizeVerdict"; payload: FinalizationReport }
  | { type: "bumpSyncBarrierSeq" }
  | { type: "setShadowPreview"; payload: LabShadowPreviewPatch }
  | { type: "clearShadowPreview" };

function normalizeDecisionIds(ids: unknown[]): string[] {
  return Array.from(new Set(ids.map((x) => String(x || "").trim()).filter(Boolean))).sort();
}

async function sha256HexOfText(text: string): Promise<string> {
  const buf = new TextEncoder().encode(text);
  const hash = await crypto.subtle.digest("SHA-256", buf);
  return Array.from(new Uint8Array(hash))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

function labReducer(state: LabStoreState, action: LabAction): LabStoreState {
  switch (action.type) {
    case "mergeSnapshot": {
      const raw = { ...action.payload } as Record<string, unknown> & Partial<LabSnapshot>;
      let journalReplace: DecisionJournalEntry[] | undefined;
      if (Array.isArray(raw.decision_journal)) {
        journalReplace = normalizeDecisionJournalEntries(raw.decision_journal as unknown[]);
        delete raw.decision_journal;
      }
      if (raw.decision_selection_ids != null && Array.isArray(raw.decision_selection_ids)) {
        raw.decision_selection_ids = normalizeDecisionIds(raw.decision_selection_ids);
      }
      const nextSeedSig =
        typeof raw.seed_signature === "string" && raw.seed_signature.trim() !== ""
          ? raw.seed_signature.trim()
          : undefined;
      const prevSeedSig =
        typeof state.snapshot?.seed_signature === "string" && state.snapshot.seed_signature.trim() !== ""
          ? state.snapshot.seed_signature.trim()
          : null;

      const seedUniverseChanged =
        Boolean(nextSeedSig && prevSeedSig && nextSeedSig !== prevSeedSig);

      if (state.isFinalized && !seedUniverseChanged) {
        return state;
      }

      const keys = Object.keys(action.payload || {});

      let nextSnapshot: LabSnapshot = {
        ...(state.snapshot || {}),
        ...raw,
        ts: Date.now(),
      };
      if (journalReplace !== undefined) {
        nextSnapshot = { ...nextSnapshot, decision_journal: journalReplace };
      }

      nextSnapshot.llm_rounds = syncLlmRoundsCanonical(state.snapshot, nextSnapshot, seedUniverseChanged);

      if (seedUniverseChanged) {
        nextSnapshot.decision_selection_ids = [];
        nextSnapshot.resolved_card_ids = [];
        nextSnapshot.decision_journal = [];
        nextSnapshot.interaction_hub = {
          ...(nextSnapshot.interaction_hub || {}),
          pending_cards: [],
          resolved_card_ids: [],
        };
      }

      const absDeltaRaw = (nextSnapshot.logic_diff || {}).abs_delta;
      const absDelta = typeof absDeltaRaw === "number" && Number.isFinite(absDeltaRaw) ? absDeltaRaw : null;
      const logs = Array.isArray((nextSnapshot.interaction_hub || {}).result_logs)
        ? ((nextSnapshot.interaction_hub || {}).result_logs as string[])
        : [];
      const lastLog = logs.length > 0 ? String(logs[logs.length - 1]) : "";
      const decisionMutation = keys.some(
        (k) =>
          k === "final_verdict" ||
          k === "resolved_card_ids" ||
          k === "decision_selection_ids" ||
          k === "decision_journal",
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
        inboxResetNonce: seedUniverseChanged ? state.inboxResetNonce + 1 : state.inboxResetNonce,
        isFinalized: seedUniverseChanged ? false : state.isFinalized,
        finalizationReport: seedUniverseChanged ? null : state.finalizationReport,
        ...(seedUniverseChanged
          ? {
              activePreviewId: null,
              previewDeityScores: null,
              previewDeityEnergyAxes: null,
              previewVfSkeleton: "",
              previewDeltaPctByDeity: {},
              previewPatternAlert: "",
              previewStructuralLinkActive: false,
              previewPatternThresholds: null,
            }
          : {}),
      };
    }
    case "clearSnapshot":
      return { ...emptyState(), uiLang: state.uiLang };
    case "requestCausalRevert": {
      if (state.isFinalized) return state;
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
    case "setRuntimeConfig":
      if (state.isFinalized) return state;
      return { ...state, runtimeConfig: action.payload };
    case "addConfirmedDecision": {
      if (state.isFinalized) return state;
      const snap = state.snapshot;
      if (!snap) return state;
      const incoming = normalizeDecisionIds(action.payload);
      const prev = Array.isArray(snap.decision_selection_ids) ? snap.decision_selection_ids : [];
      const nextIds = normalizeDecisionIds([...prev, ...incoming]);
      const nextSnapshot: LabSnapshot = {
        ...snap,
        decision_selection_ids: nextIds,
        ts: Date.now(),
      };
      const absDeltaRaw = (nextSnapshot.logic_diff || {}).abs_delta;
      const absDelta = typeof absDeltaRaw === "number" && Number.isFinite(absDeltaRaw) ? absDeltaRaw : null;
      const updateRow: LabUpdateRow = {
        id: `u-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        ts: Date.now(),
        keys: ["decision_selection_ids"],
        abs_delta: absDelta,
        overload: typeof absDelta === "number" && absDelta > 100,
        decisionMutation: true,
      };
      return {
        ...state,
        snapshot: nextSnapshot,
        updates: [updateRow, ...state.updates].slice(0, 5),
      };
    }
    case "clearDecisionInbox": {
      if (state.isFinalized) return state;
      const snap = state.snapshot;
      if (!snap) return state;
      const nextSnapshot: LabSnapshot = {
        ...snap,
        decision_selection_ids: [],
        resolved_card_ids: [],
        interaction_hub: {
          ...(snap.interaction_hub || {}),
          pending_cards: [],
          resolved_card_ids: [],
        },
        ts: Date.now(),
      };
      return {
        ...state,
        snapshot: nextSnapshot,
        inboxResetNonce: state.inboxResetNonce + 1,
      };
    }
    case "finalizeVerdict": {
      if (!state.snapshot || state.isFinalized) return state;
      const { hash, committedAt, effectiveSkillIds } = action.payload;
      const hub = state.snapshot.interaction_hub || {};
      const prevLogs = Array.isArray(hub.result_logs) ? hub.result_logs.map((x) => String(x)) : [];
      const logLine = `[FINAL_DECISION_ISSUED] 因果链条已锁定，指纹: ${hash}`;
      const nextLogs = prevLogs.some((l) => l.includes("[FINAL_DECISION_ISSUED]"))
        ? prevLogs
        : [...prevLogs, logLine].slice(-24);
      const prevMeta = (state.snapshot.metadata || {}) as Record<string, unknown>;
      const fv = (state.snapshot.final_verdict || {}) as Record<string, unknown>;
      const anchorLayer = (prevMeta.verdict_anchor_layer || {}) as { assertions?: unknown[] };
      const assertions = Array.isArray(anchorLayer.assertions) ? anchorLayer.assertions : [];
      const evidenceRefs: string[] = [];
      for (const a of assertions) {
        if (!a || typeof a !== "object" || Array.isArray(a)) continue;
        const er = (a as { evidence_refs?: unknown }).evidence_refs;
        if (Array.isArray(er)) for (const r of er) evidenceRefs.push(String(r));
      }
      const uniqRefs = Array.from(new Set(evidenceRefs)).slice(0, 64);
      const bodyStr = typeof fv.body === "string" ? fv.body : "";
      const versionId = typeof fv.version_id === "string" ? fv.version_id : "";
      const llmMeta = fv.llm_meta && typeof fv.llm_meta === "object" && !Array.isArray(fv.llm_meta) ? (fv.llm_meta as Record<string, unknown>) : {};
      const modelIdRaw = typeof llmMeta.model_name === "string" ? llmMeta.model_name.trim() : "";
      const modelId = modelIdRaw || "unknown";
      const resolvedIds = Array.isArray(state.snapshot.resolved_card_ids)
        ? state.snapshot.resolved_card_ids.map((x) => String(x))
        : [];
      const decisionIds = Array.isArray(state.snapshot.decision_selection_ids)
        ? state.snapshot.decision_selection_ids.map((x) => String(x))
        : [];
      const pt = state.snapshot.physics_tensor as Record<string, unknown> | undefined;
      const suppressed_inbox_card_ids = Array.from(
        expandResolvedInboxIds([...resolvedIds, ...decisionIds], pt ?? null),
      ).slice(0, 64);
      const confirmedRecord = {
        verdict_id: versionId || hash.slice(0, 24),
        body_excerpt: bodyStr.slice(0, 480),
        confirmed_at: new Date(committedAt).toISOString(),
        source_metadata_hash: hash,
        evidence_refs: uniqRefs,
        model_id: modelId,
        suppressed_inbox_card_ids,
      };
      const prevHc = (prevMeta.history_context || {}) as { confirmed_verdicts?: unknown[] };
      const prevCv = Array.isArray(prevHc.confirmed_verdicts) ? [...prevHc.confirmed_verdicts] : [];
      const nextCv = [...prevCv, confirmedRecord].slice(-24);
      const nextSnapshot: LabSnapshot = {
        ...state.snapshot,
        metadata: {
          ...prevMeta,
          finalization: { hash, committed_at: committedAt },
          verdict_effective_skill_ids: effectiveSkillIds ?? [],
          history_context: {
            ...prevHc,
            confirmed_verdicts: nextCv,
          },
        },
        interaction_hub: {
          ...hub,
          result_logs: nextLogs,
        },
        ts: Date.now(),
      };
      const updateRow: LabUpdateRow = {
        id: `u-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
        ts: Date.now(),
        keys: ["finalizeVerdict", "metadata.finalization"],
        abs_delta: typeof (nextSnapshot.logic_diff || {}).abs_delta === "number" ? (nextSnapshot.logic_diff as { abs_delta: number }).abs_delta : null,
        overload: false,
        decisionMutation: true,
      };
      return {
        ...state,
        isFinalized: true,
        finalizationReport: action.payload,
        snapshot: nextSnapshot,
        updates: [updateRow, ...state.updates].slice(0, 5),
        syncBarrierSeq: state.syncBarrierSeq + 1,
        activePreviewId: null,
        previewDeityScores: null,
        previewDeityEnergyAxes: null,
        previewVfSkeleton: "",
        previewDeltaPctByDeity: {},
        previewPatternAlert: "",
        previewStructuralLinkActive: false,
        previewPatternThresholds: null,
      };
    }
    case "bumpSyncBarrierSeq":
      return { ...state, syncBarrierSeq: state.syncBarrierSeq + 1 };
    case "setShadowPreview": {
      const p = action.payload;
      return {
        ...state,
        activePreviewId: p.activePreviewId !== undefined ? p.activePreviewId : state.activePreviewId,
        previewDeityScores: p.previewDeityScores !== undefined ? p.previewDeityScores : state.previewDeityScores,
        previewDeityEnergyAxes:
          p.previewDeityEnergyAxes !== undefined ? p.previewDeityEnergyAxes : state.previewDeityEnergyAxes,
        previewVfSkeleton: p.previewVfSkeleton !== undefined ? p.previewVfSkeleton : state.previewVfSkeleton,
        previewDeltaPctByDeity:
          p.previewDeltaPctByDeity !== undefined ? p.previewDeltaPctByDeity : state.previewDeltaPctByDeity,
        previewPatternAlert:
          p.previewPatternAlert !== undefined ? p.previewPatternAlert : state.previewPatternAlert,
        previewStructuralLinkActive:
          p.previewStructuralLinkActive !== undefined
            ? p.previewStructuralLinkActive
            : state.previewStructuralLinkActive,
        previewPatternThresholds:
          p.previewPatternThresholds !== undefined ? p.previewPatternThresholds : state.previewPatternThresholds,
      };
    }
    // 影子层唯一出口：指针离开 / 新悬停前清场 / SSE 异常（见 useStreamBoardExecution.clearPreview + rAF 二次 flush）
    case "clearShadowPreview":
      return {
        ...state,
        activePreviewId: null,
        previewDeityScores: null,
        previewDeityEnergyAxes: null,
        previewVfSkeleton: "",
        previewDeltaPctByDeity: {},
        previewPatternAlert: "",
        previewStructuralLinkActive: false,
        previewPatternThresholds: null,
      };
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
  setRuntimeConfig: (payload: LabRuntimeConfig) => void;
  addConfirmedDecision: (ids: string[]) => void;
  clearDecisionInbox: () => void;
  finalizeVerdict: () => Promise<boolean>;
  bumpSyncBarrierSeq: () => void;
  setShadowPreview: (payload: LabShadowPreviewPatch) => void;
  clearShadowPreview: () => void;
};

const LabSessionContext = createContext<LabStoreValue | null>(null);

export function LabStoreProvider({ children }: { children: ReactNode }) {
  const [st, dispatch] = useReducer(labReducer, undefined, emptyState);
  const storeRef = useRef(st);
  storeRef.current = st;

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
  const setRuntimeConfig = useCallback((payload: LabRuntimeConfig) => {
    dispatch({ type: "setRuntimeConfig", payload });
  }, []);
  const addConfirmedDecision = useCallback((ids: string[]) => {
    dispatch({ type: "addConfirmedDecision", payload: ids });
  }, []);
  const clearDecisionInbox = useCallback(() => {
    dispatch({ type: "clearDecisionInbox" });
  }, []);
  const finalizeVerdict = useCallback(async () => {
    const s = storeRef.current;
    if (!s.snapshot || s.isFinalized) return false;
    const effectiveSkillIds = computeVerdictEffectiveBlindSkillIds(s.snapshot);
    const snapshotForHash = {
      ...s.snapshot,
      metadata: {
        ...(s.snapshot.metadata || {}),
        verdict_effective_skill_ids: effectiveSkillIds,
      },
    };
    const hash = await sha256HexOfText(JSON.stringify(snapshotForHash));
    dispatch({
      type: "finalizeVerdict",
      payload: { hash, committedAt: Date.now(), effectiveSkillIds },
    });
    return true;
  }, []);
  const bumpSyncBarrierSeq = useCallback(() => {
    dispatch({ type: "bumpSyncBarrierSeq" });
  }, []);
  const setShadowPreview = useCallback((payload: LabShadowPreviewPatch) => {
    dispatch({ type: "setShadowPreview", payload });
  }, []);
  const clearShadowPreview = useCallback(() => {
    dispatch({ type: "clearShadowPreview" });
  }, []);

  const value = useMemo<LabStoreValue>(
    () => ({
      state: st,
      mergeSnapshot,
      clearSnapshot,
      requestCausalRevert,
      setLastSeedPayload,
      setUiLang,
      setRuntimeConfig,
      addConfirmedDecision,
      clearDecisionInbox,
      finalizeVerdict,
      bumpSyncBarrierSeq,
      setShadowPreview,
      clearShadowPreview,
    }),
    [
      st,
      mergeSnapshot,
      clearSnapshot,
      requestCausalRevert,
      setLastSeedPayload,
      setUiLang,
      setRuntimeConfig,
      addConfirmedDecision,
      clearDecisionInbox,
      finalizeVerdict,
      bumpSyncBarrierSeq,
      setShadowPreview,
      clearShadowPreview,
    ],
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
