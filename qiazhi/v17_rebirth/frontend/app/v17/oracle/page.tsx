"use client";

import { type ReactNode, useCallback, useEffect, useState } from "react";
import {
  Activity,
  ArrowRight,
  BarChart3,
  BookMarked,
  BriefcaseBusiness,
  ChevronDown,
  ChevronUp,
  FileSearch,
  ListChecks,
  Network,
  ScrollText,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import { useRouter } from "next/navigation";

import { V17_AppShell } from "@/components/V17_AppShell";
import { V17_PageGuard } from "@/components/V17_PageGuard";
import { V17_AdminUsersPanel, type AdminAuthUser } from "@/components/V17_AdminUsersPanel";
import { V17_DecisionInbox } from "@/components/V17_DecisionInbox";
import { V17_GodRingExplainCard } from "@/components/V17_GodRingExplainCard";
import { V17_NatalInput } from "@/components/V17_NatalInput";
import { V17_PurpleVerdictCard } from "@/components/V17_PurpleVerdictCard";
import { V17_SixPillarsPanel } from "@/components/V17_SixPillarsPanel";
import { V17_SurfaceTabs } from "@/components/V17_SurfaceTabs";
import { V17_FeatureOutlet } from "@/components/V17_FeatureOutlet";
import { V17_TracePanel } from "@/components/V17_TracePanel";
import type { OracleSurface } from "@/lib/accessControl";
import { jsonPostInit, noStoreInit, requestJson } from "@/lib/apiClient";
import { ORACLE_FEATURE_MODULES, resolveFeatureTabs } from "@/lib/featureRegistry";
import { t } from "@/lib/i18n";
import { useOracleSession } from "@/hooks/useOracleSession";
import { useV17Runtime } from "@/hooks/useV17Runtime";
import { classicalPatternCatalog } from "@/types/classicalPatternCatalog";

type OracleSurfaceTab = OracleSurface;
type ContentSurfaceTab = Exclude<OracleSurfaceTab, "trace">;
type AuxiliarySectionKey = "ledger" | "structure" | "runtime" | "authority" | "patterns" | "collaboration";
type LocalizeText = (zh: string, en: string, ko: string) => string;
type TranslateText = (value: string) => string;
type TranslateList = (values: string[]) => string[];
type FourPillarsSummary = { year?: string; month?: string; day?: string; hour?: string };

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

function topicHubTone(tone: "primary" | "stable" | "watch" | "soft" | "risk" | "muted"): string {
  if (tone === "primary") return "border-cyan-500/25 bg-cyan-950/25 text-cyan-50";
  if (tone === "stable") return "border-emerald-500/25 bg-emerald-950/20 text-emerald-50";
  if (tone === "watch") return "border-amber-500/25 bg-amber-950/20 text-amber-50";
  if (tone === "soft") return "border-fuchsia-500/25 bg-fuchsia-950/20 text-fuchsia-50";
  if (tone === "risk") return "border-rose-500/25 bg-rose-950/20 text-rose-50";
  return "border-zinc-800 bg-zinc-950/60 text-zinc-300";
}

function topicHubBadgeTone(tone: "primary" | "stable" | "watch" | "soft" | "risk" | "muted"): string {
  if (tone === "primary") return "border-cyan-500/25 bg-cyan-950/30 text-cyan-100";
  if (tone === "stable") return "border-emerald-500/25 bg-emerald-950/30 text-emerald-100";
  if (tone === "watch") return "border-amber-500/25 bg-amber-950/30 text-amber-100";
  if (tone === "soft") return "border-fuchsia-500/25 bg-fuchsia-950/30 text-fuchsia-100";
  if (tone === "risk") return "border-rose-500/25 bg-rose-950/30 text-rose-100";
  return "border-zinc-700 bg-zinc-900/70 text-zinc-300";
}

function patternConfidenceTone(score: number): string {
  if (score >= 0.82) return "border-emerald-500/25 bg-emerald-950/35 text-emerald-100";
  if (score >= 0.64) return "border-cyan-500/25 bg-cyan-950/35 text-cyan-100";
  if (score >= 0.48) return "border-amber-500/25 bg-amber-950/35 text-amber-100";
  return "border-zinc-500/20 bg-zinc-900/70 text-zinc-300";
}

function normalizePatternScope(scope: unknown): string {
  const key = String(scope || "").trim();
  if (key === "natal") return "原局";
  if (key === "luck_background") return "大运背景";
  if (key === "luck_only") return "大运触发";
  if (key === "flow_trigger") return "流年引动";
  if (key === "flow_only") return "流年主导";
  if (key === "runtime_pair") return "运流联动";
  if (key === "mixed") return "混合来源";
  return key || "来源待定";
}

function patternFamilyByName(name: string): string {
  return classicalPatternCatalog.find((item) => item.name === name)?.family || "格局候选";
}

type LivePatternCandidate = {
  key: string;
  name: string;
  family: string;
  confidence: number;
  scope: string;
  source: string;
  target: string;
  projectionText: string;
  profileText: string;
  manifestation: string;
  scopeWeights: Array<{ label: string; ratio: number }>;
  gate: string;
  gateReason: string;
  breakRisks: string[];
  statusLabel: string;
};

type TopicHubItem = {
  key: string;
  title: string;
  subtitle: string;
  status: string;
  tone: "primary" | "stable" | "watch" | "soft" | "risk" | "muted";
  details: string[];
  badges: string[];
};

type MobileResultTab = "chart" | "gods" | "relations" | "risks";
type StemBranchMeta = { element: "木" | "火" | "土" | "金" | "水"; yinYang: "阳" | "阴" };

const MOBILE_STEM_META: Record<string, StemBranchMeta> = {
  甲: { element: "木", yinYang: "阳" },
  乙: { element: "木", yinYang: "阴" },
  丙: { element: "火", yinYang: "阳" },
  丁: { element: "火", yinYang: "阴" },
  戊: { element: "土", yinYang: "阳" },
  己: { element: "土", yinYang: "阴" },
  庚: { element: "金", yinYang: "阳" },
  辛: { element: "金", yinYang: "阴" },
  壬: { element: "水", yinYang: "阳" },
  癸: { element: "水", yinYang: "阴" },
};

const MOBILE_BRANCH_META: Record<string, StemBranchMeta> = {
  子: { element: "水", yinYang: "阳" },
  丑: { element: "土", yinYang: "阴" },
  寅: { element: "木", yinYang: "阳" },
  卯: { element: "木", yinYang: "阴" },
  辰: { element: "土", yinYang: "阳" },
  巳: { element: "火", yinYang: "阴" },
  午: { element: "火", yinYang: "阳" },
  未: { element: "土", yinYang: "阴" },
  申: { element: "金", yinYang: "阳" },
  酉: { element: "金", yinYang: "阴" },
  戌: { element: "土", yinYang: "阳" },
  亥: { element: "水", yinYang: "阴" },
};

function mobileStemBranchMeta(value: string): StemBranchMeta | undefined {
  return MOBILE_STEM_META[value] || MOBILE_BRANCH_META[value];
}

function mobileStemBranchTextTone(value: string): string {
  const meta = mobileStemBranchMeta(value);
  if (!meta) return "text-zinc-100";
  const tone: Record<StemBranchMeta["element"], Record<StemBranchMeta["yinYang"], string>> = {
    木: { 阳: "text-lime-300", 阴: "text-emerald-300" },
    火: { 阳: "text-orange-300", 阴: "text-rose-300" },
    土: { 阳: "text-amber-300", 阴: "text-yellow-200" },
    金: { 阳: "text-slate-100", 阴: "text-zinc-300" },
    水: { 阳: "text-sky-300", 阴: "text-cyan-200" },
  };
  return tone[meta.element][meta.yinYang];
}

function MobileStemBranchGlyph({ value, className = "" }: { value: string; className?: string }) {
  const text = value || "—";
  const meta = mobileStemBranchMeta(text);
  return (
    <span
      className={`inline-block font-semibold ${mobileStemBranchTextTone(text)} ${className}`}
      title={meta ? `${meta.yinYang}${meta.element}` : undefined}
    >
      {text}
    </span>
  );
}

function MobileColoredPillarText({
  value,
  className = "",
}: {
  value: ReturnType<typeof compactPillarText>;
  className?: string;
}) {
  if (value.text === "—") return <span className={className}>—</span>;
  return (
    <span className={`inline-flex items-center gap-1 ${className}`}>
      <MobileStemBranchGlyph value={value.stem} />
      <MobileStemBranchGlyph value={value.branch} />
    </span>
  );
}

function compactPillarText(value: unknown): { stem: string; branch: string; text: string } {
  const text = String(value || "").trim();
  const compact = text.replace(/\s+/g, "");
  return {
    stem: compact.slice(0, 1) || "—",
    branch: compact.slice(1, 2) || "—",
    text: compact || "—",
  };
}

function compactRelationTitle(row: Record<string, unknown>, fallback: string): string {
  return String(
    row.relation_type ||
      row.relation ||
      row.name ||
      row.energy_axis ||
      row.axis ||
      row.plugin_label ||
      row.plugin_id ||
      fallback,
  ).trim();
}

function V17MobileResultSummary({
  ui,
  term,
  termList,
  fourPillars,
  luckPillar,
  flowPillar,
  selectedYear,
  onYearChange,
  birthLine,
  judgement,
  patternLeader,
  useGods,
  tabooGods,
  tongguanGods,
  relationRows,
  riskRows,
}: {
  ui: LocalizeText;
  term: TranslateText;
  termList: TranslateList;
  fourPillars?: FourPillarsSummary;
  luckPillar?: unknown;
  flowPillar?: unknown;
  selectedYear: number;
  onYearChange: (year: number) => void;
  birthLine: string;
  judgement: string;
  patternLeader?: LivePatternCandidate;
  useGods: string[];
  tabooGods: string[];
  tongguanGods: string[];
  relationRows: Array<Record<string, unknown>>;
  riskRows: Array<Record<string, unknown>>;
}) {
  const [activeTab, setActiveTab] = useState<MobileResultTab>("chart");
  const pillars = [
    { key: "year", label: ui("年", "Year", "년"), value: compactPillarText(fourPillars?.year) },
    { key: "month", label: ui("月", "Month", "월"), value: compactPillarText(fourPillars?.month) },
    { key: "day", label: ui("日", "Day", "일"), value: compactPillarText(fourPillars?.day) },
    { key: "hour", label: ui("时", "Hour", "시"), value: compactPillarText(fourPillars?.hour) },
  ];
  const runtimePillars = [
    { key: "luck", label: ui("大运", "Luck", "대운"), value: compactPillarText(luckPillar) },
    { key: "flow", label: ui("流年", "Flow", "세운"), value: compactPillarText(flowPillar) },
  ];
  const mobileYearChoices = Array.from({ length: 101 }, (_, index) => selectedYear - 50 + index);
  const tabs: Array<{ id: MobileResultTab; label: string }> = [
    { id: "chart", label: ui("命盘", "Chart", "명반") },
    { id: "gods", label: ui("用神", "Gods", "용신") },
    { id: "relations", label: ui("关系", "Relations", "관계") },
    { id: "risks", label: ui("风险", "Risks", "위험") },
  ];
  const activeRiskRows = riskRows.slice(0, 4);
  const activeRelationRows = relationRows.slice(0, 4);

  return (
    <section className="space-y-3 sm:hidden">
      <div className="rounded-2xl border border-violet-400/25 bg-[radial-gradient(circle_at_top_right,rgba(124,58,237,0.22),transparent_42%),linear-gradient(180deg,rgba(24,24,27,0.96),rgba(8,13,21,0.96))] p-4">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-[11px] uppercase tracking-[0.2em] text-violet-200">
              {ui("命盘结果", "Chart Result", "명반 결과")}
            </p>
            <h2 className="mt-1 text-lg font-semibold text-zinc-50">
              {patternLeader ? term(patternLeader.name) : ui("核心结论生成中", "Reading forming", "핵심 판독 생성 중")}
            </h2>
          </div>
          <span className={`rounded-full border px-2 py-1 text-[10px] ${patternLeader ? patternStatusToneForRuntime(patternLeader.statusLabel) : "border-cyan-500/25 bg-cyan-950/30 text-cyan-100"}`}>
            {patternLeader ? term(patternLeader.statusLabel) : ui("观察中", "Observing", "관찰 중")}
          </span>
        </div>
        <p className="mt-3 text-[13px] leading-6 text-zinc-200">{judgement}</p>
        <div className="mt-3 flex flex-wrap gap-1.5">
          <span className="rounded-full border border-amber-300/25 bg-amber-500/10 px-2 py-1 text-[10px] text-amber-100">
            {birthLine}
          </span>
          {useGods.slice(0, 2).map((god) => (
            <span key={`mobile_use_${god}`} className="rounded-full border border-emerald-400/25 bg-emerald-500/10 px-2 py-1 text-[10px] text-emerald-100">
              {ui("用", "Use", "용")} {term(god)}
            </span>
          ))}
          {activeRiskRows.length ? (
            <span className="rounded-full border border-amber-400/25 bg-amber-500/10 px-2 py-1 text-[10px] text-amber-100">
              {ui("风险", "Risks", "위험")} {activeRiskRows.length}
            </span>
          ) : null}
        </div>
      </div>

      <div className="rounded-2xl border border-white/10 bg-white/[0.04] p-3">
        <div className="grid grid-cols-4 gap-2">
          {pillars.map((pillar) => (
            <div key={pillar.key} className="rounded-xl border border-white/10 bg-[#0B0F16] p-2 text-center">
              <p className="text-[10px] text-zinc-500">{pillar.label}</p>
              <div className="mt-1 grid grid-rows-2 overflow-hidden rounded-lg border border-white/10">
                <span className="bg-zinc-900 py-2 text-xl font-semibold">
                  <MobileStemBranchGlyph value={pillar.value.stem} />
                </span>
                <span className="bg-zinc-950 py-2 text-lg font-semibold">
                  <MobileStemBranchGlyph value={pillar.value.branch} />
                </span>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-2 grid grid-cols-2 gap-2">
          {runtimePillars.map((pillar) => (
            <div key={pillar.key} className="flex items-center justify-between rounded-xl border border-white/10 bg-[#0B0F16] px-3 py-2">
              <span className="text-[11px] text-zinc-500">{pillar.label}</span>
              <MobileColoredPillarText value={pillar.value} className="text-base" />
            </div>
          ))}
        </div>
        <label className="mt-2 flex items-center justify-between gap-3 rounded-xl border border-amber-400/20 bg-amber-500/10 px-3 py-2">
          <span className="text-[11px] text-amber-100/80">{ui("选择流年", "Flow year", "세운 선택")}</span>
          <select
            value={selectedYear}
            onChange={(event) => onYearChange(Number(event.target.value))}
            className="min-h-8 rounded-lg border border-amber-300/25 bg-[#0B0F16] px-2 text-sm font-semibold text-amber-100 outline-none transition focus:border-amber-300/70 focus:ring-1 focus:ring-amber-300/35"
            aria-label={ui("选择流年", "Select flow year", "세운 선택")}
          >
            {mobileYearChoices.map((year) => (
              <option key={year} value={year}>
                {year}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="rounded-2xl border border-white/10 bg-[#0B0F16] p-3">
        <div className="grid grid-cols-4 gap-1 rounded-xl bg-white/[0.04] p-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`rounded-lg px-2 py-2 text-[12px] font-medium transition ${
                activeTab === tab.id
                  ? "bg-amber-300 text-zinc-950 shadow-[0_0_18px_rgba(212,175,55,0.18)]"
                  : "text-zinc-400 hover:bg-white/[0.05] hover:text-zinc-100"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        <div className="mt-3">
          {activeTab === "chart" ? (
            <div className="grid gap-2">
              <div className="rounded-xl border border-white/10 bg-white/[0.035] p-3">
                <p className="text-[11px] text-zinc-500">{ui("主格局", "Primary pattern", "주격")}</p>
                <p className="mt-1 text-base font-semibold text-zinc-100">
                  {patternLeader ? term(patternLeader.name) : ui("未成显格", "No clear pattern", "명확한 격 없음")}
                </p>
                <p className="mt-1 text-[11px] leading-5 text-zinc-400">
                  {patternLeader ? `${term(patternLeader.scope)} · ${Math.round(patternLeader.confidence * 100)}%` : ui("等待更多结构信号聚合。", "Waiting for more structural signals.", "구조 신호 집계를 기다립니다.")}
                </p>
              </div>
            </div>
          ) : null}

          {activeTab === "gods" ? (
            <div className="grid gap-2">
              {[
                { key: "use", title: ui("用神", "Useful gods", "용신"), values: useGods, tone: "border-emerald-400/20 bg-emerald-500/10 text-emerald-100" },
                { key: "taboo", title: ui("忌神", "Taboo gods", "기신"), values: tabooGods, tone: "border-rose-400/20 bg-rose-500/10 text-rose-100" },
                { key: "bridge", title: ui("通关", "Bridge gods", "통관"), values: tongguanGods, tone: "border-cyan-400/20 bg-cyan-500/10 text-cyan-100" },
              ].map((group) => (
                <div key={group.key} className="rounded-xl border border-white/10 bg-white/[0.035] p-3">
                  <p className="text-[11px] text-zinc-500">{group.title}</p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {group.values.length ? termList(group.values).slice(0, 6).map((value) => (
                      <span key={`${group.key}_${value}`} className={`rounded-full border px-2 py-1 text-[11px] ${group.tone}`}>
                        {value}
                      </span>
                    )) : (
                      <span className="text-[12px] text-zinc-500">{ui("暂无显性信号", "No explicit signal", "명시 신호 없음")}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : null}

          {activeTab === "relations" ? (
            <div className="grid gap-2">
              {activeRelationRows.length ? activeRelationRows.map((row, index) => (
                <div key={`mobile_relation_${index}`} className="rounded-xl border border-white/10 bg-white/[0.035] p-3">
                  <div className="flex items-center justify-between gap-2">
                    <p className="text-[12px] font-semibold text-zinc-100">{term(compactRelationTitle(row, ui("关系链", "Relation", "관계")))}</p>
                    <span className="rounded-full border border-cyan-400/20 bg-cyan-500/10 px-2 py-0.5 text-[10px] text-cyan-100">
                      {ui("动态", "Dynamic", "동적")}
                    </span>
                  </div>
                  <p className="mt-1 text-[11px] leading-5 text-zinc-400">
                    {String(row.reason || row.summary || row.effect || row.explain || row.energy_axis || ui("等待关系证据展开。", "Waiting for relation evidence.", "관계 근거 대기 중입니다."))}
                  </p>
                </div>
              )) : (
                <div className="rounded-xl border border-white/10 bg-white/[0.035] p-3 text-[12px] text-zinc-500">
                  {ui("暂无显著关系扰动，当前结构以静态盘面为主。", "No major relation disturbance; the static chart remains primary.", "주요 관계 교란은 없고 정적 명식이 중심입니다.")}
                </div>
              )}
            </div>
          ) : null}

          {activeTab === "risks" ? (
            <div className="grid gap-2">
              {activeRiskRows.length ? activeRiskRows.map((row, index) => (
                <div key={`mobile_risk_${index}`} className="rounded-xl border border-amber-400/20 bg-amber-500/10 p-3">
                  <p className="text-[12px] font-semibold text-amber-100">{term(decisionPluginLabel(row) || ui("风险提示", "Risk signal", "위험 신호"))}</p>
                  <p className="mt-1 text-[11px] leading-5 text-amber-50/80">
                    {String(row.reason || row.summary || row.risk_reason || row.pattern_gate_reason || ui("系统建议继续观察该风险来源。", "The system suggests watching this source.", "시스템은 이 위험 출처를 계속 관찰하라고 제안합니다."))}
                  </p>
                </div>
              )) : (
                <div className="rounded-xl border border-emerald-400/20 bg-emerald-500/10 p-3 text-[12px] text-emerald-100">
                  {ui("暂无显著破格风险。", "No major break risk.", "뚜렷한 파격 위험이 없습니다.")}
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}

function V17SimpleOracleSummary({
  ui,
  term,
  termList,
  fourPillars,
  luckPillar,
  flowPillar,
  birthLine,
  judgement,
  patternLeader,
  useGods,
  tabooGods,
  tongguanGods,
}: {
  ui: LocalizeText;
  term: TranslateText;
  termList: TranslateList;
  fourPillars?: FourPillarsSummary;
  luckPillar?: unknown;
  flowPillar?: unknown;
  birthLine: string;
  judgement: string;
  patternLeader?: LivePatternCandidate;
  useGods: string[];
  tabooGods: string[];
  tongguanGods: string[];
}) {
  const pillars = [
    { key: "year", label: ui("年柱", "Year", "년주"), value: compactPillarText(fourPillars?.year) },
    { key: "month", label: ui("月柱", "Month", "월주"), value: compactPillarText(fourPillars?.month) },
    { key: "day", label: ui("日柱", "Day", "일주"), value: compactPillarText(fourPillars?.day) },
    { key: "hour", label: ui("时柱", "Hour", "시주"), value: compactPillarText(fourPillars?.hour) },
  ];
  const godGroups = [
    { key: "use", label: ui("宜", "Favorable", "유리"), values: useGods, tone: "border-emerald-400/20 bg-emerald-500/10 text-emerald-100" },
    { key: "taboo", label: ui("忌", "Watch", "주의"), values: tabooGods, tone: "border-rose-400/20 bg-rose-500/10 text-rose-100" },
    { key: "bridge", label: ui("通关", "Bridge", "통관"), values: tongguanGods, tone: "border-cyan-400/20 bg-cyan-500/10 text-cyan-100" },
  ];

  return (
    <section className="hidden rounded-2xl border border-amber-400/20 bg-[radial-gradient(circle_at_top_left,rgba(212,175,55,0.12),transparent_34%),linear-gradient(180deg,rgba(14,18,25,0.96),rgba(7,11,18,0.96))] p-4 sm:block">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-[0.24em] text-amber-300">
            {ui("简明断语", "Concise Reading", "간결 판독")}
          </p>
          <h2 className="mt-1 text-xl font-semibold text-zinc-50">
            {patternLeader ? term(patternLeader.name) : ui("命盘核心判断", "Chart judgement", "명반 핵심 판단")}
          </h2>
          <p className="mt-1 text-sm text-zinc-400">{birthLine}</p>
        </div>
        <span className="rounded-full border border-amber-300/25 bg-amber-400/10 px-3 py-1 text-xs text-amber-100">
          {ui("普通用户模式", "User Mode", "일반 사용자 모드")}
        </span>
      </div>

      <p className="mt-4 max-w-4xl text-base leading-8 text-zinc-100">{judgement}</p>

      <div className="mt-4 grid gap-3 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-xl border border-white/10 bg-black/25 p-3">
          <p className="text-xs text-zinc-500">{ui("四柱简表", "Four pillars", "사주 간표")}</p>
          <div className="mt-3 grid grid-cols-4 gap-2">
            {pillars.map((pillar) => (
              <div key={pillar.key} className="rounded-xl border border-white/10 bg-white/[0.035] p-3 text-center">
                <p className="text-[11px] text-zinc-500">{pillar.label}</p>
                <MobileColoredPillarText value={pillar.value} className="mt-2 justify-center text-2xl font-semibold" />
              </div>
            ))}
          </div>
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            {[
              { key: "luck", label: ui("大运", "Luck", "대운"), value: luckPillar },
              { key: "flow", label: ui("流年", "Flow", "세운"), value: flowPillar },
            ].map((pillar) => (
              <div key={pillar.key} className="flex items-center justify-between rounded-xl border border-white/10 bg-white/[0.035] px-3 py-2">
                <span className="text-xs text-zinc-500">{pillar.label}</span>
                <MobileColoredPillarText value={compactPillarText(pillar.value)} className="text-lg font-semibold" />
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-white/10 bg-black/25 p-3">
          <p className="text-xs text-zinc-500">{ui("行动提示", "Reading cues", "판독 단서")}</p>
          <div className="mt-3 grid gap-2">
            {godGroups.map((group) => (
              <div key={group.key} className="rounded-xl border border-white/10 bg-white/[0.035] p-3">
                <p className="text-[11px] text-zinc-500">{group.label}</p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {group.values.length ? termList(group.values).slice(0, 4).map((value) => (
                    <span key={`${group.key}_${value}`} className={`rounded-full border px-2 py-1 text-[11px] ${group.tone}`}>
                      {value}
                    </span>
                  )) : (
                    <span className="text-[12px] text-zinc-500">{ui("暂无显性信号", "No explicit signal", "명시 신호 없음")}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

function V17MobileAnalysisDeck({
  ui,
  counts,
  canManageUsers,
  onOpen,
}: {
  ui: LocalizeText;
  counts: {
    ledger: number;
    structure: number;
    runtime: number;
    authority: number;
    patterns: number;
    collaboration: number;
  };
  canManageUsers: boolean;
  onOpen: (section: AuxiliarySectionKey) => void;
}) {
  const cards: Array<{
    key: AuxiliarySectionKey;
    title: string;
    desc: string;
    badge: string;
    tone: string;
  }> = [
    {
      key: "ledger",
      title: ui("命理师账本", "Practitioner Ledger", "명리사 장부"),
      desc: ui("回看反馈、案例与基准候选沉淀。", "Review feedback, cases, and benchmark candidates.", "피드백, 사례, 기준 후보를 되돌아봅니다."),
      badge: `${counts.ledger}`,
      tone: "border-amber-300/25 bg-amber-400/10 text-amber-100",
    },
    {
      key: "structure",
      title: ui("结构总览", "Structure", "구조"),
      desc: ui("六柱、调候、关系链的核心证据。", "Core evidence from pillars, climate, and relations.", "육주, 조후, 관계 체인의 핵심 근거입니다."),
      badge: `${counts.structure}`,
      tone: "border-cyan-400/25 bg-cyan-500/10 text-cyan-100",
    },
    {
      key: "authority",
      title: ui("体用裁决", "Body-Use", "체용 판정"),
      desc: ui("用神、忌神、通关与权威来源。", "Useful, taboo, bridge gods, and authority source.", "용신, 기신, 통관과 권위 출처입니다."),
      badge: `${counts.authority}`,
      tone: "border-emerald-400/25 bg-emerald-500/10 text-emerald-100",
    },
    {
      key: "patterns",
      title: ui("格局候选", "Patterns", "격국 후보"),
      desc: ui("主格局、次格局、成局度与破格点。", "Primary, secondary patterns, formation, and break points.", "주격, 보조 격국, 성국도와 파격점입니다."),
      badge: `${counts.patterns}`,
      tone: "border-violet-400/25 bg-violet-500/10 text-violet-100",
    },
    {
      key: "runtime",
      title: ui("运行账本", "Runtime", "운행 장부"),
      desc: ui("大运、流年、十神变化与引擎状态。", "Luck, annual flow, deity shifts, and engine state.", "대운, 세운, 십신 변화와 엔진 상태입니다."),
      badge: `${counts.runtime}`,
      tone: "border-amber-400/25 bg-amber-500/10 text-amber-100",
    },
  ];
  if (canManageUsers) {
    cards.push({
      key: "collaboration",
      title: ui("协作权限", "Collaboration", "협업 권한"),
      desc: ui("经理账号的用户与权限维护入口。", "User and role management for manager accounts.", "매니저 계정의 사용자와 권한 관리입니다."),
      badge: `${counts.collaboration}`,
      tone: "border-zinc-500/25 bg-zinc-500/10 text-zinc-100",
    });
  }

  return (
    <section className="rounded-2xl border border-white/10 bg-[#0B0F16] p-3 sm:hidden">
      <div className="flex items-end justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-[0.2em] text-cyan-300">
            {ui("深度分析", "Deep Analysis", "심층 분석")}
          </p>
          <h2 className="mt-1 text-base font-semibold text-zinc-50">
            {ui("选择一个专题展开", "Pick a topic", "주제를 선택하세요")}
          </h2>
        </div>
        <span className="rounded-full border border-white/10 bg-white/[0.04] px-2 py-1 text-[10px] text-zinc-400">
          {cards.length}
        </span>
      </div>
      <div className="mt-3 grid gap-2">
        {cards.map((card) => (
          <button
            key={card.key}
            type="button"
            onClick={() => onOpen(card.key)}
            className={`group rounded-xl border p-3 text-left transition active:scale-[0.99] ${card.tone}`}
          >
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-[13px] font-semibold text-zinc-50">{card.title}</p>
                <p className="mt-1 text-[11px] leading-5 text-zinc-400">{card.desc}</p>
              </div>
              <span className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-white/10 bg-black/20 text-[11px] group-active:translate-x-0.5">
                {card.badge}
              </span>
            </div>
          </button>
        ))}
      </div>
    </section>
  );
}

function V17ToolboxDeck({
  ui,
  traceSignalCount,
  pendingDecisionCount,
  modelLabel,
  llmLifecyclePhase,
}: {
  ui: LocalizeText;
  traceSignalCount: number;
  pendingDecisionCount: number;
  modelLabel: string;
  llmLifecyclePhase: string;
}) {
  const cards = [
    {
      key: "runtime",
      icon: <Activity className="h-4 w-4" />,
      title: ui("运行监控", "Runtime Monitor", "런타임 모니터"),
      desc: ui("查看流式状态、心跳与模型链路。", "Inspect streaming state, heartbeat, and model link.", "스트리밍 상태, 하트비트, 모델 연결을 확인합니다."),
      stat: llmLifecyclePhase,
      tone: "border-cyan-400/25 bg-cyan-500/10 text-cyan-100",
    },
    {
      key: "audit",
      icon: <ShieldAlert className="h-4 w-4" />,
      title: ui("裁决审计", "Decision Audit", "판정 감사"),
      desc: ui("查看人工确认、自动裁决与争议来源。", "Review manual, automatic, and disputed decisions.", "수동, 자동, 쟁점 판정을 검토합니다."),
      stat: `${pendingDecisionCount}`,
      tone: "border-amber-400/25 bg-amber-500/10 text-amber-100",
    },
    {
      key: "network",
      icon: <Network className="h-4 w-4" />,
      title: ui("链路诊断", "Link Diagnostics", "링크 진단"),
      desc: ui("追踪后端、插件、LLM 与物理快照。", "Trace backend, plugins, LLM, and physics snapshots.", "백엔드, 플러그인, LLM, 물리 스냅샷을 추적합니다."),
      stat: `${traceSignalCount}`,
      tone: "border-violet-400/25 bg-violet-500/10 text-violet-100",
    },
  ];

  return (
    <section className="rounded-2xl border border-white/10 bg-[#0B0F16] p-3">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-[11px] uppercase tracking-[0.2em] text-amber-300">
            {ui("工具箱", "Toolbox", "도구함")}
          </p>
          <h2 className="mt-1 text-base font-semibold text-zinc-50">
            {ui("运行与审计工具", "Runtime and audit tools", "런타임 및 감사 도구")}
          </h2>
        </div>
        <span className="rounded-full border border-white/10 bg-white/[0.04] px-2 py-1 text-[10px] text-zinc-400">
          {modelLabel}
        </span>
      </div>
      <div className="mt-3 grid gap-2 md:grid-cols-3">
        {cards.map((card) => (
          <div key={card.key} className={`rounded-xl border p-3 ${card.tone}`}>
            <div className="flex items-start justify-between gap-3">
              <span className="rounded-lg border border-white/10 bg-black/20 p-2">{card.icon}</span>
              <span className="rounded-full border border-white/10 bg-black/20 px-2 py-1 text-[10px]">{card.stat}</span>
            </div>
            <p className="mt-3 text-sm font-semibold text-zinc-50">{card.title}</p>
            <p className="mt-1 text-[11px] leading-5 text-zinc-400">{card.desc}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function OracleStartDashboard({
  language,
  name,
  professionalMode,
}: {
  language: Parameters<typeof t>[0];
  name: string;
  professionalMode: boolean;
}) {
  const allCards = [
    {
      key: "chart",
      icon: <ScrollText className="h-5 w-5" />,
      title: t(language, "oracle.dashboard.card.chart.title"),
      desc: t(language, "oracle.dashboard.card.chart.desc"),
      cta: t(language, "oracle.dashboard.card.chart.cta"),
      tone: "border-violet-400/35 bg-violet-500/10 text-violet-100",
      orb: "from-violet-400/22 to-transparent",
    },
    {
      key: "analysis",
      icon: <BarChart3 className="h-5 w-5" />,
      title: t(language, "oracle.dashboard.card.analysis.title"),
      desc: t(language, "oracle.dashboard.card.analysis.desc"),
      cta: t(language, "oracle.dashboard.card.analysis.cta"),
      tone: "border-cyan-400/35 bg-cyan-500/10 text-cyan-100",
      orb: "from-cyan-400/24 to-transparent",
    },
    {
      key: "tools",
      icon: <BriefcaseBusiness className="h-5 w-5" />,
      title: t(language, "oracle.dashboard.card.tools.title"),
      desc: t(language, "oracle.dashboard.card.tools.desc"),
      cta: t(language, "oracle.dashboard.card.tools.cta"),
      tone: "border-amber-400/35 bg-amber-500/10 text-amber-100",
      orb: "from-amber-400/24 to-transparent",
    },
  ];
  const cards = professionalMode ? allCards : allCards.slice(0, 1);

  return (
    <section className="rounded-none border-y border-white/10 bg-[#0B0F16] px-4 py-5 sm:rounded-2xl sm:border sm:bg-white/[0.035] sm:p-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold text-zinc-50 sm:text-2xl">
            {t(language, "oracle.dashboard.welcome", { name })}
          </h2>
          <p className="mt-1 text-sm leading-6 text-zinc-400">{t(language, "oracle.dashboard.subtitle")}</p>
        </div>
      </div>
      <div className={`mt-4 grid gap-3 ${professionalMode ? "md:grid-cols-3" : "md:grid-cols-1"}`}>
        {cards.map((card) => (
          <a
            key={card.key}
            href="#v17-natal-input"
            className={`group relative overflow-hidden rounded-xl border p-4 transition-all duration-200 hover:scale-[1.01] active:scale-[0.98] ${card.tone}`}
          >
            <div className={`pointer-events-none absolute right-[-28px] top-[-28px] h-28 w-28 rounded-full bg-gradient-to-br ${card.orb}`} />
            <div className="relative flex items-start justify-between gap-3">
              <div className="rounded-xl border border-white/10 bg-black/20 p-2.5">{card.icon}</div>
              <span className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/10 bg-white/[0.06] transition group-hover:translate-x-0.5">
                <ArrowRight className="h-4 w-4" />
              </span>
            </div>
            <h3 className="relative mt-4 text-base font-semibold text-zinc-50">{card.title}</h3>
            <p className="relative mt-1 text-xs leading-5 text-zinc-400">{card.desc}</p>
            <p className="relative mt-4 text-xs font-semibold text-current">{card.cta}</p>
          </a>
        ))}
      </div>
    </section>
  );
}

function AuxiliarySection({
  id,
  title,
  subtitle,
  badge,
  open,
  onToggle,
  children,
}: {
  id?: string;
  title: string;
  subtitle: string;
  badge?: string;
  open: boolean;
  onToggle: () => void;
  children: ReactNode;
}) {
  return (
    <section id={id} className="scroll-mt-24 rounded-2xl border border-cyan-500/18 bg-[linear-gradient(180deg,rgba(9,9,11,0.9),rgba(16,24,39,0.72))]">
      <button
        type="button"
        onClick={onToggle}
        className="flex w-full items-start justify-between gap-3 px-4 py-3 text-left transition hover:bg-cyan-950/10"
      >
        <div>
          <p className="text-[10px] uppercase tracking-[0.22em] text-cyan-300">{title}</p>
          <p className="mt-1 text-[11px] leading-5 text-zinc-400">{subtitle}</p>
        </div>
        <div className="flex items-center gap-2 pt-0.5">
          {badge ? (
            <span className="rounded-full border border-cyan-500/20 bg-cyan-950/30 px-2 py-1 text-[10px] text-cyan-100">
              {badge}
            </span>
          ) : null}
          <span className="rounded-full border border-zinc-700 bg-zinc-950/70 p-1.5 text-zinc-300">
            {open ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </span>
        </div>
      </button>
      {open ? <div className="border-t border-zinc-800/80 px-3 pb-3 pt-3">{children}</div> : null}
    </section>
  );
}

function normalizeManifestation(value: unknown): string {
  const key = String(value || "").trim();
  if (key === "manifested") return "成格";
  if (key === "supported") return "候选成立";
  if (key === "latent") return "潜势待成";
  if (key === "contested") return "受扰待核";
  return "观察中";
}

function patternStatusToneForRuntime(status: string): string {
  if (status === "成格") return "border-emerald-500/25 bg-emerald-950/35 text-emerald-100";
  if (status === "候选成立") return "border-cyan-500/25 bg-cyan-950/35 text-cyan-100";
  if (status === "受扰待核") return "border-rose-500/25 bg-rose-950/35 text-rose-100";
  if (status === "潜势待成") return "border-amber-500/25 bg-amber-950/35 text-amber-100";
  return "border-zinc-500/20 bg-zinc-900/70 text-zinc-300";
}

function normalizeScopeWeights(value: unknown): Array<{ label: string; ratio: number }> {
  if (!value || typeof value !== "object") return [];
  return Object.entries(value as Record<string, unknown>)
    .map(([key, raw]) => ({ label: normalizePatternScope(key), ratio: Number(raw || 0) }))
    .filter((item) => Number.isFinite(item.ratio) && item.ratio > 0)
    .sort((a, b) => b.ratio - a.ratio)
    .slice(0, 4);
}

function normalizePluginKey(value: unknown): string {
  return String(value || "")
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "_");
}

function decisionPluginLabel(row: Record<string, unknown>): string {
  return String(row.plugin_label || row.plugin_name || row.label || row.source || row.plugin_id || "")
    .trim()
    .replace(/^classical\./, "");
}

function compactProjection(value: unknown): string {
  if (!Array.isArray(value)) return "";
  return value
    .map((item) => {
      if (!item || typeof item !== "object") return "";
      const entry = item as Record<string, unknown>;
      const label = String(entry.label || entry.name || entry.family || "").trim();
      const percent = Number(entry.percent ?? entry.ratio ?? 0);
      if (!label) return "";
      return `${label}${percent > 0 ? ` ${Math.round(percent)}%` : ""}`;
    })
    .filter(Boolean)
    .slice(0, 3)
    .join(" / ");
}

function deriveLivePatternCandidates(
  allRows: Array<Record<string, unknown>>,
  pluginClaims: Array<Record<string, unknown>>,
): LivePatternCandidate[] {
  const candidates = new Map<string, LivePatternCandidate>();
  let globalGate = "";
  let globalGateReason = "";
  let globalBreakRisks: string[] = [];
  const ingest = (row: Record<string, unknown>, source: string) => {
    const name = String(row.pattern_candidate || row.pattern_name || "").trim();
    if (!name) return;
    const confidenceRaw = row.pattern_confidence_percent ?? row.pattern_confidence ?? row.match_ratio ?? 0;
    let confidence = Number(confidenceRaw || 0);
    if (confidence > 1) confidence = confidence / 100;
    confidence = Number.isFinite(confidence) ? confidence : 0;
    const target = String(row.target_god || "").trim();
    const scope = String(row.pattern_scope_label || normalizePatternScope(row.pattern_scope)).trim();
    const projectionText = compactProjection(row.cluster_projection);
    const manifestation = normalizeManifestation(row.manifestation_state);
    const scopeWeights = normalizeScopeWeights(row.scope_weights);
    const profile = Array.isArray(row.pattern_profile) ? row.pattern_profile : [];
    const profileText = profile
      .slice(0, 3)
      .map((item) => {
        if (!item || typeof item !== "object") return "";
        const family = String((item as { family?: string }).family || "").trim();
        const percent = Number((item as { percent?: number }).percent || 0);
        if (!family) return "";
        return `${family}${percent > 0 ? ` ${Math.round(percent)}%` : ""}`;
      })
      .filter(Boolean)
      .join(" / ");
    const key = `${name}::${target || "na"}`;
    const current = candidates.get(key);
    const next: LivePatternCandidate = {
      key,
      name,
      family: patternFamilyByName(name),
      confidence,
      scope: scope || "来源待定",
      source,
      target: target || "未定目标",
      projectionText,
      profileText,
      manifestation,
      scopeWeights,
      gate: globalGate,
      gateReason: globalGateReason,
      breakRisks: globalBreakRisks,
      statusLabel: manifestation,
    };
    if (!current || next.confidence > current.confidence) {
      candidates.set(key, next);
      return;
    }
    if (current && !current.scopeWeights.length && scopeWeights.length) current.scopeWeights = scopeWeights;
    if (current && !current.profileText && profileText) current.profileText = profileText;
    if (current && !current.projectionText && projectionText) current.projectionText = projectionText;
    if (current && current.statusLabel === "观察中" && manifestation !== "观察中") current.statusLabel = manifestation;
  };

  for (const row of [...pluginClaims, ...allRows]) {
    const pluginId = String(row.plugin_id || row.source || "").trim();
    if (pluginId === "classical.pattern.formation_gate.v1") {
      globalGate = String(row.pattern_gate || "").trim();
      globalGateReason = String(row.pattern_gate_reason || "").trim();
    }
    if (pluginId === "classical.pattern.break_guard.v1") {
      globalBreakRisks = Array.isArray(row.pattern_break_risks)
        ? (row.pattern_break_risks as unknown[]).map((item) => String(item || "").trim()).filter(Boolean)
        : [];
    }
  }

  for (const row of pluginClaims) ingest(row, "claim");
  for (const row of allRows) ingest(row, "decision");

  return Array.from(candidates.values())
    .map((item) => {
      const statusLabel = item.breakRisks.length
        ? "受扰待核"
        : item.gate === "月令成格" || item.gate === "强轴成格" || item.gate === "双线成格"
          ? "成格"
          : item.manifestation;
      return { ...item, gate: globalGate, gateReason: globalGateReason, breakRisks: globalBreakRisks, statusLabel };
    })
    .sort((a, b) => b.confidence - a.confidence);
}

function evidenceKindLabel(kind: string, ui: LocalizeText): string {
  const key = kind.trim();
  if (key === "pattern") return ui("格局", "Pattern", "격국");
  if (key === "risk") return ui("风险", "Risk", "위험");
  if (key === "work") return ui("做功", "Work", "작용");
  if (key === "climate") return ui("调候", "Climate", "조후");
  if (key === "semantic") return ui("象法", "Semantic", "상법");
  return ui("诊断", "Diagnostic", "진단");
}

function evidenceKindTone(kind: string): string {
  if (kind === "pattern") return "border-violet-400/25 bg-violet-500/10 text-violet-100";
  if (kind === "risk") return "border-rose-400/25 bg-rose-500/10 text-rose-100";
  if (kind === "work") return "border-cyan-400/25 bg-cyan-500/10 text-cyan-100";
  if (kind === "climate") return "border-amber-400/25 bg-amber-500/10 text-amber-100";
  if (kind === "semantic") return "border-fuchsia-400/25 bg-fuchsia-500/10 text-fuchsia-100";
  return "border-zinc-700 bg-zinc-900/70 text-zinc-300";
}

function evidenceDetailLabel(key: string, ui: LocalizeText): string {
  const labels: Record<string, string> = {
    work_evidence: ui("做功路径", "Work path", "작용 경로"),
    static_basis: ui("静态依据", "Static basis", "정적 근거"),
    zaqi_evidence: ui("杂气证据", "Mixed-Qi evidence", "잡기 근거"),
    follow_evidence: ui("从格证据", "Follow evidence", "종격 근거"),
    self_party_evidence: ui("身党证据", "Self-party evidence", "신강 근거"),
    structure_evidence: ui("结构证据", "Structure evidence", "구조 근거"),
    blade_branch: ui("羊刃支", "Blade branch", "양인 지지"),
    blade_scopes: ui("羊刃位置", "Blade scopes", "양인 위치"),
    runtime_blade_scopes: ui("运限羊刃", "Runtime blade", "운한 양인"),
    pattern_scope_label: ui("来源层", "Source scope", "출처 층"),
    pattern_break_risks: ui("破格风险", "Break risks", "파격 위험"),
    pattern_gate: ui("成格门", "Formation gate", "성격 문"),
    pattern_gate_reason: ui("成格说明", "Gate reason", "성격 설명"),
    origin_type: ui("来源类型", "Origin", "출처"),
    manifestation_state: ui("显化态", "State", "현현 상태"),
  };
  return labels[key] || key.replace(/_/g, " ");
}

function percentText(value: unknown): string {
  const raw = asNumberValue(value);
  if (!raw) return "";
  return `${Math.round((raw <= 1 ? raw * 100 : raw))}%`;
}

function compactEvidenceValue(value: unknown, term: TranslateText): string {
  if (Array.isArray(value)) {
    return value
      .map((item) => compactEvidenceValue(item, term))
      .filter(Boolean)
      .slice(0, 4)
      .join(" / ");
  }
  if (value && typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>)
      .map(([key, raw]) => {
        const compact = compactEvidenceValue(raw, term);
        return compact ? `${key}: ${compact}` : "";
      })
      .filter(Boolean)
      .slice(0, 3);
    return entries.join(" · ");
  }
  const text = String(value ?? "").trim();
  return text ? term(text) : "";
}

type PractitionerFeedbackStatus = "confirm" | "reject" | "watch" | "review";

function feedbackStatusLabel(status: PractitionerFeedbackStatus | string, ui: LocalizeText): string {
  if (status === "confirm") return ui("确认", "Confirm", "확인");
  if (status === "reject") return ui("否定", "Reject", "부정");
  if (status === "watch") return ui("待观察", "Watch", "관찰");
  if (status === "review") return ui("需复核", "Review", "재검토");
  return ui("已反馈", "Sent", "피드백됨");
}

function feedbackStatusTone(status: PractitionerFeedbackStatus | string): string {
  if (status === "confirm") return "border-emerald-400/25 bg-emerald-500/10 text-emerald-100";
  if (status === "reject") return "border-rose-400/25 bg-rose-500/10 text-rose-100";
  if (status === "watch") return "border-amber-400/25 bg-amber-500/10 text-amber-100";
  if (status === "review") return "border-violet-400/25 bg-violet-500/10 text-violet-100";
  return "border-zinc-700 bg-zinc-900/70 text-zinc-300";
}

function practitionerCaseKeyPart(value: string): string {
  const normalized = value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9._-]+/g, "_")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "");
  return normalized || `case_${Date.now()}`;
}

function normalizedPillarText(value: unknown): string {
  const compact = compactPillarText(value).text;
  return compact === "—" ? "" : compact;
}

function V17EvidencePanel({
  ui,
  term,
  items,
  summary,
  sessionId,
  chartFingerprint,
  reviewerRole,
  birthTimeISO,
  gender,
  calendarType,
  lunarIsLeapMonth,
  fourPillars,
  luckPillar,
  flowPillar,
  selectedYear,
}: {
  ui: LocalizeText;
  term: TranslateText;
  items: Array<Record<string, unknown>>;
  summary: Record<string, unknown>;
  sessionId: string;
  chartFingerprint: string;
  reviewerRole: string;
  birthTimeISO: string;
  gender: string;
  calendarType: string;
  lunarIsLeapMonth: boolean;
  fourPillars?: FourPillarsSummary;
  luckPillar?: unknown;
  flowPillar?: unknown;
  selectedYear: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const [reasonByEvidence, setReasonByEvidence] = useState<Record<string, string>>({});
  const [pendingByEvidence, setPendingByEvidence] = useState<Record<string, boolean>>({});
  const [feedbackByEvidence, setFeedbackByEvidence] = useState<Record<string, Record<string, unknown>>>({});
  const [feedbackError, setFeedbackError] = useState("");
  const [caseByEvidence, setCaseByEvidence] = useState<Record<string, Record<string, unknown>>>({});
  const [casePendingByEvidence, setCasePendingByEvidence] = useState<Record<string, boolean>>({});
  const [caseMessageByEvidence, setCaseMessageByEvidence] = useState<Record<string, string>>({});
  const [caseError, setCaseError] = useState("");
  const visibleItems = (expanded ? items.slice(0, 12) : items.slice(0, 4));
  const total = asNumberValue(summary.total, items.length);
  const candidateCount = asNumberValue(summary.candidate_count);
  const riskCount = asNumberValue(summary.risk_count);
  const observeOnlyCount = asNumberValue(summary.observe_only_count);
  const professionalFeedback = reviewerRole === "practitioner" || reviewerRole === "manager" || reviewerRole === "admin";

  useEffect(() => {
    if (!sessionId || !items.length) return;
    let cancelled = false;
    const loadFeedback = async () => {
      const query = new URLSearchParams({ session_id: sessionId, limit: "200" });
      const { data: payload, ok } = await requestJson<Record<string, unknown>>(
        `/api/auth/practitioner-feedback?${query.toString()}`,
        noStoreInit(),
      );
      if (!ok || cancelled) return;
      const rows = Array.isArray(payload.feedback) ? payload.feedback as Array<Record<string, unknown>> : [];
      const next: Record<string, Record<string, unknown>> = {};
      for (const row of rows) {
        const key = String(row.evidence_id || "").trim();
        if (key && !next[key]) next[key] = row;
      }
      setFeedbackByEvidence(next);
    };
    void loadFeedback();
    return () => {
      cancelled = true;
    };
  }, [items.length, sessionId]);

  useEffect(() => {
    if (!items.length) return;
    let cancelled = false;
    const loadCases = async () => {
      const query = new URLSearchParams({ limit: "200" });
      if (chartFingerprint) query.set("chart_fingerprint", chartFingerprint);
      if (professionalFeedback) query.set("scope", "all");
      const { data: payload, ok } = await requestJson<Record<string, unknown>>(
        `/api/auth/practitioner-cases?${query.toString()}`,
        noStoreInit(),
      );
      if (!ok || cancelled) return;
      const rows = Array.isArray(payload.cases) ? payload.cases as Array<Record<string, unknown>> : [];
      const next: Record<string, Record<string, unknown>> = {};
      for (const row of rows) {
        for (const sourceId of asStringList(row.source_feedback_ids)) {
          if (sourceId && !next[sourceId]) next[sourceId] = row;
        }
      }
      setCaseByEvidence(next);
    };
    void loadCases();
    return () => {
      cancelled = true;
    };
  }, [chartFingerprint, items.length, professionalFeedback]);

  async function submitFeedback(item: Record<string, unknown>, status: PractitionerFeedbackStatus) {
    const evidenceId = String(item.evidence_id || item.claim_id || item.title || "").trim();
    if (!evidenceId) return;
    setFeedbackError("");
    setPendingByEvidence((current) => ({ ...current, [evidenceId]: true }));
    const { data: payload, ok, error } = await requestJson<Record<string, unknown>>(
      "/api/auth/practitioner-feedback",
      jsonPostInit({
        session_id: sessionId || "default",
        evidence_id: evidenceId,
        claim_id: String(item.claim_id || "").trim(),
        plugin_id: String(item.source_plugin || "").trim(),
        evidence_type: String(item.evidence_type || "").trim(),
        target_god: String(item.target_god || "").trim(),
        status,
        reason: String(reasonByEvidence[evidenceId] || "").trim(),
        confidence: asNumberValue(item.confidence),
        source_title: String(item.title || "").trim(),
        source_summary: String(item.summary || "").trim(),
        chart_fingerprint: chartFingerprint,
        payload: {
          detail_keys: asStringList(item.detail_keys),
          candidate_status: String(item.candidate_status || "").trim(),
          origin_type: String(item.origin_type || "").trim(),
          manifestation_state: String(item.manifestation_state || "").trim(),
        },
      }),
    );
    setPendingByEvidence((current) => ({ ...current, [evidenceId]: false }));
    if (!ok) {
      setFeedbackError(error || ui("反馈提交失败。", "Failed to submit feedback.", "피드백 제출에 실패했습니다."));
      return;
    }
    const row = asLooseRecord(payload.feedback);
    setFeedbackByEvidence((current) => ({ ...current, [evidenceId]: row }));
    setReasonByEvidence((current) => ({ ...current, [evidenceId]: "" }));
  }

  async function savePractitionerCase(item: Record<string, unknown>) {
    const evidenceId = String(item.evidence_id || item.claim_id || item.title || "").trim();
    if (!evidenceId) return;
    const kind = String(item.evidence_type || "diagnostic").trim();
    const source = String(item.source_plugin || "").trim().replace(/^classical\./, "");
    const title = String(item.title || item.summary || evidenceId).trim();
    const summaryText = String(item.summary || "").trim();
    const target = String(item.target_god || "").trim();
    const existingFeedback = feedbackByEvidence[evidenceId];
    const feedbackStatus = String(existingFeedback?.status || "").trim();
    const reviewerNote = String(reasonByEvidence[evidenceId] || existingFeedback?.reason || "").trim();
    const caseStatus = professionalFeedback ? "benchmark_candidate" : "submitted";
    const detailKeys = asStringList(item.detail_keys);
    const caseKey = `real.${practitionerCaseKeyPart(chartFingerprint || sessionId || "runtime")}.${practitionerCaseKeyPart(evidenceId)}`.slice(0, 120);
    const expectedPatterns = kind.includes("pattern") || String(item.candidate_status || "").trim() ? [title] : [];
    const expectedRisks = kind.includes("risk") ? [title] : [];
    const expectedUseGods = target ? [target] : [];
    const failureModes = Array.from(new Set([
      feedbackStatus === "reject" ? `reject_${kind || "evidence"}` : "",
      kind ? `evidence_${kind}` : "",
    ].filter(Boolean)));
    const sourceFeedbackIds = Array.from(new Set([
      evidenceId,
      String(existingFeedback?.id || "").trim(),
    ].filter(Boolean)));

    setCaseError("");
    setCaseMessageByEvidence((current) => ({ ...current, [evidenceId]: "" }));
    setCasePendingByEvidence((current) => ({ ...current, [evidenceId]: true }));
    const { data: payload, ok, error } = await requestJson<Record<string, unknown>>(
      "/api/auth/practitioner-cases",
      jsonPostInit({
        case_key: caseKey,
        case_title: title ? `案例：${title}` : ui("证据案例", "Evidence case", "근거 사례"),
        description: [
          `session=${sessionId || "default"}`,
          birthTimeISO ? `birth=${birthTimeISO}` : "",
          title ? `evidence=${title}` : "",
          summaryText ? `summary=${summaryText}` : "",
          reviewerNote ? `review_note=${reviewerNote}` : "",
        ].filter(Boolean).join("\n"),
        birth_time_iso: birthTimeISO,
        gender: gender === "female" ? "female" : "male",
        calendar_type: calendarType || "solar",
        lunar_is_leap_month: lunarIsLeapMonth,
        four_pillars: {
          year: String(fourPillars?.year || "").trim(),
          month: String(fourPillars?.month || "").trim(),
          day: String(fourPillars?.day || "").trim(),
          hour: String(fourPillars?.hour || "").trim(),
        },
        luck_pillar: normalizedPillarText(luckPillar),
        flow_pillar: normalizedPillarText(flowPillar),
        flow_year: selectedYear,
        tags: Array.from(new Set([kind, source, target].filter(Boolean))).slice(0, 8),
        expected_patterns: expectedPatterns,
        expected_use_gods: expectedUseGods,
        expected_risks: expectedRisks,
        boundary_flags: detailKeys.map((key) => evidenceDetailLabel(key, ui)).slice(0, 8),
        failure_modes: failureModes,
        expected_notes: reviewerNote || summaryText || title,
        source_feedback_ids: sourceFeedbackIds,
        chart_fingerprint: chartFingerprint,
        status: caseStatus,
        payload: {
          source: "oracle_evidence_panel",
          evidence: item,
          feedback: existingFeedback || {},
          trust_hint: professionalFeedback ? "practitioner" : "user",
        },
      }),
    );
    setCasePendingByEvidence((current) => ({ ...current, [evidenceId]: false }));
    if (!ok) {
      setCaseError(error || ui("案例收录失败。", "Failed to save case.", "사례 저장에 실패했습니다."));
      return;
    }
    const row = asLooseRecord(payload.case);
    setCaseByEvidence((current) => ({ ...current, [evidenceId]: row }));
    setCaseMessageByEvidence((current) => ({
      ...current,
      [evidenceId]: professionalFeedback
        ? ui("已收录为基准候选。", "Saved as a benchmark candidate.", "기준 후보로 저장했습니다.")
        : ui("已收录为真实案例。", "Saved as a real case.", "실제 사례로 저장했습니다."),
    }));
  }

  if (!items.length) {
    return (
      <section className="rounded-2xl border border-white/10 bg-white/[0.035] p-4">
        <div className="flex items-center gap-2 text-sm font-semibold text-zinc-100">
          <FileSearch className="h-4 w-4 text-cyan-200" />
          {ui("证据链", "Evidence Chain", "근거 체인")}
        </div>
        <p className="mt-2 text-[12px] leading-5 text-zinc-500">
          {ui(
            "等待插件输出可核验依据；出现格局、风险或做功链后会在这里汇总。",
            "Waiting for verifiable plugin evidence. Pattern, risk, and work-path evidence will appear here.",
            "검증 가능한 플러그인 근거를 기다리는 중입니다. 격국, 위험, 작용 경로 근거가 여기에 모입니다.",
          )}
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-2xl border border-cyan-500/15 bg-[linear-gradient(180deg,rgba(8,13,21,0.96),rgba(12,10,24,0.82))] p-4 shadow-[0_18px_70px_rgba(8,47,73,0.16)]">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-2">
            <span className="rounded-xl border border-cyan-400/20 bg-cyan-500/10 p-2 text-cyan-100">
              <FileSearch className="h-4 w-4" />
            </span>
            <div>
              <p className="text-sm font-semibold text-zinc-50">{ui("证据链", "Evidence Chain", "근거 체인")}</p>
              <p className="mt-0.5 text-[12px] text-zinc-500">
                {ui("把断语背后的插件、条件与置信度摊开。", "Expose the plugin, condition, and confidence behind each judgement.", "판단 뒤의 플러그인, 조건, 신뢰도를 펼칩니다.")}
              </p>
            </div>
          </div>
        </div>
        <div className="grid grid-cols-4 gap-1.5 text-center sm:flex sm:flex-wrap sm:justify-end">
          {[
            [ui("总数", "Total", "합계"), total],
            [ui("格局", "Pattern", "격국"), candidateCount],
            [ui("风险", "Risk", "위험"), riskCount],
            [ui("观察", "Watch", "관찰"), observeOnlyCount],
          ].map(([label, value]) => (
            <span key={String(label)} className="rounded-xl border border-white/10 bg-white/[0.04] px-2 py-1.5 text-[11px] text-zinc-300">
              <b className="mr-1 text-zinc-50">{String(value)}</b>
              {String(label)}
            </span>
          ))}
        </div>
      </div>

      <div className="mt-4 grid gap-2 sm:grid-cols-2">
        {visibleItems.map((item, index) => {
          const kind = String(item.evidence_type || "diagnostic").trim();
          const details = asLooseRecord(item.details);
          const detailKeys = asStringList(item.detail_keys);
          const confidence = percentText(item.confidence);
          const matchRatio = percentText(item.match_ratio);
          const target = String(item.target_god || "").trim();
          const source = String(item.source_plugin || "").trim().replace(/^classical\./, "");
          const title = String(item.title || item.summary || "").trim();
          const summaryText = String(item.summary || "").trim();
          const evidenceId = String(item.evidence_id || item.claim_id || title || "").trim();
          const pending = Boolean(pendingByEvidence[evidenceId]);
          const existingFeedback = feedbackByEvidence[evidenceId];
          const feedbackStatus = String(existingFeedback?.status || "").trim();
          const existingCase = caseByEvidence[evidenceId];
          const casePending = Boolean(casePendingByEvidence[evidenceId]);
          const caseMessage = caseMessageByEvidence[evidenceId] || "";
          return (
            <article key={`${String(item.evidence_id || item.claim_id || title)}_${index}`} className="rounded-xl border border-white/10 bg-[#0B0F16]/85 p-3">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-1.5">
                    <span className={`rounded-full border px-2 py-0.5 text-[10px] ${evidenceKindTone(kind)}`}>
                      {evidenceKindLabel(kind, ui)}
                    </span>
                    {target ? (
                      <span className="rounded-full border border-emerald-400/20 bg-emerald-500/10 px-2 py-0.5 text-[10px] text-emerald-100">
                        {term(target)}
                      </span>
                    ) : null}
                    {item.observe_only ? (
                      <span className="rounded-full border border-amber-400/20 bg-amber-500/10 px-2 py-0.5 text-[10px] text-amber-100">
                        {ui("观察", "Watch", "관찰")}
                      </span>
                    ) : null}
                  </div>
                  <h3 className="mt-2 text-sm font-semibold leading-5 text-zinc-50">{term(title)}</h3>
                </div>
                <ListChecks className="mt-0.5 h-4 w-4 shrink-0 text-cyan-200/80" />
              </div>
              <p className="mt-2 line-clamp-2 text-[12px] leading-5 text-zinc-400">{summaryText}</p>
              <div className="mt-2 flex flex-wrap gap-1.5 text-[10px] text-zinc-400">
                {confidence ? <span className="rounded-full border border-white/10 bg-white/[0.04] px-2 py-0.5">{ui("置信", "Conf", "신뢰")} {confidence}</span> : null}
                {matchRatio ? <span className="rounded-full border border-white/10 bg-white/[0.04] px-2 py-0.5">{ui("命中", "Match", "적중")} {matchRatio}</span> : null}
                {source ? <span className="rounded-full border border-white/10 bg-white/[0.04] px-2 py-0.5">{source}</span> : null}
              </div>
              {detailKeys.length ? (
                <details className="group mt-2 rounded-lg border border-white/10 bg-white/[0.03] px-2 py-2">
                  <summary className="flex cursor-pointer list-none items-center justify-between gap-2 text-[11px] text-zinc-300">
                    <span>{ui("查看依据", "View evidence", "근거 보기")}</span>
                    <ChevronDown className="h-3.5 w-3.5 text-zinc-500 transition group-open:rotate-180" />
                  </summary>
                  <div className="mt-2 space-y-1.5 border-t border-white/10 pt-2">
                    {Object.entries(details).slice(0, 5).map(([key, value]) => (
                      <div key={key} className="rounded-lg bg-black/20 px-2 py-1.5">
                        <p className="text-[10px] text-zinc-500">{evidenceDetailLabel(key, ui)}</p>
                        <p className="mt-0.5 text-[11px] leading-5 text-zinc-200">{compactEvidenceValue(value, term)}</p>
                      </div>
                    ))}
                  </div>
                </details>
              ) : null}
              <div className="mt-3 rounded-lg border border-white/10 bg-white/[0.025] p-2">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-[11px] font-semibold text-zinc-300">
                    {professionalFeedback
                      ? ui("命理师反馈", "Practitioner feedback", "명리사 피드백")
                      : ui("用户反馈", "User feedback", "사용자 피드백")}
                  </p>
                  {feedbackStatus ? (
                    <span className={`rounded-full border px-2 py-0.5 text-[10px] ${feedbackStatusTone(feedbackStatus)}`}>
                      {feedbackStatusLabel(feedbackStatus, ui)}
                    </span>
                  ) : null}
                </div>
                <textarea
                  value={reasonByEvidence[evidenceId] || ""}
                  onChange={(event) => setReasonByEvidence((current) => ({ ...current, [evidenceId]: event.target.value }))}
                  rows={2}
                  maxLength={1000}
                  placeholder={ui("可补充理由，例如：羊刃不在命局，需否定。", "Optional note, e.g. no blade in the chart, reject it.", "선택 메모: 명식에 양인이 없어 부정 등")}
                  className="mt-2 w-full resize-none rounded-lg border border-white/10 bg-black/25 px-2 py-1.5 text-[11px] leading-5 text-zinc-100 outline-none transition placeholder:text-zinc-600 focus:border-cyan-400/45"
                />
                <div className="mt-2 grid grid-cols-2 gap-1.5 sm:grid-cols-4">
                  {(["confirm", "reject", "watch", "review"] as PractitionerFeedbackStatus[]).map((status) => (
                    <button
                      key={`${evidenceId}_${status}`}
                      type="button"
                      disabled={pending}
                      onClick={() => void submitFeedback(item, status)}
                      className={`rounded-lg border px-2 py-1.5 text-[11px] font-semibold transition disabled:cursor-wait disabled:opacity-60 ${
                        feedbackStatus === status
                          ? feedbackStatusTone(status)
                          : "border-white/10 bg-white/[0.035] text-zinc-300 hover:border-cyan-400/30 hover:text-cyan-50"
                      }`}
                    >
                      {pending ? ui("提交中", "Sending", "전송 중") : feedbackStatusLabel(status, ui)}
                    </button>
                  ))}
                </div>
                <div className="mt-2 rounded-lg border border-amber-400/15 bg-amber-500/[0.06] p-2">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <div className="flex items-center gap-2">
                      <span className="rounded-lg border border-amber-300/20 bg-amber-500/10 p-1.5 text-amber-100">
                        <BookMarked className="h-3.5 w-3.5" />
                      </span>
                      <div>
                        <p className="text-[11px] font-semibold text-amber-50">
                          {professionalFeedback
                            ? ui("沉淀为命理师基准候选", "Save as practitioner benchmark candidate", "명리사 기준 후보로 저장")
                            : ui("收录为真实案例", "Save as real case", "실제 사례로 저장")}
                        </p>
                        <p className="mt-0.5 text-[10px] leading-4 text-zinc-500">
                          {ui("用于后续回归、审计与自动学习。", "Feeds later regression, audit, and learning.", "이후 회귀, 감사, 학습에 사용됩니다.")}
                        </p>
                      </div>
                    </div>
                    {existingCase ? (
                      <span className="inline-flex justify-center rounded-lg border border-emerald-400/20 bg-emerald-500/10 px-2 py-1 text-[11px] font-semibold text-emerald-100">
                        {ui("已收录", "Saved", "저장됨")}
                      </span>
                    ) : (
                      <button
                        type="button"
                        disabled={casePending || !birthTimeISO}
                        onClick={() => void savePractitionerCase(item)}
                        className="inline-flex items-center justify-center gap-1 rounded-lg border border-amber-300/25 bg-amber-500/10 px-2 py-1.5 text-[11px] font-semibold text-amber-50 transition hover:border-amber-200/40 hover:bg-amber-500/15 disabled:cursor-wait disabled:opacity-60"
                      >
                        <BookMarked className="h-3.5 w-3.5" />
                        {casePending
                          ? ui("收录中", "Saving", "저장 중")
                          : professionalFeedback
                            ? ui("收录候选", "Save candidate", "후보 저장")
                            : ui("收录案例", "Save case", "사례 저장")}
                      </button>
                    )}
                  </div>
                  {caseMessage ? <p className="mt-1.5 text-[10px] text-emerald-100">{caseMessage}</p> : null}
                </div>
              </div>
            </article>
          );
        })}
      </div>
      {feedbackError ? (
        <p className="mt-3 rounded-xl border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-[12px] text-rose-100">
          {feedbackError}
        </p>
      ) : null}
      {caseError ? (
        <p className="mt-3 rounded-xl border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-[12px] text-rose-100">
          {caseError}
        </p>
      ) : null}
      {items.length > visibleItems.length ? (
        <button
          type="button"
          onClick={() => setExpanded((current) => !current)}
          className="mt-3 inline-flex w-full items-center justify-center rounded-xl border border-white/10 bg-white/[0.04] px-3 py-2 text-[12px] font-semibold text-zinc-200 transition hover:border-cyan-400/30 hover:text-cyan-50 sm:w-auto"
        >
          {expanded
            ? ui("收起证据链", "Collapse evidence", "근거 접기")
            : ui(`展开更多证据（${items.length - visibleItems.length}）`, `Show more evidence (${items.length - visibleItems.length})`, `근거 더 보기 (${items.length - visibleItems.length})`)}
        </button>
      ) : null}
    </section>
  );
}

function caseStatusLabel(status: string, ui: LocalizeText): string {
  if (status === "benchmark_candidate") return ui("基准候选", "Benchmark", "기준 후보");
  if (status === "accepted") return ui("已采纳", "Accepted", "채택");
  if (status === "rejected") return ui("已驳回", "Rejected", "반려");
  if (status === "submitted") return ui("已提交", "Submitted", "제출됨");
  if (status === "draft") return ui("草稿", "Draft", "초안");
  return status || ui("未知", "Unknown", "알 수 없음");
}

function caseStatusTone(status: string): string {
  if (status === "benchmark_candidate") return "border-amber-300/25 bg-amber-400/10 text-amber-100";
  if (status === "accepted") return "border-emerald-400/25 bg-emerald-500/10 text-emerald-100";
  if (status === "rejected") return "border-rose-400/25 bg-rose-500/10 text-rose-100";
  if (status === "submitted") return "border-cyan-400/25 bg-cyan-500/10 text-cyan-100";
  return "border-zinc-700 bg-zinc-900/70 text-zinc-300";
}

function shortLedgerTime(value: unknown): string {
  const raw = String(value || "").trim();
  if (!raw) return "—";
  const date = new Date(raw);
  if (Number.isNaN(date.getTime())) return raw.slice(0, 16);
  return date.toLocaleString(undefined, {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function countStatus(rows: Array<Record<string, unknown>>, status: string): number {
  return rows.filter((row) => String(row.status || "").trim() === status).length;
}

function learningPriorityLabel(priority: string, ui: LocalizeText): string {
  if (priority === "high") return ui("高优先", "High", "높음");
  if (priority === "medium") return ui("中优先", "Medium", "중간");
  return ui("低优先", "Low", "낮음");
}

function learningPriorityTone(priority: string): string {
  if (priority === "high") return "border-rose-400/25 bg-rose-500/10 text-rose-100";
  if (priority === "medium") return "border-amber-400/25 bg-amber-500/10 text-amber-100";
  return "border-cyan-400/25 bg-cyan-500/10 text-cyan-100";
}

function learningActionLabel(action: string, ui: LocalizeText): string {
  if (action === "review_classical_pattern_gate") return ui("复核格局门槛", "Review pattern gate", "격국 조건 검토");
  if (action === "review_relation_gate_and_runtime_origin") return ui("复核运流来源", "Review relation origin", "관계 출처 검토");
  if (action === "review_authority_weighting") return ui("复核体用权重", "Review authority weights", "권위 가중치 검토");
  if (action === "review_static_ten_gods_calibration") return ui("复核十神校准", "Review ten-god calibration", "십성 보정 검토");
  if (action === "review_prompt_contract") return ui("复核断语协议", "Review prompt contract", "단어 프로토콜 검토");
  if (action === "expand_benchmark_coverage") return ui("扩充基准样本", "Expand benchmarks", "기준 샘플 확장");
  return ui("人工协议复核", "Manual protocol review", "수동 프로토콜 검토");
}

function V17PractitionerLedgerPanel({
  ui,
  reviewerRole,
}: {
  ui: LocalizeText;
  reviewerRole: string;
}) {
  const [feedbackRows, setFeedbackRows] = useState<Array<Record<string, unknown>>>([]);
  const [caseRows, setCaseRows] = useState<Array<Record<string, unknown>>>([]);
  const [learningRows, setLearningRows] = useState<Array<Record<string, unknown>>>([]);
  const [learningSummary, setLearningSummary] = useState<Record<string, unknown>>({});
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const canViewAll = reviewerRole === "manager" || reviewerRole === "admin";

  const loadLedger = useCallback(async () => {
    setLoading(true);
    setMessage("");
    const feedbackQuery = new URLSearchParams({ limit: "80" });
    const caseQuery = new URLSearchParams({ limit: "80" });
    const learningQuery = new URLSearchParams({ limit: "120" });
    if (canViewAll) {
      feedbackQuery.set("scope", "all");
      caseQuery.set("scope", "all");
      learningQuery.set("scope", "all");
    }
    try {
      const [feedbackResp, caseResp, learningResp] = await Promise.all([
        requestJson<Record<string, unknown>>(`/api/auth/practitioner-feedback?${feedbackQuery.toString()}`, noStoreInit()),
        requestJson<Record<string, unknown>>(`/api/auth/practitioner-cases?${caseQuery.toString()}`, noStoreInit()),
        requestJson<Record<string, unknown>>(`/api/auth/practitioner-learning-candidates?${learningQuery.toString()}`, noStoreInit()),
      ]);
      if (!feedbackResp.ok) {
        throw new Error(String(feedbackResp.data.detail || ui("反馈账本加载失败。", "Failed to load feedback ledger.", "피드백 장부 로드 실패")));
      }
      if (!caseResp.ok) {
        throw new Error(String(caseResp.data.detail || ui("案例账本加载失败。", "Failed to load case ledger.", "사례 장부 로드 실패")));
      }
      if (!learningResp.ok) {
        throw new Error(String(learningResp.data.detail || ui("学习候选加载失败。", "Failed to load learning candidates.", "학습 후보 로드 실패")));
      }
      setFeedbackRows(Array.isArray(feedbackResp.data.feedback) ? feedbackResp.data.feedback as Array<Record<string, unknown>> : []);
      setCaseRows(Array.isArray(caseResp.data.cases) ? caseResp.data.cases as Array<Record<string, unknown>> : []);
      setLearningRows(Array.isArray(learningResp.data.candidates) ? learningResp.data.candidates as Array<Record<string, unknown>> : []);
      setLearningSummary(
        learningResp.data.summary && typeof learningResp.data.summary === "object"
          ? learningResp.data.summary as Record<string, unknown>
          : {},
      );
    } catch (error) {
      setMessage(error instanceof Error ? error.message : ui("命理师账本加载失败。", "Failed to load practitioner ledger.", "명리사 장부 로드 실패"));
    } finally {
      setLoading(false);
    }
  }, [canViewAll, ui]);

  useEffect(() => {
    void loadLedger();
  }, [loadLedger]);

  const latestFeedback = feedbackRows.slice(0, 6);
  const latestCases = caseRows.slice(0, 6);
  const benchmarkCount = countStatus(caseRows, "benchmark_candidate");
  const confirmedCount = countStatus(feedbackRows, "confirm");
  const rejectedCount = countStatus(feedbackRows, "reject");
  const reviewCount = countStatus(feedbackRows, "review") + countStatus(feedbackRows, "watch");
  const learningCandidateCount = Number(learningSummary.candidate_count || learningRows.length || 0);
  const manualReviewCount = Number(learningSummary.manual_review_required_count || 0);
  const latestLearning = learningRows.slice(0, 4);

  return (
    <section className="space-y-3">
      <div className="rounded-2xl border border-amber-400/18 bg-[radial-gradient(circle_at_top_left,rgba(212,175,55,0.12),transparent_32%),linear-gradient(180deg,rgba(12,10,24,0.92),rgba(8,13,21,0.82))] p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-[10px] uppercase tracking-[0.24em] text-amber-300">
              {ui("命理师账本", "Practitioner Ledger", "명리사 장부")}
            </p>
            <h2 className="mt-1 text-sm font-semibold text-zinc-100">
              {canViewAll
                ? ui("全量反馈与案例运营", "All feedback and cases", "전체 피드백과 사례 운영")
                : ui("我的反馈与案例沉淀", "My feedback and cases", "내 피드백과 사례")}
            </h2>
            <p className="mt-1 max-w-2xl text-[11px] leading-5 text-zinc-400">
              {ui(
                "这里把证据反馈、真实案例和基准候选聚合成学习候选，进入人工审计而不是自动调参。",
                "Evidence feedback, real cases, and benchmarks become review-only learning candidates.",
                "근거 피드백, 실제 사례, 기준 후보를 검토 전용 학습 후보로 모읍니다.",
              )}
            </p>
          </div>
          <button
            type="button"
            onClick={() => void loadLedger()}
            disabled={loading}
            className="rounded-xl border border-amber-300/25 bg-amber-400/10 px-3 py-2 text-[11px] font-semibold text-amber-50 transition hover:border-amber-200/45 disabled:cursor-wait disabled:opacity-60"
          >
            {loading ? ui("刷新中", "Refreshing", "새로고침 중") : ui("刷新账本", "Refresh", "새로고침")}
          </button>
        </div>

        <div className="mt-4 grid gap-2 sm:grid-cols-5">
          {[
            { label: ui("反馈", "Feedback", "피드백"), value: feedbackRows.length, tone: "text-cyan-100" },
            { label: ui("确认", "Confirm", "확인"), value: confirmedCount, tone: "text-emerald-100" },
            { label: ui("否定", "Reject", "부정"), value: rejectedCount, tone: "text-rose-100" },
            { label: ui("基准候选", "Benchmark", "기준 후보"), value: benchmarkCount || reviewCount, tone: "text-amber-100" },
            { label: ui("学习候选", "Learning", "학습 후보"), value: learningCandidateCount, tone: "text-violet-100" },
          ].map((item) => (
            <div key={item.label} className="rounded-xl border border-white/10 bg-white/[0.035] p-3">
              <p className="text-[10px] text-zinc-500">{item.label}</p>
              <p className={`mt-1 text-xl font-semibold ${item.tone}`}>{item.value}</p>
            </div>
          ))}
        </div>

        {message ? (
          <p className="mt-3 rounded-xl border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-[12px] text-rose-100">
            {message}
          </p>
        ) : null}

        <div className="mt-3 rounded-2xl border border-violet-400/18 bg-violet-950/10 p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 className="text-sm font-semibold text-zinc-100">{ui("学习候选", "Learning Candidates", "학습 후보")}</h3>
              <p className="mt-1 text-[11px] text-zinc-500">
                {ui(
                  "只进入人工审计队列，不会自动改参数。",
                  "Review-only queue; no parameter changes are applied automatically.",
                  "검토 전용 대기열이며 매개변수를 자동 변경하지 않습니다.",
                )}
              </p>
            </div>
            <span className="rounded-full border border-violet-300/20 bg-violet-400/10 px-2 py-1 text-[10px] font-semibold text-violet-100">
              {ui("待审计", "Review", "검토")} {manualReviewCount}
            </span>
          </div>
          <div className="mt-3 grid gap-2 xl:grid-cols-2">
            {latestLearning.map((row) => {
              const priority = String(row.priority || "").trim();
              const family = String(row.parameter_family || "").trim();
              const action = String(row.recommended_action || "").trim();
              const score = Number(row.signal_score || 0);
              const hints = asStringList(row.review_hints).slice(0, 2);
              const plugins = asStringList(row.source_plugins).slice(0, 2);
              const cases = asStringList(row.source_cases).slice(0, 2);
              return (
                <article key={String(row.candidate_id || family)} className="rounded-xl border border-white/10 bg-black/25 p-3">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="truncate text-[12px] font-semibold text-zinc-100">{family || ui("未分类候选", "Unclassified candidate", "미분류 후보")}</p>
                      <p className="mt-1 text-[10px] text-zinc-500">{learningActionLabel(action, ui)} · {ui("分数", "score", "점수")} {score.toFixed(2)}</p>
                    </div>
                    <span className={`rounded-full border px-2 py-0.5 text-[10px] ${learningPriorityTone(priority)}`}>
                      {learningPriorityLabel(priority, ui)}
                    </span>
                  </div>
                  <p className="mt-2 line-clamp-2 text-[11px] leading-5 text-zinc-400">
                    {hints.join(" / ") || ui("等待更多命理师反馈形成审计说明。", "Waiting for more practitioner signals.", "더 많은 명리사 신호 대기 중")}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {[...plugins, ...cases].slice(0, 4).map((item, index) => (
                      <span key={`${item}_${index}`} className="rounded-full border border-white/10 bg-white/[0.04] px-2 py-0.5 text-[10px] text-zinc-400">
                        {item}
                      </span>
                    ))}
                  </div>
                </article>
              );
            })}
            {!latestLearning.length && !loading ? (
              <p className="rounded-xl border border-white/10 bg-white/[0.035] p-3 text-[12px] text-zinc-500">
                {ui("暂无学习候选。继续收集命理师反馈和基准案例。", "No learning candidates yet. Keep collecting practitioner feedback and benchmark cases.", "아직 학습 후보가 없습니다. 피드백과 기준 사례를 계속 수집하세요.")}
              </p>
            ) : null}
          </div>
        </div>
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <div className="rounded-2xl border border-cyan-500/15 bg-zinc-950/55 p-3">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold text-zinc-100">{ui("最近反馈", "Recent Feedback", "최근 피드백")}</h3>
            <span className="rounded-full border border-white/10 bg-white/[0.04] px-2 py-1 text-[10px] text-zinc-400">{feedbackRows.length}</span>
          </div>
          <div className="mt-3 grid gap-2">
            {latestFeedback.map((row) => {
              const status = String(row.status || "").trim();
              const title = String(row.source_title || row.evidence_id || row.claim_id || "").trim();
              const reviewer = String(row.reviewer_display_name || row.reviewer_username || row.reviewer_role || "").trim();
              return (
                <article key={`feedback_${String(row.id || title)}`} className="rounded-xl border border-white/10 bg-black/25 p-3">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="truncate text-[12px] font-semibold text-zinc-100">{title || ui("未命名反馈", "Untitled feedback", "이름 없는 피드백")}</p>
                      <p className="mt-1 text-[10px] text-zinc-500">
                        {shortLedgerTime(row.created_at)}{reviewer ? ` · ${reviewer}` : ""}
                      </p>
                    </div>
                    <span className={`rounded-full border px-2 py-0.5 text-[10px] ${feedbackStatusTone(status)}`}>
                      {feedbackStatusLabel(status, ui)}
                    </span>
                  </div>
                  <p className="mt-2 line-clamp-2 text-[11px] leading-5 text-zinc-400">
                    {String(row.reason || row.source_summary || row.plugin_id || ui("暂无补充理由。", "No note yet.", "추가 메모 없음"))}
                  </p>
                </article>
              );
            })}
            {!latestFeedback.length && !loading ? (
              <p className="rounded-xl border border-white/10 bg-white/[0.035] p-3 text-[12px] text-zinc-500">
                {ui("暂无反馈记录。", "No feedback yet.", "아직 피드백이 없습니다.")}
              </p>
            ) : null}
          </div>
        </div>

        <div className="rounded-2xl border border-amber-500/15 bg-zinc-950/55 p-3">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-sm font-semibold text-zinc-100">{ui("案例与基准候选", "Cases & Benchmarks", "사례와 기준 후보")}</h3>
            <span className="rounded-full border border-white/10 bg-white/[0.04] px-2 py-1 text-[10px] text-zinc-400">{caseRows.length}</span>
          </div>
          <div className="mt-3 grid gap-2">
            {latestCases.map((row) => {
              const status = String(row.status || "").trim();
              const title = String(row.case_title || row.case_key || "").trim();
              const owner = String(row.owner_display_name || row.owner_username || row.owner_role || "").trim();
              return (
                <article key={`case_${String(row.id || title)}`} className="rounded-xl border border-white/10 bg-black/25 p-3">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <div className="min-w-0">
                      <p className="truncate text-[12px] font-semibold text-zinc-100">{title || ui("未命名案例", "Untitled case", "이름 없는 사례")}</p>
                      <p className="mt-1 text-[10px] text-zinc-500">
                        {shortLedgerTime(row.updated_at || row.created_at)}{owner ? ` · ${owner}` : ""}
                      </p>
                    </div>
                    <span className={`rounded-full border px-2 py-0.5 text-[10px] ${caseStatusTone(status)}`}>
                      {caseStatusLabel(status, ui)}
                    </span>
                  </div>
                  <p className="mt-2 line-clamp-2 text-[11px] leading-5 text-zinc-400">
                    {String(row.expected_notes || row.description || row.chart_fingerprint || ui("暂无案例说明。", "No case note yet.", "사례 설명 없음"))}
                  </p>
                </article>
              );
            })}
            {!latestCases.length && !loading ? (
              <p className="rounded-xl border border-white/10 bg-white/[0.035] p-3 text-[12px] text-zinc-500">
                {ui("暂无案例记录。", "No cases yet.", "아직 사례가 없습니다.")}
              </p>
            ) : null}
          </div>
        </div>
      </div>
    </section>
  );
}

export default function OraclePage() {
  const router = useRouter();
  const { language, user, authLoading, logout, access, ui, term, termList } = useV17Runtime();
  const s = useOracleSession({ uiLanguage: language });
  const [focusedDecisionId, setFocusedDecisionId] = useState<string>("");
  const [activeSurfaceTab, setActiveSurfaceTab] = useState<OracleSurfaceTab>("core");
  const [lastContentSurfaceTab, setLastContentSurfaceTab] = useState<ContentSurfaceTab>("core");
  const [auxiliarySections, setAuxiliarySections] = useState<Record<AuxiliarySectionKey, boolean>>({
    ledger: false,
    structure: false,
    runtime: false,
    authority: false,
    patterns: false,
    collaboration: false,
  });
  const [authUsers, setAuthUsers] = useState<AdminAuthUser[]>([]);
  const [authUsersLoading, setAuthUsersLoading] = useState(false);
  const [authUsersMessage, setAuthUsersMessage] = useState("");

  const payload = (s.physicsSnapshot?.payload || {}) as Record<string, unknown>;
  const energyMeta = payload.energy_meta && typeof payload.energy_meta === "object"
    ? (payload.energy_meta as Record<string, unknown>)
    : {};
  const fourPillars =
    payload.four_pillars && typeof payload.four_pillars === "object"
      ? (payload.four_pillars as { year?: string; month?: string; day?: string; hour?: string })
      : undefined;
  const luckPillarSnap = payload.luck_pillar;
  const flowPillarSnap = payload.flow_pillar;
  const godRingInfo =
    payload.god_rings && typeof payload.god_rings === "object"
        ? (payload.god_rings as {
            god_of_use?: string[];
            god_of_taboo?: string[];
            tongguan_gods?: string[];
            source?: string;
            mode?: string;
            display_mode?: string;
          label_of_use?: string;
          label_of_taboo?: string;
          confidence?: number;
          core_path_count?: number;
          core_use_candidates?: Array<Record<string, unknown>>;
          core_taboo_candidates?: Array<Record<string, unknown>>;
          dual_role_candidates?: Array<Record<string, unknown>>;
          judgement_bias?: {
            use_bias?: Record<string, number>;
            taboo_bias?: Record<string, number>;
          };
          judgement_bias_entries?: Array<Record<string, unknown>>;
          judgement_bias_protocol?: Record<string, unknown>;
          blind_theme?: Record<string, unknown>;
          blind_bias?: Record<string, unknown>;
          blind_bias_protocol?: Record<string, unknown>;
          stage_bias?: Record<string, Record<string, number>>;
          stage_bias_protocol?: Record<string, unknown>;
          effect_scores?: Record<string, unknown>;
          core_graph_meta?: Record<string, unknown>;
          core_paths_preview?: Array<Record<string, unknown>>;
          positive_work?: Record<string, unknown>;
          negative_work?: Record<string, unknown>;
        })
      : undefined;
  const allRows = Array.isArray(payload.all_decisions) ? payload.all_decisions as Array<Record<string, unknown>> : [];
  const meta = payload.meta && typeof payload.meta === "object" ? payload.meta as Record<string, unknown> : {};
  const pluginsPayload = asLooseRecord(payload.plugins);
  const pluginRows = Array.isArray(pluginsPayload.rows) ? pluginsPayload.rows as Array<Record<string, unknown>> : [];
  const pluginClaims = Array.isArray(pluginsPayload.claims)
    ? pluginsPayload.claims as Array<Record<string, unknown>>
    : Array.isArray(meta.plugin_claims)
      ? meta.plugin_claims as Array<Record<string, unknown>>
      : [];
  const evidenceBundle = asLooseRecord(payload.evidence_bundle);
  const evidenceItems = Array.isArray(evidenceBundle.items) ? evidenceBundle.items as Array<Record<string, unknown>> : [];
  const evidenceSummary = asLooseRecord(evidenceBundle.summary);
  const relationFormationSummary = Array.isArray(energyMeta.relation_formation_summary)
    ? energyMeta.relation_formation_summary as Array<Record<string, unknown>>
    : [];
  const relationDynamicsSummary = Array.isArray(energyMeta.relation_dynamics_summary)
    ? energyMeta.relation_dynamics_summary as Array<Record<string, unknown>>
    : [];
  const climateField = energyMeta.climate_field && typeof energyMeta.climate_field === "object"
    ? energyMeta.climate_field as Record<string, unknown>
    : {};
  const climateModifierLayer = energyMeta.climate_modifier_layer && typeof energyMeta.climate_modifier_layer === "object"
    ? energyMeta.climate_modifier_layer as Record<string, unknown>
    : {};
  const climateTheme = meta.climate_theme && typeof meta.climate_theme === "object"
    ? meta.climate_theme as Record<string, unknown>
    : {};
  const xiangfaTheme = meta.xiangfa_theme && typeof meta.xiangfa_theme === "object"
    ? meta.xiangfa_theme as Record<string, unknown>
    : {};
  const livePatternCandidates = deriveLivePatternCandidates([...allRows, ...pluginRows], pluginClaims);
  const patternLeader = livePatternCandidates[0];
  const patternRunners = livePatternCandidates.slice(1, 4);
  const activePatternScopes = Array.from(new Set(livePatternCandidates.map((item) => item.scope).filter(Boolean))).slice(0, 5);
  const leaderBreakRisks = patternLeader?.breakRisks || [];
  const patternJudgement = (() => {
    if (!patternLeader) {
      return ui(
        "当前盘面尚未形成稳定格局候选，系统仍在等待更多结构证据完成聚合。",
        "No stable pattern candidate has formed yet. The system is still waiting for more structural evidence.",
        "현재 명식에는 안정적인 격국 후보가 아직 형성되지 않았고, 시스템은 구조 증거가 더 모이기를 기다리고 있습니다.",
      );
    }
    const parts: string[] = [];
    const leadScope = term(patternLeader.scope || "来源待定");
    const leadStatus = term(patternLeader.statusLabel || "观察中");
    parts.push(
      ui(
        `当前以「${patternLeader.name}」为主格局，处于${leadStatus}态势`,
        `The leading pattern is ${term(patternLeader.name)}, currently in ${leadStatus} state`,
        `현재 주격은 ${term(patternLeader.name)}이며 ${leadStatus} 상태입니다`,
      ),
    );
    parts.push(
      ui(
        `主要证据来自${leadScope}`,
        `main evidence comes from ${leadScope}`,
        `주요 근거는 ${leadScope}에서 나옵니다`,
      ),
    );
    if (patternLeader.target && patternLeader.target !== "未定目标") {
      parts.push(
        ui(
          `主落点聚焦在${term(patternLeader.target)}`,
          `the main focus is ${term(patternLeader.target)}`,
          `주요 초점은 ${term(patternLeader.target)}입니다`,
        ),
      );
    }
    if (patternRunners.length) {
      const topRunners = patternRunners
        .slice(0, 2)
        .map((item) => `${term(item.name)} ${Math.round(item.confidence * 100)}%`)
        .join(language === "zh" ? "、" : " / ");
      if (topRunners) {
        parts.push(
          ui(
            `次格局候选包括${topRunners}`,
            `secondary candidates include ${topRunners}`,
            `보조 격국 후보는 ${topRunners}입니다`,
          ),
        );
      }
    }
    if (patternLeader.breakRisks.length) {
      parts.push(
        ui(
          `但当前受${patternLeader.breakRisks.slice(0, 2).map(term).join("、")}牵制，仍需继续核验是否破格`,
          `but current break risks ${patternLeader.breakRisks.slice(0, 2).map(term).join(" / ")} still need verification`,
          `다만 현재 ${patternLeader.breakRisks.slice(0, 2).map(term).join(" / ")}의 견제를 받아 파격 여부를 계속 확인해야 합니다`,
        ),
      );
    } else if (patternLeader.gateReason) {
      parts.push(patternLeader.gateReason);
    }
    return `${parts.join(language === "zh" ? "，" : ". ")}${language === "zh" ? "。" : "."}`;
  })();
  const useGods = asStringList(godRingInfo?.god_of_use);
  const tabooGods = asStringList(godRingInfo?.god_of_taboo);
  const tongguanGods = asStringList(godRingInfo?.tongguan_gods);
  const coreUseCandidates = Array.isArray(godRingInfo?.core_use_candidates) ? godRingInfo.core_use_candidates : [];
  const coreTabooCandidates = Array.isArray(godRingInfo?.core_taboo_candidates) ? godRingInfo.core_taboo_candidates : [];
  const blindTheme = asLooseRecord(godRingInfo?.blind_theme);
  const blindBiasProtocol = asLooseRecord(godRingInfo?.blind_bias_protocol);
  const blindBias = asLooseRecord(godRingInfo?.blind_bias);
  const blindUseBias = Object.keys(asLooseRecord(blindBias.use_bias));
  const blindTabooBias = Object.keys(asLooseRecord(blindBias.taboo_bias));
  const climateFavored = asStringList(climateTheme.favored_gods);
  const climateStrained = asStringList(climateTheme.strained_gods);
  const xiangfaSemantic = asStringList(xiangfaTheme.semantic_mapping);
  const xiangfaEvidence = asStringList(xiangfaTheme.evidence);
  const xiangfaTopics = asStringList(xiangfaTheme.source_topics);
  const riskRows = [...pluginClaims, ...pluginRows, ...allRows].filter((row) => {
    const key = normalizePluginKey(row.plugin_id || row.source);
    const label = decisionPluginLabel(row);
    return key.includes("risk") || key.includes("break_guard") || label.includes("风险") || label.includes("破格");
  });
  const judgementBiasEntries = Array.isArray(godRingInfo?.judgement_bias_entries)
    ? godRingInfo.judgement_bias_entries as Array<Record<string, unknown>>
    : [];
  const runtimeTenGodCount =
    payload.ten_gods_runtime && typeof payload.ten_gods_runtime === "object"
      ? Object.keys(payload.ten_gods_runtime as Record<string, unknown>).length
      : 0;
  const runtimeLedgerSignalCount =
    runtimeTenGodCount +
    judgementBiasEntries.length +
    pluginClaims.length +
    relationDynamicsSummary.length;
  const relationStressCount = relationDynamicsSummary.filter((row) => asNumberValue(row.stability_delta_ratio) < -0.05).length;
  const structureSignalCount =
    relationFormationSummary.length + relationDynamicsSummary.length + Object.keys(climateField).length;
  const authoritySignalCount = useGods.length + tabooGods.length + tongguanGods.length;
  const collaborationUserCount = authUsers.length;
  const topicHubItems: TopicHubItem[] = [
    {
      key: "ziping",
      title: ui("子平主裁决", "ZiPing Authority", "자평 주판정"),
      subtitle: ui(
        "月令 / 旺衰 / 调候桥 / 格局桥 / 体用",
        "Month order / balance / climate bridge / pattern bridge / body-use",
        "월령 / 왕쇠 / 조후 브리지 / 격국 브리지 / 체용",
      ),
      status: godRingInfo ? ui("硬约束已接通", "Hard constraint online", "하드 제약 연결됨") : ui("等待权威源", "Waiting for authority source", "권위 출처 대기"),
      tone: godRingInfo ? "primary" : "muted",
      details: [
        useGods.length ? `${ui("用神", "Useful gods", "용신")} ${termList(useGods.slice(0, 3)).join(" / ")}` : ui("用神待定", "Useful gods pending", "용신 대기"),
        tabooGods.length ? `${ui("忌神", "Taboo gods", "기신")} ${termList(tabooGods.slice(0, 3)).join(" / ")}` : ui("忌神待定", "Taboo gods pending", "기신 대기"),
        `${ui("候选", "Candidates", "후보")} ${coreUseCandidates.length + coreTabooCandidates.length}`,
      ],
      badges: [
        `${ui("置信", "Confidence", "신뢰도")} ${Math.round(asNumberValue(godRingInfo?.confidence) * 100)}%`,
        String(godRingInfo?.mode || godRingInfo?.display_mode || "authority"),
      ].filter(Boolean),
    },
    {
      key: "pattern",
      title: ui("格局专题", "Pattern Topic", "격국 주제"),
      subtitle: ui("古典格局 / 成局度 / 破格风险", "Classical pattern / formation / break risk", "고전 격국 / 성국도 / 파격 위험"),
      status: patternLeader ? `${term(patternLeader.name)} ${Math.round(patternLeader.confidence * 100)}%` : ui("暂无主格局", "No primary pattern", "주격 없음"),
      tone: patternLeader ? (leaderBreakRisks.length ? "watch" : "stable") : "muted",
      details: [
        patternLeader ? `${ui("状态", "State", "상태")} ${term(patternLeader.statusLabel)}` : ui("等待候选聚合", "Waiting for candidates", "후보 집계 대기"),
        patternLeader ? `${ui("来源", "Source", "출처")} ${term(patternLeader.scope)}` : `${ui("候选", "Candidates", "후보")} ${livePatternCandidates.length}`,
        leaderBreakRisks.length ? `${ui("风险", "Risk", "위험")} ${leaderBreakRisks.slice(0, 2).map(term).join(" / ")}` : ui("破格风险未显著", "No major break risk", "큰 파격 위험 없음"),
      ],
      badges: activePatternScopes.length ? activePatternScopes.map(term) : ["pattern"],
    },
    {
      key: "climate",
      title: ui("调候专题", "Climate Topic", "조후 주제"),
      subtitle: ui("寒热轴 / 燥湿轴 / 效率稳定修正", "Thermal axis / moisture axis / efficiency-stability modifier", "한열축 / 조습축 / 효율·안정 보정"),
      status: term(String(climateTheme.state || climateField.state || "调候观察")),
      tone: Object.keys(climateField).length || Object.keys(climateTheme).length ? "stable" : "muted",
      details: [
        `${ui("寒热", "Thermal", "한열")} ${asNumberValue(climateTheme.thermal_index ?? climateField.thermal_index).toFixed(2)}`,
        `${ui("燥湿", "Moisture", "조습")} ${asNumberValue(climateTheme.moisture_index ?? climateField.moisture_index).toFixed(2)}`,
        `${ui("张力", "Tension", "장력")} ${asNumberValue(climateTheme.climate_tension ?? climateField.climate_tension).toFixed(2)}`,
      ],
      badges: [
        ...climateFavored.slice(0, 2).map((god) => `${ui("顺", "Favors", "순응")} ${term(god)}`),
        ...climateStrained.slice(0, 2).map((god) => `${ui("压", "Strains", "압박")} ${term(god)}`),
      ].slice(0, 4),
    },
    {
      key: "blind",
      title: ui("盲派专题", "Blind-School Topic", "맹파 주제"),
      subtitle: ui("体用主线 / 家里家外 / 运行换挡", "Body-use route / inner-outer roles / runtime shift", "체용 주선 / 안팎 역할 / 운행 전환"),
      status: term(String(blindTheme.primary_route || "盲派未显性")),
      tone: Object.keys(blindTheme).length ? "soft" : "muted",
      details: [
        `${ui("体态", "Body mode", "체태")} ${term(String(blindTheme.body_mode || "未定"))}`,
        `${ui("桥接", "Bridge", "브리지")} ${String(blindBiasProtocol.authority_bridge_mode || "bias_only")}`,
        `${ui("推用/推忌", "Use/Taboo bias", "용/기신 편향")} ${blindUseBias.length}/${blindTabooBias.length}`,
      ],
      badges: ["bias-only", ...termList(asStringList(blindTheme.runtime_switches).slice(0, 2))],
    },
    {
      key: "xiangfa",
      title: ui("象法专题", "Image-Semantic Topic", "상법 주제"),
      subtitle: ui("语义映射 / 证据串 / 事件框架", "Semantic mapping / evidence chain / event framing", "의미 매핑 / 근거 사슬 / 사건 프레임"),
      status: xiangfaSemantic.length || xiangfaEvidence.length ? ui("semantic-only 已接通", "semantic-only online", "semantic-only 연결됨") : ui("语义等待", "Semantic pending", "의미 대기"),
      tone: xiangfaSemantic.length || xiangfaEvidence.length ? "soft" : "muted",
      details: [
        `${ui("语义", "Semantic", "의미")} ${xiangfaSemantic.length}`,
        `${ui("证据", "Evidence", "근거")} ${xiangfaEvidence.length}`,
        `${ui("主题", "Topics", "주제")} ${xiangfaTopics.length}`,
      ],
      badges: xiangfaTopics.length ? termList(xiangfaTopics.slice(0, 4)) : [ui("不入 bias", "No bias entry", "bias 미진입")],
    },
    {
      key: "risk",
      title: ui("风险专题", "Risk Topic", "위험 주제"),
      subtitle: ui("风险放大 / 破格提示 / 判定偏置", "Risk amplification / break warning / judgement bias", "위험 증폭 / 파격 경고 / 판정 편향"),
      status: riskRows.length || relationStressCount ? ui("风险链已观测", "Risk chain observed", "위험 체인 관측") : ui("无显著风险", "No major risk", "주요 위험 없음"),
      tone: riskRows.length || relationStressCount ? "risk" : "muted",
      details: [
        `${ui("风险来源", "Risk sources", "위험 출처")} ${riskRows.length}`,
        `${ui("判定偏置", "Judgement bias", "판정 편향")} ${judgementBiasEntries.length}`,
        `${ui("稳定承压", "Stability strain", "안정 압박")} ${relationStressCount}`,
      ],
      badges: riskRows.length ? Array.from(new Set(riskRows.map(decisionPluginLabel).filter(Boolean))).slice(0, 3) : ["risk guard"],
    },
  ];
  const auxiliarySignalCount =
    livePatternCandidates.length +
    relationFormationSummary.length +
    relationDynamicsSummary.length +
    topicHubItems.filter((item) => item.tone !== "muted").length;
  const traceSignalCount =
    s.traceHits.length +
    s.traceFacts.length +
    s.heartbeatHistory.length +
    (s.fullTrace ? 1 : 0);
  const canAccessAuxiliarySurface = access.canAccessOracleSurface("auxiliary");
  const canAccessTraceSurface = access.canAccessOracleSurface("trace");
  const canManageUsers = access.canManageUsers;
  const canUseProfessionalOracle = access.canUseProfessionalOracle;
  const canReadEvidence = access.canReadEvidence;
  const surfaceTabs = resolveFeatureTabs(ORACLE_FEATURE_MODULES, {
    language,
    access,
    context: {
      decisionCount: s.pendingDecisionWorkCount,
      auxiliarySignalCount,
      traceSignalCount,
    },
  });
  const verdictButtonBusy =
    s.running && ["connecting", "awaiting_first_token", "streaming"].includes(s.llmLifecyclePhase);
  const verdictButtonLabel = verdictButtonBusy
    ? t(language, "oracle.action.show_verdict.loading")
    : t(language, "oracle.action.show_verdict");
  const toggleAuxiliarySection = (section: AuxiliarySectionKey) => {
    setAuxiliarySections((current) => ({
      ...current,
      [section]: !current[section],
    }));
  };
  const openAuxiliarySection = (section: AuxiliarySectionKey) => {
    setAuxiliarySections((current) => ({
      ...current,
      [section]: true,
    }));
    requestAnimationFrame(() => {
      document.getElementById(`aux-${section}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  };

  const loadAuthUsers = useCallback(async () => {
    if (!canManageUsers) return;
    setAuthUsersLoading(true);
    setAuthUsersMessage("");
    try {
      const { data: payload, ok } = await requestJson<Record<string, unknown>>("/api/auth/users", noStoreInit());
      if (!ok) {
        throw new Error(String(payload.detail || ui("用户列表加载失败。", "Failed to load users.", "사용자 목록을 불러오지 못했습니다.")));
      }
      const rows = Array.isArray(payload.users) ? payload.users : [];
      setAuthUsers(
        rows.map((row) => {
          const item = asLooseRecord(row);
          return {
            id: Number(item.id || 0),
            username: String(item.username || "").trim(),
            display_name: String(item.display_name || "").trim(),
            email: String(item.email || "").trim(),
            role: (String(item.role || "user").trim().toLowerCase() as AdminAuthUser["role"]),
            is_active: Boolean(item.is_active),
            created_at: String(item.created_at || "").trim(),
            last_login_at: String(item.last_login_at || "").trim(),
	            latest_ip_address: String(item.latest_ip_address || "").trim(),
	            latest_user_agent: String(item.latest_user_agent || "").trim(),
	            latest_seen_at: String(item.latest_seen_at || "").trim(),
	            role_request_id: Number(item.role_request_id || 0),
	            role_request_status: String(item.role_request_status || "").trim() as AdminAuthUser["role_request_status"],
	            role_request_role: String(item.role_request_role || "").trim() as AdminAuthUser["role_request_role"],
	            role_request_reason: String(item.role_request_reason || "").trim(),
	            role_request_created_at: String(item.role_request_created_at || "").trim(),
	            role_request_updated_at: String(item.role_request_updated_at || "").trim(),
	          };
	        }),
	      );
    } catch (error) {
      setAuthUsersMessage(error instanceof Error ? error.message : ui("用户列表加载失败。", "Failed to load users.", "사용자 목록을 불러오지 못했습니다."));
    } finally {
      setAuthUsersLoading(false);
    }
  }, [canManageUsers, ui]);

	  const updateAuthUserRole = useCallback(
    async (userId: number, role: AdminAuthUser["role"]) => {
      const { data: payload, ok } = await requestJson<Record<string, unknown>>(`/api/auth/users/${userId}/role`, jsonPostInit({ role }));
      if (!ok || payload.ok === false) {
        throw new Error(String(payload.detail || ui("角色更新失败。", "Failed to update role.", "역할을 업데이트하지 못했습니다.")));
      }
      setAuthUsersMessage(ui(`角色已更新为 ${role}。`, `Role updated to ${role}.`, `역할이 ${role}(으)로 변경되었습니다.`));
      await loadAuthUsers();
    },
    [loadAuthUsers, ui],
	  );

	  const decideAuthRoleRequest = useCallback(
	    async (requestId: number, decision: "approved" | "rejected") => {
	      const { data: payload, ok } = await requestJson<Record<string, unknown>>(
	        `/api/auth/role-requests/${requestId}/decision`,
	        jsonPostInit({ status: decision }),
	      );
	      if (!ok || payload.ok === false) {
	        throw new Error(String(payload.detail || ui("申请审核失败。", "Failed to review request.", "신청을 검토하지 못했습니다.")));
	      }
	      setAuthUsersMessage(
	        decision === "approved"
	          ? ui("命理师申请已批准。", "Practitioner request approved.", "명리사 신청이 승인되었습니다.")
	          : ui("命理师申请已驳回。", "Practitioner request rejected.", "명리사 신청이 거절되었습니다."),
	      );
	      await loadAuthUsers();
	    },
	    [loadAuthUsers, ui],
	  );

  const verdictTriggerPrompt = ui(
    "请基于当前已通过的决策，生成精炼八字断语，短句为主。",
    "Generate a concise BaZi verdict from the approved decisions. Use short judgement lines.",
    "현재 승인된 결정을 바탕으로 간결한 사주 단언을 짧은 판단 문장으로 생성하세요.",
  );

  const switchContentSurface = (tab: ContentSurfaceTab) => {
    if (tab === "auxiliary" && !canAccessAuxiliarySurface) return;
    setActiveSurfaceTab(tab);
    setLastContentSurfaceTab(tab);
    s.setTraceOpen(false);
  };

  const openTraceSurface = () => {
    if (!canAccessTraceSurface) return;
    setActiveSurfaceTab("trace");
    s.setTraceOpen(true);
  };

  const closeTraceSurface = () => {
    setActiveSurfaceTab(lastContentSurfaceTab);
    s.setTraceOpen(false);
  };

  useEffect(() => {
    if (authLoading || !user) return;
    if (activeSurfaceTab === "trace" && !canAccessTraceSurface) {
      const fallbackTab: ContentSurfaceTab = canAccessAuxiliarySurface ? "auxiliary" : "core";
      setActiveSurfaceTab(fallbackTab);
      setLastContentSurfaceTab(fallbackTab);
      s.setTraceOpen(false);
      return;
    }
    if (activeSurfaceTab === "auxiliary" && !canAccessAuxiliarySurface) {
      setActiveSurfaceTab("core");
      setLastContentSurfaceTab("core");
      s.setTraceOpen(false);
    }
  }, [activeSurfaceTab, authLoading, canAccessAuxiliarySurface, canAccessTraceSurface, s, user]);

  useEffect(() => {
    if (!authLoading && user && canManageUsers) {
      void loadAuthUsers();
    }
  }, [authLoading, canManageUsers, loadAuthUsers, user]);

  async function handleLogout() {
    await logout();
    router.replace("/login");
    router.refresh();
  }

  return (
    <V17_PageGuard
      language={language}
      user={user}
      loading={authLoading}
      onLogout={() => void handleLogout()}
    >
      <V17_AppShell
        language={language}
        user={user}
        loading={authLoading}
        running={s.running}
        onRetry={s.resetRun}
        onLogout={() => void handleLogout()}
      >
        {!s.running ? (
          <OracleStartDashboard
            language={language}
            name={user?.display_name || user?.username || "Admin"}
            professionalMode={canUseProfessionalOracle}
          />
        ) : null}

        {/* ── 排盘输入 ── */}
        <div id="v17-natal-input" className="relative scroll-mt-24">
          {s.running ? (
            <div className="absolute inset-0 z-20 animate-[fadeOut_280ms_ease-out_forwards] rounded-2xl bg-black/50 backdrop-blur-[1px]" />
          ) : null}
          {!s.running ? <V17_NatalInput onStart={s.startRun} lang={language} /> : null}
        </div>

        {/* ── 运行态主体 ── */}
        {s.running ? (
          <div className="min-h-[60vh]">
            <div className="w-full space-y-3">
              {surfaceTabs.length > 1 ? (
                <V17_SurfaceTabs
                  items={surfaceTabs}
                  activeId={activeSurfaceTab}
                  onChange={(tab) => {
                    if (tab === "trace") {
                      openTraceSurface();
                    } else {
                      switchContentSurface(tab);
                    }
                  }}
                />
              ) : null}

              <V17_FeatureOutlet
                activeId={activeSurfaceTab}
                renderers={{
                  core: () => (
                    <>
                  <V17MobileResultSummary
                    ui={ui}
                    term={term}
                    termList={termList}
                    fourPillars={fourPillars}
                    luckPillar={luckPillarSnap}
                    flowPillar={flowPillarSnap}
                    selectedYear={s.selectedLuckYear}
                    onYearChange={s.setSelectedLuckYear}
                    birthLine={`${s.birthTimeISO} · ${term(s.natalGender || "")}`}
                    judgement={patternJudgement}
                    patternLeader={patternLeader}
                    useGods={useGods}
                    tabooGods={tabooGods}
                    tongguanGods={tongguanGods}
                    relationRows={relationDynamicsSummary}
                    riskRows={riskRows}
                  />
                  {!canUseProfessionalOracle ? (
                    <V17SimpleOracleSummary
                      ui={ui}
                      term={term}
                      termList={termList}
                      fourPillars={fourPillars}
                      luckPillar={luckPillarSnap}
                      flowPillar={flowPillarSnap}
                      birthLine={`${s.birthTimeISO} · ${term(s.natalGender || "")}`}
                      judgement={patternJudgement}
                      patternLeader={patternLeader}
                      useGods={useGods}
                      tabooGods={tabooGods}
                      tongguanGods={tongguanGods}
                    />
                  ) : null}
                  {canUseProfessionalOracle ? (
                  <div className="hidden sm:block">
                    <V17_SixPillarsPanel
                    fourPillars={fourPillars}
                    luckPillarFromServer={typeof luckPillarSnap === "string" ? luckPillarSnap : undefined}
                    flowPillarFromServer={typeof flowPillarSnap === "string" ? flowPillarSnap : undefined}
                    godRingInfo={godRingInfo}
                    tenGodDecomposition={
                      payload.ten_gods_decomposition_l0 && typeof payload.ten_gods_decomposition_l0 === "object"
                        ? (payload.ten_gods_decomposition_l0 as Record<
                            string,
                            {
                              manifest?: number;
                              root?: number;
                              momentum?: number;
                              momentum_month_order?: number;
                              momentum_stage?: number;
                              momentum_stage_lu?: number;
                              momentum_stage_blade?: number;
                              momentum_stage_general?: number;
                              momentum_structure?: number;
                              momentum_auxiliary?: number;
                              momentum_other?: number;
                              hidden?: number;
                              total?: number;
                            }
                          >)
                        : undefined
                    }
                    tenGodLedger={
                      payload.ten_gods_ledger && typeof payload.ten_gods_ledger === "object"
                        ? (payload.ten_gods_ledger as Record<string, Array<{ step?: string; reason?: string; delta?: number; val?: number }>>)
                        : undefined
                    }
                    climateField={climateField}
                    climateModifierLayer={climateModifierLayer}
                    climateTheme={climateTheme}
                    xiangfaTheme={xiangfaTheme}
                    patternLeader={
                      patternLeader
                        ? {
                            name: patternLeader.name,
                            confidence: patternLeader.confidence,
                            statusLabel: patternLeader.statusLabel,
                            scope: patternLeader.scope,
                          }
                        : undefined
                    }
                    projectionBridgeProtocol={
                      payload.projection_bridge_protocol && typeof payload.projection_bridge_protocol === "object"
                        ? (payload.projection_bridge_protocol as Record<string, unknown>)
                        : undefined
                    }
                    relationFormationSummary={relationFormationSummary}
                    relationDynamicsSummary={relationDynamicsSummary}
                    birthTimeISO={s.birthTimeISO}
                    gender={s.natalGender}
                    calendarType={s.natalCalendar}
                    lunarIsLeapMonth={s.lunarIsLeapMonth}
                    selectedYear={s.selectedLuckYear}
                    onYearChange={s.setSelectedLuckYear}
                    detailMode="core"
                    lang={language}
                  />
                  </div>
                  ) : null}
                  <V17_PurpleVerdictCard
                    frames={s.frames}
                    connectTickMs={s.connectTickMs}
                    running={s.running}
                    llmStatusText={s.llmStatusText}
                    llmStatusDetail={s.llmStatusDetail}
                    llmLifecyclePhase={s.llmLifecyclePhase}
                    lang={language}
                  />
                  {canReadEvidence ? (
                    <V17EvidencePanel
                      ui={ui}
                      term={term}
                      items={evidenceItems}
                      summary={evidenceSummary}
                      sessionId={s.sessionId}
                      chartFingerprint={String(payload.physics_fingerprint || "")}
                      reviewerRole={user?.role || "user"}
                      birthTimeISO={s.birthTimeISO}
                      gender={s.natalGender || "male"}
                      calendarType={s.natalCalendar || "solar"}
                      lunarIsLeapMonth={s.lunarIsLeapMonth}
                      fourPillars={fourPillars}
                      luckPillar={luckPillarSnap}
                      flowPillar={flowPillarSnap}
                      selectedYear={s.selectedLuckYear}
                    />
                  ) : null}
                  <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-zinc-800 bg-zinc-900/50 p-2.5">
                    <p className="text-xs text-zinc-400">
                      {canUseProfessionalOracle
                        ? t(language, "oracle.core.decision_notice")
                        : ui("系统会基于当前命盘生成简明断语。", "The system will generate a concise reading from the current chart.", "현재 명반을 바탕으로 간결한 단언을 생성합니다.")}
                      {canUseProfessionalOracle && s.canAutoGenerateVerdict ? ` ${t(language, "oracle.core.ready_for_verdict")}` : ""}
                    </p>
                    <button
                      type="button"
                      onClick={() => s.triggerVerdict(verdictTriggerPrompt)}
                      disabled={verdictButtonBusy}
                      aria-busy={verdictButtonBusy}
                      className={`group relative inline-flex min-h-9 w-full items-center justify-center gap-1.5 overflow-hidden rounded-lg border px-3 py-2 text-sm font-semibold transition sm:w-auto ${
                        verdictButtonBusy
                          ? "cursor-wait border-cyan-300/50 bg-cyan-500/15 text-cyan-50 shadow-[0_0_24px_rgba(34,211,238,0.18)]"
                          : "border-cyan-500/35 bg-cyan-950/25 text-cyan-100 hover:border-cyan-300/55 hover:bg-cyan-900/35 hover:text-white"
                      }`}
                    >
                      <Sparkles className={`relative z-10 h-4 w-4 ${verdictButtonBusy ? "motion-safe:animate-pulse" : ""}`} />
                      <span className="relative z-10">{verdictButtonLabel}</span>
                      {verdictButtonBusy ? (
                        <span className="relative z-10 inline-flex items-center gap-0.5" aria-hidden="true">
                          <span className="h-1 w-1 animate-bounce rounded-full bg-current [animation-delay:-200ms]" />
                          <span className="h-1 w-1 animate-bounce rounded-full bg-current [animation-delay:-100ms]" />
                          <span className="h-1 w-1 animate-bounce rounded-full bg-current" />
                        </span>
                      ) : null}
                    </button>
                  </div>
                  {canUseProfessionalOracle ? (
                    <V17_DecisionInbox
                      frames={s.frames}
                      adoptedIds={s.adoptedDecisions.map((x) => x.id).filter((id): id is string => !!id)}
                      focusedDecisionId={focusedDecisionId}
                      viewMode="manual_only"
                      locked={s.decisionInboxLocked}
                      lockMessage={s.decisionInboxLockMessage}
                      onAdopted={s.handleAdopted}
                      onAdoptedBatch={s.handleAdoptedBatch}
                      onPlanAction={s.handlePlanAction}
                      lang={language}
                    />
                  ) : null}
                  {!s.hasNarrative ? (
                    <p className="mt-3 text-xs text-violet-200/80">{t(language, "oracle.core.weaving")}</p>
                  ) : null}
                    </>
                  ),
                  trace: () => (
                    <>
                  <V17ToolboxDeck
                    ui={ui}
                    traceSignalCount={traceSignalCount}
                    pendingDecisionCount={s.pendingDecisionWorkCount}
                    modelLabel={s.modelLabel}
                    llmLifecyclePhase={s.llmLifecyclePhase}
                  />
                  <details className="group rounded-2xl border border-cyan-500/18 bg-[linear-gradient(180deg,rgba(9,9,11,0.92),rgba(16,24,39,0.72))] p-3">
                    <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-left">
                      <div>
                        <p className="text-[10px] uppercase tracking-[0.22em] text-cyan-300">{t(language, "oracle.trace.console.title")}</p>
                        <p className="mt-1 text-[12px] leading-5 text-zinc-400">
                          {ui(
                            "展开查看完整调试面板、裁决箱与后端链路。",
                            "Expand to inspect the full debug panel, decision inbox, and backend link.",
                            "전체 디버그 패널, 판정함, 백엔드 링크를 보려면 펼치세요.",
                          )}
                        </p>
                      </div>
                      <span className="rounded-full border border-zinc-700 bg-zinc-950/70 p-1.5 text-zinc-300 group-open:rotate-180">
                        <ChevronDown className="h-3.5 w-3.5" />
                      </span>
                    </summary>
                    <div className="mt-3 space-y-3 border-t border-zinc-800/80 pt-3">
                      <div className="rounded-xl border border-cyan-500/20 bg-cyan-950/15 p-3 text-[12px] leading-6 text-cyan-50">
                        {t(language, "oracle.trace.notice")}
                      </div>
                      <V17_TracePanel
                        surfaceMode="tab"
                        contentMode="debug_only"
                        collapsed={false}
                        onToggle={closeTraceSurface}
                        focusedDecisionId={focusedDecisionId}
                        llmMeta={s.llmMeta}
                        llmLifecyclePhase={s.llmLifecyclePhase}
                        llmStatusText={s.llmStatusText}
                        llmStatusDetail={s.llmStatusDetail}
                        modelLabel={s.modelLabel}
                        connectTickMs={s.connectTickMs}
                        lastHeartbeatStep={s.lastHeartbeatStep}
                        heartbeatHistory={s.heartbeatHistory}
                        streamClosed={s.streamClosed}
                        fullTrace={s.fullTrace}
                        llmAuditSnapshot={s.llmAuditSnapshot}
                        latestNarrator={s.latestNarrator as { payload?: Record<string, unknown> } | undefined}
                        traceHits={s.traceHits}
                        traceFacts={s.traceFacts}
                        birthTimeISO={s.birthTimeISO}
                        natalGender={s.natalGender}
                        natalCalendar={s.natalCalendar}
                        selectedLuckYear={s.selectedLuckYear}
                        streamEndpoint={s.streamEndpoint}
                        streamBody={s.streamBody}
                        streamQuery={s.streamQuery}
                        physicsSnapshot={s.physicsSnapshot as { payload?: Record<string, unknown> } | undefined}
                      />
                      <div className="rounded-xl border border-cyan-500/20 bg-[linear-gradient(180deg,rgba(8,47,73,0.28),rgba(9,9,11,0.84))] p-3">
                        <div className="flex flex-wrap items-start justify-between gap-3">
                          <div>
                            <p className="text-[10px] uppercase tracking-[0.22em] text-cyan-300">{t(language, "oracle.trace.console.title")}</p>
                            <p className="mt-1 text-[12px] leading-6 text-cyan-50">
                              {t(language, "oracle.trace.console.desc")}
                            </p>
                          </div>
                          <div className="flex flex-wrap gap-1.5 text-[10px]">
                            <span className="rounded-full border border-cyan-500/25 bg-cyan-950/30 px-2 py-1 text-cyan-100">
                              {t(language, "oracle.trace.console.badge.backend")}
                            </span>
                            <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-2 py-1 text-zinc-200">
                              {t(language, "oracle.trace.console.badge.full")}
                            </span>
                          </div>
                        </div>
                      </div>
                      <V17_DecisionInbox
                        frames={s.frames}
                        adoptedIds={s.adoptedDecisions.map((x) => x.id).filter((id): id is string => !!id)}
                        focusedDecisionId={focusedDecisionId}
                        locked={s.decisionInboxLocked}
                        lockMessage={s.decisionInboxLockMessage}
                        onAdopted={s.handleAdopted}
                        onAdoptedBatch={s.handleAdoptedBatch}
                        onPlanAction={s.handlePlanAction}
                        lang={language}
                      />
                    </div>
                  </details>
                    </>
                  ),
                  auxiliary: () => (
                    <>
                  <div className="rounded-xl border border-cyan-500/20 bg-cyan-950/15 p-3 text-[12px] leading-6 text-cyan-50">
                    {t(language, "oracle.aux.notice")}
                  </div>
                  <V17MobileAnalysisDeck
                    ui={ui}
                    counts={{
                      ledger: evidenceItems.length,
                      structure: structureSignalCount,
                      runtime: runtimeLedgerSignalCount,
                      authority: authoritySignalCount,
                      patterns: livePatternCandidates.length,
                      collaboration: collaborationUserCount,
                    }}
                    canManageUsers={canManageUsers && user?.role === "manager"}
                    onOpen={openAuxiliarySection}
                  />
                  <AuxiliarySection
                    id="aux-ledger"
                    title={ui("命理师账本", "Practitioner Ledger", "명리사 장부")}
                    subtitle={ui("反馈、案例与基准候选回看", "Feedback, cases, and benchmark candidates", "피드백, 사례, 기준 후보 회고")}
                    badge={canReadEvidence ? ui("已接入", "online", "연결됨") : "locked"}
                    open={auxiliarySections.ledger}
                    onToggle={() => toggleAuxiliarySection("ledger")}
                  >
                    <V17PractitionerLedgerPanel
                      ui={ui}
                      reviewerRole={user?.role || "user"}
                    />
                  </AuxiliarySection>
                  <div className="rounded-2xl border border-cyan-500/20 bg-[radial-gradient(circle_at_top_left,rgba(34,211,238,0.13),transparent_34%),linear-gradient(180deg,rgba(9,9,11,0.92),rgba(24,24,27,0.74))] p-3">
                    <div className="flex flex-wrap items-start justify-between gap-3">
                      <div>
                        <p className="text-[10px] uppercase tracking-[0.24em] text-cyan-300">{t(language, "oracle.topic_hub.title")}</p>
                        <h2 className="mt-1 text-sm font-semibold text-zinc-100">{t(language, "oracle.topic_hub.heading")}</h2>
                        <p className="mt-1 max-w-2xl text-[11px] leading-5 text-zinc-400">
                          {t(language, "oracle.topic_hub.desc")}
                        </p>
                      </div>
                      <div className="flex flex-wrap gap-1.5 text-[10px]">
                        <span className="rounded-full border border-cyan-500/25 bg-cyan-950/25 px-2 py-1 text-cyan-100">
                          {t(language, "oracle.topic_hub.active")} {topicHubItems.filter((item) => item.tone !== "muted").length}
                        </span>
                        <span className="rounded-full border border-emerald-500/25 bg-emerald-950/25 px-2 py-1 text-emerald-100">
                          {t(language, "oracle.topic_hub.hard")}
                        </span>
                        <span className="rounded-full border border-fuchsia-500/25 bg-fuchsia-950/25 px-2 py-1 text-fuchsia-100">
                          {t(language, "oracle.topic_hub.soft")}
                        </span>
                      </div>
                    </div>
                    <div className="mt-3 grid gap-2 md:grid-cols-2 xl:grid-cols-3">
                      {topicHubItems.map((item) => (
                        <div key={item.key} className={`rounded-xl border p-3 ${topicHubTone(item.tone)}`}>
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <div className="text-[12px] font-semibold">{item.title}</div>
                              <p className="mt-1 text-[10px] leading-4 text-zinc-400">{item.subtitle}</p>
                            </div>
                            <span className={`rounded-full border px-2 py-0.5 text-[9px] ${topicHubBadgeTone(item.tone)}`}>
                              {item.status}
                            </span>
                          </div>
                          <div className="mt-3 grid gap-1.5 text-[10px]">
                            {item.details.map((detail) => (
                              <div key={`${item.key}_${detail}`} className="rounded-lg border border-white/10 bg-black/20 px-2 py-1 text-zinc-300">
                                {detail}
                              </div>
                            ))}
                          </div>
                          {item.badges.length ? (
                            <div className="mt-3 flex flex-wrap gap-1.5">
                              {item.badges.slice(0, 4).map((badge) => (
                                <span key={`${item.key}_${badge}`} className={`rounded-full border px-2 py-0.5 text-[9px] ${topicHubBadgeTone(item.tone)}`}>
                                  {badge}
                                </span>
                              ))}
                            </div>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  </div>
                  <AuxiliarySection
                    id="aux-structure"
                    title={t(language, "oracle.section.structure.title")}
                    subtitle={t(language, "oracle.section.structure.subtitle")}
                    badge={`${structureSignalCount} ${ui("信号", "signals", "신호")}`}
                    open={auxiliarySections.structure}
                    onToggle={() => toggleAuxiliarySection("structure")}
                  >
                    <V17_SixPillarsPanel
                      fourPillars={fourPillars}
                      luckPillarFromServer={typeof luckPillarSnap === "string" ? luckPillarSnap : undefined}
                      flowPillarFromServer={typeof flowPillarSnap === "string" ? flowPillarSnap : undefined}
                      godRingInfo={godRingInfo}
                      tenGodDecomposition={
                        payload.ten_gods_decomposition_l0 && typeof payload.ten_gods_decomposition_l0 === "object"
                          ? (payload.ten_gods_decomposition_l0 as Record<
                              string,
                              {
                                manifest?: number;
                                root?: number;
                                momentum?: number;
                                momentum_month_order?: number;
                                momentum_stage?: number;
                                momentum_stage_lu?: number;
                                momentum_stage_blade?: number;
                                momentum_stage_general?: number;
                                momentum_structure?: number;
                                momentum_auxiliary?: number;
                                momentum_other?: number;
                                hidden?: number;
                                total?: number;
                              }
                            >)
                          : undefined
                      }
                      tenGodLedger={
                        payload.ten_gods_ledger && typeof payload.ten_gods_ledger === "object"
                          ? (payload.ten_gods_ledger as Record<string, Array<{ step?: string; reason?: string; delta?: number; val?: number }>>)
                          : undefined
                      }
                      climateField={climateField}
                      climateModifierLayer={climateModifierLayer}
                      climateTheme={climateTheme}
                      xiangfaTheme={xiangfaTheme}
                      projectionBridgeProtocol={
                        payload.projection_bridge_protocol && typeof payload.projection_bridge_protocol === "object"
                          ? (payload.projection_bridge_protocol as Record<string, unknown>)
                          : undefined
                      }
                      relationFormationSummary={relationFormationSummary}
                      relationDynamicsSummary={relationDynamicsSummary}
                      birthTimeISO={s.birthTimeISO}
                      gender={s.natalGender}
                      calendarType={s.natalCalendar}
                      lunarIsLeapMonth={s.lunarIsLeapMonth}
                      selectedYear={s.selectedLuckYear}
                      onYearChange={s.setSelectedLuckYear}
                      detailMode="auxiliary"
                      lang={language}
                    />
                  </AuxiliarySection>

                  <AuxiliarySection
                    id="aux-runtime"
                    title={t(language, "oracle.section.runtime.title")}
                    subtitle={t(language, "oracle.section.runtime.subtitle")}
                    badge={`${runtimeLedgerSignalCount} ${ui("账本", "ledger", "장부")}`}
                    open={auxiliarySections.runtime}
                    onToggle={() => toggleAuxiliarySection("runtime")}
                  >
                    <V17_TracePanel
                      surfaceMode="tab"
                      contentMode="insight_only"
                      showChrome={false}
                      collapsed={false}
                      onToggle={() => {}}
                      focusedDecisionId={focusedDecisionId}
                      llmMeta={s.llmMeta}
                      llmLifecyclePhase={s.llmLifecyclePhase}
                      llmStatusText={s.llmStatusText}
                      llmStatusDetail={s.llmStatusDetail}
                      modelLabel={s.modelLabel}
                      connectTickMs={s.connectTickMs}
                      lastHeartbeatStep={s.lastHeartbeatStep}
                      heartbeatHistory={s.heartbeatHistory}
                      streamClosed={s.streamClosed}
                      fullTrace={s.fullTrace}
                      llmAuditSnapshot={s.llmAuditSnapshot}
                      latestNarrator={s.latestNarrator as { payload?: Record<string, unknown> } | undefined}
                      traceHits={s.traceHits}
                      traceFacts={s.traceFacts}
                      birthTimeISO={s.birthTimeISO}
                      natalGender={s.natalGender}
                      natalCalendar={s.natalCalendar}
                      selectedLuckYear={s.selectedLuckYear}
                      streamEndpoint={s.streamEndpoint}
                      streamBody={s.streamBody}
                      streamQuery={s.streamQuery}
                      physicsSnapshot={s.physicsSnapshot as { payload?: Record<string, unknown> } | undefined}
                      lang={language}
                    />
                  </AuxiliarySection>

                  <AuxiliarySection
                    id="aux-authority"
                    title={t(language, "oracle.section.authority.title")}
                    subtitle={t(language, "oracle.section.authority.subtitle")}
                    badge={`${authoritySignalCount} ${ui("神", "gods", "신")}`}
                    open={auxiliarySections.authority}
                    onToggle={() => toggleAuxiliarySection("authority")}
                  >
                    <V17_GodRingExplainCard
                      godRings={godRingInfo}
                      focusedDecisionId={focusedDecisionId}
                      onFocusDecision={(decisionId) => {
                        setFocusedDecisionId(decisionId);
                        openTraceSurface();
                      }}
                      lang={language}
                    />
                  </AuxiliarySection>

                  <AuxiliarySection
                    id="aux-patterns"
                    title={t(language, "oracle.section.pattern.title")}
                    subtitle={t(language, "oracle.section.pattern.subtitle")}
                    badge={`${livePatternCandidates.length} ${ui("格局", "patterns", "격국")}`}
                    open={auxiliarySections.patterns}
                    onToggle={() => toggleAuxiliarySection("patterns")}
                  >
                    <div className="rounded-xl border border-cyan-500/20 bg-[linear-gradient(180deg,rgba(12,74,110,0.32),rgba(9,9,11,0.76))] p-3">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <div>
                          <p className="text-[10px] uppercase tracking-[0.22em] text-cyan-300">
                            {ui("格局总览", "Pattern Overview", "격국 총람")}
                          </p>
                          <p className="mt-1 text-sm text-cyan-50">
                            {ui(
                              "当前盘面的主格局、次格局、动态来源、置信度与系统判读",
                              "Primary pattern, secondary candidates, runtime sources, confidence, and system reading.",
                              "현재 명식의 주격, 보조 격국, 동적 출처, 신뢰도와 시스템 판독입니다.",
                            )}
                          </p>
                        </div>
                        <div className="flex flex-wrap gap-1.5 text-[10px]">
                          <span className="rounded-full border border-cyan-500/20 bg-zinc-950/60 px-2 py-1 text-cyan-100">
                            {ui("候选", "Candidates", "후보")} {livePatternCandidates.length}
                          </span>
                          {activePatternScopes.map((scope) => (
                            <span key={`pattern_scope_${scope}`} className="rounded-full border border-cyan-500/20 bg-zinc-950/60 px-2 py-1 text-cyan-100">
                              {term(scope)}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div className="mt-3 rounded-xl border border-cyan-500/15 bg-zinc-950/55 p-3">
                        <p className="text-[10px] uppercase tracking-[0.18em] text-cyan-300">
                          {ui("系统判读", "System Reading", "시스템 판독")}
                        </p>
                        <p className="mt-2 text-[12px] leading-6 text-cyan-50">{patternJudgement}</p>
                      </div>

                      {patternLeader ? (
                        <div className="mt-3 grid gap-3 xl:grid-cols-[1.05fr_0.95fr]">
                          <div className="rounded-xl border border-cyan-500/15 bg-zinc-950/55 p-3">
                            <div className="flex flex-wrap items-start justify-between gap-2">
                              <div>
                                <p className="text-[10px] uppercase tracking-[0.18em] text-cyan-300">
                                  {ui("主格局", "Primary Pattern", "주격")}
                                </p>
                                <p className="mt-1 text-lg text-cyan-50">{term(patternLeader.name)}</p>
                                <p className="mt-1 text-[11px] text-zinc-400">{term(patternLeader.family)}</p>
                              </div>
                              <div className="flex flex-wrap gap-1.5">
                                <span className={`rounded-full border px-2 py-1 text-[10px] ${patternStatusToneForRuntime(patternLeader.statusLabel)}`}>
                                  {term(patternLeader.statusLabel)}
                                </span>
                                <span className={`rounded-full border px-2 py-1 text-[10px] ${patternConfidenceTone(patternLeader.confidence)}`}>
                                  {ui("置信", "Confidence", "신뢰도")} {Math.round(patternLeader.confidence * 100)}%
                                </span>
                              </div>
                            </div>
                            <div className="mt-3 flex flex-wrap gap-1.5 text-[10px]">
                              <span className="rounded-full border border-cyan-500/20 bg-cyan-950/30 px-2 py-1 text-cyan-100">{term(patternLeader.scope)}</span>
                              <span className="rounded-full border border-zinc-700 bg-zinc-900/70 px-2 py-1 text-zinc-200">
                                {ui("主落点", "Focus", "초점")} {term(patternLeader.target)}
                              </span>
                              <span className="rounded-full border border-zinc-700 bg-zinc-900/70 px-2 py-1 text-zinc-300">
                                {patternLeader.source === "claim" ? ui("来自 Claim 层", "From Claim layer", "Claim 계층") : ui("来自 Decision 层", "From Decision layer", "Decision 계층")}
                              </span>
                            </div>
                            {(patternLeader.gate || patternLeader.gateReason) ? (
                              <div className="mt-3 rounded-lg border border-zinc-800 bg-zinc-900/45 p-2">
                                <p className="text-[10px] uppercase tracking-[0.16em] text-emerald-300">
                                  {ui("成格门槛", "Formation Gate", "성격 관문")}
                                </p>
                                <p className="mt-1 text-[11px] text-emerald-100">
                                  {patternLeader.gate ? term(patternLeader.gate) : ui("候选审计", "Candidate audit", "후보 감사")}
                                </p>
                                {patternLeader.gateReason ? <p className="mt-1 text-[10px] leading-relaxed text-zinc-400">{patternLeader.gateReason}</p> : null}
                              </div>
                            ) : null}
                            {patternLeader.scopeWeights.length ? (
                              <div className="mt-3 rounded-lg border border-zinc-800 bg-zinc-900/45 p-2">
                                <p className="text-[10px] uppercase tracking-[0.16em] text-cyan-300">
                                  {ui("来源证据", "Scope Evidence", "출처 근거")}
                                </p>
                                <div className="mt-2 grid gap-1.5">
                                  {patternLeader.scopeWeights.map((item) => (
                                    <div key={`${patternLeader.key}_${item.label}`} className="grid gap-1">
                                      <div className="flex items-center justify-between text-[10px]">
                                        <span className="text-zinc-300">{term(item.label)}</span>
                                        <span className="text-cyan-200">{Math.round(item.ratio * 100)}%</span>
                                      </div>
                                      <div className="h-1.5 overflow-hidden rounded-full bg-zinc-800">
                                        <div className="h-full rounded-full bg-[linear-gradient(90deg,rgba(34,211,238,0.95),rgba(45,212,191,0.95))]" style={{ width: `${Math.max(6, Math.round(item.ratio * 100))}%` }} />
                                      </div>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            ) : null}
                            {patternLeader.profileText ? (
                              <p className="mt-3 text-[11px] leading-relaxed text-zinc-300">
                                {ui("家族混合", "Family mixture", "계열 혼합")}：<span className="text-cyan-100">{patternLeader.profileText}</span>
                              </p>
                            ) : null}
                            {patternLeader.projectionText ? (
                              <p className="mt-2 text-[11px] leading-relaxed text-zinc-400">
                                {ui("投影焦点", "Projection focus", "투영 초점")}：{patternLeader.projectionText}
                              </p>
                            ) : null}
                            {leaderBreakRisks.length ? (
                              <div className="mt-3 rounded-lg border border-rose-500/20 bg-rose-950/20 p-2">
                                <p className="text-[10px] uppercase tracking-[0.16em] text-rose-300">
                                  {ui("破格风险", "Break Risks", "파격 위험")}
                                </p>
                                <div className="mt-2 flex flex-wrap gap-1.5">
                                  {leaderBreakRisks.map((risk) => (
                                    <span key={`${patternLeader.key}_${risk}`} className="rounded-full border border-rose-500/20 bg-zinc-950/50 px-2 py-1 text-[10px] text-rose-100">
                                      {term(risk)}
                                    </span>
                                  ))}
                                </div>
                              </div>
                            ) : null}
                          </div>

                          <div className="rounded-xl border border-cyan-500/15 bg-zinc-950/55 p-3">
                            <p className="text-[10px] uppercase tracking-[0.18em] text-cyan-300">
                              {ui("次格局", "Secondary Patterns", "보조 격국")}
                            </p>
                            <div className="mt-2 grid gap-2">
                              {patternRunners.length ? (
                                patternRunners.map((item) => (
                                  <div key={item.key} className="rounded-lg border border-zinc-800 bg-zinc-900/55 p-2">
                                    <div className="flex items-start justify-between gap-2">
                                      <div>
                                        <p className="text-[11px] text-cyan-50">{term(item.name)}</p>
                                        <p className="text-[9px] text-zinc-500">{term(item.family)} · {term(item.scope)}</p>
                                      </div>
                                      <div className="flex flex-wrap gap-1">
                                        <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${patternStatusToneForRuntime(item.statusLabel)}`}>
                                          {term(item.statusLabel)}
                                        </span>
                                        <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${patternConfidenceTone(item.confidence)}`}>
                                          {Math.round(item.confidence * 100)}%
                                        </span>
                                      </div>
                                    </div>
                                    <p className="mt-1 text-[10px] text-zinc-300">
                                      {ui("主落点", "Focus", "초점")} {term(item.target)}{item.profileText ? ` · ${item.profileText}` : ""}
                                    </p>
                                    {item.scopeWeights.length ? (
                                      <div className="mt-1 flex flex-wrap gap-1">
                                        {item.scopeWeights.map((scope) => (
                                          <span key={`${item.key}_${scope.label}`} className="rounded-full border border-zinc-700 bg-zinc-950/60 px-1.5 py-0.5 text-[9px] text-zinc-300">
                                            {term(scope.label)} {Math.round(scope.ratio * 100)}%
                                          </span>
                                        ))}
                                      </div>
                                    ) : null}
                                    {item.projectionText ? <p className="mt-1 text-[9px] text-zinc-500">{item.projectionText}</p> : null}
                                  </div>
                                ))
                              ) : (
                                <div className="rounded-lg border border-zinc-800 bg-zinc-900/55 p-2 text-[10px] text-zinc-500">
                                  {ui(
                                    "当前尚未形成明确的次格局分层，系统只识别到一个主候选。",
                                    "No clear secondary pattern layer has formed yet; the system currently sees only one primary candidate.",
                                    "아직 명확한 보조 격국 층이 형성되지 않았고, 시스템은 현재 하나의 주 후보만 인식했습니다.",
                                  )}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="mt-3 rounded-xl border border-cyan-500/15 bg-zinc-950/55 p-3 text-[11px] text-zinc-400">
                          {ui(
                            "当前盘面还没有显式格局候选，系统会随着插件命中和 Claim 聚合继续补全。",
                            "No explicit pattern candidate has appeared yet; the system will keep completing this as plugins and claims aggregate.",
                            "현재 명식에는 명시적 격국 후보가 없으며, 플러그인 명중과 Claim 집계에 따라 계속 보완됩니다.",
                          )}
                        </div>
                      )}
                    </div>
                  </AuxiliarySection>

                  {canManageUsers && user?.role === "manager" ? (
	                    <AuxiliarySection
	                      id="aux-collaboration"
	                      title={t(language, "oracle.section.collab.title")}
                      subtitle={t(language, "oracle.section.collab.subtitle")}
                      badge={collaborationUserCount ? `${collaborationUserCount} ${ui("用户", "users", "사용자")}` : "sync"}
                      open={auxiliarySections.collaboration}
                      onToggle={() => toggleAuxiliarySection("collaboration")}
                    >
                      <div className="rounded-2xl border border-amber-500/20 bg-amber-950/10 p-3">
                        {authUsersMessage ? (
                          <p className="mb-3 rounded-lg border border-amber-500/20 bg-black/20 px-3 py-2 text-[11px] text-amber-100">
                            {authUsersMessage}
                          </p>
                        ) : null}
                        <V17_AdminUsersPanel
                          users={authUsers}
                          loading={authUsersLoading}
	                          onRefresh={() => void loadAuthUsers()}
	                          onUpdateRole={updateAuthUserRole}
	                          onDecideRoleRequest={decideAuthRoleRequest}
	                          operatorRole="manager"
                          compact
                          title={t(language, "oracle.section.collab.title")}
                          description={t(language, "oracle.collab.desc")}
                        />
                      </div>
                    </AuxiliarySection>
                  ) : null}
                    </>
                  ),
                }}
              />
            </div>
          </div>
        ) : null}
      </V17_AppShell>
    </V17_PageGuard>
  );
}
