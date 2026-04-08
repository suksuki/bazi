"use client";

type WorkVectorItem = {
  detail?: string;
  type?: string;
  expected_work?: number;
  backfire_risk?: number;
  unlock_gain?: number;
  source_deity?: string;
  target_deity?: string;
  momentum_direction?: string;
  is_micro_path?: boolean;
};

type Props = {
  vectors: WorkVectorItem[];
  bodyLabels: string[];
  useLabels: string[];
  showWeakPaths?: boolean;
  emptyHint?: string;
};

function edgeColor(type: string): string {
  if (type === "冲" || type === "穿" || type === "刑") return "rgba(248,113,113,0.95)";
  if (type === "合") return "rgba(34,211,238,0.95)";
  return "rgba(125,211,252,0.9)";
}

function yFor(index: number, total: number): number {
  if (total <= 1) return 70;
  const gap = 90 / (total - 1);
  return 25 + index * gap;
}

export function EnergyBridge({ vectors, bodyLabels, useLabels, showWeakPaths = false, emptyHint }: Props) {
  const width = 300;
  const height = 140;

  const visibleVectors = showWeakPaths ? vectors : vectors.filter((v) => !v.is_micro_path);
  if (!visibleVectors.length) {
    return (
      <div className="flex h-28 w-full items-center justify-center rounded bg-zinc-950 text-[11px] text-zinc-400">
        {emptyHint || (showWeakPaths ? "[能量空转 / 无功可受]" : "[能量空转 / 微观路径已隐藏]")}
      </div>
    );
  }

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="h-28 w-full rounded bg-zinc-950">
      <defs>
        <filter id="eb-glow">
          <feGaussianBlur stdDeviation="1.3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      {visibleVectors.slice(0, 12).map((v, i) => {
        const gain = Number(v.unlock_gain || 0);
        const risk = Number(v.backfire_risk || 0);
        const isBackfire = risk >= gain || v.momentum_direction === "REBOUND";
        const isTurbulent = gain > 0 && risk > gain * 0.5;
        const isPathBroken = String(v.detail || "").includes("子午冲");
        const sourceIdx = Math.max(0, bodyLabels.indexOf(v.source_deity || bodyLabels[0]));
        const targetIdx = Math.max(0, useLabels.indexOf(v.target_deity || useLabels[0]));
        const bodyX = 18;
        const bodyY = yFor(sourceIdx, Math.max(1, bodyLabels.length));
        const useX = width - 18;
        const useY = yFor(targetIdx, Math.max(1, useLabels.length));
        const x1 = isBackfire ? useX : bodyX;
        const y1 = isBackfire ? useY : bodyY;
        const x2 = isBackfire ? bodyX : useX;
        const y2 = isBackfire ? bodyY : useY;
        const cx1 = 110;
        const cx2 = 190;
        const path = `M ${x1} ${y1} C ${cx1} ${y1}, ${cx2} ${y2}, ${x2} ${y2}`;
        const color = isPathBroken ? "#FB7185" : (isBackfire ? "#FF4D4F" : edgeColor(v.type || ""));
        const net = Number(v.expected_work || 0);
        const strokeWidth = Math.max(1, 1 + Math.abs(net) * 2);
        const microOpacity = v.is_micro_path ? 0.2 : 0.9;
        const dur = `${Math.max(1.2, 3.2 - Math.min(2, Math.abs(net)))}s`;
        const midX = (x1 + x2) / 2;
        const midY = (y1 + y2) / 2;
        return (
          <g key={`edge-${i}`}>
            <title>
              {(v.source_deity || "体")} [{v.type || "冲"}] {(v.target_deity || "用")}：基础能量 {gain.toFixed(1)} - 损耗 {risk.toFixed(1)} - 最终做功 {net >= 0 ? "+" : ""}
              {net.toFixed(1)}
            </title>
            <path
              d={path}
              stroke={color}
              strokeWidth={strokeWidth}
              fill="none"
              strokeOpacity={microOpacity}
              strokeDasharray={v.is_micro_path ? "2 5" : (v.type === "冲" || v.type === "穿" ? "6 4" : undefined)}
            />
            {isPathBroken ? (
              <text x={midX - 26} y={midY - 8} fontSize="9" fill="#FB7185">
                [PATH_BROKEN]
              </text>
            ) : null}
            <circle r="2.8" fill={color} filter="url(#eb-glow)">
              <animateMotion dur={dur} repeatCount="indefinite" path={path} />
            </circle>
            {isTurbulent ? (
              <g>
                <circle cx={midX} cy={midY} r="5.5" fill="none" stroke="#FF4D4F" strokeWidth="1.2" opacity="0.9">
                  <animate attributeName="r" values="4;8;4" dur="1.2s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.95;0.35;0.95" dur="1.2s" repeatCount="indefinite" />
                </circle>
                <circle cx={midX} cy={midY} r="1.8" fill="#FF4D4F" opacity="0.9">
                  <animateTransform attributeName="transform" type="rotate" from={`0 ${midX} ${midY}`} to={`360 ${midX} ${midY}`} dur="1s" repeatCount="indefinite" />
                </circle>
                {isPathBroken ? (
                  <text x={midX - 40} y={midY + 12} fontSize="9" fill="#FCA5A5">
                    食伤泄秀功能坍缩
                  </text>
                ) : null}
              </g>
            ) : null}
          </g>
        );
      })}
    </svg>
  );
}

