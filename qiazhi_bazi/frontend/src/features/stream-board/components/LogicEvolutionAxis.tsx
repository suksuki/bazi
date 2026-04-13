"use client";

import { useMemo, useState } from "react";
import type { DecisionJournalEntry } from "@/features/stream-board/decisionJournal";
import { useLabStore } from "@/features/stream-board/stores/useLabStore";
import type { LabLlmRoundEntry } from "@/features/stream-board/controller/labLlmRounds";
import { extractLlmRoundDiagnosisText } from "@/features/stream-board/components/logicEvolutionAxisExtract";

export type LogicEvolutionAxisProps = {
  resultLogs: string[];
  decisionJournal: DecisionJournalEntry[];
  /** 与 BaziMetadata.history_context.learning_annotation.entries 对齐，中枢 / 终判等追加的叙事审计行 */
  metadata?: Record<string, unknown>;
  /** 中枢 SSE `audit_pulse` 拼接的因果路由备忘（流式刷新） */
  liveCausalPulse?: string | null;
  t: (s: string) => string;
};

type AxisEv = {
  id: string;
  side: "system" | "user";
  preview: string;
  full: string;
};

/** 主界面「因果堆叠」时间轴：多轮 LLM 摘要 + 审计日志 + 抑制/勾选意志（可点击展开全文） */
export function LogicEvolutionAxis({
  resultLogs,
  decisionJournal,
  metadata = {},
  liveCausalPulse = null,
  t,
}: LogicEvolutionAxisProps) {
  const { state: labState } = useLabStore();
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const events = useMemo(() => {
    const out: AxisEv[] = [];
    const pulse = String(liveCausalPulse || "").trim();
    if (pulse) {
      out.push({
        id: "orch-causal-pulse",
        side: "system",
        preview: `${t("审计备忘")} · ${pulse.slice(0, 140)}${pulse.length > 140 ? "…" : ""}`,
        full: `${t("审计备忘")}（因果路由）\n\n${pulse}`,
      });
    }
    const rounds = Array.isArray(labState.snapshot?.llm_rounds)
      ? ([...(labState.snapshot!.llm_rounds as LabLlmRoundEntry[])] as LabLlmRoundEntry[])
      : [];
    rounds.sort((a, b) => (a.at || 0) - (b.at || 0));
    rounds.forEach((r) => {
      const full = extractLlmRoundDiagnosisText(r).trim();
      if (!full) return;
      const head = String(r.title_zh || r.scenario || "LLM").trim();
      out.push({
        id: `round-${r.id}`,
        side: "system",
        preview: `${head} · ${full.slice(0, 140)}${full.length > 140 ? "…" : ""}`,
        full: `${head}\n\n${full}`,
      });
    });

    const hc = metadata?.history_context as { learning_annotation?: { entries?: unknown[] } } | undefined;
    const la = hc?.learning_annotation;
    const laEntries: unknown[] = Array.isArray(la?.entries) ? la.entries : [];
    laEntries.forEach((raw, i) => {
      if (!raw || typeof raw !== "object" || Array.isArray(raw)) return;
      const e = raw as { kind?: unknown; reason?: unknown; trigger?: unknown };
      const parts = [e.kind, e.reason, e.trigger]
        .map((x) => (typeof x === "string" ? x.trim() : ""))
        .filter(Boolean);
      const full = parts.join(" · ");
      if (!full) return;
      out.push({
        id: `hc-${i}-${full.slice(0, 20)}`,
        side: "system",
        preview: full.slice(0, 180) + (full.length > 180 ? "…" : ""),
        full,
      });
    });

    resultLogs.forEach((raw, i) => {
      const line = String(raw || "").trim();
      if (!line) return;
      if (
        /\[SYS\]\[WILL\]|\[PHYSICS_AUDIT\]|\[LLM_AUDIT\]|\[SILENT_ANALYZE\]|终审|orchestrator|internal-loop|审计|提案|语义整合|首观/i.test(
          line,
        )
      ) {
        const full = line.trim();
        out.push({
          id: `log-${i}`,
          side: "system",
          preview: full.slice(0, 180) + (full.length > 180 ? "…" : ""),
          full,
        });
      }
    });

    decisionJournal.forEach((e, i) => {
      const id = e.inbox_card_id || e.branch_set_key || `j-${i}`;
      const action = String(e.action || "journal");
      const full = `${action}${e.branch_set_key ? ` · ${e.branch_set_key}` : ""}${e.inbox_card_id ? ` · ${e.inbox_card_id}` : ""}`;
      out.push({
        id: `jr-${id}-${e.ts}`,
        side: "user",
        preview: full.slice(0, 180) + (full.length > 180 ? "…" : ""),
        full,
      });
    });
    return out.slice(-48);
  }, [resultLogs, decisionJournal, metadata, labState.snapshot?.llm_rounds, liveCausalPulse, t]);

  if (events.length === 0) {
    return (
      <div className="rounded-lg border border-zinc-800/80 bg-zinc-950/50 px-2 py-2 text-[10px] text-zinc-600">
        {t("逻辑演化轴：尚无审计或意志记录；勾选 Inbox 或触发静默环后将在此堆叠。")}
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-cyan-900/35 bg-gradient-to-b from-zinc-950/90 to-black/40 px-2 py-2">
      <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-wide text-cyan-200/90">{t("逻辑演化轴")}</p>
      <p className="mb-1 text-[9px] text-zinc-500">{t("点击条目展开本轮完整 diagnosis / 模型输出")}</p>
      <ul className="max-h-52 space-y-1.5 overflow-y-auto pr-1 text-[10px] leading-snug">
        {events.map((ev) => {
          const open = expandedId === ev.id;
          return (
            <li
              key={ev.id}
              className={`rounded-md border ${
                ev.side === "system"
                  ? "border-zinc-700/80 bg-zinc-900/60 text-zinc-300"
                  : "border-emerald-800/50 bg-emerald-950/25 text-emerald-100/90"
              }`}
            >
              <button
                type="button"
                className="flex w-full gap-2 px-2 py-1 text-left hover:bg-white/5"
                onClick={() => setExpandedId((cur) => (cur === ev.id ? null : ev.id))}
                aria-expanded={open}
              >
                <span className="shrink-0 font-mono text-[8px] text-zinc-600">
                  {ev.side === "system" ? "SYS" : t("用户决策")}
                </span>
                <span className="min-w-0 flex-1 break-words">{open ? ev.full : ev.preview}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
