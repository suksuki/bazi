"use client";

type Props = {
  label: string;
  selected: boolean;
  isProposal: boolean;
  dotClassName: string;
  onToggle: () => void;
  deltaAbs?: number | null;
  showDeltaBadge?: boolean;
  /** 盲派 / L1 Skill 注册表 ID，右上角展示 */
  skillId?: string;
};

export function DecisionItem({
  label,
  selected,
  isProposal,
  dotClassName,
  onToggle,
  deltaAbs = null,
  showDeltaBadge = false,
  skillId,
}: Props) {
  const hasDelta = showDeltaBadge && selected && typeof deltaAbs === "number" && Number.isFinite(deltaAbs) && Math.abs(deltaAbs) > 0.0001;
  const positive = (deltaAbs || 0) > 0;
  const highLoss = typeof deltaAbs === "number" && deltaAbs > 100;
  const keyUnlock = typeof deltaAbs === "number" && deltaAbs < -50;
  const badgeClass = highLoss
    ? "animate-pulse bg-rose-950/80 text-rose-200"
    : keyUnlock
      ? "bg-emerald-300/20 text-emerald-100 shadow-[0_0_10px_rgba(74,222,128,0.45)]"
      : positive
        ? "text-rose-300"
        : "text-emerald-300";
  return (
    <div
      className={`relative flex items-center justify-between gap-3 rounded-lg border px-3 text-xs ${
        skillId ? "pb-2 pt-6" : "py-2"
      } ${selected ? "border-emerald-500/40 bg-emerald-500/10" : "border-zinc-700 bg-zinc-900"}`}
    >
      {skillId ? (
        <span
          className="absolute left-2 top-1 max-w-[min(130px,48%)] truncate rounded border border-violet-500/35 bg-violet-950/80 px-1.5 py-0.5 font-mono text-[9px] font-medium text-violet-200/95"
          title={`Skill: ${skillId}`}
        >
          {skillId}
        </span>
      ) : null}
      {hasDelta ? (
        <span
          className={`absolute right-11 top-1 rounded px-1.5 py-0.5 text-[10px] ${badgeClass}`}
        >
          {`${positive ? "+" : ""}${(deltaAbs || 0).toFixed(1)} ΔAbs`}
        </span>
      ) : null}
      <span className={selected ? "text-emerald-200" : "text-zinc-200"}>
        <span className="mr-2 inline-flex items-center">
          <span className={`mr-1 inline-block h-2 w-2 rounded-full ${dotClassName}`} />
        </span>
        {label}
        {isProposal ? (
          <span className="ml-2 rounded-md border border-violet-500/40 bg-violet-500/10 px-2 py-0.5 text-[10px] text-violet-300">
            [Auditor 提案]
          </span>
        ) : null}
      </span>
      <span className="flex items-center gap-2">
        {selected ? <span className="text-[11px] text-emerald-300">已认同</span> : null}
        <button
          type="button"
          aria-pressed={selected}
          onClick={onToggle}
          className={`flex h-5 w-5 items-center justify-center rounded border text-[12px] font-bold ${
            selected
              ? "border-emerald-400 bg-emerald-500/20 text-emerald-300"
              : "border-zinc-500 bg-zinc-950 text-transparent"
          }`}
        >
          ✓
        </button>
      </span>
    </div>
  );
}
