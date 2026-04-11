"use client";

import type { Dispatch, MutableRefObject, SetStateAction } from "react";
import { useCallback } from "react";
import type { InboxCard } from "@/features/stream-board/models";
import { API_BASE, VERDICT_TIMEOUT_MS } from "@/features/stream-board/constants";
import {
  buildFinalVerdictRequestBody,
  finalVerdictHttpFallbackLog,
  parseFinalVerdictFromApiData,
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
  pluginWeights: PluginWeights;
  lang: Lang;
  setResultLogs: Dispatch<SetStateAction<string[]>>;
};

/**
 * 终判 HTTP 调用、barrier 与静默重算延迟协调（从主编排抽离）。
 */
export function useVerdictExecution(depsRef: MutableRefObject<VerdictExecutionDeps>) {
  const generateFinalVerdict = useCallback(
    async (conflicts: string[], selectedCards: InboxCard[] = []) => {
      const d = depsRef.current;
      while (d.silentRecalcInFlightRef.current) {
        await new Promise((r) => setTimeout(r, 25));
      }
      d.verdictRecalcBarrierRef.current = true;
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
                metadata: d.metadata,
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
                pluginWeights: d.pluginWeights,
                lang: d.lang,
              }),
            ),
          });
          clearTimeout(timer);

          const data = await response.json();
          const verdictParsed = parseFinalVerdictFromApiData(data);
          if (verdictParsed) {
            return verdictParsed;
          }
          d.setResultLogs((prev) => [...prev, finalVerdictHttpFallbackLog(response, data)]);
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
