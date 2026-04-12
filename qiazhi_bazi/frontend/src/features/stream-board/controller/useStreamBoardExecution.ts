"use client";

import { useCallback, useRef, type Dispatch, type MutableRefObject, type SetStateAction } from "react";
import type { AuditItem } from "@/components/AuditSidebar";
import type { BaziMetadata, Lang, PersistenceLayer, TimelineSnapshot } from "@/types/bazi";
import type {
  DeityComponent,
  DeityEnergyAxis,
  FinalVerdictChangeLog,
  FinalVerdictHistoryItem,
  FinalVerdictSynthesisResult,
  InboxCard,
  LogicDiff,
  LogicProposal,
  LlmDiagnosticData,
  PhysicsLabConfig,
  PluginSwitches,
  SeedPayload,
  SeedSubmitResult,
} from "@/features/stream-board/models";
import type { FinalVerdictResult } from "@/features/stream-board/models";
import type { LabSnapshot } from "@/features/stream-board/stores/LabSessionContext";
import type { ConfirmedDecisionItem, ConsensusItem, MetricSnapshot } from "./streamBoardTypes";
import { augmentDiagnosisWithMangpaiManifest } from "@/features/stream-board/mangpaiChipManifest";
import { mergeBaziMetadataMemoryPatch, type RegenerationContextInput } from "./finalVerdictPayload";
import {
  appendManualEnergyPatchEntry,
  archiveSemanticVerdict,
  applyManualEnergyPatchesToDisplay,
  mergeAnalyzeSeedMetadata,
} from "@/features/stream-board/controller/individualAdjustment";
import {
  buildBlindSchoolFeaturesPayload,
  buildPhysicsConfigPayload,
  coerceLogicProposalParamKey,
  extractMetricSnapshotFromPhysics,
  hoistPhysicsAuditDiagnosis,
  isPhysicsAuditFallbackUi,
  isTrustworthyPhysicsAuditDiagnosis,
  mergeLlmDiagnosticSameSeedPreserve,
  seedPayloadSignature,
} from "@/features/stream-board/controller/streamBoardPure";
import type { StreamPipelineEventKind, StreamPipelinePhase } from "@/features/stream-board/models";
import { API_BASE } from "@/features/stream-board/constants";
import {
  streamVerdictBodyIntoState,
  stripLeadingH3PrefixIfRedundant,
} from "@/features/stream-board/controller/verdictBodyStream";

function labFinalVerdictFromParsed(verdict: FinalVerdictResult, bodyText: string): NonNullable<LabSnapshot["final_verdict"]> {
  return {
    body: bodyText,
    change_log: verdict.changeLog || {},
    logical_evidence: verdict.logicalEvidence || [],
    work_vector: verdict.workVector ?? null,
    topology_graph_v1: verdict.topologyGraphV1 ?? null,
    structure_candidates_v0: verdict.structureCandidatesV0 ?? null,
    structure_final_decision_v0: verdict.structureFinalDecisionV0 ?? null,
    version_id: verdict.versionId || "",
    llm_request_messages: verdict.llmRequestMessages ?? [],
    llm_raw_response: verdict.llmRawResponse ?? "",
    llm_meta: verdict.llmMeta,
    narrative_chunks: verdict.narrativeChunks,
  };
}

export type StreamBoardExecutionContext = {
  t: (text: string) => string;
  lang: Lang;
  apiBase: string;
  metadata: BaziMetadata | null;
  consultationId: number | null;
  confirmedDecisionIds: string[];
  baselineMetrics: MetricSnapshot | null;
  lastSeedPayload: SeedPayload | null;
  lastConclusionText: string;
  conclusionVersion: number;
  confirmedConflicts: string[];
  globalEntropy: number | null;
  llmModelName: string;
  setIsExecuting: (v: boolean) => void;
  setConsensusHistory: Dispatch<SetStateAction<ConsensusItem[]>>;
  setConfirmedConflicts: (v: string[]) => void;
  setResolvedCardIds: Dispatch<SetStateAction<string[]>>;
  setStreamingText: (v: string) => void;
  bumpVerdictBodyRenderNonce?: () => void;
  setConclusionVersion: Dispatch<SetStateAction<number>>;
  setSummaryChanged: (v: boolean) => void;
  setLastConclusionText: (v: string) => void;
  setFinalVerdictBody: (v: string) => void;
  setFinalVerdictChangeLog: (v: FinalVerdictChangeLog) => void;
  setFinalLogicalEvidence: (v: string[]) => void;
  setFinalWorkVector: (v: Record<string, unknown> | null) => void;
  setFinalTopologyGraphV1: (v: Record<string, unknown> | null) => void;
  setFinalStructureCandidatesV0: (v: Record<string, unknown> | null) => void;
  setFinalStructureFinalDecisionV0: (v: Record<string, unknown> | null) => void;
  setFinalVerdictVersionId: (v: string) => void;
  /** 发起再生终判时作为 previous_version_id 传入 */
  finalVerdictVersionId: string;
  setConfirmedDecisions: (v: ConfirmedDecisionItem[]) => void;
  setFinalVerdictHistory: Dispatch<SetStateAction<FinalVerdictHistoryItem[]>>;
  setAuditorProposalCards: Dispatch<SetStateAction<InboxCard[]>>;
  setConfirmedDecisionIds: Dispatch<SetStateAction<string[]>>;
  setSelectionResetToken: Dispatch<SetStateAction<number>>;
  setAuditItems: Dispatch<SetStateAction<AuditItem[]>>;
  setResultLogs: Dispatch<SetStateAction<string[]>>;
  applyPhysicsSqlPatch: (sql: string) => Promise<{ ok: boolean; error?: string }>;
  onSeedSubmit: (payload: SeedPayload) => Promise<SeedSubmitResult>;
  generateFinalVerdict: (
    conflicts: string[],
    selectedCards?: InboxCard[],
    opts?: {
      regenerationContext?: RegenerationContextInput | null;
      mandatoryFinalSynthesis?: boolean;
      metadataForRequest?: BaziMetadata | null;
    },
  ) => Promise<FinalVerdictResult>;
  appendFinalVerdictAuditItem: (versionId: string, auditLog: Record<string, unknown> | undefined, timestamp: string) => void;
  scheduleInteractionHubPersist: () => void;
  updateLogicDiff: (current: MetricSnapshot, forceBaseline?: boolean) => LogicDiff;
  typewriterResultLine: (line: string, delayMs?: number) => Promise<void>;
  mergeLabSnapshot: (patch: Partial<LabSnapshot>) => void;
  setMetadata: (v: BaziMetadata | null) => void;
  setDeityScores: (v: Record<string, number>) => void;
  setDeityEnergyAxes: (v: Record<string, DeityEnergyAxis>) => void;
  /** 最近一次 analyze-seed 的 physics_tensor（deity_scores 为引擎原值） */
  physicsTensor: Record<string, unknown> | null;
  llmDiagnosticData: LlmDiagnosticData | null;
  /** V3 中枢：当前管线阶段（供 UI / 调试） */
  pipelinePhase: StreamPipelinePhase;
  reportPipelineEvent: (event: StreamPipelineEventKind) => void;
  labConfig: PhysicsLabConfig;
  pluginSwitches: PluginSwitches;
  referenceYearRef: MutableRefObject<number>;
  timeline: TimelineSnapshot | null;
  isFinalized: boolean;
  setDeityComponents: Dispatch<SetStateAction<Record<string, DeityComponent>>>;
  setDeityTraceDetails: Dispatch<SetStateAction<Record<string, Record<string, unknown>>>>;
  setPhysicsAudit: Dispatch<SetStateAction<Record<string, unknown> | null>>;
  setPhysicsConfidence: Dispatch<SetStateAction<number | null>>;
  setPhysicsEvidence: Dispatch<SetStateAction<string[]>>;
  setPhysicsParams: Dispatch<SetStateAction<Record<string, number>>>;
  setGlobalEntropy: Dispatch<SetStateAction<number | null>>;
  consensusHistory: ConsensusItem[];
  setLlmDiagnosticData: Dispatch<SetStateAction<LlmDiagnosticData | null>>;
  addPhysicsAuditSemanticDiagnosisToInbox: (payload: {
    diagnosis: string;
    top_anomaly?: string;
    causal_reasoning?: string;
  }) => void;
  addPhysicsAuditSemanticVerdictToInbox: (payload: { diagnosis: string }) => void;
  addAuditorProposalToInbox: (proposal: LogicProposal) => void;
  setAutoConvertedParamKey: Dispatch<SetStateAction<string | null>>;
  setPreInjectionDeityDisplay: Dispatch<
    SetStateAction<{
      deity_scores?: Record<string, number>;
      deity_energy_axes?: Record<string, DeityEnergyAxis>;
    } | null>
  >;
  /** 意志重塑顶栏：requires_narrative_refresh 与终审整合期间 */
  setNarrativeReshapeActive?: (v: boolean) => void;
  /** 与终判请求对齐：当前 Inbox 卡片（按勾选 id 过滤后传入 selected_cards） */
  cards: InboxCard[];
  /** 实验室快照中的 metadata（含 persistence_layer），与 React state 合并供 mandatory 终审 */
  snapshotMetadata: Record<string, unknown> | null;
};

function countPersistenceSemanticRows(pl: PersistenceLayer | null | undefined): number {
  if (!pl || typeof pl !== "object") return 0;
  const s = pl.semantic_verdicts;
  return Array.isArray(s) ? s.length : 0;
}

/** mandatory 终审：优先采用快照侧 persistence_layer 条目更多的版本，避免 state 尚未回灌时意志丢失 */
function mergeMetadataForMandatorySynthesis(
  live: BaziMetadata | null,
  snapshotMeta: Record<string, unknown> | null | undefined,
): BaziMetadata | null {
  if (!live) return live;
  if (!snapshotMeta || typeof snapshotMeta !== "object" || Array.isArray(snapshotMeta)) return live;
  const snapPl = snapshotMeta.persistence_layer as PersistenceLayer | undefined;
  const livePl = live.persistence_layer;
  const nLive = countPersistenceSemanticRows(livePl ?? undefined);
  const nSnap = countPersistenceSemanticRows(snapPl ?? undefined);
  if (nSnap > nLive || (!livePl && snapPl)) {
    return { ...live, persistence_layer: snapPl ?? livePl };
  }
  return live;
}

function mergeVerdictIntoLabSnapshot(
  x: StreamBoardExecutionContext,
  verdict: FinalVerdictResult,
  bodyText: string,
) {
  const fv = labFinalVerdictFromParsed(verdict, bodyText);
  const mergedMeta = mergeBaziMetadataMemoryPatch(x.metadata, verdict.metadataMemoryPatch);
  x.mergeLabSnapshot({
    final_verdict: fv,
    metadata: mergedMeta as unknown as Record<string, unknown>,
  });
  x.setMetadata(mergedMeta);
}

/** 与 rerunFinalVerdictWithWeights 对齐：终判后按 work_vector 刷新 logic_diff 与过载审计 */
function applyPostVerdictMetrics(x: StreamBoardExecutionContext, verdict: FinalVerdictResult, selectedCards: InboxCard[]) {
  const currentMetric: MetricSnapshot = {
    absLossTotal:
      typeof (verdict.workVector as { backfire_risk?: unknown } | undefined)?.backfire_risk === "number"
        ? Number((verdict.workVector as { backfire_risk?: number }).backfire_risk)
        : null,
    entropy: x.globalEntropy,
  };
  const diff = x.updateLogicDiff(currentMetric);
  const absDelta = diff.abs_delta;
  if (typeof absDelta === "number" && absDelta > 100) {
    const source = selectedCards.map((card) => card.id).join(",") || "none";
    x.setResultLogs((prev) => [
      ...prev,
      `[CRITICAL] [ENERGY_OVERLOAD] abs_delta: ${absDelta.toFixed(2)} | Source: ${source}`,
    ]);
  }
}

const ORCH_DEBOUNCE_MS = 320;

export function useStreamBoardExecution(ctxRef: MutableRefObject<StreamBoardExecutionContext>) {
  const orchDebounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const orchResponseSeqRef = useRef(0);

  const runFinalVerdictSynthesis = useCallback(
    async (opts?: { delayMs?: number; trigger?: string }): Promise<FinalVerdictSynthesisResult | null> => {
      try {
        const xProbe = ctxRef.current;
        if (!xProbe.metadata?.pillars) {
          await xProbe.typewriterResultLine("⚪ 尚未完成排盘，跳过终审语义整合。", 12);
          return null;
        }
        xProbe.setFinalVerdictBody("");
        const delayMs = opts?.delayMs ?? 120;
        if (delayMs > 0) {
          await new Promise((r) => setTimeout(r, delayMs));
        }
        const x = ctxRef.current;
        x.reportPipelineEvent("FINAL_SYNTHESIS_STARTED");
        const trig = String(opts?.trigger || "mandatory_final_synthesis").slice(0, 64);
        const hasPrev = Boolean(x.finalVerdictVersionId?.trim());
        x.setStreamingText("终审语义整合中…");
        const idSet = new Set((x.confirmedDecisionIds || []).map((id) => String(id)));
        const inboxSelected = (x.cards || []).filter((c) => idSet.has(String(c.id)));
        const metadataForRequest = mergeMetadataForMandatorySynthesis(x.metadata, x.snapshotMetadata);
        const verdict = await x.generateFinalVerdict([], inboxSelected, {
          mandatoryFinalSynthesis: true,
          metadataForRequest: metadataForRequest ?? x.metadata,
          regenerationContext: hasPrev
            ? {
                reason: "终审语义整合（四柱·冲突点·已归档断言）",
                trigger: trig,
                previous_version_id: x.finalVerdictVersionId,
              }
            : undefined,
        });
        const body = String(verdict.body || "").trim();
        if (!body) {
          await x.typewriterResultLine("⚪ 终审整合未返回有效正文，请稍后重试。", 12);
          x.setStreamingText("");
          x.reportPipelineEvent("FINAL_SYNTHESIS_COMPLETED");
          return null;
        }
        const skel = (x.metadata as { verdict_anchor_layer?: { verdict_skeleton?: string } } | null)?.verdict_anchor_layer
          ?.verdict_skeleton;
        const skelStr = typeof skel === "string" && skel.trim() ? skel : "";
        const { prefix: h3Prefix, rest: h3Rest } = skelStr
          ? stripLeadingH3PrefixIfRedundant(skelStr, body)
          : { prefix: "", rest: body };
        const alignedBody = (h3Prefix ? `${h3Prefix}\n${h3Rest}` : h3Rest).trimEnd();
        await streamVerdictBodyIntoState(x.setFinalVerdictBody, body, {
          skeletonForHeadingAlign: skelStr || null,
        });
        x.setFinalVerdictBody(alignedBody);
        x.bumpVerdictBodyRenderNonce?.();
        await x.typewriterResultLine("✅ 终审整合已完成。", 10);
        x.setStreamingText("终审语义整合已完成。");
        x.setConclusionVersion((v) => v + 1);
        x.setSummaryChanged(Boolean(x.lastConclusionText && x.lastConclusionText !== alignedBody));
        x.setLastConclusionText(alignedBody);
        x.setFinalVerdictChangeLog(verdict.changeLog || {});
        x.setFinalLogicalEvidence(verdict.logicalEvidence || []);
        x.setFinalWorkVector((verdict.workVector as Record<string, unknown>) || null);
        x.setFinalTopologyGraphV1((verdict.topologyGraphV1 as Record<string, unknown>) || null);
        x.setFinalStructureCandidatesV0((verdict.structureCandidatesV0 as Record<string, unknown>) || null);
        x.setFinalStructureFinalDecisionV0((verdict.structureFinalDecisionV0 as Record<string, unknown>) || null);
        x.setFinalVerdictVersionId(verdict.versionId || "");
        x.setConfirmedDecisions(verdict.confirmedDecisions || []);
        x.setFinalVerdictHistory((prev) => [
          ...prev,
          {
            versionId: verdict.versionId || `v1.${prev.length + 1}`,
            body: alignedBody,
            changeLog: verdict.changeLog || {},
            logicalEvidence: verdict.logicalEvidence || [],
            createdAt: new Date().toISOString(),
          },
        ]);
        x.appendFinalVerdictAuditItem(verdict.versionId || `v1.${Date.now()}`, verdict.auditLog, new Date().toISOString());
        mergeVerdictIntoLabSnapshot(x, verdict, alignedBody);
        applyPostVerdictMetrics(x, verdict, inboxSelected);
        x.setResultLogs((prev) => [
          ...prev,
          `[LLM_AUDIT] source=final_synthesis | model=${x.llmModelName} | version=${verdict.versionId || "--"}`,
        ]);
        x.scheduleInteractionHubPersist();
        x.reportPipelineEvent("FINAL_SYNTHESIS_COMPLETED");
        return { body: alignedBody, verdict };
      } finally {
        ctxRef.current.setNarrativeReshapeActive?.(false);
      }
    },
    [ctxRef],
  );

  const runOrchestratorInternalLoopFromPendingSelection = useCallback(async () => {
    const x = ctxRef.current;
    if (x.isFinalized || !x.lastSeedPayload || !x.metadata?.pillars) return;
    const mySeq = ++orchResponseSeqRef.current;
    try {
      const res = await fetch(`${x.apiBase}/api/v1/orchestrator/internal-loop`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          metadata: x.metadata,
          enabled_plugins: [
            ...(x.pluginSwitches.blindSchool ? ["classical.blind_school.v1"] : []),
            ...(x.pluginSwitches.wangshuai ? ["classical.wangshuai.v1"] : []),
            ...(x.pluginSwitches.wealthRisk ? ["modern.wealth_risk.v1"] : []),
          ],
          blind_school_features: buildBlindSchoolFeaturesPayload(x.pluginSwitches),
          physics_config: buildPhysicsConfigPayload(x.labConfig),
          session_id: x.consultationId ?? undefined,
          dayun: x.timeline?.dayun ?? undefined,
          liunian: x.timeline?.liunian ?? undefined,
        }),
      });
      if (!res.ok) return;
      if (mySeq !== orchResponseSeqRef.current) return;
      const data = (await res.json()) as {
        metadata: BaziMetadata;
        physics_tensor: Record<string, unknown>;
        requires_narrative_refresh?: boolean;
        pre_injection_deity_display?: {
          deity_scores?: Record<string, number>;
          deity_energy_axes?: Record<string, DeityEnergyAxis>;
        };
      };
      const tensor = data.physics_tensor;
      if (!tensor || typeof tensor !== "object") return;
      if (mySeq !== orchResponseSeqRef.current) return;

      const incomingSig = seedPayloadSignature(x.lastSeedPayload);
      const mergedMeta = mergeAnalyzeSeedMetadata(data.metadata, x.metadata, incomingSig, {
        sameSeedResubmit: true,
      });
      x.setMetadata(mergedMeta);
      x.mergeLabSnapshot({
        physics_tensor: tensor,
        metadata: mergedMeta as unknown as Record<string, unknown>,
      });

      if (tensor.deity_scores && typeof tensor.deity_scores === "object") {
        const rawScores = tensor.deity_scores as Record<string, number>;
        const rawAxes =
          tensor.deity_energy_axes && typeof tensor.deity_energy_axes === "object"
            ? (tensor.deity_energy_axes as Record<string, DeityEnergyAxis>)
            : {};
        const applied = applyManualEnergyPatchesToDisplay(
          rawScores,
          rawAxes,
          mergedMeta.manual_energy_patch ?? null,
          incomingSig,
        );
        x.setDeityScores(applied.scores);
        x.setDeityEnergyAxes(applied.axes);
      }
      if (tensor.deity_components && typeof tensor.deity_components === "object") {
        x.setDeityComponents(tensor.deity_components as Record<string, DeityComponent>);
      }
      if (tensor.deity_trace_details && typeof tensor.deity_trace_details === "object") {
        x.setDeityTraceDetails(tensor.deity_trace_details as Record<string, Record<string, unknown>>);
      } else if ((tensor.meta as Record<string, unknown> | undefined)?.deity_trace_details) {
        x.setDeityTraceDetails(
          (tensor.meta as Record<string, unknown>).deity_trace_details as Record<string, Record<string, unknown>>,
        );
      } else {
        x.setDeityTraceDetails({});
      }
      if (tensor.audit_log && typeof tensor.audit_log === "object") {
        x.setPhysicsAudit(tensor.audit_log as Record<string, unknown>);
      }
      x.setPhysicsConfidence(typeof tensor.confidence === "number" ? tensor.confidence : null);
      if (Array.isArray(tensor.evidence)) {
        x.setPhysicsEvidence(tensor.evidence.map((item: unknown) => String(item)));
      } else {
        x.setPhysicsEvidence([]);
      }
      const pMeta = (tensor.meta || {}) as Record<string, unknown>;
      if (pMeta.params && typeof pMeta.params === "object") {
        x.setPhysicsParams(pMeta.params as Record<string, number>);
      }
      const ge = pMeta.global_entropy;
      x.setGlobalEntropy(typeof ge === "number" && Number.isFinite(ge) ? ge : null);

      const currentMetric = extractMetricSnapshotFromPhysics(tensor);
      x.updateLogicDiff(currentMetric, x.confirmedDecisionIds.length === 0 || !x.baselineMetrics);
      x.scheduleInteractionHubPersist();

      const pid = data.pre_injection_deity_display;
      if (pid?.deity_scores && Object.keys(pid.deity_scores).length > 0) {
        x.setPreInjectionDeityDisplay(pid);
      } else {
        x.setPreInjectionDeityDisplay(null);
      }

      if (data.requires_narrative_refresh) {
        x.setNarrativeReshapeActive?.(true);
        x.reportPipelineEvent("NARRATIVE_REFRESH_STARTED");
        x.setStreamingText(x.t("意志正在重塑现实…"));
        const duelCtx = [
          "[Will-Conflict Duel · 用户意志 vs 当前物理场]",
          "以下为刷新后的 verdict_skeleton（含 ### 风险预警），请专评张力，勿改写引擎已收敛的物理结论：",
          String(mergedMeta.verdict_anchor_layer?.verdict_skeleton || "").slice(0, 7200),
        ].join("\n\n");
        void (async () => {
          try {
            const ar = await fetch(`${x.apiBase}/api/v1/audit-physics-with-llm`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                metadata: mergedMeta,
                physics_tensor: tensor,
                lang: x.lang,
                consensus_history: x.consensusHistory,
                session_id: x.consultationId ?? undefined,
                audit_prompt_tier: "compact",
                will_conflict_duel_context: duelCtx,
              }),
            });
            if (!ar.ok) return;
            const auditData = (await ar.json()) as Record<string, unknown>;
            const chipLogsRaw = pMeta.mangpai_chip_logs;
            const mangpaiChipLogs = Array.isArray(chipLogsRaw) ? chipLogsRaw.map((v: unknown) => String(v || "")) : [];
            const diagnosisRaw = hoistPhysicsAuditDiagnosis(auditData);
            const diagnosisAugmented = diagnosisRaw
              ? augmentDiagnosisWithMangpaiManifest(diagnosisRaw, mangpaiChipLogs)
              : "";
            if (diagnosisAugmented && !isPhysicsAuditFallbackUi(auditData)) {
              x.addPhysicsAuditSemanticDiagnosisToInbox({
                diagnosis: diagnosisAugmented,
                top_anomaly: typeof auditData.top_anomaly === "string" ? auditData.top_anomaly : undefined,
                causal_reasoning: typeof auditData.causal_reasoning === "string" ? auditData.causal_reasoning : undefined,
              });
              x.addPhysicsAuditSemanticVerdictToInbox({ diagnosis: diagnosisAugmented });
            }
            const rawLp = auditData.logic_proposal as LogicProposal | undefined;
            const logicProposal = rawLp && typeof rawLp === "object" ? coerceLogicProposalParamKey(rawLp) : undefined;
            if (logicProposal?.param_key) {
              x.setAutoConvertedParamKey(logicProposal.param_key);
              x.addAuditorProposalToInbox({
                ...logicProposal,
                ...(diagnosisAugmented ? { diagnosis: diagnosisAugmented } : {}),
              });
            } else {
              x.setAutoConvertedParamKey(null);
            }
            const lastSig = x.lastSeedPayload ? seedPayloadSignature(x.lastSeedPayload) : null;
            x.setLlmDiagnosticData((prev) =>
              mergeLlmDiagnosticSameSeedPreserve(Boolean(lastSig), prev, {
                ...auditData,
                ...(diagnosisAugmented ? { diagnosis: diagnosisAugmented } : {}),
              }),
            );
            if (diagnosisAugmented) {
              x.setResultLogs((prev) => [...prev, `[PHYSICS_AUDIT] ${diagnosisAugmented.slice(0, 420)}`].slice(-48));
            }
          } catch {
            /* 意志对垒审计静默失败 */
          }
        })();
        void runFinalVerdictSynthesis({ delayMs: 120, trigger: "will_injection_narrative_refresh" });
      }
    } catch {
      /* 静默失败：不打扰勾选流 */
    }
  }, [ctxRef, runFinalVerdictSynthesis]);

  const scheduleSilentInternalLoopOnApprovalSelection = useCallback(
    (_selected: InboxCard[]) => {
      const x = ctxRef.current;
      if (x.isFinalized || !x.lastSeedPayload || !x.metadata?.pillars) return;
      if (orchDebounceTimerRef.current) clearTimeout(orchDebounceTimerRef.current);
      orchDebounceTimerRef.current = setTimeout(() => {
        orchDebounceTimerRef.current = null;
        void runOrchestratorInternalLoopFromPendingSelection();
      }, ORCH_DEBOUNCE_MS);
    },
    [ctxRef, runOrchestratorInternalLoopFromPendingSelection],
  );

  const onExecuteDecision = useCallback(async (selected: InboxCard[]) => {
    const x = ctxRef.current;
    x.setIsExecuting(true);
    try {
      const selectedCards = selected as InboxCard[];
      const now = new Date().toISOString();
      const conflicts = selectedCards.map((card) => card.conflictDetail).filter(Boolean) as string[];
      const sqlLegacyProposals = selectedCards.filter(
        (card) =>
          card.cardType === "auditor-proposal" &&
          typeof card.proposal?.sql_patch === "string" &&
          card.proposal.sql_patch.trim().length > 0 &&
          card.proposal.adjustment_type !== "ENERGY_PATCH",
      );
      const energyPatchCards = selectedCards.filter(
        (card) =>
          card.cardType === "energy-patch" ||
          (card.cardType === "auditor-proposal" && card.proposal?.adjustment_type === "ENERGY_PATCH"),
      );
      const semanticVerdictCards = selectedCards.filter((card) => card.cardType === "semantic-verdict");
      const proposals = sqlLegacyProposals;

      const auditishSelected = selectedCards.filter(
        (card) => card.cardType === "energy-patch" || card.cardType === "auditor-proposal",
      );
      if (
        auditishSelected.length > 0 &&
        !isTrustworthyPhysicsAuditDiagnosis(x.llmDiagnosticData?.diagnosis, x.llmDiagnosticData?.top_anomaly)
      ) {
        await x.typewriterResultLine(x.t("审计失败，请重算"));
        x.setStreamingText(x.t("审计失败，请重算"));
        return;
      }

      if (proposals.length > 0) {
        x.setConsensusHistory((prev) => [
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
      if (energyPatchCards.length > 0) {
        x.setConsensusHistory((prev) => [
          ...prev,
          ...energyPatchCards
            .map((proposalCard) => ({
              decision_key: `ENERGY_PATCH:${String(proposalCard.proposal?.param_key || "")}`,
              confirmed_value: typeof proposalCard.proposal?.suggested_value === "number" ? proposalCard.proposal.suggested_value : undefined,
              reasoning: String(proposalCard.proposal?.reason || proposalCard.proposal?.expected_impact || "manual_energy_patch"),
            }))
            .filter((item) => item.decision_key.startsWith("ENERGY_PATCH:") && item.decision_key.length > "ENERGY_PATCH:".length),
        ]);
      }

      if (
        conflicts.length === 0 &&
        proposals.length === 0 &&
        energyPatchCards.length === 0 &&
        semanticVerdictCards.length === 0
      ) {
        await x.typewriterResultLine("⚪ 未选择任何冲合项/提案，本轮不触发终极判词。");
        return;
      }

      x.setConfirmedConflicts(conflicts);
      x.setResolvedCardIds((prev) => [...new Set([...prev, ...selectedCards.map((card) => card.id)])]);

      const seedSig = x.lastSeedPayload ? seedPayloadSignature(x.lastSeedPayload) : null;

      if (energyPatchCards.length > 0 || semanticVerdictCards.length > 0) {
        const actionType =
          energyPatchCards.length > 0 && semanticVerdictCards.length > 0
            ? "ENERGY_PATCH | SEMANTIC_VERDICT"
            : energyPatchCards.length > 0
              ? "ENERGY_PATCH"
              : "SEMANTIC_VERDICT";
        console.log("--- [Audit] Decision Confirm Start ---");
        console.log("Action Type:", actionType);
        console.log("Payload Data:", {
          energyPatchCards: energyPatchCards.map((c) => ({
            id: c.id,
            cardType: c.cardType,
            param_key: c.proposal?.param_key,
            energy_deltas: c.proposal?.energy_deltas,
            conflictDetail: String(c.conflictDetail || "").slice(0, 240),
          })),
          semanticVerdictCards: semanticVerdictCards.map((c) => ({
            id: c.id,
            cardType: c.cardType,
            conflictDetail: String(c.conflictDetail || "").slice(0, 240),
            markdownExcerpt: String(c.markdown || "").slice(0, 240),
          })),
          allSelectedIds: selectedCards.map((c) => c.id),
        });
        console.log(
          "Target Seed Hash (seedPayloadSignature; BaziMetadata 无顶层 seed_hash):",
          seedSig,
        );
        console.log("metadata.manual_energy_patch?.seed_hash:", x.metadata?.manual_energy_patch?.seed_hash ?? null);
      }

      x.setStreamingText(
        proposals.length > 0 && conflicts.length === 0
          ? `${x.t("已确认")} 审计员提案，正在执行参数校准…`
          : energyPatchCards.length > 0 && conflicts.length === 0
            ? `${x.t("已确认")} 个人能量补丁，正在写入命例…`
            : `${x.t("已确认")} ${conflicts.join("、")}${x.t("，正在执行全局裁决…")}`,
      );

      if (x.consultationId) {
        try {
          await fetch(`${x.apiBase}/api/decision-steps`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              consultation_id: x.consultationId,
              step_type: "execute-decision",
              raw_data: { metadata: x.metadata, selected_conflicts: conflicts },
              human_choice: {
                action: "execute",
                selected_conflicts: conflicts,
                selected_proposals: proposals.map((proposalCard) => proposalCard.proposal),
                energy_patch_cards: energyPatchCards.map((c) => ({
                  id: c.id,
                  param_key: c.proposal?.param_key,
                  energy_deltas: c.proposal?.energy_deltas,
                })),
                semantic_verdict_cards: semanticVerdictCards.map((c) => ({ id: c.id, excerpt: (c.markdown || "").slice(0, 400) })),
              },
            }),
          });
        } catch {
          /* DB 不可用时本地乐观流程足够 */
        }
      }

      let metaWorking = x.metadata;
      for (const card of semanticVerdictCards) {
        const text = String(card.conflictDetail || "").trim() || String(card.markdown || "").trim();
        if (!seedSig || !text) continue;
        metaWorking = archiveSemanticVerdict(metaWorking, seedSig, text, card.id, now);
      }
      if (semanticVerdictCards.length && metaWorking) {
        x.setMetadata(metaWorking);
        x.mergeLabSnapshot({ metadata: metaWorking as unknown as Record<string, unknown> });
        await x.typewriterResultLine("📇 断语已归档并与当前生辰指纹绑定。", 12);
      }

      for (const card of energyPatchCards) {
        const deltas = (card.proposal?.energy_deltas || {}) as Record<string, number>;
        if (!seedSig || !metaWorking) continue;
        metaWorking = appendManualEnergyPatchEntry(metaWorking, seedSig, {
          delta_by_deity: { ...deltas },
          param_key: card.proposal?.param_key,
          suggested_value: card.proposal?.suggested_value,
          reason: String(card.proposal?.reason || card.proposal?.expected_impact || ""),
          confirmed_at: now,
          source_card_id: card.id,
        });
      }
      if (energyPatchCards.length && metaWorking && seedSig) {
        const diag = String(
          energyPatchCards.map((c) => c.proposal?.diagnosis).find((d) => String(d || "").trim()) ||
            x.llmDiagnosticData?.diagnosis ||
            "",
        ).trim();
        if (diag) {
          metaWorking = archiveSemanticVerdict(metaWorking, seedSig, diag, "inbox-energy-patch", now) ?? metaWorking;
        }
        x.setMetadata(metaWorking);
        x.mergeLabSnapshot({ metadata: metaWorking as unknown as Record<string, unknown> });
        const tensor = x.physicsTensor;
        const rawScores = (tensor?.deity_scores && typeof tensor.deity_scores === "object"
          ? tensor.deity_scores
          : {}) as Record<string, number>;
        const rawAxes = (tensor?.deity_energy_axes && typeof tensor.deity_energy_axes === "object"
          ? tensor.deity_energy_axes
          : {}) as Record<string, DeityEnergyAxis>;
        const applied = applyManualEnergyPatchesToDisplay(
          rawScores,
          rawAxes,
          metaWorking.manual_energy_patch ?? null,
          seedSig,
        );
        x.setDeityScores(applied.scores);
        x.setDeityEnergyAxes(applied.axes);
        await x.typewriterResultLine("🎚️ 个人能量补丁已应用（展示层修正，未修改全局物理常数）。", 12);
      }

      for (const proposalCard of proposals) {
        const result = await x.applyPhysicsSqlPatch(proposalCard.proposal?.sql_patch || "");
        if (!result.ok) {
          await x.typewriterResultLine(`❌ 参数建议执行失败：${result.error}`);
          x.setStreamingText(`参数校准失败：${result.error}`);
          return;
        }
      }

      if (proposals.length > 0 && x.lastSeedPayload) {
        await x.typewriterResultLine("🧬 参数校准已执行，系统正在按新物理常数重算…", 18);
        x.setStreamingText("系统逻辑已接收裁决，正在自动重算...");
        x.reportPipelineEvent("RECALC_STARTED");
        await x.onSeedSubmit(x.lastSeedPayload);
        x.reportPipelineEvent("RECALC_COMPLETED");
        x.setAuditorProposalCards([]);
        x.setConfirmedDecisionIds([]);
        x.setSelectionResetToken((value) => value + 1);

        let verdict = await x.generateFinalVerdict(
          conflicts,
          selectedCards,
          x.finalVerdictVersionId?.trim()
            ? {
                regenerationContext: {
                  reason: "审计员 SQL 提案已应用并完成静默重算",
                  trigger: "physics_sql_patch",
                  previous_version_id: x.finalVerdictVersionId,
                },
              }
            : undefined,
        );
        let bodyOut = String(verdict.body || "").trim();
        if (!bodyOut) {
          await x.typewriterResultLine("⚪ 终判 JSON 未解析出正文，正基于已验证事实发起终审整合…", 14);
          const synth = await runFinalVerdictSynthesis({
            delayMs: 90,
            trigger: "sql_patch_verdict_parse_fallback",
          });
          if (synth?.body) {
            verdict = synth.verdict;
            bodyOut = synth.body;
          }
        }
        if (bodyOut) {
          await x.typewriterResultLine(`${x.t("✅ 终极判词：")}${bodyOut}`, 18);
          x.setStreamingText(x.t("全局裁决完成，终极判词已生成。"));
          x.setConclusionVersion((value) => value + 1);
          x.setSummaryChanged(Boolean(x.lastConclusionText && x.lastConclusionText !== bodyOut));
          x.setLastConclusionText(bodyOut);
          x.setFinalVerdictBody(bodyOut);
          x.setFinalVerdictChangeLog(verdict.changeLog || {});
          x.setFinalLogicalEvidence(verdict.logicalEvidence || []);
          x.setFinalWorkVector((verdict.workVector as Record<string, unknown>) || null);
          x.setFinalTopologyGraphV1((verdict.topologyGraphV1 as Record<string, unknown>) || null);
          x.setFinalStructureCandidatesV0((verdict.structureCandidatesV0 as Record<string, unknown>) || null);
          x.setFinalStructureFinalDecisionV0((verdict.structureFinalDecisionV0 as Record<string, unknown>) || null);
          x.setFinalVerdictVersionId(verdict.versionId || "");
          x.setConfirmedDecisions(verdict.confirmedDecisions || []);
          x.setFinalVerdictHistory((prev) => [
            ...prev,
            {
              versionId: verdict.versionId || `v1.${x.conclusionVersion + 1}`,
              body: bodyOut,
              changeLog: verdict.changeLog || {},
              logicalEvidence: verdict.logicalEvidence || [],
              createdAt: new Date().toISOString(),
            },
          ]);
          x.appendFinalVerdictAuditItem(verdict.versionId || `v1.${x.conclusionVersion + 1}`, verdict.auditLog, new Date().toISOString());
          mergeVerdictIntoLabSnapshot(x, verdict, bodyOut);
          applyPostVerdictMetrics(x, verdict, selectedCards);
        }

        x.setAuditItems((prev) => [
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
        x.scheduleInteractionHubPersist();
        return;
      }

      const selectedIdSet = new Set(selectedCards.map((c) => c.id));
      if (
        proposals.length === 0 &&
        conflicts.length === 0 &&
        (energyPatchCards.length > 0 || semanticVerdictCards.length > 0)
      ) {
        x.setAuditorProposalCards((prev) => prev.filter((c) => !selectedIdSet.has(c.id)));
        x.setConfirmedDecisionIds([]);
        x.setSelectionResetToken((value) => value + 1);
        x.setAuditItems((prev) => [
          ...prev,
          {
            id: `arbiter-step-${Date.now()}`,
            step: "04",
            role: "Arbiter",
            action: `个体干预已落库（能量补丁 ${energyPatchCards.length} · 断语归档 ${semanticVerdictCards.length}）`,
            timestamp: now,
            payload: { selected_card_ids: [...selectedIdSet] },
          },
        ]);
        x.scheduleInteractionHubPersist();
        await runFinalVerdictSynthesis({ delayMs: 100, trigger: "inbox_semantic_or_energy" });
        return;
      }

      if (conflicts.length > 0) {
        x.setFinalVerdictBody("");
        let verdict = await x.generateFinalVerdict(
          conflicts,
          selectedCards,
          x.finalVerdictVersionId?.trim()
            ? {
                regenerationContext: {
                  reason: "已确认 Inbox 冲合/卡片并执行全局裁决",
                  trigger: "inbox_execute",
                  previous_version_id: x.finalVerdictVersionId,
                },
              }
            : undefined,
        );
        let bodyText = String(verdict.body || "").trim();
        if (!bodyText) {
          await x.typewriterResultLine("⚪ 终判 JSON 未解析出正文，正基于已验证事实发起终审整合…", 14);
          const synth = await runFinalVerdictSynthesis({
            delayMs: 90,
            trigger: "conflict_inbox_verdict_parse_fallback",
          });
          if (synth?.body) {
            verdict = synth.verdict;
            bodyText = synth.body;
          }
        }
        const safeVerdict = bodyText
          ? bodyText
          : (x.lang === "KO" ? x.t("[KO] 结果提取失败。") : "结果提取失败，请稍后重试。");
        await x.typewriterResultLine(`${x.t("✅ 终极判词：")}${safeVerdict}`, 18);
        x.setStreamingText(x.t("全局裁决完成，终极判词已生成。"));
        x.setConclusionVersion((value) => value + 1);
        x.setSummaryChanged(Boolean(x.lastConclusionText && x.lastConclusionText !== safeVerdict));
        x.setLastConclusionText(safeVerdict);
        x.setFinalVerdictBody(safeVerdict);
        x.setFinalVerdictChangeLog(verdict.changeLog || {});
        x.setFinalLogicalEvidence(verdict.logicalEvidence || []);
        x.setFinalWorkVector((verdict.workVector as Record<string, unknown>) || null);
        x.setFinalTopologyGraphV1((verdict.topologyGraphV1 as Record<string, unknown>) || null);
        x.setFinalStructureCandidatesV0((verdict.structureCandidatesV0 as Record<string, unknown>) || null);
        x.setFinalStructureFinalDecisionV0((verdict.structureFinalDecisionV0 as Record<string, unknown>) || null);
        x.setFinalVerdictVersionId(verdict.versionId || "");
        x.setConfirmedDecisions(verdict.confirmedDecisions || []);
        x.setFinalVerdictHistory((prev) => [
          ...prev,
          {
            versionId: verdict.versionId || `v1.${x.conclusionVersion + 1}`,
            body: safeVerdict,
            changeLog: verdict.changeLog || {},
            logicalEvidence: verdict.logicalEvidence || [],
            createdAt: new Date().toISOString(),
          },
        ]);
        x.appendFinalVerdictAuditItem(verdict.versionId || `v1.${x.conclusionVersion + 1}`, verdict.auditLog, new Date().toISOString());
        mergeVerdictIntoLabSnapshot(x, verdict, safeVerdict);
        applyPostVerdictMetrics(x, verdict, selectedCards);
      }

      x.setAuditorProposalCards((prev) => prev.filter((card) => !selectedCards.some((selectedCard) => selectedCard.id === card.id)));
      x.setConfirmedDecisionIds([]);
      x.setSelectionResetToken((value) => value + 1);
      x.setAuditItems((prev) => [
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
      x.scheduleInteractionHubPersist();
    } finally {
      ctxRef.current.setIsExecuting(false);
    }
  }, [ctxRef, runFinalVerdictSynthesis]);

  const rerunFinalVerdictWithWeights = useCallback(
    async (selectedCards: InboxCard[] = []) => {
      const x = ctxRef.current;
      const selectedConflicts = selectedCards.map((card) => String(card.conflictDetail || "").trim()).filter(Boolean);
      const conflicts = selectedConflicts.length > 0 ? selectedConflicts : (x.confirmedConflicts || []);
      const verdict = await x.generateFinalVerdict(
        conflicts,
        selectedCards,
        x.finalVerdictVersionId?.trim()
          ? {
              regenerationContext: {
                reason: "用户触发语义重算（Regenerate）或插件权重调整后再裁决",
                trigger: "manual_regenerate",
                previous_version_id: x.finalVerdictVersionId,
              },
            }
          : undefined,
      );
      const safeVerdict = (verdict.body || "").trim() ? verdict.body : "结果提取失败，请稍后重试。";
      x.setFinalVerdictBody(safeVerdict);
      x.setFinalVerdictChangeLog(verdict.changeLog || {});
      x.setFinalLogicalEvidence(verdict.logicalEvidence || []);
      x.setFinalWorkVector((verdict.workVector as Record<string, unknown>) || null);
      x.setFinalTopologyGraphV1((verdict.topologyGraphV1 as Record<string, unknown>) || null);
      x.setFinalStructureCandidatesV0((verdict.structureCandidatesV0 as Record<string, unknown>) || null);
      x.setFinalStructureFinalDecisionV0((verdict.structureFinalDecisionV0 as Record<string, unknown>) || null);
      x.setFinalVerdictVersionId(verdict.versionId || "");
      x.setConfirmedDecisions(verdict.confirmedDecisions || []);
      const llmSource = verdict.versionId ? "model_pipeline" : "fallback";
      x.setResultLogs((prev) => [
        ...prev,
        `[LLM_AUDIT] source=${llmSource} | model=${x.llmModelName} | version=${verdict.versionId || "--"}`,
      ]);
      x.setConfirmedConflicts(conflicts);
      if (selectedCards.length > 0) {
        x.setResolvedCardIds((prev) => [...new Set([...prev, ...selectedCards.map((card) => card.id)])]);
      }
      x.setAuditItems((prev) => [
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
        entropy: x.globalEntropy,
      };
      const diff = x.updateLogicDiff(currentMetric);
      const absDelta = diff.abs_delta;
      if (typeof absDelta === "number" && absDelta > 100) {
        const source = selectedCards.map((card) => card.id).join(",") || "none";
        x.setResultLogs((prev) => [
          ...prev,
          `[CRITICAL] [ENERGY_OVERLOAD] abs_delta: ${absDelta.toFixed(2)} | Source: ${source}`,
        ]);
      }
      mergeVerdictIntoLabSnapshot(x, verdict, safeVerdict);
    },
    [ctxRef],
  );

  const refreshVerdict = useCallback(
    async (selected: InboxCard[]) => {
      await rerunFinalVerdictWithWeights(selected);
    },
    [rerunFinalVerdictWithWeights],
  );

  const executeDecisionAndRefresh = useCallback(
    async (selected: InboxCard[]) => {
      // 曾在此处串联 refreshVerdict → 第二次终判请求；小模型下易覆盖首次已打字展示的正文，造成「判词突然变短/消失」。
      await onExecuteDecision(selected);
    },
    [onExecuteDecision],
  );

  return {
    onExecuteDecision,
    rerunFinalVerdictWithWeights,
    refreshVerdict,
    executeDecisionAndRefresh,
    runFinalVerdictSynthesis,
    scheduleSilentInternalLoopOnApprovalSelection,
  };
}
