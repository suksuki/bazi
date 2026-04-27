"use client";

import { useState } from "react";
import { BriefcaseBusiness, CalendarRange, ChevronDown, FileSearch, Sparkles, TrendingUp } from "lucide-react";

import { jsonPostInit, requestJson } from "@/lib/apiClient";
import type { AppLanguage } from "@/lib/i18n";

type LocalizeText = (zh: string, en: string, ko: string) => string;
type TranslateText = (value: string) => string;
type WealthPreviewMode = "llm" | "contract" | "";

function asLooseRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function asNumberValue(value: unknown, fallback = 0): number {
  const next = Number(value);
  return Number.isFinite(next) ? next : fallback;
}

function asStringList(value: unknown): string[] {
  return Array.isArray(value) ? value.map((item) => String(item || "").trim()).filter(Boolean) : [];
}

function asRecordList(value: unknown): Array<Record<string, unknown>> {
  return Array.isArray(value) ? value.map(asLooseRecord).filter((row) => Object.keys(row).length > 0) : [];
}

function percentLabel(value: unknown): string {
  const raw = asNumberValue(value);
  const normalized = raw <= 1 ? raw * 100 : raw;
  return `${Math.round(normalized)}%`;
}

function localizedWealthStance(value: unknown, ui: LocalizeText): string {
  const key = String(value || "").trim();
  if (key === "active") return ui("机会明显", "Clear opportunity", "기회 뚜렷");
  if (key === "volatile") return ui("机会有波动", "Volatile opportunity", "기회 변동");
  if (key === "watch") return ui("需要观察", "Needs watching", "관찰 필요");
  if (key === "latent") return ui("信号偏弱", "Weak signal", "신호 약함");
  return ui("未定", "Pending", "미정");
}


function localizedPathSize(value: unknown, ui: LocalizeText): string {
  const key = String(value || "").trim();
  if (key === "大") return ui("大（主路径）", "Large (top)", "대(주)");
  if (key === "中") return ui("中（次级）", "Medium", "중(보통)");
  if (key === "小") return ui("小（低）", "Small", "소(낮음)");
  return ui("待观察", "Pending", "관찰");
}

function pathSizeToneClass(value: unknown): string {
  const key = String(value || "").trim();
  if (key === "大") return "bg-emerald-400/12 text-emerald-100 border-emerald-300/35";
  if (key === "中") return "bg-cyan-400/12 text-cyan-100 border-cyan-300/30";
  if (key === "小") return "bg-zinc-400/12 text-zinc-100 border-zinc-300/30";
  return "bg-white/10 text-zinc-300 border-white/15";
}

function localizedWealthUsableState(value: unknown, ui: LocalizeText): string {
  const key = String(value || "").trim();
  if (key === "wealth_as_use") return ui("容易落地", "Easier to land", "실현 쉬움");
  if (key === "wealth_as_taboo") return ui("先控风险", "Risk first", "위험 우선");
  if (key === "wealth_needs_bridge") return ui("先补条件", "Build conditions", "조건 필요");
  return ui("待观察", "Watch", "관찰");
}

function localizedWealthVisibility(value: unknown, ui: LocalizeText): string {
  const key = String(value || "").trim();
  if (key === "explicit_wealth") return ui("收入机会清晰", "Clear income path", "수입 경로 명확");
  if (key === "hidden_wealth") return ui("靠能力转化", "Skill conversion", "능력 전환");
  if (key === "indirect_wealth") return ui("靠平台/专业", "Platform/profession", "플랫폼/전문성");
  return ui("弱信号", "Weak signal", "약한 신호");
}

function wealthResultReasonLabel(value: unknown, ui: LocalizeText): string {
  const reason = String(value || "").trim();
  if (reason === "execute_llm_disabled") return ui("仅生成提示词", "Prompt only", "프롬프트만 생성");
  if (reason === "missing_wealth_profile") return ui("缺少财富分析", "Missing analysis", "분석 없음");
  if (reason === "llm_config_incomplete") return ui("模型未配置", "Model not configured", "모델 미설정");
  if (reason === "llm_dispatch_failed") return ui("调用失败", "Dispatch failed", "호출 실패");
  if (reason === "not_dispatched") return ui("未调用", "Not dispatched", "미호출");
  return reason;
}

function localizedTimelineStance(value: unknown, ui: LocalizeText): string {
  const key = String(value || "").trim();
  if (key === "opportunity_with_pressure") return ui("有机会也要控风险", "Opportunity with risk", "기회와 위험 관리");
  if (key === "opportunity_period") return ui("收入机会较多", "More income chances", "수입 기회 많음");
  if (key === "pressure_period") return ui("先守现金流", "Protect cash flow", "현금흐름 우선");
  if (key === "conversion_period") return ui("能力变现期", "Skill monetization", "능력 수익화");
  if (key === "steady_observation") return ui("稳步经营", "Steady building", "안정 운영");
  return ui("待生成", "Pending", "대기");
}

function localizedAttentionType(value: unknown, ui: LocalizeText): string {
  const key = String(value || "").trim();
  if (key === "opportunity_with_risk") return ui("机会+风控", "Opportunity + risk", "기회+위험");
  if (key === "opportunity") return ui("收入机会", "Income chance", "수입 기회");
  if (key === "risk_watch") return ui("防漏钱", "Leak watch", "돈 새는 곳 주의");
  if (key === "conversion_watch") return ui("变现机会", "Monetization", "수익화");
  if (key === "steady_watch") return ui("稳步经营", "Steady", "안정 운영");
  return ui("关注", "Watch", "관찰");
}

function localizedClosureState(value: unknown, ui: LocalizeText): string {
  const key = String(value || "").trim();
  if (key === "closed") return ui("路径闭合", "Path closed", "경로 완결");
  if (key === "partial_closed") return ui("部分闭合", "Partly closed", "부분 완결");
  if (key === "volatile") return ui("波动", "Volatile", "변동");
  if (key === "open") return ui("未闭合", "Open", "열림");
  if (key === "leaking") return ui("有漏损", "Leaking", "누수");
  if (key === "blocked") return ui("被阻断", "Blocked", "차단");
  return ui("待观察", "Pending", "관찰");
}

function closureStateToneClass(value: unknown): string {
  const key = String(value || "").trim();
  if (key === "closed") return "border-emerald-300/35 bg-emerald-400/12 text-emerald-100";
  if (key === "partial_closed") return "border-cyan-300/30 bg-cyan-400/12 text-cyan-100";
  if (key === "volatile") return "border-amber-300/30 bg-amber-400/10 text-amber-100";
  if (key === "open") return "border-sky-300/25 bg-sky-400/10 text-sky-100";
  if (key === "leaking") return "border-rose-300/30 bg-rose-400/12 text-rose-100";
  return "border-white/15 bg-white/10 text-zinc-100";
}

function attentionToneClass(level: unknown): string {
  const key = String(level || "").trim();
  if (key === "high") return "border-amber-300/35 bg-amber-400/10 text-amber-50";
  if (key === "medium") return "border-cyan-300/25 bg-cyan-400/10 text-cyan-50";
  return "border-white/10 bg-white/[0.035] text-zinc-200";
}

function shortPreviewTime(value: unknown): string {
  const raw = String(value || "").trim();
  if (!raw) return "";
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return raw.slice(0, 16);
  return date.toLocaleString(undefined, {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function graphLabelOf(node: Record<string, unknown> | undefined | null, fallback: string): string {
  const item = asLooseRecord(node);
  const label = String(item.label || "").trim();
  return label || fallback;
}

function graphNodeText(node: Record<string, unknown>): string {
  const nodeType = String(node.type || "").trim();
  const label = graphLabelOf(node, String(node.id || ""));
  if (nodeType === "claim") {
    const source = String(node.plugin_id || "").trim();
    const shortSource = source ? source.split(".").slice(0, 2).join(".") : "";
    const coreLabel = label.includes("#") ? label.split("#").slice(-1)[0] || label : label;
    return shortSource ? `${coreLabel}（${shortSource}）` : coreLabel;
  }
  return label;
}

export function V17_WealthAssertionPreviewPanel({
  ui,
  term,
  language,
  sessionId,
  resetKey,
  wealthProfile,
  initialPreview,
  initialCodePreview,
  initialTimeline,
  canRequest,
  physicsReady,
}: {
  ui: LocalizeText;
  term: TranslateText;
  language: AppLanguage;
  sessionId: string;
  resetKey: string;
  wealthProfile: Record<string, unknown>;
  initialPreview: Record<string, unknown>;
  initialCodePreview: Record<string, unknown>;
  initialTimeline: Record<string, unknown>;
  canRequest: boolean;
  physicsReady: boolean;
}) {
  const [previewOverride, setPreviewOverride] = useState<{ resetKey: string; preview: Record<string, unknown> } | null>(null);
  const [codePreviewOverride, setCodePreviewOverride] = useState<{ resetKey: string; preview: Record<string, unknown> } | null>(null);
  const [timelineOverride, setTimelineOverride] = useState<{ resetKey: string; preview: Record<string, unknown> } | null>(null);
  const [pendingMode, setPendingMode] = useState<WealthPreviewMode>("");
  const [codePending, setCodePending] = useState(false);
  const [timelinePending, setTimelinePending] = useState(false);
  const [errorState, setErrorState] = useState<{ resetKey: string; message: string } | null>(null);

  const preview = previewOverride?.resetKey === resetKey ? previewOverride.preview : initialPreview;
  const codePreview = codePreviewOverride?.resetKey === resetKey ? codePreviewOverride.preview : initialCodePreview;
  const timeline = timelineOverride?.resetKey === resetKey ? timelineOverride.preview : initialTimeline;
  const error = errorState?.resetKey === resetKey ? errorState.message : "";
  const previewProfile = asLooseRecord(preview.wealth_profile);
  const profile = Object.keys(wealthProfile).length ? wealthProfile : previewProfile;
  const channels = Array.isArray(profile.primary_channels)
    ? (profile.primary_channels as Array<unknown>).map(asLooseRecord).filter((row) => String(row.id || row.label || "").trim())
    : [];
  const strengths = asStringList(profile.strengths).slice(0, 3);
  const risks = asStringList(profile.risks).slice(0, 3);
  const bridgeRequirements = asStringList(profile.bridge_requirements).slice(0, 3);
  const evidence = asStringList(profile.evidence).slice(0, 4);
  const llmResult = asLooseRecord(preview.llm_result);
  const promptContract = asLooseRecord(preview.prompt_contract);
  const codeFromPreview = asLooseRecord(preview.wealth_code);
  const codeSummaryFromCodePreview = asLooseRecord(codePreview.wealth_code_summary);
  const wealthCode = Object.keys(codeFromPreview).length
    ? codeFromPreview
    : Object.keys(codeSummaryFromCodePreview).length
      ? codeSummaryFromCodePreview
      : asLooseRecord(codePreview.wealth_code);
  const evidenceGraph = asLooseRecord(wealthCode.evidence_graph) || asLooseRecord(codeSummaryFromCodePreview.evidence_graph);
  const pathSummary = asLooseRecord(codePreview.path_summary);
  const primaryPath = asLooseRecord(wealthCode.primary_wealth_path);
  const wealthSource = asLooseRecord(wealthCode.wealth_source);
  const monetizationEngine = asLooseRecord(wealthCode.monetization_engine);
  const carrier = asLooseRecord(wealthCode.carrier);
  const wealthVault = asLooseRecord(wealthCode.wealth_vault);
  const secondaryPaths = asRecordList(wealthCode.secondary_paths).slice(0, 3);
  const leakagePoints = asRecordList(wealthCode.leakage_points).slice(0, 3);
  const yearWatchlist = asRecordList(wealthCode.flow_year_watchlist).slice(0, 3);
  const mechanismChains = asRecordList(wealthCode.mechanism_chains).slice(0, 2);
  const primaryMechanismChain = mechanismChains[0] || {};
  const pathRankings = asRecordList(wealthCode.path_rankings).slice(0, 5);
  const graphNodes = asRecordList(evidenceGraph.nodes);
  const graphEdges = asRecordList(evidenceGraph.edges);
  const pathNodeIds = new Set(
    [primaryPath.id, ...secondaryPaths.map((row) => row.id)]
      .map((row) => String(row || ""))
      .filter(Boolean),
  );
  const claimNodes = graphNodes.filter((row) => String(row.type || "") === "claim");
  const claimNodeById = new Map<string, Record<string, unknown>>();
  for (const row of claimNodes) {
    const id = String(row.id || "");
    if (id) {
      claimNodeById.set(id, row);
    }
  }
  const claimSupportEdges = graphEdges.filter((row) => {
    const rel = String(row.relation || "");
    const from = String(row.from || "");
    const to = String(row.to || "");
    return rel === "supports" && to && pathNodeIds.has(to) && claimNodeById.has(from);
  });
  const claimSupportRows = claimSupportEdges
    .map((row) => {
      const from = String(row.from || "");
      const to = String(row.to || "");
      const edgeWeight = asNumberValue(row.evidence_weight, 0);
      const target = graphNodes.find((node) => String(node.id || "") === to) || ({ id: to } as Record<string, unknown>);
      const source = claimNodeById.get(from) || ({ id: from } as Record<string, unknown>);
      return { from: graphNodeText(source), to: graphLabelOf(target, ui("待识别路径", "Unknown path", "미확인 경로")), relation: String(row.relation || ""), weight: edgeWeight, rule: String(row.rule_id || ""), id: `${from}->${to}:${String(row.rule_id || "")}` };
    })
    .sort((left, right) => right.weight - left.weight)
    .slice(0, 6);
  const primaryClaims = asRecordList(primaryPath.claim_supports).slice(0, 6);
  const hasWealthCode = Object.keys(wealthCode).length > 0;
  const displayChannels = hasWealthCode
    ? [
        {
          id: String(primaryPath.id || "primary_wealth_path"),
          label: String(primaryPath.plain_name || pathSummary.primary_path_label || ui("主要财富路径", "Main wealth path", "주 재물 경로")),
          score: primaryPath.score ?? wealthCode.score,
        },
        ...secondaryPaths.map((row) => ({
          id: String(row.id || row.plain_name || row.plain_summary || ""),
          label: String(row.plain_name || row.plain_summary || row.id || ""),
          score: row.score,
        })),
      ].filter((row) => row.id || row.label)
    : channels;
  const topChannel = displayChannels[0] || {};
  const luckWindow = asLooseRecord(timeline.luck_window);
  const currentFlow = asLooseRecord(timeline.current_flow);
  const topAttentionYears = asRecordList(timeline.top_attention_years).slice(0, 4);
  const decadeYears = asRecordList(timeline.decade_years).slice(0, 10);
  const reply = String(llmResult.reply || "").trim();
  const promptText = String(preview.prompt_text || "").trim();
  const previewCreatedAt = String(preview.created_at || "").trim();
  const timelineCreatedAt = String(timeline.created_at || "").trim();
  const hasProfile = Object.keys(profile).length > 0;
  const hasPreview = Object.keys(preview).length > 0;
  const hasTimeline = Object.keys(timeline).length > 0;
  const timelineReady = Boolean(timeline.timeline_ready);
  const canSubmit = canRequest && physicsReady && Boolean(sessionId) && !pendingMode;
  const canCodeSubmit = canRequest && physicsReady && Boolean(sessionId) && !codePending;
  const canTimelineSubmit = canRequest && physicsReady && Boolean(sessionId) && !timelinePending;
  const score = percentLabel(profile.score);
  const confidence = percentLabel(profile.confidence);
  const risk = percentLabel(profile.risk);

  async function requestPreview(executeLlm: boolean) {
    if (!canRequest) {
      setErrorState({ resetKey, message: ui("需要管理员权限。", "Admin access required.", "관리자 권한이 필요합니다.") });
      return;
    }
    if (!sessionId || !physicsReady) {
      setErrorState({ resetKey, message: ui("等待命盘快照。", "Waiting for chart snapshot.", "명반 스냅샷 대기 중입니다.") });
      return;
    }
    const mode: WealthPreviewMode = executeLlm ? "llm" : "contract";
    setPendingMode(mode);
    setErrorState(null);
    await requestCodePreview({ silent: true });
    const { data, ok, error: requestError } = await requestJson<Record<string, unknown>>(
      "/api/v17-admin/topic/wealth-assertion-preview",
      jsonPostInit({
        v17_origin: "v17_rebirth",
        session_id: sessionId,
        ui_lang: language,
        execute_llm: executeLlm,
        persist: true,
      }),
    );
    setPendingMode("");
    const nextPreview = asLooseRecord(data.preview);
    if (!ok || data.ok === false || !Object.keys(nextPreview).length) {
      setErrorState({
        resetKey,
        message: requestError || String(data.detail || "") || ui("财富解读生成失败。", "Failed to create wealth reading.", "재물 해석을 만들지 못했습니다."),
      });
      return;
    }
    setPreviewOverride({ resetKey, preview: nextPreview });
  }

  async function requestCodePreview({ silent = false }: { silent?: boolean } = {}) {
    if (!canRequest) {
      if (!silent) setErrorState({ resetKey, message: ui("需要管理员权限。", "Admin access required.", "관리자 권한이 필요합니다.") });
      return null;
    }
    if (!sessionId || !physicsReady) {
      if (!silent) setErrorState({ resetKey, message: ui("等待命盘快照。", "Waiting for chart snapshot.", "명반 스냅샷 대기 중입니다.") });
      return null;
    }
    setCodePending(true);
    if (!silent) setErrorState(null);
    const { data, ok, error: requestError } = await requestJson<Record<string, unknown>>(
      "/api/v17-admin/topic/wealth-code-preview",
      jsonPostInit({
        v17_origin: "v17_rebirth",
        session_id: sessionId,
        persist: true,
      }),
    );
    setCodePending(false);
    const nextPreview = asLooseRecord(data.preview);
    if (!ok || data.ok === false || !Object.keys(nextPreview).length) {
      if (!silent) {
        setErrorState({
          resetKey,
          message: requestError || String(data.detail || "") || ui("财富路径生成失败。", "Failed to build wealth path.", "재물 경로 생성에 실패했습니다."),
        });
      }
      return null;
    }
    setCodePreviewOverride({ resetKey, preview: nextPreview });
    return nextPreview;
  }

  async function requestTimeline() {
    if (!canRequest) {
      setErrorState({ resetKey, message: ui("需要管理员权限。", "Admin access required.", "관리자 권한이 필요합니다.") });
      return;
    }
    if (!sessionId || !physicsReady) {
      setErrorState({ resetKey, message: ui("等待命盘快照。", "Waiting for chart snapshot.", "명반 스냅샷 대기 중입니다.") });
      return;
    }
    setTimelinePending(true);
    setErrorState(null);
    const { data, ok, error: requestError } = await requestJson<Record<string, unknown>>(
      "/api/v17-admin/topic/wealth-timeline-preview",
      jsonPostInit({
        v17_origin: "v17_rebirth",
        session_id: sessionId,
        persist: true,
      }),
    );
    setTimelinePending(false);
    const nextPreview = asLooseRecord(data.preview);
    if (!ok || data.ok === false || !Object.keys(nextPreview).length) {
      setErrorState({
        resetKey,
        message: requestError || String(data.detail || "") || ui("十年参考生成失败。", "Failed to build decade notes.", "10년 참고 생성에 실패했습니다."),
      });
      return;
    }
    setTimelineOverride({ resetKey, preview: nextPreview });
  }

  return (
    <section className="rounded-xl border border-emerald-400/18 bg-[linear-gradient(135deg,rgba(6,78,59,0.22),rgba(24,24,27,0.92)_48%,rgba(120,53,15,0.18))] p-4 shadow-[0_18px_60px_rgba(6,78,59,0.12)]">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-emerald-300/20 bg-emerald-400/10 text-emerald-100">
              <BriefcaseBusiness className="h-4 w-4" />
            </span>
            <div>
              <p className="text-[10px] uppercase tracking-[0.22em] text-emerald-300">
                {ui("财富专题", "Wealth Topic", "재물 주제")}
              </p>
              <h3 className="mt-0.5 text-base font-semibold text-zinc-50">
                {ui("财富机会与风险", "Wealth Opportunity & Risk", "재물 기회와 위험")}
              </h3>
            </div>
          </div>
        </div>
        <div className="flex flex-wrap gap-1.5">
          <span className="rounded-full border border-emerald-300/20 bg-emerald-400/10 px-2 py-1 text-[10px] text-emerald-100">
            {hasProfile ? `${ui("收入机会", "Income chance", "수입 기회")} ${score}` : ui("等待分析", "Pending", "대기")}
          </span>
          <span className="rounded-full border border-amber-300/20 bg-amber-400/10 px-2 py-1 text-[10px] text-amber-100">
            {hasPreview ? ui("已有解读", "Reading ready", "해석 있음") : ui("未生成", "Not generated", "미생성")}
          </span>
        </div>
      </div>

      {hasProfile ? (
        <div className="mt-4 grid gap-3 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="space-y-3">
            <div className="flex flex-wrap gap-1.5">
              {[
                `${ui("参考度", "Confidence", "신뢰")} ${confidence}`,
                `${ui("风险", "Risk", "위험")} ${risk}`,
                localizedWealthStance(profile.stance, ui),
                localizedWealthUsableState(profile.usable_state, ui),
                localizedWealthVisibility(profile.visibility, ui),
              ].map((item) => (
                <span key={item} className="rounded-full border border-white/10 bg-black/20 px-2 py-1 text-[11px] text-zinc-200">
                  {item}
                </span>
              ))}
            </div>

            {topChannel.id || topChannel.label ? (
              <div>
                <p className="text-[11px] text-zinc-500">{ui("主要赚钱方式", "Main money path", "주 수입 방식")}</p>
                <p className="mt-1 text-sm font-semibold text-zinc-100">
                  {term(String(topChannel.label || topChannel.id || ""))}
                  <span className="ml-2 text-[11px] font-medium text-emerald-200">{percentLabel(topChannel.score)}</span>
                </p>
              </div>
            ) : null}

            {displayChannels.length ? (
              <div className="space-y-2">
                {displayChannels.slice(0, 3).map((channel) => {
                  const label = term(String(channel.label || channel.id || ""));
                  const width = Math.max(6, Math.min(100, asNumberValue(channel.score) * 100));
                  return (
                    <div key={String(channel.id || label)} className="grid grid-cols-[minmax(0,1fr)_56px] items-center gap-2">
                      <div className="min-w-0">
                        <div className="flex items-center justify-between gap-2 text-[11px] text-zinc-300">
                          <span className="truncate">{label}</span>
                        </div>
                        <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-white/10">
                          <div className="h-full rounded-full bg-emerald-300" style={{ width: `${width}%` }} />
                        </div>
                      </div>
                      <span className="text-right text-[11px] text-emerald-100">{percentLabel(channel.score)}</span>
                    </div>
                  );
                })}
              </div>
            ) : null}
          </div>

          <div className="space-y-3 border-t border-white/10 pt-3 lg:border-l lg:border-t-0 lg:pl-4 lg:pt-0">
            {reply ? (
              <div>
                <div className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-amber-200" />
                  <p className="text-[12px] font-semibold text-amber-50">
                    {ui("财富解读", "Wealth reading", "재물 해석")}
                  </p>
                </div>
                <p className="mt-2 whitespace-pre-line text-sm leading-7 text-zinc-100">{reply}</p>
              </div>
            ) : (
              <div>
                <p className="text-[12px] font-semibold text-zinc-100">
                  {hasPreview
                    ? wealthResultReasonLabel(llmResult.reason, ui)
                    : ui("等待财富解读", "Reading pending", "해석 대기")}
                </p>
                <p className="mt-1 text-[12px] leading-5 text-zinc-500">
                  {String(profile.llm_prompt_focus ? asStringList(profile.llm_prompt_focus)[0] : "") ||
                    ui("财富分析已就绪。", "Wealth analysis is ready.", "재물 분석이 준비되었습니다.")}
                </p>
              </div>
            )}

            <div className="grid gap-2 sm:grid-cols-3">
              {[
                { key: "strengths", label: ui("可以发挥", "Use this", "활용점"), values: strengths },
                { key: "bridge", label: ui("要先做到", "Build first", "먼저 할 것"), values: bridgeRequirements },
                { key: "risks", label: ui("要避开的坑", "Avoid", "피할 점"), values: risks },
              ].map((group) => (
                <div key={group.key} className="min-w-0">
                  <p className="text-[11px] text-zinc-500">{group.label}</p>
                  <div className="mt-1 space-y-1">
                    {group.values.length ? group.values.map((item) => (
                      <p key={`${group.key}_${item}`} className="line-clamp-2 text-[11px] leading-5 text-zinc-300">
                        {term(item)}
                      </p>
                    )) : (
                      <p className="text-[11px] text-zinc-600">{ui("待定", "Pending", "대기")}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <p className="mt-4 text-[12px] leading-5 text-zinc-500">
          {ui("正在等待财富分析数据。", "Waiting for wealth analysis data.", "재물 분석 데이터를 기다립니다.")}
        </p>
      )}

      {hasProfile ? (
        <div className="mt-4 border-t border-white/10 pt-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-[10px] uppercase tracking-[0.2em] text-emerald-300">
                {ui("财富路径", "Wealth Path", "재물 경로")}
              </p>
              <h4 className="mt-0.5 text-sm font-semibold text-zinc-50">
                {hasWealthCode
                  ? term(String(primaryPath.plain_name || pathSummary.primary_path_label || ui("主要财富路径", "Main wealth path", "주 재물 경로")))
                  : ui("等待财富路径解码", "Waiting for wealth-path decoding", "재물 경로 해독 대기")}
              </h4>
            </div>
            <div className="flex flex-wrap gap-1.5">
              <span className="rounded-full border border-emerald-300/20 bg-emerald-400/10 px-2 py-1 text-[10px] text-emerald-100">
                {hasWealthCode ? `${ui("路径闭合", "Path", "경로")} ${percentLabel(wealthCode.score)}` : ui("待生成", "Pending", "대기")}
              </span>
              {hasWealthCode ? (
                <span className="rounded-full border border-amber-300/20 bg-amber-400/10 px-2 py-1 text-[10px] text-amber-100">
                  {ui("漏财风险", "Leak risk", "누수 위험")} {percentLabel(wealthCode.risk)}
                </span>
              ) : null}
            </div>
          </div>

          {hasWealthCode ? (
            <div className="mt-3 grid gap-3 xl:grid-cols-[1.05fr_0.95fr]">
              {pathRankings.length ? (
                <div className="rounded-lg border border-cyan-300/20 bg-black/20 p-3">
                  <p className="text-[11px] text-zinc-500">{ui("路径规模排序", "Path ranking by scale", "경로 규모 순위")}</p>
                  <div className="mt-2 space-y-1.5">
                    {pathRankings.slice(0, 5).map((row, index) => {
                      const rowSize = localizedPathSize(row.size, ui);
                      const isPrimary = index === 0;
                      return (
                        <div
                          key={`path_ranking_${String(row.id || index)}`}
                          className={`rounded-lg border px-2 py-1.5 ${pathSizeToneClass(row.size)}`}
                        >
                          <div className="flex items-center justify-between gap-2 text-[11px]">
                            <p className="font-medium text-zinc-100">
                              {ui("排名", "Rank", "순위")} {String(row.rank || index + 1)} · {term(String(row.plain_name || row.id || ""))}
                            </p>
                            <span className={isPrimary ? "rounded-full border border-white/25 bg-white/15 px-1.5 py-0.5 text-zinc-100" : "text-zinc-300"}>
                              {rowSize}
                            </span>
                          </div>
                          <p className="mt-1 text-[11px] text-zinc-300">
                            {ui("规模分", "Scale score", "규모 점수")} {percentLabel(row.combined_score || row.score || 0)}
                            {row.risk ? ` · ${ui("风险", "Risk", "위험")} ${percentLabel(row.risk)}` : null}
                            {row.evidence_count ? ` · ${ui("证据", "Evidence", "근거")} ${String(row.evidence_count)}` : null}
                          </p>
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : null}
              {mechanismChains.length ? (
                <div className="rounded-lg border border-emerald-300/20 bg-black/20 p-3">
                  <p className="text-[11px] text-zinc-500">{ui("核心机制链", "Core mechanism chain", "핵심 메커니즘 체인")}</p>
                  <p className="mt-1 text-sm font-semibold leading-6 text-zinc-100">
                    {term(String(primaryMechanismChain.plain_name || primaryMechanismChain.chain_name || ui("待生成机制链", "Awaiting mechanism chain", "메커니즘 준비 중")))}
                  </p>
                  <p className="mt-1 text-[11px] leading-5 text-zinc-300">
                    {term(String(primaryMechanismChain.plain_summary || ""))}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    <span className={`rounded-full border px-2 py-1 text-[10px] ${closureStateToneClass(primaryMechanismChain.closure_state)}`}>
                      {localizedClosureState(primaryMechanismChain.closure_state, ui)} · {percentLabel(primaryMechanismChain.activation_score || primaryMechanismChain.score)}
                    </span>
                    <span className="rounded-full border border-white/20 bg-white/10 px-2 py-1 text-[10px] text-zinc-200">
                      {ui("完整度", "Completeness", "완성도")} {percentLabel(primaryMechanismChain.completeness || 0)}
                    </span>
                    <span className="rounded-full border border-white/20 bg-white/10 px-2 py-1 text-[10px] text-zinc-200">
                      {ui("风险位点", "Risk tags", "위험표지")} {asStringList(primaryMechanismChain.risk_modes).length}
                    </span>
                  </div>
                  {asStringList(primaryMechanismChain.timing_triggers).length ? (
                    <div className="mt-2 border-t border-white/10 pt-2">
                      <p className="text-[11px] text-zinc-500">{ui("激活时机", "Timing triggers", "활성화 시점")}</p>
                      <div className="mt-1 flex flex-wrap gap-1.5">
                        {asStringList(primaryMechanismChain.timing_triggers).slice(0, 3).map((item) => (
                          <span key={`mechanism-timing-${item}`} className="rounded-full border border-white/20 bg-white/10 px-2 py-1 text-[10px] text-zinc-300">
                            {term(item)}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : null}
                  <div className="mt-2 space-y-1">
                    {asRecordList(primaryMechanismChain.steps).map((step, idx) => (
                      <p key={`mechanism_step_${String(idx)}_${String(step.path_id || "")}`} className="text-[11px] leading-5 text-zinc-400">
                        {ui(
                          `${idx + 1}. `,
                          `${idx + 1}. `,
                          `${idx + 1}. `,
                        )}
                        <span className={step.present ? "text-emerald-100" : "text-zinc-500"}>
                          {term(String(step.plain_name || step.path_id || ""))}
                        </span>
                      </p>
                    ))}
                  </div>
                  {asStringList(primaryMechanismChain.forbidden_terms).length ? (
                    <div className="mt-2 border-t border-white/10 pt-2">
                      <p className="text-[11px] text-zinc-500">
                        {ui("防偏差提醒", "Avoid bias", "편향 경고")}
                      </p>
                      <div className="mt-1 flex flex-wrap gap-1.5">
                        {asStringList(primaryMechanismChain.forbidden_terms).slice(0, 3).map((item) => (
                          <span
                            key={`mechanism-forbid-${item}`}
                            className="rounded-full border border-rose-300/25 bg-rose-500/10 px-2 py-1 text-[10px] text-rose-100"
                          >
                            {term(item)}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : null}
                </div>
              ) : null}
              <div className="rounded-lg border border-white/10 bg-black/20 p-3">
                <p className="text-[11px] text-zinc-500">{ui("钱从哪里来", "Where money comes from", "돈이 어디서 오는가")}</p>
                <p className="mt-1 text-sm font-semibold leading-6 text-zinc-100">
                  {term(String(wealthSource.plain_source || pathSummary.wealth_source || primaryPath.plain_summary || ui("需要继续观察收入来源。", "Income source needs more observation.", "수입원은 추가 관찰이 필요합니다.")))}
                </p>
                <div className="mt-2 grid gap-2 sm:grid-cols-2">
                  <div>
                    <p className="text-[11px] text-zinc-500">{ui("靠什么变现", "Monetization", "수익화 방식")}</p>
                    <p className="mt-1 text-[12px] leading-5 text-emerald-100">
                      {term(String(monetizationEngine.plain_driver || ui("混合变现链路", "Mixed monetization chain", "혼합 수익화 흐름")))}
                    </p>
                  </div>
                  <div>
                    <p className="text-[11px] text-zinc-500">{ui("靠什么接住", "How to hold it", "어떻게 받아낼까")}</p>
                    <p className="mt-1 text-[12px] leading-5 text-cyan-100">
                      {term(String(carrier.plain_type || ui("综合承接能力", "Overall carrying capacity", "종합 수용 능력")))}
                    </p>
                  </div>
                </div>
                {asStringList(carrier.requirements).length ? (
                  <div className="mt-3 space-y-1">
                    {asStringList(carrier.requirements).slice(0, 3).map((item) => (
                      <p key={`wealth_carrier_${item}`} className="text-[11px] leading-5 text-zinc-400">
                        {term(item)}
                      </p>
                    ))}
                  </div>
                ) : null}
              </div>

              <div className="rounded-lg border border-white/10 bg-black/20 p-3">
                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
                  <div>
                    <p className="text-[11px] text-zinc-500">{ui("财富沉淀", "Wealth storage", "재물 축적")}</p>
                    <p className="mt-1 text-[12px] leading-5 text-zinc-300">
                      {term(String(wealthVault.plain_summary || ui("先按收入路径和现金流承接判断。", "Read by income path and cash-flow capacity first.", "수입 경로와 현금흐름 수용력으로 봅니다.")))}
                    </p>
                  </div>
                  <div>
                    <p className="text-[11px] text-zinc-500">{ui("哪里容易漏钱", "Where money leaks", "돈이 새는 곳")}</p>
                    <div className="mt-1 space-y-1">
                      {leakagePoints.length ? leakagePoints.map((row) => (
                        <p key={`wealth_leak_${String(row.id || row.plain_name)}`} className="text-[11px] leading-5 text-amber-100/90">
                          {term(String(row.plain_name || ""))}
                        </p>
                      )) : (
                        <p className="text-[11px] leading-5 text-zinc-500">
                          {ui("未见突出的漏财点，仍要看合同、账期和合作边界。", "No standout leak point; still watch contracts, payment terms, and cooperation boundaries.", "뚜렷한 누수점은 약하지만 계약, 회수 주기, 협업 경계를 봐야 합니다.")}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
                {yearWatchlist.length ? (
                  <div className="mt-3 border-t border-white/10 pt-2">
                    <p className="text-[11px] text-zinc-500">{ui("路径触发年份", "Path-trigger years", "경로 촉발 연도")}</p>
                    <div className="mt-1 flex flex-wrap gap-1.5">
                      {yearWatchlist.map((row) => (
                        <span key={`wealth_code_year_${String(row.year || row.focus)}`} className="rounded-full border border-cyan-300/20 bg-cyan-400/10 px-2 py-1 text-[10px] text-cyan-100">
                          {String(row.year || "—")} {term(String(row.focus || row.plain_name || ""))}
                        </span>
                      ))}
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          ) : (
            <p className="mt-3 text-[12px] leading-5 text-zinc-500">
              {ui("可以先生成财富路径，再让财富解读围绕真实的收入路径、变现链路和漏财点来写。", "Build the wealth path first so the reading can focus on income path, monetization, and leakage points.", "먼저 재물 경로를 생성하면 해석이 수입 경로, 수익화, 누수 지점을 중심으로 작성됩니다.")}
            </p>
          )}
        </div>
      ) : null}

      {hasWealthCode && (claimSupportRows.length || claimNodes.length) ? (
        <div className="mt-4 border-t border-white/10 pt-4">
          <div className="flex items-center gap-2">
            <FileSearch className="h-4 w-4 text-cyan-200" />
            <p className="text-sm font-semibold text-zinc-50">
              {ui("审计支撑链路", "Audit support path", "감사 근거 경로")}
            </p>
          </div>
          {claimSupportRows.length ? (
            <div className="mt-2 space-y-2">
              {claimSupportRows.map((row) => (
                <div key={row.id} className="rounded-lg border border-white/10 bg-black/20 p-2 text-[11px] text-zinc-200">
                  <p className="font-medium text-cyan-100">{term(`证据：${row.from}`)}</p>
                  <p className="mt-1 text-zinc-300">
                    {ui("支持", "supports", "지원")} {term(row.to)} · {ui("权重", "weight", "가중치")} {percentLabel(row.weight)}
                  </p>
                  {row.rule ? <p className="mt-1 text-zinc-500">{ui("规则", "Rule", "규칙")}：{row.rule}</p> : null}
                </div>
              ))}
            </div>
          ) : (
            <div className="mt-2 space-y-2">
              {primaryClaims.length ? (
                primaryClaims.map((row, idx) => {
                  const claim = asLooseRecord(row);
                  return (
                    <div key={`fallback-claim-${idx}`} className="rounded-lg border border-white/10 bg-black/20 p-2 text-[11px]">
                      <p className="font-medium text-cyan-100">{term(String(claim.claim_text || claim.label || claim.claim_id || ""))}</p>
                      <p className="mt-1 text-zinc-400">
                        {ui("支持路径", "Supports path", "지원 경로")} {term(graphLabelOf(primaryPath, ui("主路径", "Primary path", "주 경로")))} · {ui("权重", "weight", "가중치")} {percentLabel(claim.weight)}
                      </p>
                    </div>
                  );
                })
              ) : (
                <p className="text-[11px] text-zinc-500">
                  {ui("待补充可审计证据链。", "No auditable support chain yet.", "감사 가능한 근거 체인이 아직 없습니다.")}
                </p>
              )}
            </div>
          )}
          <p className="mt-2 text-[10px] text-zinc-500">
            {ui("该面板仅展示可追溯证据，不展示原始八字。", "This panel only shows traceable evidence, not raw chart data.", "이 패널은 원본 사주 원문을 보여주지 않고 추적 가능한 증거만 표시합니다.")}
          </p>
        </div>
      ) : null}

      {hasProfile ? (
        <div className="mt-4 border-t border-white/10 pt-4">
          <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-cyan-300/20 bg-cyan-400/10 text-cyan-100">
                  <CalendarRange className="h-4 w-4" />
                </span>
                <div>
                  <p className="text-[10px] uppercase tracking-[0.2em] text-cyan-300">
                    {ui("十年/今年", "Decade / Year", "10년 / 올해")}
                  </p>
                  <h4 className="mt-0.5 text-sm font-semibold text-zinc-50">
                    {ui("财富关注时间", "Money Timing", "재물 시기")}
                  </h4>
                </div>
              </div>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {timelineCreatedAt ? (
                <span className="rounded-full border border-white/10 bg-white/[0.035] px-2 py-1 text-[10px] text-zinc-400">
                  {shortPreviewTime(timelineCreatedAt)}
                </span>
              ) : null}
              <span className="rounded-full border border-cyan-300/20 bg-cyan-400/10 px-2 py-1 text-[10px] text-cyan-100">
                {timelineReady ? ui("已生成", "Ready", "준비됨") : ui("待生成", "Pending", "대기")}
              </span>
              {luckWindow.stance ? (
                <span className="rounded-full border border-amber-300/20 bg-amber-400/10 px-2 py-1 text-[10px] text-amber-100">
                  {localizedTimelineStance(luckWindow.stance, ui)}
                </span>
              ) : null}
            </div>
          </div>

          {timelineReady ? (
            <div className="mt-3 space-y-3">
              <div className="grid gap-3 xl:grid-cols-[0.85fr_1.15fr]">
                <div className="rounded-lg border border-white/10 bg-black/20 p-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div>
                      <p className="text-[11px] text-zinc-500">{ui("当前十年阶段", "Current decade", "현재 10년 흐름")}</p>
                      <p className="mt-1 text-sm font-semibold text-zinc-100">
                        {String(luckWindow.luck_pillar || "—")}
                        <span className="ml-2 text-[11px] font-medium text-cyan-200">
                          {String(luckWindow.start_year || "—")}-{String(luckWindow.end_year || "—")}
                        </span>
                      </p>
                    </div>
                    <div className="text-right text-[11px] text-zinc-400">
                      <p>{ui("收入机会", "Income", "수입 기회")} {percentLabel(luckWindow.score)}</p>
                      <p>{ui("风险", "Risk", "위험")} {percentLabel(luckWindow.risk)}</p>
                    </div>
                  </div>
                  <p className="mt-2 line-clamp-3 text-[12px] leading-5 text-zinc-300">
                    {term(String(luckWindow.summary || ""))}
                  </p>
                  {asStringList(luckWindow.reasons).length ? (
                    <div className="mt-2 space-y-1">
                      {asStringList(luckWindow.reasons).slice(0, 2).map((item) => (
                        <p key={`luck_reason_${item}`} className="line-clamp-2 text-[11px] leading-5 text-zinc-500">
                          {term(item)}
                        </p>
                      ))}
                    </div>
                  ) : null}
                </div>

                <div className="rounded-lg border border-white/10 bg-black/20 p-3">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div>
                      <p className="text-[11px] text-zinc-500">{ui("今年重点", "This year", "올해 초점")}</p>
                      <p className="mt-1 text-sm font-semibold text-zinc-100">
                        {String(currentFlow.year || "—")} {String(currentFlow.flow_pillar || "—")}
                      </p>
                    </div>
                    <span className={`rounded-full border px-2 py-1 text-[10px] ${attentionToneClass(currentFlow.attention_level)}`}>
                      {localizedAttentionType(currentFlow.attention_type, ui)}
                    </span>
                  </div>
                  <div className="mt-2 grid grid-cols-[minmax(0,1fr)_56px] items-center gap-2">
                    <div className="h-1.5 overflow-hidden rounded-full bg-white/10">
                      <div className="h-full rounded-full bg-cyan-300" style={{ width: `${Math.max(6, Math.min(100, asNumberValue(currentFlow.score) * 100))}%` }} />
                    </div>
                    <span className="text-right text-[11px] text-cyan-100">{percentLabel(currentFlow.score)}</span>
                  </div>
                  <p className="mt-2 text-[12px] font-semibold text-zinc-100">
                    {term(String(currentFlow.focus || ui("稳态观察", "Steady watch", "안정 관찰")))}
                  </p>
                  {asStringList(currentFlow.reasons).slice(0, 2).map((item) => (
                    <p key={`current_flow_${item}`} className="mt-1 line-clamp-2 text-[11px] leading-5 text-zinc-500">
                      {term(item)}
                    </p>
                  ))}
                </div>
              </div>

                  {topAttentionYears.length ? (
                    <div>
                  <div className="flex items-center gap-2">
                    <TrendingUp className="h-4 w-4 text-amber-200" />
                    <p className="text-[12px] font-semibold text-amber-50">
                      {ui("未来十年重点年份", "Key years in this decade", "10년 주요 연도")}
                    </p>
                  </div>
                      <div className="mt-2 grid gap-2 sm:grid-cols-2 xl:grid-cols-4">
                        {topAttentionYears.map((row) => {
                          const key = `wealth_timeline_${String(row.year || "")}_${String(row.flow_pillar || "")}`;
                          const activated = asRecordList(row.activated_chains);
                          return (
                            <div key={key} className={`min-w-0 rounded-lg border p-3 ${attentionToneClass(row.attention_level)}`}>
                          <div className="flex items-start justify-between gap-2">
                            <div className="min-w-0">
                              <p className="text-sm font-semibold">
                                {String(row.year || "—")} {String(row.flow_pillar || "—")}
                              </p>
                              <p className="mt-0.5 truncate text-[11px] opacity-80">
                                {term(String(row.focus || ""))}
                              </p>
                            </div>
                            <span className="shrink-0 text-[11px] opacity-80">{percentLabel(row.score)}</span>
                          </div>
                          <div className="mt-2 flex flex-wrap gap-1">
                            {asStringList(row.tags).slice(0, 3).map((tag) => (
                              <span key={`${key}_${tag}`} className="rounded-full border border-current/20 bg-black/15 px-1.5 py-0.5 text-[10px]">
                                {term(tag)}
                              </span>
                            ))}
                          </div>
                          {activated.length ? (
                            <div className="mt-2 border-t border-white/15 pt-2">
                              <p className="text-[11px] text-zinc-500">{ui("激活机制链", "Activated chains", "활성화 메커니즘")}</p>
                              <div className="mt-1 space-y-1">
                                {activated.slice(0, 2).map((activatedChain) => (
                                  <p key={`${key}_${String(activatedChain.chain_id || "")}`} className="text-[11px] leading-5 text-zinc-300">
                                    <span className="font-medium text-zinc-100">{term(String(activatedChain.plain_name || activatedChain.chain_id || ""))}</span>
                                    <span className="ml-2">
                                      <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${closureStateToneClass(activatedChain.closure_state)}`}>
                                        {localizedClosureState(activatedChain.closure_state, ui)}
                                      </span>
                                      <span className="ml-2 text-zinc-400">{percentLabel(activatedChain.activation_score || 0)}</span>
                                    </span>
                                  </p>
                                ))}
                              </div>
                            </div>
                          ) : null}
                          {asStringList(row.reasons).slice(0, 1).map((item) => (
                            <p key={`${key}_${item}`} className="mt-2 line-clamp-2 text-[11px] leading-5 opacity-80">
                              {term(item)}
                            </p>
                          ))}
                        </div>
                      );
                    })}
                  </div>
                </div>
              ) : null}

              {decadeYears.length ? (
                <details className="group">
                  <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-[11px] text-zinc-400">
                    <span>{ui("逐年参考", "Year-by-year notes", "연도별 참고")}</span>
                    <ChevronDown className="h-3.5 w-3.5 transition group-open:rotate-180" />
                  </summary>
                  <div className="mt-2 grid gap-1.5 sm:grid-cols-2">
                    {decadeYears.map((row) => (
                      <div key={`decade_${String(row.year || "")}_${String(row.flow_pillar || "")}`} className="grid grid-cols-[72px_minmax(0,1fr)_52px] items-center gap-2 rounded-lg border border-white/10 bg-white/[0.025] px-2 py-1.5 text-[11px] text-zinc-300">
                        <span className="font-semibold text-zinc-100">{String(row.year || "—")} {String(row.flow_pillar || "—")}</span>
                        <span className="truncate">{term(String(row.focus || ""))}</span>
                        <span className="text-right text-cyan-100">{percentLabel(row.score)}</span>
                      </div>
                    ))}
                  </div>
                </details>
              ) : null}
            </div>
          ) : (
            <p className="mt-3 text-[12px] leading-5 text-zinc-500">
              {hasTimeline
                ? ui("时间窗材料不足，等待服务端快照补齐。", "Timeline material is incomplete.", "시간 창 자료가 부족합니다.")
                : ui("可以基于当前财富分析，生成未来十年的收入机会与风险参考。", "Build income-opportunity and risk notes for this decade.", "현재 재물 분석으로 10년 수입 기회와 위험 참고를 생성할 수 있습니다.")}
            </p>
          )}
        </div>
      ) : null}

      <div className="mt-4 flex flex-col gap-2 border-t border-white/10 pt-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap gap-1.5 text-[10px] text-zinc-500">
          {previewCreatedAt ? (
            <span className="rounded-full border border-white/10 bg-white/[0.035] px-2 py-1">
              {shortPreviewTime(previewCreatedAt)}
            </span>
          ) : null}
          {evidence.slice(0, 2).map((item) => (
            <span key={`wealth_evidence_${item}`} className="max-w-full truncate rounded-full border border-white/10 bg-white/[0.035] px-2 py-1 sm:max-w-[260px]">
              {term(item)}
            </span>
          ))}
        </div>
        <div className="grid grid-cols-1 gap-2 sm:flex sm:justify-end">
          <button
            type="button"
            disabled={!canCodeSubmit}
            onClick={() => void requestCodePreview()}
            className="inline-flex min-h-9 items-center justify-center gap-1.5 rounded-lg border border-emerald-300/30 bg-emerald-400/10 px-3 py-2 text-[12px] font-semibold text-emerald-50 transition hover:border-emerald-200/55 hover:bg-emerald-400/15 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <TrendingUp className="h-3.5 w-3.5" />
            {codePending ? ui("生成中", "Building", "생성 중") : ui("生成财富路径", "Wealth path", "재물 경로 생성")}
          </button>
          <button
            type="button"
            disabled={!canTimelineSubmit}
            onClick={() => void requestTimeline()}
            className="inline-flex min-h-9 items-center justify-center gap-1.5 rounded-lg border border-cyan-300/30 bg-cyan-400/10 px-3 py-2 text-[12px] font-semibold text-cyan-50 transition hover:border-cyan-200/55 hover:bg-cyan-400/15 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <CalendarRange className="h-3.5 w-3.5" />
            {timelinePending ? ui("生成中", "Building", "생성 중") : ui("生成十年参考", "Decade notes", "10년 참고 생성")}
          </button>
          <button
            type="button"
            disabled={!canSubmit}
            onClick={() => void requestPreview(false)}
            className="inline-flex min-h-9 items-center justify-center gap-1.5 rounded-lg border border-zinc-600/50 bg-zinc-900/70 px-3 py-2 text-[12px] font-semibold text-zinc-200 transition hover:border-emerald-300/45 hover:text-emerald-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <FileSearch className="h-3.5 w-3.5" />
            {pendingMode === "contract" ? ui("生成中", "Building", "생성 중") : ui("看提示词", "Prompt", "프롬프트")}
          </button>
          <button
            type="button"
            disabled={!canSubmit}
            onClick={() => void requestPreview(true)}
            className="inline-flex min-h-9 items-center justify-center gap-1.5 rounded-lg border border-amber-300/30 bg-amber-400/10 px-3 py-2 text-[12px] font-semibold text-amber-50 transition hover:border-amber-200/55 hover:bg-amber-400/15 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <Sparkles className="h-3.5 w-3.5" />
            {pendingMode === "llm" ? ui("生成中", "Writing", "작성 중") : ui("生成解读", "Write", "해석 생성")}
          </button>
        </div>
      </div>

      {!canRequest ? (
        <p className="mt-2 text-[11px] text-zinc-500">
          {ui("财富解读生成仅管理员可调用。", "Wealth reading generation requires admin access.", "재물 해석 생성은 관리자만 호출할 수 있습니다.")}
        </p>
      ) : null}
      {error ? (
        <p className="mt-2 rounded-lg border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-[11px] text-rose-100">
          {error}
        </p>
      ) : null}

      {promptText || Object.keys(promptContract).length ? (
        <details className="group mt-3 border-t border-white/10 pt-3">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-[11px] text-zinc-400">
            <span>{ui("后台材料", "Backstage material", "백스테이지 자료")}</span>
            <ChevronDown className="h-3.5 w-3.5 transition group-open:rotate-180" />
          </summary>
          <div className="mt-2 max-h-80 overflow-auto rounded-lg border border-white/10 bg-black/25 p-3">
            {Object.keys(promptContract).length ? (
              <pre className="whitespace-pre-wrap break-words text-[10px] leading-5 text-emerald-100/85">
                {JSON.stringify(promptContract, null, 2)}
              </pre>
            ) : null}
            {promptText ? (
              <pre className="mt-3 whitespace-pre-wrap break-words border-t border-white/10 pt-3 text-[10px] leading-5 text-zinc-300">
                {promptText}
              </pre>
            ) : null}
          </div>
        </details>
      ) : null}
    </section>
  );
}
