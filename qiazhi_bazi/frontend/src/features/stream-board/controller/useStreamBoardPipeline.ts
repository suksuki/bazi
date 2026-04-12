import { useCallback, useEffect, useRef, type Dispatch, type MutableRefObject, type SetStateAction } from "react";
import type { AuditItem } from "@/components/AuditSidebar";
import type { ShellActiveView } from "@/components/layout/ActiveViewContext";
import type { Lang, BaziMetadata, TimelineSnapshot } from "@/types/bazi";
import type { LabStoreState } from "@/features/stream-board/stores/useLabStore";
import type { ConfirmedDecisionItem, ConsensusItem } from "@/features/stream-board/controller/streamBoardTypes";
import type {
  DeityComponent,
  DeityEnergyAxis,
  FinalVerdictChangeLog,
  FinalVerdictHistoryItem,
  InboxCard,
  LogicDiff,
  LlmDiagnosticData,
  PhysicsLabConfig,
  PluginWeights,
  SeedPayload,
} from "@/features/stream-board/models";

export interface StreamBoardPipelineParams {
  labStateRef: MutableRefObject<LabStoreState>;
  labState: LabStoreState;
  setLastSeedPayload: Dispatch<SetStateAction<SeedPayload | null>>;
  persistLastSeedToStore: (p: SeedPayload | null) => void;
  setMetadata: Dispatch<SetStateAction<BaziMetadata | null>>;
  setStreamingText: Dispatch<SetStateAction<string>>;
  setAuditItems: Dispatch<SetStateAction<AuditItem[]>>;
  setResultLogs: Dispatch<SetStateAction<string[]>>;
  setDeityScores: Dispatch<SetStateAction<Record<string, number>>>;
  setDeityEnergyAxes: Dispatch<SetStateAction<Record<string, DeityEnergyAxis>>>;
  setDeityComponents: Dispatch<SetStateAction<Record<string, DeityComponent>>>;
  setDeityTraceDetails: Dispatch<SetStateAction<Record<string, Record<string, unknown>>>>;
  setHoveredDeity: Dispatch<SetStateAction<string | undefined>>;
  setPhysicsAudit: Dispatch<SetStateAction<Record<string, unknown> | null>>;
  setPhysicsConfidence: Dispatch<SetStateAction<number | null>>;
  setPhysicsEvidence: Dispatch<SetStateAction<string[]>>;
  setShowPhysicsAudit: Dispatch<SetStateAction<boolean>>;
  setAuditorProposalCards: Dispatch<SetStateAction<InboxCard[]>>;
  setResolvedCardIds: Dispatch<SetStateAction<string[]>>;
  setPhysicsParams: Dispatch<SetStateAction<Record<string, number>>>;
  setGlobalEntropy: Dispatch<SetStateAction<number | null>>;
  setConfirmedConflicts: Dispatch<SetStateAction<string[]>>;
  setFirstPromptText: Dispatch<SetStateAction<string>>;
  setTimeline: Dispatch<SetStateAction<TimelineSnapshot | null>>;
  setLlmDiagnosticData: Dispatch<SetStateAction<LlmDiagnosticData | null>>;
  setFinalVerdictBody: Dispatch<SetStateAction<string>>;
  setFinalVerdictChangeLog: Dispatch<SetStateAction<FinalVerdictChangeLog>>;
  setFinalVerdictVersionId: Dispatch<SetStateAction<string>>;
  setFinalLogicalEvidence: Dispatch<SetStateAction<string[]>>;
  setFinalWorkVector: Dispatch<SetStateAction<Record<string, unknown> | null>>;
  setFinalTopologyGraphV1: Dispatch<SetStateAction<Record<string, unknown> | null>>;
  setFinalStructureCandidatesV0: Dispatch<SetStateAction<Record<string, unknown> | null>>;
  setFinalStructureFinalDecisionV0: Dispatch<SetStateAction<Record<string, unknown> | null>>;
  setFinalVerdictHistory: Dispatch<SetStateAction<FinalVerdictHistoryItem[]>>;
  setStressTestResult: Dispatch<SetStateAction<Record<string, unknown> | null>>;
  setGenderComparisonResult: Dispatch<SetStateAction<Record<string, unknown> | null>>;
  setConsensusHistory: Dispatch<SetStateAction<ConsensusItem[]>>;
  setConfirmedDecisions: Dispatch<SetStateAction<ConfirmedDecisionItem[]>>;
  setConfirmedDecisionIds: Dispatch<SetStateAction<string[]>>;
  resetSeedPreviewState: () => void;
  setConsultationId: Dispatch<SetStateAction<number | null>>;
  setSelectionResetToken: Dispatch<SetStateAction<number>>;
  setLogicDiff: Dispatch<SetStateAction<LogicDiff>>;
  mergeSnapshot: (diff: Record<string, unknown>) => void;
  clearDecisionInbox: () => void;
  onSeedSubmit: (p: SeedPayload) => Promise<void>;
  langRef: MutableRefObject<Lang>;
  setLangState: (l: Lang) => void;
  setUiLang: (l: Lang) => void;
  lastSeedPayloadRef: MutableRefObject<SeedPayload | null>;
  metadataRef: MutableRefObject<BaziMetadata | null>;
  busyRef: MutableRefObject<boolean>;
  isStreamingRef: MutableRefObject<boolean>;
  isExecutingRef: MutableRefObject<boolean>;
  isSnapshotRestoringRef: MutableRefObject<boolean>;
  applyPhysicsSqlPatch: (s: string) => Promise<{ ok: boolean; error?: string }>;
  llmDiagnosticData: LlmDiagnosticData | null;
  typewriterResultLine: (s: string, delayMs?: number) => Promise<void>;
  labConfig: PhysicsLabConfig;
  lastSeedPayload: SeedPayload | null;
  confirmedDecisions: ConfirmedDecisionItem[];
  reCalculateAbsRef: MutableRefObject<() => Promise<void>>;
  reCalculateAbsSilentlyImplRef: MutableRefObject<() => Promise<void>>;
  setSigShiftFlashKey: Dispatch<SetStateAction<number>>;
  activeView: ShellActiveView;
  busy: boolean;
  isStreaming: boolean;
  isExecuting: boolean;
}

export function useStreamBoardPipeline(params: StreamBoardPipelineParams) {
  const {
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
  } = params;

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
      first_observation_llm: undefined,
      physics_auditor_llm: undefined,
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
  }, [
    mergeSnapshot,
    clearDecisionInbox,
    persistLastSeedToStore,
    resetSeedPreviewState,
    labStateRef,
    setLastSeedPayload,
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
    setConsultationId,
    setSelectionResetToken,
    setLogicDiff,
  ]);

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
    [setUiLang, langRef, setLangState, lastSeedPayloadRef, metadataRef, busyRef, isStreamingRef, isExecutingRef],
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
  }, [labState.causalRevertNonce, labState.lastSeedPayload, isSnapshotRestoringRef]);

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

  async function revokeConfirmedDecision(id: string) {
    const nextDecisions = confirmedDecisions.filter((item) => item.id !== id);
    setConfirmedDecisions(nextDecisions);
    setConfirmedDecisionIds((prev) => prev.filter((item) => item !== id));
  }

  const reCalculateAbs = useCallback(async () => {
    await reCalculateAbsSilentlyImplRef.current();
  }, [reCalculateAbsSilentlyImplRef]);
  reCalculateAbsRef.current = reCalculateAbs;

  const runtimeConfigSerializedRef = useRef<string | null>(null);
  /** 浏览器下 setTimeout 句柄为 number；避免与 NodeJS.Timeout 混用导致类型冲突 */
  const pluginRecalcTimerRef = useRef<number | null>(null);
  const prevActiveViewRef = useRef<ShellActiveView | null>(null);

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
  }, [reCalculateAbs, labStateRef, setSigShiftFlashKey]);

  useEffect(() => {
    const sig = JSON.stringify(labState.runtimeConfig);
    if (runtimeConfigSerializedRef.current === null) {
      runtimeConfigSerializedRef.current = sig;
    }
    const prevView = prevActiveViewRef.current;
    /** 离开机房进入实验室/黑匣子时立即补一次重算，避免防抖尚未触发时快照滞后。 */
    const shouldFlushViewEntry =
      prevView !== null &&
      prevView !== activeView &&
      prevView === "admin" &&
      (activeView === "lab" || activeView === "debug");
    prevActiveViewRef.current = activeView;

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

    if (shouldFlushViewEntry) {
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
      pluginRecalcTimerRef.current = window.setTimeout(runNow, 280);
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

  return {
    clearLabPipelineForSeedDraft,
    setLang,
    applyCurrentSqlPatch,
    applyLabConfigAndRecalculate,
    revokeConfirmedDecision,
    reCalculateAbs,
  };
}
