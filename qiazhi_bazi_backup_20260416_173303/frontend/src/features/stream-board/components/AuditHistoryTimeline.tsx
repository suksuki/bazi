"use client";

import React from "react";

export function AuditHistoryTimeline(props: {
  originalNarrative: string;
  reasonCode: string;
  correctedNarrative: string;
}) {
  const { originalNarrative, reasonCode, correctedNarrative } = props;
  if (!originalNarrative && !correctedNarrative) return null;
  return (
    <div className="mt-4 rounded-xl border border-fuchsia-500/45 bg-fuchsia-950/30 p-3">
      <p className="text-sm font-semibold text-fuchsia-100">AuditHistoryTimeline</p>
      <div className="mt-2 space-y-2 text-xs">
        <div className="rounded border border-zinc-700/70 bg-zinc-950/60 p-2 text-zinc-100">
          <span className="mr-2 text-fuchsia-300">[原叙事]</span>
          {originalNarrative || "（无记录）"}
        </div>
        <div className="rounded border border-rose-700/70 bg-rose-950/35 p-2 text-rose-100">
          <span className="mr-2 text-rose-300">[拒稿原因]</span>
          {reasonCode || "LIG_AXIS_POS_MISMATCH"}
        </div>
        <div className="rounded border border-emerald-700/70 bg-emerald-950/35 p-2 text-emerald-100">
          <span className="mr-2 text-emerald-300">[修正后叙事]</span>
          {correctedNarrative || "（等待修正输出）"}
        </div>
      </div>
    </div>
  );
}
