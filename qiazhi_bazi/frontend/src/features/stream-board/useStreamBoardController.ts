"use client";

import useSWR from "swr";
import { useMemo, useState } from "react";
import type { AuditItem } from "@/components/AuditSidebar";
import type { BaziMetadata, DecisionStep, Lang, TimelineSnapshot } from "@/types/bazi";
import { adminHeaders, API_BASE, fetcher, VERDICT_TIMEOUT_MS } from "./constants";
import { buildInboxCards, createAuditorProposalCard } from "./cardBuilder";
import type {
  DeityComponent,
  DeityEnergyAxis,
  FinalVerdictChangeLog,
  FinalVerdictHistoryItem,
  InboxCard,
  LlmDiagnosticData,
  LogicProposal,
  PhysicsLabConfig,
  SeedPayload,
  StreamBoardViewModel,
} from "./models";
import { buildFallbackVerdict, calculateFireEnergyAfterConflicts } from "./utils";
import { useTranslationQueue } from "./useTranslationQueue";

type ConsensusItem = { decision_key: string; confirmed_value?: number; reasoning?: string };

export function useStreamBoardController(): StreamBoardViewModel {
  const [lang, setLang] = useState<Lang>("ZH");
  const [busy, setBusy] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [selectedBranch, setSelectedBranch] = useState<string>();
  const [metadata, setMetadata] = useState<BaziMetadata | null>(null);
  const [streamingText, setStreamingText] = useState("");
  const [steps, setSteps] = useState<DecisionStep[]>([]);
  const [consultationId, setConsultationId] = useState<number | null>(null);
  const [auditItems, setAuditItems] = useState<AuditItem[]>([]);
  const [health, setHealth] = useState({ dbOk: false, llmOk: false });
  const [llmModelName, setLlmModelName] = useState("LLM");
  const [resultLogs, setResultLogs] = useState<string[]>([]);
  const [confirmedConflicts, setConfirmedConflicts] = useState<string[]>([]);
  const [firstPromptText, setFirstPromptText] = useState("");
  const [timeline, setTimeline] = useState<TimelineSnapshot | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [deityScores, setDeityScores] = useState<Record<string, number>>({});
  const [deityEnergyAxes, setDeityEnergyAxes] = useState<Record<string, DeityEnergyAxis>>({});
  const [deityComponents, setDeityComponents] = useState<Record<string, DeityComponent>>({});
  const [deityTraceDetails, setDeityTraceDetails] = useState<Record<string, Record<string, unknown>>>({});
  const [hoveredDeity, setHoveredDeity] = useState<string>();
  const [physicsAudit, setPhysicsAudit] = useState<Record<string, unknown> | null>(null);
  const [physicsConfidence, setPhysicsConfidence] = useState<number | null>(null);
  const [physicsEvidence, setPhysicsEvidence] = useState<string[]>([]);
  const [labConfig, setLabConfig] = useState<PhysicsLabConfig>({
    WEIGHT_LUCK: 0.4,
    WEIGHT_YEAR: 0.2,
    BASE_BACKFIRE_RISK: 0.2,
    HIGH_IMBALANCE_RISK: 0.35,
    TOMB_LOCK_RATE: 0.9,
  });
  const [showPhysicsAudit, setShowPhysicsAudit] = useState(false);
  const [llmDiagnosticData, setLlmDiagnosticData] = useState<LlmDiagnosticData | null>(null);
  const [lastSeedPayload, setLastSeedPayload] = useState<SeedPayload | null>(null);
  const [auditorProposalCards, setAuditorProposalCards] = useState<InboxCard[]>([]);
  const [physicsParams, setPhysicsParams] = useState<Record<string, number>>({});
  const [autoConvertedParamKey, setAutoConvertedParamKey] = useState<string | null>(null);
  const [resolvedCardIds, setResolvedCardIds] = useState<string[]>([]);
  const [selectionResetToken, setSelectionResetToken] = useState(0);
  const [conclusionVersion, setConclusionVersion] = useState(0);
  const [lastConclusionText, setLastConclusionText] = useState("");
  const [summaryChanged, setSummaryChanged] = useState(false);
  const [consensusHistory, setConsensusHistory] = useState<ConsensusItem[]>([]);
  const [finalVerdictBody, setFinalVerdictBody] = useState("");
  const [finalVerdictChangeLog, setFinalVerdictChangeLog] = useState<FinalVerdictChangeLog>({});
  const [finalVerdictVersionId, setFinalVerdictVersionId] = useState("");
  const [finalLogicalEvidence, setFinalLogicalEvidence] = useState<string[]>([]);
  const [finalWorkVector, setFinalWorkVector] = useState<Record<string, unknown> | null>(null);
  const [finalVerdictHistory, setFinalVerdictHistory] = useState<FinalVerdictHistoryItem[]>([]);
  const [logicDrawerOpen, setLogicDrawerOpen] = useState(false);
  const [logicDrawerTitle, setLogicDrawerTitle] = useState("Arbiter Logic Drawer");
  const [logicDrawerFocus, setLogicDrawerFocus] = useState("");
  const [logicDrawerDetails, setLogicDrawerDetails] = useState<string[]>([]);
  const [logicDrawerTrace, setLogicDrawerTrace] = useState<Record<string, unknown> | null>(null);

  const { data: historyData, mutate } = useSWR<{ items: DecisionStep[] } | null>(
    `${API_BASE}/api/history`,
    fetcher,
    { revalidateOnFocus: false, shouldRetryOnError: false },
  );

  const { i18nCalls, t } = useTranslationQueue({
    lang,
    isExecuting,
    isStreaming,
    dynamicTexts: [
      ...(metadata?.conflict_matrix.points.map((point) => point.detail) || []),
      ...firstPromptText
        .replace(/\r/g, "")
        .split(/\n+/)
        .flatMap((line) => line.split(/(?<=[。！？!?])/))
        .map((item) => item.trim())
        .filter(Boolean)
        .slice(0, 4),
      ...auditorProposalCards.map((card) => card.conflictDetail || card.title),
      ...auditItems.map((item) => item.action),
      ...resultLogs,
    ],
  });

  const cards = useMemo(
    () => buildInboxCards({ metadata, firstPromptText, auditorProposalCards, resolvedCardIds, lang, t }),
    [metadata, firstPromptText, auditorProposalCards, resolvedCardIds, lang, t],
  );

  const pendingDecisionCount = cards.filter((card) => card.id !== "fallback-deep-scan").length;
  const l1Certified = Boolean(llmDiagnosticData?.alignment_score && llmDiagnosticData.alignment_score > 80) && pendingDecisionCount === 0;
  const hardRouteLogs = useMemo<string[]>(
    () => ((((physicsAudit as { trace?: { hard_route_logs?: string[] } } | null)?.trace?.hard_route_logs) || []) as string[]),
    [physicsAudit],
  );

  async function refreshHealth() {
    let dbOk = false;
    let llmOk = false;

    try {
      const dbResponse = await fetch(`${API_BASE}/api/admin/db-status`, { headers: adminHeaders });
      const dbData = await dbResponse.json();
      dbOk = Boolean(dbData?.ok);
    } catch {
      dbOk = false;
    }

    try {
      const configResponse = await fetch(`${API_BASE}/api/admin/runtime-config`, { headers: adminHeaders });
      const configData = await configResponse.json();
      const llm = configData?.config?.llm ?? {};
      setLlmModelName(String(llm.model || "LLM"));

      const modelsResponse = await fetch(`${API_BASE}/api/admin/llm-models`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...adminHeaders },
        body: JSON.stringify({ base_url: llm.base_url, api_key: llm.api_key }),
      });
      const modelsData = await modelsResponse.json();
      llmOk = Boolean(modelsData?.ok && Array.isArray(modelsData?.models));
    } catch {
      llmOk = false;
      setLlmModelName("LLM");
    }

    setHealth({ dbOk, llmOk });
  }

  async function typewriter(fullText: string) {
    for (let index = 0; index < fullText.length; index += 1) {
      setStreamingText(fullText.slice(0, index + 1));
      await new Promise((resolve) => setTimeout(resolve, 10));
    }
  }

  async function typewriterResultLine(line: string, delayMs = 8) {
    setIsStreaming(true);
    setResultLogs((prev) => [...prev, ""]);
    for (let index = 0; index < line.length; index += 1) {
      const current = line.slice(0, index + 1);
      setResultLogs((prev) => {
        const next = [...prev];
        next[next.length - 1] = current;
        return next;
      });
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
    setIsStreaming(false);
  }

  async function generateFinalVerdict(conflicts: string[], selectedCards: InboxCard[] = []) {
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), VERDICT_TIMEOUT_MS);
      const selectedPayload = selectedCards.map((card) => ({
        id: card.id,
        title: card.title,
        cardType: card.cardType || "conflict",
        displayText: card.displayText || card.conflictDetail || card.title,
      }));

      const response = await fetch(`${API_BASE}/api/v1/final-verdict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          metadata: metadata || {},
          physics_tensor: {
            deity_scores: deityScores,
            deity_energy_axes: deityEnergyAxes,
            deity_components: deityComponents,
            deity_trace_details: deityTraceDetails,
            audit_log: physicsAudit || {},
            top_anomaly: llmDiagnosticData?.top_anomaly || "",
            causal_reasoning: llmDiagnosticData?.causal_reasoning || "",
            tuning_suggestions: llmDiagnosticData?.tuning_suggestions || [],
            timeline: timeline || {},
            conflict_list: conflicts || [],
            fire_energy_after_conflict: calculateFireEnergyAfterConflicts(metadata?.pillars, conflicts),
          },
          selected_cards: selectedPayload,
          consensus_history: consensusHistory,
          previous_verdict: finalVerdictBody || lastConclusionText || "",
          previous_logical_evidence: finalLogicalEvidence,
          consultation_id: consultationId ?? undefined,
          lang,
        }),
      });
      clearTimeout(timer);

      const data = await response.json();
      if (response.ok && data?.verdict_body) {
        return {
          body: String(data.verdict_body),
          changeLog: {
            physics_diff: Array.isArray(data?.change_log?.physics_diff) ? data.change_log.physics_diff.map((item: unknown) => String(item)) : [],
            consensus_diff: Array.isArray(data?.change_log?.consensus_diff) ? data.change_log.consensus_diff.map((item: unknown) => String(item)) : [],
            text_diff_hint: String(data?.change_log?.text_diff_hint || ""),
          },
          logicalEvidence: Array.isArray(data.logical_evidence) ? data.logical_evidence.map((item: unknown) => String(item)) : [],
          versionId: String(data.version_id || ""),
          workVector: (data?.work_vector && typeof data.work_vector === "object") ? data.work_vector as Record<string, unknown> : {},
          auditLog: (data?.audit_log && typeof data.audit_log === "object") ? data.audit_log as Record<string, unknown> : {},
        };
      }
    } catch {
      // Fall through to the conservative local fallback below.
    }

    return buildFallbackVerdict(conflicts);
  }

  async function applyPhysicsSqlPatch(sqlPatch: string): Promise<{ ok: boolean; error?: string }> {
    if (!sqlPatch.trim()) {
      return { ok: false, error: "缺少可执行 SQL 补丁" };
    }

    const response = await fetch(`${API_BASE}/api/admin/apply-physics-sql`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...adminHeaders },
      body: JSON.stringify({ sql_patch: sqlPatch, auto_refresh: true }),
    });
    const data = await response.json().catch(() => ({}));

    if (!response.ok || !data?.ok) {
      const maybeAuthHint = response.status === 401
        ? "（请检查 NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN / QIAZHI_ADMIN_TOKEN 配置）"
        : "";
      return { ok: false, error: `${String(data?.detail ?? "apply physics sql failed")}${maybeAuthHint}` };
    }

    setResultLogs((prev) => [
      ...prev,
      `🛠️ 已应用参数建议：${data?.updated?.param_key ?? "unknown"} -> ${data?.updated?.new_value ?? "?"}`,
    ]);
    return { ok: true };
  }

  function addAuditorProposalToInbox(proposal: LogicProposal) {
    const card = createAuditorProposalCard(proposal);
    if (!card) return;

    setAuditorProposalCards((prev) => {
      const alreadyAdded = prev.some((item) => item.proposal?.param_key === proposal.param_key);
      return alreadyAdded ? prev : [card, ...prev];
    });
  }

  function openLogicDrawer(payload: { title: string; focus: string; details: string[]; deityTrace?: Record<string, unknown> }) {
    setLogicDrawerTitle(payload.title);
    setLogicDrawerFocus(payload.focus);
    setLogicDrawerDetails(payload.details);
    setLogicDrawerTrace(payload.deityTrace || null);
    setLogicDrawerOpen(true);
  }

  function openLogicDrawerByDeity(deity: string) {
    const trace = deityTraceDetails?.[deity] as Record<string, unknown> | undefined;
    openLogicDrawer({
      title: `${deity} 演算路径`,
      focus: deity,
      details: [`${deity}: ${Number(deityScores[deity] ?? 0).toFixed(2)}%`, "来自 Result Summary 点击下钻。"],
      deityTrace: trace,
    });
  }

  function onEvidenceItemClick(evidence: string) {
    const text = String(evidence || "");
    const deityNames = ["比肩", "劫财", "食神", "伤官", "正财", "偏财", "正官", "七杀", "正印", "偏印"];
    const hit = deityNames.find((name) => text.includes(name));
    if (hit) {
      openLogicDrawerByDeity(hit);
      return;
    }

    openLogicDrawer({
      title: "证据条目下钻",
      focus: "Logical Evidence",
      details: [text, "该证据暂未映射到特定十神，已展示原始条目。"],
    });
  }

  function showVerdictHistory() {
    if (finalVerdictHistory.length === 0) return;

    const lines = finalVerdictHistory
      .map((item, index) => `#${index + 1} ${item.versionId} @ ${new Date(item.createdAt).toLocaleString()}`)
      .concat(["---"])
      .concat(
        finalVerdictHistory.flatMap((item) => [
          `【${item.versionId}】`,
          item.body,
          ...(item.changeLog.physics_diff || []).map((change) => `[物理] ${change}`),
          ...(item.changeLog.consensus_diff || []).map((change) => `[共识] ${change}`),
          ...(item.changeLog.text_diff_hint ? [`[判词] ${item.changeLog.text_diff_hint}`] : []),
          ...(item.logicalEvidence || []).slice(0, 6).map((evidence) => `[证据] ${evidence}`),
          "",
        ]),
      );

    openLogicDrawer({
      title: "Result Summary 版本回放",
      focus: "Final Verdict History",
      details: lines,
    });
  }

  function appendFinalVerdictAuditItem(versionId: string, auditLog: Record<string, unknown> | undefined, timestamp: string) {
    setAuditItems((prev) => [
      ...prev,
      {
        id: `auditor-final-${Date.now()}`,
        step: "05",
        role: "Auditor",
        action: "终判审计链路已生成",
        timestamp,
        payload: {
          model_name: llmModelName,
          final_verdict_version_id: versionId || "--",
          ...(auditLog || {}),
        },
      },
    ]);
  }

  async function onSeedSubmit(payload: SeedPayload) {
    setLastSeedPayload(payload);
    setBusy(true);
    setIsStreaming(true);
    setAutoConvertedParamKey(null);
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
    setConfirmedConflicts([]);
    setFirstPromptText("");
    setTimeline(null);
    setLlmDiagnosticData(null);
    setFinalVerdictBody("");
    setFinalVerdictChangeLog({});
    setFinalVerdictVersionId("");
    setFinalLogicalEvidence([]);
    setFinalWorkVector(null);
    setFinalVerdictHistory([]);

    await refreshHealth();

    try {
      let currentSessionId = consultationId;
      setStreamingText(t("第一波：物理排盘中…"));
      setAuditItems([
        {
          id: `arbiter-submit-${Date.now()}`,
          step: "01",
          role: "Arbiter",
          action: `提交生辰 ${payload.date} ${payload.time}，请求物理建模。`,
          timestamp: new Date().toISOString(),
          payload,
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
          setConsultationId(consultationData.id as number);
          currentSessionId = consultationData.id as number;
        }
      } catch {
        // Consultation logging should not block the main inference flow.
      }

      setStreamingText(t("第二波：特征扫描中…"));
      const response = await fetch(`${API_BASE}/api/v1/analyze-seed`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          date: payload.date,
          time: payload.time,
          calendar: payload.calendar,
          lang,
          latitude: 31.2304,
          longitude: 121.4737,
          session_id: currentSessionId ?? undefined,
          physics_config: labConfig,
        }),
      });

      if (!response.ok) throw new Error(await response.text());
      const data = await response.json();
      setMetadata(data.metadata as BaziMetadata);
      setTimeline((data.timeline ?? null) as TimelineSnapshot | null);

      if (data.physics_tensor?.normalized) {
        const normalized = data.physics_tensor.normalized as Record<string, number>;
        setResultLogs((prev) => [
          ...prev,
          `⚙️ 能量矩阵(木火土金水)：${normalized.wood ?? 0}/${normalized.fire ?? 0}/${normalized.earth ?? 0}/${normalized.metal ?? 0}/${normalized.water ?? 0}`,
        ]);
      }
      if (data.physics_tensor?.deity_scores) {
        setDeityScores(data.physics_tensor.deity_scores as Record<string, number>);
      }
      if (data.physics_tensor?.deity_energy_axes) {
        setDeityEnergyAxes(data.physics_tensor.deity_energy_axes as Record<string, DeityEnergyAxis>);
      }
      if (data.physics_tensor?.deity_components) {
        setDeityComponents(data.physics_tensor.deity_components as Record<string, DeityComponent>);
      }
      if (data.physics_tensor?.deity_trace_details) {
        setDeityTraceDetails(data.physics_tensor.deity_trace_details as Record<string, Record<string, unknown>>);
      } else if (data.physics_tensor?.meta?.deity_trace_details) {
        setDeityTraceDetails(data.physics_tensor.meta.deity_trace_details as Record<string, Record<string, unknown>>);
      } else {
        setDeityTraceDetails({});
      }
      if (data.physics_tensor?.audit_log) {
        setPhysicsAudit(data.physics_tensor.audit_log as Record<string, unknown>);
      }
      if (typeof data.physics_tensor?.confidence === "number") {
        setPhysicsConfidence(data.physics_tensor.confidence);
      } else {
        setPhysicsConfidence(null);
      }
      if (Array.isArray(data.physics_tensor?.evidence)) {
        setPhysicsEvidence(data.physics_tensor.evidence.map((item: unknown) => String(item)));
      } else {
        setPhysicsEvidence([]);
      }
      if (data.physics_tensor?.meta?.params) {
        setPhysicsParams(data.physics_tensor.meta.params as Record<string, number>);
      }

      if (data.metadata && data.physics_tensor) {
        try {
          const auditResponse = await fetch(`${API_BASE}/api/v1/audit-physics-with-llm`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              metadata: data.metadata,
              physics_tensor: data.physics_tensor,
              lang,
              consensus_history: consensusHistory,
              session_id: currentSessionId ?? undefined,
            }),
          });
          const auditData = await auditResponse.json();
          if (!auditResponse.ok) {
            throw new Error(String(auditData?.detail ?? "audit-physics-with-llm failed"));
          }

          const logicProposal = auditData?.logic_proposal as LogicProposal | undefined;
          const structuredHit = Boolean(auditData?.structured_hit);
          const alignment = typeof auditData?.alignment_score === "number"
            ? auditData.alignment_score
            : Number(auditData?.alignment_score);
          const shouldAutoConvert = Boolean(logicProposal?.param_key) && structuredHit && Number.isFinite(alignment) && alignment < 40;
          if (shouldAutoConvert && logicProposal) {
            setAutoConvertedParamKey(logicProposal.param_key || null);
            addAuditorProposalToInbox(logicProposal);
          }

          setLlmDiagnosticData({
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
        } catch {
          // Keep the main board usable even if the auditor call fails.
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
                    ? (item.payload as { model_name?: string }).model_name || llmModelName
                    : llmModelName,
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

        setAuditItems([mapped[0]]);
        await new Promise((resolve) => setTimeout(resolve, 220));
        setAuditItems([mapped[0], mapped[1]]);
        await new Promise((resolve) => setTimeout(resolve, 220));
        setAuditItems([mapped[0], mapped[1], mapped[2]]);
      }

      setStreamingText(`${t("扫描完毕，发现")} ${(data.metadata?.conflict_matrix?.points ?? []).length} ${t("处冲合特征，正在生成首条判词…")}`);
      setFirstPromptText(data.llm_prompt || "");
      await typewriter(data.llm_prompt || "");
    } catch (error) {
      await typewriter(`${t("连接后端失败：")}${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setBusy(false);
      setIsStreaming(false);
    }
  }

  async function onExecuteDecision(selected: InboxCard[]) {
    setIsExecuting(true);
    try {
      const selectedCards = selected as InboxCard[];
      const now = new Date().toISOString();
      const conflicts = selectedCards.map((card) => card.conflictDetail).filter(Boolean) as string[];
      const proposals = selectedCards.filter((card) => card.cardType === "auditor-proposal" && card.proposal?.sql_patch);
      if (proposals.length > 0) {
        setConsensusHistory((prev) => [
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
        await typewriterResultLine("⚪ 未选择任何冲合项/提案，本轮不触发终极判词。");
        return;
      }

      setConfirmedConflicts(conflicts);
      setResolvedCardIds((prev) => [...new Set([...prev, ...selectedCards.map((card) => card.id)])]);

      const answer = proposals.length > 0 && conflicts.length === 0
        ? `确认 ${proposals.length} 项审计员提案`
        : `批量确认 ${conflicts.length} 项`;
      setSteps((prev) => [
        {
          id: `execute-decision-${now}`,
          title: "execute-decision",
          answer,
          createdAt: now,
        },
        ...prev,
      ]);

      setStreamingText(
        proposals.length > 0 && conflicts.length === 0
          ? `${t("已确认")} 审计员提案，正在执行参数校准…`
          : `${t("已确认")} ${conflicts.join("、")}${t("，正在执行全局裁决…")}`,
      );

      if (consultationId) {
        try {
          await fetch(`${API_BASE}/api/decision-steps`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              consultation_id: consultationId,
              step_type: "execute-decision",
              raw_data: { metadata, selected_conflicts: conflicts },
              human_choice: {
                action: "execute",
                selected_conflicts: conflicts,
                selected_proposals: proposals.map((proposalCard) => proposalCard.proposal),
              },
            }),
          });
        } catch {
          // Local optimistic flow is enough when the DB is unavailable.
        }
      }

      for (const proposalCard of proposals) {
        const result = await applyPhysicsSqlPatch(proposalCard.proposal?.sql_patch || "");
        if (!result.ok) {
          await typewriterResultLine(`❌ 参数建议执行失败：${result.error}`);
          setStreamingText(`参数校准失败：${result.error}`);
          return;
        }
      }

      if (proposals.length > 0 && lastSeedPayload) {
        await typewriterResultLine("🧬 参数校准已执行，系统正在按新物理常数重算…", 18);
        setStreamingText("系统逻辑已接收裁决，正在自动重算...");
        await onSeedSubmit(lastSeedPayload);
        setAuditorProposalCards([]);
        setSelectionResetToken((value) => value + 1);

        const verdict = await generateFinalVerdict(conflicts, selectedCards);
        if ((verdict.body || "").trim()) {
          await typewriterResultLine(`${t("✅ 终极判词：")}${verdict.body}`, 18);
          setStreamingText(t("全局裁决完成，终极判词已生成。"));
          setConclusionVersion((value) => value + 1);
          setSummaryChanged(Boolean(lastConclusionText && lastConclusionText !== verdict.body));
          setLastConclusionText(verdict.body);
          setFinalVerdictBody(verdict.body);
          setFinalVerdictChangeLog(verdict.changeLog || {});
          setFinalLogicalEvidence(verdict.logicalEvidence || []);
          setFinalWorkVector((verdict.workVector as Record<string, unknown>) || null);
          setFinalVerdictVersionId(verdict.versionId || "");
          setFinalVerdictHistory((prev) => [
            ...prev,
            {
              versionId: verdict.versionId || `v1.${conclusionVersion + 1}`,
              body: verdict.body,
              changeLog: verdict.changeLog || {},
              logicalEvidence: verdict.logicalEvidence || [],
              createdAt: new Date().toISOString(),
            },
          ]);
          appendFinalVerdictAuditItem(verdict.versionId || `v1.${conclusionVersion + 1}`, verdict.auditLog, new Date().toISOString());
        }

        setAuditItems((prev) => [
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
        await mutate();
        return;
      }

      if (conflicts.length > 0) {
        const verdict = await generateFinalVerdict(conflicts, selectedCards);
        const safeVerdict = (verdict.body || "").trim()
          ? verdict.body
          : (lang === "KO" ? t("[KO] 结果提取失败。") : "结果提取失败，请稍后重试。");
        await typewriterResultLine(`${t("✅ 终极判词：")}${safeVerdict}`, 18);
        setStreamingText(t("全局裁决完成，终极判词已生成。"));
        setConclusionVersion((value) => value + 1);
        setSummaryChanged(Boolean(lastConclusionText && lastConclusionText !== safeVerdict));
        setLastConclusionText(safeVerdict);
        setFinalVerdictBody(safeVerdict);
        setFinalVerdictChangeLog(verdict.changeLog || {});
        setFinalLogicalEvidence(verdict.logicalEvidence || []);
        setFinalWorkVector((verdict.workVector as Record<string, unknown>) || null);
        setFinalVerdictVersionId(verdict.versionId || "");
        setFinalVerdictHistory((prev) => [
          ...prev,
          {
            versionId: verdict.versionId || `v1.${conclusionVersion + 1}`,
            body: safeVerdict,
            changeLog: verdict.changeLog || {},
            logicalEvidence: verdict.logicalEvidence || [],
            createdAt: new Date().toISOString(),
          },
        ]);
        appendFinalVerdictAuditItem(verdict.versionId || `v1.${conclusionVersion + 1}`, verdict.auditLog, new Date().toISOString());
      }

      setAuditorProposalCards((prev) => prev.filter((card) => !selectedCards.some((selectedCard) => selectedCard.id === card.id)));
      setSelectionResetToken((value) => value + 1);
      setAuditItems((prev) => [
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
      await mutate();
    } finally {
      setIsExecuting(false);
    }
  }

  async function onRollback(id: string) {
    if (id.startsWith("db-")) {
      const targetId = Number(id.slice(3));
      if (Number.isFinite(targetId) && targetId > 0) {
        try {
          const response = await fetch(`${API_BASE}/api/decision-steps/rollback`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              target_step_id: targetId,
              reason: "user rollback from drawer",
            }),
          });
          if (!response.ok) {
            throw new Error(await response.text());
          }
          await mutate();
          setStreamingText(t("已记录回滚事件（审计追加，不删除历史）。"));
          await typewriterResultLine(`↩️ 已记录回滚事件：step#${targetId}，请重新选择裁决路径。`);
          setAuditItems((prev) => [
            ...prev,
            {
              id: `arbiter-rollback-${Date.now()}`,
              step: "05",
              role: "Arbiter",
              action: `触发回滚事件：step#${targetId}`,
              timestamp: new Date().toISOString(),
              payload: { target_step_id: targetId },
            },
          ]);
          return;
        } catch (error) {
          setStreamingText(`${t("回滚事件写入失败：")}${error instanceof Error ? error.message : String(error)}`);
          return;
        }
      }
    }

    setSteps((prev) => prev.filter((step) => step.id !== id));
  }

  async function applyCurrentSqlPatch() {
    const result = await applyPhysicsSqlPatch(llmDiagnosticData?.sql_patch || "");
    if (!result.ok) {
      await typewriterResultLine(`❌ 参数建议执行失败：${result.error}`);
      setStreamingText(`参数校准失败：${result.error}`);
    }
  }

  async function applyLabConfigAndRecalculate() {
    if (!lastSeedPayload) return;
    setResultLogs((prev) => [...prev, `🧪 实验参数已应用：luck=${labConfig.WEIGHT_LUCK}, year=${labConfig.WEIGHT_YEAR}`]);
    await onSeedSubmit(lastSeedPayload);
  }

  const mergedSteps = historyData?.items?.length ? [...steps, ...historyData.items] : steps;

  return {
    lang,
    setLang,
    busy,
    drawerOpen,
    setDrawerOpen,
    consultationId,
    metadata,
    timeline,
    selectedBranch,
    setSelectedBranch,
    auditItems,
    health,
    llmModelName,
    i18nCalls,
    deityScores,
    deityEnergyAxes,
    deityComponents,
    deityTraceDetails,
    hoveredDeity,
    setHoveredDeity,
    confirmedConflicts,
    llmDiagnosticData,
    physicsParams,
    auditorProposalCards,
    autoConvertedParamKey,
    consensusHistory,
    cards,
    resultLogs,
    finalVerdictBody,
    finalVerdictChangeLog,
    finalLogicalEvidence,
    finalWorkVector,
    finalVerdictHistory,
    selectionResetToken,
    finalVerdictVersionId,
    conclusionVersion,
    summaryChanged,
    l1Certified,
    physicsAudit,
    physicsConfidence,
    physicsEvidence,
    labConfig,
    setLabConfig,
    showPhysicsAudit,
    setShowPhysicsAudit,
    mergedSteps,
    logicDrawerOpen,
    logicDrawerTitle,
    logicDrawerFocus,
    logicDrawerDetails,
    logicDrawerTrace,
    setLogicDrawerOpen,
    onSeedSubmit,
    addAuditorProposalToInbox,
    onExecuteDecision,
    openLogicDrawer,
    openLogicDrawerByDeity,
    onEvidenceItemClick,
    showVerdictHistory,
    onRollback,
    applyCurrentSqlPatch,
    applyLabConfigAndRecalculate,
    t,
  };
}
