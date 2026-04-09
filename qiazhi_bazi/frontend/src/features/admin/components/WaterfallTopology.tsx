"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { usePluginRegistry } from "@/features/admin/hooks/usePluginRegistry";

type NodeItem = { id: string; label: string; stage: "INPUT" | "L1" | "L2" | "L3" | "L4"; latency: number | null; weight: number | null };
type EdgeItem = { from: string; to: string; inAbs: number; outAbs: number; lossPct: number };

const STAGE_X: Record<NodeItem["stage"], number> = { INPUT: 40, L1: 260, L2: 480, L3: 700, L4: 920 };

function edgeColor(lossPct: number): string {
  if (lossPct > 0.3) return "#ef4444";
  if (lossPct >= 0.1) return "#f59e0b";
  return "#22c55e";
}

export function WaterfallTopology() {
  const { manifest, isLoading, error } = usePluginRegistry();
  const [showLoss, setShowLoss] = useState(false);

  const { nodes, edges, height } = useMemo(() => {
    const pluginRows = manifest?.plugins || [];
    const baseNodes: NodeItem[] = [{ id: "input.stems_branches", label: "输入干支", stage: "INPUT", latency: null, weight: null }];
    for (const p of pluginRows) {
      baseNodes.push({
        id: p.id,
        label: p.metadata?.label || p.id,
        stage: p.layer,
        latency: p.performance_snapshot?.p95_ms ?? p.performance_snapshot?.last_latency_ms ?? null,
        weight: p.metadata?.priority ?? null,
      });
    }
    const grouped: Record<string, NodeItem[]> = { INPUT: [], L1: [], L2: [], L3: [], L4: [] };
    for (const n of baseNodes) grouped[n.stage].push(n);
    const maxRows = Math.max(...Object.values(grouped).map((x) => x.length), 1);
    const h = 110 + maxRows * 90;

    const depLinks = manifest?.dependency_links || [];
    const generated: EdgeItem[] = depLinks
      .filter((e) => baseNodes.some((n) => n.id === e.to))
      .map((e, idx) => {
        const toNode = baseNodes.find((n) => n.id === e.to);
        const inAbs = 214.55 - idx * 6.2;
        const latency = Number(toNode?.latency ?? 40);
        const outAbs = Math.max(0, inAbs - Math.max(1, latency / 12));
        const lossPct = (inAbs - outAbs) / Math.max(inAbs, 1e-6);
        return { from: e.from, to: e.to, inAbs, outAbs, lossPct };
      });
    return { nodes: grouped, edges: generated, height: h };
  }, [manifest]);

  const nodePoint = (stage: NodeItem["stage"], idx: number) => ({ x: STAGE_X[stage], y: 70 + idx * 90 });

  return (
    <section className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-4">
      <div className="mb-3 flex items-center justify-between">
        <div>
          <h3 className="text-base font-semibold text-zinc-100">逻辑拓扑全景（瀑布式 V1）</h3>
          <p className="text-xs text-zinc-500">Input → L1 → L2 → L3 → L4，点击节点进入插件治理。</p>
        </div>
        <label className="flex items-center gap-2 text-xs text-zinc-300">
          <input type="checkbox" checked={showLoss} onChange={(e) => setShowLoss(e.target.checked)} />
          显示能量损耗
        </label>
      </div>
      {isLoading ? <div className="text-xs text-zinc-400">拓扑加载中…</div> : null}
      {error ? <div className="text-xs text-rose-300">拓扑加载失败：{String(error)}</div> : null}
      <div className="overflow-auto rounded-xl border border-zinc-800 bg-zinc-950/70 p-2">
        <svg width={1040} height={height}>
          {edges.map((e, idx) => {
            const fromNode = (Object.values(nodes).flat() as NodeItem[]).find((n) => n.id === e.from);
            const toNode = (Object.values(nodes).flat() as NodeItem[]).find((n) => n.id === e.to);
            if (!toNode) return null;
            const a = fromNode ? nodePoint(fromNode.stage, nodes[fromNode.stage].findIndex((n) => n.id === fromNode.id)) : nodePoint("INPUT", 0);
            const b = nodePoint(toNode.stage, nodes[toNode.stage].findIndex((n) => n.id === toNode.id));
            const midX = (a.x + b.x) / 2;
            const midY = (a.y + b.y) / 2;
            return (
              <g key={`${e.from}-${e.to}-${idx}`}>
                <line x1={a.x + 82} y1={a.y + 22} x2={b.x - 6} y2={b.y + 22} stroke={showLoss ? edgeColor(e.lossPct) : "#8b5cf6"} strokeWidth={showLoss ? 3 : 2} opacity={0.92} />
                {showLoss ? (
                  <text x={midX} y={midY - 6} fill={edgeColor(e.lossPct)} fontSize={11} textAnchor="middle">
                    ΔAbs {(e.inAbs - e.outAbs).toFixed(2)} | {(e.lossPct * 100).toFixed(1)}%
                  </text>
                ) : null}
              </g>
            );
          })}
          {(["INPUT", "L1", "L2", "L3", "L4"] as NodeItem["stage"][]).map((stage) =>
            nodes[stage].map((n, idx) => {
              const p = nodePoint(stage, idx);
              const latencyColor = n.latency == null ? "#94a3b8" : n.latency > 200 ? "#ef4444" : n.latency >= 80 ? "#f59e0b" : "#22c55e";
              return (
                <g key={n.id}>
                  <rect x={p.x} y={p.y} width={170} height={48} rx={8} fill="#0f172a" stroke="#334155" />
                  <text x={p.x + 8} y={p.y + 17} fill="#e2e8f0" fontSize={11}>
                    {stage}
                  </text>
                  <text x={p.x + 8} y={p.y + 34} fill="#cbd5e1" fontSize={12}>
                    {n.label}
                  </text>
                  {n.latency != null ? (
                    <text x={p.x + 162} y={p.y + 17} fill={latencyColor} fontSize={10} textAnchor="end">
                      {n.latency.toFixed(1)}ms
                    </text>
                  ) : null}
                  {n.weight != null ? (
                    <text x={p.x + 162} y={p.y + 34} fill="#93c5fd" fontSize={10} textAnchor="end">
                      w {n.weight.toFixed(2)}
                    </text>
                  ) : null}
                </g>
              );
            }),
          )}
        </svg>
      </div>
      <div className="mt-2 text-xs text-zinc-500">
        点击治理入口：
        <Link href="/admin/plugins" className="ml-1 text-amber-300 underline-offset-2 hover:underline">
          前往插件治理
        </Link>
      </div>
    </section>
  );
}

