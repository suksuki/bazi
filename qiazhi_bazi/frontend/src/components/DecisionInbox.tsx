"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import { elementColorClass } from "@/constants/termMap";
import { DecisionInboxCard, VerdictChangeLog } from "@/features/decision-inbox/types";
import {
  getCardElement,
  getCardLabel,
  getEvidenceTone,
  isAuditorProposal,
  isVerdictDeity,
  pruneSelectedIds,
  splitVerdictLine,
} from "@/features/decision-inbox/utils";

type Props = {
  cards: DecisionInboxCard[];
  resultLogs: string[];
  verdictBody?: string;
  verdictChangeLog?: VerdictChangeLog;
  logicalEvidence?: string[];
  workVector?: Record<string, unknown>;
  highlightVerdict?: boolean;
  onExecuteDecision: (selected: DecisionInboxCard[]) => Promise<void>;
  onVerdictDeityClick?: (deity: string) => void;
  onEvidenceClick?: (evidence: string) => void;
  onShowVersionHistory?: () => void;
  hasVerdictHistory?: boolean;
  selectionResetToken?: number;
  summaryVersionLabel?: string;
  summaryChanged?: boolean;
  l1Certified?: boolean;
  t?: (s: string) => string;
};

export function DecisionInbox({
  cards,
  resultLogs,
  verdictBody = "",
  verdictChangeLog = {},
  logicalEvidence = [],
  workVector = {},
  highlightVerdict = false,
  onExecuteDecision,
  onVerdictDeityClick,
  onEvidenceClick,
  onShowVersionHistory,
  hasVerdictHistory = false,
  selectionResetToken = 0,
  summaryVersionLabel,
  summaryChanged = false,
  l1Certified = false,
  t = (s) => s,
}: Props) {
  const [selectedIds, setSelectedIds] = useState<Record<string, boolean>>({});
  const [executing, setExecuting] = useState(false);
  const [evidenceOpen, setEvidenceOpen] = useState(false);

  const selectedCards = cards.filter((c) => selectedIds[c.id]);

  useEffect(() => {
    // 卡片内容可能因翻译或流式更新变化；仅移除不存在的 id，避免勾选被瞬间清空。
    setSelectedIds((prev) => pruneSelectedIds(prev, cards.map((card) => card.id)));
  }, [cards]);

  useEffect(() => {
    setSelectedIds({});
  }, [selectionResetToken]);

  async function execute() {
    setExecuting(true);
    try {
      await onExecuteDecision(selectedCards);
    } finally {
      setExecuting(false);
    }
  }

  function renderVerdictLine(line: string, idx: number) {
    const parts = splitVerdictLine(line);
    return (
      <p
        key={`${idx}-${line.slice(0, 12)}`}
        className={`whitespace-pre-wrap leading-relaxed ${
          summaryChanged
            ? "rounded-md bg-gradient-to-r from-amber-500/10 via-emerald-500/5 to-transparent px-2 py-1 text-emerald-200"
            : "text-emerald-300"
        } ${
          highlightVerdict ? "text-[1.2rem] font-semibold" : "text-sm"
        }`}
      >
        {parts.map((part, i) => (
          isVerdictDeity(part) ? (
            <button
              key={`${idx}-${i}-${part}`}
              type="button"
              onClick={() => onVerdictDeityClick?.(part)}
              className="mx-[1px] rounded border border-sky-500/30 bg-sky-500/10 px-1 text-sky-200 hover:bg-sky-500/20"
              title={`查看 ${part} 的演算路径`}
            >
              {part}
            </button>
          ) : (
            <span key={`${idx}-${i}`}>{part}</span>
          )
        ))}
      </p>
    );
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
              <AnimatePresence initial={false}>
              {cards.map((card) => (
                (() => {
                  const labelText = getCardLabel(card);
                  const element = getCardElement(card);
                  const isProposal = isAuditorProposal(card.cardType);
                  return (
                <motion.label
                  key={card.id}
                  initial={{ opacity: 0, x: 18 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -100 }}
                  transition={{ duration: 0.22 }}
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
                    {isProposal ? (
                      <span className="ml-2 rounded-md border border-violet-500/40 bg-violet-500/10 px-2 py-0.5 text-[10px] text-violet-300">
                        [Auditor 提案]
                      </span>
                    ) : null}
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
                </motion.label>
                  );
                })()
              ))}
              </AnimatePresence>
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
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-zinc-200">{t("Result Summary")}</h4>
          <div className="flex items-center gap-2">
            {hasVerdictHistory ? (
              <button
                type="button"
                onClick={() => onShowVersionHistory?.()}
                className="rounded-md border border-zinc-700 bg-zinc-900 px-2 py-0.5 text-[10px] text-zinc-300 hover:bg-zinc-800"
              >
                查看历史版本
              </button>
            ) : null}
            {summaryVersionLabel ? (
              <span className="rounded-md border border-zinc-700 bg-zinc-900 px-2 py-0.5 text-[10px] text-zinc-400">
                {summaryVersionLabel}
              </span>
            ) : null}
          </div>
        </div>
        <div className="mt-2 space-y-1">
          {l1Certified ? (
            <div className="mb-2 inline-flex items-center rounded-md border border-emerald-500/40 bg-emerald-500/10 px-2 py-0.5 text-[10px] text-emerald-300">
              L1 Certified
            </div>
          ) : null}
          {!verdictBody && resultLogs.length === 0 ? <p className="text-xs text-zinc-500">{t("等待确认后生成阶段结论…")}</p> : null}
          {verdictBody
            ? verdictBody.split("\n").map((x, i) => renderVerdictLine(x, i))
            : resultLogs.map((x, i) => renderVerdictLine(x, i))}
          {(verdictChangeLog.physics_diff?.length || verdictChangeLog.consensus_diff?.length || verdictChangeLog.text_diff_hint) ? (
            <div className="mt-2 rounded-md border border-zinc-700 bg-zinc-900 p-2 text-[11px]">
              <div className="grid grid-cols-1 gap-2 md:grid-cols-3">
                <div className="rounded border border-zinc-700 bg-zinc-950 p-2">
                  <p className="mb-1 text-zinc-300">物理场变动</p>
                  {(verdictChangeLog.physics_diff || []).length === 0 ? <p className="text-zinc-500">- 无</p> : null}
                  {(verdictChangeLog.physics_diff || []).map((x, i) => <p key={`pd-${i}`} className="text-zinc-400">- {x}</p>)}
                </div>
                <div className="rounded border border-zinc-700 bg-zinc-950 p-2">
                  <p className="mb-1 text-zinc-300">共识固化</p>
                  {(verdictChangeLog.consensus_diff || []).length === 0 ? <p className="text-zinc-500">- 无</p> : null}
                  {(verdictChangeLog.consensus_diff || []).map((x, i) => <p key={`cd-${i}`} className="text-zinc-400">- {x}</p>)}
                </div>
                <div className="rounded border border-zinc-700 bg-zinc-950 p-2">
                  <p className="mb-1 text-zinc-300">判词修正</p>
                  <p className="text-zinc-400">{verdictChangeLog.text_diff_hint || "无"}</p>
                </div>
              </div>
            </div>
          ) : null}
          {logicalEvidence.length > 0 ? (
            <div className="mt-2 rounded-md border border-zinc-700 bg-zinc-900 p-2 text-[11px]">
              <button
                type="button"
                onClick={() => setEvidenceOpen((v) => !v)}
                className="rounded border border-zinc-700 bg-zinc-950 px-2 py-0.5 text-zinc-300 hover:bg-zinc-800"
              >
                {evidenceOpen ? "收起证据快照" : "展开证据快照"}
              </button>
              {evidenceOpen ? (
                <div className="mt-2 max-h-40 space-y-1 overflow-auto">
                  {logicalEvidence.map((x, i) => (
                    <button
                      key={`ev-${i}`}
                      type="button"
                      onClick={() => onEvidenceClick?.(x)}
                      className={`block w-full rounded border px-2 py-1 text-left hover:border-sky-500/40 hover:text-sky-200 ${getEvidenceTone(x)}`}
                      title="点击下钻证据"
                    >
                      {x}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}
          {Array.isArray((workVector as { work_vectors?: unknown[] })?.work_vectors)
            && ((workVector as { work_vectors?: unknown[] })?.work_vectors || []).length > 0 ? (
              <div className="mt-2 rounded-md border border-zinc-700 bg-zinc-900 p-2 text-[11px]">
                <p className="mb-1 text-zinc-300">盲派做功链路图（L2）</p>
                <div className="space-y-1">
                  {((workVector as { work_vectors?: Array<Record<string, unknown>> }).work_vectors || []).slice(0, 3).map((item, idx) => {
                    const net = Number(item.expected_work ?? 0);
                    const tone = net > 0 ? "text-cyan-300" : (net < 0 ? "text-orange-300" : "text-zinc-300");
                    const trigger = String(item.detail || item.type || "冲");
                    return (
                      <p key={`wv-${idx}`} className={tone}>
                        触发: {trigger}
                        {" -> "}
                        释放: {Number(item.released_energy ?? 0).toFixed(2)}
                        {" -> "}
                        损耗: -{Number(item.backfire_risk ?? 0).toFixed(2)}
                        {" -> "}
                        净值: {net >= 0 ? "+" : ""}{net.toFixed(2)}
                      </p>
                    );
                  })}
                </div>
              </div>
            ) : null}
        </div>
      </section>
    </section>
  );
}
