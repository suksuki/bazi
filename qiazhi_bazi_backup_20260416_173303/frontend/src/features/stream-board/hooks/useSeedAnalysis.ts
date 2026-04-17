"use client";

import type { AuditItem } from "@/components/AuditSidebar";
import type { Dispatch, MutableRefObject, SetStateAction } from "react";
import { useCallback } from "react";
import type { BaziMetadata, Lang, TimelineSnapshot } from "@/types/bazi";
import { API_BASE } from "@/features/stream-board/constants";
import {
  buildBlindSchoolFeaturesPayload,
  buildPhysicsConfigPayload,
  buildStreamBoardEnabledPlugins,
  coerceLogicProposalParamKey,
  mergeLlmDiagnosticSameSeedPreserve,
  extractMetricSnapshotFromPhysics,
  parsePatternThresholdsPayload,
  hoistPhysicsAuditDiagnosis,
  isPhysicsAuditFallbackUi,
  seedPayloadSignature,
  applyPhysicsConvergenceProbeUnlock,
} from "@/features/stream-board/controller/streamBoardPure";
import {
  applyManualEnergyPatchesToDisplay,
  mergeAnalyzeSeedMetadata,
} from "@/features/stream-board/controller/individualAdjustment";
import type { ConsensusItem, MetricSnapshot } from "@/features/stream-board/controller/streamBoardTypes";
import type {
  AnalyzeSeedThoughtPhase,
  BrainHubAudit,
  DissentBlock,
  DeityComponent,
  DeityEnergyAxis,
  FinalVerdictHistoryItem,
  InboxCard,
  LogicDiff,
  LogicProposal,
  LlmDiagnosticData,
  FinalVerdictChangeLog,
  PatternThresholdRow,
  PhysicsLabConfig,
  PluginSwitches,
  PsvSignal,
  SeedPayload,
  SeedSubmitOptions,
} from "../models";
import type { LabLlmRoundSnapshot } from "@/features/stream-board/stores/LabSessionContext";
import { parseFirstObservationLlmFromAnalyze, parsePhysicsAuditorLlm } from "@/features/stream-board/controller/labLlmSnapshotParse";
import type { StreamPipelineEventKind } from "@/features/stream-board/models";
import { augmentDiagnosisWithMangpaiManifest } from "@/features/stream-board/mangpaiChipManifest";

type AnalyzeSeedStreamLine =
  | { type: "phase"; phase: string; message: string }
  | { type: "complete"; data: Record<string, unknown> }
  | { type: "error"; code?: string; detail?: string; pulse_id?: string | null };

async function readAnalyzeSeedNdjsonStream(
  response: Response,
  onPhase: (phase: string, message: string) => void,
): Promise<Record<string, any>> {
  if (!response.body) {
    throw new Error("analyze-seed stream: empty body");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let complete: Record<string, any> | null = null;
  for (;;) {
    let done = false;
    let value: Uint8Array | undefined;
    try {
      const part = await reader.read();
      done = part.done;
      value = part.value;
    } catch (err) {
      // 常见于反向代理/HTTP2 中途断流：交由上层自动回退非流式接口
      throw new Error(`STREAM_READ_ABORTED:${err instanceof Error ? err.message : String(err)}`);
    }
    buffer += decoder.decode(value ?? new Uint8Array(), { stream: !done });
    const parts = buffer.split("\n");
    buffer = parts.pop() ?? "";
    for (const line of parts) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      let ev: AnalyzeSeedStreamLine;
      try {
        ev = JSON.parse(trimmed) as AnalyzeSeedStreamLine;
      } catch {
        continue;
      }
      if (ev.type === "phase" && ev.phase && ev.message) {
        onPhase(ev.phase, ev.message);
      } else if (ev.type === "complete" && ev.data && typeof ev.data === "object") {
        complete = ev.data as Record<string, any>;
      } else if (ev.type === "error") {
        const code = String(ev.code || "");
        const detail = String(ev.detail || "");
        if (code === "ANALYZE_SEED_FLOW_STATE_CONFLICT") {
          throw new Error("系统状态冲突，请尝试刷新重置");
        }
        if (code === "V12_SCHEMA_VIOLATION_ERROR") {
          throw new Error("逻辑断点异常，请检查 Fact 节点完整性");
        }
        if (code === "ANALYZE_SEED_INVALID_INPUT") {
          throw new Error(detail || "输入格式错误");
        }
        throw new Error(detail || "analyze-seed 流式计算失败");
      }
    }
    if (done) break;
  }
  const tail = buffer.trim();
  if (tail) {
    try {
      const ev = JSON.parse(tail) as AnalyzeSeedStreamLine;
      if (ev.type === "complete" && ev.data && typeof ev.data === "object") {
        complete = ev.data as Record<string, any>;
      }
    } catch {
      // ignore tail parse failure
    }
  }
  if (!complete) {
    throw new Error("analyze-seed stream ended without result");
  }
  return complete;
}

export type SeedAnalysisDeps = {
  persistLastSeedToStore: (p: SeedPayload | null) => void;
  setLastSeedPayload: Dispatch<SetStateAction<SeedPayload | null>>;
  setMetadata: Dispatch<SetStateAction<BaziMetadata | null>>;
  consensusHistory: ConsensusItem[];
  setBusy: (v: boolean) => void;
  setIsStreaming: (v: boolean) => void;
  setAutoConvertedParamKey: Dispatch<SetStateAction<string | null>>;
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
  setPatternThresholds: Dispatch<SetStateAction<PatternThresholdRow[]>>;
  setPatternThresholdsStatus: Dispatch<SetStateAction<string | null>>;
  setConfirmedConflicts: Dispatch<SetStateAction<string[]>>;
  setFirstPromptText: Dispatch<SetStateAction<string>>;
  setTimeline: Dispatch<SetStateAction<TimelineSnapshot | null>>;
  setLlmDiagnosticData: Dispatch<SetStateAction<LlmDiagnosticData | null>>;
  setFinalVerdictBody: Dispatch<SetStateAction<string>>;
  setFinalVerdictChangeLog: Dispatch<SetStateAction<FinalVerdictChangeLog>>;
  setFinalVerdictVersionId: Dispatch<SetStateAction<string>>;
  setInterruptRequest?: Dispatch<SetStateAction<Record<string, unknown> | null>>;
  setPsvSignals?: Dispatch<SetStateAction<PsvSignal[]>>;
  setBrainHubAudit?: Dispatch<SetStateAction<BrainHubAudit | null>>;
  setBrainHubDissentBlock?: Dispatch<SetStateAction<DissentBlock | null>>;
  setFinalLogicalEvidence: Dispatch<SetStateAction<string[]>>;
  setFinalWorkVector: Dispatch<SetStateAction<Record<string, unknown> | null>>;
  setFinalTopologyGraphV1: Dispatch<SetStateAction<Record<string, unknown> | null>>;
  setFinalStructureCandidatesV0: Dispatch<SetStateAction<Record<string, unknown> | null>>;
  setFinalStructureFinalDecisionV0: Dispatch<SetStateAction<Record<string, unknown> | null>>;
  setFinalVerdictHistory: Dispatch<SetStateAction<FinalVerdictHistoryItem[]>>;
  setStressTestResult: Dispatch<SetStateAction<Record<string, unknown> | null>>;
  setGenderComparisonResult: Dispatch<SetStateAction<Record<string, unknown> | null>>;
  setConsensusHistory: Dispatch<SetStateAction<ConsensusItem[]>>;
  refreshHealth: () => Promise<{ dbOk: boolean; llmOk: boolean }>;
  t: (key: string) => string;
  referenceYearRef: MutableRefObject<number>;
  consultationId: number | null;
  setConsultationId: Dispatch<SetStateAction<number | null>>;
  labConfig: PhysicsLabConfig;
  pluginSwitches: PluginSwitches;
  lang: Lang;
  markActiveSession: (sessionId?: number | null) => void;
  /** V3 中枢状态机：与 `reducePipelinePhase` 对齐 */
  reportPipelineEvent?: (event: StreamPipelineEventKind) => void;
  resetSeedPreviewState: () => void;
  confirmedDecisionIds: string[];
  baselineMetrics: MetricSnapshot | null;
  persistSnapshot: (payload: {
    physics_tensor: Record<string, unknown>;
    metadata?: Record<string, unknown>;
    timeline?: Record<string, unknown> | null;
    llm_prompt?: string;
    first_observation_llm?: LabLlmRoundSnapshot;
    physics_auditor_llm?: LabLlmRoundSnapshot;
    audit_summary?: unknown;
    consultationIdOverride?: number | null;
    healthOverride?: { dbOk: boolean; llmOk: boolean };
    auditorBriefingOverride?: Record<string, unknown> | null;
    seedSignatureOverride?: string | null;
  }) => void;
  appendSystemAuditLog: (line: string) => void;
  getMetadata: () => BaziMetadata | null;
  addAuditorProposalToInbox: (proposal: LogicProposal) => void;
  addPhysicsAuditSemanticDiagnosisToInbox: (payload: {
    diagnosis: string;
    top_anomaly?: string;
    causal_reasoning?: string;
  }) => void;
  addPhysicsAuditSemanticVerdictToInbox: (payload: { diagnosis: string }) => void;
  typewriter: (fullText: string) => Promise<void>;
  updateLogicDiff: (current: MetricSnapshot, forceBaseline?: boolean) => LogicDiff;
  scheduleInteractionHubPersist: () => void;
  llmModelName: string;
  mergeSnapshot: (diff: Record<string, unknown>) => void;
  /** V13.02：analyze-seed 后空追问态自动 resume（与 StreamBoard resume 同签名） */
  resumeFromInterrupt?: (
    feedback: {
      action: "confirm_conflict" | "adjust_energy" | "ignore_warning";
      user_intention_id: string;
      wealth_weight_delta: number;
      preferred_plugin_id?: string;
    },
    options?: { metadataOverride?: BaziMetadata | null },
  ) => Promise<void>;
  /** 最近一次成功 analyze-seed 的 seed 签名；用于区分「校准重算」与「用户更换生辰」 */
  seedShieldSigRef: MutableRefObject<string | null>;
  /** URL ``?pure_physics_audit=1``：纯物理审计，不挂载格局 manifest 插件 */
  purePhysicsAudit?: boolean;
  /** V13.05：NDJSON analyze-seed 阶段心跳 */
  setAnalyzeSeedThoughtPhase?: Dispatch<SetStateAction<AnalyzeSeedThoughtPhase>>;
};

/**
 * 首次排盘 / 生辰提交：consultation、analyze-seed、审计 LLM、快照与首条判词流式。
 */
export function useSeedAnalysis(depsRef: MutableRefObject<SeedAnalysisDeps>) {
  const onSeedSubmit = useCallback(
    async (payload: SeedPayload, options?: SeedSubmitOptions) => {
      const d = depsRef.current;
      const labMerged: PhysicsLabConfig = {
        ...d.labConfig,
        ...(options?.physics_config_merge && typeof options.physics_config_merge === "object"
          ? options.physics_config_merge
          : {}),
      };
      const incomingSig = seedPayloadSignature(payload);
      const priorSig = d.seedShieldSigRef.current;
      const sameSeedResubmit = priorSig !== null && incomingSig !== null && priorSig === incomingSig;
      if (priorSig !== null && incomingSig !== null && priorSig !== incomingSig) {
        d.mergeSnapshot({ decision_journal: [] });
      }
      d.setLastSeedPayload(payload);
      d.persistLastSeedToStore(payload);
      d.setBusy(true);
      d.setIsStreaming(true);
      d.reportPipelineEvent?.("SCAN_STARTED");
      d.setAutoConvertedParamKey(null);
      d.setStreamingText("");
      d.setAuditItems([]);
      if (!sameSeedResubmit) {
        d.setResultLogs([]);
      }
      d.setDeityScores({});
      d.setDeityEnergyAxes({});
      d.setDeityComponents({});
      d.setDeityTraceDetails({});
      d.setHoveredDeity(undefined);
      d.setPhysicsAudit(null);
      d.setPhysicsConfidence(null);
      d.setPhysicsEvidence([]);
      d.setShowPhysicsAudit(false);
      d.setAuditorProposalCards([]);
      d.setResolvedCardIds([]);
      d.setPhysicsParams({});
      d.setGlobalEntropy(null);
      d.setConfirmedConflicts([]);
      if (!sameSeedResubmit) {
        d.setFirstPromptText("");
      }
      d.setTimeline(null);
      if (!sameSeedResubmit) {
        d.setLlmDiagnosticData(null);
      }
      d.setFinalVerdictBody("");
      d.setFinalVerdictChangeLog({});
      d.setFinalVerdictVersionId("");
      d.setFinalLogicalEvidence([]);
      d.setFinalWorkVector(null);
      d.setFinalTopologyGraphV1(null);
      d.setFinalStructureCandidatesV0(null);
      d.setFinalStructureFinalDecisionV0(null);
      d.setFinalVerdictHistory([]);
      d.setStressTestResult(null);
      d.setGenderComparisonResult(null);
      d.setConsensusHistory([]);

      const latestHealth = await d.refreshHealth();

      try {
        let currentSessionId = d.consultationId;
        const dateNorm = String(payload.date || "").trim();
        const timeNorm = String(payload.time || "").trim();
        if (!/^\d{4}-\d{2}-\d{2}$/.test(dateNorm)) {
          throw new Error(`日期格式错误: ${dateNorm || "empty"}（应为 YYYY-MM-DD）`);
        }
        if (!/^\d{2}:\d{2}$/.test(timeNorm)) {
          throw new Error(`时间格式错误: ${timeNorm || "empty"}（应为 HH:MM）`);
        }
        d.setStreamingText(d.t("物理引擎排盘中…"));
        d.setAuditItems([
          {
            id: `arbiter-submit-${Date.now()}`,
            step: "01",
            role: "Arbiter",
            action: `提交生辰 ${payload.date} ${payload.time}，请求物理建模。`,
            timestamp: new Date().toISOString(),
            payload: { ...payload, reference_year: d.referenceYearRef.current },
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
            d.setConsultationId(consultationData.id as number);
            currentSessionId = consultationData.id as number;
          }
        } catch {
          /* consultation logging should not block main flow */
        }

        d.setStreamingText(d.t("多轮 LLM 与物理审计准备中…"));
        const analyzeBody = {
          date: dateNorm,
          time: timeNorm,
          calendar: payload.calendar,
          gender: payload.gender,
          lang: d.lang,
          latitude: 31.2304,
          longitude: 121.4737,
          session_id: currentSessionId ?? undefined,
          physics_config: buildPhysicsConfigPayload(labMerged),
          enabled_plugins: buildStreamBoardEnabledPlugins(d.pluginSwitches, {
            purePhysicsAudit: Boolean(d.purePhysicsAudit),
          }),
          blind_school_features: buildBlindSchoolFeaturesPayload(d.pluginSwitches),
          reference_year: d.referenceYearRef.current,
        };
        const analyzeInit: RequestInit = {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(analyzeBody),
        };
        const streamUrl = `${API_BASE}/api/v1/analyze-seed/stream`;
        const jsonUrl = `${API_BASE}/api/v1/analyze-seed`;

        d.setAnalyzeSeedThoughtPhase?.({ phase: "PHASE_PHYSICS", message: "解析天干地支能量场..." });

        const streamRes = await fetch(streamUrl, analyzeInit);
        // 与历史 ``response.json()`` 一致：后端 analyze-seed 负载字段繁多，此处保留宽松类型。
        let data: Record<string, any>;
        if (streamRes.ok) {
          try {
            data = await readAnalyzeSeedNdjsonStream(streamRes, (phase, message) => {
              d.setAnalyzeSeedThoughtPhase?.({ phase, message });
            });
          } catch (streamErr) {
            d.appendSystemAuditLog(
              `[STREAM_FALLBACK] analyze-seed stream interrupted, fallback to json: ${
                streamErr instanceof Error ? streamErr.message : String(streamErr)
              }`,
            );
            d.setAnalyzeSeedThoughtPhase?.(null);
            const response = await fetch(jsonUrl, analyzeInit);
            if (!response.ok) {
              let detailMessage = "";
              try {
                const errJson = (await response.json()) as { detail?: unknown };
                const detail = errJson.detail as Record<string, unknown> | undefined;
                detailMessage = String(detail?.user_message || detail?.message || "");
              } catch {
                detailMessage = await response.text();
              }
              throw new Error(detailMessage || `analyze-seed fallback failed (HTTP ${response.status})`);
            }
            data = (await response.json()) as Record<string, any>;
          }
        } else if (streamRes.status === 404) {
          d.setAnalyzeSeedThoughtPhase?.(null);
          const response = await fetch(jsonUrl, analyzeInit);
          if (!response.ok) {
            let detailCode = "";
            let detailMessage = "";
            try {
              const errJson = (await response.json()) as { detail?: unknown };
              const detail = errJson.detail as Record<string, unknown> | undefined;
              detailCode = String(detail?.code || "");
              detailMessage = String(detail?.user_message || detail?.message || "");
            } catch {
              detailMessage = await response.text();
            }
            if (response.status === 409 || detailCode === "ANALYZE_SEED_FLOW_STATE_CONFLICT") {
              throw new Error("系统状态冲突，请尝试刷新重置");
            }
            if (response.status === 422 || detailCode === "V12_SCHEMA_VIOLATION_ERROR") {
              throw new Error("逻辑断点异常，请检查 Fact 节点完整性");
            }
            throw new Error(detailMessage || `analyze-seed failed (HTTP ${response.status})`);
          }
          data = (await response.json()) as Record<string, unknown>;
        } else {
          d.setAnalyzeSeedThoughtPhase?.(null);
          let detailCode = "";
          let detailMessage = "";
          try {
            const errJson = (await streamRes.json()) as { detail?: unknown };
            const detail = errJson.detail as Record<string, unknown> | undefined;
            detailCode = String(detail?.code || "");
            detailMessage = String(detail?.user_message || detail?.message || "");
          } catch {
            detailMessage = await streamRes.text();
          }
          if (streamRes.status === 409 || detailCode === "ANALYZE_SEED_FLOW_STATE_CONFLICT") {
            throw new Error("系统状态冲突，请尝试刷新重置");
          }
          if (streamRes.status === 422 || detailCode === "V12_SCHEMA_VIOLATION_ERROR") {
            throw new Error("逻辑断点异常，请检查 Fact 节点完整性");
          }
          throw new Error(detailMessage || `analyze-seed stream failed (HTTP ${streamRes.status})`);
        }
        d.reportPipelineEvent?.("SCAN_COMPLETED");
        if (incomingSig) {
          d.seedShieldSigRef.current = incomingSig;
        }
        d.markActiveSession(currentSessionId ?? d.consultationId ?? null);
        const mergedMeta = mergeAnalyzeSeedMetadata(
          data.metadata as BaziMetadata,
          d.getMetadata(),
          incomingSig,
          { sameSeedResubmit },
        );
        const { metadata: metaAfterConvergence, clearProbeInterrupt } = applyPhysicsConvergenceProbeUnlock(
          mergedMeta,
          data.physics_tensor as Record<string, unknown> | undefined,
        );
        d.setMetadata(metaAfterConvergence);
        const rawInterruptFromPayload =
          data.interrupt_request && typeof data.interrupt_request === "object" && !Array.isArray(data.interrupt_request)
            ? (data.interrupt_request as Record<string, unknown>)
            : null;
        if (clearProbeInterrupt) {
          d.setInterruptRequest?.(null);
        } else {
          d.setInterruptRequest?.(
            rawInterruptFromPayload && Object.keys(rawInterruptFromPayload).length > 0 ? rawInterruptFromPayload : null,
          );
        }
        const interruptReq = clearProbeInterrupt ? null : rawInterruptFromPayload;

        const sessionForAuto = currentSessionId ?? d.consultationId ?? null;
        const fsAuto = String(metaAfterConvergence.flow_state || "").toLowerCase();
        const pqIr =
          interruptReq && typeof interruptReq === "object"
            ? String((interruptReq as Record<string, unknown>).probe_query || "").trim()
            : "";
        const plM = metaAfterConvergence.persistence_layer as { interrupt_request?: Record<string, unknown> } | undefined;
        const pr = plM?.interrupt_request;
        const pqPl =
          typeof pr === "object" && pr && !Array.isArray(pr)
            ? String((pr as Record<string, unknown>).probe_query || "").trim()
            : "";
        if (fsAuto === "probe_waiting" && !pqIr && !pqPl && sessionForAuto && d.resumeFromInterrupt) {
          try {
            await d.resumeFromInterrupt(
              {
                action: "confirm_conflict",
                user_intention_id: "AUTO_SYNC_V1302",
                wealth_weight_delta: 0,
              },
              { metadataOverride: metaAfterConvergence },
            );
            d.appendSystemAuditLog("V13.02：probe_waiting 且无 probe_query，已自动 resume 对齐。");
          } catch (autoErr) {
            d.appendSystemAuditLog(
              `V13.02 自动 resume 跳过：${autoErr instanceof Error ? autoErr.message : String(autoErr)}`,
            );
          }
        }

        const psvRaw = Array.isArray((data as Record<string, unknown>).psv_manifest)
          ? ((data as Record<string, unknown>).psv_manifest as Array<Record<string, unknown>>)
          : [];
        d.setPsvSignals?.(
          psvRaw.map((x) => ({
            axis: String(x.axis || ""),
            polarity: String(x.polarity || ""),
            strength: Number(x.strength || 0),
            evidence: Array.isArray(x.evidence) ? x.evidence.map((e) => String(e)) : [],
          })),
        );
        const bh = (data as Record<string, unknown>).brain_hub_preview;
        if (bh && typeof bh === "object" && !Array.isArray(bh)) {
          const o = bh as Record<string, unknown>;
          d.setBrainHubAudit?.(
            o.audit && typeof o.audit === "object" && !Array.isArray(o.audit) ? (o.audit as BrainHubAudit) : null,
          );
          d.setBrainHubDissentBlock?.(
            o.dissent_block && typeof o.dissent_block === "object" && !Array.isArray(o.dissent_block)
              ? (o.dissent_block as DissentBlock)
              : null,
          );
        } else {
          d.setBrainHubAudit?.(null);
          d.setBrainHubDissentBlock?.(null);
        }
        const tl = (data.timeline ?? null) as TimelineSnapshot | null;
        d.setTimeline(tl);
        d.resetSeedPreviewState();
        const ry = d.referenceYearRef.current;
        if (tl?.dayun && tl?.liunian) {
          d.setResultLogs((prev) => [
            ...prev,
            `📅 ${d.t("参考年")} ${ry} → ${d.t("大运")} ${tl.dayun} · ${d.t("流年")} ${tl.liunian}（${d.t("已随测算写入命盘")}）`,
          ]);
        }

        if (data.physics_tensor?.normalized) {
          const normalized = data.physics_tensor.normalized as Record<string, number>;
          d.setResultLogs((prev) => [
            ...prev,
            `⚙️ 能量矩阵(木火土金水)：${normalized.wood ?? 0}/${normalized.fire ?? 0}/${normalized.earth ?? 0}/${normalized.metal ?? 0}/${normalized.water ?? 0}`,
          ]);
        }
        if (data.physics_tensor?.deity_scores) {
          const rawScores = data.physics_tensor.deity_scores as Record<string, number>;
          const rawAxes =
            data.physics_tensor.deity_energy_axes && typeof data.physics_tensor.deity_energy_axes === "object"
              ? (data.physics_tensor.deity_energy_axes as Record<string, DeityEnergyAxis>)
              : {};
          const applied = applyManualEnergyPatchesToDisplay(
            rawScores,
            rawAxes,
            metaAfterConvergence.manual_energy_patch ?? null,
            incomingSig,
          );
          d.setDeityScores(applied.scores);
          d.setDeityEnergyAxes(applied.axes);
        }
        if (data.physics_tensor?.deity_components) {
          d.setDeityComponents(data.physics_tensor.deity_components as Record<string, DeityComponent>);
        }
        if (data.physics_tensor?.deity_trace_details) {
          d.setDeityTraceDetails(data.physics_tensor.deity_trace_details as Record<string, Record<string, unknown>>);
        } else if (data.physics_tensor?.meta?.deity_trace_details) {
          d.setDeityTraceDetails(data.physics_tensor.meta.deity_trace_details as Record<string, Record<string, unknown>>);
        } else {
          d.setDeityTraceDetails({});
        }
        if (data.physics_tensor?.audit_log) {
          d.setPhysicsAudit(data.physics_tensor.audit_log as Record<string, unknown>);
        }
        if (typeof data.physics_tensor?.confidence === "number") {
          d.setPhysicsConfidence(data.physics_tensor.confidence);
        } else {
          d.setPhysicsConfidence(null);
        }
        if (Array.isArray(data.physics_tensor?.evidence)) {
          d.setPhysicsEvidence(data.physics_tensor.evidence.map((item: unknown) => String(item)));
        } else {
          d.setPhysicsEvidence([]);
        }
        if (data.physics_tensor?.meta?.params) {
          d.setPhysicsParams(data.physics_tensor.meta.params as Record<string, number>);
        }
        const geRaw = (data.physics_tensor?.meta as { global_entropy?: unknown } | undefined)?.global_entropy;
        d.setGlobalEntropy(typeof geRaw === "number" && Number.isFinite(geRaw) ? geRaw : null);
        const pMetaSeed = (data.physics_tensor?.meta || {}) as Record<string, unknown>;
        if (
          Object.prototype.hasOwnProperty.call(pMetaSeed, "pattern_thresholds") ||
          Object.prototype.hasOwnProperty.call(pMetaSeed, "pattern_thresholds_status")
        ) {
          const ptRows = parsePatternThresholdsPayload(pMetaSeed.pattern_thresholds);
          d.setPatternThresholds(ptRows);
          const stSeed = pMetaSeed.pattern_thresholds_status;
          d.setPatternThresholdsStatus(
            typeof stSeed === "string" && stSeed.trim()
              ? stSeed.trim()
              : ptRows.length > 0
                ? "OK"
                : null,
          );
        }
        const mangpaiChips = (data.physics_tensor?.meta as { mangpai_chip_logs?: unknown } | undefined)?.mangpai_chip_logs;
        if (Array.isArray(mangpaiChips)) {
          for (const line of mangpaiChips) {
            const s = String(line || "").trim();
            if (s) d.appendSystemAuditLog(s);
          }
        }
        const currentMetric = extractMetricSnapshotFromPhysics((data.physics_tensor as Record<string, unknown> | undefined) || null);
        const diff = d.updateLogicDiff(currentMetric, d.confirmedDecisionIds.length === 0 || !d.baselineMetrics);
        const absDelta = diff.abs_delta;
        if (typeof absDelta === "number" && absDelta > 100) {
          const source = d.confirmedDecisionIds.join(",") || "seed_submit";
          d.setResultLogs((prev) => [
            ...prev,
            `[CRITICAL] [ENERGY_OVERLOAD] abs_delta: ${absDelta.toFixed(2)} | Source: ${source}`,
          ]);
        }

        try {
          if (data.physics_tensor) {
            const dataRec = data as Record<string, unknown>;
            d.persistSnapshot({
              physics_tensor: data.physics_tensor as Record<string, unknown>,
              metadata: metaAfterConvergence as unknown as Record<string, unknown>,
              timeline: (data.timeline ?? null) as Record<string, unknown> | null,
              llm_prompt: typeof data.llm_prompt === "string" ? data.llm_prompt : "",
              first_observation_llm: parseFirstObservationLlmFromAnalyze(dataRec),
              audit_summary: data.audit_summary,
              consultationIdOverride: currentSessionId ?? d.consultationId ?? null,
              healthOverride: latestHealth,
            });
          }
        } catch {
          /* ignore quota / privacy mode */
        }

        if (data.metadata && data.physics_tensor) {
          try {
            const auditResponse = await fetch(`${API_BASE}/api/v1/audit-physics-with-llm`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                metadata: metaAfterConvergence,
                physics_tensor: data.physics_tensor,
                lang: d.lang,
                consensus_history: d.consensusHistory,
                session_id: currentSessionId ?? undefined,
              }),
            });
            const auditData = await auditResponse.json();
            if (!auditResponse.ok) {
              throw new Error(String(auditData?.detail ?? "audit-physics-with-llm failed"));
            }

            const auditRec = auditData as Record<string, unknown>;
            const diagnosisRaw = hoistPhysicsAuditDiagnosis(auditRec);
            const metaPt = data.physics_tensor as Record<string, unknown> | undefined;
            const metaInner =
              metaPt && typeof metaPt.meta === "object" && metaPt.meta !== null
                ? (metaPt.meta as Record<string, unknown>)
                : {};
            const chipLogsRaw = metaInner.mangpai_chip_logs;
            const mangpaiChipLogs = Array.isArray(chipLogsRaw) ? chipLogsRaw.map((x) => String(x || "")) : [];
            const diagnosisAugmented = diagnosisRaw
              ? augmentDiagnosisWithMangpaiManifest(diagnosisRaw, mangpaiChipLogs)
              : "";
            if (diagnosisAugmented && !isPhysicsAuditFallbackUi(auditRec)) {
              d.addPhysicsAuditSemanticDiagnosisToInbox({
                diagnosis: diagnosisAugmented,
                top_anomaly: typeof auditData?.top_anomaly === "string" ? auditData.top_anomaly : undefined,
                causal_reasoning: typeof auditData?.causal_reasoning === "string" ? auditData.causal_reasoning : undefined,
              });
              d.addPhysicsAuditSemanticVerdictToInbox({ diagnosis: diagnosisAugmented });
            }

            const rawLp = auditData?.logic_proposal as LogicProposal | undefined;
            const logicProposal = rawLp && typeof rawLp === "object" ? coerceLogicProposalParamKey(rawLp) : undefined;
            if (logicProposal?.param_key) {
              d.setAutoConvertedParamKey(logicProposal.param_key);
              d.addAuditorProposalToInbox({
                ...logicProposal,
                ...(diagnosisAugmented ? { diagnosis: diagnosisAugmented } : {}),
              });
            } else {
              d.setAutoConvertedParamKey(null);
            }

            d.setLlmDiagnosticData((prev) =>
              mergeLlmDiagnosticSameSeedPreserve(sameSeedResubmit, prev, {
                ...(auditData as Record<string, unknown>),
                ...(diagnosisAugmented ? { diagnosis: diagnosisAugmented } : {}),
              }),
            );
            if (diagnosisAugmented) {
              d.setResultLogs((prev) => [...prev, `[PHYSICS_AUDIT] ${diagnosisAugmented.slice(0, 420)}`].slice(-48));
            }
            if (process.env.NODE_ENV === "development") {
              console.debug("[qiazhi/audit-physics]", {
                structured_hit: auditData?.structured_hit,
                repair_mode: auditData?.repair_mode,
                fallback_ui: isPhysicsAuditFallbackUi(auditRec),
              });
            }
            try {
              if (data.physics_tensor) {
                const dataRec = data as Record<string, unknown>;
                d.persistSnapshot({
                  physics_tensor: data.physics_tensor as Record<string, unknown>,
                  metadata: metaAfterConvergence as unknown as Record<string, unknown>,
                  timeline: (data.timeline ?? null) as Record<string, unknown> | null,
                  llm_prompt: data.llm_prompt || "",
                  first_observation_llm: parseFirstObservationLlmFromAnalyze(dataRec),
                  physics_auditor_llm: parsePhysicsAuditorLlm(auditRec),
                  audit_summary: data.audit_summary,
                  consultationIdOverride: currentSessionId ?? d.consultationId ?? null,
                  healthOverride: latestHealth,
                  auditorBriefingOverride: {
                    alignment_score: auditData?.alignment_score,
                    structured_hit: auditData?.structured_hit,
                    repair_mode: auditData?.repair_mode,
                    top_anomaly: auditData?.top_anomaly,
                    causal_reasoning: auditData?.causal_reasoning,
                    tuning_suggestions: auditData?.tuning_suggestions,
                    logic_proposal: auditData?.logic_proposal,
                    auto_joined_decision_box: Boolean(diagnosisRaw || logicProposal?.param_key),
                  },
                });
              }
            } catch {
              /* ignore quota / privacy mode */
            }
          } catch {
            /* keep board usable if auditor fails */
          }
        }
        d.reportPipelineEvent?.("AUDIT_COMPLETED");

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
                      ? (item.payload as { model_name?: string }).model_name || d.llmModelName
                      : d.llmModelName,
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

          d.setAuditItems([mapped[0]]);
          await new Promise((resolve) => setTimeout(resolve, 220));
          d.setAuditItems([mapped[0], mapped[1]]);
          await new Promise((resolve) => setTimeout(resolve, 220));
          d.setAuditItems([mapped[0], mapped[1], mapped[2]]);
        }

        if (data.physics_tensor) {
          d.scheduleInteractionHubPersist();
        }

        d.setStreamingText(
          `${d.t("扫描完毕，发现")} ${(data.metadata?.conflict_matrix?.points ?? []).length} ${d.t("处冲合特征，正在生成首条判词…")}`,
        );
        d.setFirstPromptText(data.llm_prompt || "");
        await d.typewriter(data.llm_prompt || "");
        const pt = data.physics_tensor;
        return {
          ok: true as const,
          physics_tensor:
            pt && typeof pt === "object" ? (pt as Record<string, unknown>) : null,
        };
      } catch (error) {
        const msg = `${d.t("连接后端失败：")}${error instanceof Error ? error.message : String(error)}`;
        await d.typewriter(msg);
        return { ok: false as const, error: msg };
      } finally {
        d.setAnalyzeSeedThoughtPhase?.(null);
        d.setBusy(false);
        d.setIsStreaming(false);
      }
    },
    [depsRef],
  );

  return { onSeedSubmit };
}
