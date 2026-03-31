"use client";

import { motion } from "framer-motion";
import type { BaziMetadata, ConflictPoint, TimelineSnapshot } from "@/types/bazi";
import type { Lang } from "@/types/bazi";
import { mapBranch, mapConflictDetail, mapStem } from "@/constants/termMap";

type Props = {
  metadata: BaziMetadata | null;
  timeline?: TimelineSnapshot | null;
  selected?: string;
  confirmedConflictDetails?: string[];
  onPickBranch: (branch: string) => void;
  t?: (s: string) => string;
  lang?: Lang;
};

const PILLAR_ORDER: Array<keyof NonNullable<BaziMetadata["pillars"]>> = ["year", "month", "day", "hour"];

function branchInConflict(branch: string, points: ConflictPoint[]): boolean {
  return points.some((p) => p.detail.includes(branch));
}

function splitGanZhi(gz: string): { stem: string; branch: string } {
  if (gz && gz.length >= 2) {
    return { stem: gz[0], branch: gz[1] };
  }
  return { stem: "?", branch: gz || "?" };
}

function clampEnergy(v: number) {
  return Math.max(0, Math.min(100, Math.round(v)));
}

export function BaziCard({
  metadata,
  timeline,
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
  const branchEnergy: Record<string, number> = {
    year_branch: pillars.year.energy_value ?? 100,
    month_branch: pillars.month.energy_value ?? 100,
    day_branch: pillars.day.energy_value ?? 100,
    hour_branch: pillars.hour.energy_value ?? 100,
  };
  points.forEach((p) => {
    if (!confirmedConflictDetails.includes(p.detail)) return;
    if (p.kind === "clash") {
      if (p.detail.includes("子午冲") && p.positions.length === 2) {
        const [a, b] = p.positions;
        const aBranch = (pillars as Record<string, { branch: string }>)[a.replace("_branch", "")]?.branch;
        const bBranch = (pillars as Record<string, { branch: string }>)[b.replace("_branch", "")]?.branch;
        if (aBranch === "子") {
          branchEnergy[a] = clampEnergy(branchEnergy[a] - 30);
          branchEnergy[b] = clampEnergy(branchEnergy[b] - 60);
        } else if (bBranch === "子") {
          branchEnergy[a] = clampEnergy(branchEnergy[a] - 60);
          branchEnergy[b] = clampEnergy(branchEnergy[b] - 30);
        } else {
          branchEnergy[a] = clampEnergy(branchEnergy[a] - 45);
          branchEnergy[b] = clampEnergy(branchEnergy[b] - 45);
        }
      } else {
        p.positions.forEach((pos) => {
          branchEnergy[pos] = clampEnergy((branchEnergy[pos] ?? 100) - 40);
        });
      }
    }
  });
  return (
    <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-medium">{t("动态命盘卡片")}</h3>
        <span className="text-xs text-zinc-500">{t("点击地支查看辩证")}</span>
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
            <div key={k} className="relative rounded-xl border border-zinc-800 bg-zinc-950 p-2 text-center">
              <p className="text-[10px] uppercase tracking-wide text-zinc-500">{k}</p>
              <p className="mt-1 text-lg">{mapStem(item.stem, lang)}</p>
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
                <div className="mt-1 rounded-md border border-zinc-700 px-2 py-1 text-base">{mapBranch(gb.branch, lang)}</div>
                </div>
              );
            })
          : null}
      </div>
      {points.length === 0 ? <p className="mt-3 text-xs text-zinc-500">{t("暂无冲突点。")}</p> : null}
    </section>
  );
}
