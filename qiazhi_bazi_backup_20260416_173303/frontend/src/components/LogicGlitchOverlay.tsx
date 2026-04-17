"use client";

import { useEffect, useState } from "react";

type Props = {
  active: boolean;
  /** L1 global_entropy 0..1：≥0.8 触发强故障；0.4–0.8 轻量闪烁 */
  entropy?: number | null;
};

export function LogicGlitchOverlay({ active, entropy }: Props) {
  const [visible, setVisible] = useState(false);

  const chaos = active || (typeof entropy === "number" && entropy >= 0.8);
  const tension = typeof entropy === "number" && entropy >= 0.4 && entropy < 0.8;

  useEffect(() => {
    if (!chaos && !tension) return;
    setVisible(true);
    if (typeof navigator !== "undefined" && typeof navigator.vibrate === "function") {
      navigator.vibrate(chaos ? 35 : 14);
    }
    const ms = chaos ? 180 : 110;
    const timer = window.setTimeout(() => setVisible(false), ms);
    return () => window.clearTimeout(timer);
  }, [active, entropy, chaos, tension]);

  if (!visible) return null;
  const opacity = chaos ? 1 : 0.42;
  return (
    <div
      data-testid="logic-glitch-overlay"
      className="pointer-events-none fixed inset-0 z-40 mix-blend-screen"
      style={{
        background:
          "linear-gradient(120deg, rgba(255,0,80,0.16), rgba(0,255,220,0.12), rgba(255,255,255,0.06))",
        clipPath: chaos
          ? "polygon(0 2%, 100% 0, 100% 28%, 0 34%, 0 38%, 100% 35%, 100% 66%, 0 70%, 0 74%, 100% 70%, 100% 100%, 0 98%)"
          : "polygon(0 0, 100% 0, 100% 100%, 0 100%)",
        transform: chaos ? "translate3d(1px,-1px,0)" : "none",
        opacity,
      }}
    />
  );
}
