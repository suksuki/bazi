"use client";

import { useMemo } from "react";

/** 与后端 `UniversalPatternEngine.evaluate` 行对齐（Admin 用字段子集）。 */
export type PatternEvalRow = {
  pattern_id?: string;
  name?: string;
  primary_axis?: string | null;
  exclusion_hit?: boolean;
  affinity_score?: number;
  pre_exclusion_affinity?: number;
  primary_axis_energy?: number;
  gating_min_energy?: number | null;
  gating_max_self_energy?: number | null;
  exclusion_axis_snapshots?: Array<{
    axis: string;
    label_zh: string;
    energy: number;
    threshold: number;
    triggered: boolean;
  }>;
  trace_logic?: string[];
  trace_display_zh?: string[];
  stability?: number;
  engine_v?: string;
};

export type CollisionBand = "idle" | "full" | "near" | "blocked";

export function collisionBandForRow(row: PatternEvalRow | undefined): CollisionBand {
  if (!row) return "idle";
  if (row.exclusion_hit) return "blocked";
  const aff = Number(row.affinity_score);
  if (Number.isFinite(aff) && aff >= 0.72) return "full";
  if (Number.isFinite(aff) && aff >= 0.06) return "near";
  return "idle";
}

/** 拦截项：叉号旁白 / 弹层用（人读 + 机器 trace）。 */
export function getInterceptReasonLines(row: PatternEvalRow): string[] {
  const zh = [...(row.trace_display_zh || [])].filter(Boolean);
  const logic = (row.trace_logic || []).filter((x) => String(x).includes("exclusion:"));
  return [...zh, ...logic.map(String)].slice(0, 12);
}

/** 碰撞列表排序：未触线优先，再按亲和度降序。 */
export function sortEntriesWithCollision(
  entries: { section: string; key: string; spec: Record<string, unknown> }[],
  collisionById: Map<string, PatternEvalRow>,
): { section: string; key: string; spec: Record<string, unknown> }[] {
  return [...entries].sort((a, b) => {
    const ida = String(a.spec.id ?? a.key).trim();
    const idb = String(b.spec.id ?? b.key).trim();
    const ra = collisionById.get(ida);
    const rb = collisionById.get(idb);
    const ba = ra?.exclusion_hit === true ? 1 : 0;
    const bb = rb?.exclusion_hit === true ? 1 : 0;
    if (ba !== bb) return ba - bb;
    const sa = Number(ra?.affinity_score);
    const sb = Number(rb?.affinity_score);
    return (Number.isFinite(sb) ? sb : -1) - (Number.isFinite(sa) ? sa : -1);
  });
}

/** 当前八字下「净命中」：亲和最高且未触线；若全部触线则返回 null。 */
export function pickHitPatternId(sortedEntries: { spec: Record<string, unknown>; key: string }[], collisionById: Map<string, PatternEvalRow>): string | null {
  for (const e of sortedEntries) {
    const id = String(e.spec.id ?? e.key).trim();
    const r = collisionById.get(id);
    if (r && r.exclusion_hit !== true) return id;
  }
  return null;
}

export function buildGapHints(row: PatternEvalRow): string[] {
  const hints: string[] = [];
  if (row.exclusion_hit) return hints;
  const min = row.gating_min_energy;
  const pe = Number(row.primary_axis_energy);
  if (min != null && Number.isFinite(min) && Number.isFinite(pe) && pe + 1e-4 < min) {
    hints.push(`主轴未达门限：当前 ${(pe * 100).toFixed(1)}%，需 ≥ ${(min * 100).toFixed(1)}%（相对占比口径）`);
  }
  for (const line of row.trace_logic || []) {
    const s = String(line);
    if (s.includes("month_gate:penalize") || s.includes("month_gate_custom:penalize")) {
      hints.push("月令门控：月令与主轴当令关系未通过，门控折扣。");
    }
    if (s.includes("self_gate:scale")) {
      hints.push("身强门：比劫能量超过 max_self_energy，已按比例折扣。");
    }
  }
  const aff = Number(row.affinity_score);
  const pre = Number(row.pre_exclusion_affinity);
  if (
    hints.length === 0 &&
    Number.isFinite(aff) &&
    Number.isFinite(pre) &&
    aff < 0.72 &&
    pre >= 0.5
  ) {
    hints.push("排除线未触发，但门控/共振仍压低达成度；可展开 trace 细查。");
  }
  return hints.slice(0, 6);
}

const PRIMARY_AXIS_GLYPH: Record<string, string> = {
  Gov_Axis: "⚖",
  Kill_Axis: "⚔",
  Output_Axis: "✦",
  Seal_Axis: "▣",
  Self_Axis: "◎",
  Wealth_Axis: "◈",
  Robber_Axis: "◇",
  Metal_Axis: "⛓",
  Water_Axis: "≋",
  Wood_Dominance_Axis: "木",
  Fire_Dominance_Axis: "火",
};

function axisGlyph(axis: string): string {
  const k = axis.trim();
  return PRIMARY_AXIS_GLYPH[k] || "◇";
}

function descFootnote(description: string, max = 96): string {
  const t = description.trim();
  if (!t) return "";
  return t.length <= max ? t : `${t.slice(0, max)}…`;
}

function pentagonPoints(cx: number, cy: number, radius: number, vals: number[], n: number): string {
  return vals
    .map((v, i) => {
      const ang = -Math.PI / 2 + (i * 2 * Math.PI) / n;
      const r = radius * Math.max(0, Math.min(1, v));
      return `${cx + r * Math.cos(ang)},${cy + r * Math.sin(ang)}`;
    })
    .join(" ");
}

/** 判定 DNA：五轴雷达（纯 SVG）。 */
function PatternDnaRadar({ row }: { row: PatternEvalRow }) {
  const cx = 100;
  const cy = 100;
  const R = 58;
  const n = 5;
  const labels = ["主轴/门槛", "门控合成", "终亲和", "结构稳", "红线净空"];
  const pe = Number(row.primary_axis_energy);
  const min = Number(row.gating_min_energy);
  const gateRatio = Number.isFinite(pe) && Number.isFinite(min) && min > 1e-9 ? Math.min(1, pe / min) : 0;
  const pre = Math.min(1, Math.max(0, Number(row.pre_exclusion_affinity ?? 0)));
  const aff = Math.min(1, Math.max(0, Number(row.affinity_score ?? 0)));
  const stab = Math.min(1, Math.max(0, Number(row.stability ?? 0)));
  const safe = row.exclusion_hit ? 0 : 1;
  const vals = [gateRatio, pre, aff, stab, safe];
  const unit = [1, 1, 1, 1, 1];
  const outlinePts = pentagonPoints(cx, cy, R, unit, n);
  const dataPts = pentagonPoints(cx, cy, R, vals, n);

  return (
    <div className="flex flex-col items-center gap-2">
      <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-500">判定 DNA · 雷达</p>
      <svg width={200} height={200} viewBox="0 0 200 200" className="text-[8px]">
        <polygon points={outlinePts} fill="none" stroke="rgb(63 63 70)" strokeWidth={1} strokeDasharray="3 3" />
        <polygon points={outlinePts} fill="none" stroke="rgb(82 82 91)" strokeWidth={1} />
        <polygon points={dataPts} fill="rgba(16,185,129,0.2)" stroke="rgb(52 211 153)" strokeWidth={1.5} />
        {labels.map((lab, i) => {
          const ang = -Math.PI / 2 + (i * 2 * Math.PI) / n;
          const x = cx + (R + 22) * Math.cos(ang);
          const y = cy + (R + 22) * Math.sin(ang);
          return (
            <text key={lab} x={x} y={y} fill="rgb(161 161 170)" textAnchor="middle" dominantBaseline="middle" className="select-none">
              {lab}
            </text>
          );
        })}
      </svg>
      <p className="max-w-[220px] text-center text-[9px] leading-snug text-zinc-600">
        主轴/门槛=当前能量÷法典 min；红线净空=未触线 1 / 触线 0。终亲和含触线惩罚。
      </p>
    </div>
  );
}

type Props = {
  sectionLabel: string;
  manifestKey: string;
  spec: Record<string, unknown>;
  traceLabels: Record<string, string>;
  collisionRow: PatternEvalRow | null;
  specJson: string;
  onSpecJsonChange: (v: string) => void;
  onApplyMerge: () => void;
};

export function PatternSpecView({
  sectionLabel,
  manifestKey,
  spec,
  traceLabels,
  collisionRow,
  specJson,
  onSpecJsonChange,
  onApplyMerge,
}: Props) {
  const displayName = String(spec.display_name ?? spec.id ?? manifestKey);
  const description = String(spec.description ?? "").trim();
  const primaryAxis = String(spec.primary_axis ?? "").trim();
  const gating = spec.gating && typeof spec.gating === "object" && !Array.isArray(spec.gating) ? (spec.gating as Record<string, unknown>) : {};
  const exclusions =
    spec.exclusions && typeof spec.exclusions === "object" && !Array.isArray(spec.exclusions)
      ? (spec.exclusions as Record<string, number>)
      : {};
  const minEnergy = typeof gating.min_energy === "number" ? gating.min_energy : Number.NaN;
  const maxSelf = typeof gating.max_self_energy === "number" ? gating.max_self_energy : null;

  const livePe = collisionRow?.primary_axis_energy;
  const liveMin = collisionRow?.gating_min_energy ?? (Number.isFinite(minEnergy) ? minEnergy : null);

  const exclusionBars = useMemo(() => {
    const snaps = collisionRow?.exclusion_axis_snapshots;
    if (snaps && snaps.length) {
      return snaps.map((s) => ({
        key: s.axis,
        label: s.label_zh || traceLabels[s.axis] || s.axis,
        thr: s.threshold,
        energy: s.energy,
        triggered: s.triggered,
      }));
    }
    return Object.entries(exclusions).map(([axis, thr]) => ({
      key: axis,
      label: traceLabels[axis] || axis,
      thr: Number(thr),
      energy: null as number | null,
      triggered: false as boolean,
    }));
  }, [collisionRow?.exclusion_axis_snapshots, exclusions, traceLabels]);

  const scaleMax = useMemo(() => {
    const candidates: number[] = [1, minEnergy, liveMin ?? 0, livePe ?? 0].filter((x) => typeof x === "number" && Number.isFinite(x));
    return Math.max(0.15, ...candidates, 0.28);
  }, [minEnergy, liveMin, livePe]);

  return (
    <div className="space-y-4 rounded border border-zinc-800/90 bg-zinc-950/50 p-4">
      <header className="space-y-2 border-b border-zinc-800/80 pb-3">
        <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-500">
          {sectionLabel} · {manifestKey}
        </p>
        <h2 className="text-lg font-semibold tracking-tight text-zinc-50">{displayName}</h2>
        <p className="flex items-center gap-2 text-[12px] text-zinc-400">
          <span className="text-lg leading-none text-sky-300/90" title={primaryAxis || "主轴"}>
            {primaryAxis ? axisGlyph(primaryAxis) : "—"}
          </span>
          <span className="font-mono text-[11px] text-zinc-500">{primaryAxis || "未配置主轴"}</span>
        </p>
      </header>

      {description ? (
        <section className="rounded-lg border border-sky-900/40 bg-sky-950/20 px-3 py-3">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-sky-400/80">命理依据（法典 description · 统摄各参）</p>
          <p className="mt-1.5 text-[15px] font-medium leading-relaxed text-sky-50/95">{description}</p>
        </section>
      ) : (
        <p className="text-[12px] text-zinc-600">本法典条未填写 description。</p>
      )}

      <div className="grid gap-4 border-b border-zinc-800/80 pb-4 md:grid-cols-[200px_1fr]">
        <div className="flex justify-center border-b border-zinc-800/60 pb-4 md:border-b-0 md:border-r md:pb-0 md:pr-4">
          {collisionRow ? (
            <PatternDnaRadar row={collisionRow} />
          ) : (
            <p className="self-center text-center text-[10px] text-zinc-600">
              运行顶部 Test Input 后
              <br />
              可在此查看雷达
            </p>
          )}
        </div>
        <div className="min-w-0 space-y-3">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-zinc-500">横向对比 · 主轴门控</p>
          <p className="text-[10px] leading-snug text-zinc-600">
            <span className="text-emerald-400/90">■</span> 绿色带：法典要求主轴至少达到的能量带（≥ min_energy 一侧为「达标域」）。
            <span className="ml-2 text-rose-400/90">■</span> 浅红：红线禁区刻度（见下节）。
          </p>
          {description ? (
            <p className="border-l-2 border-emerald-700/50 pl-2 text-[10px] italic leading-snug text-zinc-500">
              门控参数法理：{descFootnote(description, 140)}
            </p>
          ) : null}
          <div className="relative h-10 overflow-hidden rounded-md border border-emerald-900/40 bg-zinc-950">
            {Number.isFinite(minEnergy) && scaleMax > 0 ? (
              <div
                className="absolute inset-y-0 bg-emerald-600/30"
                style={{
                  left: `${Math.min(100, (minEnergy / scaleMax) * 100)}%`,
                  right: 0,
                }}
                title="达标域：主轴能量需落入此带右界以上（相对占比口径）"
              />
            ) : null}
            {livePe != null && Number.isFinite(livePe) ? (
              <>
                <div
                  className="absolute inset-y-1 rounded-sm bg-sky-400/85 transition-all"
                  style={{ width: `${Math.min(100, (livePe / scaleMax) * 100)}%` }}
                  title={`当前主轴 ${(livePe * 100).toFixed(1)}%`}
                />
                {liveMin != null && Number.isFinite(liveMin) ? (
                  <div
                    className="absolute bottom-0 top-0 w-0.5 bg-emerald-300 shadow-[0_0_8px_rgba(52,211,153,0.5)]"
                    style={{ left: `${Math.min(99.5, (liveMin / scaleMax) * 100)}%` }}
                    title={`min_energy ${(liveMin * 100).toFixed(1)}%`}
                  />
                ) : null}
              </>
            ) : (
              <span className="absolute inset-0 flex items-center justify-center text-[10px] text-zinc-500">
                等待 Test Input 碰撞结果…
              </span>
            )}
          </div>
          <div className="flex flex-wrap gap-3 text-[10px] text-zinc-500">
            {Number.isFinite(minEnergy) ? (
              <span>
                min_energy: <span className="font-mono text-emerald-200/90">{(minEnergy * 100).toFixed(1)}%</span>
              </span>
            ) : null}
            {livePe != null && Number.isFinite(livePe) ? (
              <span>
                当前主轴: <span className="font-mono text-sky-100">{(livePe * 100).toFixed(1)}%</span>
              </span>
            ) : null}
            {maxSelf != null ? (
              <span>
                max_self: <span className="font-mono text-amber-200/80">{(maxSelf * 100).toFixed(1)}%</span>
              </span>
            ) : null}
          </div>
        </div>
      </div>

      <section className="space-y-2">
        <p className="text-[10px] font-semibold uppercase tracking-widest text-rose-500/90">红线禁区 · exclusions（绝对禁止区）</p>
        {description ? (
          <p className="border-l-2 border-rose-800/50 pl-2 text-[10px] italic leading-snug text-zinc-500">
            红线条款法理：{descFootnote(description, 140)}
          </p>
        ) : null}
        <p className="text-[11px] text-zinc-500">右侧为「逾阈即拦截」；能量刻线进入深红区即触线。</p>
        <div className="space-y-3">
          {exclusionBars.length ? (
            exclusionBars.map((row) => {
              const cap = Math.max(0.08, row.thr, row.energy ?? 0, 0.02);
              const thrPct = (row.thr / cap) * 100;
              const en = row.energy;
              const enPct = en != null && Number.isFinite(en) ? Math.min(100, (en / cap) * 100) : null;
              return (
                <div key={row.key} className="space-y-1">
                  <div className="flex justify-between text-[10px] text-zinc-400">
                    <span className={row.triggered ? "font-medium text-rose-300" : ""}>{row.label}</span>
                    <span className="font-mono">
                      阈 {(row.thr * 100).toFixed(1)}%
                      {en != null ? ` · 当前 ${(en * 100).toFixed(1)}%` : ""}
                    </span>
                  </div>
                  <div className="relative h-7 overflow-hidden rounded border border-rose-900/50 bg-zinc-950">
                    <div
                      className="absolute inset-y-0 right-0 bg-rose-600/35"
                      style={{ width: `${100 - thrPct}%` }}
                      title="绝对禁止区：能量超过阈值即格局触线"
                    />
                    {enPct != null ? (
                      <div
                        className={`absolute bottom-0 top-0 w-0.5 ${row.triggered ? "bg-rose-500 shadow-[0_0_10px_#f43f5e]" : "bg-amber-300/90"}`}
                        style={{ left: `${Math.min(99.5, enPct)}%` }}
                      />
                    ) : null}
                  </div>
                  {description ? (
                    <p className="pl-0.5 text-[9px] leading-snug text-zinc-600">↳ 条款与全盘叙事：{descFootnote(description, 100)}</p>
                  ) : null}
                </div>
              );
            })
          ) : (
            <p className="text-[11px] text-zinc-600">本法典条未配置 exclusions。</p>
          )}
        </div>
      </section>

      {collisionRow ? (
        <section className="rounded border border-violet-900/40 bg-violet-950/15 p-2 text-[11px] text-violet-100/90">
          <p className="text-[10px] font-semibold uppercase text-violet-400/90">本轮合成</p>
          <p className="mt-1 font-mono text-[10px] text-zinc-400">
            affinity {(collisionRow.affinity_score ?? 0).toFixed(3)} · pre_excl{" "}
            {(collisionRow.pre_exclusion_affinity ?? 0).toFixed(3)}
          </p>
        </section>
      ) : null}

      <details className="rounded border border-zinc-800 bg-black/30">
        <summary className="cursor-pointer select-none px-3 py-2 text-[11px] text-zinc-400 hover:text-zinc-200">
          高级 · 直接编辑格局 JSON（合并到全量草稿）
        </summary>
        <div className="space-y-2 border-t border-zinc-800/80 p-3">
          <textarea
            value={specJson}
            onChange={(e) => onSpecJsonChange(e.target.value)}
            spellCheck={false}
            className="h-48 w-full resize-y rounded border border-zinc-800 bg-zinc-950/80 p-2 font-mono text-[11px] leading-snug text-zinc-200 outline-none focus:border-zinc-600"
          />
          <button
            type="button"
            onClick={onApplyMerge}
            className="rounded border border-zinc-600 px-2 py-1 text-[11px] text-zinc-200 hover:bg-zinc-900"
          >
            合并到全量草稿
          </button>
        </div>
      </details>

    </div>
  );
}
