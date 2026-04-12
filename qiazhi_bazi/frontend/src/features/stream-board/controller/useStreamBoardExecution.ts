"use client";

import { useCallback, type Dispatch, type MutableRefObject, type SetStateAction } from "react";
import type { AuditItem } from "@/components/AuditSidebar";
import type { BaziMetadata, Lang } from "@/types/bazi";
import type {
  FinalVerdictChangeLog,
  FinalVerdictHistoryItem,
  InboxCard,
  LogicDiff,
  SeedPayload,
} from "@/features/stream-board/models";
import type { FinalVerdictResult } from "@/features/stream-board/models";
import type { LabSnapshot } from "@/features/stream-board/stores/LabSessionContext";
import type { ConfirmedDecisionItem, ConsensusItem, MetricSnapshot } from "./streamBoardTypes";
import { mergeBaziMetadataMemoryPatch, type RegenerationContextInput } from "./finalVerdictPayload";

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
  setConfirmedDecisionIds: (v: string[]) => void;
  setSelectionResetToken: Dispatch<SetStateAction<number>>;
  setAuditItems: Dispatch<SetStateAction<AuditItem[]>>;
  setResultLogs: Dispatch<SetStateAction<string[]>>;
  applyPhysicsSqlPatch: (sql: string) => Promise<{ ok: boolean; error?: string }>;
  onSeedSubmit: (payload: SeedPayload) => Promise<void>;
  generateFinalVerdict: (
    conflicts: string[],
    selectedCards?: InboxCard[],
    opts?: { regenerationContext?: RegenerationContextInput | null },
  ) => Promise<FinalVerdictResult>;
  appendFinalVerdictAuditItem: (versionId: string, auditLog: Record<string, unknown> | undefined, timestamp: string) => void;
  scheduleInteractionHubPersist: () => void;
  updateLogicDiff: (current: MetricSnapshot, forceBaseline?: boolean) => LogicDiff;
  typewriterResultLine: (line: string, delayMs?: number) => Promise<void>;
  mergeLabSnapshot: (patch: Partial<LabSnapshot>) => void;
  setMetadata: (v: BaziMetadata | null) => void;
};

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

export function useStreamBoardExecution(ctxRef: MutableRefObject<StreamBoardExecutionContext>) {
  const onExecuteDecision = useCallback(async (selected: InboxCard[]) => {
    const x = ctxRef.current;
    x.setIsExecuting(true);
    try {
      const selectedCards = selected as InboxCard[];
      const now = new Date().toISOString();
      const conflicts = selectedCards.map((card) => card.conflictDetail).filter(Boolean) as string[];
      const proposals = selectedCards.filter((card) => card.cardType === "auditor-proposal" && card.proposal?.sql_patch);
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

      if (conflicts.length === 0 && proposals.length === 0) {
        await x.typewriterResultLine("⚪ 未选择任何冲合项/提案，本轮不触发终极判词。");
        return;
      }

      x.setConfirmedConflicts(conflicts);
      x.setResolvedCardIds((prev) => [...new Set([...prev, ...selectedCards.map((card) => card.id)])]);

      x.setStreamingText(
        proposals.length > 0 && conflicts.length === 0
          ? `${x.t("已确认")} 审计员提案，正在执行参数校准…`
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
              },
            }),
          });
        } catch {
          /* DB 不可用时本地乐观流程足够 */
        }
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
        await x.onSeedSubmit(x.lastSeedPayload);
        x.setAuditorProposalCards([]);
        x.setConfirmedDecisionIds([]);
        x.setSelectionResetToken((value) => value + 1);

        const verdict = await x.generateFinalVerdict(
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
        if ((verdict.body || "").trim()) {
          await x.typewriterResultLine(`${x.t("✅ 终极判词：")}${verdict.body}`, 18);
          x.setStreamingText(x.t("全局裁决完成，终极判词已生成。"));
          x.setConclusionVersion((value) => value + 1);
          x.setSummaryChanged(Boolean(x.lastConclusionText && x.lastConclusionText !== verdict.body));
          x.setLastConclusionText(verdict.body);
          x.setFinalVerdictBody(verdict.body);
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
              body: verdict.body,
              changeLog: verdict.changeLog || {},
              logicalEvidence: verdict.logicalEvidence || [],
              createdAt: new Date().toISOString(),
            },
          ]);
          x.appendFinalVerdictAuditItem(verdict.versionId || `v1.${x.conclusionVersion + 1}`, verdict.auditLog, new Date().toISOString());
          mergeVerdictIntoLabSnapshot(x, verdict, verdict.body);
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

      if (conflicts.length > 0) {
        const verdict = await x.generateFinalVerdict(
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
        const safeVerdict = (verdict.body || "").trim()
          ? verdict.body
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
  }, [ctxRef]);

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
      await onExecuteDecision(selected);
      await refreshVerdict(selected);
    },
    [onExecuteDecision, refreshVerdict],
  );

  return {
    onExecuteDecision,
    rerunFinalVerdictWithWeights,
    refreshVerdict,
    executeDecisionAndRefresh,
  };
}
