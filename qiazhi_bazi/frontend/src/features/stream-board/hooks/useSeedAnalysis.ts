"use client";

import type { AuditItem } from "@/components/AuditSidebar";
import type { Dispatch, MutableRefObject, SetStateAction } from "react";
import { useCallback } from "react";
import type { BaziMetadata, Lang, TimelineSnapshot } from "@/types/bazi";
import { API_BASE } from "@/features/stream-board/constants";
import {
  buildBlindSchoolFeaturesPayload,
  extractMetricSnapshotFromPhysics,
} from "@/features/stream-board/controller/streamBoardPure";
import type { ConsensusItem, MetricSnapshot } from "@/features/stream-board/controller/streamBoardTypes";
import type {
  DeityComponent,
  DeityEnergyAxis,
  FinalVerdictHistoryItem,
  InboxCard,
  LogicDiff,
  LogicProposal,
  LlmDiagnosticData,
  FinalVerdictChangeLog,
  PhysicsLabConfig,
  PluginSwitches,
  SeedPayload,
} from "../models";

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
  refreshHealth: () => Promise<{ dbOk: boolean; llmOk: boolean }>;
  t: (key: string) => string;
  referenceYearRef: MutableRefObject<number>;
  consultationId: number | null;
  setConsultationId: Dispatch<SetStateAction<number | null>>;
  labConfig: PhysicsLabConfig;
  pluginSwitches: PluginSwitches;
  lang: Lang;
  markActiveSession: (sessionId?: number | null) => void;
  resetSeedPreviewState: () => void;
  confirmedDecisionIds: string[];
  baselineMetrics: MetricSnapshot | null;
  persistSnapshot: (payload: {
    physics_tensor: Record<string, unknown>;
    metadata?: Record<string, unknown>;
    timeline?: Record<string, unknown> | null;
    llm_prompt?: string;
    audit_summary?: unknown;
    consultationIdOverride?: number | null;
    healthOverride?: { dbOk: boolean; llmOk: boolean };
    auditorBriefingOverride?: Record<string, unknown> | null;
    seedSignatureOverride?: string | null;
  }) => void;
  appendSystemAuditLog: (line: string) => void;
  addAuditorProposalToInbox: (proposal: LogicProposal) => void;
  typewriter: (fullText: string) => Promise<void>;
  updateLogicDiff: (current: MetricSnapshot, forceBaseline?: boolean) => LogicDiff;
  scheduleInteractionHubPersist: () => void;
  llmModelName: string;
};

/**
 * 首次排盘 / 生辰提交：consultation、analyze-seed、审计 LLM、快照与首条判词流式。
 */
export function useSeedAnalysis(depsRef: MutableRefObject<SeedAnalysisDeps>) {
  const onSeedSubmit = useCallback(
    async (payload: SeedPayload) => {
      const d = depsRef.current;
      d.setLastSeedPayload(payload);
      d.persistLastSeedToStore(payload);
      d.setBusy(true);
      d.setIsStreaming(true);
      d.setAutoConvertedParamKey(null);
      d.setStreamingText("");
      d.setAuditItems([]);
      d.setResultLogs([]);
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
      d.setFirstPromptText("");
      d.setTimeline(null);
      d.setLlmDiagnosticData(null);
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
        d.setStreamingText(d.t("第一波：物理排盘中…"));
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

        d.setStreamingText(d.t("第二波：特征扫描中…"));
        const response = await fetch(`${API_BASE}/api/v1/analyze-seed`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            date: payload.date,
            time: payload.time,
            calendar: payload.calendar,
            gender: payload.gender,
            lang: d.lang,
            latitude: 31.2304,
            longitude: 121.4737,
            session_id: currentSessionId ?? undefined,
            physics_config: d.labConfig,
            enabled_plugins: [
              ...(d.pluginSwitches.blindSchool ? ["classical.blind_school.v1"] : []),
              ...(d.pluginSwitches.wangshuai ? ["classical.wangshuai.v1"] : []),
              ...(d.pluginSwitches.wealthRisk ? ["modern.wealth_risk.v1"] : []),
            ],
            blind_school_features: buildBlindSchoolFeaturesPayload(d.pluginSwitches),
            reference_year: d.referenceYearRef.current,
          }),
        });

        if (!response.ok) throw new Error(await response.text());
        const data = await response.json();
        d.markActiveSession(currentSessionId ?? d.consultationId ?? null);
        d.setMetadata(data.metadata as BaziMetadata);
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
          d.setDeityScores(data.physics_tensor.deity_scores as Record<string, number>);
        }
        if (data.physics_tensor?.deity_energy_axes) {
          d.setDeityEnergyAxes(data.physics_tensor.deity_energy_axes as Record<string, DeityEnergyAxis>);
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
            d.persistSnapshot({
              physics_tensor: data.physics_tensor as Record<string, unknown>,
              metadata: data.metadata as Record<string, unknown>,
              timeline: (data.timeline ?? null) as Record<string, unknown> | null,
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
                metadata: data.metadata,
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

            const logicProposal = auditData?.logic_proposal as LogicProposal | undefined;
            if (logicProposal?.param_key) {
              d.setAutoConvertedParamKey(logicProposal.param_key);
              d.addAuditorProposalToInbox(logicProposal);
            } else {
              d.setAutoConvertedParamKey(null);
            }

            d.setLlmDiagnosticData({
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
                d.persistSnapshot({
                  physics_tensor: data.physics_tensor as Record<string, unknown>,
                  metadata: data.metadata as Record<string, unknown>,
                  timeline: (data.timeline ?? null) as Record<string, unknown> | null,
                  llm_prompt: data.llm_prompt || "",
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
                    auto_joined_decision_box: Boolean(logicProposal?.param_key),
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
      } catch (error) {
        await d.typewriter(`${d.t("连接后端失败：")}${error instanceof Error ? error.message : String(error)}`);
      } finally {
        d.setBusy(false);
        d.setIsStreaming(false);
      }
    },
    [depsRef],
  );

  return { onSeedSubmit };
}
