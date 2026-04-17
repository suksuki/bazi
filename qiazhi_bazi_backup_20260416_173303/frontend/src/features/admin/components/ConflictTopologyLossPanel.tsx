"use client";

import { useMemo } from "react";

type TopoEntry = {
  detail?: string;
  kind?: string;
  linear_multiplier?: number | null;
  pct_change_display?: number | null;
  source?: string;
  manifest_entry_id?: string;
  /** PAIR_DECAYS 等五行折损可读串 */
  element_loss_display?: string;
};

function readTopology(meta: unknown): { aggregate: number | null; entries: TopoEntry[] } | null {
  if (!meta || typeof meta !== "object") return null;
  const m = meta as Record<string, unknown>;
  const raw = m.conflict_topology_v1;
  if (!raw || typeof raw !== "object") return null;
  const t = raw as Record<string, unknown>;
  const agg = t.aggregate_conflict_linear_factor;
  const aggregate = typeof agg === "number" && Number.isFinite(agg) ? agg : Number(agg) || null;
  const entries: TopoEntry[] = [];
  const arr = t.entries;
  if (Array.isArray(arr)) {
    for (const x of arr) {
      if (x && typeof x === "object") entries.push(x as TopoEntry);
    }
  }
  return { aggregate, entries };
}

type Props = {
  physicsTensor: Record<string, unknown> | null | undefined;
  className?: string;
};


/** V9.0：冲突法典产生的逐条损耗与 aggregate 乘子（Admin 演算区） */
export function ConflictTopologyLossPanel({ physicsTensor, className = "" }: Props) {
  const parsed = useMemo(() => readTopology(physicsTensor?.meta), [physicsTensor?.meta]);

  if (!parsed) {
    return (
      <div
        className={`rounded border border-zinc-800/80 bg-zinc-950/50 px-2 py-1.5 text-[10px] text-zinc-500 ${className}`}
        data-testid="conflict-topology-loss-empty"
      >
        暂无冲突拓扑数据（需含 conflict_matrix 的完整物理推断）。
      </div>
    );
  }

  const { aggregate, entries } = parsed;

  return (
    <div
      className={`rounded-lg border border-rose-900/40 bg-gradient-to-br from-rose-950/25 to-zinc-950/90 p-2.5 ${className}`}
      data-testid="conflict-topology-loss"
    >
      <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-rose-200/90">
        冲突损耗明细 · CONFLICT_MANIFEST
        {aggregate != null ? (
          <span className="ml-2 font-mono normal-case text-rose-300/80">aggregate ×{aggregate.toFixed(4)}</span>
        ) : null}
      </p>
      {!entries.length ? (
        <p className="text-[10px] text-zinc-500">当前无冲突矩阵扫描点。</p>
      ) : (
        <ul className="space-y-1 text-[10px] leading-snug text-zinc-200">
          {entries.map((e, i) => {
            const detail = String(e.detail || "").trim() || "（无 detail）";
            const mult = e.linear_multiplier;
            const pct = e.pct_change_display;
            const src = String(e.source || "");
            const mid = String(e.manifest_entry_id || "");
            const eloss = String(e.element_loss_display || "").trim();
            const tail = eloss
              ? eloss
              : mult != null && pct != null
                ? `线性能量 ×${mult} (${pct >= 0 ? "+" : ""}${pct}%)`
                : "（legacy / 无乘子）";
            const srcLine = [src, mid].filter(Boolean).join(" · ");
            return (
              <li key={i} className="font-mono text-[10px]">
                <span className="text-rose-100/95">{detail}</span>
                <span className="text-zinc-400"> → </span>
                <span>{tail}</span>
                {srcLine ? <span className="block pl-2 text-[9px] text-zinc-500">Source: {srcLine}</span> : null}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
