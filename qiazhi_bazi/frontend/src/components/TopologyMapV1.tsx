"use client";
import { CircularTopologyEngine } from "@/components/CircularTopologyEngine";

type Edge = {
  from?: string;
  to?: string;
  relation?: string;
  relation_type?: string;
  final_work?: number;
  detail?: string;
};

type Props = {
  graph?: Record<string, unknown>;
  /** 点击「三合」拓扑边时回调（用于黑匣子跳转结构卡片） */
  onActivateSanheEdge?: (edge: Edge) => void;
  /** 与 edge.detail 或 `${from}->${to}` 对齐的高亮键 */
  activeEdgeKey?: string | null;
};

function selectEdgesForHud(raw: Edge[]): Edge[] {
  const sanhe = raw.filter((e) => e.relation_type === "sanhe_cluster");
  const rest = raw.filter((e) => e.relation_type !== "sanhe_cluster");
  return [...sanhe, ...rest].slice(0, 24);
}

function edgeKey(e: Edge, idx: number): string {
  const d = String(e.detail || "").trim();
  if (d) return d;
  return `${String(e.from)}->${String(e.to)}:${idx}`;
}

export function TopologyMapV1({ graph = {}, onActivateSanheEdge, activeEdgeKey }: Props) {
  const rawEdges = ((graph as { edges?: Edge[] }).edges || []) as Edge[];
  const edges = selectEdgesForHud(rawEdges);
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
          const isSanhe = e.relation_type === "sanhe_cluster";
          const tone = isSanhe ? "text-amber-300" : work >= 1.5 ? "text-cyan-300" : "text-zinc-300";
          const barClass = isSanhe ? "bg-amber-400/85" : "bg-cyan-500/80";
          const width = `${Math.max(10, Math.min(100, work * 20))}%`;
          const ek = edgeKey(e, idx);
          const active = Boolean(activeEdgeKey && (ek === activeEdgeKey || String(e.detail) === activeEdgeKey));
          const shellClass = `w-full rounded border p-1 text-left transition-colors ${
            active ? "border-amber-400/70 bg-amber-950/30 ring-1 ring-amber-500/40" : "border-zinc-800 bg-zinc-900"
          } ${isSanhe && onActivateSanheEdge ? "cursor-pointer hover:border-amber-600/50" : ""}`;
          const inner = (
            <>
              <p className={tone}>
                {e.from} ~&gt; {e.to} [{e.relation}] {e.detail ? `| ${e.detail}` : ""}
              </p>
              <div className="mt-1 h-1.5 rounded bg-zinc-800">
                <div className={`h-full rounded ${barClass}`} style={{ width }} />
              </div>
              {isSanhe && onActivateSanheEdge ? (
                <p className="mt-0.5 text-[9px] text-amber-200/80">点击此行联动下方「三合结构」卡片</p>
              ) : null}
            </>
          );
          if (isSanhe && onActivateSanheEdge) {
            return (
              <button key={`edge-${idx}`} type="button" className={shellClass} onClick={() => onActivateSanheEdge(e)}>
                {inner}
              </button>
            );
          }
          return (
            <div key={`edge-${idx}`} className={shellClass}>
              {inner}
            </div>
          );
        })}
      </div>
    </div>
  );
}
