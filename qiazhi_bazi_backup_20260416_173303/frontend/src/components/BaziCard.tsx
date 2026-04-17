"use client";

import { motion } from "framer-motion";
import type { BaziMetadata, ConflictPoint, TimelineSnapshot } from "@/types/bazi";
import type { Lang } from "@/types/bazi";
import { mapBranch, mapConflictDetail, mapStem } from "@/constants/termMap";
import { BRANCH_HIDDEN_STEMS, BRANCH_MAIN_STEM, PILLAR_ORDER } from "@/features/bazi-card/constants";
import {
  branchInConflict,
  computeBranchEnergy,
  computeRootState,
  deityAbbr,
  resolveTimelineStem,
  splitGanZhi,
} from "@/features/bazi-card/utils";

type Props = {
  metadata: BaziMetadata | null;
  timeline?: TimelineSnapshot | null;
  deityScores?: Record<string, number>;
  deityEnergyAxes?: Record<string, { absolute_energy?: number; relative_percentage?: number }>;
  rootDetailsByDeity?: Record<string, { root_sources?: string[]; stem_sources?: string[]; is_floating?: boolean }>;
  hoveredDeity?: string;
  selected?: string;
  confirmedConflictDetails?: string[];
  onPickBranch: (branch: string) => void;
  t?: (s: string) => string;
  lang?: Lang;
};

export function BaziCard({
  metadata,
  timeline,
  deityScores = {},
  deityEnergyAxes = {},
  rootDetailsByDeity = {},
  hoveredDeity,
  selected,
  confirmedConflictDetails = [],
  onPickBranch,
  t = (s) => s,
  lang = "ZH",
}: Props) {
  if (!metadata?.pillars) {
    return (
      <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4">
        <p className="text-sm text-zinc-500">{t("命盘卡片将在输入后出现。")}</p>
      </section>
    );
  }

  const points = metadata.conflict_matrix.points;
  const pillars = metadata.pillars;
  const dayStem = pillars.day.stem;
  const hoveredRoot = hoveredDeity ? (rootDetailsByDeity[hoveredDeity] || {}) : {};
  const hoveredRootSources = new Set<string>((hoveredRoot.root_sources || []) as string[]);
  const hoveredStemSources = new Set<string>((hoveredRoot.stem_sources || []) as string[]);
  const { roots, hasRootInNatal, unstableRoot, hasGengLuck, hasBingWuYear, selfEnergy, extremeExhausted, selfGlow } =
    computeRootState({
      dayStem,
      pillars,
      timeline,
      confirmedConflictDetails,
      deityScores,
      deityEnergyAxes,
    });
  const branchEnergy = computeBranchEnergy({ pillars, points, confirmedConflictDetails });
  return (
    <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-medium">{t("动态命盘卡片")}</h3>
        <span className="text-xs text-zinc-500">{t("点击地支查看辩证")}</span>
      </div>
      <div className={`mb-3 rounded-lg border px-2 py-1 text-xs ${hasRootInNatal ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300" : "border-rose-500/40 bg-rose-500/10 text-rose-300"}`}>
        日主锚点：{dayStem}（Self={selfEnergy.toFixed(2)}） {hasRootInNatal ? "已通根" : "无根"}
      </div>
      <div className="grid grid-cols-2 gap-2 lg:grid-cols-6">
        {PILLAR_ORDER.map((k) => {
          const item = pillars[k];
          const hot = branchInConflict(item.branch, points);
          const active = selected === item.branch;
          const posKey = `${k}_branch`;
          const energy = branchEnergy[posKey] ?? 100;
          const badges = points.filter((p) => p.positions.includes(posKey));
          return (
            <div
              key={k}
              className={`relative rounded-xl border bg-zinc-950 p-2 text-center ${
                hoveredRootSources.has(`${k}_branch`) ? "animate-pulse border-amber-400/80" : "border-zinc-800"
              }`}
            >
              <p className="text-[10px] uppercase tracking-wide text-zinc-500">{k}</p>
              <p
                className="mt-1 text-lg"
                style={
                  k === "day"
                    ? {
                        textShadow: `0 0 8px rgba(251,191,36,${selfGlow}), 0 0 18px rgba(245,158,11,${selfGlow})`,
                        fontWeight: 700,
                        opacity: extremeExhausted ? 0.30 : 1.0,
                        animation: extremeExhausted ? "qz-fade-pulse 3s ease-in-out infinite" : undefined,
                      }
                    : (hoveredStemSources.has(`${k}_stem`)
                        ? { textShadow: "0 0 10px rgba(56,189,248,0.7)" }
                        : undefined)
                }
              >
                {mapStem(item.stem, lang)}
              </p>
              <div className="mt-0.5 text-[10px] text-zinc-400">
                {k === "day" ? "我" : deityAbbr(dayStem, item.stem)}
              </div>
              <motion.button
                type="button"
                onClick={() => onPickBranch(item.branch)}
                animate={hot ? { boxShadow: ["0 0 0px rgba(245,158,11,.0)", "0 0 10px rgba(245,158,11,.6)", "0 0 0px rgba(245,158,11,.0)"] } : {}}
                transition={{ duration: 1.8, repeat: hot ? Infinity : 0 }}
                className={`mt-1 w-full rounded-md border px-2 py-1 text-base ${
                  active ? "border-amber-400 bg-amber-500/20" : "border-zinc-700"
                }`}
              >
                {mapBranch(item.branch, lang)}
              </motion.button>
              <div className="mt-0.5 text-[10px] text-zinc-500">
                {deityAbbr(dayStem, BRANCH_MAIN_STEM[item.branch] || item.stem)}
                {BRANCH_HIDDEN_STEMS[item.branch]?.length ? (
                  <span className="ml-1 text-[9px] text-zinc-600">
                    ({BRANCH_HIDDEN_STEMS[item.branch].map((s) => deityAbbr(dayStem, s)).join("/")})
                  </span>
                ) : null}
              </div>
              {k !== "day" && roots.includes(item.branch) ? (
                <div
                  className={`pointer-events-none mt-1 text-[10px] ${unstableRoot ? "animate-pulse" : ""}`}
                  style={{
                    color: unstableRoot ? "#fca5a5" : "#fcd34d",
                    opacity: unstableRoot ? 0.75 : 0.95,
                  }}
                >
                  {unstableRoot ? "↘ 根链波动" : "↘ 通根链路"}
                </div>
              ) : null}
              <div className="mt-2">
                <div className="mb-1 flex items-center justify-between text-[10px] text-zinc-500">
                  <span>{t("能量")}</span>
                  <span>{energy}%</span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded bg-zinc-800">
                  <motion.div
                    className="h-full bg-emerald-400"
                    animate={{ width: `${energy}%` }}
                    transition={{ duration: 0.55, ease: "easeOut" }}
                  />
                </div>
              </div>
              {hasGengLuck && k === "day" ? (
                <div className="mt-1 text-[10px] text-sky-300">⬅ 庚运压制箭头</div>
              ) : null}
              {badges.length > 0 ? (
                <div className="pointer-events-none absolute bottom-1 right-1 flex max-w-[90%] flex-wrap justify-end gap-1">
                  {badges.slice(0, 2).map((b, i) => {
                    const confirmed = confirmedConflictDetails.includes(b.detail);
                    return (
                    <span
                      key={`${b.detail}-${i}`}
                      className={`rounded-full border px-1.5 py-0.5 text-[9px] leading-none ${
                        confirmed
                          ? "border-rose-500/50 bg-rose-500/20 text-rose-300"
                          : "border-amber-500/40 bg-amber-500/15 text-amber-300"
                      }`}
                    >
                      {mapConflictDetail(b.detail, lang)}
                    </span>
                    );
                  })}
                </div>
              ) : null}
            </div>
          );
        })}
        {timeline
          ? [
              { key: "dayun", label: t("大运"), value: timeline.dayun },
              { key: "liunian", label: `${t("流年")}(${timeline.reference_year})`, value: timeline.liunian },
            ].map((x) => {
              const gb = splitGanZhi(x.value);
              return (
                <div key={x.key} className="rounded-xl border border-zinc-800 bg-zinc-950 p-2 text-center">
                  <p className="text-[10px] uppercase tracking-wide text-zinc-500">{x.label}</p>
                <p className="mt-1 text-lg">{mapStem(gb.stem, lang)}</p>
                <div className="mt-0.5 text-[10px] text-zinc-400">{deityAbbr(dayStem, gb.stem)}</div>
                <div className="mt-1 rounded-md border border-zinc-700 px-2 py-1 text-base">{mapBranch(gb.branch, lang)}</div>
                <div className="mt-0.5 text-[10px] text-zinc-500">
                  {deityAbbr(dayStem, resolveTimelineStem(gb.branch, gb.stem))}
                  {BRANCH_HIDDEN_STEMS[gb.branch]?.length ? (
                    <span className="ml-1 text-[9px] text-zinc-600">
                      ({BRANCH_HIDDEN_STEMS[gb.branch].map((s) => deityAbbr(dayStem, s)).join("/")})
                    </span>
                  ) : null}
                </div>
                </div>
              );
            })
          : null}
      </div>
      {hasBingWuYear ? (
        <div className="mt-3 rounded-lg border border-red-500/40 bg-gradient-to-r from-red-900/30 via-red-700/20 to-orange-600/20 px-2 py-1 text-[11px] text-red-200">
          流年丙午触发聚火效应，热力扩散中...
        </div>
      ) : null}
      {points.length === 0 ? <p className="mt-3 text-xs text-zinc-500">{t("暂无冲突点。")}</p> : null}
      <style jsx>{`
        @keyframes qz-fade-pulse {
          0% { opacity: 0.30; }
          50% { opacity: 0.10; }
          100% { opacity: 0.30; }
        }
      `}</style>
    </section>
  );
}
