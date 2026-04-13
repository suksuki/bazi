"use client";

import { useMemo } from "react";

type Five = Record<string, number>;

const ORDER = ["wood", "fire", "earth", "metal", "water"] as const;

const LABEL: Record<(typeof ORDER)[number], string> = {
  wood: "木 Wood",
  fire: "火 Fire",
  earth: "土 Earth",
  metal: "金 Metal",
  water: "水 Water",
};

function readCompare(meta: unknown): { pre: Five; post: Five } | null {
  if (!meta || typeof meta !== "object") return null;
  const m = meta as Record<string, unknown>;
  const block = m.climate_manifest_field_compare_v1;
  if (!block || typeof block !== "object") return null;
  const b = block as Record<string, unknown>;
  const pre = b.normalized_pre_manifest;
  const post = b.normalized_post_manifest_pre_hard_climate;
  if (!pre || !post || typeof pre !== "object" || typeof post !== "object") return null;
  const out = (raw: Record<string, unknown>): Five => {
    const o: Five = {};
    for (const k of ORDER) {
      const v = raw[k];
      o[k] = typeof v === "number" && Number.isFinite(v) ? v : Number(v) || 0;
    }
    return o;
  };
  return { pre: out(pre as Record<string, unknown>), post: out(post as Record<string, unknown>) };
}

function pctDelta(before: number, after: number): number | null {
  if (!(before > 1e-8)) return null;
  return Math.round(((after - before) / before) * 1000) / 10;
}

type Props = {
  physicsTensor: Record<string, unknown> | null | undefined;
  className?: string;
};

/**
 * V8.3：展示月令调候法典对五行场强分布的影响（归一化前后对比，不含 ClimateInferenceSkill 硬通道）。
 */
export function ClimateFieldStrengthCompare({ physicsTensor, className = "" }: Props) {
  const meta = physicsTensor?.meta;
  const pair = useMemo(() => readCompare(meta), [meta]);
  const monthBranch = useMemo(() => {
    if (!meta || typeof meta !== "object") return "";
    const m = meta as Record<string, unknown>;
    const cfc = m.climate_field_correction_v1;
    if (!cfc || typeof cfc !== "object") return "";
    return String((cfc as Record<string, unknown>).month_branch || "").trim();
  }, [meta]);

  if (!pair) {
    return (
      <div
        className={`rounded border border-zinc-800/80 bg-zinc-950/50 px-2 py-1.5 text-[10px] text-zinc-500 ${className}`}
        data-testid="climate-field-compare-empty"
      >
        暂无场强对比数据（需完整物理推断链路，非手写张量预览）。
      </div>
    );
  }

  const { pre, post } = pair;

  return (
    <div
      className={`rounded-lg border border-cyan-900/45 bg-gradient-to-br from-cyan-950/30 to-zinc-950/90 p-2.5 ${className}`}
      data-testid="climate-field-compare"
    >
      <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-cyan-300/90">
        场强对比 · 调候法典
        {monthBranch ? <span className="ml-2 font-mono normal-case text-cyan-500/90">月令 {monthBranch}</span> : null}
      </p>
      <ul className="space-y-1 font-mono text-[10px] leading-tight text-zinc-200">
        {ORDER.map((k) => {
          const a = pre[k];
          const b = post[k];
          const p = pctDelta(a, b);
          const cap = k.charAt(0).toUpperCase() + k.slice(1);
          const arrow = `${a.toFixed(2)} → ${b.toFixed(2)}`;
          const tail = p == null ? "" : p === 0 ? " (0%)" : ` (${p > 0 ? "+" : ""}${p}%)`;
          return (
            <li key={k} className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5" data-element={k}>
              <span className="min-w-[100px] text-cyan-200/80">{LABEL[k]}</span>
              <span className="text-zinc-300">
                <span className="text-zinc-500">{cap}:</span> {arrow}
                <span className={p != null && p > 0 ? "text-amber-300/95" : p != null && p < 0 ? "text-sky-300/90" : "text-zinc-500"}>
                  {tail}
                </span>
              </span>
            </li>
          );
        })}
      </ul>
      <p className="mt-1.5 text-[9px] leading-snug text-zinc-500">
        左侧为 climate_mods=1（各五行）的归一化场强；右侧为当前 ``climate_manifest.json`` 月令乘子后的场强（第二段硬调候前）。
      </p>
    </div>
  );
}
