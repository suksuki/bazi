"use client";

import type { Dispatch, MutableRefObject, SetStateAction } from "react";
import { useCallback } from "react";
import type { InboxCard } from "@/features/stream-board/models";
import { API_BASE, FINAL_VERDICT_TRY_NDJSON_STREAM, VERDICT_TIMEOUT_MS } from "@/features/stream-board/constants";
import {
  buildFinalVerdictRequestBody,
  finalVerdictHttpFallbackLog,
  parseFinalVerdictFromApiData,
  V12_SCHEMA_VIOLATION_ERROR,
  type RegenerationContextInput,
} from "@/features/stream-board/controller/finalVerdictPayload";
import { buildFallbackVerdict } from "@/features/stream-board/utils";
import type { BaziMetadata, Lang, TimelineSnapshot } from "@/types/bazi";
import type { DeityComponent, DeityEnergyAxis, LlmDiagnosticData, PluginWeights } from "../models";
import type { PluginSwitches } from "../models";
import type { ConsensusItem } from "@/features/stream-board/controller/streamBoardTypes";

function mapFinalVerdictError(status: number, detailCode: string): string {
  const code = String(detailCode || "").trim();
  if (status === 409 || code === "FINAL_VERDICT_FLOW_STATE_CONFLICT") {
    return "系统正在等待您的逻辑确认（PROBE_WAITING），请先完成反馈。";
  }
  if (status === 422 || code === "V12_SCHEMA_VIOLATION_ERROR") {
    return "断言结构违章（V12_SCHEMA_VIOLATION），已拦截非血统输出。";
  }
  return "";
}

function emitVerdictFlowConflictNavigationPulse(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(
    new CustomEvent("qiazhi:verdict-flow-conflict", {
      detail: { code: "FINAL_VERDICT_FLOW_STATE_CONFLICT" },
    }),
  );
}

export type VerdictExecutionDeps = {
  silentRecalcInFlightRef: MutableRefObject<boolean>;
  verdictRecalcBarrierRef: MutableRefObject<boolean>;
  silentRecalcDeferredRef: MutableRefObject<boolean>;
  bumpSyncBarrierSeq: () => void;
  reCalculateAbsRef: MutableRefObject<() => Promise<void>>;
  metadata: BaziMetadata | null;
  deityScores: Record<string, number>;
  deityEnergyAxes: Record<string, DeityEnergyAxis>;
  deityComponents: Record<string, DeityComponent>;
  deityTraceDetails: Record<string, Record<string, unknown>>;
  physicsAudit: Record<string, unknown> | null;
  llmDiagnosticData: LlmDiagnosticData | null;
  timeline: TimelineSnapshot | null;
  consensusHistory: ConsensusItem[];
  finalVerdictBody: string;
  lastConclusionText: string;
  finalLogicalEvidence: string[];
  consultationId: number | null;
  pluginSwitches: PluginSwitches;
  /** URL ``?pure_physics_audit=1`` */
  purePhysicsAudit?: boolean;
  pluginWeights: PluginWeights;
  lang: Lang;
  setResultLogs: Dispatch<SetStateAction<string[]>>;
  /** NDJSON 流式终判时写入 UI 提示（服务端 token 累积） */
  setStreamingText?: Dispatch<SetStateAction<string>>;
};

async function consumeFinalVerdictNdjsonStream(
  res: Response,
  onCumulativeToken: (text: string) => void,
): Promise<unknown> {
  const body = res.body;
  if (!body) throw new Error("empty body");
  const reader = body.getReader();
  const dec = new TextDecoder();
  let buf = "";
  let acc = "";
  let complete: unknown = null;
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buf += dec.decode(value, { stream: true });
    for (;;) {
      const nl = buf.indexOf("\n");
      if (nl < 0) break;
      const line = buf.slice(0, nl).trim();
      buf = buf.slice(nl + 1);
      if (!line) continue;
      let ev: { type?: string; text?: string; data?: unknown; detail?: string; code?: string; status_code?: number };
      try {
        ev = JSON.parse(line) as typeof ev;
      } catch {
        continue;
      }
      if (ev.type === "token" && typeof ev.text === "string") {
        acc += ev.text;
        onCumulativeToken(acc);
      } else if (ev.type === "complete" && ev.data) {
        complete = ev.data;
      } else if (ev.type === "error") {
        const mapped = mapFinalVerdictError(Number(ev.status_code || 0), String(ev.code || ""));
        if (mapped && (Number(ev.status_code || 0) === 409 || String(ev.code || "") === "FINAL_VERDICT_FLOW_STATE_CONFLICT")) {
          emitVerdictFlowConflictNavigationPulse();
        }
        throw new Error(mapped || (typeof ev.detail === "string" ? ev.detail : "ndjson error"));
      }
    }
  }
  return complete;
}

/**
 * 终判 HTTP 调用、barrier 与静默重算延迟协调（从主编排抽离）。
 */
export function useVerdictExecution(depsRef: MutableRefObject<VerdictExecutionDeps>) {
  const generateFinalVerdict = useCallback(
    async (
      conflicts: string[],
      selectedCards: InboxCard[] = [],
      opts?: {
        regenerationContext?: RegenerationContextInput | null;
        mandatoryFinalSynthesis?: boolean;
        metadataForRequest?: BaziMetadata | null;
      },
    ) => {
      const d = depsRef.current;
      while (d.silentRecalcInFlightRef.current) {
        await new Promise((r) => setTimeout(r, 25));
      }
      d.verdictRecalcBarrierRef.current = true;
      try {
        try {
          const controller = new AbortController();
          const timer = setTimeout(() => controller.abort(), VERDICT_TIMEOUT_MS);
          try {
          const jsonBody = JSON.stringify(
            buildFinalVerdictRequestBody({
              metadata: d.metadata,
              metadataForRequest: opts?.metadataForRequest,
              deityScores: d.deityScores,
              deityEnergyAxes: d.deityEnergyAxes,
              deityComponents: d.deityComponents,
              deityTraceDetails: d.deityTraceDetails,
              physicsAudit: d.physicsAudit,
              llmDiagnosticData: d.llmDiagnosticData,
              timeline: (d.timeline || {}) as Record<string, unknown> | null,
              conflicts,
              selectedCards,
              consensusHistory: d.consensusHistory,
              finalVerdictBody: d.finalVerdictBody,
              lastConclusionText: d.lastConclusionText,
              finalLogicalEvidence: d.finalLogicalEvidence,
              consultationId: d.consultationId,
              pluginSwitches: d.pluginSwitches,
              purePhysicsAudit: d.purePhysicsAudit,
              pluginWeights: d.pluginWeights,
              lang: d.lang,
              regenerationContext: opts?.regenerationContext,
              mandatoryFinalSynthesis: opts?.mandatoryFinalSynthesis,
            }),
          );

          const jsonUrl = `${API_BASE}/api/v1/final-verdict`;
          const streamUrl = `${API_BASE}/api/v1/final-verdict/stream`;

          const tryStream = FINAL_VERDICT_TRY_NDJSON_STREAM && Boolean(d.setStreamingText);
          if (tryStream) {
            d.setStreamingText?.("");
            const sRes = await fetch(streamUrl, {
              method: "POST",
              headers: { "Content-Type": "application/json", Accept: "application/x-ndjson" },
              signal: controller.signal,
              body: jsonBody,
            });
            if (sRes.ok && sRes.body) {
              try {
                const data = await consumeFinalVerdictNdjsonStream(sRes, (cum) => d.setStreamingText?.(cum));
                const verdictParsed = parseFinalVerdictFromApiData(data);
                if (verdictParsed) return verdictParsed;
              } catch (error) {
                if (error instanceof Error && error.name === V12_SCHEMA_VIOLATION_ERROR) {
                  throw error;
                }
                /* fall through to JSON POST */
              }
            }
          }

          const response = await fetch(jsonUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            signal: controller.signal,
            body: jsonBody,
          });
          const data = await response.json();
          if (!response.ok) {
            const detail = data?.detail && typeof data.detail === "object" ? data.detail : {};
            const mapped = mapFinalVerdictError(Number(response.status || 0), String(detail?.code || ""));
            if (mapped && (Number(response.status || 0) === 409 || String(detail?.code || "") === "FINAL_VERDICT_FLOW_STATE_CONFLICT")) {
              emitVerdictFlowConflictNavigationPulse();
            }
            throw new Error(mapped || String(detail?.user_message || detail?.message || data?.detail || `HTTP ${response.status}`));
          }
          const verdictParsed = parseFinalVerdictFromApiData(data);
          if (verdictParsed) {
            return verdictParsed;
          }
          d.setResultLogs((prev) => [...prev, finalVerdictHttpFallbackLog(response, data)]);
          } finally {
            clearTimeout(timer);
          }
        } catch (error) {
          if (error instanceof Error && error.name === V12_SCHEMA_VIOLATION_ERROR) {
            throw error;
          }
          const hint = error instanceof Error ? error.message : "unknown";
          const isFlowConflict = hint.includes("PROBE_WAITING") || hint.includes("逻辑确认");
          d.setResultLogs((prev) => [
            ...prev,
            isFlowConflict ? `🧭 终判等待确认：${hint}` : `⚠️ 终判接口异常：${hint}；已进入保底断言。`,
          ]);
        }

        return buildFallbackVerdict(conflicts);
      } finally {
        d.verdictRecalcBarrierRef.current = false;
        d.bumpSyncBarrierSeq();
        if (d.silentRecalcDeferredRef.current) {
          d.silentRecalcDeferredRef.current = false;
          void d.reCalculateAbsRef.current();
        }
      }
    },
    [depsRef],
  );

  return { generateFinalVerdict };
}
