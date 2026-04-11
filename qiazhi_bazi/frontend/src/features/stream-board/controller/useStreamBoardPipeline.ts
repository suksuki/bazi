import { useCallback, useRef, useEffect } from "react";
import { type Lang } from "@/types/bazi";

export interface StreamBoardPipelineParams {
  labStateRef: React.MutableRefObject<any>;
  labState: any;
  setLastSeedPayload: (p: any) => void;
  persistLastSeedToStore: (p: any) => void;
  setMetadata: (m: any) => void;
  setStreamingText: (s: string) => void;
  setAuditItems: React.Dispatch<React.SetStateAction<any[]>>;
  setResultLogs: React.Dispatch<React.SetStateAction<any[]>>;
  setDeityScores: (s: any) => void;
  setDeityEnergyAxes: (s: any) => void;
  setDeityComponents: (c: any) => void;
  setDeityTraceDetails: (d: any) => void;
  setHoveredDeity: (d: any) => void;
  setPhysicsAudit: (a: any) => void;
  setPhysicsConfidence: (c: any) => void;
  setPhysicsEvidence: (e: any[]) => void;
  setShowPhysicsAudit: (s: boolean) => void;
  setAuditorProposalCards: (c: any[]) => void;
  setResolvedCardIds: (c: any[]) => void;
  setPhysicsParams: (p: any) => void;
  setGlobalEntropy: (e: any) => void;
  setConfirmedConflicts: (c: any[]) => void;
  setFirstPromptText: (p: string) => void;
  setTimeline: (t: any) => void;
  setLlmDiagnosticData: (d: any) => void;
  setFinalVerdictBody: (b: string) => void;
  setFinalVerdictChangeLog: (c: any) => void;
  setFinalVerdictVersionId: (v: string) => void;
  setFinalLogicalEvidence: (e: any[]) => void;
  setFinalWorkVector: (w: any) => void;
  setFinalTopologyGraphV1: (g: any) => void;
  setFinalStructureCandidatesV0: (c: any) => void;
  setFinalStructureFinalDecisionV0: (d: any) => void;
  setFinalVerdictHistory: (h: any[]) => void;
  setStressTestResult: (r: any) => void;
  setGenderComparisonResult: (r: any) => void;
  setConsensusHistory: (h: any[]) => void;
  setConfirmedDecisions: (d: any[]) => void;
  setConfirmedDecisionIds: (ids: any) => void;
  resetSeedPreviewState: () => void;
  setConsultationId: (id: any) => void;
  setSelectionResetToken: (t: any) => void;
  setLogicDiff: (d: any) => void;
  mergeSnapshot: (s: any) => void;
  clearDecisionInbox: () => void;
  onSeedSubmit: (p: any) => Promise<void>;
  langRef: React.MutableRefObject<Lang>;
  setLangState: (l: Lang) => void;
  setUiLang: (l: Lang) => void;
  lastSeedPayloadRef: React.MutableRefObject<any>;
  metadataRef: React.MutableRefObject<any>;
  busyRef: React.MutableRefObject<boolean>;
  isStreamingRef: React.MutableRefObject<boolean>;
  isExecutingRef: React.MutableRefObject<boolean>;
  isSnapshotRestoringRef: React.MutableRefObject<boolean>;
  applyPhysicsSqlPatch: (s: string) => Promise<any>;
  llmDiagnosticData: any;
  typewriterResultLine: (s: string) => Promise<void>;
  labConfig: any;
  lastSeedPayload: any;
  confirmedDecisions: any[];
  reCalculateAbsRef: React.MutableRefObject<any>;
  reCalculateAbsSilentlyImplRef: React.MutableRefObject<any>;
  setSigShiftFlashKey: (v: any) => void;
  activeView: string;
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
    setSelectionResetToken((v: number) => v + 1);
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
  }, [mergeSnapshot, clearDecisionInbox, persistLastSeedToStore, resetSeedPreviewState,
      labStateRef, setLastSeedPayload, setMetadata, setStreamingText, setAuditItems, setResultLogs, setDeityScores, setDeityEnergyAxes, setDeityComponents, setDeityTraceDetails, setHoveredDeity, setPhysicsAudit, setPhysicsConfidence, setPhysicsEvidence, setShowPhysicsAudit, setAuditorProposalCards, setResolvedCardIds, setPhysicsParams, setGlobalEntropy, setConfirmedConflicts, setFirstPromptText, setTimeline, setLlmDiagnosticData, setFinalVerdictBody, setFinalVerdictChangeLog, setFinalVerdictVersionId, setFinalLogicalEvidence, setFinalWorkVector, setFinalTopologyGraphV1, setFinalStructureCandidatesV0, setFinalStructureFinalDecisionV0, setFinalVerdictHistory, setStressTestResult, setGenderComparisonResult, setConsensusHistory, setConfirmedDecisions, setConfirmedDecisionIds, setConsultationId, setSelectionResetToken, setLogicDiff]);

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
    setResultLogs((prev: any) => [
      ...prev,
      `🧪 实验参数已应用：luck=${labConfig.WEIGHT_LUCK}, year=${labConfig.WEIGHT_YEAR}, climate=${labConfig.CLIMATE_INTENSITY}`,
    ]);
    await onSeedSubmit(lastSeedPayload);
  }

  async function revokeConfirmedDecision(id: string) {
    const nextDecisions = confirmedDecisions.filter((item) => item.id !== id);
    setConfirmedDecisions(nextDecisions);
    setConfirmedDecisionIds((prev: any) => prev.filter((item: string) => item !== id));
  }

  const reCalculateAbs = useCallback(async () => {
    await reCalculateAbsSilentlyImplRef.current();
  }, [reCalculateAbsSilentlyImplRef]);
  reCalculateAbsRef.current = reCalculateAbs;
  reCalculateAbsRef.current = reCalculateAbs;

  const runtimeConfigSerializedRef = useRef<string | null>(null);
  const pluginRecalcTimerRef = useRef<number | null>(null);
  const prevActiveViewRef = useRef<string | null>(null);

  const onPluginConfigChange = useCallback(() => {
    const prevJson = runtimeConfigSerializedRef.current;
    if (prevJson) {
      try {
        const prevCfg = JSON.parse(prevJson) as { pluginWeights?: any };
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
          setSigShiftFlashKey((k: number) => k + 1);
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
