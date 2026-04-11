"use client";

import { AbsDistributionChart } from "@/features/stream-board/components/AbsDistributionChart";
import { buildConsensusText } from "@/features/ten-god-list/utils";

type Props = {
  deityScores: Record<string, number>;
  /** 来自 `physics_tensor.meta.causal_routing`，驱动 Abs 条冲突雷电标 */
  causalRouting?: Record<string, unknown> | null;
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
  tombLockRate?: number;
  tombReleased?: boolean;
  climateIntensity?: number;
  climateSeason?: string;
  onOpenLogic?: (payload: {
    title: string;
    focus: string;
    details: string[];
    deityTrace?: Record<string, unknown>;
  }) => void;
  onHoverDeity?: (deityName?: string) => void;
};

export function TenGodNumericList({
  deityScores,
  causalRouting = null,
  deityEnergyAxes = {},
  deityComponents = {},
  deityTraceDetails = {},
  topAnomaly,
  consensusHistory = [],
  hardRouteLogs = [],
  tombLockRate = 0.9,
  tombReleased = false,
  climateIntensity = 0,
  climateSeason = "",
  onOpenLogic,
  onHoverDeity,
}: Props) {
  const anomalyTag = (topAnomaly || "").trim();
  const consensusText = buildConsensusText(consensusHistory);
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
          <span className={`rounded-md border px-2 py-0.5 text-[10px] ${tombReleased ? "border-cyan-500/40 bg-cyan-500/10 text-cyan-300" : "border-zinc-700 bg-zinc-800 text-zinc-300"}`}>
            {tombReleased ? "[Released]" : `[Locked ${Math.round(tombLockRate * 100)}%]`}
          </span>
          <span className="text-[11px] text-zinc-500">[十神名 | 能量条 | 百分比]</span>
        </div>
      </div>
      <AbsDistributionChart
        deityScores={deityScores}
        deityEnergyAxes={deityEnergyAxes}
        deityComponents={deityComponents}
        causalRouting={causalRouting}
        topAnomaly={topAnomaly}
        hardRouteLogs={hardRouteLogs}
        climateIntensity={climateIntensity}
        climateSeason={climateSeason}
        onOpenLogic={onOpenLogic}
        onHoverDeity={onHoverDeity}
        deityTraceDetails={deityTraceDetails}
      />
      <div className="mt-3 rounded-lg border border-zinc-700 bg-zinc-900/60 px-3 py-2 text-[11px] text-zinc-500">
        [L2 Structure Skill: Waiting for Alignment...]
      </div>
    </section>
  );
}
