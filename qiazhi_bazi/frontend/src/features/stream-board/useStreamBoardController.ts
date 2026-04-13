"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { AuditItem } from "@/components/AuditSidebar";
import type { BaziMetadata, Lang, TimelineSnapshot } from "@/types/bazi";
import { API_BASE } from "./constants";
import { applyPhysicsSqlPatch as requestApplyPhysicsSqlPatch } from "./controller/adminPhysicsApi";
import type { LabSnapshotHydrationSinks } from "./controller/labSnapshotHydration";
import {
  buildBlindSchoolFeaturesPayload,
  coerceLogicProposalParamKey,
  extractInteractionHubMangpai,
  extractMetricSnapshotFromPhysics,
  interpolateColor,
  decisionIdsSignature,
  normalizeDecisionIds,
  normalizedSnapshotDecisionIds,
  seedPayloadSignature,
  isTrustworthyPhysicsAuditDiagnosis,
} from "./controller/streamBoardPure";
import type {
  ConfirmedDecisionItem,
  ConsensusItem,
  MetricSnapshot,
  SilentBoardCtx,
  SilentRecalcPhysicsSetters,
} from "./controller/streamBoardTypes";
import type { StreamPipelineEventKind, StreamPipelinePhase } from "./models";
import { useSeedPreviewModule } from "./controller/useSeedPreviewModule";
import { useStreamBoardExecution, type StreamBoardExecutionContext } from "./controller/useStreamBoardExecution";
import { useStreamBoardDiagnosticActions, type StreamBoardDiagnosticDeps } from "./controller/useStreamBoardDiagnosticActions";
import { useStreamBoardDrawerActions, type StreamBoardDrawerDeps } from "./controller/useStreamBoardDrawerActions";
import { useStreamBoardSnapshotPersist, type StreamBoardSnapshotPersistDeps } from "./controller/useStreamBoardSnapshotPersist";
import { useStreamBoardPipeline, reducePipelinePhase } from "./controller/useStreamBoardPipeline";
import { useStreamBoardHealth } from "./controller/useStreamBoardHealth";
import type { DecisionJournalEntry } from "@/features/stream-board/decisionJournal";
import { normalizeDecisionJournalEntries } from "@/features/stream-board/decisionJournal";
import {
  buildInboxCards,
  createAuditorProposalCard,
  createPhysicsAuditSemanticDiagnosisCard,
  createPhysicsAuditSemanticVerdictCard,
  type DecisionSignalToNoiseMeta,
} from "./cardBuilder";
import { augmentDiagnosisWithMangpaiManifest } from "./mangpaiChipManifest";
import { SILENT_PHYSICS_RECALC_EVENT } from "./physicsRecalcDispatch";
import type {
  DeityComponent,
  DeityEnergyAxis,
  FinalVerdictChangeLog,
  InboxCard,
  LogicDiff,
  LlmDiagnosticData,
  LogicProposal,
  PatternThresholdRow,
  PluginWeights,
  SeedPayload,
  StreamBoardViewModel,
} from "./models";
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
import { useSeedAnalysis, type SeedAnalysisDeps } from "@/features/stream-board/hooks/useSeedAnalysis";
import { useVerdictExecution, type VerdictExecutionDeps } from "@/features/stream-board/hooks/useVerdictExecution";
import { useLabStore, useUiLang } from "@/features/stream-board/stores/useLabStore";

export function useStreamBoardController(): StreamBoardViewModel {
  const searchParams = useClientSearchParams();
  const purePhysicsAudit = useMemo(
    () =>
      (searchParams.get("pure_physics_audit") || searchParams.get("purePhysicsAudit") || "").trim() === "1",
    [searchParams],
  );
  const {
    state: labState,
    mergeSnapshot,
    setLastSeedPayload: persistLastSeedToStore,
    finalizeVerdict: finalizeVerdictFromLab,
    bumpSyncBarrierSeq,
    clearDecisionInbox,
    setShadowPreview,
    clearShadowPreview,
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
  const referenceYearRecalcInitRef = useRef(false);
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
  const [verdictBodyRenderNonce, setVerdictBodyRenderNonce] = useState(0);
  const [patternThresholds, setPatternThresholds] = useState<PatternThresholdRow[]>([]);
  const [patternThresholdsStatus, setPatternThresholdsStatus] = useState<string | null>(null);
  const appendSilentAnalyzeLogRef = useRef<(line: string) => void>(() => {});
  appendSilentAnalyzeLogRef.current = (line: string) => {
    setResultLogs((prev) => [...prev, line].slice(-48));
  };

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
  const [pipelinePhase, setPipelinePhase] = useState<StreamPipelinePhase>("READY");
  const [narrativeReshapeActive, setNarrativeReshapeActive] = useState(false);
  const [orchestratorVfSkeletonLines, setOrchestratorVfSkeletonLines] = useState<string[]>([]);
  const [orchestratorCausalAuditPulse, setOrchestratorCausalAuditPulse] = useState("");
  const reportPipelineEvent = useCallback((event: StreamPipelineEventKind) => {
    setPipelinePhase((prev) => reducePipelinePhase(prev, event));
  }, []);
  const finalizeVerdict = useCallback(async () => {
    const ok = await finalizeVerdictFromLab();
    if (ok) setPipelinePhase("DECIDED");
    return ok;
  }, [finalizeVerdictFromLab]);
  const [hoveredDeity, setHoveredDeity] = useState<string>();
  const { labConfig, setLabConfig, pluginSwitches, setPluginSwitches, pluginWeights, setPluginWeights } = useLabConfig();
  const [lastSeedPayload, setLastSeedPayload] = useState<SeedPayload | null>(null);
  const [auditorProposalCards, setAuditorProposalCards] = useState<InboxCard[]>([]);
  const [autoConvertedParamKey, setAutoConvertedParamKey] = useState<string | null>(null);
  const [resolvedCardIds, setResolvedCardIds] = useState<string[]>([]);
  const [selectionResetToken, setSelectionResetToken] = useState(0);
  const [sigShiftFlashKey, setSigShiftFlashKey] = useState(0);
  const [consensusHistory, setConsensusHistory] = useState<ConsensusItem[]>([]);
  const [preInjectionDeityDisplay, setPreInjectionDeityDisplay] = useState<{
    deity_scores?: Record<string, number>;
    deity_energy_axes?: Record<string, DeityEnergyAxis>;
  } | null>(null);
  const [showPreInjectionAbsSnapshot, setShowPreInjectionAbsSnapshot] = useState(false);
  const [confirmedDecisions, setConfirmedDecisions] = useState<ConfirmedDecisionItem[]>([]);
  const [confirmedDecisionIds, setConfirmedDecisionIds] = useState<string[]>(
    () => normalizedSnapshotDecisionIds(initialSnapshot?.decision_selection_ids),
  );
  useEffect(() => {
    if (!metadata?.pillars) {
      setPreInjectionDeityDisplay(null);
      setOrchestratorVfSkeletonLines([]);
      setOrchestratorCausalAuditPulse("");
      clearShadowPreview();
    }
  }, [metadata?.pillars, clearShadowPreview]);
  const urlDecisionHydrated = true;
  const isSnapshotRestoringRef = useRef(false);
  const reCalculateAbsSilentlyImplRef = useRef<() => Promise<void>>(async () => {});
  const runtimeConfigSerializedRef = useRef<string | null>(null);
  const pluginRecalcTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const silentRecalcInFlightRef = useRef(false);
  const inboxNonceHandledRef = useRef(0);
  const seedShieldSigRef = useRef<string | null>(null);
  const verdictRecalcBarrierRef = useRef(false);
  const silentRecalcDeferredRef = useRef(false);
  const reCalculateAbsRef = useRef<() => Promise<void>>(async () => {});
  const verdictDepsRef = useRef<VerdictExecutionDeps>({} as VerdictExecutionDeps);
  const { generateFinalVerdict } = useVerdictExecution(verdictDepsRef);
  const seedAnalysisDepsRef = useRef<SeedAnalysisDeps>({} as SeedAnalysisDeps);
  const { onSeedSubmit } = useSeedAnalysis(seedAnalysisDepsRef);
  const diagnosticDepsRef = useRef<StreamBoardDiagnosticDeps>({} as StreamBoardDiagnosticDeps);
  const { runStressTest, runGenderComparison } = useStreamBoardDiagnosticActions(diagnosticDepsRef);
  const drawerDepsRef = useRef<StreamBoardDrawerDeps>({} as StreamBoardDrawerDeps);
  const { openLogicDrawer, openLogicDrawerByDeity, onEvidenceItemClick, showVerdictHistory } = useStreamBoardDrawerActions(drawerDepsRef);
  const snapshotPersistDepsRef = useRef<StreamBoardSnapshotPersistDeps>({} as StreamBoardSnapshotPersistDeps);
  const { updateLogicDiff, setAsBaseline, persistSnapshot, scheduleInteractionHubPersist, markActiveSession } = useStreamBoardSnapshotPersist(snapshotPersistDepsRef);
  const prevActiveViewRef = useRef<ShellActiveView | null>(null);
  const isRestoringRef = useRef(false);
  const silentCtxRef = useRef<SilentBoardCtx>({
    consultationId: null,
    purePhysicsAudit: false,
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
    temporalGanzhiOverride: null,
  });
  const settersRef = useRef<SilentRecalcPhysicsSetters>({
    setMetadata: (_m) => {},
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
    setPatternThresholds: (_x) => {},
    setPatternThresholdsStatus: (_x) => {},
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
    setPatternThresholds,
    setPatternThresholdsStatus,
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
    setConfirmedDecisionIds,
    setResolvedCardIds,
    setSelectionResetToken,
  });

  const structureReasonLines = useMemo(() => {
    const chain = (finalStructureFinalDecisionV0 as { logical_reasoning_chain?: unknown } | null | undefined)
      ?.logical_reasoning_chain;
    if (!Array.isArray(chain)) return [] as string[];
    return chain.map((x) => String(x || "").trim()).filter(Boolean).slice(0, 40);
  }, [finalStructureFinalDecisionV0]);

  const verdictBodyLines = useMemo(() => {
    const raw = String(finalVerdictBody || "").trim();
    if (!raw) return [] as string[];
    return raw.split("\n").map((s) => s.trim()).filter(Boolean).slice(0, 120);
  }, [finalVerdictBody]);

  const patternCodexHeadline = useMemo((): string => {
    const meta = labState.snapshot?.physics_tensor?.meta as Record<string, unknown> | undefined;
    const hit = typeof meta?.hit_pattern_name === "string" ? meta.hit_pattern_name.trim() : "";
    const l2 = typeof meta?.l2_pattern_result_summary_v1 === "string" ? meta.l2_pattern_result_summary_v1.trim() : "";
    const raw = hit || l2 || "常规格";
    if (!raw || raw === "平常局" || raw.startsWith("平常局")) return "常规格";
    return raw;
  }, [labState.snapshot?.physics_tensor?.meta]);

  const patternNameZh = patternCodexHeadline;

  const structureStrategicRec = useMemo(() => {
    const rec = (finalStructureFinalDecisionV0 as { strategic_advice?: { recommendation?: string } } | null | undefined)
      ?.strategic_advice?.recommendation;
    const s = String(rec || "").trim();
    return s ? [s] : [];
  }, [finalStructureFinalDecisionV0]);

  const structureDivergenceFirst = useMemo(() => {
    const rep = (finalStructureFinalDecisionV0 as { plugin_conflict_report?: { divergence_notes?: string[] } } | null | undefined)
      ?.plugin_conflict_report?.divergence_notes;
    if (!Array.isArray(rep) || !rep.length) return [] as string[];
    const first = String(rep[0] || "").trim();
    return first ? [first] : [];
  }, [finalStructureFinalDecisionV0]);

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
      ...verdictBodyLines,
      ...finalLogicalEvidence,
      ...(finalVerdictChangeLog.physics_diff || []),
      ...(finalVerdictChangeLog.consensus_diff || []),
      ...(finalVerdictChangeLog.text_diff_hint ? [finalVerdictChangeLog.text_diff_hint] : []),
      ...structureReasonLines,
      ...(patternNameZh ? [patternNameZh] : []),
      ...structureStrategicRec,
      ...structureDivergenceFirst,
    ],
  });

  const decisionSignalToNoise = useMemo((): DecisionSignalToNoiseMeta | undefined => {
    const meta = labState.snapshot?.physics_tensor?.meta as Record<string, unknown> | undefined;
    const raw = meta?.decision_signal_to_noise;
    if (raw && typeof raw === "object") return raw as DecisionSignalToNoiseMeta;
    return undefined;
  }, [labState.snapshot?.physics_tensor?.meta]);

  const causalRouting = useMemo((): Record<string, unknown> | null => {
    const meta = labState.snapshot?.physics_tensor?.meta as Record<string, unknown> | undefined;
    const cr = meta?.causal_routing;
    return cr && typeof cr === "object" ? (cr as Record<string, unknown>) : null;
  }, [labState.snapshot?.physics_tensor?.meta]);

  const patternProfile = useMemo((): Record<string, unknown> | null => {
    const meta = labState.snapshot?.physics_tensor?.meta as Record<string, unknown> | undefined;
    const raw = meta?.pattern_profile;
    return raw && typeof raw === "object" && !Array.isArray(raw) ? (raw as Record<string, unknown>) : null;
  }, [labState.snapshot?.physics_tensor?.meta]);

  const l1JunctionFlagsForInbox = useMemo((): Record<string, unknown> | null => {
    const meta = labState.snapshot?.physics_tensor?.meta as Record<string, unknown> | undefined;
    const raw = meta?.l1_junction_flags;
    return raw && typeof raw === "object" && !Array.isArray(raw) ? (raw as Record<string, unknown>) : null;
  }, [labState.snapshot?.physics_tensor?.meta]);

  const physicsTensorForInbox = useMemo((): Record<string, unknown> | null => {
    const pt = labState.snapshot?.physics_tensor;
    return pt && typeof pt === "object" ? (pt as Record<string, unknown>) : null;
  }, [labState.snapshot?.physics_tensor]);

  const decisionJournal = useMemo((): DecisionJournalEntry[] => {
    const raw = labState.snapshot?.decision_journal;
    return normalizeDecisionJournalEntries(Array.isArray(raw) ? raw : []);
  }, [labState.snapshot?.decision_journal]);

  const cards = useMemo(
    () =>
      buildInboxCards({
        metadata,
        firstPromptText,
        auditorProposalCards,
        resolvedCardIds,
        decisionSelectionIds: confirmedDecisionIds,
        decisionJournal,
        t,
        decisionSignalToNoise,
        patternProfile,
        l1JunctionFlags: l1JunctionFlagsForInbox,
        physicsTensor: physicsTensorForInbox,
      }),
    [
      metadata,
      firstPromptText,
      auditorProposalCards,
      resolvedCardIds,
      confirmedDecisionIds,
      decisionJournal,
      t,
      decisionSignalToNoise,
      patternProfile,
      l1JunctionFlagsForInbox,
      physicsTensorForInbox,
    ],
  );
  const updateLogicDiffRef = useRef(updateLogicDiff);
  updateLogicDiffRef.current = updateLogicDiff;

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
  }, [labState.isFinalized, labState.finalizationReport?.hash, setResultLogs]);

  const pendingDecisionCount = cards.filter((card) => card.id !== "fallback-deep-scan").length;
  const l1Certified = Boolean(llmDiagnosticData?.alignment_score && llmDiagnosticData.alignment_score > 80) && pendingDecisionCount === 0;
  const auditInboxConfirmationBlockedReason = useMemo(() => {
    const needsAuditVoice = auditorProposalCards.some(
      (c) => c.cardType === "energy-patch" || c.cardType === "auditor-proposal",
    );
    if (!needsAuditVoice) return null;
    if (isTrustworthyPhysicsAuditDiagnosis(llmDiagnosticData?.diagnosis, llmDiagnosticData?.top_anomaly)) return null;
    return t("审计失败，请重算");
  }, [auditorProposalCards, llmDiagnosticData, t]);
  const hardRouteLogs = useMemo<string[]>(
    () => ((((physicsAudit as { trace?: { hard_route_logs?: string[] } } | null)?.trace?.hard_route_logs) || []) as string[]),
    [physicsAudit],
  );

  const persistSnapshotRef = useRef(persistSnapshot);
  persistSnapshotRef.current = persistSnapshot;



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

  async function applyPhysicsSqlPatch(sqlPatch: string): Promise<{ ok: boolean; error?: string }> {
    const result = await requestApplyPhysicsSqlPatch(API_BASE, sqlPatch);
    if (!result.ok) return { ok: false, error: result.error };
    setResultLogs((prev) => [
      ...prev,
      `🛠️ 已应用参数建议：${result.updated?.param_key ?? "unknown"} -> ${result.updated?.new_value ?? "?"}`,
    ]);
    return { ok: true };
  }

  function addPhysicsAuditSemanticDiagnosisToInbox(payload: {
    diagnosis: string;
    top_anomaly?: string;
    causal_reasoning?: string;
  }) {
    const chipLogs = (() => {
      const pt = labStateRef.current?.snapshot?.physics_tensor as Record<string, unknown> | undefined;
      const m = pt?.meta as Record<string, unknown> | undefined;
      const r = m?.mangpai_chip_logs;
      return Array.isArray(r) ? r.map((x) => String(x || "")) : [];
    })();
    const diagnosis = augmentDiagnosisWithMangpaiManifest(payload.diagnosis, chipLogs);
    const card = createPhysicsAuditSemanticDiagnosisCard({ ...payload, diagnosis });
    if (!card) return;
    setAuditorProposalCards((prev) => {
      const rest = prev.filter((item) => item.id !== "physics-audit-diag");
      return [card, ...rest];
    });
  }

  function addPhysicsAuditSemanticVerdictToInbox(payload: { diagnosis: string }) {
    const chipLogs = (() => {
      const pt = labStateRef.current?.snapshot?.physics_tensor as Record<string, unknown> | undefined;
      const m = pt?.meta as Record<string, unknown> | undefined;
      const r = m?.mangpai_chip_logs;
      return Array.isArray(r) ? r.map((x) => String(x || "")) : [];
    })();
    const diagnosis = augmentDiagnosisWithMangpaiManifest(payload.diagnosis, chipLogs);
    const card = createPhysicsAuditSemanticVerdictCard({ ...payload, diagnosis });
    if (!card) return;
    setAuditorProposalCards((prev) => {
      const rest = prev.filter((item) => item.id !== "physics-audit-semver");
      return [card, ...rest];
    });
  }

  function addAuditorProposalToInbox(proposal: LogicProposal) {
    const chipLogs = (() => {
      const pt = labStateRef.current?.snapshot?.physics_tensor as Record<string, unknown> | undefined;
      const m = pt?.meta as Record<string, unknown> | undefined;
      const r = m?.mangpai_chip_logs;
      return Array.isArray(r) ? r.map((x) => String(x || "")) : [];
    })();
    const withDx =
      typeof proposal.diagnosis === "string" && proposal.diagnosis.trim()
        ? { ...proposal, diagnosis: augmentDiagnosisWithMangpaiManifest(proposal.diagnosis, chipLogs) }
        : proposal;
    const coerced = coerceLogicProposalParamKey(withDx);
    const card = createAuditorProposalCard(coerced);
    if (!card) return;

    setAuditorProposalCards((prev) => {
      const alreadyAdded = prev.some((item) => item.proposal?.param_key === coerced.param_key);
      return alreadyAdded ? prev : [card, ...prev];
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

  const {
    clearLabPipelineForSeedDraft,
    setLang,
    applyCurrentSqlPatch,
    applyLabConfigAndRecalculate,
    revokeConfirmedDecision,
    reCalculateAbs,
  } = useStreamBoardPipeline({
    labStateRef,
    labState,
    setLastSeedPayload,
    persistLastSeedToStore,
    setMetadata,
    setStreamingText,
    setAuditItems,
    setResultLogs,
    setDeityScores,
    setDeityEnergyAxes,
    setDeityComponents,
    setDeityTraceDetails,
    setHoveredDeity,
    setPhysicsAudit,
    setPhysicsConfidence,
    setPhysicsEvidence,
    setShowPhysicsAudit,
    setAuditorProposalCards,
    setResolvedCardIds,
    setPhysicsParams,
    setGlobalEntropy,
    setPatternThresholds,
    setPatternThresholdsStatus,
    setConfirmedConflicts,
    setFirstPromptText,
    setTimeline,
    setLlmDiagnosticData,
    setFinalVerdictBody,
    setFinalVerdictChangeLog,
    setFinalVerdictVersionId,
    setFinalLogicalEvidence,
    setFinalWorkVector,
    setFinalTopologyGraphV1,
    setFinalStructureCandidatesV0,
    setFinalStructureFinalDecisionV0,
    setFinalVerdictHistory,
    setStressTestResult,
    setGenderComparisonResult,
    setConsensusHistory,
    setConfirmedDecisions,
    setConfirmedDecisionIds,
    resetSeedPreviewState,
    setConsultationId,
    setSelectionResetToken,
    setLogicDiff,
    mergeSnapshot,
    seedShieldSigRef,
    clearDecisionInbox,
    onSeedSubmit,
    langRef,
    setLangState,
    setUiLang,
    lastSeedPayloadRef,
    metadataRef,
    busyRef,
    isStreamingRef,
    isExecutingRef,
    isSnapshotRestoringRef,
    applyPhysicsSqlPatch,
    llmDiagnosticData,
    typewriterResultLine,
    labConfig,
    lastSeedPayload,
    confirmedDecisions,
    reCalculateAbsRef,
    reCalculateAbsSilentlyImplRef,
    setSigShiftFlashKey,
    activeView,
    busy,
    isStreaming,
    isExecuting,
  });

  const {
    onExecuteDecision,
    rerunFinalVerdictWithWeights,
    refreshVerdict,
    executeDecisionAndRefresh,
    runFinalVerdictSynthesis,
    scheduleSilentInternalLoopOnApprovalSelection,
    previewDecision,
    clearPreview,
  } = useStreamBoardExecution(executionCtxRef);

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
    appendSilentAnalyzeLogRef,
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
  }, [referenceYear, referenceYearRef, metadata, lastSeedPayload, busy, isStreaming, isExecuting, mergeSnapshot]);

  const seedSigForRecalcReset = useMemo(
    () => (lastSeedPayload ? seedPayloadSignature(lastSeedPayload) : ""),
    [lastSeedPayload],
  );
  useEffect(() => {
    referenceYearRecalcInitRef.current = false;
  }, [seedSigForRecalcReset]);

  useEffect(() => {
    if (busy || isStreaming || isExecuting) return;
    if (!metadata || !lastSeedPayload) return;
    if (labStateRef.current.isFinalized) return;
    if (!referenceYearRecalcInitRef.current) {
      referenceYearRecalcInitRef.current = true;
      return;
    }
    const t = window.setTimeout(() => {
      void reCalculateAbsRef.current();
    }, 480);
    return () => window.clearTimeout(t);
  }, [referenceYear, metadata, lastSeedPayload, busy, isStreaming, isExecuting]);

  useEffect(() => {
    const onSilentRecalc = () => {
      void reCalculateAbsRef.current();
    };
    window.addEventListener(SILENT_PHYSICS_RECALC_EVENT, onSilentRecalc);
    return () => window.removeEventListener(SILENT_PHYSICS_RECALC_EVENT, onSilentRecalc);
  }, []);

  langRef.current = lang;
  lastSeedPayloadRef.current = lastSeedPayload;
  metadataRef.current = metadata;
  busyRef.current = busy;
  isStreamingRef.current = isStreaming;
  isExecutingRef.current = isExecuting;
  isRestoringRef.current = isRestoring;
  silentCtxRef.current = {
    consultationId,
    purePhysicsAudit,
    labConfig,
    pluginSwitches,
    pluginWeights,
    lang,
    baselineMetrics,
    confirmedDecisionIds,
    temporalGanzhiOverride: timeline
      ? { liunian: String(timeline.liunian ?? ""), dayun: String(timeline.dayun ?? "") }
      : null,
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
    setPatternThresholds,
    setPatternThresholdsStatus,
  };

  verdictDepsRef.current = {
    silentRecalcInFlightRef,
    verdictRecalcBarrierRef,
    silentRecalcDeferredRef,
    bumpSyncBarrierSeq,
    reCalculateAbsRef,
    metadata,
    deityScores,
    deityEnergyAxes,
    deityComponents,
    deityTraceDetails,
    physicsAudit,
    llmDiagnosticData,
    timeline,
    consensusHistory,
    finalVerdictBody,
    lastConclusionText,
    finalLogicalEvidence,
    consultationId,
    pluginSwitches,
    purePhysicsAudit,
    pluginWeights,
    lang,
    setResultLogs,
    setStreamingText,
  };

  seedAnalysisDepsRef.current = {
    persistLastSeedToStore,
    setLastSeedPayload,
    setMetadata,
    consensusHistory,
    setBusy,
    setIsStreaming,
    setAutoConvertedParamKey,
    setStreamingText,
    setAuditItems,
    setResultLogs,
    setDeityScores,
    setDeityEnergyAxes,
    setDeityComponents,
    setDeityTraceDetails,
    setHoveredDeity,
    setPhysicsAudit,
    setPhysicsConfidence,
    setPhysicsEvidence,
    setShowPhysicsAudit,
    setAuditorProposalCards,
    setResolvedCardIds,
    setPhysicsParams,
    setGlobalEntropy,
    setPatternThresholds,
    setPatternThresholdsStatus,
    setConfirmedConflicts,
    setFirstPromptText,
    setTimeline,
    setLlmDiagnosticData,
    setFinalVerdictBody,
    setFinalVerdictChangeLog,
    setFinalVerdictVersionId,
    setFinalLogicalEvidence,
    setFinalWorkVector,
    setFinalTopologyGraphV1,
    setFinalStructureCandidatesV0,
    setFinalStructureFinalDecisionV0,
    setFinalVerdictHistory,
    setStressTestResult,
    setGenderComparisonResult,
    setConsensusHistory,
    refreshHealth,
    t,
    referenceYearRef,
    consultationId,
    setConsultationId,
    labConfig,
    pluginSwitches,
    lang,
    markActiveSession,
    resetSeedPreviewState,
    confirmedDecisionIds,
    baselineMetrics,
    persistSnapshot,
    appendSystemAuditLog,
    getMetadata: () => metadataRef.current,
    addAuditorProposalToInbox,
    addPhysicsAuditSemanticDiagnosisToInbox,
    addPhysicsAuditSemanticVerdictToInbox,
    typewriter,
    updateLogicDiff,
    scheduleInteractionHubPersist,
    llmModelName,
    mergeSnapshot,
    seedShieldSigRef,
    reportPipelineEvent,
    purePhysicsAudit,
  };

  diagnosticDepsRef.current = {
    metadata,
    lastSeedPayload,
    labConfig,
    pluginSwitches,
    purePhysicsAudit,
    pluginWeights,
    lang,
    finalStructureFinalDecisionV0: finalStructureFinalDecisionV0 as Record<string, unknown> | null,
    referenceYearRef,
    setStressTestResult,
    setGenderComparisonResult,
    setResultLogs,
  };

  drawerDepsRef.current = {
    deityScores,
    deityTraceDetails,
    finalVerdictHistory,
    setLogicDrawerTitle,
    setLogicDrawerFocus,
    setLogicDrawerDetails,
    setLogicDrawerTrace,
    setLogicDrawerOpen,
  };

  snapshotPersistDepsRef.current = {
    labStateRef,
    labState,
    mergeSnapshot,
    setBaselineMetrics,
    baselineMetrics,
    setLogicDiff,
    setResultLogs,
    finalWorkVector: finalWorkVector as Record<string, unknown> | null,
    globalEntropy,
    isSnapshotRestoringRef,
    isRestoring,
    lastSeedPayload,
    resolvedCardIds,
    confirmedDecisionIds,
    decisionJournal,
    health,
    i18nCalls,
    auditItems,
    resultLogs,
    cards,
    consultationId,
    llmDiagnosticData: llmDiagnosticData as Record<string, unknown> | null,
    finalVerdictBody: finalVerdictBody || undefined,
    finalVerdictChangeLog,
    finalLogicalEvidence,
    finalTopologyGraphV1: finalTopologyGraphV1 as Record<string, unknown> | null,
    finalStructureCandidatesV0: finalStructureCandidatesV0 as Record<string, unknown> | null,
    finalStructureFinalDecisionV0: finalStructureFinalDecisionV0 as Record<string, unknown> | null,
    finalVerdictVersionId,
  };

  executionCtxRef.current = {
    t,
    lang,
    apiBase: API_BASE,
    metadata,
    consultationId,
    confirmedDecisionIds,
    baselineMetrics,
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
    bumpVerdictBodyRenderNonce: () => setVerdictBodyRenderNonce((n) => n + 1),
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
    finalVerdictVersionId,
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
    mergeLabSnapshot: mergeSnapshot,
    setMetadata,
    setDeityScores,
    setDeityEnergyAxes,
    physicsTensor: (labState.snapshot?.physics_tensor as Record<string, unknown> | null) ?? null,
    llmDiagnosticData,
    pipelinePhase,
    reportPipelineEvent,
    labConfig,
    pluginSwitches,
    purePhysicsAudit,
    referenceYearRef,
    timeline,
    isFinalized: labState.isFinalized,
    setDeityComponents,
    setDeityTraceDetails,
    setPhysicsAudit,
    setPhysicsConfidence,
    setPhysicsEvidence,
    setPhysicsParams,
    setGlobalEntropy,
    setPatternThresholds,
    setPatternThresholdsStatus,
    consensusHistory,
    setLlmDiagnosticData,
    addPhysicsAuditSemanticDiagnosisToInbox,
    addPhysicsAuditSemanticVerdictToInbox,
    addAuditorProposalToInbox,
    setAutoConvertedParamKey,
    setPreInjectionDeityDisplay,
    setOrchestratorVfSkeletonLines,
    setOrchestratorCausalAuditPulse,
    setLabShadowPreview: setShadowPreview,
    clearLabShadowPreview: clearShadowPreview,
    deityScores,
    setNarrativeReshapeActive,
    cards,
    snapshotMetadata: (labState.snapshot?.metadata as Record<string, unknown> | null | undefined) ?? null,
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

  const energyFlowAudit = useMemo(() => {
    const meta = labState.snapshot?.physics_tensor?.meta as Record<string, unknown> | undefined;
    const raw = meta?.energy_flow_audit;
    return raw && typeof raw === "object" && !Array.isArray(raw) ? (raw as Record<string, unknown>) : null;
  }, [labState.snapshot?.physics_tensor]);

  useEffect(() => {
    if (!preInjectionDeityDisplay) setShowPreInjectionAbsSnapshot(false);
  }, [preInjectionDeityDisplay]);

  useEffect(() => {
    if (labState.isFinalized) setPipelinePhase("DECIDED");
    else setPipelinePhase((p) => (p === "DECIDED" ? "READY" : p));
  }, [labState.isFinalized]);

  const mangpaiChipLogsForTrace = useMemo(() => {
    const meta = labState.snapshot?.physics_tensor?.meta as Record<string, unknown> | undefined;
    if (!meta) return [] as string[];
    const raw = meta.mangpai_chip_logs;
    return Array.isArray(raw) ? raw.map((x) => String(x)).filter(Boolean) : [];
  }, [labState.snapshot?.physics_tensor?.meta]);

  const conflictScanLabels = useMemo(() => {
    const pts = (metadata as { conflict_matrix?: { points?: unknown[] } } | null)?.conflict_matrix?.points;
    if (!Array.isArray(pts)) return [] as string[];
    return pts
      .map((p) => {
        if (p && typeof p === "object" && "detail" in p) return String((p as { detail?: string }).detail || "").trim();
        return "";
      })
      .filter(Boolean)
      .slice(0, 32);
  }, [metadata]);

  const verdictSkeletonContentKey = useMemo(() => {
    const sk = (metadata as { verdict_anchor_layer?: { verdict_skeleton?: string } } | null)?.verdict_anchor_layer
      ?.verdict_skeleton;
    return typeof sk === "string" ? sk : "";
  }, [metadata]);

  return {
    lang,
    setLang,
    busy,
    pipelinePhase,
    narrativeReshapeActive,
    orchestratorVfSkeletonLines,
    orchestratorCausalAuditPulse,
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
    auditInboxConfirmationBlockedReason,
    llmDiagnosticData,
    physicsParams,
    globalEntropy,
    causalRouting,
    preInjectionDeityDisplay,
    showPreInjectionAbsSnapshot,
    setShowPreInjectionAbsSnapshot,
    mangpaiChipLogsForTrace,
    conflictScanLabels,
    verdictSkeletonContentKey,
    patternProfile,
    patternCodexHeadline,
    energyFlowAudit,
    patternThresholds,
    patternThresholdsStatus,
    auditorProposalCards,
    autoConvertedParamKey,
    consensusHistory,
    cards,
    resultLogs,
    streamingText,
    verdictBodyRenderNonce,
    finalVerdictBody,
    finalVerdictChangeLog,
    finalLogicalEvidence,
    finalWorkVector,
    finalTopologyGraphV1,
    finalStructureCandidatesV0,
    finalStructureFinalDecisionV0,
    confirmedDecisions,
    confirmedDecisionIds,
    decisionJournal,
    mergeLabSnapshot: mergeSnapshot,
    setConfirmedDecisionIds,
    urlDecisionHydrated,
    snapshotUrlTag,
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
    purePhysicsAudit: Boolean(purePhysicsAudit),
    physicsTensorSnapshot: (labState.snapshot?.physics_tensor as Record<string, unknown> | null) ?? null,
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
    addPhysicsAuditSemanticDiagnosisToInbox,
    onExecuteDecision,
    previewDecision,
    clearPreview,
    scheduleSilentInternalLoopOnApprovalSelection,
    runFinalVerdictSynthesis,
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
