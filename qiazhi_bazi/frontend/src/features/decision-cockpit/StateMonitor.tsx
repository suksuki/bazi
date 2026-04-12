"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import type { TimelineSnapshot } from "@/types/bazi";
import { inferDeityEnergyAttribution } from "./inferEnergyAttribution";

type PillarKey = "year" | "month" | "day" | "hour";

type AxisSample = {
  abs: number;
  /** 悬停波峰：η / runtime 参数一行摘要 */
  etaSnapshot: string;
};

type Props = {
  metadata: Record<string, unknown> | null | undefined;
  timeline: TimelineSnapshot | null | undefined;
  physicsTensor: Record<string, unknown> | null | undefined;
};

const PILLAR_LABEL: Record<PillarKey, string> = {
  year: "年柱",
  month: "月柱",
  day: "日柱",
  hour: "时柱",
};

const ETA_SNAPSHOT_KEYS = [
  "L1_OP_PROD_ETA",
  "L1_OP_DEST_ETA",
  "L1_OP_CONN_ETA",
  "SGJG_COORDINATE_DISTORTION_DECAY",
  "MANGPAI_ETA_DIMENSIONAL_CRUSH",
  "INTERDIMENSIONAL_CONDUCTIVITY",
  "SHOW_WEAK_WORK_PATHS",
] as const;

function buildEtaSnapshotTitle(physics: Record<string, unknown> | null | undefined): string {
  if (!physics) return "（无 physics_tensor）";
  const meta = (physics.meta || {}) as Record<string, unknown>;
  const rc = (meta.runtime_physics_config || {}) as Record<string, unknown>;
  const parts: string[] = [];
  for (const k of ETA_SNAPSHOT_KEYS) {
    const v = rc[k];
    if (typeof v === "number" && Number.isFinite(v)) parts.push(`${k}=${v.toFixed(3)}`);
  }
  if (parts.length === 0) {
    for (const [k, v] of Object.entries(rc).slice(0, 6)) {
      if (typeof v === "number" && Number.isFinite(v)) parts.push(`${k}=${(v as number).toFixed(3)}`);
    }
  }
  return parts.length ? `η / 运行参数快照：${parts.join(" · ")}` : "η 快照：（meta.runtime_physics_config 暂无数值项）";
}

function miniSparkline(samples: AxisSample[], w = 72, h = 22): JSX.Element {
  const values = samples.map((s) => s.abs);
  if (values.length < 2) {
    return (
      <svg width={w} height={h} className="text-zinc-600">
        <text x={4} y={14} fontSize="9" fill="currentColor">
          —
        </text>
      </svg>
    );
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = Math.max(1e-6, max - min);
  const pts = values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * (w - 4) + 2;
      const y = h - 2 - ((v - min) / span) * (h - 6);
      return `${x},${y}`;
    })
    .join(" ");
  return (
    <svg width={w} height={h} className="text-cyan-400/90">
      <polyline fill="none" stroke="currentColor" strokeWidth="1.2" points={pts} />
      {samples.map((s, i) => {
        const x = (i / (samples.length - 1)) * (w - 4) + 2;
        const y = h - 2 - ((s.abs - min) / span) * (h - 6);
        const tip = `${s.etaSnapshot}\n|Abs|=${s.abs.toFixed(4)}`;
        return <circle key={i} cx={x} cy={y} r={1.8} fill="currentColor" opacity={0.85}><title>{tip}</title></circle>;
      })}
    </svg>
  );
}

export function StateMonitor({ metadata, timeline, physicsTensor }: Props) {
  const [axisHistory, setAxisHistory] = useState<Record<string, AxisSample[]>>({});
  const lastSigRef = useRef<string>("");

  const pillars = (metadata?.pillars || {}) as Record<string, { stem?: string; branch?: string }>;

  const deityAxes = useMemo(() => {
    const raw = physicsTensor?.deity_energy_axes;
    return raw && typeof raw === "object" ? (raw as Record<string, { absolute_energy?: number }>) : {};
  }, [physicsTensor]);

  const axesSig = useMemo(() => {
    const parts: string[] = [];
    for (const k of Object.keys(deityAxes).sort()) {
      const v = deityAxes[k]?.absolute_energy;
      parts.push(`${k}:${typeof v === "number" && Number.isFinite(v) ? v.toFixed(4) : "0"}`);
    }
    return parts.join("|");
  }, [deityAxes]);

  useEffect(() => {
    if (!axesSig || axesSig === lastSigRef.current) return;
    lastSigRef.current = axesSig;
    const axes = deityAxes;
    if (!axes || Object.keys(axes).length === 0) return;
    const etaSnap = buildEtaSnapshotTitle(physicsTensor ?? undefined);
    setAxisHistory((prev) => {
      const next = { ...prev };
      for (const [k, v] of Object.entries(axes)) {
        const abs = typeof v?.absolute_energy === "number" && Number.isFinite(v.absolute_energy) ? v.absolute_energy : 0;
        const sample: AxisSample = { abs, etaSnapshot: etaSnap };
        const arr = [...(next[k] || []), sample].slice(-32);
        next[k] = arr;
      }
      return next;
    });
  }, [axesSig, deityAxes, physicsTensor]);

  const liu = timeline?.liunian ? String(timeline.liunian) : "—";
  const dy = timeline?.dayun ? String(timeline.dayun) : "—";

  return (
    <div className="rounded-xl border border-cyan-900/40 bg-zinc-950/60 p-3">
      <p className="text-[10px] font-medium uppercase tracking-wide text-cyan-300/90">实时状态 · 元数据与十神 Abs</p>
      <p className="mt-1 text-[11px] text-zinc-500">岁运与四柱激活态；静默重算后追加 Sparkline 样本（最多 32 点）。悬停曲线节点可查看 η / 运行参数快照。</p>

      <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
        {(Object.keys(PILLAR_LABEL) as PillarKey[]).map((pk) => {
          const p = pillars[pk] || {};
          const active = Boolean(p.stem || p.branch);
          return (
            <div
              key={pk}
              className={`rounded-lg border px-2 py-2 text-[11px] ${
                active ? "border-cyan-700/50 bg-cyan-950/25 text-cyan-50" : "border-zinc-800 bg-zinc-900/40 text-zinc-600"
              }`}
            >
              <p className="text-[10px] font-medium text-zinc-500">{PILLAR_LABEL[pk]}</p>
              <p className="mt-1 font-mono text-[12px]">
                {p.stem || "—"}
                {p.branch || "—"}
              </p>
              <p className="mt-0.5 text-[9px] text-zinc-500">{active ? "已激活" : "未排盘"}</p>
            </div>
          );
        })}
      </div>

      <div className="mt-3 flex flex-wrap gap-3 rounded-lg border border-zinc-800/80 bg-zinc-900/40 px-2 py-2 text-[11px]">
        <span className="text-zinc-400">
          大运: <span className="font-mono text-amber-200/90">{dy}</span>
        </span>
        <span className="text-zinc-400">
          流年: <span className="font-mono text-amber-200/90">{liu}</span>
        </span>
      </div>

      <div className="mt-4 max-h-56 overflow-auto">
        <p className="text-[10px] font-medium uppercase tracking-wide text-zinc-500">十神轴 |absolute_energy| 轨迹</p>
        <ul className="mt-2 space-y-2">
          {Object.keys(deityAxes).length === 0 ? (
            <li className="text-[11px] text-zinc-600">尚无 deity_energy_axes（请先排盘）。</li>
          ) : (
            Object.entries(deityAxes).map(([name, row]) => {
              const cur =
                typeof row?.absolute_energy === "number" && Number.isFinite(row.absolute_energy) ? row.absolute_energy : 0;
              const hist = axisHistory[name] || [];
              const samples = hist.length ? hist : [{ abs: cur, etaSnapshot: buildEtaSnapshotTitle(physicsTensor ?? undefined) }];
              const prev = hist.length >= 2 ? hist[hist.length - 2].abs : null;
              const last = hist.length >= 1 ? hist[hist.length - 1].abs : cur;
              const attr =
                prev != null && Number.isFinite(prev)
                  ? inferDeityEnergyAttribution(physicsTensor ?? undefined, name, prev, last)
                  : null;

              return (
                <li
                  key={name}
                  className="flex flex-wrap items-center justify-between gap-2 rounded border border-zinc-800/70 bg-zinc-950/50 px-2 py-1.5"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-[11px] text-zinc-200">{name}</span>
                      <span className="font-mono text-[10px] text-cyan-200/90">{cur.toFixed(3)}</span>
                    </div>
                    {attr ? (
                      <p className="mt-1 text-[9px] leading-snug text-amber-200/85" title={attr}>
                        变动归因：{attr.length > 96 ? `${attr.slice(0, 94)}…` : attr}
                      </p>
                    ) : null}
                  </div>
                  {miniSparkline(samples)}
                </li>
              );
            })
          )}
        </ul>
      </div>
    </div>
  );
}
