"use client";

import { useEffect, useRef } from "react";
import type { SanheClusterRow } from "./sanheClusters";

type Props = {
  clusters: SanheClusterRow[];
  /** 与 Topology 边 detail 或 branches 拼接对齐 */
  activeDetail: string | null;
};

export function SanheStructurePanel({ clusters, activeDetail }: Props) {
  const refMap = useRef<Record<string, HTMLDivElement | null>>({});

  useEffect(() => {
    if (!activeDetail) return;
    const hit = clusters.find((c) => activeDetail.includes(c.branches.join("·")) || activeDetail === c.detail);
    const el = hit ? refMap.current[hit.key] : null;
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [activeDetail, clusters]);

  if (clusters.length === 0) {
    return (
      <div
        id="sanhe-cluster-panel"
        className="rounded-xl border border-zinc-800 bg-zinc-950/40 p-3 text-[11px] text-zinc-600"
      >
        当前命例未登记三合合成场（composite_field_impact.sanhe_clusters 为空）。
      </div>
    );
  }

  return (
    <div id="sanhe-cluster-panel" className="rounded-xl border border-amber-900/35 bg-amber-950/15 p-3">
      <p className="text-[10px] font-medium uppercase tracking-wide text-amber-200/90">三合结构 · 能量贡献</p>
      <p className="mt-1 text-[11px] text-zinc-500">与拓扑金黄色边同源；cluster_abs 为合成场聚合强度摘要。</p>
      <ul className="mt-3 space-y-2">
        {clusters.map((c) => {
          const hot =
            activeDetail &&
            (activeDetail.includes(c.branches.join("·")) || activeDetail === c.detail || activeDetail.includes(c.detail));
          return (
            <li key={c.key}>
              <div
                ref={(el) => {
                  refMap.current[c.key] = el;
                }}
                className={`rounded-lg border px-2 py-2 transition-colors ${
                  hot ? "border-amber-400/70 bg-amber-950/35 ring-1 ring-amber-500/35" : "border-zinc-800/80 bg-zinc-950/50"
                }`}
              >
                <p className="font-mono text-[10px] text-amber-100/90">{c.detail}</p>
                <p className="mt-1 text-[11px] text-zinc-300">
                  支位：<span className="font-mono text-cyan-200/90">{c.branches.join(" · ")}</span>
                </p>
                <p className="mt-0.5 text-[11px] text-zinc-400">
                  状态 <span className="font-mono text-zinc-200">{c.status}</span>
                  {c.clusterAbs != null ? (
                    <>
                      {" "}
                      · cluster_abs{" "}
                      <span className="font-mono text-amber-200/90">{c.clusterAbs.toFixed(4)}</span>
                    </>
                  ) : null}
                </p>
                <p className="mt-1 font-mono text-[10px] text-zinc-500">nodes: {c.nodeLine}</p>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
