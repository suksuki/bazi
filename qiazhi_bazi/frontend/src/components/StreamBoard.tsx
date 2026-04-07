"use client";

import useSWR from "swr";
import { useEffect, useMemo, useRef, useState } from "react";
import { mapConflictDetail } from "@/constants/termMap";
import { AuditSidebar, type AuditItem } from "@/components/AuditSidebar";
import { BaziCard } from "@/components/BaziCard";
import { DecisionInbox } from "@/components/DecisionInbox";
import { TenGodNumericList } from "@/components/TenGodNumericList";
import { ArbiterLogicDrawer } from "@/components/ArbiterLogicDrawer";
import { LogDrawer } from "@/components/LogDrawer";
import { SeedInput } from "@/components/SeedInput";
import { AuditorBriefing } from "@/components/AuditorBriefing";
import type { BaziMetadata, DecisionStep, Lang, TimelineSnapshot } from "@/types/bazi";

const API_BASE = process.env.NEXT_PUBLIC_QIAZHI_API ?? "http://127.0.0.1:8001";
const ADMIN_TOKEN = process.env.NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN ?? "";
const adminHeaders: Record<string, string> = ADMIN_TOKEN ? { "X-Admin-Token": ADMIN_TOKEN } : {};
const fetcher = (url: string) => fetch(url).then((r) => r.json());
const VERDICT_TIMEOUT_MS = 15000;
const TRANSLATION_DEBOUNCE_MS = 500;
const TRANSLATION_CACHE_MAX = 200;

function calculateFireEnergyAfterConflicts(
  pillars: NonNullable<BaziMetadata["pillars"]> | null | undefined,
  conflicts: string[],
) {
  if (!pillars) return 100;
  const hasZiWu = conflicts.some((x) => x.includes("子午冲"));
  if (!hasZiWu) return 100;
  const monthBranch = pillars.month.branch;
  if (monthBranch === "子") return 40;
  if (monthBranch === "午") return 70;
  return 55;
}

const I18N: Record<Lang, { title: string; subtitle: string }> = {
  ZH: { title: "掐指一算", subtitle: "对话即推演，卡片即逻辑" },
  EN: { title: "Qiazhi-Bazi", subtitle: "Dialogue as inference, cards as logic." },
  KO: { title: "Qiazhi-Bazi", subtitle: "대화는 추론, 카드는 논리." },
};

const STATIC_I18N: Record<Lang, Record<string, string>> = {
  ZH: {},
  EN: {
    "历史": "History",
    "流式对话与决策卡片": "Streaming dialogue and decision cards",
    "批量勾选后，一次性执行全局裁决。": "Select in batch, then execute a global decision once.",
    "暂无可裁决冲合项。": "No actionable clash/combine items.",
    "已认同": "Accepted",
    "执行中...": "Executing...",
    "执行全局裁决": "Execute Global Decision",
    "已选": "Selected",
    "项": "items",
    "等待确认后生成阶段结论…": "Awaiting confirmation to generate stage conclusion...",
    "动态命盘卡片": "Dynamic Bazi Card",
    "点击地支查看辩证": "Click branch to inspect",
    "命盘卡片将在输入后出现。": "The chart card will appear after input.",
    "大运": "Luck Pillar",
    "流年": "Annual Pillar",
    "暂无冲突点。": "No conflict points.",
    "Audit Sidebar": "Audit Sidebar",
    "权力三角：Arbiter / Core / Auditor": "Power Triangle: Arbiter / Core / Auditor",
    "DB(本地)": "DB(本地)",
    "LLM(0.10)": "LLM(0.10)",
    "等待交互步骤…": "Waiting for interaction steps...",
    "Step": "Step",
    "Decision History": "Decision History",
    "关闭": "Close",
    "暂无历史记录。": "No history records.",
    "记录回滚事件": "Record rollback event",
    "仅本地撤销": "Local undo only",
    "The Seed": "The Seed",
    "输入生日后，系统将进入流式推演。": "After entering birth data, the system starts streaming inference.",
    "公历": "Solar",
    "农历": "Lunar",
    "日期时刻": "Date & Time",
    "年": "Y",
    "月": "M",
    "日": "D",
    "时": "H",
    "分": "Min",
    "推演中…": "Inferring...",
    "掐指一算": "Analyze",
    "Decision Inbox": "Decision Inbox",
    "Atomic Conflicts Checklist": "Atomic Conflicts Checklist",
    "Result Summary": "Result Summary",
  },
  KO: {
    "历史": "기록",
    "流式对话与决策卡片": "스트리밍 대화 및 의사결정 카드",
    "批量勾选后，一次性执行全局裁决。": "일괄 선택 후 전역 판정을 한 번에 실행합니다.",
    "暂无可裁决冲合项。": "판정 가능한 충·합 항목이 없습니다.",
    "已认同": "승인됨",
    "执行中...": "실행 중...",
    "执行全局裁决": "전역 판정 실행",
    "已选": "선택",
    "项": "개",
    "等待确认后生成阶段结论…": "확인 후 단계 결론이 생성됩니다…",
    "动态命盘卡片": "동적 명반 카드",
    "点击地支查看辩证": "지지를 눌러 확인",
    "命盘卡片将在输入后出现。": "입력 후 명반 카드가 표시됩니다.",
    "大运": "대운",
    "流年": "세운",
    "暂无冲突点。": "충돌 포인트 없음.",
    "Audit Sidebar": "감사 사이드바",
    "权力三角：Arbiter / Core / Auditor": "권한 삼각: Arbiter / Core / Auditor",
    "DB(本地)": "DB(本地)",
    "LLM(0.10)": "LLM(0.10)",
    "等待交互步骤…": "상호작용 단계를 기다리는 중…",
    "Step": "단계",
    "Decision History": "결정 이력",
    "关闭": "닫기",
    "暂无历史记录。": "이력 없음.",
    "记录回滚事件": "롤백 이벤트 기록",
    "仅本地撤销": "로컬만 취소",
    "The Seed": "입력 시드",
    "输入生日后，系统将进入流式推演。": "생년월일 입력 후 시스템이 스트리밍 추론을 시작합니다.",
    "公历": "양력",
    "农历": "음력",
    "日期时刻": "날짜/시간",
    "年": "년",
    "月": "월",
    "日": "일",
    "时": "시",
    "分": "분",
    "推演中…": "추론 중…",
    "掐指一算": "분석 시작",
    "Decision Inbox": "결정 인박스",
    "Atomic Conflicts Checklist": "원자 충돌 체크리스트",
    "Result Summary": "결과 요약",
    "[KO] 결과 추출에 실패했습니다. (结果提取失败)": "[KO] 결과 추출에 실패했습니다. (结果提取失败)",
  },
};

export function StreamBoard() {
  type LogicProposal = {
    title?: string;
    param_key?: string;
    suggested_value?: number;
    reason?: string;
    expected_impact?: string;
    sql_patch?: string;
    source_role?: string;
  };
  type InboxCard = {
    id: string;
    title: string;
    markdown: string;
    conflictDetail?: string;
    displayText?: string;
    cardType?: "conflict" | "auditor-proposal" | "proposal";
    proposal?: LogicProposal;
  };
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
  const [llmModelName, setLlmModelName] = useState<string>("LLM");
  const [resultLogs, setResultLogs] = useState<string[]>([]);
  const [confirmedConflicts, setConfirmedConflicts] = useState<string[]>([]);
  const [firstPromptText, setFirstPromptText] = useState("");
  const [timeline, setTimeline] = useState<TimelineSnapshot | null>(null);
  const [translations, setTranslations] = useState<Record<string, string>>({});
  const [isExecuting, setIsExecuting] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [i18nCalls, setI18nCalls] = useState(0);
  const [deityScores, setDeityScores] = useState<Record<string, number>>({});
  const [deityEnergyAxes, setDeityEnergyAxes] = useState<Record<string, { absolute_energy?: number; relative_percentage?: number }>>({});
  const [deityComponents, setDeityComponents] = useState<Record<string, {
    total_score?: number;
    stem_score?: number;
    root_score?: number;
    root_sources?: string[];
    stem_sources?: string[];
    is_floating?: boolean;
  }>>({});
  const [deityTraceDetails, setDeityTraceDetails] = useState<Record<string, Record<string, unknown>>>({});
  const [hoveredDeity, setHoveredDeity] = useState<string | undefined>(undefined);
  const [physicsAudit, setPhysicsAudit] = useState<Record<string, unknown> | null>(null);
  const [showPhysicsAudit, setShowPhysicsAudit] = useState(false);
  const [llmDiagnosticLoading, setLlmDiagnosticLoading] = useState(false);
  const [llmDiagnosticError, setLlmDiagnosticError] = useState("");
  const [llmDiagnosticData, setLlmDiagnosticData] = useState<{
    diagnosis?: string;
    alignment_score?: number;
    top_anomaly?: string;
    causal_reasoning?: string;
    tuning_suggestions?: string[];
    sql_patch?: string;
    refresh_hint?: string;
    structured_hit?: boolean;
    repair_mode?: string;
    logic_proposal?: LogicProposal;
  } | null>(null);
  const [lastSeedPayload, setLastSeedPayload] = useState<{ date: string; time: string; calendar: "solar" | "lunar" } | null>(null);
  const [auditorProposalCards, setAuditorProposalCards] = useState<InboxCard[]>([]);
  const [physicsParams, setPhysicsParams] = useState<Record<string, number>>({});
  const [autoConvertedParamKey, setAutoConvertedParamKey] = useState<string | null>(null);
  const [resolvedCardIds, setResolvedCardIds] = useState<string[]>([]);
  const [selectionResetToken, setSelectionResetToken] = useState(0);
  const [conclusionVersion, setConclusionVersion] = useState(0);
  const [lastConclusionText, setLastConclusionText] = useState("");
  const [summaryChanged, setSummaryChanged] = useState(false);
  const [consensusHistory, setConsensusHistory] = useState<Array<{ decision_key: string; confirmed_value?: number; reasoning?: string }>>([]);
  const [finalVerdictBody, setFinalVerdictBody] = useState("");
  const [finalVerdictChangeLog, setFinalVerdictChangeLog] = useState<{
    physics_diff?: string[];
    consensus_diff?: string[];
    text_diff_hint?: string;
  }>({});
  const [finalVerdictVersionId, setFinalVerdictVersionId] = useState("");
  const [finalLogicalEvidence, setFinalLogicalEvidence] = useState<string[]>([]);
  const [finalVerdictHistory, setFinalVerdictHistory] = useState<Array<{
    versionId: string;
    body: string;
    changeLog: { physics_diff?: string[]; consensus_diff?: string[]; text_diff_hint?: string };
    logicalEvidence: string[];
    createdAt: string;
  }>>([]);
  const [logicDrawerOpen, setLogicDrawerOpen] = useState(false);
  const [logicDrawerTitle, setLogicDrawerTitle] = useState("Arbiter Logic Drawer");
  const [logicDrawerFocus, setLogicDrawerFocus] = useState("");
  const [logicDrawerDetails, setLogicDrawerDetails] = useState<string[]>([]);
  const [logicDrawerTrace, setLogicDrawerTrace] = useState<Record<string, unknown> | null>(null);
  const translationCacheRef = useRef<Map<string, string>>(new Map());
  const pendingTextsRef = useRef<Set<string>>(new Set());
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const t = (s: string) => translations[s] ?? STATIC_I18N[lang]?.[s] ?? s;

  const { data: historyData, mutate } = useSWR<{ items: DecisionStep[] } | null>(
    `${API_BASE}/api/history`,
    fetcher,
    { revalidateOnFocus: false, shouldRetryOnError: false }
  );

  useEffect(() => () => {
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
  }, []);

  const cards = useMemo<InboxCard[]>(() => {
    if (!metadata) return [];
    const detected = metadata.conflict_matrix.points.map((p, i) => ({
      id: `conflict-${i}-${p.detail}`,
      title: `冲突确认：${p.detail}`,
      conflictDetail: p.detail,
      markdown: mapConflictDetail(`系统检测到 ${p.detail}。请选择是否深入分析该局部。`, lang),
      displayText: mapConflictDetail(p.detail, lang),
      cardType: "conflict" as const,
    }));
    const sentenceItems = firstPromptText
      .replace(/\r/g, "")
      .split(/\n+/)
      .flatMap((line) => line.split(/(?<=[。！？!?])/))
      .map((x) => x.trim())
      .filter(Boolean)
      .slice(0, 4)
      .map((text, idx) => ({
        id: `llm-observe-${idx}`,
        title: `判词观察项 ${idx + 1}`,
        conflictDetail: text,
        markdown: text,
        displayText: text,
        cardType: "conflict" as const,
      }));
    const proposalCards = auditorProposalCards.map((c, idx) => ({
      ...c,
      id: c.id || `auditor-proposal-${idx}-${c.title}`,
      cardType: "auditor-proposal" as const,
    }));
    let mergedCards: InboxCard[];
    if (detected.length > 0 || sentenceItems.length > 0 || proposalCards.length > 0) {
      mergedCards = [...proposalCards, ...detected, ...sentenceItems];
    } else {
      mergedCards = [
      {
        id: "fallback-deep-scan",
        title: "继续深度扫描",
        conflictDetail: "未见明显冲合，进入深层扫描",
        markdown: "当前未检测到六冲/六合，是否继续执行深层结构扫描？",
        displayText: t("未见明显冲合，进入深层扫描"),
        cardType: "conflict" as const,
      },
      ];
    }
    return mergedCards.filter((c) => !resolvedCardIds.includes(c.id));
  }, [metadata, firstPromptText, lang, translations, auditorProposalCards, t, resolvedCardIds]);
  const pendingDecisionCount = cards.filter((c) => c.id !== "fallback-deep-scan").length;
  const l1Certified = Boolean(llmDiagnosticData?.alignment_score && llmDiagnosticData.alignment_score > 80) && pendingDecisionCount === 0;
  const hardRouteLogs = useMemo<string[]>(
    () => ((((physicsAudit as { trace?: { hard_route_logs?: string[] } } | null)?.trace?.hard_route_logs) || []) as string[]),
    [physicsAudit]
  );

  function cacheKey(l: Lang, text: string) {
    return `${l}::${text}`;
  }

  function isAlreadyTargetLanguage(text: string, target: Lang) {
    if (!text) return false;
    if (target === "KO") return /[\uac00-\ud7a3]/.test(text);
    if (target === "EN") return /^[\x00-\x7F\s.,!?;:'"()[\]{}\-_/]+$/.test(text);
    return /[\u4e00-\u9fff]/.test(text);
  }

  function writeTranslationCache(key: string, value: string) {
    const cache = translationCacheRef.current;
    cache.set(key, value);
    if (cache.size > TRANSLATION_CACHE_MAX) {
      const oldestKey = cache.keys().next().value as string | undefined;
      if (oldestKey) cache.delete(oldestKey);
    }
  }

  function resolveLocalTermTranslation(text: string): string | null {
    const byStatic = STATIC_I18N[lang]?.[text];
    if (byStatic) return byStatic;
    const byTermMap = mapConflictDetail(text, lang);
    if (byTermMap !== text) return byTermMap;
    return null;
  }

  async function flushTranslationQueue() {
    if (lang === "ZH" || isExecuting || isStreaming) return;
    const queued = Array.from(pendingTextsRef.current);
    pendingTextsRef.current.clear();
    if (queued.length === 0) return;
    const remoteNeeded: string[] = [];
    const merged: Record<string, string> = {};
    for (const raw of queued) {
      const text = raw.trim();
      if (!text) continue;
      const key = cacheKey(lang, text);
      const cached = translationCacheRef.current.get(key);
      if (cached) {
        merged[text] = cached;
        continue;
      }
      const local = resolveLocalTermTranslation(text);
      if (local) {
        merged[text] = local;
        writeTranslationCache(key, local);
        continue;
      }
      if (isAlreadyTargetLanguage(text, lang)) {
        merged[text] = text;
        writeTranslationCache(key, text);
        continue;
      }
      remoteNeeded.push(text);
    }
    if (Object.keys(merged).length > 0) {
      setTranslations((prev) => ({ ...prev, ...merged }));
    }
    if (remoteNeeded.length === 0) return;
    try {
      setI18nCalls((n) => n + 1);
      const r = await fetch(`${API_BASE}/api/i18n/translate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ texts: remoteNeeded, target_lang: lang }),
      });
      const j = await r.json();
      const items = (j?.items ?? []) as string[];
      if (Array.isArray(items) && items.length === remoteNeeded.length) {
        setTranslations((prev) => {
          const next = { ...prev };
          remoteNeeded.forEach((k, i) => {
            next[k] = items[i];
            writeTranslationCache(cacheKey(lang, k), items[i]);
          });
          return next;
        });
      }
    } catch {
      // ignore
    }
  }

  function enqueueTranslations(texts: string[]) {
    if (lang === "ZH" || isExecuting || isStreaming) return;
    texts.forEach((x) => {
      const s = (x || "").trim();
      if (s) pendingTextsRef.current.add(s);
    });
    if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    debounceTimerRef.current = setTimeout(() => {
      void flushTranslationQueue();
    }, TRANSLATION_DEBOUNCE_MS);
  }

  useEffect(() => {
    const uiTexts = [
      "掐指一算",
      "对话即推演，卡片即逻辑",
      "历史",
      "流式对话与决策卡片",
      "批量勾选后，一次性执行全局裁决。",
      "暂无可裁决冲合项。",
      "已认同",
      "执行中...",
      "执行全局裁决",
      "已选",
      "项",
      "等待确认后生成阶段结论…",
      "动态命盘卡片",
      "点击地支查看辩证",
      "命盘卡片将在输入后出现。",
      "大运",
      "流年",
      "暂无冲突点。",
      "Audit Sidebar",
      "权力三角：Arbiter / Core / Auditor",
      "DB(本地)",
      "LLM(0.10)",
      "等待交互步骤…",
      "Step",
      "Decision History",
      "关闭",
      "暂无历史记录。",
      "记录回滚事件",
      "仅本地撤销",
      "The Seed",
      "输入生日后，系统将进入流式推演。",
      "公历",
      "农历",
      "日期时刻",
      "年",
      "月",
      "日",
      "时",
      "分",
      "推演中…",
      "第一波：物理排盘中…",
      "第二波：特征扫描中…",
      "扫描完毕，发现",
      "处冲合特征，正在生成首条判词…",
      "全局裁决完成，终极判词已生成。",
      "已记录回滚事件（审计追加，不删除历史）。",
      "回滚事件写入失败：",
      "已确认",
      "，正在执行全局裁决…",
      "✅ 终极判词：",
      "[KO] 결과 추출에 실패했습니다. (结果提取失败)",
    ];
    if (lang === "ZH") {
      setTranslations({});
      return;
    }
    enqueueTranslations(uiTexts);
  }, [lang]);

  useEffect(() => {
    if (lang === "ZH" || isExecuting) return;
    const dynamicTexts = [
      ...cards.map((c) => c.conflictDetail || c.title),
      ...auditItems.map((x) => x.action),
      ...resultLogs,
    ];
    enqueueTranslations(dynamicTexts);
  }, [lang, cards, auditItems, resultLogs, isExecuting, isStreaming]);

  async function refreshHealth() {
    let dbOk = false;
    let llmOk = false;
    try {
      const dbR = await fetch(`${API_BASE}/api/admin/db-status`, { headers: adminHeaders });
      const dbJ = await dbR.json();
      dbOk = Boolean(dbJ?.ok);
    } catch {
      dbOk = false;
    }
    try {
      const cfgR = await fetch(`${API_BASE}/api/admin/runtime-config`, { headers: adminHeaders });
      const cfgJ = await cfgR.json();
      const llm = cfgJ?.config?.llm ?? {};
      setLlmModelName(String(llm.model || "LLM"));
      const mR = await fetch(`${API_BASE}/api/admin/llm-models`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...adminHeaders },
        body: JSON.stringify({ base_url: llm.base_url, api_key: llm.api_key }),
      });
      const mJ = await mR.json();
      llmOk = Boolean(mJ?.ok && Array.isArray(mJ?.models));
    } catch {
      llmOk = false;
      setLlmModelName("LLM");
    }
    setHealth({ dbOk, llmOk });
  }

  async function onSeedSubmit(payload: { date: string; time: string; calendar: "solar" | "lunar" }) {
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
    setShowPhysicsAudit(false);
    setAuditorProposalCards([]);
    setResolvedCardIds([]);
    setPhysicsParams({});
    setConfirmedConflicts([]);
    setFirstPromptText("");
    setTimeline(null);
    setI18nCalls(0);
    setLlmDiagnosticLoading(false);
    setLlmDiagnosticError("");
    setLlmDiagnosticData(null);
    setFinalVerdictBody("");
    setFinalVerdictChangeLog({});
    setFinalVerdictVersionId("");
    setFinalLogicalEvidence([]);
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
        const c = await fetch(`${API_BASE}/api/consultations`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            subject_ref: null,
            input_meta: { ...payload, source: "seed_input" },
          }),
        });
        if (c.ok) {
          const cj = await c.json();
          setConsultationId(cj.id as number);
          currentSessionId = cj.id as number;
        }
      } catch {
        // 记录失败不应阻断推演主链路
      }
      setStreamingText(t("第二波：特征扫描中…"));
      const body = {
        date: payload.date,
        time: payload.time,
        calendar: payload.calendar,
        lang,
        latitude: 31.2304,
        longitude: 121.4737,
        session_id: currentSessionId ?? undefined,
      };
      const r = await fetch(`${API_BASE}/api/v1/analyze-seed`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!r.ok) throw new Error(await r.text());
      const j = await r.json();
      setMetadata(j.metadata as BaziMetadata);
      setTimeline((j.timeline ?? null) as TimelineSnapshot | null);
      if (j.physics_tensor?.normalized) {
        const n = j.physics_tensor.normalized as Record<string, number>;
        setResultLogs((prev) => [
          ...prev,
          `⚙️ 能量矩阵(木火土金水)：${n.wood ?? 0}/${n.fire ?? 0}/${n.earth ?? 0}/${n.metal ?? 0}/${n.water ?? 0}`,
        ]);
      }
      if (j.physics_tensor?.deity_scores) {
        setDeityScores(j.physics_tensor.deity_scores as Record<string, number>);
      }
      if (j.physics_tensor?.deity_energy_axes) {
        setDeityEnergyAxes(j.physics_tensor.deity_energy_axes as Record<string, { absolute_energy?: number; relative_percentage?: number }>);
      } else {
        setDeityEnergyAxes({});
      }
      if (j.physics_tensor?.deity_components) {
        setDeityComponents(j.physics_tensor.deity_components as Record<string, {
          total_score?: number;
          stem_score?: number;
          root_score?: number;
          root_sources?: string[];
          stem_sources?: string[];
          is_floating?: boolean;
        }>);
      } else {
        setDeityComponents({});
      }
      if (j.physics_tensor?.deity_trace_details) {
        setDeityTraceDetails(j.physics_tensor.deity_trace_details as Record<string, Record<string, unknown>>);
      } else if (j.physics_tensor?.meta?.deity_trace_details) {
        setDeityTraceDetails(j.physics_tensor.meta.deity_trace_details as Record<string, Record<string, unknown>>);
      } else {
        setDeityTraceDetails({});
      }
      if (j.physics_tensor?.audit_log) {
        setPhysicsAudit(j.physics_tensor.audit_log as Record<string, unknown>);
      }
      if (j.physics_tensor?.meta?.params) {
        setPhysicsParams(j.physics_tensor.meta.params as Record<string, number>);
      }
      if (j.metadata && j.physics_tensor) {
        setLlmDiagnosticLoading(true);
        setLlmDiagnosticError("");
        try {
          const auditR = await fetch(`${API_BASE}/api/v1/audit-physics-with-llm`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              metadata: j.metadata,
              physics_tensor: j.physics_tensor,
              lang,
              consensus_history: consensusHistory,
              session_id: currentSessionId ?? undefined,
            }),
          });
          const auditJ = await auditR.json();
          if (!auditR.ok) {
            throw new Error(String(auditJ?.detail ?? "audit-physics-with-llm failed"));
          }

          // 智能预案：严重偏差时自动把提案塞入 Decision Inbox，供角色1统一勾选裁决
          const lp = auditJ?.logic_proposal as LogicProposal | undefined;
          const structuredHit = Boolean(auditJ?.structured_hit);
          const alignment = typeof auditJ?.alignment_score === "number" ? auditJ.alignment_score : Number(auditJ?.alignment_score);
          const shouldAutoConvert =
            Boolean(lp?.param_key) && structuredHit && Number.isFinite(alignment) && alignment < 40.0;
          if (shouldAutoConvert && lp) {
            setAutoConvertedParamKey(lp.param_key || null);
            addAuditorProposalToInbox(lp);
          }

          setLlmDiagnosticData({
            diagnosis: auditJ?.diagnosis,
            alignment_score: auditJ?.alignment_score,
            top_anomaly: auditJ?.top_anomaly,
            causal_reasoning: auditJ?.causal_reasoning,
            tuning_suggestions: auditJ?.tuning_suggestions,
            sql_patch: auditJ?.sql_patch,
            refresh_hint: auditJ?.refresh_hint,
            logic_proposal: auditJ?.logic_proposal,
            structured_hit: auditJ?.structured_hit,
            repair_mode: auditJ?.repair_mode,
          });
        } catch (err) {
          setLlmDiagnosticError(err instanceof Error ? err.message : String(err));
        } finally {
          setLlmDiagnosticLoading(false);
        }
      }
      const incoming = (j.audit_summary ?? []) as Array<{
        step?: string;
        role: "Arbiter" | "Core" | "Auditor";
        action: string;
        timestamp: string;
        payload?: unknown;
      }>;
      if (incoming.length >= 3) {
        const mapped: AuditItem[] = incoming.map((x, idx) => ({
          id: `${x.role}-${x.timestamp}-${idx}`,
          step: x.step,
          role: x.role,
          action: x.action,
          timestamp: x.timestamp,
          payload: x.role === "Auditor"
            ? {
                ...(x.payload && typeof x.payload === "object" ? (x.payload as Record<string, unknown>) : {}),
                model_name: String(
                  (x.payload && typeof x.payload === "object" && "model_name" in x.payload)
                    ? (x.payload as { model_name?: string }).model_name || llmModelName
                    : llmModelName
                ),
                param_version_id: String(j?.physics_tensor?.audit_log?.param_version_id || "--"),
              }
            : x.payload,
        }));
        // 步进式渲染：先 01，再 02，再 03
        setAuditItems([mapped[0]]);
        await new Promise((resolve) => setTimeout(resolve, 220));
        setAuditItems([mapped[0], mapped[1]]);
        await new Promise((resolve) => setTimeout(resolve, 220));
        setAuditItems([mapped[0], mapped[1], mapped[2]]);
      }
      setStreamingText(`${t("扫描完毕，发现")} ${(j.metadata?.conflict_matrix?.points ?? []).length} ${t("处冲合特征，正在生成首条判词…")}`);
      setFirstPromptText(j.llm_prompt || "");
      await typewriter(j.llm_prompt || "");
    } catch (e) {
      await typewriter(`${t("连接后端失败：")}${e instanceof Error ? e.message : String(e)}`);
    } finally {
      setBusy(false);
      setIsStreaming(false);
    }
  }

  async function typewriter(fullText: string) {
    for (let i = 0; i < fullText.length; i += 1) {
      setStreamingText(fullText.slice(0, i + 1));
      // 轻量打字机效果
      await new Promise((resolve) => setTimeout(resolve, 10));
    }
  }

  async function typewriterResultLine(line: string, delayMs = 8) {
    setIsStreaming(true);
    setResultLogs((prev) => [...prev, ""]);
    for (let i = 0; i < line.length; i += 1) {
      const current = line.slice(0, i + 1);
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
      const selectedPayload = selectedCards.map((c) => ({
        id: c.id,
        title: c.title,
        cardType: c.cardType || "conflict",
        displayText: c.displayText || c.conflictDetail || c.title,
      }));
      const r = await fetch(`${API_BASE}/api/v1/final-verdict`, {
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
      const j = await r.json();
      if (r.ok && j?.verdict_body) {
        return {
          body: String(j.verdict_body),
          changeLog: {
            physics_diff: Array.isArray(j?.change_log?.physics_diff) ? j.change_log.physics_diff.map((x: unknown) => String(x)) : [],
            consensus_diff: Array.isArray(j?.change_log?.consensus_diff) ? j.change_log.consensus_diff.map((x: unknown) => String(x)) : [],
            text_diff_hint: String(j?.change_log?.text_diff_hint || ""),
          },
          logicalEvidence: Array.isArray(j.logical_evidence) ? j.logical_evidence.map((x: unknown) => String(x)) : [],
          versionId: String(j.version_id || ""),
        };
      }
    } catch {
      // fallback
    }
    return {
      body: [
        "### 核心气象",
        `四柱主轴受 ${conflicts.join("、") || "既定校准项"} 牵动，结构进入高张力区。`,
        "### 裁决共识",
        "已依据本轮确认项完成参数校准并重算，当前断言以更新后物理真值为准。",
        "### 行为指引",
        "执行节奏应先稳后进：先修结构短板，再借顺势年份做放大决策。",
      ].join("\n"),
      changeLog: { text_diff_hint: "Fallback：终判服务异常，已使用保底全量断言。" },
      logicalEvidence: [],
      versionId: "",
    };
  }

  async function onExecuteDecision(selected: any[]) {
    setIsExecuting(true);
    try {
      const selectedCards = selected as InboxCard[];
      const now = new Date().toISOString();
      const conflicts = selectedCards.map((x) => x.conflictDetail).filter(Boolean) as string[];
      const proposals = selectedCards.filter((x) => x.cardType === "auditor-proposal" && x.proposal?.sql_patch);
      if (proposals.length > 0) {
        setConsensusHistory((prev) => [
          ...prev,
          ...proposals
            .map((p) => ({
              decision_key: String(p.proposal?.param_key || ""),
              confirmed_value: typeof p.proposal?.suggested_value === "number" ? p.proposal?.suggested_value : undefined,
              reasoning: String(p.proposal?.reason || p.proposal?.expected_impact || ""),
            }))
            .filter((x) => x.decision_key),
        ]);
      }
      const hasAny = conflicts.length > 0 || proposals.length > 0;
      if (!hasAny) {
        await typewriterResultLine("⚪ 未选择任何冲合项/提案，本轮不触发终极判词。");
        return;
      }
      setConfirmedConflicts(conflicts);
      setResolvedCardIds((prev) => [...new Set([...prev, ...selectedCards.map((x) => x.id)])]);

      const answer = proposals.length > 0 && conflicts.length === 0 ? `确认 ${proposals.length} 项审计员提案` : `批量确认 ${conflicts.length} 项`;
      const newStep: DecisionStep = {
        id: `execute-decision-${now}`,
        title: "execute-decision",
        answer,
        createdAt: now,
      };
      setSteps((prev) => [newStep, ...prev]);
      setStreamingText(
        proposals.length > 0 && conflicts.length === 0
          ? `${t("已确认")} 审计员提案，正在执行参数校准…`
          : `${t("已确认")} ${conflicts.join("、")}${t("，正在执行全局裁决…")}`
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
                selected_proposals: proposals.map((p) => p.proposal),
              },
            }),
          });
        } catch {
          // DB 离线时走前端内存态，避免阻塞终极判词生成
        }
      }
      for (const p of proposals) {
        const ret = await applyPhysicsSqlPatch(p.proposal?.sql_patch || "");
        if (!ret.ok) {
          await typewriterResultLine(`❌ 参数建议执行失败：${ret.error}`);
          setStreamingText(`参数校准失败：${ret.error}`);
          return;
        }
      }

      if (proposals.length > 0 && lastSeedPayload) {
        await typewriterResultLine("🧬 参数校准已执行，系统正在按新物理常数重算…", 18);
        setStreamingText("系统逻辑已接收裁决，正在自动重算...");
        await onSeedSubmit(lastSeedPayload);
        setAuditorProposalCards([]);
        setSelectionResetToken((n) => n + 1);

        const recalculatedVerdict = await generateFinalVerdict(conflicts, selectedCards);
        if ((recalculatedVerdict.body || "").trim()) {
          await typewriterResultLine(`${t("✅ 终极判词：")}${recalculatedVerdict.body}`, 18);
          setStreamingText(t("全局裁决完成，终极判词已生成。"));
          setConclusionVersion((v) => v + 1);
          setSummaryChanged(Boolean(lastConclusionText && lastConclusionText !== recalculatedVerdict.body));
          setLastConclusionText(recalculatedVerdict.body);
          setFinalVerdictBody(recalculatedVerdict.body);
          setFinalVerdictChangeLog(recalculatedVerdict.changeLog || {});
          setFinalLogicalEvidence(recalculatedVerdict.logicalEvidence || []);
          setFinalVerdictVersionId(recalculatedVerdict.versionId || "");
          setFinalVerdictHistory((prev) => [
            ...prev,
            {
              versionId: recalculatedVerdict.versionId || `v1.${conclusionVersion + 1}`,
              body: recalculatedVerdict.body,
              changeLog: recalculatedVerdict.changeLog || {},
              logicalEvidence: recalculatedVerdict.logicalEvidence || [],
              createdAt: new Date().toISOString(),
            },
          ]);
        }

        setAuditItems((prev) => [
          ...prev,
          {
            id: `arbiter-step-${Date.now()}`,
            step: "04",
            role: "Arbiter",
            action: `执行审计员提案参数校准（共确认 ${proposals.length} 项）`,
            timestamp: now,
            payload: { selected_proposals: proposals.map((p) => p.proposal) },
          },
        ]);
        await mutate();
        return;
      }

      if (conflicts.length > 0) {
        const verdict = await generateFinalVerdict(conflicts, selectedCards);
        const safeVerdict = (verdict.body || "").trim()
          ? verdict.body
          : (lang === "KO" ? t("[KO] 결과 추출에 실패했습니다. (结果提取失败)") : "结果提取失败，请稍后重试。");
        await typewriterResultLine(`${t("✅ 终极判词：")}${safeVerdict}`, 18);
        setStreamingText(t("全局裁决完成，终极判词已生成。"));
        setConclusionVersion((v) => v + 1);
        setSummaryChanged(Boolean(lastConclusionText && lastConclusionText !== safeVerdict));
        setLastConclusionText(safeVerdict);
        setFinalVerdictBody(safeVerdict);
        setFinalVerdictChangeLog(verdict.changeLog || {});
        setFinalLogicalEvidence(verdict.logicalEvidence || []);
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
      }
      setAuditorProposalCards((prev) => prev.filter((c) => !selectedCards.some((s) => s.id === c.id)));
      setSelectionResetToken((n) => n + 1);
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
          const r = await fetch(`${API_BASE}/api/decision-steps/rollback`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              target_step_id: targetId,
              reason: "user rollback from drawer",
            }),
          });
          if (!r.ok) {
            throw new Error(await r.text());
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
        } catch (e) {
          setStreamingText(`${t("回滚事件写入失败：")}${e instanceof Error ? e.message : String(e)}`);
          return;
        }
      }
    }
    // 本地临时步骤仍可即时移除
    setSteps((prev) => prev.filter((s) => s.id !== id));
  }

  const mergedSteps = historyData?.items?.length ? [...steps, ...historyData.items] : steps;

  async function applyPhysicsSqlPatch(sqlPatch: string): Promise<{ ok: boolean; error?: string }> {
    if (!sqlPatch.trim()) {
      return { ok: false, error: "缺少可执行 SQL 补丁" };
    }
    const r = await fetch(`${API_BASE}/api/admin/apply-physics-sql`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...adminHeaders },
      body: JSON.stringify({ sql_patch: sqlPatch, auto_refresh: true }),
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok || !j?.ok) {
      const maybeAuthHint =
        r.status === 401
          ? "（请检查 NEXT_PUBLIC_QIAZHI_ADMIN_TOKEN / QIAZHI_ADMIN_TOKEN 配置）"
          : "";
      return { ok: false, error: `${String(j?.detail ?? "apply physics sql failed")}${maybeAuthHint}` };
    }
    setResultLogs((prev) => [
      ...prev,
      `🛠️ 已应用参数建议：${j?.updated?.param_key ?? "unknown"} -> ${j?.updated?.new_value ?? "?"}`,
    ]);
    return { ok: true };
  }

  function addAuditorProposalToInbox(proposal: LogicProposal) {
    const paramKey = proposal?.param_key || "";
    if (!paramKey) return;
    setAuditorProposalCards((prev) => {
      const already = prev.some((c) => c.proposal?.param_key === paramKey);
      if (already) return prev;
      return [
        {
          id: `auditor-proposal-${Date.now()}`,
          title: proposal.title?.trim() ? proposal.title : "参数校准",
          markdown: `${proposal.reason || ""}\n预期影响：${proposal.expected_impact || ""}`.trim(),
          conflictDetail: proposal.reason || "",
          displayText: proposal.param_key ? `参数校准：${proposal.param_key}` : "Auditor 提案参数校准",
          cardType: "auditor-proposal",
          proposal,
        },
        ...prev,
      ];
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
    const hit = deityNames.find((d) => text.includes(d));
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
      .map((x, idx) => `#${idx + 1} ${x.versionId} @ ${new Date(x.createdAt).toLocaleString()}`)
      .concat(["---"])
      .concat(
        finalVerdictHistory.flatMap((x) => [
          `【${x.versionId}】`,
          x.body,
          ...((x.changeLog?.physics_diff || []).map((c) => `[物理] ${c}`)),
          ...((x.changeLog?.consensus_diff || []).map((c) => `[共识] ${c}`)),
          ...(x.changeLog?.text_diff_hint ? [`[判词] ${x.changeLog.text_diff_hint}`] : []),
          ...((x.logicalEvidence || []).slice(0, 6).map((e) => `[证据] ${e}`)),
          "",
        ])
      );
    openLogicDrawer({
      title: "Result Summary 版本回放",
      focus: "Final Verdict History",
      details: lines,
    });
  }

  return (
    <main className="mx-auto min-h-dvh w-full max-w-[1400px] px-3 py-4">
      <header className="mb-3 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">{t(I18N[lang].title)}</h1>
          <p className="text-xs text-zinc-500">{t(I18N[lang].subtitle)}</p>
          <span className="mt-1 inline-flex rounded-md border border-emerald-500/40 bg-emerald-500/10 px-2 py-0.5 text-[10px] text-emerald-300">
            Layer 1 Fully Aligned
          </span>
        </div>
        <div className="flex items-center gap-1">
          {(["ZH", "EN", "KO"] as const).map((k) => (
            <button
              key={k}
              type="button"
              onClick={() => setLang(k)}
              className={`rounded-md px-2 py-1 text-xs ${lang === k ? "bg-amber-500 text-zinc-950" : "bg-zinc-800 text-zinc-300"}`}
            >
              {k}
            </button>
          ))}
          <button
            type="button"
            onClick={() => setDrawerOpen(true)}
            className="ml-1 rounded-md bg-zinc-800 px-2 py-1 text-xs text-zinc-300"
          >
            {t("历史")}
          </button>
        </div>
      </header>
      <div className="flex flex-col gap-3 md:flex-row">
        <AuditSidebar
          items={auditItems}
          dbOk={health.dbOk}
          llmOk={health.llmOk}
          llmModelName={llmModelName}
          i18nCalls={i18nCalls}
          sessionId={consultationId}
          t={t}
          topSlot={(
            <BaziCard
              metadata={metadata}
              timeline={timeline}
              deityScores={deityScores}
              deityEnergyAxes={deityEnergyAxes}
              rootDetailsByDeity={deityComponents}
              hoveredDeity={hoveredDeity}
              selected={selectedBranch}
              confirmedConflictDetails={confirmedConflicts}
              onPickBranch={setSelectedBranch}
              t={t}
              lang={lang}
            />
          )}
          middleSlot={Object.keys(deityScores).length > 0 ? (
            <div className="relative">
              <TenGodNumericList
                deityScores={deityScores}
                deityEnergyAxes={deityEnergyAxes}
                deityComponents={deityComponents}
                deityTraceDetails={deityTraceDetails}
                topAnomaly={llmDiagnosticData?.top_anomaly}
                consensusHistory={consensusHistory}
                hardRouteLogs={hardRouteLogs}
                onOpenLogic={openLogicDrawer}
                onHoverDeity={setHoveredDeity}
              />
            </div>
          ) : null}
        />
        <div className="flex-1 space-y-3">
          <SeedInput onSubmit={onSeedSubmit} busy={busy} t={t} />
          {llmDiagnosticData?.logic_proposal ? (
            <AuditorBriefing
              t={t}
              causalReasoning={llmDiagnosticData.causal_reasoning}
              tuningSuggestions={llmDiagnosticData.tuning_suggestions}
              logicProposal={llmDiagnosticData.logic_proposal}
              currentParams={physicsParams}
              alreadyAdded={auditorProposalCards.some((c) => c.proposal?.param_key === llmDiagnosticData.logic_proposal?.param_key)}
              autoConverted={autoConvertedParamKey === llmDiagnosticData.logic_proposal?.param_key}
              alignmentScore={llmDiagnosticData.alignment_score}
              structuredHit={llmDiagnosticData.structured_hit}
              repairMode={llmDiagnosticData.repair_mode}
              onAddToInbox={(proposal) => addAuditorProposalToInbox(proposal)}
            />
          ) : null}
          <DecisionInbox
            cards={cards}
            resultLogs={resultLogs}
            verdictBody={finalVerdictBody}
            verdictChangeLog={finalVerdictChangeLog}
            logicalEvidence={finalLogicalEvidence}
            highlightVerdict={false}
            onExecuteDecision={onExecuteDecision}
            onVerdictDeityClick={openLogicDrawerByDeity}
            onEvidenceClick={onEvidenceItemClick}
            onShowVersionHistory={showVerdictHistory}
            hasVerdictHistory={finalVerdictHistory.length > 1}
            selectionResetToken={selectionResetToken}
            summaryVersionLabel={`${finalVerdictVersionId || `Conclusion v1.${conclusionVersion}`} (Based on Physics v${String((physicsAudit as { param_version_id?: string } | null)?.param_version_id || "--").slice(0, 8)})`}
            summaryChanged={summaryChanged}
            l1Certified={l1Certified}
            t={t}
          />
          {physicsAudit ? (
            <div className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-3">
              <button
                type="button"
                onClick={() => setShowPhysicsAudit((v) => !v)}
                className="rounded border border-zinc-700 bg-zinc-800 px-2 py-1 text-xs text-zinc-300"
              >
                {showPhysicsAudit ? "隐藏审计链路" : "查看审计链路"}
              </button>
              {showPhysicsAudit ? (
                <pre className="mt-2 max-h-64 overflow-auto rounded border border-zinc-800 bg-zinc-950 p-2 text-[11px] text-zinc-300">
                  {JSON.stringify(physicsAudit, null, 2)}
                </pre>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>

      <LogDrawer open={drawerOpen} steps={mergedSteps} onClose={() => setDrawerOpen(false)} onRollback={onRollback} t={t} />
      <ArbiterLogicDrawer
        open={logicDrawerOpen}
        title={logicDrawerTitle}
        focus={logicDrawerFocus}
        details={logicDrawerDetails.length ? logicDrawerDetails : [llmDiagnosticData?.causal_reasoning || "暂无批注内容。"]}
        deityTrace={logicDrawerTrace}
        auditSource={physicsAudit}
        onClose={() => setLogicDrawerOpen(false)}
        onApplySql={async () => {
          const ret = await applyPhysicsSqlPatch(llmDiagnosticData?.sql_patch || "");
          if (!ret.ok) {
            await typewriterResultLine(`❌ 参数建议执行失败：${ret.error}`);
            setStreamingText(`参数校准失败：${ret.error}`);
          }
        }}
      />
    </main>
  );
}
