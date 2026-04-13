"use client";

type FlowSegment = {
  from?: string;
  to?: string;
  state?: string;
  from_abs?: number;
  to_abs?: number;
  threshold?: number;
};

type FlowAudit = {
  segments?: FlowSegment[];
  break_indices?: number[];
  abs_threshold?: number;
};

const EL_LABEL: Record<string, string> = {
  wood: "木",
  fire: "火",
  earth: "土",
  metal: "金",
  water: "水",
};

type Props = {
  audit: FlowAudit | null | undefined;
  className?: string;
  /** 参考年等：变化时触发动画 key */
  motionKey?: string | number;
  t?: (s: string) => string;
  /** 影子预览开启：仅展示层，不改 audit 真值 */
  previewActive?: boolean;
  /** 预览下假想「修补」的断裂段索引（与 segments 下标对齐） */
  previewHealSegmentIndices?: ReadonlySet<number> | null;
};

export function EnergyFlowChainStrip({
  audit,
  className = "",
  motionKey,
  t = (s: string) => s,
  previewActive = false,
  previewHealSegmentIndices = null,
}: Props) {
  const segments = Array.isArray(audit?.segments) ? audit!.segments! : [];
  if (segments.length === 0) return null;
  const breaks = new Set(Array.isArray(audit?.break_indices) ? audit!.break_indices! : []);
  return (
    <div
      className={`rounded-lg border border-zinc-700 bg-zinc-950/90 px-2 py-2 text-[10px] text-zinc-300 ${className}`}
      data-testid="energy-flow-chain-strip"
    >
      <p className="mb-1.5 font-medium text-amber-200/90">{t("因果流通链（五行相生）")}</p>
      <div className="flex flex-wrap items-center gap-x-1 gap-y-1">
        {segments.map((seg, idx) => {
          const from = String(seg.from || "");
          const to = String(seg.to || "");
          const broken = breaks.has(idx) || seg.state === "BROKEN";
          const previewHeal = Boolean(previewActive && previewHealSegmentIndices?.has(idx));
          return (
            <span
              key={`${String(motionKey ?? "")}-${from}-${to}-${idx}`}
              className="inline-flex items-center gap-0.5 transition-colors duration-500 ease-in-out"
            >
              {idx > 0 ? <span className="text-zinc-600">·</span> : null}
              <span
                className={
                  previewHeal
                    ? "font-semibold text-fuchsia-200/85"
                    : broken
                      ? "font-semibold text-rose-400"
                      : "text-emerald-300/90"
                }
              >
                {t(EL_LABEL[from] || from)}
                <span className="text-zinc-500">→</span>
                {t(EL_LABEL[to] || to)}
              </span>
              {broken && previewHeal ? (
                <span className="text-fuchsia-300/70" title={t("energyFlow.preview.virtualLink")}>
                  ✓
                </span>
              ) : broken ? (
                <span className="text-rose-500">✗</span>
              ) : (
                <span className="text-emerald-500/80">✓</span>
              )}
            </span>
          );
        })}
      </div>
      {typeof audit?.abs_threshold === "number" ? (
        <p className="mt-1 text-[9px] text-zinc-600">
          {t("阈值（归一化场强）:")} {audit.abs_threshold}
        </p>
      ) : null}
    </div>
  );
}
