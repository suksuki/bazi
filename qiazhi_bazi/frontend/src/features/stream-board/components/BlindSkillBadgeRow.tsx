"use client";

import { motion } from "framer-motion";
import { useBlindSkillHighlight } from "@/features/stream-board/context/BlindSkillHighlightContext";
import type { BlindSkillBadge } from "@/features/stream-board/utils/blindSkillRuntime";

export function BlindSkillBadgeRow({ badges }: { badges: BlindSkillBadge[] }) {
  const { highlightedBadgeId } = useBlindSkillHighlight();
  if (!badges.length) return null;
  return (
    <div className="mb-2 flex flex-wrap items-center gap-2 rounded-lg border border-violet-500/25 bg-violet-950/30 px-2 py-1.5">
      <span className="text-[10px] font-semibold uppercase tracking-wide text-violet-300/90">盲派 Skill</span>
      {badges.map((b) => {
        const dim = !b.armed;
        const hot = b.armed && b.hit;
        const pulse = highlightedBadgeId === b.id;
        return (
          <motion.span
            key={b.id}
            title={`${b.id}${b.hit ? " · 本局已命中信号" : b.armed ? " · 已武装" : " · 未启用"}`}
            animate={{ scale: pulse ? 1.14 : 1 }}
            transition={{ type: "spring", stiffness: 460, damping: 20 }}
            className={`inline-block rounded-md border px-2 py-0.5 text-[10px] font-bold transition-shadow ${
              dim
                ? "border-zinc-700/80 bg-zinc-900/50 text-zinc-600 opacity-45 grayscale"
                : hot
                  ? "border-amber-400/60 bg-amber-500/15 text-amber-200 shadow-[0_0_12px_rgba(251,191,36,0.2)]"
                  : "border-zinc-600 bg-zinc-900/70 text-zinc-400"
            } ${pulse && !dim ? "shadow-[0_0_14px_rgba(167,139,250,0.45)] ring-1 ring-violet-400/50" : ""}`}
          >
            {b.shortLabel}
          </motion.span>
        );
      })}
    </div>
  );
}
