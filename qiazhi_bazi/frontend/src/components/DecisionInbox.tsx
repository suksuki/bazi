"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import { detectElementFromText, elementColorClass } from "@/constants/termMap";

type Card = {
  id: string;
  title: string;
  markdown: string;
  conflictDetail?: string;
  displayText?: string;
};

type Props = {
  cards: Card[];
  resultLogs: string[];
  highlightVerdict?: boolean;
  onExecuteDecision: (selected: Card[]) => Promise<void>;
  t?: (s: string) => string;
};

export function DecisionInbox({ cards, resultLogs, highlightVerdict = false, onExecuteDecision, t = (s) => s }: Props) {
  const [selectedIds, setSelectedIds] = useState<Record<string, boolean>>({});
  const [executing, setExecuting] = useState(false);

  const selectedCards = cards.filter((c) => selectedIds[c.id]);

  useEffect(() => {
    setSelectedIds({});
  }, [cards]);

  async function execute() {
    setExecuting(true);
    try {
      await onExecuteDecision(selectedCards);
    } finally {
      setExecuting(false);
    }
  }

  return (
    <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-medium">{t("Decision Inbox")}</h3>
        <span className="text-xs text-zinc-500">{t("流式对话与决策卡片")}</span>
      </div>

      <div className="space-y-3">
        <AnimatePresence initial={false}>
          <motion.article
            key="checklist"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-xl border border-zinc-800 bg-zinc-950 p-3"
          >
            <h4 className="text-sm font-medium text-zinc-100">{t("Atomic Conflicts Checklist")}</h4>
            <p className="mt-1 text-xs text-zinc-400">{t("批量勾选后，一次性执行全局裁决。")}</p>
            <div className="mt-3 space-y-2">
              {cards.length === 0 ? <p className="text-xs text-zinc-500">{t("暂无可裁决冲合项。")}</p> : null}
              {cards.map((card) => (
                (() => {
                  const labelText = card.displayText ?? card.conflictDetail ?? card.title;
                  const element = detectElementFromText(labelText);
                  return (
                <label
                  key={card.id}
                  className={`flex items-center justify-between gap-3 rounded-lg border px-3 py-2 text-xs ${
                    selectedIds[card.id]
                      ? "border-emerald-500/40 bg-emerald-500/10"
                      : "border-zinc-700 bg-zinc-900"
                  }`}
                >
                  <span className={selectedIds[card.id] ? "text-emerald-200" : "text-zinc-200"}>
                    <span className="mr-2 inline-flex items-center">
                      <span className={`mr-1 inline-block h-2 w-2 rounded-full ${elementColorClass(element)}`} />
                    </span>
                    {labelText}
                  </span>
                  <span className="flex items-center gap-2">
                    {selectedIds[card.id] ? <span className="text-[11px] text-emerald-300">{t("已认同")}</span> : null}
                    <button
                      type="button"
                      aria-label={`勾选 ${card.conflictDetail ?? card.title}`}
                      aria-pressed={Boolean(selectedIds[card.id])}
                      onClick={() =>
                        setSelectedIds((prev) => ({
                          ...prev,
                          [card.id]: !prev[card.id],
                        }))
                      }
                      className={`flex h-5 w-5 items-center justify-center rounded border text-[12px] font-bold ${
                        selectedIds[card.id]
                          ? "border-emerald-400 bg-emerald-500/20 text-emerald-300"
                          : "border-zinc-500 bg-zinc-950 text-transparent"
                      }`}
                    >
                      ✓
                    </button>
                  </span>
                </label>
                  );
                })()
              ))}
            </div>
            <button
              type="button"
              disabled={executing || selectedCards.length === 0}
              onClick={execute}
              className="mt-3 w-full rounded-lg bg-amber-500 px-3 py-2 text-xs font-medium text-zinc-950 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {executing ? t("执行中...") : `${t("执行全局裁决")}（${t("已选")} ${selectedCards.length} ${t("项")}）`}
            </button>
          </motion.article>
        </AnimatePresence>
      </div>

      <section
        className={`mt-4 rounded-xl bg-zinc-950 p-3 ${
          highlightVerdict ? "border-2 border-amber-400/70 shadow-[0_0_18px_rgba(251,191,36,0.25)]" : "border border-zinc-800"
        }`}
      >
        <h4 className="text-sm font-semibold text-zinc-200">{t("Result Summary")}</h4>
        <div className="mt-2 space-y-1">
          {resultLogs.length === 0 ? <p className="text-xs text-zinc-500">{t("等待确认后生成阶段结论…")}</p> : null}
          {resultLogs.map((x, i) => (
            <p
              key={`${i}-${x.slice(0, 12)}`}
              className={`whitespace-pre-wrap leading-relaxed text-emerald-300 ${
                highlightVerdict ? "text-[1.2rem] font-semibold" : "text-sm"
              }`}
            >
              {x}
            </p>
          ))}
        </div>
      </section>
    </section>
  );
}
