"use client";
import { CircularTopologyEngine } from "@/components/CircularTopologyEngine";

type Edge = {
  from?: string;
  to?: string;
  relation?: string;
  final_work?: number;
  detail?: string;
};

type Props = {
  graph?: Record<string, unknown>;
};

export function TopologyMapV1({ graph = {} }: Props) {
  const edges = ((graph as { edges?: Edge[] }).edges || []).slice(0, 12);
  const nodes = ((graph as { nodes?: Array<{ id: string; label: string; kind?: string }> }).nodes || []);
  const params = ((graph as { params?: Record<string, number> }).params || {});
  const threshold = Number(params.WORK_MIN_THRESHOLD || (graph as { threshold?: number }).threshold || 0.5);
  const climateIntensity = Number(((graph as { params?: Record<string, number> }).params || {}).CLIMATE_INTENSITY || 0.6);
  if (edges.length === 0) {
    return (
      <div className="rounded border border-zinc-700 bg-zinc-950 p-2 text-[11px] text-zinc-500">
        ETRM Topology HUD：暂无可视路径（低于阈值或无冲合输入）
      </div>
    );
  }
  return (
    <div className="rounded border border-zinc-700 bg-zinc-950 p-2 text-[11px]">
      <p className="mb-1 text-zinc-300">ETRM 拓扑图（V1）</p>
      <CircularTopologyEngine nodes={nodes} edges={edges} threshold={threshold} climateIntensity={climateIntensity} />
      <div className="space-y-1">
        {edges.map((e, idx) => {
          const work = Number(e.final_work || 0);
          const tone = work >= 1.5 ? "text-cyan-300" : "text-zinc-300";
          const width = `${Math.max(10, Math.min(100, work * 20))}%`;
          return (
            <div key={`edge-${idx}`} className="rounded border border-zinc-800 bg-zinc-900 p-1">
              <p className={tone}>
                {e.from} ~&gt; {e.to} [{e.relation}] {e.detail ? `| ${e.detail}` : ""}
              </p>
              <div className="mt-1 h-1.5 rounded bg-zinc-800">
                <div className="h-full rounded bg-cyan-500/80" style={{ width }} />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
