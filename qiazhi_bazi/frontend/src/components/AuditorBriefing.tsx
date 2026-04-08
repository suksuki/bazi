"use client";

import { LogicProposal } from "@/features/auditor-briefing/types";
import { formatVal, getAuditorBriefingState } from "@/features/auditor-briefing/utils";

type Props = {
  causalReasoning?: string;
  tuningSuggestions?: string[];
  logicProposal?: LogicProposal | null;
  currentParams?: Record<string, number>;
  alignmentScore?: number;
  structuredHit?: boolean;
  repairMode?: string;
  autoConverted?: boolean;
  t?: (s: string) => string;
  alreadyAdded?: boolean;
  onAddToInbox?: (proposal: LogicProposal) => void;
};

export function AuditorBriefing({
  causalReasoning,
  tuningSuggestions = [],
  logicProposal,
  currentParams,
  alignmentScore,
  structuredHit,
  repairMode,
  autoConverted = false,
  t = (s) => s,
  alreadyAdded = false,
  onAddToInbox,
}: Props) {
  if (!logicProposal) return null;
  // 用户手动转入 Decision Inbox 后，临时语义窗口必须消失；
  // 但“自动转法案”需要在气泡中给出可视反馈，因此允许保留（autoConverted=true）。
  if (alreadyAdded && !autoConverted) return null;
  const { key, currentValue, nextValue, hasSqlPatch, aligned, disableByState } = getAuditorBriefingState({
    logicProposal,
    currentParams,
    alignmentScore,
    structuredHit,
    autoConverted,
    alreadyAdded,
  });

  return (
    <section className="rounded-2xl border border-amber-500/35 bg-amber-950/35 p-4 shadow-[0_0_26px_rgba(245,158,11,0.08)]">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-violet-300">{t("审计员简报 (Auditor Briefing)")}</h3>
        {autoConverted ? (
          <span className="rounded-md border border-amber-500/50 bg-amber-500/15 px-2 py-0.5 text-[11px] text-amber-100">
            已自动转化为决策项
          </span>
        ) : aligned ? (
          <span className="rounded-md border border-emerald-500/40 bg-emerald-500/10 px-2 py-0.5 text-[11px] text-emerald-300">
            逻辑已对齐
          </span>
        ) : (
          <span className="rounded-md border border-amber-500/40 bg-amber-500/10 px-2 py-0.5 text-[11px] text-amber-200">
            角色3 -&gt; 角色1裁决
          </span>
        )}
      </div>
      {autoConverted ? (
        <p className="mb-2 text-[11px] leading-relaxed text-amber-100">
          检测到严重物理偏差，已自动生成校准预案供裁决。
        </p>
      ) : null}

      {causalReasoning ? (
        <p className="text-xs leading-relaxed text-amber-100">{causalReasoning}</p>
      ) : null}

      {key ? (
        <div className="mt-3 rounded-xl border border-amber-500/25 bg-zinc-950 p-3">
          <div className="flex items-center justify-between gap-3 text-[11px] text-amber-200">
            <span>物理参数对比预览</span>
            <span>
              {key}: {formatVal(currentValue)} -&gt; {formatVal(nextValue)}
            </span>
          </div>
          <div className="mt-2 h-2 overflow-hidden rounded bg-zinc-800">
            <div
              className="h-full bg-amber-400/80"
              style={{
                width: `${Math.max(0, Math.min(100, (Number(nextValue ?? 0) / 2.0) * 100))}%`,
              }}
            />
          </div>
          {logicProposal.expected_impact ? (
            <p className="mt-2 text-[11px] text-amber-100">
              预期物理影响：{logicProposal.expected_impact}
            </p>
          ) : null}
        </div>
      ) : null}

      {tuningSuggestions.length ? (
        <div className="mt-3 space-y-1 rounded-xl border border-amber-500/20 bg-zinc-950 p-3">
          <h4 className="text-[11px] font-semibold text-amber-100">{t("语义化建议")}</h4>
          {tuningSuggestions.slice(0, 3).map((s, i) => (
            <p key={`${i}-${s}`} className="text-[11px] text-amber-100">
              {s}
            </p>
          ))}
        </div>
      ) : null}

      <div className="mt-4 flex items-center justify-between gap-2">
        <button
          type="button"
          disabled={disableByState || aligned || !hasSqlPatch}
          onClick={() => {
            if (!hasSqlPatch) return;
            onAddToInbox?.(logicProposal);
          }}
          className={`w-full rounded-lg px-3 py-2 text-xs font-medium ${
            disableByState || aligned
              ? "cursor-not-allowed bg-zinc-800/60 text-zinc-300 border border-zinc-700/60"
              : !hasSqlPatch
                ? "cursor-not-allowed bg-zinc-800 text-zinc-400"
                : "bg-amber-500/15 text-amber-200 border border-amber-500/40 hover:bg-amber-500/25"
          }`}
        >
          {autoConverted || alreadyAdded
            ? t("已转化为决策项")
            : aligned
              ? t("逻辑已对齐，无需校准")
              : !hasSqlPatch
                ? t("暂无可执行 SQL")
                : t("[转化为决策] 加入 Decision Inbox")}
        </button>
      </div>
    </section>
  );
}
