"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  dispatchGlobalEvent,
  PHASE_LOCK_SHIMMER,
  PHASE_POLAR_RIPPLE,
  PHASE_TRANSITION_FLASH,
  type PhaseTransitionFlashDetail,
} from "@/utils/globalUiEvents";

const FLASH_MS = 1500;

/**
 * 全局相变反馈：监听 `PHASE_TRANSITION_FLASH` 底部 Flash；监听 `PHASE_LOCK_SHIMMER` 给 html 极微震颤类名（音效可同事件挂载）。
 */
export function PhaseTransitionAura() {
  const [flash, setFlash] = useState<string | null>(null);
  const flashTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastFlashAtRef = useRef(0);

  const showFlash = useCallback((message: string) => {
    const now = Date.now();
    if (now - lastFlashAtRef.current < FLASH_MS + 80) return;
    lastFlashAtRef.current = now;
    if (flashTimerRef.current) {
      clearTimeout(flashTimerRef.current);
      flashTimerRef.current = null;
    }
    setFlash(message);
    flashTimerRef.current = setTimeout(() => {
      flashTimerRef.current = null;
      setFlash(null);
    }, FLASH_MS);
  }, []);

  useEffect(() => {
    const onFlash = (ev: Event) => {
      const ce = ev as CustomEvent<PhaseTransitionFlashDetail | null>;
      const msg = ce.detail && typeof ce.detail.message === "string" ? ce.detail.message.trim() : "";
      if (!msg) return;
      showFlash(msg);
      dispatchGlobalEvent(PHASE_POLAR_RIPPLE);
    };
    window.addEventListener(PHASE_TRANSITION_FLASH, onFlash as EventListener);
    return () => window.removeEventListener(PHASE_TRANSITION_FLASH, onFlash as EventListener);
  }, [showFlash]);

  useEffect(() => {
    const onShimmer = () => {
      const root = document.documentElement;
      root.classList.add("phase-lock-shimmer-tremor");
      window.setTimeout(() => root.classList.remove("phase-lock-shimmer-tremor"), 720);
      dispatchGlobalEvent(PHASE_POLAR_RIPPLE);
    };
    window.addEventListener(PHASE_LOCK_SHIMMER, onShimmer);
    return () => window.removeEventListener(PHASE_LOCK_SHIMMER, onShimmer);
  }, []);

  useEffect(
    () => () => {
      if (flashTimerRef.current) clearTimeout(flashTimerRef.current);
    },
    [],
  );

  return (
    <AnimatePresence>
      {flash ? (
        <motion.div
          key={flash}
          role="status"
          aria-live="polite"
          initial={{ opacity: 0, y: 16, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 10, scale: 0.98 }}
          transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
          className="pointer-events-none fixed bottom-10 left-1/2 z-[120] w-[min(92vw,22rem)] -translate-x-1/2 rounded-xl border border-amber-400/45 bg-amber-950/82 px-4 py-3 text-center shadow-[0_8px_40px_rgba(0,0,0,0.55),0_0_32px_rgba(251,191,36,0.28)] backdrop-blur-md"
        >
          <p className="text-[10px] font-semibold uppercase tracking-[0.2em] text-amber-200/90">Phase lock</p>
          <p className="mt-1 text-[12px] font-medium leading-snug text-amber-50/95">{flash}</p>
        </motion.div>
      ) : null}
    </AnimatePresence>
  );
}
