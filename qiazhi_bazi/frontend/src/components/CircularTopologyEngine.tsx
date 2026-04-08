"use client";
import { TopologyAnimationSystem } from "@/components/TopologyAnimationSystem";

type Node = { id: string; label: string; kind?: string };
type Edge = {
  from?: string;
  to?: string;
  relation?: string;
  relation_type?: string;
  stem_resonance?: boolean;
  efficiency_score?: number;
  clash_vibration_flag?: boolean;
  final_work?: number;
};

type Props = {
  nodes?: Node[];
  edges?: Edge[];
  climateIntensity?: number;
  threshold?: number;
};

const BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];

export function CircularTopologyEngine({ nodes = [], edges = [], climateIntensity = 0, threshold = 0.5 }: Props) {
  const size = 320;
  const center = size / 2;
  const radius = 120;
  const filteredEdges = edges.filter((e) => Number(e.final_work || 0) >= threshold);
  const nodeAbs = new Map<string, number>();
  const nodeMap = new Map<string, { x: number; y: number; label: string }>();
  BRANCHES.forEach((b, idx) => {
    const angle = (-Math.PI / 2) + (idx * (Math.PI * 2)) / 12;
    nodeMap.set(b, {
      x: center + radius * Math.cos(angle),
      y: center + radius * Math.sin(angle),
      label: b,
    });
  });
  // fallback for unknown labels from backend
  nodes.forEach((n, idx) => {
    nodeAbs.set(n.label, Number((n as Node & { abs_final?: number }).abs_final || 0));
    if (nodeMap.has(n.label)) return;
    const angle = (-Math.PI / 2) + (idx * (Math.PI * 2)) / Math.max(1, nodes.length);
    nodeMap.set(n.label, { x: center + (radius - 35) * Math.cos(angle), y: center + (radius - 35) * Math.sin(angle), label: n.label });
  });

  const pointOf = (token?: string) => {
    const key = token?.includes("month") ? "寅" : token?.includes("day") ? "午" : "子";
    return nodeMap.get(key)!;
  };

  const animatedEdges = filteredEdges.map((e, idx) => {
    const s = pointOf(e.from);
    const t = pointOf(e.to);
    const work = Number(e.final_work || 0);
    const width = Math.max(1, Math.min(7, work));
    const opacity = Math.max(0.2, Math.min(1, 0.35 + climateIntensity * 0.65));
    const clashLike = e.relation_type === "clash" || e.relation_type === "pierce";
    const color = e.relation_type === "combination" ? "rgba(34,211,238,0.9)" : clashLike ? "rgba(251,113,133,0.9)" : "rgba(148,163,184,0.85)";
    const dash = e.stem_resonance ? "5 4" : undefined;
    const c1x = (s.x + t.x) / 2 + (s.y - t.y) * 0.12;
    const c1y = (s.y + t.y) / 2 + (t.x - s.x) * 0.12;
    const d = `M ${s.x} ${s.y} Q ${c1x} ${c1y} ${t.x} ${t.y}`;
    return {
      id: `${idx}-${e.relation || "r"}`,
      d,
      color,
      width,
      opacity,
      dash,
      efficiency: Number(e.efficiency_score ?? 0.6),
      vibration: Boolean(e.clash_vibration_flag),
    };
  });

  return (
    <div className="rounded border border-zinc-700 bg-zinc-950 p-2">
      <p className="mb-1 text-[11px] text-zinc-300">Circular Resonance Field (V1)</p>
      <style>{`
        @keyframes topo-shake {
          0% { transform: translate(0, 0); }
          25% { transform: translate(0.6px, -0.4px); }
          50% { transform: translate(-0.6px, 0.5px); }
          75% { transform: translate(0.4px, 0.6px); }
          100% { transform: translate(0, 0); }
        }
      `}</style>
      <svg viewBox={`0 0 ${size} ${size}`} className="h-[320px] w-full">
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="1.8" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <circle cx={center} cy={center} r={radius + 10} fill="none" stroke="rgba(100,116,139,0.3)" />
        <TopologyAnimationSystem edges={animatedEdges} />
        {Array.from(nodeMap.values()).map((n) => (
          <g key={`node-${n.label}`}>
            <circle
              cx={n.x}
              cy={n.y}
              r={10 + Math.max(0, Math.min(8, (nodeAbs.get(n.label) || 0) * 0.6))}
              fill="rgba(56,189,248,0.08)"
            />
            <circle cx={n.x} cy={n.y} r={10} fill="rgba(24,24,27,0.95)" stroke="rgba(148,163,184,0.8)" />
            <text x={n.x} y={n.y + 4} textAnchor="middle" fontSize="10" fill="rgba(226,232,240,0.95)">
              {n.label}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}
