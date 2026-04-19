"use client";

import { classicalPatternCatalog, summarizeClassicalPatternCatalog, type ClassicalPatternStatus } from "@/types/classicalPatternCatalog";

function patternStatusTone(status: ClassicalPatternStatus): string {
  if (status === "implemented") return "border-emerald-500/25 bg-emerald-950/35 text-emerald-100";
  if (status === "partial") return "border-amber-500/25 bg-amber-950/35 text-amber-100";
  return "border-zinc-500/20 bg-zinc-900/70 text-zinc-300";
}

export function V17_ClassicalPatternAtlas({
  title = "Classical Pattern Atlas",
  subtitle = "古典格局全集目录、定义条件与系统挂接状态",
  compact = false,
}: {
  title?: string;
  subtitle?: string;
  compact?: boolean;
}) {
  const patternCatalogSummary = summarizeClassicalPatternCatalog();
  const patternFamilies = Object.entries(patternCatalogSummary.familyCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, compact ? 6 : 8);
  const highlightedPatterns = compact ? classicalPatternCatalog.slice(0, 12) : classicalPatternCatalog;

  return (
    <div className="rounded-xl border border-cyan-500/20 bg-[linear-gradient(180deg,rgba(8,47,73,0.35),rgba(9,9,11,0.72))] p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="text-[10px] uppercase tracking-[0.22em] text-cyan-300">{title}</p>
          <p className="mt-1 text-sm text-cyan-50">{subtitle}</p>
        </div>
        <div className="flex flex-wrap gap-1.5 text-[10px]">
          <span className="rounded-full border border-cyan-500/20 bg-zinc-950/60 px-2 py-1 text-cyan-100">总计 {patternCatalogSummary.total}</span>
          <span className="rounded-full border border-emerald-500/20 bg-zinc-950/60 px-2 py-1 text-emerald-100">已实现 {patternCatalogSummary.implemented}</span>
          <span className="rounded-full border border-amber-500/20 bg-zinc-950/60 px-2 py-1 text-amber-100">部分实现 {patternCatalogSummary.partial}</span>
          <span className="rounded-full border border-zinc-500/20 bg-zinc-950/60 px-2 py-1 text-zinc-300">待补齐 {patternCatalogSummary.planned}</span>
        </div>
      </div>

      <div className="mt-3 grid gap-3 xl:grid-cols-[0.8fr_1.2fr]">
        <div className="rounded-xl border border-cyan-500/15 bg-zinc-950/55 p-2.5">
          <p className="text-[10px] uppercase tracking-[0.18em] text-cyan-300">Family Coverage</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            {patternFamilies.map(([family, count]) => (
              <span
                key={`pattern_family_${family}`}
                className="rounded-full border border-cyan-500/20 bg-zinc-900/60 px-2 py-1 text-[10px] text-cyan-100"
              >
                {family} {count}
              </span>
            ))}
          </div>
          <p className="mt-3 text-[10px] leading-relaxed text-zinc-400">
            这张表现在展示的是 L2 古典格局全集与工程挂接状态。当前 35 条目录都已经有候选入口，
            但仍属于观察型格局层，不会直接改写十神物理值。
          </p>
        </div>

        <div className="rounded-xl border border-cyan-500/15 bg-zinc-950/55 p-2.5">
          <p className="text-[10px] uppercase tracking-[0.18em] text-cyan-300">Pattern Catalog</p>
          <div className="mt-2 grid gap-2 md:grid-cols-2">
            {highlightedPatterns.map((item) => (
              <div key={item.id} className="rounded-lg border border-zinc-800 bg-zinc-900/55 p-2">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-[11px] text-cyan-50">{item.name}</p>
                    <p className="text-[9px] text-zinc-500">{item.family}</p>
                  </div>
                  <span className={`rounded-full border px-1.5 py-0.5 text-[9px] ${patternStatusTone(item.status)}`}>
                    {item.status === "implemented" ? "已实现" : item.status === "partial" ? "部分实现" : "待实现"}
                  </span>
                </div>
                <p className="mt-1 text-[10px] leading-relaxed text-zinc-300">{item.definition}</p>
                <p className="mt-1 text-[9px] text-emerald-200/85">
                  成格：{item.conditions.slice(0, 2).join("；")}
                </p>
                <p className="mt-1 text-[9px] text-rose-200/80">
                  破格：{item.breakers.slice(0, 2).join("；")}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
