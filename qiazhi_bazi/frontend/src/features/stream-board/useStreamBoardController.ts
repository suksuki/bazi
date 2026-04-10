"use client";

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import type { AuditItem, AuditRole } from "@/components/AuditSidebar";
import type { BaziMetadata, Lang, TimelineSnapshot } from "@/types/bazi";
import { adminHeaders, API_BASE, VERDICT_TIMEOUT_MS } from "./constants";
import { buildInboxCards, createAuditorProposalCard } from "./cardBuilder";
import type {
  DeityComponent,
  DeityEnergyAxis,
  FinalVerdictChangeLog,
  FinalVerdictHistoryItem,
  InboxCard,
  LogicDiff,
  LlmDiagnosticData,
  LogicProposal,
  PhysicsLabConfig,
  PluginSwitches,
  PluginWeights,
  SeedPayload,
  StreamBoardViewModel,
} from "./models";
import { buildFallbackVerdict, calculateFireEnergyAfterConflicts } from "./utils";
import { useClientSearchParams } from "./useClientSearchParams";
import { useTranslationQueue } from "./useTranslationQueue";
import { useActiveView, type ShellActiveView } from "@/components/layout/ActiveViewContext";
import { useLabConfig } from "@/features/lab-config/LabConfigContext";
import { useLabStore, useUiLang } from "@/features/stream-board/stores/useLabStore";

type ConsensusItem = { decision_key: string; confirmed_value?: number; reasoning?: string };
type ConfirmedDecisionItem = { id: string; label: string; is_confirmed: boolean; confirmed_at?: string };
type MetricSnapshot = { absLossTotal: number | null; entropy: number | null };

type SilentBoardCtx = {
  consultationId: number | null;
  labConfig: PhysicsLabConfig;
  pluginSwitches: PluginSwitches;
  pluginWeights: PluginWeights;
  lang: Lang;
  baselineMetrics: MetricSnapshot | null;
  confirmedDecisionIds: string[];
};

function buildBlindSchoolFeaturesPayload(sw: PluginSwitches) {
  return {
    enable_pierce_harm: sw.blindSchoolPierceHarm !== false,
    enable_tomb_vault: sw.blindSchoolTombVault !== false,
    enable_host_guest_bonus: sw.blindSchoolHostGuest !== false,
  };
}

function extractMetricSnapshotFromPhysics(physicsTensor: Record<string, unknown> | null | undefined): MetricSnapshot {
  const auditLog = (physicsTensor?.audit_log as Record<string, unknown> | undefined) || {};
  const trace = (auditLog.trace as Record<string, unknown> | undefined) || {};
  const meta = (physicsTensor?.meta as Record<string, unknown> | undefined) || {};
  const absRaw = trace.clash_abs_loss_total ?? auditLog.clash_abs_loss_total ?? meta.clash_abs_loss_total ?? meta.abs_loss_total;
  const entropyRaw = meta.global_entropy;
  return {
    absLossTotal: typeof absRaw === "number" && Number.isFinite(absRaw) ? absRaw : null,
    entropy: typeof entropyRaw === "number" && Number.isFinite(entropyRaw) ? entropyRaw : null,
  };
}

/** 后端 meta.interaction_hub_mangpai → 并入实验室 interaction_hub（主权占优金标等） */
function extractInteractionHubMangpai(physicsTensor: Record<string, unknown> | null | undefined): Record<string, unknown> {
  if (!physicsTensor || typeof physicsTensor !== "object") return {};
  const meta = physicsTensor.meta as Record<string, unknown> | undefined;
  const m = meta?.interaction_hub_mangpai;
  if (!m || typeof m !== "object" || Array.isArray(m)) return {};
  return m as Record<string, unknown>;
}

function seedPayloadSignature(seed: SeedPayload | null | undefined): string | null {
  if (!seed) return null;
  return JSON.stringify({
    date: seed.date,
    time: seed.time,
    calendar: seed.calendar,
    gender: seed.gender,
  });
}

type NavigationInfo = {
  navType: "reload" | "navigate" | "back_forward" | "unknown";
  hasValidSnapshot: boolean;
  intent: "FRESH_START" | "RESTORE_AUDIT";
};

function interpolateColor(startHex: string, endHex: string, ratio: number): string {
  const normalized = Math.max(0, Math.min(1, ratio));
  const parse = (hex: string) => {
    const v = hex.replace("#", "");
    const full = v.length === 3 ? v.split("").map((x) => `${x}${x}`).join("") : v;
    return {
      r: parseInt(full.slice(0, 2), 16),
      g: parseInt(full.slice(2, 4), 16),
      b: parseInt(full.slice(4, 6), 16),
    };
  };
  const a = parse(startHex);
  const b = parse(endHex);
  const toHex = (v: number) => Math.round(v).toString(16).padStart(2, "0");
  const r = a.r + (b.r - a.r) * normalized;
  const g = a.g + (b.g - a.g) * normalized;
  const bVal = a.b + (b.b - a.b) * normalized;
  return `#${toHex(r)}${toHex(g)}${toHex(bVal)}`;
}

export function useStreamBoardController(): StreamBoardViewModel {
  const searchParams = useClientSearchParams();
  const {
    state: labState,
    mergeSnapshot,
    setLastSeedPayload: persistLastSeedToStore,
    finalizeVerdict,
    bumpSyncBarrierSeq,
  } = useLabStore();
  const { activeView } = useActiveView();
  const labStateRef = useRef(labState);
  labStateRef.current = labState;
  const initialSnapshot = (labState.snapshot || null) as {
    physics_tensor?: Record<string, unknown>;
    final_verdict?: {
      body?: string;
      change_log?: FinalVerdictChangeLog;
      logical_evidence?: string[];
      work_vector?: Record<string, unknown>;
      topology_graph_v1?: Record<string, unknown>;
      structure_candidates_v0?: Record<string, unknown>;
      structure_final_decision_v0?: Record<string, unknown>;
      version_id?: string;
    };
    decision_selection_ids?: string[];
  } | null;
  const { uiLang, setUiLang } = useUiLang();
  const [lang, setLangState] = useState<Lang>("ZH");
  const langRef = useRef<Lang>("ZH");
  const lastSeedPayloadRef = useRef<SeedPayload | null>(null);
  const metadataRef = useRef<BaziMetadata | null>(null);
  const busyRef = useRef(false);
  const isStreamingRef = useRef(false);
  const isExecutingRef = useRef(false);

  useEffect(() => {
    if (uiLang === langRef.current) return;
    langRef.current = uiLang;
    setLangState(uiLang);
  }, [uiLang]);

  const [busy, setBusy] = useState(false);
  const [selectedBranch, setSelectedBranch] = useState<string>();
  const [metadata, setMetadata] = useState<BaziMetadata | null>(null);
  const [streamingText, setStreamingText] = useState("");
  const [consultationId, setConsultationId] = useState<number | null>(null);
  const [auditItems, setAuditItems] = useState<AuditItem[]>([]);
  const [health, setHealth] = useState({ dbOk: false, llmOk: false });
  const [llmModelName, setLlmModelName] = useState("LLM");
  const [resultLogs, setResultLogs] = useState<string[]>([]);
  const [confirmedConflicts, setConfirmedConflicts] = useState<string[]>([]);
  const [firstPromptText, setFirstPromptText] = useState("");
  const [timeline, setTimeline] = useState<TimelineSnapshot | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [deityScores, setDeityScores] = useState<Record<string, number>>(
    () => ((initialSnapshot?.physics_tensor?.deity_scores as Record<string, number> | undefined) || {}),
  );
  const [deityEnergyAxes, setDeityEnergyAxes] = useState<Record<string, DeityEnergyAxis>>(
    () => ((initialSnapshot?.physics_tensor?.deity_energy_axes as Record<string, DeityEnergyAxis> | undefined) || {}),
  );
  const [deityComponents, setDeityComponents] = useState<Record<string, DeityComponent>>(
    () => ((initialSnapshot?.physics_tensor?.deity_components as Record<string, DeityComponent> | undefined) || {}),
  );
  const [deityTraceDetails, setDeityTraceDetails] = useState<Record<string, Record<string, unknown>>>(
    () => ((initialSnapshot?.physics_tensor?.deity_trace_details as Record<string, Record<string, unknown>> | undefined) || {}),
  );
  const [hoveredDeity, setHoveredDeity] = useState<string>();
  const [physicsAudit, setPhysicsAudit] = useState<Record<string, unknown> | null>(null);
  const [physicsConfidence, setPhysicsConfidence] = useState<number | null>(null);
  const [physicsEvidence, setPhysicsEvidence] = useState<string[]>([]);
  const { labConfig, setLabConfig, pluginSwitches, setPluginSwitches, pluginWeights, setPluginWeights } = useLabConfig();
  const [showPhysicsAudit, setShowPhysicsAudit] = useState(false);
  const [llmDiagnosticData, setLlmDiagnosticData] = useState<LlmDiagnosticData | null>(null);
  const [lastSeedPayload, setLastSeedPayload] = useState<SeedPayload | null>(null);
  const [auditorProposalCards, setAuditorProposalCards] = useState<InboxCard[]>([]);
  const [physicsParams, setPhysicsParams] = useState<Record<string, number>>({});
  const [globalEntropy, setGlobalEntropy] = useState<number | null>(null);
  const [autoConvertedParamKey, setAutoConvertedParamKey] = useState<string | null>(null);
  const [resolvedCardIds, setResolvedCardIds] = useState<string[]>([]);
  const [selectionResetToken, setSelectionResetToken] = useState(0);
  const [sigShiftFlashKey, setSigShiftFlashKey] = useState(0);
  const [conclusionVersion, setConclusionVersion] = useState(0);
  const [lastConclusionText, setLastConclusionText] = useState("");
  const [summaryChanged, setSummaryChanged] = useState(false);
  const [consensusHistory, setConsensusHistory] = useState<ConsensusItem[]>([]);
  const [finalVerdictBody, setFinalVerdictBody] = useState(() => String(initialSnapshot?.final_verdict?.body || ""));
  const [finalVerdictChangeLog, setFinalVerdictChangeLog] = useState<FinalVerdictChangeLog>(
    () => (initialSnapshot?.final_verdict?.change_log || {}) as FinalVerdictChangeLog,
  );
  const [finalVerdictVersionId, setFinalVerdictVersionId] = useState(() => String(initialSnapshot?.final_verdict?.version_id || ""));
  const [finalLogicalEvidence, setFinalLogicalEvidence] = useState<string[]>(
    () => (Array.isArray(initialSnapshot?.final_verdict?.logical_evidence) ? initialSnapshot.final_verdict.logical_evidence.map((x) => String(x)) : []),
  );
  const [finalWorkVector, setFinalWorkVector] = useState<Record<string, unknown> | null>(
    () => (initialSnapshot?.final_verdict?.work_vector as Record<string, unknown>) || null,
  );
  const [finalTopologyGraphV1, setFinalTopologyGraphV1] = useState<Record<string, unknown> | null>(
    () => (initialSnapshot?.final_verdict?.topology_graph_v1 as Record<string, unknown>) || null,
  );
  const [finalStructureCandidatesV0, setFinalStructureCandidatesV0] = useState<Record<string, unknown> | null>(
    () => (initialSnapshot?.final_verdict?.structure_candidates_v0 as Record<string, unknown>) || null,
  );
  const [finalStructureFinalDecisionV0, setFinalStructureFinalDecisionV0] = useState<Record<string, unknown> | null>(
    () => (initialSnapshot?.final_verdict?.structure_final_decision_v0 as Record<string, unknown>) || null,
  );
  const [confirmedDecisions, setConfirmedDecisions] = useState<ConfirmedDecisionItem[]>([]);
  const [confirmedDecisionIds, setConfirmedDecisionIds] = useState<string[]>(
    () => [...new Set((initialSnapshot?.decision_selection_ids || []).map((x) => String(x).trim()).filter(Boolean))].sort(),
  );
  const urlDecisionHydrated = true;
  const isSnapshotRestoringRef = useRef(false);
  const reCalculateAbsSilentlyImplRef = useRef<() => Promise<void>>(async () => {});
  const runtimeConfigSerializedRef = useRef<string | null>(null);
  const pluginRecalcTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const silentRecalcInFlightRef = useRef(false);
  const inboxNonceHandledRef = useRef(0);
  const verdictRecalcBarrierRef = useRef(false);
  const silentRecalcDeferredRef = useRef(false);
  const reCalculateAbsRef = useRef<() => Promise<void>>(async () => {});
  const prevActiveViewRef = useRef<ShellActiveView | null>(null);
  const isRestoringRef = useRef(false);
  const silentCtxRef = useRef<SilentBoardCtx>({
    consultationId: null,
    labConfig: {
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
    },
    pluginSwitches: {
      blindSchool: true,
      wangshuai: true,
      wealthRisk: false,
      blindSchoolPierceHarm: true,
      blindSchoolTombVault: true,
      blindSchoolHostGuest: true,
    },
    pluginWeights: { blindSchool: 0.8, wangshuai: 0.6 },
    lang: "ZH",
    baselineMetrics: null,
    confirmedDecisionIds: [],
  });
  const settersRef = useRef({
    setMetadata: (_m: BaziMetadata | null) => {},
    setTimeline: (_t: TimelineSnapshot | null) => {},
    setDeityScores: (_s: Record<string, number>) => {},
    setDeityEnergyAxes: (_a: Record<string, DeityEnergyAxis>) => {},
    setDeityComponents: (_c: Record<string, DeityComponent>) => {},
    setDeityTraceDetails: (_d: Record<string, Record<string, unknown>>) => {},
    setPhysicsAudit: (_a: Record<string, unknown> | null) => {},
    setPhysicsConfidence: (_n: number | null) => {},
    setPhysicsEvidence: (_e: string[]) => {},
    setPhysicsParams: (_p: Record<string, number>) => {},
    setGlobalEntropy: (_g: number | null) => {},
  });
  const navHandledRef = useRef(false);
  const [isRestoring, setIsRestoring] = useState(false);
  const [baselineMetrics, setBaselineMetrics] = useState<MetricSnapshot | null>(null);
  const [logicDiff, setLogicDiff] = useState<LogicDiff>({
    baseline_abs_loss_total: null,
    current_abs_loss_total: null,
    abs_delta: null,
    baseline_entropy: null,
    current_entropy: null,
    entropy_delta: null,
  });
  const [finalVerdictHistory, setFinalVerdictHistory] = useState<FinalVerdictHistoryItem[]>([]);
  const [stressTestResult, setStressTestResult] = useState<Record<string, unknown> | null>(null);
  const [genderComparisonResult, setGenderComparisonResult] = useState<Record<string, unknown> | null>(null);
  const [logicDrawerOpen, setLogicDrawerOpen] = useState(false);
  const [logicDrawerTitle, setLogicDrawerTitle] = useState("Arbiter Logic Drawer");
  const [logicDrawerFocus, setLogicDrawerFocus] = useState("");
  const [logicDrawerDetails, setLogicDrawerDetails] = useState<string[]>([]);
  const [logicDrawerTrace, setLogicDrawerTrace] = useState<Record<string, unknown> | null>(null);
  const [snapshotAvailable, setSnapshotAvailable] = useState(false);

  const { i18nCalls, t } = useTranslationQueue({
    lang,
    isExecuting,
    isStreaming,
    dynamicTexts: [
      ...(metadata?.conflict_matrix.points.map((point) => point.detail) || []),
      ...firstPromptText
        .replace(/\r/g, "")
        .split(/\n+/)
        .flatMap((line) => line.split(/(?<=[。！？!?])/))
        .map((item) => item.trim())
        .filter(Boolean)
        .slice(0, 4),
      ...auditorProposalCards.map((card) => card.conflictDetail || card.title),
      ...auditItems.map((item) => item.action),
      ...resultLogs,
    ],
  });

  const cards = useMemo(
    () => buildInboxCards({ metadata, firstPromptText, auditorProposalCards, resolvedCardIds, t }),
    [metadata, firstPromptText, auditorProposalCards, resolvedCardIds, t],
  );
  const normalizeDecisionIds = (list: string[]) => [...new Set(list.map((item) => String(item || "").trim()).filter(Boolean))].sort();
  const updateLogicDiff = (current: MetricSnapshot, forceBaseline = false): LogicDiff => {
    const baselineFromStore = (() => {
      const b = labState.snapshot?.baseline_snapshot;
      if (!b) return null;
      const absLoss = typeof b.abs_loss_total === "number"
        ? b.abs_loss_total
        : extractMetricSnapshotFromPhysics((b.physics_tensor || null) as Record<string, unknown> | null).absLossTotal;
      const entropy = typeof b.global_entropy === "number"
        ? b.global_entropy
        : extractMetricSnapshotFromPhysics((b.physics_tensor || null) as Record<string, unknown> | null).entropy;
      return { absLossTotal: absLoss ?? null, entropy: entropy ?? null } as MetricSnapshot;
    })();
    const shouldSetBaseline = forceBaseline || (!baselineFromStore && !baselineMetrics);
    const base = shouldSetBaseline ? current : (baselineFromStore || baselineMetrics);
    if (shouldSetBaseline) setBaselineMetrics(current);
    const baseAbs = base?.absLossTotal ?? null;
    const baseEntropy = base?.entropy ?? null;
    const nextDiff: LogicDiff = {
      baseline_abs_loss_total: baseAbs,
      current_abs_loss_total: current.absLossTotal,
      abs_delta: baseAbs !== null && current.absLossTotal !== null ? current.absLossTotal - baseAbs : null,
      baseline_entropy: baseEntropy,
      current_entropy: current.entropy,
      entropy_delta: baseEntropy !== null && current.entropy !== null ? current.entropy - baseEntropy : null,
    };
    setLogicDiff(nextDiff);
    mergeSnapshot({ logic_diff: nextDiff });
    return nextDiff;
  };
  const updateLogicDiffRef = useRef(updateLogicDiff);
  updateLogicDiffRef.current = updateLogicDiff;
  const setAsBaseline = () => {
    const currentTensor = (labState.snapshot?.physics_tensor || null) as Record<string, unknown> | null;
    const snapshot: MetricSnapshot = {
      absLossTotal: typeof (finalWorkVector as { backfire_risk?: unknown } | null)?.backfire_risk === "number"
        ? Number((finalWorkVector as { backfire_risk?: number }).backfire_risk)
        : null,
      entropy: globalEntropy,
    };
    setBaselineMetrics(snapshot);
    setLogicDiff({
      baseline_abs_loss_total: snapshot.absLossTotal,
      current_abs_loss_total: snapshot.absLossTotal,
      abs_delta: 0,
      baseline_entropy: snapshot.entropy,
      current_entropy: snapshot.entropy,
      entropy_delta: 0,
    });
    mergeSnapshot({
      baseline_snapshot: {
        physics_tensor: currentTensor ? JSON.parse(JSON.stringify(currentTensor)) as Record<string, unknown> : null,
        global_entropy: snapshot.entropy,
        abs_loss_total: snapshot.absLossTotal,
        at: Date.now(),
      },
      logic_diff: {
        baseline_abs_loss_total: snapshot.absLossTotal,
        current_abs_loss_total: snapshot.absLossTotal,
        abs_delta: 0,
        baseline_entropy: snapshot.entropy,
        current_entropy: snapshot.entropy,
        entropy_delta: 0,
      },
    });
    setResultLogs((prev) => [...prev, "因果锚点已固化"]);
  };

  const appendSystemAuditLog = (line: string) => {
    const text = String(line || "").trim();
    if (!text) return;
    setResultLogs((prev) => {
      const next = [...prev, text];
      mergeSnapshot({
        interaction_hub: {
          ...((labState.snapshot?.interaction_hub || {}) as Record<string, unknown>),
          result_logs: next.slice(-24),
        },
      });
      return next;
    });
  };

  useEffect(() => {
    if (!labState.isFinalized || !labState.finalizationReport?.hash) return;
    const line = `[FINAL_DECISION_ISSUED] 因果链条已锁定，指纹: ${labState.finalizationReport.hash}`;
    setResultLogs((prev) => {
      if (prev.some((l) => String(l).includes("[FINAL_DECISION_ISSUED]"))) return prev;
      return [...prev, line];
    });
  }, [labState.isFinalized, labState.finalizationReport?.hash]);

  const pendingDecisionCount = cards.filter((card) => card.id !== "fallback-deep-scan").length;
  const l1Certified = Boolean(llmDiagnosticData?.alignment_score && llmDiagnosticData.alignment_score > 80) && pendingDecisionCount === 0;
  const hardRouteLogs = useMemo<string[]>(
    () => ((((physicsAudit as { trace?: { hard_route_logs?: string[] } } | null)?.trace?.hard_route_logs) || []) as string[]),
    [physicsAudit],
  );

  const buildInteractionHub = (opts?: {
    consultationIdOverride?: number | null;
    healthOverride?: { dbOk: boolean; llmOk: boolean };
    auditorBriefingOverride?: Record<string, unknown> | null;
  }) => {
    const h = opts?.healthOverride || health;
    const briefing = opts?.auditorBriefingOverride || (llmDiagnosticData ? {
      alignment_score: llmDiagnosticData.alignment_score,
      structured_hit: llmDiagnosticData.structured_hit,
      repair_mode: llmDiagnosticData.repair_mode,
      top_anomaly: llmDiagnosticData.top_anomaly,
      causal_reasoning: llmDiagnosticData.causal_reasoning,
      tuning_suggestions: llmDiagnosticData.tuning_suggestions,
      logic_proposal: llmDiagnosticData.logic_proposal,
      auto_joined_decision_box: Boolean(llmDiagnosticData.logic_proposal?.param_key),
    } : null);
    return {
      consultation_id: opts?.consultationIdOverride ?? consultationId ?? null,
      health: {
        db_ok: Boolean(h.dbOk),
        llm_ok: Boolean(h.llmOk),
      },
      i18n_calls: i18nCalls,
      audit_items: auditItems.map((item) => ({
        id: item.id,
        step: item.step || "",
        role: item.role,
        action: item.action,
        timestamp: item.timestamp,
      })),
      result_logs: resultLogs.slice(-24),
      pending_cards: cards
        .filter((card) => card.id !== "fallback-deep-scan")
        .map((card) => ({
          id: card.id,
          title: card.title,
          card_type: card.cardType || "conflict",
        })),
      resolved_card_ids: resolvedCardIds.slice(-120),
      auditor_briefing: briefing || undefined,
    };
  };

  const persistSnapshot = (payload: {
    physics_tensor: Record<string, unknown>;
    metadata?: Record<string, unknown>;
    timeline?: Record<string, unknown> | null;
    llm_prompt?: string;
    audit_summary?: unknown;
    consultationIdOverride?: number | null;
    healthOverride?: { dbOk: boolean; llmOk: boolean };
    auditorBriefingOverride?: Record<string, unknown> | null;
    seedSignatureOverride?: string | null;
    finalVerdictOverride?: {
      body?: string;
      change_log?: FinalVerdictChangeLog;
      logical_evidence?: string[];
      work_vector?: Record<string, unknown> | null;
      topology_graph_v1?: Record<string, unknown> | null;
      structure_candidates_v0?: Record<string, unknown> | null;
      structure_final_decision_v0?: Record<string, unknown> | null;
      version_id?: string;
    };
  }) => {
    if (isSnapshotRestoringRef.current || isRestoring) return;
    if (labStateRef.current.isFinalized) return;
    const previousFinalVerdict = (labState.snapshot?.final_verdict || null) as Record<string, unknown> | null;
    const seedSig =
      payload.seedSignatureOverride !== undefined
        ? payload.seedSignatureOverride
        : seedPayloadSignature(lastSeedPayload);
    mergeSnapshot({
      active_session_id: payload.consultationIdOverride != null
        ? String(payload.consultationIdOverride)
        : (labState.snapshot?.active_session_id || `session-${Date.now()}`),
      physics_tensor: payload.physics_tensor,
      metadata: payload.metadata,
      timeline: payload.timeline ?? null,
      llm_prompt: payload.llm_prompt || "",
      audit_summary: payload.audit_summary,
      ...(seedSig ? { seed_signature: seedSig } : {}),
      resolved_card_ids: resolvedCardIds.slice(-240),
      decision_selection_ids: normalizeDecisionIds(confirmedDecisionIds),
      interaction_hub: {
        ...buildInteractionHub({
          consultationIdOverride: payload.consultationIdOverride,
          healthOverride: payload.healthOverride,
          auditorBriefingOverride: payload.auditorBriefingOverride,
        }),
        ...extractInteractionHubMangpai(payload.physics_tensor),
      },
      final_verdict: payload.finalVerdictOverride || previousFinalVerdict || {
        body: finalVerdictBody,
        change_log: finalVerdictChangeLog,
        logical_evidence: finalLogicalEvidence,
        work_vector: finalWorkVector,
        topology_graph_v1: finalTopologyGraphV1,
        structure_candidates_v0: finalStructureCandidatesV0,
        structure_final_decision_v0: finalStructureFinalDecisionV0,
        version_id: finalVerdictVersionId,
      },
    });
    setSnapshotAvailable(true);
  };

  const persistSnapshotRef = useRef(persistSnapshot);
  persistSnapshotRef.current = persistSnapshot;

  /** 等 React 提交 audit_items / result_logs 后再写入 interaction_hub，否则黑匣子一直是空 hub。 */
  const scheduleInteractionHubPersist = useCallback(() => {
    window.setTimeout(() => {
      if (labStateRef.current.isFinalized) return;
      const snap = labStateRef.current.snapshot;
      if (!snap?.physics_tensor) return;
      const sidRaw = snap.active_session_id;
      let consultationIdOverride: number | null = null;
      if (sidRaw != null && String(sidRaw).trim() !== "") {
        const n = Number(String(sidRaw));
        if (Number.isFinite(n)) consultationIdOverride = n;
      }
      persistSnapshotRef.current({
        physics_tensor: snap.physics_tensor as Record<string, unknown>,
        metadata: (snap.metadata ?? {}) as Record<string, unknown>,
        timeline: (snap.timeline ?? null) as Record<string, unknown> | null,
        llm_prompt: String(snap.llm_prompt || ""),
        audit_summary: snap.audit_summary,
        consultationIdOverride,
      });
    }, 0);
  }, []);

  const markActiveSession = (sessionId?: number | null) => {
    const sid = sessionId != null ? String(sessionId) : (labState.snapshot?.active_session_id || `session-${Date.now()}`);
    mergeSnapshot({ active_session_id: sid });
  };

  const mergeSnapshotRef = useRef(mergeSnapshot);
  mergeSnapshotRef.current = mergeSnapshot;

  useEffect(() => {
    if (!urlDecisionHydrated) return;
    if (isSnapshotRestoringRef.current || isRestoring) return;
    if (!labState.snapshot?.active_session_id) return;
    const next = normalizeDecisionIds(confirmedDecisionIds);
    const prev = normalizeDecisionIds(labState.snapshot?.decision_selection_ids || []);
    if (next.join("\u0000") === prev.join("\u0000")) return;
    mergeSnapshotRef.current({ decision_selection_ids: next });
  }, [
    confirmedDecisionIds,
    urlDecisionHydrated,
    isRestoring,
    labState.snapshot?.active_session_id,
    labState.snapshot?.decision_selection_ids,
  ]);

  async function refreshHealth() {
    let dbOk = false;
    let llmOk = false;

    try {
      const dbResponse = await fetch(`${API_BASE}/api/admin/db-status`, { headers: adminHeaders });
      const dbData = await dbResponse.json();
      dbOk = Boolean(dbData?.ok);
    } catch {
      dbOk = false;
    }

    try {
      const configResponse = await fetch(`${API_BASE}/api/admin/runtime-config`, { headers: adminHeaders });
      const configData = await configResponse.json();
      const llm = configData?.config?.llm ?? {};
      setLlmModelName(String(llm.model || "LLM"));

      const modelsResponse = await fetch(`${API_BASE}/api/admin/llm-models`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...adminHeaders },
        body: JSON.stringify({ base_url: llm.base_url, api_key: llm.api_key }),
      });
      const modelsData = await modelsResponse.json();
      llmOk = Boolean(modelsData?.ok && Array.isArray(modelsData?.models));
    } catch {
      llmOk = false;
      setLlmModelName("LLM");
    }

    const next = { dbOk, llmOk };
    setHealth(next);
    return next;
  }

  const refreshHealthRef = useRef(refreshHealth);
  refreshHealthRef.current = refreshHealth;

  async function typewriter(fullText: string) {
    for (let index = 0; index < fullText.length; index += 1) {
      setStreamingText(fullText.slice(0, index + 1));
      await new Promise((resolve) => setTimeout(resolve, 10));
    }
  }

  async function typewriterResultLine(line: string, delayMs = 8) {
    setIsStreaming(true);
    setResultLogs((prev) => [...prev, ""]);
    for (let index = 0; index < line.length; index += 1) {
      const current = line.slice(0, index + 1);
      setResultLogs((prev) => {
        const next = [...prev];
        next[next.length - 1] = current;
        return next;
      });
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
    setIsStreaming(false);
  }

  async function generateFinalVerdict(conflicts: string[], selectedCards: InboxCard[] = []) {
    while (silentRecalcInFlightRef.current) {
      await new Promise((r) => setTimeout(r, 25));
    }
    verdictRecalcBarrierRef.current = true;
    try {
      try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), VERDICT_TIMEOUT_MS);
      const selectedPayload = selectedCards.map((card) => ({
        id: card.id,
        title: card.title,
        cardType: card.cardType || "conflict",
        displayText: card.displayText || card.conflictDetail || card.title,
      }));

      const absNodesFromAxes = Object.fromEntries(
        Object.entries(deityEnergyAxes || {}).map(([name, axis]) => [
          name,
          Number((axis && typeof axis === "object" ? axis.absolute_energy : 0) || 0),
        ]),
      );
      const absNodesFromScores = Object.fromEntries(
        Object.entries(deityScores || {}).map(([name, score]) => [name, Number(score || 0)]),
      );
      const absNodes = Object.keys(absNodesFromAxes).length > 0 ? absNodesFromAxes : absNodesFromScores;

      const response = await fetch(`${API_BASE}/api/v1/final-verdict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          metadata: metadata || {},
          physics_tensor: {
            abs_nodes: absNodes,
            deity_scores: deityScores,
            deity_energy_axes: deityEnergyAxes,
            deity_components: deityComponents,
            deity_trace_details: deityTraceDetails,
            audit_log: physicsAudit || {},
            top_anomaly: llmDiagnosticData?.top_anomaly || "",
            causal_reasoning: llmDiagnosticData?.causal_reasoning || "",
            tuning_suggestions: llmDiagnosticData?.tuning_suggestions || [],
            timeline: timeline || {},
            conflict_list: conflicts || [],
            fire_energy_after_conflict: calculateFireEnergyAfterConflicts(metadata?.pillars, conflicts),
            meta: {
              enabled_plugins: [
                ...(pluginSwitches.blindSchool ? ["classical.blind_school.v1"] : []),
                ...(pluginSwitches.wangshuai ? ["classical.wangshuai.v1"] : []),
                ...(pluginSwitches.wealthRisk ? ["modern.wealth_risk.v1"] : []),
              ],
              blind_school_features: buildBlindSchoolFeaturesPayload(pluginSwitches),
            },
          },
          selected_cards: selectedPayload,
          consensus_history: consensusHistory,
          previous_verdict: finalVerdictBody || lastConclusionText || "",
          previous_logical_evidence: finalLogicalEvidence,
          consultation_id: consultationId ?? undefined,
          clear_previous_verdict: true,
          force_clear_cache: true,
          enabled_plugins: [
            ...(pluginSwitches.blindSchool ? ["classical.blind_school.v1"] : []),
            ...(pluginSwitches.wangshuai ? ["classical.wangshuai.v1"] : []),
            ...(pluginSwitches.wealthRisk ? ["modern.wealth_risk.v1"] : []),
          ],
          plugin_weights: {
            "classical.blind_school.v1": Number(pluginWeights.blindSchool || 0),
            "classical.wangshuai.v1": Number(pluginWeights.wangshuai || 0),
          },
          lang,
        }),
      });
      clearTimeout(timer);

      const data = await response.json();
      if (response.ok && data?.verdict_body) {
        return {
          body: String(data.verdict_body),
          changeLog: {
            physics_diff: Array.isArray(data?.change_log?.physics_diff) ? data.change_log.physics_diff.map((item: unknown) => String(item)) : [],
            consensus_diff: Array.isArray(data?.change_log?.consensus_diff) ? data.change_log.consensus_diff.map((item: unknown) => String(item)) : [],
            text_diff_hint: String(data?.change_log?.text_diff_hint || ""),
          },
          logicalEvidence: Array.isArray(data.logical_evidence) ? data.logical_evidence.map((item: unknown) => String(item)) : [],
          versionId: String(data.version_id || ""),
          workVector: (data?.work_vector && typeof data.work_vector === "object") ? data.work_vector as Record<string, unknown> : {},
          topologyGraphV1: (data?.topology_graph_v1 && typeof data.topology_graph_v1 === "object")
            ? data.topology_graph_v1 as Record<string, unknown>
            : {},
          structureCandidatesV0: (data?.structure_candidates_v0 && typeof data.structure_candidates_v0 === "object")
            ? data.structure_candidates_v0 as Record<string, unknown>
            : {},
          structureFinalDecisionV0: (data?.structure_final_decision_v0 && typeof data.structure_final_decision_v0 === "object")
            ? data.structure_final_decision_v0 as Record<string, unknown>
            : {},
          auditLog: (data?.audit_log && typeof data.audit_log === "object") ? data.audit_log as Record<string, unknown> : {},
          confirmedDecisions: Array.isArray(data?.confirmed_decisions)
            ? data.confirmed_decisions
              .filter((item: unknown) => item && typeof item === "object")
              .map((item: unknown) => {
                const obj = item as Record<string, unknown>;
                return {
                  id: String(obj.id || ""),
                  label: String(obj.label || ""),
                  is_confirmed: Boolean(obj.is_confirmed),
                  confirmed_at: typeof obj.confirmed_at === "string" ? obj.confirmed_at : undefined,
                };
              })
              .filter((item: ConfirmedDecisionItem) => item.id)
            : [],
        };
      }
      setResultLogs((prev) => [
        ...prev,
        `⚠️ 终判接口回退：status=${response.status} detail=${String(data?.detail || "unknown")}`,
      ]);
    } catch (error) {
      // Fall through to the conservative local fallback below.
      const hint = error instanceof Error ? error.message : "unknown";
      setResultLogs((prev) => [...prev, `⚠️ 终判接口异常：${hint}；已进入保底断言。`]);
    }

    return buildFallbackVerdict(conflicts);
      } finally {
        verdictRecalcBarrierRef.current = false;
        bumpSyncBarrierSeq();
        if (silentRecalcDeferredRef.current) {
          silentRecalcDeferredRef.current = false;
          void reCalculateAbsRef.current();
        }
      }
  }

  async function applyPhysicsSqlPatch(sqlPatch: string): Promise<{ ok: boolean; error?: string }> {
    if (!sqlPatch.trim()) {
      return { ok: false, error: "缺少可执行 SQL 补丁" };
    }

    const response = await fetch(`${API_BASE}/api/admin/apply-physics-sql`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...adminHeaders },
      body: JSON.stringify({ sql_patch: sqlPatch, auto_refresh: true }),
    });
    const data = await response.json().catch(() => ({}));

    if (!response.ok || !data?.ok) {
      const maybeAuthHint = response.status === 401
        ? "（请检查 NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN / QIAZHI_ADMIN_TOKEN 配置）"
        : "";
      return { ok: false, error: `${String(data?.detail ?? "apply physics sql failed")}${maybeAuthHint}` };
    }

    setResultLogs((prev) => [
      ...prev,
      `🛠️ 已应用参数建议：${data?.updated?.param_key ?? "unknown"} -> ${data?.updated?.new_value ?? "?"}`,
    ]);
    return { ok: true };
  }

  function addAuditorProposalToInbox(proposal: LogicProposal) {
    const card = createAuditorProposalCard(proposal);
    if (!card) return;

    setAuditorProposalCards((prev) => {
      const alreadyAdded = prev.some((item) => item.proposal?.param_key === proposal.param_key);
      return alreadyAdded ? prev : [card, ...prev];
    });
  }

  function openLogicDrawer(payload: { title: string; focus: string; details: string[]; deityTrace?: Record<string, unknown> }) {
    setLogicDrawerTitle(payload.title);
    setLogicDrawerFocus(payload.focus);
    setLogicDrawerDetails(payload.details);
    setLogicDrawerTrace(payload.deityTrace || null);
    setLogicDrawerOpen(true);
  }

  function openLogicDrawerByDeity(deity: string) {
    const trace = deityTraceDetails?.[deity] as Record<string, unknown> | undefined;
    openLogicDrawer({
      title: `${deity} 演算路径`,
      focus: deity,
      details: [`${deity}: ${Number(deityScores[deity] ?? 0).toFixed(2)}%`, "来自 Result Summary 点击下钻。"],
      deityTrace: trace,
    });
  }

  function onEvidenceItemClick(evidence: string) {
    const text = String(evidence || "");
    const deityNames = ["比肩", "劫财", "食神", "伤官", "正财", "偏财", "正官", "七杀", "正印", "偏印"];
    const hit = deityNames.find((name) => text.includes(name));
    if (hit) {
      openLogicDrawerByDeity(hit);
      return;
    }

    openLogicDrawer({
      title: "证据条目下钻",
      focus: "Logical Evidence",
      details: [text, "该证据暂未映射到特定十神，已展示原始条目。"],
    });
  }

  function showVerdictHistory() {
    if (finalVerdictHistory.length === 0) return;

    const lines = finalVerdictHistory
      .map((item, index) => `#${index + 1} ${item.versionId} @ ${new Date(item.createdAt).toLocaleString()}`)
      .concat(["---"])
      .concat(
        finalVerdictHistory.flatMap((item) => [
          `【${item.versionId}】`,
          item.body,
          ...(item.changeLog.physics_diff || []).map((change) => `[物理] ${change}`),
          ...(item.changeLog.consensus_diff || []).map((change) => `[共识] ${change}`),
          ...(item.changeLog.text_diff_hint ? [`[判词] ${item.changeLog.text_diff_hint}`] : []),
          ...(item.logicalEvidence || []).slice(0, 6).map((evidence) => `[证据] ${evidence}`),
          "",
        ]),
      );

    openLogicDrawer({
      title: "Result Summary 版本回放",
      focus: "Final Verdict History",
      details: lines,
    });
  }

  function appendFinalVerdictAuditItem(versionId: string, auditLog: Record<string, unknown> | undefined, timestamp: string) {
    setAuditItems((prev) => [
      ...prev,
      {
        id: `auditor-final-${Date.now()}`,
        step: "05",
        role: "Auditor",
        action: "终判审计链路已生成",
        timestamp,
        payload: {
          model_name: llmModelName,
          final_verdict_version_id: versionId || "--",
          ...(auditLog || {}),
        },
      },
    ]);
  }

  async function onSeedSubmit(payload: SeedPayload) {
    setLastSeedPayload(payload);
    persistLastSeedToStore(payload);
    setBusy(true);
    setIsStreaming(true);
    setAutoConvertedParamKey(null);
    setStreamingText("");
    setAuditItems([]);
    setResultLogs([]);
    setDeityScores({});
    setDeityEnergyAxes({});
    setDeityComponents({});
    setDeityTraceDetails({});
    setHoveredDeity(undefined);
    setPhysicsAudit(null);
    setPhysicsConfidence(null);
    setPhysicsEvidence([]);
    setShowPhysicsAudit(false);
    setAuditorProposalCards([]);
    setResolvedCardIds([]);
    setPhysicsParams({});
    setGlobalEntropy(null);
    setConfirmedConflicts([]);
    setFirstPromptText("");
    setTimeline(null);
    setLlmDiagnosticData(null);
    setFinalVerdictBody("");
    setFinalVerdictChangeLog({});
    setFinalVerdictVersionId("");
    setFinalLogicalEvidence([]);
    setFinalWorkVector(null);
    setFinalTopologyGraphV1(null);
    setFinalStructureCandidatesV0(null);
    setFinalStructureFinalDecisionV0(null);
    setFinalVerdictHistory([]);
    setStressTestResult(null);
    setGenderComparisonResult(null);
    setConsensusHistory([]);

    const latestHealth = await refreshHealth();

    try {
      let currentSessionId = consultationId;
      setStreamingText(t("第一波：物理排盘中…"));
      setAuditItems([
        {
          id: `arbiter-submit-${Date.now()}`,
          step: "01",
          role: "Arbiter",
          action: `提交生辰 ${payload.date} ${payload.time}，请求物理建模。`,
          timestamp: new Date().toISOString(),
          payload,
        },
      ]);

      try {
        const consultationResponse = await fetch(`${API_BASE}/api/consultations`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            subject_ref: null,
            input_meta: { ...payload, source: "seed_input" },
          }),
        });
        if (consultationResponse.ok) {
          const consultationData = await consultationResponse.json();
          setConsultationId(consultationData.id as number);
          currentSessionId = consultationData.id as number;
        }
      } catch {
        // Consultation logging should not block the main inference flow.
      }

      setStreamingText(t("第二波：特征扫描中…"));
      const response = await fetch(`${API_BASE}/api/v1/analyze-seed`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          date: payload.date,
          time: payload.time,
          calendar: payload.calendar,
          gender: payload.gender,
          lang,
          latitude: 31.2304,
          longitude: 121.4737,
          session_id: currentSessionId ?? undefined,
          physics_config: labConfig,
          enabled_plugins: [
            ...(pluginSwitches.blindSchool ? ["classical.blind_school.v1"] : []),
            ...(pluginSwitches.wangshuai ? ["classical.wangshuai.v1"] : []),
            ...(pluginSwitches.wealthRisk ? ["modern.wealth_risk.v1"] : []),
          ],
          blind_school_features: buildBlindSchoolFeaturesPayload(pluginSwitches),
        }),
      });

      if (!response.ok) throw new Error(await response.text());
      const data = await response.json();
      markActiveSession(currentSessionId ?? consultationId ?? null);
      setMetadata(data.metadata as BaziMetadata);
      setTimeline((data.timeline ?? null) as TimelineSnapshot | null);

      if (data.physics_tensor?.normalized) {
        const normalized = data.physics_tensor.normalized as Record<string, number>;
        setResultLogs((prev) => [
          ...prev,
          `⚙️ 能量矩阵(木火土金水)：${normalized.wood ?? 0}/${normalized.fire ?? 0}/${normalized.earth ?? 0}/${normalized.metal ?? 0}/${normalized.water ?? 0}`,
        ]);
      }
      if (data.physics_tensor?.deity_scores) {
        setDeityScores(data.physics_tensor.deity_scores as Record<string, number>);
      }
      if (data.physics_tensor?.deity_energy_axes) {
        setDeityEnergyAxes(data.physics_tensor.deity_energy_axes as Record<string, DeityEnergyAxis>);
      }
      if (data.physics_tensor?.deity_components) {
        setDeityComponents(data.physics_tensor.deity_components as Record<string, DeityComponent>);
      }
      if (data.physics_tensor?.deity_trace_details) {
        setDeityTraceDetails(data.physics_tensor.deity_trace_details as Record<string, Record<string, unknown>>);
      } else if (data.physics_tensor?.meta?.deity_trace_details) {
        setDeityTraceDetails(data.physics_tensor.meta.deity_trace_details as Record<string, Record<string, unknown>>);
      } else {
        setDeityTraceDetails({});
      }
      if (data.physics_tensor?.audit_log) {
        setPhysicsAudit(data.physics_tensor.audit_log as Record<string, unknown>);
      }
      if (typeof data.physics_tensor?.confidence === "number") {
        setPhysicsConfidence(data.physics_tensor.confidence);
      } else {
        setPhysicsConfidence(null);
      }
      if (Array.isArray(data.physics_tensor?.evidence)) {
        setPhysicsEvidence(data.physics_tensor.evidence.map((item: unknown) => String(item)));
      } else {
        setPhysicsEvidence([]);
      }
      if (data.physics_tensor?.meta?.params) {
        setPhysicsParams(data.physics_tensor.meta.params as Record<string, number>);
      }
      const geRaw = (data.physics_tensor?.meta as { global_entropy?: unknown } | undefined)?.global_entropy;
      setGlobalEntropy(typeof geRaw === "number" && Number.isFinite(geRaw) ? geRaw : null);
      const mangpaiChips = (data.physics_tensor?.meta as { mangpai_chip_logs?: unknown } | undefined)?.mangpai_chip_logs;
      if (Array.isArray(mangpaiChips)) {
        for (const line of mangpaiChips) {
          const s = String(line || "").trim();
          if (s) appendSystemAuditLog(s);
        }
      }
      const currentMetric = extractMetricSnapshotFromPhysics((data.physics_tensor as Record<string, unknown> | undefined) || null);
      const diff = updateLogicDiff(currentMetric, confirmedDecisionIds.length === 0 || !baselineMetrics);
      const absDelta = diff.abs_delta;
      if (typeof absDelta === "number" && absDelta > 100) {
        const source = confirmedDecisionIds.join(",") || "seed_submit";
        setResultLogs((prev) => [
          ...prev,
          `[CRITICAL] [ENERGY_OVERLOAD] abs_delta: ${absDelta.toFixed(2)} | Source: ${source}`,
        ]);
      }

      try {
        if (data.physics_tensor) {
          persistSnapshot({
            physics_tensor: data.physics_tensor as Record<string, unknown>,
            metadata: data.metadata as Record<string, unknown>,
            timeline: (data.timeline ?? null) as Record<string, unknown> | null,
            audit_summary: data.audit_summary,
            consultationIdOverride: currentSessionId ?? consultationId ?? null,
            healthOverride: latestHealth,
          });
        }
      } catch {
        // ignore quota / privacy mode
      }

      if (data.metadata && data.physics_tensor) {
        try {
          const auditResponse = await fetch(`${API_BASE}/api/v1/audit-physics-with-llm`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              metadata: data.metadata,
              physics_tensor: data.physics_tensor,
              lang,
              consensus_history: consensusHistory,
              session_id: currentSessionId ?? undefined,
            }),
          });
          const auditData = await auditResponse.json();
          if (!auditResponse.ok) {
            throw new Error(String(auditData?.detail ?? "audit-physics-with-llm failed"));
          }

          const logicProposal = auditData?.logic_proposal as LogicProposal | undefined;
          if (logicProposal?.param_key) {
            // 新策略：审计员提案默认并入 Decision Inbox，无需手动确认「加入」。
            setAutoConvertedParamKey(logicProposal.param_key);
            addAuditorProposalToInbox(logicProposal);
          } else {
            setAutoConvertedParamKey(null);
          }

          setLlmDiagnosticData({
            diagnosis: auditData?.diagnosis,
            alignment_score: auditData?.alignment_score,
            top_anomaly: auditData?.top_anomaly,
            causal_reasoning: auditData?.causal_reasoning,
            tuning_suggestions: auditData?.tuning_suggestions,
            sql_patch: auditData?.sql_patch,
            refresh_hint: auditData?.refresh_hint,
            logic_proposal: auditData?.logic_proposal,
            structured_hit: auditData?.structured_hit,
            repair_mode: auditData?.repair_mode,
          });
          try {
            if (data.physics_tensor) {
              persistSnapshot({
                physics_tensor: data.physics_tensor as Record<string, unknown>,
                metadata: data.metadata as Record<string, unknown>,
                timeline: (data.timeline ?? null) as Record<string, unknown> | null,
                llm_prompt: data.llm_prompt || "",
                audit_summary: data.audit_summary,
                consultationIdOverride: currentSessionId ?? consultationId ?? null,
                healthOverride: latestHealth,
                auditorBriefingOverride: {
                  alignment_score: auditData?.alignment_score,
                  structured_hit: auditData?.structured_hit,
                  repair_mode: auditData?.repair_mode,
                  top_anomaly: auditData?.top_anomaly,
                  causal_reasoning: auditData?.causal_reasoning,
                  tuning_suggestions: auditData?.tuning_suggestions,
                  logic_proposal: auditData?.logic_proposal,
                  auto_joined_decision_box: Boolean(logicProposal?.param_key),
                },
              });
            }
          } catch {
            // ignore quota / privacy mode
          }
        } catch {
          // Keep the main board usable even if the auditor call fails.
        }
      }

      const incoming = (data.audit_summary ?? []) as Array<{
        step?: string;
        role: "Arbiter" | "Core" | "Auditor";
        action: string;
        timestamp: string;
        payload?: unknown;
      }>;
      if (incoming.length >= 3) {
        const mapped = incoming.map((item, index) => ({
          id: `${item.role}-${item.timestamp}-${index}`,
          step: item.step,
          role: item.role,
          action: item.action,
          timestamp: item.timestamp,
          payload: item.role === "Auditor"
            ? {
                ...(item.payload && typeof item.payload === "object" ? (item.payload as Record<string, unknown>) : {}),
                model_name: String(
                  (item.payload && typeof item.payload === "object" && "model_name" in item.payload)
                    ? (item.payload as { model_name?: string }).model_name || llmModelName
                    : llmModelName,
                ),
                param_version_id: String(data?.physics_tensor?.audit_log?.param_version_id || "--"),
                physics_confidence: typeof data?.physics_tensor?.confidence === "number"
                  ? data.physics_tensor.confidence
                  : null,
                physics_evidence: Array.isArray(data?.physics_tensor?.evidence)
                  ? data.physics_tensor.evidence.map((item: unknown) => String(item))
                  : [],
              }
            : item.payload,
        })) as AuditItem[];

        setAuditItems([mapped[0]]);
        await new Promise((resolve) => setTimeout(resolve, 220));
        setAuditItems([mapped[0], mapped[1]]);
        await new Promise((resolve) => setTimeout(resolve, 220));
        setAuditItems([mapped[0], mapped[1], mapped[2]]);
      }

      if (data.physics_tensor) {
        scheduleInteractionHubPersist();
      }

      setStreamingText(`${t("扫描完毕，发现")} ${(data.metadata?.conflict_matrix?.points ?? []).length} ${t("处冲合特征，正在生成首条判词…")}`);
      setFirstPromptText(data.llm_prompt || "");
      await typewriter(data.llm_prompt || "");
    } catch (error) {
      await typewriter(`${t("连接后端失败：")}${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setBusy(false);
      setIsStreaming(false);
    }
  }

  const lastCausalRevertHandledRef = useRef(0);
  const onSeedSubmitRef = useRef(onSeedSubmit);
  onSeedSubmitRef.current = onSeedSubmit;

  const setLang = useCallback(
    (next: Lang) => {
      if (next === langRef.current) return;
      langRef.current = next;
      setLangState(next);
      setUiLang(next);
      queueMicrotask(() => {
        const p = lastSeedPayloadRef.current;
        if (!p || !metadataRef.current) return;
        if (busyRef.current || isStreamingRef.current || isExecutingRef.current) return;
        void onSeedSubmitRef.current(p);
      });
    },
    [setUiLang],
  );

  useEffect(() => {
    if (isSnapshotRestoringRef.current) return;
    if (labState.causalRevertNonce === 0) {
      lastCausalRevertHandledRef.current = 0;
      return;
    }
    const n = labState.causalRevertNonce;
    if (n === lastCausalRevertHandledRef.current) return;
    lastCausalRevertHandledRef.current = n;
    const payload = labState.lastSeedPayload;
    if (!payload) return;
    void onSeedSubmitRef.current(payload);
  }, [labState.causalRevertNonce, labState.lastSeedPayload]);

  async function onExecuteDecision(selected: InboxCard[]) {
    setIsExecuting(true);
    try {
      const selectedCards = selected as InboxCard[];
      const now = new Date().toISOString();
      const conflicts = selectedCards.map((card) => card.conflictDetail).filter(Boolean) as string[];
      const proposals = selectedCards.filter((card) => card.cardType === "auditor-proposal" && card.proposal?.sql_patch);
      if (proposals.length > 0) {
        setConsensusHistory((prev) => [
          ...prev,
          ...proposals
            .map((proposalCard) => ({
              decision_key: String(proposalCard.proposal?.param_key || ""),
              confirmed_value: typeof proposalCard.proposal?.suggested_value === "number" ? proposalCard.proposal.suggested_value : undefined,
              reasoning: String(proposalCard.proposal?.reason || proposalCard.proposal?.expected_impact || ""),
            }))
            .filter((item) => item.decision_key),
        ]);
      }

      if (conflicts.length === 0 && proposals.length === 0) {
        await typewriterResultLine("⚪ 未选择任何冲合项/提案，本轮不触发终极判词。");
        return;
      }

      setConfirmedConflicts(conflicts);
      setResolvedCardIds((prev) => [...new Set([...prev, ...selectedCards.map((card) => card.id)])]);

      setStreamingText(
        proposals.length > 0 && conflicts.length === 0
          ? `${t("已确认")} 审计员提案，正在执行参数校准…`
          : `${t("已确认")} ${conflicts.join("、")}${t("，正在执行全局裁决…")}`,
      );

      if (consultationId) {
        try {
          await fetch(`${API_BASE}/api/decision-steps`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              consultation_id: consultationId,
              step_type: "execute-decision",
              raw_data: { metadata, selected_conflicts: conflicts },
              human_choice: {
                action: "execute",
                selected_conflicts: conflicts,
                selected_proposals: proposals.map((proposalCard) => proposalCard.proposal),
              },
            }),
          });
        } catch {
          // Local optimistic flow is enough when the DB is unavailable.
        }
      }

      for (const proposalCard of proposals) {
        const result = await applyPhysicsSqlPatch(proposalCard.proposal?.sql_patch || "");
        if (!result.ok) {
          await typewriterResultLine(`❌ 参数建议执行失败：${result.error}`);
          setStreamingText(`参数校准失败：${result.error}`);
          return;
        }
      }

      if (proposals.length > 0 && lastSeedPayload) {
        await typewriterResultLine("🧬 参数校准已执行，系统正在按新物理常数重算…", 18);
        setStreamingText("系统逻辑已接收裁决，正在自动重算...");
        await onSeedSubmit(lastSeedPayload);
        setAuditorProposalCards([]);
        setConfirmedDecisionIds([]);
        setSelectionResetToken((value) => value + 1);

        const verdict = await generateFinalVerdict(conflicts, selectedCards);
        if ((verdict.body || "").trim()) {
          await typewriterResultLine(`${t("✅ 终极判词：")}${verdict.body}`, 18);
          setStreamingText(t("全局裁决完成，终极判词已生成。"));
          setConclusionVersion((value) => value + 1);
          setSummaryChanged(Boolean(lastConclusionText && lastConclusionText !== verdict.body));
          setLastConclusionText(verdict.body);
          setFinalVerdictBody(verdict.body);
          setFinalVerdictChangeLog(verdict.changeLog || {});
          setFinalLogicalEvidence(verdict.logicalEvidence || []);
          setFinalWorkVector((verdict.workVector as Record<string, unknown>) || null);
          setFinalTopologyGraphV1((verdict.topologyGraphV1 as Record<string, unknown>) || null);
          setFinalStructureCandidatesV0((verdict.structureCandidatesV0 as Record<string, unknown>) || null);
          setFinalStructureFinalDecisionV0((verdict.structureFinalDecisionV0 as Record<string, unknown>) || null);
          setFinalVerdictVersionId(verdict.versionId || "");
          setConfirmedDecisions(verdict.confirmedDecisions || []);
          setFinalVerdictHistory((prev) => [
            ...prev,
            {
              versionId: verdict.versionId || `v1.${conclusionVersion + 1}`,
              body: verdict.body,
              changeLog: verdict.changeLog || {},
              logicalEvidence: verdict.logicalEvidence || [],
              createdAt: new Date().toISOString(),
            },
          ]);
          appendFinalVerdictAuditItem(verdict.versionId || `v1.${conclusionVersion + 1}`, verdict.auditLog, new Date().toISOString());
        }

        setAuditItems((prev) => [
          ...prev,
          {
            id: `arbiter-step-${Date.now()}`,
            step: "04",
            role: "Arbiter",
            action: `执行审计员提案参数校准（共确认 ${proposals.length} 项）`,
            timestamp: now,
            payload: { selected_proposals: proposals.map((proposalCard) => proposalCard.proposal) },
          },
        ]);
        scheduleInteractionHubPersist();
        return;
      }

      if (conflicts.length > 0) {
        const verdict = await generateFinalVerdict(conflicts, selectedCards);
        const safeVerdict = (verdict.body || "").trim()
          ? verdict.body
          : (lang === "KO" ? t("[KO] 结果提取失败。") : "结果提取失败，请稍后重试。");
        await typewriterResultLine(`${t("✅ 终极判词：")}${safeVerdict}`, 18);
        setStreamingText(t("全局裁决完成，终极判词已生成。"));
        setConclusionVersion((value) => value + 1);
        setSummaryChanged(Boolean(lastConclusionText && lastConclusionText !== safeVerdict));
        setLastConclusionText(safeVerdict);
        setFinalVerdictBody(safeVerdict);
        setFinalVerdictChangeLog(verdict.changeLog || {});
        setFinalLogicalEvidence(verdict.logicalEvidence || []);
        setFinalWorkVector((verdict.workVector as Record<string, unknown>) || null);
        setFinalTopologyGraphV1((verdict.topologyGraphV1 as Record<string, unknown>) || null);
        setFinalStructureCandidatesV0((verdict.structureCandidatesV0 as Record<string, unknown>) || null);
        setFinalStructureFinalDecisionV0((verdict.structureFinalDecisionV0 as Record<string, unknown>) || null);
        setFinalVerdictVersionId(verdict.versionId || "");
        setConfirmedDecisions(verdict.confirmedDecisions || []);
        setFinalVerdictHistory((prev) => [
          ...prev,
          {
            versionId: verdict.versionId || `v1.${conclusionVersion + 1}`,
            body: safeVerdict,
            changeLog: verdict.changeLog || {},
            logicalEvidence: verdict.logicalEvidence || [],
            createdAt: new Date().toISOString(),
          },
        ]);
        appendFinalVerdictAuditItem(verdict.versionId || `v1.${conclusionVersion + 1}`, verdict.auditLog, new Date().toISOString());
      }

      setAuditorProposalCards((prev) => prev.filter((card) => !selectedCards.some((selectedCard) => selectedCard.id === card.id)));
      setConfirmedDecisionIds([]);
      setSelectionResetToken((value) => value + 1);
      setAuditItems((prev) => [
        ...prev,
        {
          id: `arbiter-step-${Date.now()}`,
          step: "04",
          role: "Arbiter",
          action: `执行全局裁决（共确认 ${conflicts.length} 项）`,
          timestamp: now,
          payload: { selected_conflicts: conflicts },
        },
      ]);
      scheduleInteractionHubPersist();
    } finally {
      setIsExecuting(false);
    }
  }

  async function applyCurrentSqlPatch() {
    const result = await applyPhysicsSqlPatch(llmDiagnosticData?.sql_patch || "");
    if (!result.ok) {
      await typewriterResultLine(`❌ 参数建议执行失败：${result.error}`);
      setStreamingText(`参数校准失败：${result.error}`);
    }
  }

  async function applyLabConfigAndRecalculate() {
    if (!lastSeedPayload) return;
    setResultLogs((prev) => [
      ...prev,
      `🧪 实验参数已应用：luck=${labConfig.WEIGHT_LUCK}, year=${labConfig.WEIGHT_YEAR}, climate=${labConfig.CLIMATE_INTENSITY}`,
    ]);
    await onSeedSubmit(lastSeedPayload);
  }

  async function runStressTest(scenario: string) {
    if (!metadata) return;
    const parts = String(scenario || "").split(/[,\s/]+/).filter(Boolean);
    const yearPillar = parts[0] || "";
    const luckPillar = parts[1] || "";
    const response = await fetch(`${API_BASE}/api/v1/analyze/stress-test`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        metadata,
        gender: ((metadata as Record<string, unknown>)?.gender as string) || "male",
        physics_config: labConfig,
        baseline_structure_final_decision: finalStructureFinalDecisionV0 || {},
        year_pillar: yearPillar,
        luck_pillar: luckPillar,
        enabled_plugins: [
          ...(pluginSwitches.blindSchool ? ["classical.blind_school.v1"] : []),
          ...(pluginSwitches.wangshuai ? ["classical.wangshuai.v1"] : []),
          ...(pluginSwitches.wealthRisk ? ["modern.wealth_risk.v1"] : []),
        ],
        lang,
      }),
    });
    const data = await response.json().catch(() => ({}));
    if (response.ok && data?.ok) {
      setStressTestResult(data as Record<string, unknown>);
      setResultLogs((prev) => [
        ...prev,
        `🧪 压力测试 ${yearPillar}${luckPillar ? `/${luckPillar}` : ""} -> rollback=${Boolean(data.rollback_triggered)} ΔAbs=${Number(data.delta_abs || 0).toFixed(2)}`,
      ]);
    } else {
      setResultLogs((prev) => [...prev, `❌ 压力测试失败：${String(data?.detail || "unknown")}`]);
    }
  }

  async function runGenderComparison() {
    if (!lastSeedPayload) return;
    const base = {
      date: lastSeedPayload.date,
      time: lastSeedPayload.time,
      calendar: lastSeedPayload.calendar,
      lang,
      latitude: 31.2304,
      longitude: 121.4737,
      physics_config: labConfig,
      enabled_plugins: [
        ...(pluginSwitches.blindSchool ? ["classical.blind_school.v1"] : []),
        ...(pluginSwitches.wangshuai ? ["classical.wangshuai.v1"] : []),
        ...(pluginSwitches.wealthRisk ? ["modern.wealth_risk.v1"] : []),
      ],
      blind_school_features: buildBlindSchoolFeaturesPayload(pluginSwitches),
    };
    const [maleResp, femaleResp] = await Promise.all([
      fetch(`${API_BASE}/api/v1/analyze-seed`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...base, gender: "male" }),
      }),
      fetch(`${API_BASE}/api/v1/analyze-seed`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ...base, gender: "female" }),
      }),
    ]);
    const maleData = await maleResp.json().catch(() => ({}));
    const femaleData = await femaleResp.json().catch(() => ({}));
    const maleAxes = (maleData?.physics_tensor?.deity_energy_axes || {}) as Record<string, { absolute_energy?: number }>;
    const femaleAxes = (femaleData?.physics_tensor?.deity_energy_axes || {}) as Record<string, { absolute_energy?: number }>;
    const malePeakAbs = Math.max(0, ...Object.values(maleAxes).map((v) => Number(v?.absolute_energy || 0)));
    const femalePeakAbs = Math.max(0, ...Object.values(femaleAxes).map((v) => Number(v?.absolute_energy || 0)));

    const [maleVerdictResp, femaleVerdictResp] = await Promise.all([
      fetch(`${API_BASE}/api/v1/final-verdict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          metadata: maleData?.metadata || {},
          physics_tensor: maleData?.physics_tensor || {},
          selected_cards: [],
          consensus_history: [],
          enabled_plugins: [
            ...(pluginSwitches.blindSchool ? ["classical.blind_school.v1"] : []),
            ...(pluginSwitches.wangshuai ? ["classical.wangshuai.v1"] : []),
            ...(pluginSwitches.wealthRisk ? ["modern.wealth_risk.v1"] : []),
          ],
          plugin_weights: {
            "classical.blind_school.v1": Number(pluginWeights.blindSchool || 0),
            "classical.wangshuai.v1": Number(pluginWeights.wangshuai || 0),
          },
          clear_previous_verdict: true,
          force_clear_cache: true,
          lang,
        }),
      }),
      fetch(`${API_BASE}/api/v1/final-verdict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          metadata: femaleData?.metadata || {},
          physics_tensor: femaleData?.physics_tensor || {},
          selected_cards: [],
          consensus_history: [],
          enabled_plugins: [
            ...(pluginSwitches.blindSchool ? ["classical.blind_school.v1"] : []),
            ...(pluginSwitches.wangshuai ? ["classical.wangshuai.v1"] : []),
            ...(pluginSwitches.wealthRisk ? ["modern.wealth_risk.v1"] : []),
          ],
          plugin_weights: {
            "classical.blind_school.v1": Number(pluginWeights.blindSchool || 0),
            "classical.wangshuai.v1": Number(pluginWeights.wangshuai || 0),
          },
          clear_previous_verdict: true,
          force_clear_cache: true,
          lang,
        }),
      }),
    ]);
    const maleVerdict = await maleVerdictResp.json().catch(() => ({}));
    const femaleVerdict = await femaleVerdictResp.json().catch(() => ({}));
    const maleWork = Number(maleVerdict?.work_vector?.work_expectation || 0);
    const femaleWork = Number(femaleVerdict?.work_vector?.work_expectation || 0);
    const toPathBreakScore = (verdict: Record<string, unknown>) => {
      const vectors = (((verdict?.work_vector as { work_vectors?: Array<Record<string, unknown>> } | undefined)?.work_vectors) || []);
      const ziwu = vectors.filter((item) => String(item?.detail || "").includes("子午冲"));
      if (ziwu.length === 0) return 0;
      const scores = ziwu.map((item) => {
        const gain = Number(item?.unlock_gain || 0);
        const risk = Number(item?.backfire_risk || 0);
        if (gain <= 0) return 1;
        return Math.max(0, Math.min(1, risk / gain));
      });
      return Math.max(...scores);
    };
    const malePathBreakScore = toPathBreakScore(maleVerdict as Record<string, unknown>);
    const femalePathBreakScore = toPathBreakScore(femaleVerdict as Record<string, unknown>);
    const totalWeight = Math.max(0.0001, Number(pluginWeights.blindSchool || 0) + Number(pluginWeights.wangshuai || 0));
    const blindRatio = Number(pluginWeights.blindSchool || 0) / totalWeight;
    const maleThemeColor = interpolateColor("#2D4F1E", "#1A1A1A", blindRatio);
    const femaleThemeColor = interpolateColor("#2D4F1E", "#1A1A1A", 1 - blindRatio);
    const summary = `若为坤造（女），当前做功净值从 ${maleWork.toFixed(2)} 变化为 ${femaleWork.toFixed(2)}；子午冲损毁度 男${Math.round(malePathBreakScore * 100)}% / 女${Math.round(femalePathBreakScore * 100)}%。`;

    setGenderComparisonResult({
      male_dayun: String(maleData?.timeline?.dayun || ""),
      female_dayun: String(femaleData?.timeline?.dayun || ""),
      male_peak_abs: malePeakAbs,
      female_peak_abs: femalePeakAbs,
      male_work_net: maleWork,
      female_work_net: femaleWork,
      male_path_break_score: malePathBreakScore,
      female_path_break_score: femalePathBreakScore,
      male_theme_color: maleThemeColor,
      female_theme_color: femaleThemeColor,
      summary,
    });
    setResultLogs((prev) => [...prev, `🧭 性别镜像对比完成：男(${maleWork.toFixed(2)}) vs 女(${femaleWork.toFixed(2)})`]);
  }

  async function rerunFinalVerdictWithWeights(selectedCards: InboxCard[] = []) {
    const selectedConflicts = selectedCards
      .map((card) => String(card.conflictDetail || "").trim())
      .filter(Boolean);
    const conflicts = selectedConflicts.length > 0 ? selectedConflicts : (confirmedConflicts || []);
    const verdict = await generateFinalVerdict(
      conflicts,
      selectedCards,
    );
    const safeVerdict = (verdict.body || "").trim() ? verdict.body : "结果提取失败，请稍后重试。";
    setFinalVerdictBody(safeVerdict);
    setFinalVerdictChangeLog(verdict.changeLog || {});
    setFinalLogicalEvidence(verdict.logicalEvidence || []);
    setFinalWorkVector((verdict.workVector as Record<string, unknown>) || null);
    setFinalTopologyGraphV1((verdict.topologyGraphV1 as Record<string, unknown>) || null);
    setFinalStructureCandidatesV0((verdict.structureCandidatesV0 as Record<string, unknown>) || null);
    setFinalStructureFinalDecisionV0((verdict.structureFinalDecisionV0 as Record<string, unknown>) || null);
    setFinalVerdictVersionId(verdict.versionId || "");
    setConfirmedDecisions(verdict.confirmedDecisions || []);
    const llmSource = verdict.versionId ? "model_pipeline" : "fallback";
    setResultLogs((prev) => [
      ...prev,
      `[LLM_AUDIT] source=${llmSource} | model=${llmModelName} | version=${verdict.versionId || "--"}`,
    ]);
    setConfirmedConflicts(conflicts);
    if (selectedCards.length > 0) {
      setResolvedCardIds((prev) => [...new Set([...prev, ...selectedCards.map((card) => card.id)])]);
    }
    setAuditItems((prev) => [
      ...prev,
      {
        id: `arbiter-semantic-${Date.now()}`,
        step: "04",
        role: "Arbiter",
        action: `执行语义重算（共确认 ${selectedCards.length} 项）`,
        timestamp: new Date().toISOString(),
        payload: {
          selected_card_ids: selectedCards.map((card) => card.id),
          selected_conflicts: conflicts,
        },
      },
    ]);
    const currentMetric: MetricSnapshot = {
      absLossTotal: typeof (verdict.workVector as { backfire_risk?: unknown } | undefined)?.backfire_risk === "number"
        ? Number((verdict.workVector as { backfire_risk?: number }).backfire_risk)
        : null,
      entropy: globalEntropy,
    };
    const diff = updateLogicDiff(currentMetric);
    const absDelta = diff.abs_delta;
    if (typeof absDelta === "number" && absDelta > 100) {
      const source = selectedCards.map((card) => card.id).join(",") || "none";
      setResultLogs((prev) => [
        ...prev,
        `[CRITICAL] [ENERGY_OVERLOAD] abs_delta: ${absDelta.toFixed(2)} | Source: ${source}`,
      ]);
    }
  }

  async function refreshVerdict(selected: InboxCard[]) {
    await rerunFinalVerdictWithWeights(selected);
  }

  async function executeDecisionAndRefresh(selected: InboxCard[]) {
    await onExecuteDecision(selected);
    await refreshVerdict(selected);
  }

  async function revokeConfirmedDecision(id: string) {
    const nextDecisions = confirmedDecisions.filter((item) => item.id !== id);
    setConfirmedDecisions(nextDecisions);
    setConfirmedDecisionIds((prev) => prev.filter((item) => item !== id));
  }

  /**
   * 实验室 store 里 mergeSnapshot 已有完整因果现场，但本 hook 内大量 useState 默认空。
   * 任意导致 StreamBoard 重挂载的情况都必须从 snapshot 灌回，否则界面像「全丢」。
   */
  useLayoutEffect(() => {
    if (metadata !== null) return;
    const snap = labState.snapshot;
    if (!snap?.metadata) return;

    isSnapshotRestoringRef.current = true;
    try {
      const rawMeta = snap.metadata as Record<string, unknown>;
      const points = (rawMeta.conflict_matrix as { points?: unknown } | undefined)?.points;
      const nextMeta: BaziMetadata = {
        version: String(rawMeta.version ?? "1"),
        pillars: (rawMeta.pillars ?? null) as BaziMetadata["pillars"],
        conflict_matrix: {
          points: Array.isArray(points) ? (points as BaziMetadata["conflict_matrix"]["points"]) : [],
        },
        flow_state: String(rawMeta.flow_state ?? "ready"),
        notes: String(rawMeta.notes ?? ""),
      };
      setMetadata(nextMeta);

      setTimeline((snap.timeline as TimelineSnapshot) ?? null);
      setFirstPromptText(String(snap.llm_prompt || ""));

      const hub = snap.interaction_hub;
      if (hub?.consultation_id != null && typeof hub.consultation_id === "number") {
        setConsultationId(hub.consultation_id);
      } else if (snap.active_session_id) {
        const n = Number(String(snap.active_session_id));
        if (Number.isFinite(n)) setConsultationId(n);
      }

      if (hub?.health) {
        setHealth({ dbOk: Boolean(hub.health.db_ok), llmOk: Boolean(hub.health.llm_ok) });
      }

      const rawItems = hub?.audit_items;
      if (Array.isArray(rawItems) && rawItems.length > 0) {
        setAuditItems(
          rawItems.map((item, idx) => ({
            id: String(item?.id ?? `audit-${idx}`),
            step: item?.step,
            role: (String(item?.role ?? "Core") as AuditRole),
            action: String(item?.action ?? item?.step ?? "—"),
            timestamp: String(item?.timestamp ?? ""),
          })),
        );
      }

      if (Array.isArray(hub?.result_logs)) {
        setResultLogs(hub.result_logs.map((x) => String(x)));
      }

      const briefing = hub?.auditor_briefing;
      if (briefing && typeof briefing === "object") {
        const b = briefing as Record<string, unknown>;
        const proposal = b.logic_proposal as LogicProposal | undefined;
        const nextDiag: LlmDiagnosticData = {
          alignment_score: typeof b.alignment_score === "number" ? b.alignment_score : undefined,
          structured_hit: typeof b.structured_hit === "boolean" ? b.structured_hit : undefined,
          repair_mode: b.repair_mode != null ? String(b.repair_mode) : undefined,
          top_anomaly: b.top_anomaly != null ? String(b.top_anomaly) : undefined,
          causal_reasoning: b.causal_reasoning != null ? String(b.causal_reasoning) : undefined,
          tuning_suggestions: Array.isArray(b.tuning_suggestions) ? b.tuning_suggestions.map((x) => String(x)) : undefined,
          logic_proposal: proposal,
          sql_patch: b.sql_patch != null ? String(b.sql_patch) : undefined,
        };
        setLlmDiagnosticData(nextDiag);
      }

      const tensor = snap.physics_tensor as Record<string, unknown> | undefined;
      if (tensor && typeof tensor === "object") {
        if (tensor.deity_scores && typeof tensor.deity_scores === "object") {
          setDeityScores(tensor.deity_scores as Record<string, number>);
        }
        if (tensor.deity_energy_axes && typeof tensor.deity_energy_axes === "object") {
          setDeityEnergyAxes(tensor.deity_energy_axes as Record<string, DeityEnergyAxis>);
        }
        if (tensor.deity_components && typeof tensor.deity_components === "object") {
          setDeityComponents(tensor.deity_components as Record<string, DeityComponent>);
        }
        if (tensor.deity_trace_details && typeof tensor.deity_trace_details === "object") {
          setDeityTraceDetails(tensor.deity_trace_details as Record<string, Record<string, unknown>>);
        }
        const pMeta = (tensor.meta || {}) as Record<string, unknown>;
        if (pMeta.deity_trace_details && typeof pMeta.deity_trace_details === "object" && !tensor.deity_trace_details) {
          setDeityTraceDetails(pMeta.deity_trace_details as Record<string, Record<string, unknown>>);
        }
        if (tensor.audit_log && typeof tensor.audit_log === "object") {
          setPhysicsAudit(tensor.audit_log as Record<string, unknown>);
        }
        setPhysicsConfidence(typeof tensor.confidence === "number" ? tensor.confidence : null);
        if (Array.isArray(tensor.evidence)) {
          setPhysicsEvidence(tensor.evidence.map((x) => String(x)));
        } else {
          setPhysicsEvidence([]);
        }
        if (pMeta.params && typeof pMeta.params === "object") {
          setPhysicsParams(pMeta.params as Record<string, number>);
        }
        const ge = pMeta.global_entropy;
        setGlobalEntropy(typeof ge === "number" && Number.isFinite(ge) ? ge : null);
      }

      const fv = snap.final_verdict;
      if (fv && typeof fv === "object") {
        setFinalVerdictBody(String(fv.body ?? ""));
        setFinalVerdictChangeLog((fv.change_log || {}) as FinalVerdictChangeLog);
        setFinalVerdictVersionId(String(fv.version_id ?? ""));
        setFinalLogicalEvidence(Array.isArray(fv.logical_evidence) ? fv.logical_evidence.map((x) => String(x)) : []);
        setFinalWorkVector((fv.work_vector as Record<string, unknown>) || null);
        setFinalTopologyGraphV1((fv.topology_graph_v1 as Record<string, unknown>) || null);
        setFinalStructureCandidatesV0((fv.structure_candidates_v0 as Record<string, unknown>) || null);
        setFinalStructureFinalDecisionV0((fv.structure_final_decision_v0 as Record<string, unknown>) || null);
      }

      if (Array.isArray(snap.resolved_card_ids)) {
        setResolvedCardIds(snap.resolved_card_ids.map((x) => String(x)));
      }
      if (Array.isArray(snap.decision_selection_ids)) {
        setConfirmedDecisionIds(normalizeDecisionIds(snap.decision_selection_ids.map((x) => String(x))));
      }

      const ld = snap.logic_diff;
      if (ld) {
        setLogicDiff({
          baseline_abs_loss_total: ld.baseline_abs_loss_total ?? null,
          current_abs_loss_total: ld.current_abs_loss_total ?? null,
          abs_delta: ld.abs_delta ?? null,
          baseline_entropy: ld.baseline_entropy ?? null,
          current_entropy: ld.current_entropy ?? null,
          entropy_delta: ld.entropy_delta ?? null,
        });
      }

      if (labState.lastSeedPayload) {
        setLastSeedPayload(labState.lastSeedPayload);
      }

      setSnapshotAvailable(true);
    } finally {
      queueMicrotask(() => {
        isSnapshotRestoringRef.current = false;
      });
    }
  }, [labState.snapshot, labState.lastSeedPayload, metadata]);

  useLayoutEffect(() => {
    if (navHandledRef.current) return;
    if (typeof window === "undefined") return;
    navHandledRef.current = true;
    const params = new URLSearchParams(window.location.search);
    const hasSnapshot = Boolean(labState.snapshot);
    const hasActiveSession = Boolean(labState.snapshot?.active_session_id);
    const hasValidSnapshot = hasSnapshot && hasActiveSession;
    const navEntry = performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming | undefined;
    const navType = ((navEntry?.type || "unknown") as NavigationInfo["navType"]);
    const isReload = navType === "reload";
    const isBackForward = navType === "back_forward";
    const resumeFromMarker = false;
    let intent: NavigationInfo["intent"] = "FRESH_START";

    if (hasValidSnapshot && (isReload || isBackForward || resumeFromMarker)) {
      intent = "RESTORE_AUDIT";
    } else {
      intent = "FRESH_START";
    }

    const navInfo: NavigationInfo = {
      navType,
      hasValidSnapshot,
      intent,
    };
    const debugMode = (params.get("debug") || "").trim() === "1";
    if (debugMode) {
      // State Recovery Auditor: deterministic diagnostics for recovery decisions.
      // eslint-disable-next-line no-console
      console.info("[StateRecoveryAuditor]", navInfo);
    }
  }, [labState.snapshot]);

  useEffect(() => {
    setSnapshotAvailable(Boolean(labState.snapshot));
  }, [labState.snapshot]);

  const reCalculateAbs = useCallback(async () => {
    await reCalculateAbsSilentlyImplRef.current();
  }, []);
  reCalculateAbsRef.current = reCalculateAbs;

  const onPluginConfigChange = useCallback(() => {
    const prevJson = runtimeConfigSerializedRef.current;
    if (prevJson) {
      try {
        const prevCfg = JSON.parse(prevJson) as { pluginWeights?: PluginWeights };
        const pw = prevCfg.pluginWeights;
        const next = labStateRef.current.runtimeConfig.pluginWeights;
        if (
          pw &&
          typeof pw.blindSchool === "number" &&
          Number.isFinite(pw.blindSchool) &&
          typeof pw.wangshuai === "number" &&
          Number.isFinite(pw.wangshuai) &&
          (Math.abs(next.blindSchool - pw.blindSchool) > 0.2 ||
            Math.abs(next.wangshuai - pw.wangshuai) > 0.2)
        ) {
          setSigShiftFlashKey((k) => k + 1);
        }
      } catch {
        /* ignore */
      }
    }
    runtimeConfigSerializedRef.current = JSON.stringify(labStateRef.current.runtimeConfig);
    void reCalculateAbs();
  }, [reCalculateAbs]);

  useEffect(() => {
    const sig = JSON.stringify(labState.runtimeConfig);
    if (runtimeConfigSerializedRef.current === null) {
      runtimeConfigSerializedRef.current = sig;
    }
    const prevView = prevActiveViewRef.current;
    const enteredLab = activeView === "lab" && prevView !== null && prevView !== "lab";
    prevActiveViewRef.current = activeView;

    if (activeView !== "lab") {
      return () => {
        if (pluginRecalcTimerRef.current) {
          clearTimeout(pluginRecalcTimerRef.current);
          pluginRecalcTimerRef.current = null;
        }
      };
    }
    if (!lastSeedPayload || busy || isStreaming || isExecuting) {
      return () => {
        if (pluginRecalcTimerRef.current) {
          clearTimeout(pluginRecalcTimerRef.current);
          pluginRecalcTimerRef.current = null;
        }
      };
    }

    const drift = runtimeConfigSerializedRef.current !== sig;

    const runNow = () => {
      if (pluginRecalcTimerRef.current) {
        clearTimeout(pluginRecalcTimerRef.current);
        pluginRecalcTimerRef.current = null;
      }
      onPluginConfigChange();
    };

    if (enteredLab) {
      runNow();
      return () => {
        if (pluginRecalcTimerRef.current) {
          clearTimeout(pluginRecalcTimerRef.current);
          pluginRecalcTimerRef.current = null;
        }
      };
    }

    if (drift) {
      if (pluginRecalcTimerRef.current) clearTimeout(pluginRecalcTimerRef.current);
      pluginRecalcTimerRef.current = setTimeout(runNow, 280);
    }

    return () => {
      if (pluginRecalcTimerRef.current) {
        clearTimeout(pluginRecalcTimerRef.current);
        pluginRecalcTimerRef.current = null;
      }
    };
  }, [
    labState.runtimeConfig,
    activeView,
    lastSeedPayload,
    busy,
    isStreaming,
    isExecuting,
    onPluginConfigChange,
  ]);

  useLayoutEffect(() => {
    const n = labState.inboxResetNonce;
    if (n === 0 || n === inboxNonceHandledRef.current) return;
    inboxNonceHandledRef.current = n;
    setConfirmedDecisionIds(normalizeDecisionIds(labState.snapshot?.decision_selection_ids || []));
    setResolvedCardIds((labState.snapshot?.resolved_card_ids || []).map((x) => String(x)));
    setSelectionResetToken((v) => v + 1);
  }, [
    labState.inboxResetNonce,
    labState.snapshot?.decision_selection_ids,
    labState.snapshot?.resolved_card_ids,
  ]);

  useLayoutEffect(() => {
    reCalculateAbsSilentlyImplRef.current = async () => {
      const seed = lastSeedPayloadRef.current;
      if (!seed || isSnapshotRestoringRef.current || isRestoringRef.current) return;
      if (labStateRef.current.isFinalized) return;
      if (verdictRecalcBarrierRef.current) {
        silentRecalcDeferredRef.current = true;
        return;
      }
      if (silentRecalcInFlightRef.current) return;
      silentRecalcInFlightRef.current = true;
      const c = silentCtxRef.current;
      const set = settersRef.current;
      try {
        const latestHealth = await refreshHealthRef.current();
        const response = await fetch(`${API_BASE}/api/v1/analyze-seed`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            date: seed.date,
            time: seed.time,
            calendar: seed.calendar,
            gender: seed.gender,
            lang: c.lang,
            latitude: 31.2304,
            longitude: 121.4737,
            session_id: c.consultationId ?? undefined,
            physics_config: c.labConfig,
            enabled_plugins: [
              ...(c.pluginSwitches.blindSchool ? ["classical.blind_school.v1"] : []),
              ...(c.pluginSwitches.wangshuai ? ["classical.wangshuai.v1"] : []),
              ...(c.pluginSwitches.wealthRisk ? ["modern.wealth_risk.v1"] : []),
            ],
            blind_school_features: buildBlindSchoolFeaturesPayload(c.pluginSwitches),
          }),
        });
        if (!response.ok) return;
        const data = await response.json();
        const tensor = (data.physics_tensor || null) as Record<string, unknown> | null;
        if (!tensor || typeof tensor !== "object") return;

        set.setMetadata(data.metadata as BaziMetadata);
        set.setTimeline((data.timeline ?? null) as TimelineSnapshot | null);
        if (tensor.deity_scores && typeof tensor.deity_scores === "object") {
          set.setDeityScores(tensor.deity_scores as Record<string, number>);
        }
        if (tensor.deity_energy_axes && typeof tensor.deity_energy_axes === "object") {
          set.setDeityEnergyAxes(tensor.deity_energy_axes as Record<string, DeityEnergyAxis>);
        }
        if (tensor.deity_components && typeof tensor.deity_components === "object") {
          set.setDeityComponents(tensor.deity_components as Record<string, DeityComponent>);
        }
        if (tensor.deity_trace_details && typeof tensor.deity_trace_details === "object") {
          set.setDeityTraceDetails(tensor.deity_trace_details as Record<string, Record<string, unknown>>);
        } else if ((tensor.meta as Record<string, unknown> | undefined)?.deity_trace_details) {
          set.setDeityTraceDetails(
            (tensor.meta as Record<string, unknown>).deity_trace_details as Record<string, Record<string, unknown>>,
          );
        } else {
          set.setDeityTraceDetails({});
        }
        if (tensor.audit_log && typeof tensor.audit_log === "object") {
          set.setPhysicsAudit(tensor.audit_log as Record<string, unknown>);
        }
        set.setPhysicsConfidence(typeof tensor.confidence === "number" ? tensor.confidence : null);
        if (Array.isArray(tensor.evidence)) {
          set.setPhysicsEvidence(tensor.evidence.map((item: unknown) => String(item)));
        } else {
          set.setPhysicsEvidence([]);
        }
        const pMeta = (tensor.meta || {}) as Record<string, unknown>;
        if (pMeta.params && typeof pMeta.params === "object") {
          set.setPhysicsParams(pMeta.params as Record<string, number>);
        }
        const ge = pMeta.global_entropy;
        set.setGlobalEntropy(typeof ge === "number" && Number.isFinite(ge) ? ge : null);

        const currentMetric = extractMetricSnapshotFromPhysics(tensor);
        updateLogicDiffRef.current(currentMetric, c.confirmedDecisionIds.length === 0 || !c.baselineMetrics);
        persistSnapshotRef.current({
          physics_tensor: tensor,
          metadata: data.metadata as Record<string, unknown>,
          timeline: (data.timeline ?? null) as Record<string, unknown> | null,
          llm_prompt: data.llm_prompt || "",
          audit_summary: data.audit_summary,
          consultationIdOverride: c.consultationId,
          healthOverride: latestHealth,
          seedSignatureOverride: seedPayloadSignature(seed),
        });
        bumpSyncBarrierSeq();
        scheduleInteractionHubPersist();
      } catch {
        /* silent */
      } finally {
        silentRecalcInFlightRef.current = false;
      }
    };
  }, [bumpSyncBarrierSeq, scheduleInteractionHubPersist]);

  langRef.current = lang;
  lastSeedPayloadRef.current = lastSeedPayload;
  metadataRef.current = metadata;
  busyRef.current = busy;
  isStreamingRef.current = isStreaming;
  isExecutingRef.current = isExecuting;
  isRestoringRef.current = isRestoring;
  silentCtxRef.current = {
    consultationId,
    labConfig,
    pluginSwitches,
    pluginWeights,
    lang,
    baselineMetrics,
    confirmedDecisionIds,
  };
  settersRef.current = {
    setMetadata,
    setTimeline,
    setDeityScores,
    setDeityEnergyAxes,
    setDeityComponents,
    setDeityTraceDetails,
    setPhysicsAudit,
    setPhysicsConfidence,
    setPhysicsEvidence,
    setPhysicsParams,
    setGlobalEntropy,
  };

  const snapshotUrlTag = useMemo(() => {
    const raw = (searchParams.get("tag") || "").trim();
    if (!raw) return "";
    return raw.replace(/[^\w\-:.]/g, "").slice(0, 48);
  }, [searchParams]);

  const streamThemeChroma = useMemo(() => {
    const blindWeight = Number(pluginWeights.blindSchool || 0);
    const wanshuaiWeight = Number(pluginWeights.wangshuai || 0);
    const total = Math.max(0.0001, blindWeight + wanshuaiWeight);
    const blindRatio = blindWeight / total;
    const wangshuaiRatio = wanshuaiWeight / total;
    const bgColor = interpolateColor(
      "#2D4F1E", // WangShuai green
      "#1A1A1A", // BlindSchool black
      blindRatio,
    );
    const conflictReport = ((finalStructureFinalDecisionV0 as {
      plugin_conflict_report?: { tension_level?: number; zone?: string; has_polarity_reversal?: boolean };
    } | null)?.plugin_conflict_report || {});
    const tension = Number(conflictReport.tension_level || 0);
    const isConflictOverload = String(conflictReport.zone || "BLUE") === "RED" && tension > 0.8;
    const hasPolarityReversal = Boolean(conflictReport.has_polarity_reversal);
    return { bgColor, blindRatio, wangshuaiRatio, isConflictOverload, hasPolarityReversal };
  }, [pluginWeights.blindSchool, pluginWeights.wangshuai, finalStructureFinalDecisionV0]);

  return {
    lang,
    setLang,
    busy,
    consultationId,
    metadata,
    timeline,
    selectedBranch,
    setSelectedBranch,
    auditItems,
    health,
    llmModelName,
    i18nCalls,
    deityScores,
    deityEnergyAxes,
    deityComponents,
    deityTraceDetails,
    hoveredDeity,
    setHoveredDeity,
    confirmedConflicts,
    llmDiagnosticData,
    physicsParams,
    globalEntropy,
    auditorProposalCards,
    autoConvertedParamKey,
    consensusHistory,
    cards,
    resultLogs,
    finalVerdictBody,
    finalVerdictChangeLog,
    finalLogicalEvidence,
    finalWorkVector,
    finalTopologyGraphV1,
    finalStructureCandidatesV0,
    finalStructureFinalDecisionV0,
    confirmedDecisions,
    confirmedDecisionIds,
    setConfirmedDecisionIds,
    urlDecisionHydrated,
    snapshotUrlTag,
    snapshotAvailable,
    setAsBaseline,
    logicDiff,
    stressTestResult,
    genderComparisonResult,
    finalVerdictHistory,
    selectionResetToken,
    finalVerdictVersionId,
    conclusionVersion,
    summaryChanged,
    l1Certified,
    physicsAudit,
    physicsConfidence,
    physicsEvidence,
    labConfig,
    setLabConfig,
    showPhysicsAudit,
    setShowPhysicsAudit,
    pluginSwitches,
    setPluginSwitches,
    pluginWeights,
    setPluginWeights,
    streamThemeChroma,
    rerunFinalVerdictWithWeights,
    logicDrawerOpen,
    logicDrawerTitle,
    logicDrawerFocus,
    logicDrawerDetails,
    logicDrawerTrace,
    setLogicDrawerOpen,
    onSeedSubmit,
    addAuditorProposalToInbox,
    onExecuteDecision,
    refreshVerdict,
    executeDecisionAndRefresh,
    appendSystemAuditLog,
    revokeConfirmedDecision,
    openLogicDrawer,
    openLogicDrawerByDeity,
    onEvidenceItemClick,
    showVerdictHistory,
    applyCurrentSqlPatch,
    applyLabConfigAndRecalculate,
    reCalculateAbs,
    runStressTest,
    runGenderComparison,
    t,
    inboxResetNonce: labState.inboxResetNonce,
    sigShiftFlashKey,
    isFinalized: labState.isFinalized,
    finalizeVerdict,
    syncBarrierSeq: labState.syncBarrierSeq,
  };
}
