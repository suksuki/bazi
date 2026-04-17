import { useCallback } from "react";
import type { LabLlmRoundSnapshot, LabStoreState } from "@/features/stream-board/stores/LabSessionContext";
import type { SeedPayload, InboxCard, FinalVerdictChangeLog, LogicDiff } from "@/features/stream-board/models";
import type { MetricSnapshot } from "./streamBoardTypes";
import type { DecisionJournalEntry } from "@/features/stream-board/decisionJournal";
import { normalizeDecisionJournalEntries } from "@/features/stream-board/decisionJournal";
import {
  extractMetricSnapshotFromPhysics,
  seedPayloadSignature,
  normalizeDecisionIds,
  extractInteractionHubMangpai,
} from "./streamBoardPure";

export interface StreamBoardSnapshotPersistDeps {
  labStateRef: React.MutableRefObject<LabStoreState>;
  labState: LabStoreState;
  mergeSnapshot: (diff: Record<string, unknown>) => void;
  setBaselineMetrics: React.Dispatch<React.SetStateAction<MetricSnapshot | null>>;
  baselineMetrics: MetricSnapshot | null;
  setLogicDiff: (diff: LogicDiff) => void;
  setResultLogs: React.Dispatch<React.SetStateAction<string[]>>;
  finalWorkVector: Record<string, unknown> | null;
  globalEntropy: number | null;
  isSnapshotRestoringRef: React.MutableRefObject<boolean>;
  isRestoring: boolean;
  lastSeedPayload: SeedPayload | null;
  resolvedCardIds: string[];
  confirmedDecisionIds: string[];
  health: { dbOk: boolean; llmOk: boolean };
  i18nCalls: number;
  auditItems: Array<{ id?: string; step?: string; role?: string; action?: string; timestamp?: string }>;
  resultLogs: string[];
  cards: InboxCard[];
  decisionJournal: DecisionJournalEntry[];
  consultationId: number | null;
  llmDiagnosticData: Record<string, unknown> | null;
  finalVerdictBody?: string;
  finalVerdictChangeLog?: FinalVerdictChangeLog;
  finalLogicalEvidence?: string[];
  finalTopologyGraphV1?: Record<string, unknown> | null;
  finalStructureCandidatesV0?: Record<string, unknown> | null;
  finalStructureFinalDecisionV0?: Record<string, unknown> | null;
  finalVerdictVersionId?: string;
}

export function useStreamBoardSnapshotPersist(depsRef: React.MutableRefObject<StreamBoardSnapshotPersistDeps>) {
  const updateLogicDiff = useCallback((current: MetricSnapshot, forceBaseline = false): LogicDiff => {
    const deps = depsRef.current;
    const baselineFromStore = (() => {
      const b = deps.labState.snapshot?.baseline_snapshot;
      if (!b) return null;
      const absLoss = typeof b.abs_loss_total === "number"
        ? b.abs_loss_total
        : extractMetricSnapshotFromPhysics((b.physics_tensor || null) as Record<string, unknown> | null).absLossTotal;
      const entropy = typeof b.global_entropy === "number"
        ? b.global_entropy
        : extractMetricSnapshotFromPhysics((b.physics_tensor || null) as Record<string, unknown> | null).entropy;
      return { absLossTotal: absLoss ?? null, entropy: entropy ?? null } as MetricSnapshot;
    })();
    const shouldSetBaseline = forceBaseline || (!baselineFromStore && !deps.baselineMetrics);
    const base = shouldSetBaseline ? current : (baselineFromStore || deps.baselineMetrics);
    if (shouldSetBaseline) deps.setBaselineMetrics(current);
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
    deps.setLogicDiff(nextDiff);
    deps.mergeSnapshot({ logic_diff: nextDiff });
    if (typeof process !== "undefined" && process.env.NODE_ENV === "development") {
      // 基线遥测：UI 已降噪，开发态仍可在控制台审计 logic_diff
      // eslint-disable-next-line no-console
      console.debug("[telemetry] logic_diff", nextDiff);
    }
    return nextDiff;
  }, [depsRef]);

  const setAsBaseline = useCallback(() => {
    const deps = depsRef.current;
    const currentTensor = (deps.labState.snapshot?.physics_tensor || null) as Record<string, unknown> | null;
    const snapshot: MetricSnapshot = {
      absLossTotal: typeof (deps.finalWorkVector as { backfire_risk?: unknown } | null)?.backfire_risk === "number"
        ? Number((deps.finalWorkVector as { backfire_risk?: number }).backfire_risk)
        : null,
      entropy: deps.globalEntropy,
    };
    deps.setBaselineMetrics(snapshot);
    deps.setLogicDiff({
      baseline_abs_loss_total: snapshot.absLossTotal,
      current_abs_loss_total: snapshot.absLossTotal,
      abs_delta: 0,
      baseline_entropy: snapshot.entropy,
      current_entropy: snapshot.entropy,
      entropy_delta: 0,
    });
    deps.mergeSnapshot({
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
    deps.setResultLogs((prev) => [...prev, "因果锚点已固化"]);
  }, [depsRef]);

  const buildInteractionHub = useCallback((opts?: {
    consultationIdOverride?: number | null;
    healthOverride?: { dbOk: boolean; llmOk: boolean };
    auditorBriefingOverride?: Record<string, unknown> | null;
  }) => {
    const deps = depsRef.current;
    const h = opts?.healthOverride || deps.health;
    const llmDiagnosticData = deps.llmDiagnosticData as any;
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
      consultation_id: opts?.consultationIdOverride ?? deps.consultationId ?? null,
      health: {
        db_ok: Boolean(h.dbOk),
        llm_ok: Boolean(h.llmOk),
      },
      i18n_calls: deps.i18nCalls,
      audit_items: deps.auditItems.map((item) => ({
        id: item.id,
        step: item.step || "",
        role: item.role,
        action: item.action,
        timestamp: item.timestamp,
      })),
      result_logs: deps.resultLogs.slice(-24),
      pending_cards: deps.cards
        .filter((card) => card.id !== "fallback-deep-scan")
        .map((card) => ({
          id: card.id,
          title: card.title,
          card_type: card.cardType || "conflict",
        })),
      resolved_card_ids: deps.resolvedCardIds.slice(-120),
      auditor_briefing: briefing || undefined,
    };
  }, [depsRef]);

  const persistSnapshot = useCallback((payload: {
    physics_tensor: Record<string, unknown>;
    metadata?: Record<string, unknown>;
    timeline?: Record<string, unknown> | null;
    llm_prompt?: string;
    audit_summary?: unknown;
    consultationIdOverride?: number | null;
    healthOverride?: { dbOk: boolean; llmOk: boolean };
    auditorBriefingOverride?: Record<string, unknown> | null;
    seedSignatureOverride?: string | null;
    first_observation_llm?: LabLlmRoundSnapshot;
    physics_auditor_llm?: LabLlmRoundSnapshot;
    finalVerdictOverride?: {
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
    };
  }) => {
    const deps = depsRef.current;
    if (deps.isSnapshotRestoringRef.current || deps.isRestoring) return;
    if (deps.labStateRef.current.isFinalized) return;
    const previousFinalVerdict = (deps.labState.snapshot?.final_verdict || null) as Record<string, unknown> | null;
    const seedSig =
      payload.seedSignatureOverride !== undefined
        ? payload.seedSignatureOverride
        : seedPayloadSignature(deps.lastSeedPayload);
    const ihOptions = {
        consultationIdOverride: payload.consultationIdOverride,
        healthOverride: payload.healthOverride,
        auditorBriefingOverride: payload.auditorBriefingOverride,
    };
    deps.mergeSnapshot({
      active_session_id: payload.consultationIdOverride != null
        ? String(payload.consultationIdOverride)
        : (deps.labState.snapshot?.active_session_id || `session-${Date.now()}`),
      physics_tensor: payload.physics_tensor,
      metadata: payload.metadata,
      timeline: payload.timeline ?? null,
      llm_prompt: payload.llm_prompt || "",
      ...(payload.first_observation_llm != null ? { first_observation_llm: payload.first_observation_llm } : {}),
      ...(payload.physics_auditor_llm != null ? { physics_auditor_llm: payload.physics_auditor_llm } : {}),
      audit_summary: payload.audit_summary,
      ...(seedSig ? { seed_signature: seedSig } : {}),
      resolved_card_ids: deps.resolvedCardIds.slice(-240),
      decision_selection_ids: normalizeDecisionIds(deps.confirmedDecisionIds),
      decision_journal: normalizeDecisionJournalEntries(deps.decisionJournal as unknown[]),
      interaction_hub: {
        ...buildInteractionHub(ihOptions),
        ...extractInteractionHubMangpai(payload.physics_tensor),
      },
      final_verdict: payload.finalVerdictOverride || previousFinalVerdict || {
        body: deps.finalVerdictBody,
        change_log: deps.finalVerdictChangeLog,
        logical_evidence: deps.finalLogicalEvidence,
        work_vector: deps.finalWorkVector,
        topology_graph_v1: deps.finalTopologyGraphV1,
        structure_candidates_v0: deps.finalStructureCandidatesV0,
        structure_final_decision_v0: deps.finalStructureFinalDecisionV0,
        version_id: deps.finalVerdictVersionId,
      },
    });
  }, [depsRef, buildInteractionHub]);

  const scheduleInteractionHubPersist = useCallback(() => {
    window.setTimeout(() => {
      const deps = depsRef.current;
      if (deps.labStateRef.current.isFinalized) return;
      const snap = deps.labStateRef.current.snapshot;
      if (!snap?.physics_tensor) return;
      const sidRaw = snap.active_session_id;
      let consultationIdOverride: number | null = null;
      if (sidRaw != null && String(sidRaw).trim() !== "") {
        const n = Number(String(sidRaw));
        if (Number.isFinite(n)) consultationIdOverride = n;
      }
      persistSnapshot({
        physics_tensor: snap.physics_tensor as Record<string, unknown>,
        metadata: (snap.metadata ?? {}) as Record<string, unknown>,
        timeline: (snap.timeline ?? null) as Record<string, unknown> | null,
        llm_prompt: String(snap.llm_prompt || ""),
        ...(snap.first_observation_llm != null ? { first_observation_llm: snap.first_observation_llm } : {}),
        ...(snap.physics_auditor_llm != null ? { physics_auditor_llm: snap.physics_auditor_llm } : {}),
        audit_summary: snap.audit_summary,
        consultationIdOverride,
      });
    }, 0);
  }, [depsRef, persistSnapshot]);

  const markActiveSession = useCallback((sessionId?: number | null) => {
    const deps = depsRef.current;
    const sid = sessionId != null ? String(sessionId) : (deps.labState.snapshot?.active_session_id || `session-${Date.now()}`);
    deps.mergeSnapshot({ active_session_id: sid });
  }, [depsRef]);

  return { updateLogicDiff, setAsBaseline, buildInteractionHub, persistSnapshot, scheduleInteractionHubPersist, markActiveSession };
}
