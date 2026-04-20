"use client";

type Props = {
  pluginCount: number;
  hasAuthoritySource: boolean;
};

const positionWeights = [
  ["月柱", "1.00"],
  ["日柱", "0.92"],
  ["时柱", "0.85"],
  ["年柱", "0.72"],
  ["大运", "0.88"],
  ["流年", "0.56"],
];

const distanceWeights = [
  ["同柱", "1.00"],
  ["相邻", "0.78"],
  ["隔柱", "0.52"],
  ["远隔", "0.31"],
];

export function V17_AdminCoreEnginePanel({
  pluginCount,
  hasAuthoritySource,
}: Props) {
  return (
    <section className="rounded-2xl border border-zinc-800 bg-[radial-gradient(circle_at_top_left,rgba(251,191,36,0.10),transparent_32%),linear-gradient(180deg,rgba(24,24,27,0.88),rgba(9,9,11,0.96))] p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="text-[11px] uppercase tracking-[0.28em] text-amber-300/80">Core Engine</div>
          <h3 className="mt-2 text-sm font-semibold text-zinc-100">Six-Pillar Spacetime Core</h3>
          <p className="mt-1 max-w-3xl text-[11px] leading-6 text-zinc-400">
            这是六柱时空作用核心层，不属于普通插件。它负责柱位权重、距离衰减、做功路径、效应裁决与体用输出。
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-[10px]">
          <span className="rounded-full border border-zinc-700 bg-zinc-950/70 px-3 py-1 text-zinc-400">
            已接插件 {pluginCount}
          </span>
          <span className={`rounded-full border px-3 py-1 ${hasAuthoritySource ? "border-emerald-500/30 bg-emerald-950/20 text-emerald-300" : "border-amber-500/30 bg-amber-950/20 text-amber-300"}`}>
            {hasAuthoritySource ? "权威体用来源已接通" : "当前仍可能降级到 fallback"}
          </span>
        </div>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
          <div className="mb-2 text-[11px] font-semibold text-zinc-300">柱位权重</div>
          <div className="grid gap-2 text-[10px] text-zinc-400">
            {positionWeights.map(([label, value]) => (
              <div key={label} className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                <span>{label}</span>
                <span className="font-mono text-zinc-200">{value}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-950/60 p-3">
          <div className="mb-2 text-[11px] font-semibold text-zinc-300">距离衰减</div>
          <div className="grid gap-2 text-[10px] text-zinc-400">
            {distanceWeights.map(([label, value]) => (
              <div key={label} className="flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-950/60 px-3 py-2">
                <span>{label}</span>
                <span className="font-mono text-zinc-200">{value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
