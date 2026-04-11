"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { AuditItem } from "@/components/AuditSidebar";
import type { BaziMetadata, Lang, TimelineSnapshot } from "@/types/bazi";
import { API_BASE, VERDICT_TIMEOUT_MS } from "./constants";
import { applyPhysicsSqlPatch as requestApplyPhysicsSqlPatch } from "./controller/adminPhysicsApi";
import {
  buildFinalVerdictRequestBody,
  finalVerdictHttpFallbackLog,
  parseFinalVerdictFromApiData,
} from "./controller/finalVerdictPayload";
import type { LabSnapshotHydrationSinks } from "./controller/labSnapshotHydration";
import {
  buildBlindSchoolFeaturesPayload,
  extractInteractionHubMangpai,
  extractMetricSnapshotFromPhysics,
  interpolateColor,
  decisionIdsSignature,
  normalizeDecisionIds,
  normalizedSnapshotDecisionIds,
  seedPayloadSignature,
} from "./controller/streamBoardPure";
import type {
  ConfirmedDecisionItem,
  ConsensusItem,
  MetricSnapshot,
  SilentBoardCtx,
  SilentRecalcPhysicsSetters,
} from "./controller/streamBoardTypes";
import { useSeedPreviewModule } from "./controller/useSeedPreviewModule";
import { useStreamBoardExecution, type StreamBoardExecutionContext } from "./controller/useStreamBoardExecution";
import { useStreamBoardHealth } from "./controller/useStreamBoardHealth";
import { buildInboxCards, createAuditorProposalCard, type DecisionSignalToNoiseMeta } from "./cardBuilder";
import type {
  DeityComponent,
  DeityEnergyAxis,
  FinalVerdictChangeLog,
  InboxCard,
  LogicDiff,
  LlmDiagnosticData,
  LogicProposal,
  PluginWeights,
  SeedPayload,
  StreamBoardViewModel,
} from "./models";
import { buildFallbackVerdict } from "./utils";
import { useClientSearchParams } from "./useClientSearchParams";
import { useTranslationQueue } from "./useTranslationQueue";
import { useActiveView, type ShellActiveView } from "@/components/layout/ActiveViewContext";
import { useLabConfig } from "@/features/lab-config/LabConfigContext";
import { useStreamBoardLabSnapshotEffects } from "@/features/stream-board/hooks/useStreamBoardLabSnapshotEffects";
import { useStreamBoardSilentRecalculateLayout } from "@/features/stream-board/hooks/useStreamBoardSilentRecalculateLayout";
import { useStreamBoardAuditUiState } from "@/features/stream-board/hooks/useStreamBoardAuditUiState";
import { useStreamBoardLogicDrawerState } from "@/features/stream-board/hooks/useStreamBoardLogicDrawerState";
import { useStreamBoardPhysicsState } from "@/features/stream-board/hooks/useStreamBoardPhysicsState";
import type { StreamBoardHydrationSnapshot } from "@/features/stream-board/hooks/streamBoardSnapshotTypes";
import { useStreamBoardVerdictState } from "@/features/stream-board/hooks/useStreamBoardVerdictState";
import { useLabStore, useUiLang } from "@/features/stream-board/stores/useLabStore";

export function useStreamBoardController(): StreamBoardViewModel {
  const searchParams = useClientSearchParams();
  const {
    state: labState,
    mergeSnapshot,
    setLastSeedPayload: persistLastSeedToStore,
    finalizeVerdict,
    bumpSyncBarrierSeq,
    clearDecisionInbox,
  } = useLabStore();
  const { activeView } = useActiveView();
  const labStateRef = useRef(labState);
  labStateRef.current = labState;

  const { health, setHealth, llmModelName, setLlmModelName, refreshHealth } = useStreamBoardHealth(API_BASE);
  const {
    referenceYear,
    setReferenceYear,
    referenceYearRef,
    seedPreviewPillars,
    seedPreviewTimeline,
    seedPreviewBusy,
    seedPreviewError,
    scheduleSeedDraftPreview,
    refreshSeedPreview,
    resetSeedPreviewState,
  } = useSeedPreviewModule(API_BASE);

  const initialSnapshot = (labState.snapshot || null) as StreamBoardHydrationSnapshot;
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

  const {
    conclusionVersion,
    setConclusionVersion,
    lastConclusionText,
    setLastConclusionText,
    summaryChanged,
    setSummaryChanged,
    finalVerdictBody,
    setFinalVerdictBody,
    finalVerdictChangeLog,
    setFinalVerdictChangeLog,
    finalVerdictVersionId,
    setFinalVerdictVersionId,
    finalLogicalEvidence,
    setFinalLogicalEvidence,
    finalWorkVector,
    setFinalWorkVector,
    finalTopologyGraphV1,
    setFinalTopologyGraphV1,
    finalStructureCandidatesV0,
    setFinalStructureCandidatesV0,
    finalStructureFinalDecisionV0,
    setFinalStructureFinalDecisionV0,
    finalVerdictHistory,
    setFinalVerdictHistory,
  } = useStreamBoardVerdictState(initialSnapshot);

  const {
    deityScores,
    setDeityScores,
    deityEnergyAxes,
    setDeityEnergyAxes,
    deityComponents,
    setDeityComponents,
    deityTraceDetails,
    setDeityTraceDetails,
    physicsAudit,
    setPhysicsAudit,
    physicsConfidence,
    setPhysicsConfidence,
    physicsEvidence,
    setPhysicsEvidence,
    physicsParams,
    setPhysicsParams,
    globalEntropy,
    setGlobalEntropy,
  } = useStreamBoardPhysicsState(initialSnapshot);

  const {
    streamingText,
    setStreamingText,
    auditItems,
    setAuditItems,
    resultLogs,
    setResultLogs,
    showPhysicsAudit,
    setShowPhysicsAudit,
    llmDiagnosticData,
    setLlmDiagnosticData,
  } = useStreamBoardAuditUiState();

  const {
    logicDrawerOpen,
    setLogicDrawerOpen,
    logicDrawerTitle,
    setLogicDrawerTitle,
    logicDrawerFocus,
    setLogicDrawerFocus,
    logicDrawerDetails,
    setLogicDrawerDetails,
    logicDrawerTrace,
    setLogicDrawerTrace,
  } = useStreamBoardLogicDrawerState();

  const [busy, setBusy] = useState(false);
  const [selectedBranch, setSelectedBranch] = useState<string>();
  const [metadata, setMetadata] = useState<BaziMetadata | null>(null);
  const [consultationId, setConsultationId] = useState<number | null>(null);
  const [confirmedConflicts, setConfirmedConflicts] = useState<string[]>([]);
  const [firstPromptText, setFirstPromptText] = useState("");
  const [timeline, setTimeline] = useState<TimelineSnapshot | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [hoveredDeity, setHoveredDeity] = useState<string>();
  const { labConfig, setLabConfig, pluginSwitches, setPluginSwitches, pluginWeights, setPluginWeights } = useLabConfig();
  const [lastSeedPayload, setLastSeedPayload] = useState<SeedPayload | null>(null);
  const [auditorProposalCards, setAuditorProposalCards] = useState<InboxCard[]>([]);
  const [autoConvertedParamKey, setAutoConvertedParamKey] = useState<string | null>(null);
  const [resolvedCardIds, setResolvedCardIds] = useState<string[]>([]);
  const [selectionResetToken, setSelectionResetToken] = useState(0);
  const [sigShiftFlashKey, setSigShiftFlashKey] = useState(0);
  const [consensusHistory, setConsensusHistory] = useState<ConsensusItem[]>([]);
  const [confirmedDecisions, setConfirmedDecisions] = useState<ConfirmedDecisionItem[]>([]);
  const [confirmedDecisionIds, setConfirmedDecisionIds] = useState<string[]>(
    () => normalizedSnapshotDecisionIds(initialSnapshot?.decision_selection_ids),
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
  const settersRef = useRef<SilentRecalcPhysicsSetters>({
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
  const executionCtxRef = useRef<StreamBoardExecutionContext>(null as unknown as StreamBoardExecutionContext);
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
  const [stressTestResult, setStressTestResult] = useState<Record<string, unknown> | null>(null);
  const [genderComparisonResult, setGenderComparisonResult] = useState<Record<string, unknown> | null>(null);
  const [snapshotAvailable, setSnapshotAvailable] = useState(false);

  const hydrationSinksRef = useRef({} as LabSnapshotHydrationSinks);
  hydrationSinksRef.current = {
    setMetadata,
    setTimeline,
    setFirstPromptText,
    setConsultationId,
    setHealth,
    setAuditItems,
    setResultLogs,
    setLlmDiagnosticData,
    setDeityScores,
    setDeityEnergyAxes,
    setDeityComponents,
    setDeityTraceDetails,
    setPhysicsAudit,
    setPhysicsConfidence,
    setPhysicsEvidence,
    setPhysicsParams,
    setGlobalEntropy,
    setFinalVerdictBody,
    setFinalVerdictChangeLog,
    setFinalVerdictVersionId,
    setFinalLogicalEvidence,
    setFinalWorkVector,
    setFinalTopologyGraphV1,
    setFinalStructureCandidatesV0,
    setFinalStructureFinalDecisionV0,
    setResolvedCardIds,
    setConfirmedDecisionIds,
    setLogicDiff,
    setLastSeedPayload,
    setSnapshotAvailable,
  };

  useStreamBoardLabSnapshotEffects({
    metadata,
    labSnapshot: labState.snapshot,
    lastSeedPayload: labState.lastSeedPayload,
    inboxResetNonce: labState.inboxResetNonce,
    isSnapshotRestoringRef,
    inboxNonceHandledRef,
    navHandledRef,
    hydrationSinksRef,
    setSnapshotAvailable,
    setConfirmedDecisionIds,
    setResolvedCardIds,
    setSelectionResetToken,
  });

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

  const decisionSignalToNoise = useMemo((): DecisionSignalToNoiseMeta | undefined => {
    const meta = labState.snapshot?.physics_tensor?.meta as Record<string, unknown> | undefined;
    const raw = meta?.decision_signal_to_noise;
    if (raw && typeof raw === "object") return raw as DecisionSignalToNoiseMeta;
    return undefined;
  }, [labState.snapshot?.physics_tensor?.meta]);

  const cards = useMemo(
    () =>
      buildInboxCards({
        metadata,
        firstPromptText,
        auditorProposalCards,
        resolvedCardIds,
        t,
        decisionSignalToNoise,
      }),
    [metadata, firstPromptText, auditorProposalCards, resolvedCardIds, t, decisionSignalToNoise],
  );
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
    const prev = normalizedSnapshotDecisionIds(labState.snapshot?.decision_selection_ids);
    if (decisionIdsSignature(next) === decisionIdsSignature(prev)) return;
    mergeSnapshotRef.current({ decision_selection_ids: next });
  }, [
    confirmedDecisionIds,
    urlDecisionHydrated,
    isRestoring,
    labState.snapshot?.active_session_id,
    labState.snapshot?.decision_selection_ids,
  ]);

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

      const response = await fetch(`${API_BASE}/api/v1/final-verdict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify(
          buildFinalVerdictRequestBody({
            metadata,
            deityScores,
            deityEnergyAxes,
            deityComponents,
            deityTraceDetails,
            physicsAudit,
            llmDiagnosticData,
            timeline: (timeline || {}) as Record<string, unknown> | null,
            conflicts,
            selectedCards,
            consensusHistory,
            finalVerdictBody,
            lastConclusionText,
            finalLogicalEvidence,
            consultationId,
            pluginSwitches,
            pluginWeights,
            lang,
          }),
        ),
      });
      clearTimeout(timer);

      const data = await response.json();
      const verdictParsed = parseFinalVerdictFromApiData(data);
      if (verdictParsed) {
        return verdictParsed;
      }
      setResultLogs((prev) => [...prev, finalVerdictHttpFallbackLog(response, data)]);
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
    const result = await requestApplyPhysicsSqlPatch(API_BASE, sqlPatch);
    if (!result.ok) return { ok: false, error: result.error };
    setResultLogs((prev) => [
      ...prev,
      `🛠️ 已应用参数建议：${result.updated?.param_key ?? "unknown"} -> ${result.updated?.new_value ?? "?"}`,
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

  const clearLabPipelineForSeedDraft = useCallback(() => {
    if (labStateRef.current.isFinalized) return;
    setLastSeedPayload(null);
    persistLastSeedToStore(null);
    setMetadata(null);
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
    setConfirmedDecisions([]);
    setConfirmedDecisionIds([]);
    resetSeedPreviewState();
    setConsultationId(null);
    setSelectionResetToken((v) => v + 1);
    setLogicDiff({
      baseline_abs_loss_total: null,
      current_abs_loss_total: null,
      abs_delta: null,
      baseline_entropy: null,
      current_entropy: null,
      entropy_delta: null,
    });
    const hub = labStateRef.current.snapshot?.interaction_hub || {};
    mergeSnapshot({
      metadata: undefined,
      physics_tensor: undefined,
      timeline: undefined,
      final_verdict: undefined,
      audit_summary: undefined,
      llm_prompt: undefined,
      seed_signature: undefined,
      active_session_id: undefined,
      logic_diff: {
        baseline_abs_loss_total: null,
        current_abs_loss_total: null,
        abs_delta: null,
        baseline_entropy: null,
        current_entropy: null,
        entropy_delta: null,
      },
      decision_selection_ids: [],
      resolved_card_ids: [],
      interaction_hub: {
        ...hub,
        consultation_id: null,
        pending_cards: [],
        resolved_card_ids: [],
        result_logs: [],
        audit_items: [],
      },
    });
    clearDecisionInbox();
  }, [mergeSnapshot, clearDecisionInbox, persistLastSeedToStore, resetSeedPreviewState]);

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
          payload: { ...payload, reference_year: referenceYearRef.current },
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
          reference_year: referenceYearRef.current,
        }),
      });

      if (!response.ok) throw new Error(await response.text());
      const data = await response.json();
      markActiveSession(currentSessionId ?? consultationId ?? null);
      setMetadata(data.metadata as BaziMetadata);
      const tl = (data.timeline ?? null) as TimelineSnapshot | null;
      setTimeline(tl);
      resetSeedPreviewState();
      const ry = referenceYearRef.current;
      if (tl?.dayun && tl?.liunian) {
        setResultLogs((prev) => [
          ...prev,
          `📅 ${t("参考年")} ${ry} → ${t("大运")} ${tl.dayun} · ${t("流年")} ${tl.liunian}（${t("已随测算写入命盘")}）`,
        ]);
      }

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

  const { onExecuteDecision, rerunFinalVerdictWithWeights, refreshVerdict, executeDecisionAndRefresh } =
    useStreamBoardExecution(executionCtxRef);

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
      reference_year: referenceYearRef.current,
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

  async function revokeConfirmedDecision(id: string) {
    const nextDecisions = confirmedDecisions.filter((item) => item.id !== id);
    setConfirmedDecisions(nextDecisions);
    setConfirmedDecisionIds((prev) => prev.filter((item) => item !== id));
  }

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

  useStreamBoardSilentRecalculateLayout({
    reCalculateAbsSilentlyImplRef,
    lastSeedPayloadRef,
    isSnapshotRestoringRef,
    isRestoringRef,
    labStateRef,
    verdictRecalcBarrierRef,
    silentRecalcDeferredRef,
    silentRecalcInFlightRef,
    silentCtxRef,
    settersRef,
    refreshHealthRef,
    referenceYearRef,
    updateLogicDiffRef,
    persistSnapshotRef,
    bumpSyncBarrierSeq,
    scheduleInteractionHubPersist,
  });

  useEffect(() => {
    if (busy || isStreaming || isExecuting) return;
    if (!metadata || !lastSeedPayload) return;
    if (labStateRef.current.isFinalized) return;
    let cancelled = false;
    const timer = window.setTimeout(async () => {
      try {
        const res = await fetch(`${API_BASE}/api/v1/seed-preview`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            date: lastSeedPayload.date,
            time: lastSeedPayload.time,
            calendar: lastSeedPayload.calendar,
            gender: lastSeedPayload.gender,
            reference_year: referenceYearRef.current,
          }),
        });
        if (!res.ok || cancelled) return;
        const data = (await res.json()) as { timeline: TimelineSnapshot };
        if (cancelled) return;
        const tl = data.timeline;
        setTimeline(tl);
        mergeSnapshot({ timeline: tl as unknown as Record<string, unknown> });
      } catch {
        /* ignore */
      }
    }, 240);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [referenceYear, metadata, lastSeedPayload, busy, isStreaming, isExecuting, mergeSnapshot]);

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

  executionCtxRef.current = {
    t,
    lang,
    apiBase: API_BASE,
    metadata,
    consultationId,
    lastSeedPayload,
    lastConclusionText,
    conclusionVersion,
    confirmedConflicts,
    globalEntropy,
    llmModelName,
    setIsExecuting,
    setConsensusHistory,
    setConfirmedConflicts,
    setResolvedCardIds,
    setStreamingText,
    setConclusionVersion,
    setSummaryChanged,
    setLastConclusionText,
    setFinalVerdictBody,
    setFinalVerdictChangeLog,
    setFinalLogicalEvidence,
    setFinalWorkVector,
    setFinalTopologyGraphV1,
    setFinalStructureCandidatesV0,
    setFinalStructureFinalDecisionV0,
    setFinalVerdictVersionId,
    setConfirmedDecisions,
    setFinalVerdictHistory,
    setAuditorProposalCards,
    setConfirmedDecisionIds,
    setSelectionResetToken,
    setAuditItems,
    setResultLogs,
    applyPhysicsSqlPatch,
    onSeedSubmit,
    generateFinalVerdict,
    appendFinalVerdictAuditItem,
    scheduleInteractionHubPersist,
    updateLogicDiff,
    typewriterResultLine,
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

  const lastCommittedSeedSignature = useMemo(() => seedPayloadSignature(lastSeedPayload), [lastSeedPayload]);

  return {
    lang,
    setLang,
    busy,
    consultationId,
    metadata,
    timeline,
    referenceYear,
    setReferenceYear,
    seedPreviewPillars,
    seedPreviewTimeline,
    seedPreviewBusy,
    seedPreviewError,
    scheduleSeedDraftPreview,
    refreshSeedPreview,
    clearLabPipelineForSeedDraft,
    lastCommittedSeedSignature,
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
