"use client";

import { ALL_DEITIES, TEN_GOD_ORDER } from "@/features/ten-god-list/constants";
import { buildConsensusText, buildLockedDeitySet, extractHardRouteKeys } from "@/features/ten-god-list/utils";

type Props = {
  deityScores: Record<string, number>;
  deityEnergyAxes?: Record<string, { absolute_energy?: number; relative_percentage?: number }>;
  deityComponents?: Record<string, {
    total_score?: number;
    stem_score?: number;
    root_score?: number;
    root_sources?: string[];
    stem_sources?: string[];
    is_floating?: boolean;
  }>;
  deityTraceDetails?: Record<string, {
    base_energy?: { raw_deity_energy?: number; contribution_sources?: Array<Record<string, unknown>> };
    interventions?: { applied_params?: Record<string, number> };
    normalization?: { final_percent?: number; final_energy_before_pct?: number; all_deities_final_energy_sum?: number; formula?: string };
  }>;
  topAnomaly?: string;
  consensusHistory?: Array<{ decision_key: string; confirmed_value?: number; reasoning?: string }>;
  hardRouteLogs?: string[];
  onOpenLogic?: (payload: {
    title: string;
    focus: string;
    details: string[];
    deityTrace?: Record<string, unknown>;
  }) => void;
  onHoverDeity?: (deityName?: string) => void;
};

function LockIcon({ title }: { title: string }) {
  return (
    <span title={title} className="inline-flex items-center text-sky-300 transition-colors hover:text-sky-200" aria-label={title}>
      <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M7 10V7.8C7 5.15 9.15 3 11.8 3C14.45 3 16.6 5.15 16.6 7.8V10" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        <rect x="5" y="10" width="14" height="11" rx="2.2" stroke="currentColor" strokeWidth="1.8" />
        <circle cx="12" cy="15.5" r="1.3" fill="currentColor" />
      </svg>
    </span>
  );
}

export function TenGodNumericList({
  deityScores,
  deityEnergyAxes = {},
  deityComponents = {},
  deityTraceDetails = {},
  topAnomaly,
  consensusHistory = [],
  hardRouteLogs = [],
  onOpenLogic,
  onHoverDeity,
}: Props) {
  const anomalyTag = (topAnomaly || "").trim();
  const consensusText = buildConsensusText(consensusHistory);
  const lockedByKeys = extractHardRouteKeys(hardRouteLogs);
  const lockedDeities = buildLockedDeitySet(hardRouteLogs);
  return (
    <section className="rounded-2xl border border-amber-500/30 bg-zinc-900/50 p-4">
      <div className="mb-2 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-amber-300">十神纯数看板</h3>
        <div className="flex items-center gap-2">
          {consensusHistory.length > 0 ? (
            <span
              title={consensusText || "已存在会话共识"}
              className="rounded-md border border-sky-500/40 bg-sky-500/10 px-2 py-0.5 text-[10px] text-sky-300"
            >
              共识已对齐
            </span>
          ) : null}
          <span className="text-[11px] text-zinc-500">[十神名 | 能量条 | 百分比]</span>
        </div>
      </div>
      <div className="space-y-2">
        {TEN_GOD_ORDER.map((name) => {
          const relPct = Number((deityEnergyAxes[name]?.relative_percentage ?? deityScores[name]) ?? 0);
          const absEnergy = Number((deityEnergyAxes[name]?.absolute_energy ?? 0) ?? 0);
          const comp = deityComponents[name] || {};
          const stemScore = Number(comp.stem_score ?? relPct);
          const rootScore = Number(comp.root_score ?? 0);
          const totalScore = Number(comp.total_score ?? relPct);
          const totalAbsWidth = Math.max(0, Math.min(100, (absEnergy / 10) * 100));
          const ratioStem = totalScore > 0 ? Math.max(0, stemScore) / totalScore : 0;
          const ratioRoot = totalScore > 0 ? Math.max(0, rootScore) / totalScore : 0;
          const rootWidth = `${Math.max(0, Math.min(100, totalAbsWidth * ratioRoot))}%`;
          const stemWidth = `${Math.max(0, Math.min(100, totalAbsWidth * ratioStem))}%`;
          const hit = anomalyTag && (anomalyTag.includes(name) || (name === "比肩" && anomalyTag.includes("比劫")));
          return (
            <button
              key={name}
              type="button"
              onClick={() =>
                onOpenLogic?.({
                  title: `${name} 数值审计`,
                  focus: name,
                  details: [
                    `${name}: ${totalScore.toFixed(2)}% (Abs: ${absEnergy.toFixed(2)})`,
                    hit ? `[审计预警] ${anomalyTag}` : "当前未命中该项异常关键词。",
                    "点击后可查看：基础动能 / 物理干预 / 归一化校准",
                  ],
                  deityTrace: deityTraceDetails[name] as Record<string, unknown> | undefined,
                })
              }
              className="w-full rounded-lg border border-zinc-800 bg-zinc-950 px-2 py-2 text-left transition-colors hover:bg-zinc-900/90"
              title="点击查看演算路径"
              onMouseEnter={() => onHoverDeity?.(name)}
              onMouseLeave={() => onHoverDeity?.(undefined)}
            >
              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-300">{name}</span>
                <span className="flex items-center gap-2">
                  {hit ? (
                    <span className="rounded-full border border-rose-500/60 bg-rose-500/20 px-2 py-0.5 text-[10px] text-rose-300">
                      ! 挑刺
                    </span>
                  ) : null}
                  {lockedDeities.has(name) ? <LockIcon title={`该能量场已根据共识参数 ${lockedByKeys.join(", ") || "N/A"} 锁定`} /> : null}
                  <span className="text-zinc-400">
                    {totalScore.toFixed(2)}%{" "}
                    <span className="text-sky-300">(Abs: {absEnergy.toFixed(2)})</span>
                  </span>
                </span>
              </div>
              <div className="mt-1.5 h-1.5 w-full overflow-hidden rounded bg-zinc-800">
                <div className="flex h-full w-full">
                  <div className="h-full bg-amber-500/90" style={{ width: rootWidth }} />
                  <div className="h-full bg-amber-300/45" style={{ width: stemWidth }} />
                </div>
              </div>
              <div className="mt-1 text-[10px] text-zinc-500">
                (透:{stemScore.toFixed(2)} | 根:{rootScore.toFixed(2)})
              </div>
            </button>
          );
        })}
      </div>
      <div className="mt-3 rounded-lg border border-zinc-700 bg-zinc-900/60 px-3 py-2 text-[11px] text-zinc-500">
        [L2 Structure Skill: Waiting for Alignment...]
      </div>
    </section>
  );
}
