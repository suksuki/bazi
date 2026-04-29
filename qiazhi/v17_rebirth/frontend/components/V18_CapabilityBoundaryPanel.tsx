"use client";

import type { ReactNode } from "react";

import type { AppLanguage } from "@/lib/i18n";

export type CapabilityBoundary = {
  capabilityBoundary: boolean;
  message?: string;
  supportedScopes: string[];
  unsupportedScopes: string[];
  suggestedQueries: string[];
  detectedTopic?: string;
};

type CapabilityBoundaryCopy = {
  title: string;
  intro: string;
  canAnswer: string;
  notSupported: string;
  tryAsking: string;
  rewriteQuestion: string;
  helper: string;
  supportedScopes: string[];
  unsupportedScopes: string[];
  suggestedQueries: string[];
};

const COPY: Record<AppLanguage, CapabilityBoundaryCopy> = {
  zh: {
    title: "当前系统能力（Beta）",
    intro: "这个问题目前不在系统的可验证规则范围内。不是你问错了，而是系统会先说明自己能可靠回答什么。",
    canAnswer: "我可以回答",
    notSupported: "暂未覆盖",
    tryAsking: "建议提问",
    rewriteQuestion: "改写并提问",
    helper: "系统只会在可验证规则范围内生成预测；进入支持范围后，才会展示 Prediction Summary 与解释。",
    supportedScopes: ["财运趋势", "收入稳定性", "财富风险与机会"],
    unsupportedScopes: ["命盘结构解析", "感情 / 婚姻", "健康 / 家庭"],
    suggestedQueries: ["我这两年财运如何？", "收入是否稳定？", "有没有明显风险？"],
  },
  en: {
    title: "Current capabilities (Beta)",
    intro: "This question is outside the system's verifiable rule scope. You did not ask it wrong; the system is making its boundary clear first.",
    canAnswer: "I can answer",
    notSupported: "Not yet supported",
    tryAsking: "Try asking",
    rewriteQuestion: "Rewrite and ask",
    helper: "Predictions are only generated inside the verifiable rule scope. Prediction Summary and explanation appear after the question is supported.",
    supportedScopes: ["Wealth trend", "Income stability", "Risk & opportunity"],
    unsupportedScopes: ["Full chart interpretation", "Relationships", "Health"],
    suggestedQueries: ["How is my financial outlook in the next 2 years?", "Will my income be stable?", "Is there any obvious investment or cash-flow risk?"],
  },
  ko: {
    title: "현재 시스템 지원 범위 (Beta)",
    intro: "이 질문은 현재 검증 가능한 규칙 범위 밖에 있습니다. 질문이 틀린 것이 아니라, 시스템이 먼저 답변 가능한 범위를 설명합니다.",
    canAnswer: "다음 질문에 답할 수 있습니다",
    notSupported: "아직 지원하지 않음",
    tryAsking: "추천 질문",
    rewriteQuestion: "바꿔서 질문하기",
    helper: "검증 가능한 규칙 범위 안에서만 예측을 생성합니다. 지원 범위에 들어오면 Prediction Summary와 설명이 표시됩니다.",
    supportedScopes: ["재물 흐름", "수입 안정성", "기회와 리스크"],
    unsupportedScopes: ["전체 명식 해석", "연애/결혼", "건강"],
    suggestedQueries: ["앞으로 2년 재물운은 어떤가요?", "수입은 안정적일까요?", "투자나 현금흐름 리스크가 있나요?"],
  },
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
}

function readBool(source: unknown, key: string): boolean {
  if (!isRecord(source)) return false;
  return source[key] === true;
}

function readString(source: unknown, keys: string[], fallback = ""): string {
  if (!isRecord(source)) return fallback;
  for (const key of keys) {
    const value = source[key];
    if (typeof value === "string" && value.trim()) return value.trim();
  }
  return fallback;
}

function readStringArray(source: unknown, keys: string[]): string[] {
  if (!isRecord(source)) return [];
  for (const key of keys) {
    const value = source[key];
    if (!Array.isArray(value)) continue;
    return value.map((item) => String(item || "").trim()).filter(Boolean);
  }
  return [];
}

export function capabilityBoundaryFromSafeOutput(source: unknown): CapabilityBoundary | null {
  const isBoundary =
    readString(source, ["type"]) === "capability_boundary" ||
    readBool(source, "capability_boundary") ||
    readBool(source, "capabilityBoundary");
  if (!isBoundary) return null;
  return {
    capabilityBoundary: true,
    message: readString(source, ["message", "text"]),
    supportedScopes: readStringArray(source, ["supported_scopes", "supportedScopes"]),
    unsupportedScopes: readStringArray(source, ["unsupported_scopes", "unsupportedScopes"]),
    suggestedQueries: readStringArray(source, ["suggested_queries", "suggestedQueries"]),
    detectedTopic: readString(source, ["detected_topic", "detectedTopic"]),
  };
}

export function CapabilityBoundaryPanel({
  boundary,
  className = "",
  language = "zh",
  onTryQuery,
}: {
  boundary?: CapabilityBoundary | null;
  className?: string;
  language?: AppLanguage;
  onTryQuery?: (query: string) => void;
}): ReactNode {
  const text = COPY[language] || COPY.zh;
  const supported = language === "zh" && boundary?.supportedScopes.length ? boundary.supportedScopes : text.supportedScopes;
  const unsupported = language === "zh" && boundary?.unsupportedScopes.length ? boundary.unsupportedScopes : text.unsupportedScopes;
  const suggested = language === "zh" && boundary?.suggestedQueries.length ? boundary.suggestedQueries : text.suggestedQueries;

  return (
    <section className={`rounded-[1.5rem] border border-amber-300/25 bg-amber-300/[0.08] p-4 shadow-2xl shadow-black/20 backdrop-blur sm:rounded-[2rem] sm:p-5 ${className}`}>
      <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-amber-100/80">Capability Boundary</p>
          <h2 className="mt-2 text-2xl font-semibold text-white">{text.title}</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-amber-50/90">{boundary?.message && language === "zh" ? boundary.message : text.intro}</p>
        </div>
        {boundary?.detectedTopic ? (
          <span className="rounded-full border border-amber-100/20 bg-black/20 px-3 py-1.5 text-xs text-amber-50">
            detected: {boundary.detectedTopic}
          </span>
        ) : null}
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <CapabilityList title={text.canAnswer} marker="✔" tone="supported" items={supported} />
        <CapabilityList title={text.notSupported} marker="✖" tone="unsupported" items={unsupported} />
      </div>

      <div className="mt-5 rounded-2xl border border-white/10 bg-black/20 p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <p className="text-sm font-semibold text-white">{text.tryAsking}</p>
          {onTryQuery && suggested[0] ? (
            <button
              type="button"
              onClick={() => onTryQuery(suggested[0])}
              className="rounded-full bg-cyan-300 px-3 py-1.5 text-xs font-semibold text-slate-950 transition hover:bg-cyan-200"
            >
              {text.rewriteQuestion}
            </button>
          ) : null}
        </div>
        <div className="flex snap-x gap-2 overflow-x-auto pb-2 [-ms-overflow-style:none] [scrollbar-width:none] sm:flex-wrap sm:overflow-visible sm:pb-0 [&::-webkit-scrollbar]:hidden">
          {suggested.map((query) => (
            <button
              key={query}
              type="button"
              onClick={() => onTryQuery?.(query)}
              className="rounded-full border border-cyan-200/20 bg-cyan-200/10 px-3 py-1.5 text-xs text-cyan-50 transition hover:bg-cyan-200/15"
            >
              {query}
            </button>
          ))}
        </div>
        <p className="mt-4 text-xs leading-5 text-slate-400">{text.helper}</p>
      </div>
    </section>
  );
}

function CapabilityList({
  items,
  marker,
  title,
  tone,
}: {
  items: string[];
  marker: string;
  title: string;
  tone: "supported" | "unsupported";
}): ReactNode {
  const markerClass = tone === "supported" ? "text-emerald-200" : "text-rose-200";
  return (
    <article className="rounded-2xl border border-white/10 bg-black/20 p-4">
      <h3 className="mb-3 text-sm font-semibold text-white">{title}</h3>
      <ul className="space-y-2 text-sm text-slate-200">
        {items.map((item) => (
          <li key={item} className="flex items-start gap-2">
            <span className={`mt-0.5 ${markerClass}`}>{marker}</span>
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </article>
  );
}
