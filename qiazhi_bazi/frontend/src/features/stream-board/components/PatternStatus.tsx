"use client";

import { useState } from "react";

export type PatternProfileSlice = {
  pattern_name_zh?: string;
  pattern_kind?: string;
  sovereignty_priority?: boolean;
  dominance_ratio?: number;
  xi_ji_reversal_lines?: string[];
};

type Props = {
  profile: PatternProfileSlice | null | undefined;
  className?: string;
  t?: (s: string) => string;
};

export function PatternStatus({ profile, className = "", t = (s: string) => s }: Props) {
  const [open, setOpen] = useState(false);
  if (!profile || typeof profile !== "object") return null;
  const nameRaw = String(profile.pattern_name_zh || "").trim() || "平常局";
  const name = nameRaw === "平常局" ? t("平常局") : t(nameRaw);
  const kind = String(profile.pattern_kind || "none");
  const ratio =
    typeof profile.dominance_ratio === "number" && Number.isFinite(profile.dominance_ratio)
      ? profile.dominance_ratio
      : null;
  const lines = (profile.xi_ji_reversal_lines || []).filter(
    (x): x is string => typeof x === "string" && x.trim().length > 0,
  );
  const sov = Boolean(profile.sovereignty_priority);

  return (
    <div
      className={`relative rounded-lg border border-violet-500/40 bg-gradient-to-r from-violet-950/80 via-zinc-950 to-zinc-950 px-3 py-2 shadow-[0_0_20px_rgba(139,92,246,0.12)] ${className}`}
      data-testid="pattern-status"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onFocus={() => setOpen(true)}
      onBlur={() => setOpen(false)}
      tabIndex={0}
    >
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <span className="text-[10px] font-semibold uppercase tracking-[0.2em] text-violet-300/90">{t("当前格局")}</span>
        {sov ? (
          <span className="rounded border border-amber-500/50 bg-amber-950/50 px-1.5 py-0.5 font-mono text-[9px] text-amber-200">
            {t("格局主权")}
          </span>
        ) : null}
      </div>
      <p className="mt-1 text-sm font-semibold text-zinc-100">{name}</p>
      <p className="mt-0.5 font-mono text-[10px] text-zinc-500">
        kind={kind}
        {ratio != null ? `${t(" · 集中度 ")}${(ratio * 100).toFixed(1)}%` : ""}
      </p>
      {open && lines.length > 0 ? (
        <div
          className="absolute left-0 right-0 top-full z-20 mt-1 rounded-lg border border-zinc-600 bg-zinc-950/98 p-2 text-[11px] leading-relaxed text-zinc-200 shadow-xl backdrop-blur-sm"
          role="tooltip"
        >
          <p className="mb-1 text-[10px] font-medium text-violet-300/90">{t("喜忌反转说明（悬浮）")}</p>
          <ul className="list-disc space-y-1 pl-4">
            {lines.map((line, i) => (
              <li key={i}>{t(line)}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
