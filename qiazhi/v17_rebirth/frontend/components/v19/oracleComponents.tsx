"use client";

import { useState } from "react";
import {
  Activity,
  ArrowRight,
  CalendarDays,
  Check,
  ChevronDown,
  CircleUserRound,
  Clock3,
  FileSearch,
  Home,
  MapPin,
  MessageSquareText,
  Play,
  RotateCcw,
  ShieldCheck,
  ThumbsUp,
} from "lucide-react";
import type {
  ChartStructureSummaryProps,
  EvidenceCard,
  EvidenceCardListProps,
  FeedbackPanelProps,
  InferenceSignalItem,
  InferenceSignalListProps,
  LocalizedLabel,
  ReplayCardProps,
  ResultCardProps,
  SignalTagCategory,
  SignalTagProps,
  SupportedThemeId,
  ThemeId,
  ThemeOption,
  TimeStructureSummaryProps,
  UiLocale,
} from "./types";
import { labelText } from "./types";
import { StateGate, TrustBar } from "./primitives";
import type { BirthInput, CalendarType, Gender } from "@/lib/v19/chartStructureTypes";

function sourceText(source?: { sourceType: string; sourceKey: string; sourceVersion?: string }) {
  if (!source) {
    return "source: n/a";
  }

  return `${source.sourceType}.${source.sourceKey}${source.sourceVersion ? ` · ${source.sourceVersion}` : ""}`;
}

function categoryTone(category: SignalTagCategory) {
  const tones: Record<SignalTagCategory, string> = {
    day_master: "border-amber-200 bg-amber-50 text-amber-900",
    ten_god: "border-slate-200 bg-slate-50 text-slate-800",
    structure: "border-blue-200 bg-blue-50 text-blue-900",
    flow: "border-red-200 bg-red-50 text-red-800",
    conflict: "border-orange-200 bg-orange-50 text-orange-900",
    uncertainty: "border-amber-200 bg-amber-50 text-amber-900",
    verification: "border-emerald-200 bg-emerald-50 text-emerald-900",
    risk: "border-red-200 bg-red-50 text-red-800",
  };

  return tones[category];
}

function valueClass(value: string) {
  if (["weak", "blocked", "unstable", "high", "peer_overwhelms_wealth", "wealth_weak"].includes(value)) {
    return "text-red-700";
  }
  if (["passed", "stable", "active", "late_spring"].includes(value)) {
    return "text-emerald-700";
  }
  if (["medium", "conflicted", "leaning_weak"].includes(value)) {
    return "text-amber-700";
  }
  return "text-blue-700";
}

function isSupportedThemeId(themeId: ThemeId): themeId is SupportedThemeId {
  return themeId === "wealth_structure" || themeId === "income_stability" || themeId === "risk_opportunity";
}

export function SignalTag({ signal, locale }: { signal: SignalTagProps; locale: UiLocale }) {
  return (
    <div className={`rounded-xl border px-3 py-3 ${categoryTone(signal.category)}`}>
      <div className="text-[0.72rem] font-semibold uppercase tracking-[0.14em] opacity-75">
        {labelText(signal.label, locale)}
      </div>
      <div className={`break-safe mt-1 text-sm font-bold ${valueClass(signal.value)}`}>{signal.value}</div>
      {typeof signal.confidence === "number" ? (
        <div className="mt-1 text-[0.68rem] opacity-70">{Math.round(signal.confidence * 100)}% confidence</div>
      ) : null}
    </div>
  );
}

export function SystemContractHeader({ locale }: { locale: UiLocale }) {
  const steps = [
    { zh: "命盘结构", en: "chart structure", ko: "명식 구조" },
    { zh: "推理信号", en: "inference signals", ko: "추론 신호" },
    { zh: "验证结果", en: "verified result", ko: "검증 결과" },
    { zh: "证据", en: "evidence", ko: "근거" },
    { zh: "回放", en: "replay", ko: "리플레이" },
  ];

  return (
    <header className="overflow-hidden rounded-[2rem] border border-blue-100 bg-gradient-to-br from-white via-blue-50/60 to-amber-50/40 p-5 shadow-sm shadow-blue-100/70 sm:p-7">
      <div className="flex flex-col gap-5 xl:flex-row xl:items-start xl:justify-between">
        <div className="max-w-2xl">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-slate-950 text-white shadow-lg shadow-slate-300">
              <ShieldCheck className="h-6 w-6" aria-hidden="true" />
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-blue-700">V19 Oracle</p>
              <h1 className="text-2xl font-semibold tracking-[-0.04em] text-slate-950 sm:text-4xl">
                Structured Reasoning System
              </h1>
            </div>
          </div>
          <p className="mt-4 max-w-xl text-sm leading-7 text-slate-600 sm:text-base">
            A verified reasoning system for Bazi analysis. Not fortune-telling. Not chat. Not mystical.
          </p>
        </div>
        <div className="grid gap-2 text-sm text-slate-700 sm:grid-cols-3 xl:min-w-[520px]">
          <InfoBlock
            title={{ zh: "这是什么", en: "What is this?", ko: "무엇인가요?" }}
            content={{ zh: "先理解命盘，再输出可验证结果。", en: "It reads structure before producing verified results.", ko: "구조를 먼저 읽고 검증 가능한 결과를 냅니다." }}
            locale={locale}
          />
          <InfoBlock
            title={{ zh: "现在能问什么", en: "What can I ask?", ko: "무엇을 물을 수 있나요?" }}
            content={{ zh: "财富结构、收入稳定性、风险机会。", en: "Wealth structure, income stability, risk and opportunity.", ko: "재물 구조, 수입 안정성, 위험과 기회." }}
            locale={locale}
          />
          <InfoBlock
            title={{ zh: "下一步", en: "Next step", ko: "다음 단계" }}
            content={{ zh: "输入出生信息或使用样例命盘。", en: "Enter birth information or use the sample chart.", ko: "출생 정보를 입력하거나 샘플 명식을 사용하세요." }}
            locale={locale}
          />
        </div>
      </div>
      <div className="mt-6 flex flex-wrap items-center gap-2 text-xs font-semibold text-slate-500">
        {steps.map((step, index) => (
          <span key={step.en} className="flex items-center gap-2">
            <span>{labelText(step, locale)}</span>
            {index < steps.length - 1 ? <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" /> : null}
          </span>
        ))}
      </div>
    </header>
  );
}

function InfoBlock({ title, content, locale }: { title: LocalizedLabel; content: LocalizedLabel; locale: UiLocale }) {
  return (
    <div className="rounded-2xl border border-white/80 bg-white/75 p-4 shadow-sm">
      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{labelText(title, locale)}</div>
      <div className="mt-2 text-sm leading-6 text-slate-700">{labelText(content, locale)}</div>
    </div>
  );
}

export function BirthInputPanel({
  birthInput,
  onChange,
  onSubmit,
}: {
  birthInput: BirthInput;
  onChange: (birthInput: BirthInput) => void;
  onSubmit: () => void;
}) {
  const updateNumber = (key: "year" | "month" | "day" | "hour", value: string) => {
    onChange({
      ...birthInput,
      [key]: Number.parseInt(value, 10),
    });
  };

  const updateCalendarType = (calendar_type: CalendarType) => {
    onChange({
      ...birthInput,
      calendar_type,
    });
  };

  const updateGender = (gender: Gender) => {
    onChange({
      ...birthInput,
      gender,
    });
  };

  const rows = [
    { icon: CalendarDays, label: "Year", key: "year" as const, value: birthInput.year },
    { icon: CalendarDays, label: "Month", key: "month" as const, value: birthInput.month },
    { icon: CalendarDays, label: "Day", key: "day" as const, value: birthInput.day },
    { icon: Clock3, label: "Hour", key: "hour" as const, value: birthInput.hour },
  ];

  return (
    <div className="space-y-3">
      {rows.map((row) => {
        const Icon = row.icon;
        return (
          <div key={row.label} className="flex items-center justify-between gap-4 rounded-xl border border-slate-100 bg-white px-3 py-3">
            <div className="flex items-center gap-3 text-sm font-medium text-slate-600">
              <Icon className="h-4 w-4 text-blue-600" aria-hidden="true" />
              {row.label}
            </div>
            <input
              value={Number.isNaN(row.value) ? "" : row.value}
              onChange={(event) => updateNumber(row.key, event.target.value)}
              className="w-24 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-right text-sm font-semibold text-slate-950 outline-none transition focus:border-blue-400 focus:bg-white"
              inputMode="numeric"
            />
          </div>
        );
      })}
      <div className="grid grid-cols-2 gap-3">
        <label className="rounded-xl border border-slate-100 bg-white px-3 py-3 text-sm font-medium text-slate-600">
          <span className="mb-2 flex items-center gap-2">
            <CircleUserRound className="h-4 w-4 text-blue-600" aria-hidden="true" />
            Gender
          </span>
          <select
            value={birthInput.gender}
            onChange={(event) => updateGender(event.target.value as Gender)}
            className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-950 outline-none focus:border-blue-400"
          >
            <option value="male">male</option>
            <option value="female">female</option>
          </select>
        </label>
        <label className="rounded-xl border border-slate-100 bg-white px-3 py-3 text-sm font-medium text-slate-600">
          <span className="mb-2 flex items-center gap-2">
            <MapPin className="h-4 w-4 text-blue-600" aria-hidden="true" />
            Calendar
          </span>
          <select
            value={birthInput.calendar_type}
            onChange={(event) => updateCalendarType(event.target.value as CalendarType)}
            className="w-full rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm font-semibold text-slate-950 outline-none focus:border-blue-400"
          >
            <option value="solar">solar</option>
            <option value="lunar">lunar</option>
          </select>
        </label>
      </div>
      <button
        type="button"
        onClick={onSubmit}
        className="w-full rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white shadow-lg shadow-blue-200 transition hover:bg-blue-700"
      >
        Compute local structure
      </button>
    </div>
  );
}

export function UnsupportedBoundaryCard({ reason }: { reason: string }) {
  return (
    <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900">
      <div className="text-xs font-semibold uppercase tracking-[0.18em] text-amber-700">unsupported boundary</div>
      <h3 className="mt-2 text-base font-semibold">Input not supported by local P3 prototype</h3>
      <p className="break-safe mt-2">
        reason: <span className="font-semibold">{reason}</span>
      </p>
      <p className="mt-2 text-amber-800">Solar input is supported. Lunar conversion is intentionally not implemented in P3.</p>
    </div>
  );
}

export function ChartStructureSummary({ chart, locale }: { chart: ChartStructureSummaryProps; locale: UiLocale }) {
  const signals = chart.signals.slice(0, chart.maxVisibleSignals ?? 5);

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
      {signals.map((signal) => (
        <SignalTag key={`${signal.label.en}-${signal.value}`} signal={signal} locale={locale} />
      ))}
    </div>
  );
}

export function FlowYearSelector({
  selectedYear,
  onChange,
}: {
  selectedYear: number;
  onChange: (year: number) => void;
}) {
  return (
    <label className="flex items-center justify-between gap-4 rounded-xl border border-slate-100 bg-white px-3 py-3 text-sm font-medium text-slate-600">
      <span className="flex items-center gap-3">
        <CalendarDays className="h-4 w-4 text-blue-600" aria-hidden="true" />
        Flow Year
      </span>
      <input
        value={Number.isNaN(selectedYear) ? "" : selectedYear}
        onChange={(event) => onChange(Number.parseInt(event.target.value, 10))}
        className="w-28 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-right text-sm font-semibold text-slate-950 outline-none transition focus:border-blue-400 focus:bg-white"
        inputMode="numeric"
      />
    </label>
  );
}

export function TimeStructureSummary({ timeStructure }: { timeStructure: TimeStructureSummaryProps }) {
  const { flowYear } = timeStructure;
  const relationRows = [
    ...flowYear.relations_with_natal.clashes.map((relation) => ({ kind: "clash", relation })),
    ...flowYear.relations_with_natal.combinations.map((relation) => ({ kind: "combination", relation })),
  ];

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-cyan-200 bg-cyan-50 px-3 py-3 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-800">
        Structure only · no prediction
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Flow Year</div>
          <div className="mt-2 text-lg font-semibold text-slate-950">
            {flowYear.year} ({flowYear.pillar.stem}
            {flowYear.pillar.branch})
          </div>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Relations</div>
          <div className="mt-2 space-y-1 text-sm font-semibold text-slate-800">
            {relationRows.length > 0 ? (
              relationRows.map((row) => (
                <div key={`${row.kind}-${row.relation}`}>
                  {row.kind}: {row.relation}
                </div>
              ))
            ) : (
              <div>none</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export function InferenceSignalList({ inference, locale }: { inference: InferenceSignalListProps; locale: UiLocale }) {
  return (
    <div className="space-y-3">
      {inference.signals.map((signal) => (
        <InferenceSignalRow key={signal.signalKey} signal={signal} locale={locale} />
      ))}
    </div>
  );
}

function InferenceSignalRow({ signal, locale }: { signal: InferenceSignalItem; locale: UiLocale }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-3">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="flex w-full items-start justify-between gap-3 text-left"
        aria-expanded={open}
      >
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className={`rounded-full border px-2 py-1 text-xs font-semibold ${categoryTone(signal.category)}`}>
              {labelText(signal.label, locale)}
            </span>
            <span className={`break-safe text-sm font-bold ${valueClass(signal.value)}`}>{signal.value}</span>
          </div>
          {signal.shortReason ? (
            <p className="mt-2 text-sm leading-6 text-slate-600">{labelText(signal.shortReason, locale)}</p>
          ) : null}
        </div>
        <ChevronDown className={`mt-1 h-4 w-4 shrink-0 text-slate-500 transition ${open ? "rotate-180" : ""}`} />
      </button>
      {open ? (
        <div className="mt-3 space-y-2 border-t border-slate-100 pt-3 text-xs leading-5 text-slate-500">
          {signal.sources.map((source) => (
            <div key={`${source.sourceType}-${source.sourceKey}`} className="break-safe rounded-lg bg-slate-50 px-3 py-2">
              {sourceText(source)}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function ThemeSelector({
  options,
  selectedThemeId,
  onSelect,
  locale,
}: {
  options: ThemeOption[];
  selectedThemeId?: SupportedThemeId;
  onSelect: (themeId: SupportedThemeId) => void;
  locale: UiLocale;
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {options.map((option) => {
        const selected = option.themeId === selectedThemeId;
        const themeId = option.themeId;
        const supported = isSupportedThemeId(themeId);
        return (
          <StateGate key={themeId} enabled={option.enabled} reason={option.disabledReason} locale={locale}>
            <button
              type="button"
              disabled={!option.enabled || !supported}
              onClick={() => {
                if (supported && option.enabled) {
                  onSelect(themeId);
                }
              }}
              className={`w-full rounded-lg px-3 py-3 text-left text-sm font-semibold transition ${
                selected ? "bg-blue-600 text-white shadow-lg shadow-blue-200" : option.enabled ? "bg-white text-slate-900 hover:bg-blue-50" : "cursor-not-allowed text-slate-400"
              }`}
            >
              {labelText(option.label, locale)}
            </button>
          </StateGate>
        );
      })}
    </div>
  );
}

export function ResultCard({ result, locale }: { result: ResultCardProps; locale: UiLocale }) {
  return (
    <div className="space-y-5">
      <TrustBar trust={result.trust} />
      <div className="overflow-hidden rounded-3xl border border-blue-100 bg-gradient-to-br from-white via-blue-50/70 to-amber-50/40 p-5 sm:p-7">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="text-xs font-semibold uppercase tracking-[0.24em] text-blue-700">Verified Result</div>
            <div className="mt-3 space-y-2">
              {result.summary.items.map((item) => (
                <div key={item.key}>
                  <div className="text-sm font-semibold text-blue-700">{labelText(item.label, locale)}</div>
                  <div className={`break-safe text-4xl font-semibold tracking-[-0.05em] ${valueClass(item.value)}`}>{item.value}</div>
                </div>
              ))}
            </div>
          </div>
          <div className="relative flex min-h-32 flex-1 items-end justify-end overflow-hidden rounded-3xl bg-white/60 p-5">
            <div className="absolute bottom-5 right-6 h-20 w-44 rounded-[50%] bg-blue-200/60 blur-2xl" />
            <div className="absolute bottom-8 right-12 h-12 w-28 rounded-[50%] bg-amber-200/70 blur-xl" />
            <div className="relative flex h-24 w-24 items-center justify-center rounded-3xl bg-blue-600 text-white shadow-xl shadow-blue-200">
              <Activity className="h-10 w-10" aria-hidden="true" />
            </div>
          </div>
        </div>
        <div className="mt-5 flex flex-wrap gap-2">
          {[...(result.uncertainty ?? []), ...(result.risk ?? [])].map((signal) => (
            <SignalTag key={`${signal.label.en}-${signal.value}`} signal={signal} locale={locale} />
          ))}
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          {result.actions.map((action) => (
            <button
              key={action.type}
              type="button"
              disabled={!action.enabled}
              className={`flex items-center justify-center gap-2 rounded-xl px-4 py-3 text-sm font-semibold transition ${
                action.enabled
                  ? action.type === "feedback"
                    ? "bg-blue-600 text-white shadow-lg shadow-blue-200 hover:bg-blue-700"
                    : "border border-blue-300 bg-white text-blue-700 hover:bg-blue-50"
                  : "cursor-not-allowed border border-slate-200 bg-slate-50 text-slate-400"
              }`}
            >
              {action.type === "feedback" ? <ThumbsUp className="h-4 w-4" /> : null}
              {action.type === "replay" ? <Play className="h-4 w-4" /> : null}
              {action.type === "ask_followup" ? <MessageSquareText className="h-4 w-4" /> : null}
              {action.type.replace("_", " ")}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

export function EvidenceCardList({ evidenceList, locale }: { evidenceList: EvidenceCardListProps; locale: UiLocale }) {
  const [expanded, setExpanded] = useState(false);
  const visibleCount = evidenceList.visibleCount ?? 2;
  const cards = expanded ? evidenceList.evidence : evidenceList.evidence.slice(0, visibleCount);

  return (
    <div className="space-y-4">
      <div className="grid gap-3 xl:grid-cols-2">
        {cards.map((card) => (
          <EvidenceItem key={card.evidenceId} card={card} locale={locale} />
        ))}
      </div>
      {evidenceList.expandable && evidenceList.evidence.length > visibleCount ? (
        <button
          type="button"
          onClick={() => setExpanded((value) => !value)}
          className="w-full rounded-xl border border-blue-200 bg-white px-4 py-3 text-sm font-semibold text-blue-700 hover:bg-blue-50"
        >
          {expanded ? "Collapse evidence" : `View all evidence (${evidenceList.evidence.length})`}
        </button>
      ) : null}
    </div>
  );
}

function EvidenceItem({ card, locale }: { card: EvidenceCard; locale: UiLocale }) {
  const [open, setOpen] = useState(false);

  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm shadow-slate-100">
      <div className="flex flex-wrap items-center gap-2">
        <span className="rounded-full bg-blue-50 px-2 py-1 text-[0.68rem] font-semibold uppercase tracking-[0.15em] text-blue-700">
          {card.strength ?? "signal"}
        </span>
        <span className="rounded-full bg-emerald-50 px-2 py-1 text-[0.68rem] font-semibold text-emerald-700">
          {card.verifierStatus ?? "unknown"}
        </span>
      </div>
      <h3 className="mt-3 text-base font-semibold text-slate-950">{labelText(card.label, locale)}</h3>
      <p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-600">{labelText(card.detail, locale)}</p>
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="mt-3 flex items-center gap-1 text-sm font-semibold text-blue-700"
        aria-expanded={open}
      >
        Details
        <ChevronDown className={`h-4 w-4 transition ${open ? "rotate-180" : ""}`} />
      </button>
      {open ? (
        <div className="mt-3 space-y-2 border-t border-slate-100 pt-3 text-xs leading-5 text-slate-500">
          {card.sources.map((source) => (
            <div key={`${source.sourceType}-${source.sourceKey}`} className="break-safe rounded-lg bg-slate-50 px-3 py-2">
              {sourceText(source)}
            </div>
          ))}
        </div>
      ) : null}
    </article>
  );
}

export function FeedbackPanel({ feedback }: { feedback: FeedbackPanelProps }) {
  return (
    <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-5">
      {feedback.allowedValues.map((value) => (
        <button
          key={value}
          type="button"
          className="rounded-xl border border-emerald-200 bg-white px-3 py-3 text-sm font-semibold text-emerald-800 hover:bg-emerald-50"
        >
          {value.replaceAll("_", " ")}
        </button>
      ))}
    </div>
  );
}

export function ReplayCard({ replay, locale }: { replay: ReplayCardProps; locale: UiLocale }) {
  return (
    <div className="space-y-4">
      <div className="grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 sm:grid-cols-3">
        <ReplayFact label="Prediction ID" value={replay.predictionId} />
        <ReplayFact label="Contract Hash" value={replay.contractHash} />
        <ReplayFact label="Verifier Status" value={replay.verifierStatus} />
      </div>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {replay.anchors.map((anchor) => (
          <div key={`${anchor.label.en}-${anchor.value}`} className="rounded-xl border border-slate-200 bg-white p-3">
            <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{labelText(anchor.label, locale)}</div>
            <div className="break-safe mt-2 text-sm font-semibold text-slate-950">{anchor.value}</div>
          </div>
        ))}
      </div>
      {replay.publicSafe ? (
        <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-center text-sm text-slate-500">
          This result is replayable and verifiable. Redacted for privacy.
        </div>
      ) : null}
    </div>
  );
}

function ReplayFact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</div>
      <div className="break-safe mt-1 text-sm font-semibold text-slate-950">{value}</div>
    </div>
  );
}

export function MobileUserNav() {
  const items = [
    { icon: Home, label: "Home" },
    { icon: RotateCcw, label: "History" },
    { icon: FileSearch, label: "Replay" },
    { icon: CircleUserRound, label: "Profile" },
  ];

  return (
    <nav className="mx-auto mt-4 w-full max-w-md rounded-3xl border border-slate-200 bg-white/95 px-3 py-2 shadow-xl shadow-slate-300/40 backdrop-blur xl:hidden">
      <div className="grid grid-cols-4 gap-1">
        {items.map((item, index) => {
          const Icon = item.icon;
          return (
            <button
              key={item.label}
              type="button"
              className={`flex flex-col items-center justify-center rounded-2xl px-2 py-2 text-xs font-semibold ${
                index === 0 ? "bg-blue-50 text-blue-700" : "text-slate-500"
              }`}
            >
              <Icon className="mb-1 h-4 w-4" aria-hidden="true" />
              {item.label}
            </button>
          );
        })}
      </div>
    </nav>
  );
}
