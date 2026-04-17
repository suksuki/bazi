"use client";

import { useMemo } from "react";
import { buildDecisionTimelineEvents, type DecisionTimelineEvent, type TimelineTier } from "./decisionTimelineModel";

const TIER_RING: Record<TimelineTier, string> = {
  physics: "border-sky-500/50 bg-sky-950/35 text-sky-100",
  plugin: "border-emerald-500/45 bg-emerald-950/30 text-emerald-100",
  router: "border-amber-500/50 bg-amber-950/30 text-amber-100",
  llm: "border-violet-500/45 bg-violet-950/30 text-violet-100",
  verdict: "border-fuchsia-500/45 bg-fuchsia-950/30 text-fuchsia-100",
  hub: "border-zinc-500/40 bg-zinc-900/50 text-zinc-200",
};

type Props = {
  snapshot: Record<string, unknown> | null;
};

export function DecisionTimeline({ snapshot }: Props) {
  const events = useMemo(() => buildDecisionTimelineEvents(snapshot), [snapshot]);

  if (events.length === 0) {
    return (
      <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-4 text-xs text-zinc-500">
        暂无决策时序数据。完成排盘或静默重算后，将在此串联物理 → 插件 → 路由 → LLM → 终审。
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3">
      <p className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">全链路决策时序</p>
      <p className="mt-1 text-[11px] leading-relaxed text-zinc-500">
        物理检出 · 插件介入 · CausalRouter 仲裁 · LLM 装配 · 终审断言（指令 token 已译为行为描述）。
      </p>
      <ol className="relative mt-4 border-l border-zinc-800 pl-4">
        {events.map((e: DecisionTimelineEvent) => (
          <li key={e.id} className="relative mb-5 last:mb-0">
            <span
              className={`absolute -left-[7px] mt-0.5 h-3 w-3 rounded-full border-2 border-zinc-950 ${
                e.tier === "router"
                  ? "bg-amber-400"
                  : e.tier === "llm"
                    ? "bg-violet-400"
                    : e.tier === "verdict"
                      ? "bg-fuchsia-400"
                      : e.tier === "plugin"
                        ? "bg-emerald-400"
                        : e.tier === "hub"
                          ? "bg-zinc-500"
                          : "bg-sky-400"
              }`}
            />
            <div className="flex flex-wrap items-baseline gap-2">
              <span className="font-mono text-[10px] text-zinc-500">{e.tsLabel}</span>
              <span className={`rounded border px-1.5 py-0 text-[9px] font-medium ${TIER_RING[e.tier]}`}>{e.titleZh}</span>
            </div>
            <p className="mt-1 text-[12px] font-medium leading-snug text-zinc-100">{e.bodyZh}</p>
            <details className="mt-1">
              <summary className="cursor-pointer text-[10px] text-zinc-500">原始信号</summary>
              <pre className="mt-1 max-h-28 overflow-auto whitespace-pre-wrap break-all rounded border border-zinc-800/80 bg-zinc-950/80 p-2 font-mono text-[9px] text-zinc-500">
                {e.raw}
              </pre>
            </details>
          </li>
        ))}
      </ol>
    </div>
  );
}
