"use client";

import type { TimelineSnapshot } from "@/types/bazi";

type Props = {
  referenceYear: number;
  onYearChange: (y: number) => void;
  timeline: TimelineSnapshot | null;
  disabled?: boolean;
  className?: string;
};

const MIN_Y = 1940;
const MAX_Y = 2040;

export function TemporalYearSlider({ referenceYear, onYearChange, timeline, disabled, className = "" }: Props) {
  const liu = timeline?.liunian ? String(timeline.liunian) : "—";
  const dy = timeline?.dayun ? String(timeline.dayun) : "—";
  return (
    <div className={`rounded-lg border border-cyan-900/50 bg-cyan-950/25 px-2 py-2 ${className}`} data-testid="temporal-year-slider">
      <div className="mb-1 flex flex-wrap items-center justify-between gap-2 text-[10px] text-cyan-100/90">
        <span className="font-medium tracking-wide">时空模拟（大运 / 流年）</span>
        <span className="font-mono text-cyan-300/90">
          流年 {liu} · 大运 {dy}
        </span>
      </div>
      <div className="flex items-center gap-2">
        <input
          type="range"
          min={MIN_Y}
          max={MAX_Y}
          step={1}
          value={Math.min(MAX_Y, Math.max(MIN_Y, referenceYear))}
          disabled={disabled}
          onChange={(e) => onYearChange(Number(e.target.value))}
          className="h-2 flex-1 cursor-pointer accent-cyan-400 disabled:cursor-not-allowed disabled:opacity-40"
          aria-label="模拟公历参考年"
        />
        <input
          type="number"
          min={MIN_Y}
          max={MAX_Y}
          value={referenceYear}
          disabled={disabled}
          onChange={(e) => {
            const v = Number(e.target.value);
            if (!Number.isFinite(v)) return;
            onYearChange(Math.min(MAX_Y, Math.max(MIN_Y, Math.round(v))));
          }}
          className="w-16 rounded border border-zinc-600 bg-zinc-900 px-1 py-0.5 text-center font-mono text-[11px] text-zinc-100 disabled:opacity-40"
        />
      </div>
      <p className="mt-1 text-[9px] leading-snug text-zinc-500">
        拖动将静默重算物理张量，并把当前大运/流年干支作为 <span className="font-mono text-zinc-400">external_overrides</span> 提交后端。
      </p>
    </div>
  );
}
