"use client";

type Props = {
  /** 与 ``physics_tensor.meta.hit_pattern_name`` 对齐（L2 法典顶栏） */
  hitPatternName: string;
  className?: string;
  t?: (s: string) => string;
};

/** V9.1：顶栏主标题黑底区，仅展示 L2 命中名（无雷达图 / 无旧结构徽章） */
export function StreamBoardMainHeading({ hitPatternName, className = "", t = (s) => s }: Props) {
  const line = String(hitPatternName || "").trim() || "常规格";
  return (
    <div
      className={`rounded-lg border border-zinc-800 bg-zinc-950 px-3 py-2 shadow-[inset_0_1px_0_rgba(255,255,255,0.04)] ${className}`}
      data-testid="stream-board-main-heading"
    >
      <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-zinc-500">{t("当前格局")}</p>
      <p className="mt-1 text-base font-semibold leading-snug text-zinc-50">{line}</p>
    </div>
  );
}
