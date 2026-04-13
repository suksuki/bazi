"use client";

import type { Dispatch, MutableRefObject, SetStateAction } from "react";
import { useCallback } from "react";
import type { InboxCard } from "@/features/stream-board/models";
import { API_BASE, FINAL_VERDICT_TRY_NDJSON_STREAM, VERDICT_TIMEOUT_MS } from "@/features/stream-board/constants";
import {
  buildFinalVerdictRequestBody,
  finalVerdictHttpFallbackLog,
  parseFinalVerdictFromApiData,
  type RegenerationContextInput,
} from "@/features/stream-board/controller/finalVerdictPayload";
import { buildFallbackVerdict } from "@/features/stream-board/utils";
import type { BaziMetadata, Lang, TimelineSnapshot } from "@/types/bazi";
import type { DeityComponent, DeityEnergyAxis, LlmDiagnosticData, PluginWeights } from "../models";
import type { PluginSwitches } from "../models";
import type { ConsensusItem } from "@/features/stream-board/controller/streamBoardTypes";

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
      let ev: { type?: string; text?: string; data?: unknown; detail?: string };
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
        throw new Error(typeof ev.detail === "string" ? ev.detail : "ndjson error");
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
              } catch {
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
          const verdictParsed = parseFinalVerdictFromApiData(data);
          if (verdictParsed) {
            return verdictParsed;
          }
          d.setResultLogs((prev) => [...prev, finalVerdictHttpFallbackLog(response, data)]);
          } finally {
            clearTimeout(timer);
          }
        } catch (error) {
          const hint = error instanceof Error ? error.message : "unknown";
          d.setResultLogs((prev) => [...prev, `⚠️ 终判接口异常：${hint}；已进入保底断言。`]);
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
