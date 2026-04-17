"use client";
import { useState } from "react";
import { TopologyAnimationSystem } from "@/components/TopologyAnimationSystem";

type Node = { id: string; label: string; kind?: string; pre_will_energy?: number; abs_final?: number };
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
  /** V11：与 meta.intention_context.topology_node_will_inverse_factor 一致；>1 虚线在外，<1 虚线在内 */
  willInverseFactor?: number;
  t?: (s: string) => string;
};

const BRANCHES = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"];
const BRANCH_LABELS = new Set(BRANCHES);

function radiusFromAbs(abs: number): number {
  return 10 + Math.max(0, Math.min(8, abs * 0.6));
}

export function CircularTopologyEngine({
  nodes = [],
  edges = [],
  climateIntensity = 0,
  threshold = 0.5,
  willInverseFactor = 1,
  t = (s) => s,
}: Props) {
  const size = 320;
  const center = size / 2;
  const radius = 120;
  const filteredEdges = edges.filter((e) => Number(e.final_work || 0) >= threshold);
  const nodeAbs = new Map<string, number>();
  const nodePreWillAbs = new Map<string, number>();
  const nodeMap = new Map<string, { x: number; y: number; label: string }>();
  const [report, setReport] = useState<{
    label: string;
    absPost: number;
    absPre: number;
    factor: number;
  } | null>(null);

  const factor = Number(willInverseFactor);
  const factorOk = Number.isFinite(factor) && factor > 0 && Math.abs(factor - 1) > 1e-4;

  BRANCHES.forEach((b, idx) => {
    const angle = (-Math.PI / 2) + (idx * (Math.PI * 2)) / 12;
    nodeMap.set(b, {
      x: center + radius * Math.cos(angle),
      y: center + radius * Math.sin(angle),
      label: b,
    });
  });
  nodes.forEach((n, idx) => {
    nodeAbs.set(n.label, Number(n.abs_final || 0));
    const preW = Number(n.pre_will_energy);
    if (Number.isFinite(preW) && preW > 0) {
      nodePreWillAbs.set(n.label, preW);
    }
    if (nodeMap.has(n.label)) return;
    const angle = (-Math.PI / 2) + (idx * (Math.PI * 2)) / Math.max(1, nodes.length);
    nodeMap.set(n.label, {
      x: center + (radius - 35) * Math.cos(angle),
      y: center + (radius - 35) * Math.sin(angle),
      label: n.label,
    });
  });

  const idToLabel = new Map(nodes.map((n) => [n.id, n.label]));

  const pointOf = (token?: string) => {
    const raw = (token || "").trim();
    if (raw.length === 1 && BRANCH_LABELS.has(raw)) {
      return nodeMap.get(raw) ?? nodeMap.get("子")!;
    }
    const fromId = idToLabel.get(raw || "");
    if (fromId && BRANCH_LABELS.has(fromId)) {
      return nodeMap.get(fromId)!;
    }
    const key = raw.includes("month") ? "寅" : raw.includes("day") ? "午" : "子";
    return nodeMap.get(key)!;
  };

  function openNodeReport(label: string) {
    const absPost = nodeAbs.get(label) || 0;
    const preFromNode = nodePreWillAbs.get(label);
    const absPre =
      preFromNode != null && Number.isFinite(preFromNode) && preFromNode > 0
        ? preFromNode
        : factorOk
          ? absPost / factor
          : absPost;
    const effFactor = factorOk ? factor : absPost > 0 && absPre > 0 ? absPost / absPre : 1;
    setReport({
      label,
      absPost,
      absPre,
      factor: effFactor,
    });
  }

  const animatedEdges = filteredEdges.map((e, idx) => {
    const s = pointOf(e.from);
    const te = pointOf(e.to);
    const work = Number(e.final_work || 0);
    const width = Math.max(1, Math.min(7, work));
    const opacity = Math.max(0.2, Math.min(1, 0.35 + climateIntensity * 0.65));
    const clashLike = e.relation_type === "clash" || e.relation_type === "pierce";
    const color =
      e.relation_type === "sanhe_cluster"
        ? "rgba(250,204,21,0.95)"
        : e.relation_type === "combination"
          ? "rgba(34,211,238,0.9)"
          : clashLike
            ? "rgba(251,113,133,0.9)"
            : "rgba(148,163,184,0.85)";
    const dash = e.stem_resonance ? "5 4" : undefined;
    const c1x = (s.x + te.x) / 2 + (s.y - te.y) * 0.12;
    const c1y = (s.y + te.y) / 2 + (te.x - s.x) * 0.12;
    const d = `M ${s.x} ${s.y} Q ${c1x} ${c1y} ${te.x} ${te.y}`;
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
    <div className="relative rounded border border-zinc-700 bg-zinc-950 p-2">
      <p className="mb-1 text-[11px] text-zinc-300">Circular Resonance Field (V1)</p>
      {report ? (
        <div
          className="absolute left-1/2 top-8 z-[30] w-[min(92%,16rem)] -translate-x-1/2 rounded-lg border border-cyan-600/50 bg-zinc-950/98 p-2 text-[10px] text-cyan-50 shadow-xl"
          role="dialog"
          aria-label={t("topology.willReport.title")}
        >
          <p className="mb-1 font-semibold text-cyan-200">{t("topology.willReport.title")}</p>
          <p className="mb-1 text-zinc-300">
            {t("topology.willReport.node")}: <span className="font-mono text-cyan-100">{report.label}</span>
          </p>
          <ul className="space-y-0.5 font-mono text-[9px] text-zinc-400">
            <li>
              {t("topology.willReport.post")}: {report.absPost.toFixed(4)}
            </li>
            <li>
              {t("topology.willReport.pre")}: {report.absPre.toFixed(4)}
            </li>
            <li>
              {t("topology.willReport.factor")}: {report.factor.toFixed(4)} {t("topology.willReport.formula")}
            </li>
            <li className="text-zinc-500">{t("topology.willReport.hint")}</li>
          </ul>
          <button
            type="button"
            className="mt-2 w-full rounded border border-zinc-600 py-0.5 text-[9px] text-zinc-300 hover:bg-zinc-800"
            onClick={() => setReport(null)}
          >
            {t("topology.willReport.close")}
          </button>
        </div>
      ) : null}
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
        {Array.from(nodeMap.values()).map((n) => {
          const abs = nodeAbs.get(n.label) || 0;
          const rCore = radiusFromAbs(abs);
          const rGhost = factorOk ? Math.max(6, Math.min(24, rCore * factor)) : null;
          const showRing = factorOk && rGhost != null && Math.abs(rGhost - rCore) > 0.35;
          const outerFirst = factorOk && factor > 1;
          const innerGhost = factorOk && factor < 1;
          const clickable = true;
          return (
            <g
              key={`node-${n.label}`}
              style={{ cursor: clickable ? "pointer" : "default" }}
              onClick={clickable ? () => openNodeReport(n.label) : undefined}
            >
              {showRing && outerFirst ? (
                <circle
                  cx={n.x}
                  cy={n.y}
                  r={rGhost!}
                  fill="none"
                  stroke="rgba(34,211,238,0.32)"
                  strokeWidth={1}
                  strokeDasharray="4 3"
                  opacity={0.95}
                />
              ) : null}
              <circle cx={n.x} cy={n.y} r={rCore} fill="rgba(56,189,248,0.08)" />
              {showRing && innerGhost ? (
                <circle
                  cx={n.x}
                  cy={n.y}
                  r={rGhost!}
                  fill="none"
                  stroke="rgba(34,211,238,0.32)"
                  strokeWidth={1}
                  strokeDasharray="4 3"
                  opacity={0.95}
                />
              ) : null}
              <circle cx={n.x} cy={n.y} r={10} fill="rgba(24,24,27,0.95)" stroke="rgba(148,163,184,0.8)" />
              <text x={n.x} y={n.y + 4} textAnchor="middle" fontSize="10" fill="rgba(226,232,240,0.95)">
                {n.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}
