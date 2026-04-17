"use client";

type AnimatedEdge = {
  id: string;
  d: string;
  color: string;
  width: number;
  opacity: number;
  dash?: string;
  efficiency: number;
  vibration?: boolean;
};

type Props = {
  edges: AnimatedEdge[];
};

export function TopologyAnimationSystem({ edges }: Props) {
  return (
    <>
      {edges.map((e) => (
        <g key={`anim-${e.id}`} opacity={e.opacity}>
          <path
            d={e.d}
            fill="none"
            stroke={e.color}
            strokeWidth={e.width}
            strokeDasharray={e.dash || undefined}
            style={{
              transformBox: "fill-box",
              transformOrigin: "center",
              animation: e.vibration ? "topo-shake 0.24s linear infinite" : undefined,
            }}
          />
          <circle r={Math.max(1.5, Math.min(4, e.width / 1.8))} fill={e.color}>
            <animateMotion
              dur={`${Math.max(0.8, 3.0 - e.efficiency * 2.2)}s`}
              repeatCount="indefinite"
              rotate="auto"
              path={e.d}
            />
          </circle>
        </g>
      ))}
    </>
  );
}
