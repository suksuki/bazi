"use client";

import useSWR from "swr";
import { useEffect, useMemo, useRef, useState } from "react";
import { mapConflictDetail } from "@/constants/termMap";
import { AuditSidebar, type AuditItem } from "@/components/AuditSidebar";
import { BaziCard } from "@/components/BaziCard";
import { DecisionInbox } from "@/components/DecisionInbox";
import { LogDrawer } from "@/components/LogDrawer";
import { SeedInput } from "@/components/SeedInput";
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
    "DB(0.13)": "DB(0.13)",
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
    "DB(0.13)": "DB(0.13)",
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
  const [resultLogs, setResultLogs] = useState<string[]>([]);
  const [confirmedConflicts, setConfirmedConflicts] = useState<string[]>([]);
  const [firstPromptText, setFirstPromptText] = useState("");
  const [timeline, setTimeline] = useState<TimelineSnapshot | null>(null);
  const [translations, setTranslations] = useState<Record<string, string>>({});
  const [isExecuting, setIsExecuting] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [i18nCalls, setI18nCalls] = useState(0);
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

  const cards = useMemo(() => {
    if (!metadata) return [];
    const detected = metadata.conflict_matrix.points.map((p, i) => ({
      id: `conflict-${i}-${p.detail}`,
      title: `冲突确认：${p.detail}`,
      conflictDetail: p.detail,
      markdown: mapConflictDetail(`系统检测到 ${p.detail}。请选择是否深入分析该局部。`, lang),
      displayText: mapConflictDetail(p.detail, lang),
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
      }));
    if (detected.length > 0 || sentenceItems.length > 0) return [...detected, ...sentenceItems];
    return [
      {
        id: "fallback-deep-scan",
        title: "继续深度扫描",
        conflictDetail: "未见明显冲合，进入深层扫描",
        markdown: "当前未检测到六冲/六合，是否继续执行深层结构扫描？",
        displayText: t("未见明显冲合，进入深层扫描"),
      },
    ];
  }, [metadata, firstPromptText, lang, translations]);

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
      "DB(0.13)",
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
      const mR = await fetch(`${API_BASE}/api/admin/llm-models`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...adminHeaders },
        body: JSON.stringify({ base_url: llm.base_url, api_key: llm.api_key }),
      });
      const mJ = await mR.json();
      llmOk = Boolean(mJ?.ok && Array.isArray(mJ?.models));
    } catch {
      llmOk = false;
    }
    setHealth({ dbOk, llmOk });
  }

  async function onSeedSubmit(payload: { date: string; time: string; calendar: "solar" | "lunar" }) {
    setBusy(true);
    setIsStreaming(true);
    setStreamingText("");
    setAuditItems([]);
    setResultLogs([]);
    setConfirmedConflicts([]);
    setFirstPromptText("");
    setTimeline(null);
    setI18nCalls(0);
    await refreshHealth();
    try {
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
          payload: x.payload,
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

  async function generateFinalVerdict(conflicts: string[]) {
    const pillars = metadata?.pillars;
    const pillarText = pillars
      ? `${pillars.year.stem}${pillars.year.branch} / ${pillars.month.stem}${pillars.month.branch} / ${pillars.day.stem}${pillars.day.branch} / ${pillars.hour.stem}${pillars.hour.branch}`
      : "未知";
    const timelineText = timeline
      ? `大运=${timeline.dayun}，流年(${timeline.reference_year})=${timeline.liunian}`
      : "大运流年未知";
    const fireEnergy = calculateFireEnergyAfterConflicts(pillars, conflicts);
    const langConstraint =
      lang === "EN"
        ? "Please output strictly in English Markdown."
        : lang === "KO"
          ? "한국어 마크다운으로만 출력해 주세요."
          : "请严格使用中文 Markdown 输出。";
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), VERDICT_TIMEOUT_MS);
      const r = await fetch(`${API_BASE}/api/llm/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          messages: [
            {
              role: "system",
              content:
                "你是Qiazhi-Bazi系统首席审计员。请基于确定物理事实生成详细终极判词。"
                + "输出必须是 Markdown，并包含小节：命局总览、冲突机制与能量损耗、格局重心与用忌、大运流年触发点、行动建议。"
                + "不要输出思考过程，内容要具体、有判断，不要空话。建议长度 280~420 字。"
                + "禁止使用不确定词：可能、也许、大概、我觉得、从…来看。请使用确定性断语。"
                + langConstraint,
            },
            {
              role: "user",
              content:
                `四柱：${pillarText}\n`
                + `已确认冲突：${conflicts.join("、")}\n`
                + `时空上下文：${timelineText}\n`
                + `当前午火能量已衰减至 ${fireEnergy}%，请据此判定护卫能力。\n`
                + "请给出详细终极判词。",
            },
          ],
          temperature: 0.35,
          max_tokens: 900,
          lang,
        }),
      });
      clearTimeout(timer);
      const j = await r.json();
      if (r.ok && j?.content) return String(j.content);
    } catch {
      // fallback
    }
    return [
      "### 命局总览",
      `四柱主轴受 ${conflicts.join("、")} 牵动，结构进入高张力区。`,
      "### 冲突机制与能量损耗",
      "冲合并发会放大主轴耗泄，先稳住受损最重的核心位，再谈放大优势。",
      "### 格局重心与用忌",
      "当前宜以“调候+制衡”为优先，避免继续叠加耗泄与逆势扩张。",
      "### 大运流年触发点",
      timelineText,
      "### 行动建议",
      "执行节奏应“先稳后进”：先修结构短板，再借顺势年份做放大决策。",
    ].join("\n");
  }

  async function onExecuteDecision(selected: Array<{ id: string; conflictDetail?: string }>) {
    setIsExecuting(true);
    try {
      const now = new Date().toISOString();
      const conflicts = selected.map((x) => x.conflictDetail).filter(Boolean) as string[];
      if (conflicts.length === 0) {
        await typewriterResultLine("⚪ 未选择任何冲合项，本轮不触发终极判词。");
        return;
      }
      setConfirmedConflicts(conflicts);
      const answer = `批量确认 ${conflicts.length} 项`;
      const newStep: DecisionStep = {
        id: `execute-decision-${now}`,
        title: "execute-decision",
        answer,
        createdAt: now,
      };
      setSteps((prev) => [newStep, ...prev]);
      setStreamingText(`${t("已确认")} ${conflicts.join("、")}${t("，正在执行全局裁决…")}`);
      if (consultationId) {
        try {
          await fetch(`${API_BASE}/api/decision-steps`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              consultation_id: consultationId,
              step_type: "execute-decision",
              raw_data: { metadata, selected_conflicts: conflicts },
              human_choice: { action: "execute", selected_conflicts: conflicts },
            }),
          });
        } catch {
          // DB 离线时走前端内存态，避免阻塞终极判词生成
        }
      }
      const verdict = await generateFinalVerdict(conflicts);
      const safeVerdict = verdict.trim()
        ? verdict
        : (lang === "KO" ? t("[KO] 결과 추출에 실패했습니다. (结果提取失败)") : "结果提取失败，请稍后重试。");
      await typewriterResultLine(`${t("✅ 终极判词：")}${safeVerdict}`, 18);
      setStreamingText(t("全局裁决完成，终极判词已生成。"));
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

  return (
    <main className="mx-auto min-h-dvh w-full max-w-[1400px] px-3 py-4">
      <header className="mb-3 flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold">{t(I18N[lang].title)}</h1>
          <p className="text-xs text-zinc-500">{t(I18N[lang].subtitle)}</p>
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
          i18nCalls={i18nCalls}
          sessionId={consultationId}
          t={t}
        />
        <div className="flex-1 space-y-3">
          <SeedInput onSubmit={onSeedSubmit} busy={busy} t={t} />
          <section className="grid gap-3 xl:grid-cols-12">
            <div className="xl:col-span-5">
              <BaziCard
                metadata={metadata}
                timeline={timeline}
                selected={selectedBranch}
                confirmedConflictDetails={confirmedConflicts}
                onPickBranch={setSelectedBranch}
                t={t}
                lang={lang}
              />
            </div>
            <div className="xl:col-span-7">
              <DecisionInbox
                cards={cards}
                resultLogs={resultLogs}
                highlightVerdict={false}
                onExecuteDecision={onExecuteDecision}
                t={t}
              />
            </div>
          </section>
        </div>
      </div>

      <LogDrawer open={drawerOpen} steps={mergedSteps} onClose={() => setDrawerOpen(false)} onRollback={onRollback} t={t} />
    </main>
  );
}
