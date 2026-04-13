"use client";

import { AnimatePresence, motion } from "framer-motion";

export function PreviewDeltaPercentBadge({ deltaLabel }: { deltaLabel: string }) {
  return (
    <span className="pointer-events-none absolute -right-1 -top-4 z-[5] flex h-4 min-w-[2.5rem] items-center justify-end overflow-hidden whitespace-nowrap text-[9px] font-semibold text-fuchsia-100 shadow-preview-delta-pct drop-shadow-sm">
      <AnimatePresence mode="popLayout" initial={false}>
        <motion.span
          key={deltaLabel}
          layout
          initial={{ y: 12, opacity: 0, filter: "blur(3px)" }}
          animate={{ y: 0, opacity: 1, filter: "blur(0px)" }}
          exit={{ y: -12, opacity: 0, filter: "blur(3px)" }}
          transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
          className="inline-block tabular-nums"
        >
          {deltaLabel}
        </motion.span>
      </AnimatePresence>
    </span>
  );
}
