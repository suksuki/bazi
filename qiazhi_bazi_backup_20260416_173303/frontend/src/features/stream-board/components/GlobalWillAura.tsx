"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useMemo } from "react";
import { useLabStore } from "@/features/stream-board/stores/useLabStore";

function previewHasExclusionHit(rows: unknown): boolean {
  if (!Array.isArray(rows)) return false;
  return rows.some((r) => {
    if (!r || typeof r !== "object" || Array.isArray(r)) return false;
    return (r as { exclusion_hit?: boolean }).exclusion_hit === true;
  });
}

/**
 * 影子预览（悬停卡平行宇宙）激活时：全屏极淡紫 inset 呼吸边光；
 * 若预览 `pattern_thresholds` 含 `exclusion_hit`，切换为暗红微弱脉冲（禁区触碰）。
 */
export function GlobalWillAura() {
  const { state } = useLabStore();
  const shadowActive = Boolean(state.activePreviewId?.trim());
  const exclusionDanger = useMemo(
    () => shadowActive && previewHasExclusionHit(state.previewPatternThresholds),
    [shadowActive, state.previewPatternThresholds],
  );

  return (
    <AnimatePresence>
      {shadowActive ? (
        <motion.div
          key={exclusionDanger ? "global-will-aura-exclusion" : "global-will-aura"}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
          className={`pointer-events-none fixed inset-0 z-[38] ${
            exclusionDanger ? "global-will-aura-exclusion-edge" : "global-will-aura-edge"
          }`}
          aria-hidden
        />
      ) : null}
    </AnimatePresence>
  );
}
