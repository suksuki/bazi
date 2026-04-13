"use client";

import { useState } from "react";
import { StreamBoardMainHeading } from "@/features/stream-board/components/StreamBoardMainHeading";

export type PatternProfileSlice = {
  pattern_name_zh?: string;
  pattern_kind?: string;
  sovereignty_priority?: boolean;
  dominance_ratio?: number;
  xi_ji_reversal_lines?: string[];
};

type Props = {
  profile: PatternProfileSlice | null | undefined;
  /** 与 ``meta.hit_pattern_name`` / ``l2_pattern_result_summary_v1`` 一致（L2 法典） */
  patternCodexHeadline: string;
  className?: string;
  t?: (s: string) => string;
};

function sanitizeHeadline(raw: string): string {
  const s = String(raw || "").trim();
  if (!s || s === "平常局" || s.startsWith("平常局")) return "常规格";
  return s;
}

export function PatternStatus({ profile, patternCodexHeadline, className = "", t = (s: string) => s }: Props) {
  const [open, setOpen] = useState(false);
  const prof = profile && typeof profile === "object" ? (profile as PatternProfileSlice) : null;
  const headline = sanitizeHeadline(patternCodexHeadline || "常规格");

  const lines = (prof?.xi_ji_reversal_lines || []).filter(
    (x): x is string => typeof x === "string" && x.trim().length > 0,
  );
  const sov = Boolean(prof?.sovereignty_priority);

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
      <div className="flex flex-wrap items-start justify-between gap-2">
        <StreamBoardMainHeading hitPatternName={headline} className="min-w-0 flex-1 border-zinc-700/90" t={t} />
        {sov ? (
          <span className="shrink-0 rounded border border-amber-500/50 bg-amber-950/50 px-1.5 py-0.5 font-mono text-[9px] text-amber-200">
            {t("格局主权")}
          </span>
        ) : null}
      </div>
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
